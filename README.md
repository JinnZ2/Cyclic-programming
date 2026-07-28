# Cyclic Programming

An experimental interpreter for a small language whose operations are written
as energy transfers, plus a cascade model that uses the same accounting to ask
when a degrading system stops being worth repairing.

Two halves, one idea: track where capacity goes, and never let an operation
create it from nothing.

- **The interpreter** (`cyclic_interpreter.py`) executes expressions written
  with mathematical operators — `∇F(a↔b)`, `∮regenerate(f, 30)`, `⊗(a, b)`.
  Bidirectional exchange is checked for energy conservation at runtime;
  several other operations are not, and do not conserve it (see
  [Known gaps](#known-gaps)). A COBOL-inspired bridge offers the same
  operations in a division/verb syntax.
- **The cascade model** (`harm.py`, `simulator.py`, `repurpose_controller.py`)
  models nodes that draw down capacity faster than they regenerate, and the
  cost that displaces onto whatever they are coupled to. It reports when a
  system crosses the point where continuing is cheaper than reversing.

The two halves meet in `cyclic_repurpose_adapter.py`, which backs the cascade
model with the interpreter when it is importable and a plain conserving model
when it is not.

## Install

Pure standard library, Python 3.9+. Nothing is required to run it.

```bash
pip install -e .          # optional, provides the `cyclic` entry point
pip install -e ".[dev]"   # adds pytest
```

## Run

```bash
python3 cyclic_interpreter.py            # interactive REPL
python3 cyclic_interpreter.py --demo     # built-in demo
python3 cyclic_interpreter.py -e "⊗(a, b)"
python3 cyclic_interpreter.py prog.cyc   # run a .cyc or .cob file
python3 demo.py                          # every feature, with output
```

```python
from cyclic_interpreter import CyclicalInterpreter

interp = CyclicalInterpreter()
interp.create_field("sun", 200.0, frequency=1.0)
interp.create_field("planet", 100.0, frequency=2.0)

interp.execute("∇F(sun↔planet)|∂E/∂t=0")   # bidirectional exchange
interp.execute("∮regenerate(planet, 30)")   # regenerative cycle
interp.execute("~(sun ≈ planet)")           # resonance
interp.display_state()
```

## Language features

| Feature | Syntax |
|---|---|
| Bidirectional exchange | `∇F(a↔b)\|∂E/∂t=0` |
| Regenerative cycle | `∮regenerate(field, E)` |
| Natural decay | `∂decay(field, rate)` |
| Symbiosis | `∇∇(a⇄b)` |
| Quantum entanglement | `⊗(a, b)` |
| Resonance | `~(a ≈ b)` |
| Phase transition | `∂phase(field, state)` |
| Fractal generation | `∮^n(field, depth)` |
| Spatial gradient | `∇spatial(a, b)` |
| Multi-field network | `∇³F(a↔b↔c↔d)\|...` |
| COBOL program | `IDENTIFICATION DIVISION...` |
| COBOL inline | `COBOL:VERB args` |

Phase transitions follow the order crystalline → normal → liquid → gas →
plasma. The other constraints are intended rather than enforced: energy
conservation is checked on bidirectional exchange only, entropy increases in
practice without a guard, and coherence is clamped everywhere except
resonance. See [Known gaps](#known-gaps) for what that costs.

`decay()` takes a *rate* (a fraction of current energy), not an absolute
amount. See `QUICK_REFERENCE.md` for the full syntax and `Specifications.md`
for the design rationale.

## Repurposing

`harm.read()` takes a snapshot of a coupled system and reports four things:
per-node imbalance, total induced imbalance at each order outward, whether
cost is being displaced through couplings, and whether it inflates rather than
dissipates. It returns numbers, not a verdict.

`simulator.run()` makes that dynamical — displaced cost erodes the receiving
node's regeneration, so deficits compound — and reports the tick at which
reversal starts outpacing continuation.

`repurpose_controller.run_with_repurposing()` adds the two things that let a
system pull out of a cascade: passive recovery, and a finite reserve a
controller can spend to restore capacity. The reserve is finite and decays, so
a controller that spends indiscriminately runs dry before the cascade stops.

Two worked examples, same arithmetic applied to different domains:

```bash
python3 component_repurpose.py   # degraded electronic parts
python3 language_ecosystem.py    # programming language ecosystems
```

## Cross-repo link

`component_repurpose.py` runs on real data from
[Component-failure-repurposing-database](https://github.com/JinnZ2/Component-failure-repurposing-database),
which catalogues what a component can still do after a given failure mode — a
silicon diode with parametric degradation makes a decent environmental sensor
or a hardware RNG.

The link is declared in `.fieldlink.json`, matching the manifest format that
repo already uses. Linked data is vendored under `vendor/`, not fetched:
`fieldlink.py` resolves declared paths to local files and reports anything
missing rather than reaching for the network.

```bash
python3 fieldlink.py   # show which declared sources are present
```

To refresh the vendored matrix:

```bash
curl -L -o vendor/component-failure-db/matrices/repurpose_effectiveness.csv \
  https://raw.githubusercontent.com/JinnZ2/Component-failure-repurposing-database/main/matrices/repurpose_effectiveness.csv
```

That database grades effectiveness as High/Medium/Low;
`repurpose_table.GRADE_TO_EFFECTIVENESS` maps those to 0.9/0.6/0.3. It carries
no cost column, so cost is derived as `1 - effectiveness` — a poorer repurpose
takes more work to press into service. Both are modeling choices made here,
not upstream data.

## Layout

```
cyclic_interpreter.py           interpreter, COBOL bridge, REPL, CLI
demo.py                         every feature, with output
harm.py                         snapshot of a coupled system
simulator.py                    steps harm.py forward in time
repurpose_controller.py         recovery and a finite repurposing reserve
repurpose_table.py              (source, target) -> (cost, effectiveness)
cyclic_repurpose_adapter.py     the one bridge to the interpreter
component_repurpose.py          component failure data through the model
language_ecosystem.py           the same model, applied to languages
fieldlink.py                    resolves .fieldlink.json
.fieldlink.json                 declared cross-repo sources
quantity.py                     physics-quantity types + the conserving Ledger
quantity_audit.py               checks interpreter operations against those types
taxonomy_lab.py                 falsification harness for the taxonomy
residue_probe.py                E3 fixture: is a label actually inert?
adversarial_corpus.py           bias probe with an answer key (17 cases)
quantity_checker.py             mutable typed variables, composes dimensions
taxonomy_conformance.py         one spec, checked against both implementations
code_playground.py              chains typed snippets into repurpose paths
recycling_playground.py         mines a source tree for reusable snippets
repurpose_workshop.py           CLI over the catalogue and the playground
vector_recycling_playground.py  vector-space snippet transformations
token_recycling_playground.py   token-level recycling experiments
QUANTITY_TAXONOMY.md            the vocabulary and what testing it found
vendor/                         vendored data from linked repos
tests/                          pytest suite
```

## Tests

```bash
python3 -m pytest tests/ -v
```

The modules outside the interpreter also carry assert-based self-tests that
run without pytest:

```bash
python3 harm.py
python3 simulator.py
python3 repurpose_controller.py
```

## Known gaps

`check_energy_conservation()` has exactly one call site, inside
`execute_bidirectional_interaction`. Every other operation is unchecked, and
several do not conserve energy. `quantity_audit.py` measures this:

```bash
python3 quantity_audit.py
```

As of this commit, 4 of 10 operations satisfy the types their cells should
carry:

- **Resonance and symbiosis create energy in a closed pair.** `~(a ≈ b)`
  multiplies both fields by `1 + 0.2·resonance_strength` with nothing
  debited; sixteen applications turn 200 units into 3697.
- **Coherence is clamped in `regenerate` but not in `resonate_with`**, so
  repeated resonance carries it to 1.6, outside its [0,1] bound. The existing
  `test_coherence_bounded` passes because it exercises entanglement, which
  does clamp.
- **`regenerate`, `decay` and `phase` move energy with no reservoir cell to
  debit**, so the change is real but unaccounted.

Treat resonance amplification as a documented behaviour of the current
interpreter, not as a conservation guarantee. `QUANTITY_TAXONOMY.md` describes
the typing that would make these unwritable rather than merely reported.

## Status

Working proof of concept. The physics is a modeling metaphor rather than a
simulation of anything — energy here is bookkeeping, not joules. The
draw/regen numbers in the ecosystem examples are hand-set to illustrate the
threshold, not measured from real systems. See [Known gaps](#known-gaps) for
where the interpreter's own invariants are not upheld.

## Related

- [Component-failure-repurposing-database](https://github.com/JinnZ2/Component-failure-repurposing-database) — failure modes and what degraded parts can still do
- [Geometric-to-Binary Computational Bridge](https://github.com/JinnZ2/Geometric-to-Binary-Computational-Bridge) — geometric representations and binary computation

## License

MIT. Copyright 2025 JinnZ2.
