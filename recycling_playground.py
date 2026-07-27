# recycling_playground.py — code waste recycling via Quantity Taxonomy.
# CC0. stdlib only. phone-buildable.
# Requires: quantity_checker.py, code_playground.py (for snippet/catalog integration)

import ast
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from quantity_checker import (
    QuantityType, Extensivity, Conservation, Datum, Transfer,
    QuantityVar
)
from code_playground import CodeSnippet, Playground  # reuse snippet definition

# ----------------------------------------------------------------------
# Heuristic type inference from Python AST
# ----------------------------------------------------------------------

# A dictionary mapping common variable name patterns to quantity types.
# Extensible; this is the "recycling" domain knowledge.
PATTERN_TO_TYPE = {
    # volume, mass, count, energy
    r'\b(water|volume|tank|cubic|liters?|gallons?)\b': QuantityType(
        Extensivity.EXTENSIVE, Conservation.CONSERVED, Datum.ABSOLUTE,
        Transfer.DEBIT_CREDIT, (0,3,0,0,0,0,0), floor=0.0
    ),
    r'\b(energy|kwh|joule|watt|power)\b': QuantityType(
        Extensivity.EXTENSIVE, Conservation.CONSERVED, Datum.ABSOLUTE,
        Transfer.DEBIT_CREDIT, (1,2,-2,0,0,0,0), floor=0.0
    ),
    r'\b(temp|temperature|kelvin|celsius|fahrenheit)\b': QuantityType(
        Extensivity.INTENSIVE, Conservation.PRODUCIBLE, Datum.RELATIVE,
        Transfer.EQUILIBRATE, (0,0,0,0,1,0,0), floor=0.0
    ),
    r'\b(count|number|quantity|qty)\b': QuantityType(
        Extensivity.EXTENSIVE, Conservation.MONOTONE, Datum.ABSOLUTE,
        Transfer.COPY, (0,0,0,0,0,0,0), floor=0.0
    ),
    r'\b(price|cost|money|dollar)\b': QuantityType(
        Extensivity.EXTENSIVE, Conservation.CONSERVED, Datum.ABSOLUTE,
        Transfer.DEBIT_CREDIT, (1,0,0,0,0,0,0), floor=0.0
    ),
    r'\b(ratio|efficiency|rate|percentage)\b': QuantityType(
        Extensivity.INTENSIVE, Conservation.PRODUCIBLE, Datum.RELATIVE,
        Transfer.COPY, (0,0,0,0,0,0,0), bounded=(0,1)
    ),
    r'\b(mass|kg|weight)\b': QuantityType(
        Extensivity.EXTENSIVE, Conservation.CONSERVED, Datum.ABSOLUTE,
        Transfer.DEBIT_CREDIT, (1,0,0,0,0,0,0), floor=0.0
    ),
}

def infer_type_from_name(name: str) -> Optional[QuantityType]:
    """Heuristic: match variable/function name against known patterns."""
    name_lower = name.lower()
    for pattern, qtype in PATTERN_TO_TYPE.items():
        if re.search(pattern, name_lower):
            return qtype
    # fallback: if name contains 'vol', 'mass', etc., try harder
    if 'vol' in name_lower:
        return QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED, Datum.ABSOLUTE,
                           Transfer.DEBIT_CREDIT, (0,3,0,0,0,0,0), floor=0.0)
    return None

def infer_type_from_annotation(ann: ast.AST) -> Optional[QuantityType]:
    """If annotation is a string like 'QuantityType(...)' we could parse, but keep simple."""
    # Not implemented; could parse type comments like "# qty: energy"
    return None

def extract_snippets_from_file(filepath: str) -> List[CodeSnippet]:
    """
    Parse a Python file and extract functions/classes as potential snippets.
    Attempt to infer input/output quantity types from parameter names and
    return variable names.
    """
    snippets = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, UnicodeDecodeError):
        return []

    # Helper to infer types from a list of variable names
    def infer_var_types(names: List[str]) -> Dict[str, QuantityType]:
        types = {}
        for n in names:
            qt = infer_type_from_name(n)
            if qt:
                types[n] = qt
        return types

    # Walk the tree for function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            # Input types from parameter names
            params = [arg.arg for arg in node.args.args]
            input_types = infer_var_types(params)
            # Output types: try to guess from the function name and the return statement
            # Simplistic: look for a 'return' that returns a single variable
            output_types = {}
            for n in ast.walk(node):
                if isinstance(n, ast.Return) and n.value:
                    if isinstance(n.value, ast.Name):
                        out_var = n.value.id
                        qt = infer_type_from_name(out_var)
                        if qt:
                            output_types[out_var] = qt
            # If no output inferred, try from function name itself (e.g., "pump_water" -> water volume)
            if not output_types:
                qt = infer_type_from_name(func_name)
                if qt:
                    output_types[f"{func_name}_result"] = qt
            # Create snippet
            if input_types or output_types:  # only if we got something
                snippet = CodeSnippet(
                    language="Python",
                    name=func_name,
                    code=ast.get_source_segment(source, node) or "",
                    input_types=input_types,
                    output_types=output_types,
                    description=f"Extracted from {filepath}"
                )
                snippets.append(snippet)
    return snippets

# ----------------------------------------------------------------------
# Waste scanner: crawl a directory and catalog all snippets
# ----------------------------------------------------------------------

class WasteCatalog:
    def __init__(self, root_dir: str):
        self.snippets: List[CodeSnippet] = []
        self.scan(root_dir)

    def scan(self, root_dir: str):
        """Recursively find all .py files and extract snippets."""
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                if fname.endswith('.py'):
                    full_path = os.path.join(dirpath, fname)
                    extracted = extract_snippets_from_file(full_path)
                    for s in extracted:
                        # Add source location to name to avoid collisions
                        s.name = f"{os.path.relpath(full_path, root_dir)}::{s.name}"
                        self.snippets.append(s)

    def query_by_types(self, input_types: Dict[str, QuantityType],
                       output_types: Dict[str, QuantityType]) -> List[CodeSnippet]:
        """
        Find snippets whose inferred types are compatible with the given
        input/output type requirements. Compatibility: same dimension, extensivity.
        """
        matches = []
        for s in self.snippets:
            # Check if all required inputs are provided by snippet's inputs (contravariant)
            # For simplicity, check that the snippet's inputs are a superset of required inputs
            if not all(req in s.input_types for req in input_types):
                continue
            # Check compatibility for each overlapping input
            ok = True
            for var, req_type in input_types.items():
                if var in s.input_types:
                    snip_type = s.input_types[var]
                    if snip_type.dimension != req_type.dimension or snip_type.extensivity != req_type.extensivity:
                        ok = False
                        break
            if not ok:
                continue
            # Similarly for outputs: snippet must provide at least the required outputs
            if not all(req in s.output_types for req in output_types):
                continue
            for var, req_type in output_types.items():
                if var in s.output_types:
                    snip_type = s.output_types[var]
                    if snip_type.dimension != req_type.dimension or snip_type.extensivity != req_type.extensivity:
                        ok = False
                        break
            if ok:
                matches.append(s)
        return matches

# ----------------------------------------------------------------------
# Integration with the creative playground
# ----------------------------------------------------------------------

def recycling_to_playground(catalog: WasteCatalog,
                            initial_inputs: Dict[str, QuantityType],
                            target_outputs: Dict[str, QuantityType],
                            max_depth: int = 3,
                            max_chains: int = 5):
    """
    Use the waste catalog as the snippet library for the Playground.
    This allows exploring repurposing from scrap code.
    """
    playground = Playground(catalog.snippets)
    chains = playground.find_chains(initial_inputs, target_outputs,
                                    max_depth, max_chains)
    return chains

# ----------------------------------------------------------------------
# Demo: scan a dummy code directory and find a recycling chain
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile

    # Create a temporary directory with some "waste" Python files
    with tempfile.TemporaryDirectory() as tmpdir:
        # File 1: a function that computes water volume from pump energy
        with open(os.path.join(tmpdir, "pump_utils.py"), "w") as f:
            f.write("""
def pump_water(energy_in, efficiency):
    # Returns water volume
    water_out = energy_in * efficiency / 9.81  # rough
    return water_out
""")
        # File 2: a function that computes temperature rise from solar energy and water volume
        with open(os.path.join(tmpdir, "solar_heater.py"), "w") as f:
            f.write("""
def heat_water(sunlight_energy, water_volume, cop):
    temp_rise = sunlight_energy * cop / (water_volume * 4.186)
    return temp_rise
""")
        # File 3: a function that mixes two water volumes
        with open(os.path.join(tmpdir, "mixer.py"), "w") as f:
            f.write("""
def temper_valve(hot_vol, cold_vol, hot_temp, cold_temp):
    mixed_vol = hot_vol + cold_vol
    mixed_temp = (hot_vol * hot_temp + cold_vol * cold_temp) / mixed_vol
    return mixed_vol, mixed_temp
""")
        # Scan the waste
        catalog = WasteCatalog(tmpdir)
        print(f"Recycled {len(catalog.snippets)} snippets from waste.")
        for s in catalog.snippets:
            print(f"  {s.name}: {s.input_types} -> {s.output_types}")

        # Try to find a creative repurpose chain: from sunlight energy + hot/cold water volumes+temps
        # to a mixed output stream.
        initial = {
            "energy_in": QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED,
                                      Datum.ABSOLUTE, Transfer.DEBIT_CREDIT,
                                      (1,2,-2,0,0,0,0), floor=0.0),
            "sunlight_energy": QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED,
                                            Datum.ABSOLUTE, Transfer.DEBIT_CREDIT,
                                            (1,2,-2,0,0,0,0), floor=0.0),
            "hot_vol": QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED,
                                    Datum.ABSOLUTE, Transfer.DEBIT_CREDIT,
                                    (0,3,0,0,0,0,0), floor=0.0),
            "cold_vol": QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED,
                                     Datum.ABSOLUTE, Transfer.DEBIT_CREDIT,
                                     (0,3,0,0,0,0,0), floor=0.0),
            "hot_temp": QuantityType(Extensivity.INTENSIVE, Conservation.PRODUCIBLE,
                                     Datum.RELATIVE, Transfer.EQUILIBRATE,
                                     (0,0,0,0,1,0,0)),
            "cold_temp": QuantityType(Extensivity.INTENSIVE, Conservation.PRODUCIBLE,
                                      Datum.RELATIVE, Transfer.EQUILIBRATE,
                                      (0,0,0,0,1,0,0)),
        }
        target = {
            "mixed_vol": QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED,
                                      Datum.ABSOLUTE, Transfer.DEBIT_CREDIT,
                                      (0,3,0,0,0,0,0), floor=0.0),
            "mixed_temp": QuantityType(Extensivity.INTENSIVE, Conservation.PRODUCIBLE,
                                       Datum.RELATIVE, Transfer.EQUILIBRATE,
                                       (0,0,0,0,1,0,0)),
        }

        chains = recycling_to_playground(catalog, initial, target, max_depth=3)
        print(f"\nFound {len(chains)} repurpose chains:")
        for i, chain in enumerate(chains):
            print(f"Chain {i+1}:")
            for step in chain.steps:
                print(f"  {step.name}: {step.description}")
            print(f"  total estimated translation cost: {chain.total_cost:.3f}\n")
