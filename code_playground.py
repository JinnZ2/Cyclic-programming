# code_playground.py — cross‑language snippet repurpose playground.
# CC0. stdlib only. phone‑buildable.
# Depends on: quantity_checker.py, repurpose_table.py (optional)

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from quantity_checker import (
    QuantityType, QuantityVar, Extensivity, Conservation,
    Datum, Transfer, QuantityError
)
# The old language_translation_table module was merged into repurpose_table,
# which holds the same (source, target) -> (cost, effectiveness) mapping and
# can also load it from CSV. The import stays optional: a missing table means
# "assume translation is free", handled at the lookup below.
try:
    from repurpose_table import DEFAULT_LANGUAGE_TABLE as TRANSLATION_TABLE
except ImportError:  # pragma: no cover - depends on install layout
    TRANSLATION_TABLE = {}

# ----------------------------------------------------------------------
# Core data structures
# ----------------------------------------------------------------------

@dataclass
class CodeSnippet:
    """
    A small, self‑contained piece of logic tagged with its input/output
    quantity types. The actual code string is language‑specific, but the
    type signature is language‑independent.
    """
    language: str
    name: str
    code: str                        # human‑readable snippet (any language)
    input_types: Dict[str, QuantityType]   # variable name → type
    output_types: Dict[str, QuantityType]  # variable name → type
    description: str = ""

@dataclass
class RepurposeChain:
    """
    A sequence of snippets wired together. The chain is viable if the
    output types of one snippet match the input types of the next (after
    possible language‑internal conversions). Costs are estimated from the
    translation table.
    """
    steps: List[CodeSnippet] = field(default_factory=list)
    total_cost: float = 0.0
    total_effectiveness: float = 1.0

    def add_step(self, snippet: CodeSnippet, cost: float, effectiveness: float):
        self.steps.append(snippet)
        self.total_cost += cost
        self.total_effectiveness *= effectiveness

    def apply(self, input_vars: Dict[str, QuantityVar]) -> Dict[str, QuantityVar]:
        """
        Actually run the chain (in simulation) by feeding variables through
        each snippet. Because we don't execute arbitrary code, we simulate
        type‑level propagation: each step consumes certain typed variables
        and produces new ones with the declared output types. Values are
        lost; only types propagate — the creative assembly is at the type level.
        """
        current = {**input_vars}
        for step in self.steps:
            # Check that all required inputs are present
            for name, needed_type in step.input_types.items():
                if name not in current:
                    raise QuantityError(f"Missing input {name} for {step.name}")
                # Ideally check type compatibility; simplified here
            # Produce outputs (values set to 0 for simulation)
            for out_name, out_qtype in step.output_types.items():
                current[out_name] = QuantityVar(out_name, 0.0, out_qtype)
        return current

# ----------------------------------------------------------------------
# Playground engine
# ----------------------------------------------------------------------

class Playground:
    def __init__(self, snippets: List[CodeSnippet]):
        self.snippets = {s.name: s for s in snippets}
        # Build adjacency: which outputs can feed which inputs
        self.graph = self._build_graph()

    def _type_compatible(self, src_type: QuantityType, dst_type: QuantityType) -> bool:
        """True if src_type can be used where dst_type is expected."""
        # Must have same dimension, same datum, compatible extensivity
        if src_type.dimension != dst_type.dimension:
            return False
        if src_type.extensivity != dst_type.extensivity:
            return False
        if src_type.datum != dst_type.datum:
            return False
        # Signedness? Floor/ceiling? Simplified: only strict equality for now
        # In a full version, contravariance applies.
        return True

    def _match_inputs(self, snippet: CodeSnippet,
                      available: Dict[str, QuantityType]) -> Optional[Dict[str, str]]:
        """
        Bind each of the snippet's inputs to an available variable of
        compatible type. Returns {parameter: variable} or None if any input
        cannot be satisfied.

        Matching is by TYPE, not by name. The reduction rule this playground
        rests on says two bindings with the same topology and quantity type
        are the same binding, and that names differing is not a difference —
        so keying the search on names would make it depend on exactly the
        thing it claims to discard. A snippet expecting `electric_energy_in`
        must accept a variable called `sunlight` carrying the same energy type.

        Each variable is consumed by at most one parameter, so a mixer needing
        two water volumes will not fire on a single stream. The assignment is
        greedy in sorted order rather than a full bipartite matching, which is
        adequate for playground-sized snippet sets and deterministic.
        """
        binding: Dict[str, str] = {}
        used: set = set()
        for param, needed in snippet.input_types.items():
            candidate = next(
                (var for var in sorted(available)
                 if var not in used
                 and self._type_compatible(available[var], needed)),
                None)
            if candidate is None:
                return None
            binding[param] = candidate
            used.add(candidate)
        return binding

    def _build_graph(self) -> Dict[str, List[Tuple[str, str, float, float]]]:
        """
        Returns {src_snippet_name: [(dest_snippet_name, src_output, dest_input, cost, effectiveness)]}
        where cost/effectiveness come from the translation table.
        """
        graph = {}
        for src_name, src_snip in self.snippets.items():
            edges = []
            for dst_name, dst_snip in self.snippets.items():
                if src_name == dst_name:
                    continue
                # For every output of src, can it match an input of dst?
                for src_out, src_type in src_snip.output_types.items():
                    for dst_in, dst_type in dst_snip.input_types.items():
                        if self._type_compatible(src_type, dst_type):
                            # Look up translation cost from source language to dest language
                            # Fallback: assume perfect translation (cost 0, eff 1) if table missing
                            try:
                                cost, eff = TRANSLATION_TABLE.get(
                                    (src_snip.language, dst_snip.language), (0.0, 1.0)
                                )
                            except NameError:
                                cost, eff = 0.0, 1.0
                            edges.append((dst_name, src_out, dst_in, cost, eff))
            graph[src_name] = edges
        return graph

    def find_chains(self,
                    initial_inputs: Dict[str, QuantityType],
                    target_outputs: Dict[str, QuantityType],
                    max_depth: int = 3,
                    max_chains: int = 5) -> List[RepurposeChain]:
        """
        Search for snippet chains that start from the given input types and
        eventually produce the target output types. Returns a list of viable
        chains sorted by ascending total_cost.
        """
        chains = []
        # BFS over composition depth
        queue = []
        # Initial state: no steps yet, current available variables = initial_inputs
        # We'll store (vars_dict, chain_so_far)
        queue.append((initial_inputs, RepurposeChain()))
        while queue:
            current_vars, chain = queue.pop(0)
            if len(chain.steps) >= max_depth:
                continue
            # Which snippets can we trigger from the current available vars?
            # For each snippet, if all its inputs are present, we can apply it.
            for s_name, s in self.snippets.items():
                # Fireable when every input can be bound to some available
                # variable of compatible type — by type, not by name.
                if self._match_inputs(s, current_vars) is None:
                    continue
                # This snippet is fireable. We'll need to produce its outputs
                new_vars = {**current_vars, **s.output_types}  # type annotation only
                # But also need to estimate cost of translating from current context language?
                # For simplicity, we use the graph edges to weight cost.
                # Actually, we need to know which previous step's output feeds which input.
                # A full implementation would track edges; here we approximate cost = sum of translation costs from prior snippet language to s.language.
                # For now, just a flat cost of 0.1 per step if languages differ.
                cost_estimate = 0.1 if (chain.steps and chain.steps[-1].language != s.language) else 0.0
                new_chain = RepurposeChain()
                new_chain.steps = chain.steps.copy()
                new_chain.add_step(s, cost_estimate, 1.0)
                # Check if target outputs are now covered
                # Target reached when every wanted output type is present on
                # some produced variable — again by type, not by name.
                wanted = CodeSnippet("", "", "", dict(target_outputs), {})
                if self._match_inputs(wanted, new_vars) is not None:
                    chains.append(new_chain)
                    if len(chains) >= max_chains:
                        return sorted(chains, key=lambda c: c.total_cost)
                # Continue search
                queue.append((new_vars, new_chain))
        return sorted(chains, key=lambda c: c.total_cost)

# ----------------------------------------------------------------------
# Demo: creative assembly of water treatment and energy management
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # Define some quantity types (reusing from earlier taxonomy)
    water_volume = QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED,
                                Datum.ABSOLUTE, Transfer.DEBIT_CREDIT,
                                (0,3,0,0,0,0,0), floor=0.0)
    temperature = QuantityType(Extensivity.INTENSIVE, Conservation.PRODUCIBLE,
                               Datum.RELATIVE, Transfer.EQUILIBRATE,
                               (0,0,0,0,1,0,0), floor=0.0)
    energy = QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED,
                          Datum.ABSOLUTE, Transfer.DEBIT_CREDIT,
                          (1,2,-2,0,0,0,0), floor=0.0)  # M L^2 T^-2

    # Create snippets from different languages
    pump = CodeSnippet(
        language="Python", name="electric_pump",
        code="water_volume_out = electric_energy_in * pump_efficiency / head",
        input_types={"electric_energy_in": energy, "pump_efficiency": QuantityType(Extensivity.INTENSIVE, Conservation.PRODUCIBLE, Datum.RELATIVE, Transfer.COPY, (0,0,0,0,0,0,0), floor=0.0, ceiling=1.0)},
        output_types={"water_volume_out": water_volume},
        description="Converts electrical energy to pumped water volume."
    )

    heater = CodeSnippet(
        language="Rust", name="solar_heater",
        code="fn heat_water(sunlight_kwh: f64, water_liters: f64) -> f64 { sunlight_kwh * COP / (water_liters * 4.186) }",
        input_types={"sunlight_energy": energy, "cold_water_volume": water_volume},
        output_types={"hot_water_temp_rise": temperature},
        description="Heats water using solar energy; temperature rise depends on energy and volume."
    )

    # A COBOL snippet that mixes hot/cold water
    mixer = CodeSnippet(
        language="COBOL", name="tempering_valve",
        code="MOVE HOT-WATER-VOL TO TEMP-MIX. *> (pseudocode)",
        input_types={"hot_vol": water_volume, "cold_vol": water_volume,
                     "hot_temp": temperature, "cold_temp": temperature},
        output_types={"mixed_volume": water_volume, "mixed_temp": temperature},
        description="Mixes two water streams to a desired temperature."
    )

    snippets = [pump, heater, mixer]
    playground = Playground(snippets)

    # We want: from sunlight (energy) and two water sources (volumes, temps)
    # produce a mixed stream at a target temperature.
    initial = {
        "sunlight": energy,
        "source_cold_vol": water_volume,
        "source_hot_vol": water_volume,
        "source_cold_temp": temperature,
        "source_hot_temp": temperature,
    }
    target = {
        "output_volume": water_volume,
        "output_temp": temperature,
    }

    chains = playground.find_chains(initial, target, max_depth=4, max_chains=3)
    for i, chain in enumerate(chains):
        print(f"Chain {i+1}:")
        for step in chain.steps:
            print(f"  {step.language}/{step.name}: {step.description}")
        print(f"  estimated cost: {chain.total_cost:.3f}\n")
