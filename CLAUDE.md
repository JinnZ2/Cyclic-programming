# CLAUDE.md

## Project Overview

This repo holds two things that share one idea — track where capacity goes, and never let an operation create it from nothing.

1. **A proof-of-concept interpreter** for a small language whose operations are written as energy transfers using mathematical Unicode operators, with a COBOL-inspired alternative syntax. Energy is bookkeeping, not joules: the physics is a modeling metaphor, and docs should not claim otherwise.
2. **A cascade model** that uses the same accounting to ask when a degrading system passes the point where continuing is cheaper than reversing, and whether repurposing keeps it on the near side.

**License:** MIT (Copyright 2025 JinnZ2). The cascade-model modules carry CC0 headers from their original author.

## Repository Structure

```
├── cyclic_interpreter.py        # Main interpreter, COBOL bridge, REPL, and CLI
├── demo.py                      # Feature showcase with 10 runnable examples
├── harm.py                      # Snapshot read of a coupled system
├── simulator.py                 # Steps harm.py forward in time
├── repurpose_controller.py      # Passive recovery + a finite repurposing reserve
├── repurpose_table.py           # (source, target) -> (cost, effectiveness)
├── cyclic_repurpose_adapter.py  # The only bridge to the interpreter
├── component_repurpose.py       # Component failure data through the cascade model
├── language_ecosystem.py        # Same model, applied to language ecosystems
├── fieldlink.py                 # Resolves .fieldlink.json cross-repo sources
├── .fieldlink.json              # Declared links to sibling repos
├── quantity.py                  # Physics-quantity types + the conserving Ledger
├── quantity_audit.py            # Checks interpreter ops against declared cell types
├── taxonomy_lab.py              # Falsification harness (E1 coverage/E2 axes/E3 residue)
├── residue_probe.py             # E3 fixture: is a label actually inert?
├── adversarial_corpus.py        # Bias probe with an answer key (17 cases)
├── quantity_checker.py          # Lighter typed-variable prototype (see note below)
├── code_playground.py           # Chains typed snippets into repurpose paths
├── recycling_playground.py      # Mines a source tree for reusable snippets
├── repurpose_workshop.py        # CLI over the catalogue and the playground
├── vector_recycling_playground.py  # Vector-space snippet transformations
├── token_recycling_playground.py   # Token-level recycling experiments
├── QUANTITY_TAXONOMY.md         # The vocabulary and what testing it found
├── vendor/                      # Vendored data from linked repos
├── pyproject.toml               # Python packaging config (pip install -e .)
├── tests/
│   └── test_interpreter.py      # pytest test suite
├── README.md                    # Project overview and quick start
├── Specifications.md            # Core language specification and principles
├── QUICK_REFERENCE.md           # Syntax quick reference guide
├── Cyclic_language_complete.md  # Full feature matrix with verified results
├── Expanded.md                  # Extended features documentation
└── LICENSE                      # MIT License
```

## Cascade model

`harm.py` reads a snapshot: per-node draw-minus-regen imbalance, induced imbalance at each order outward, whether cost is displaced through couplings, and whether it inflates. `simulator.py` makes it dynamical — displaced cost erodes the receiving node's regen. `repurpose_controller.py` adds passive recovery plus a finite, decaying reserve a controller spends to restore capacity.

Controller convention: a controller is called as `controller(t, system, reserve)` and returns a list of `(node_name, amount)` actions. **The runner charges the reserve** — a controller must not decrement `reserve.value` itself.

Two worked examples use the identical machinery on different domains: `component_repurpose.py` (degraded electronic parts, real upstream data) and `language_ecosystem.py` (language ecosystems, hand-set numbers).

## Cross-repo link

`.fieldlink.json` mirrors the manifest format used by [Component-failure-repurposing-database](https://github.com/JinnZ2/Component-failure-repurposing-database). Linked data is **vendored under `vendor/`, never fetched at runtime** — the manifest sets `"offline": true`, and `fieldlink.py` reports a missing source rather than reaching for the network. Use `fieldlink.component_matrix_path()` to locate vendored data; do not hardcode paths under `vendor/`.

`repurpose_table.load_component_matrix()` adapts that repo's `matrices/repurpose_effectiveness.csv` into the same `(source, target) -> (cost, effectiveness)` shape used for languages. Two modeling choices live there and must stay documented as choices, not upstream facts: High/Medium/Low grades map to 0.9/0.6/0.3, and cost is derived as `1 - effectiveness` because the CSV has no cost column. Source keys are `"Component/Failure Mode"`.

## Key Architecture

### Core Classes (in `cyclic_interpreter.py`)

- **`EnergyState`** (dataclass): Tracks energy, entropy, quantum coherence, and phase angle for each field.
- **`FieldState`** (dataclass): Represents a field with energy, spatial position, capacity, frequency, phase state, entanglement links, and history.
- **`FieldOperator`** (enum): Defines operators — gradient, partial derivative, bidirectional exchange, tensor/entanglement, cycle, and resonance.
- **`ConservationViolation`** (exception): Raised when energy conservation is violated.
- **`CyclicalInterpreter`**: Main interpreter class with parser, field registry, and execution engine.
- **`COBOLBridge`**: Translates COBOL-style structured syntax into Cyclic field operations, mapping enterprise computing paradigms onto physics-based computation.

### 12 Language Features (including COBOL)

| Feature | Syntax | Method |
|---|---|---|
| Bidirectional Exchange | `∇F(a↔b)\|∂E/∂t=0` | `interact_with()` |
| Regenerative Cycles | `∮regenerate(field, E)` | `regenerate()` |
| Natural Decay | `∂decay(field, rate)` | `decay()` |
| Symbiotic Relationships | `∇∇(a⇄b)` | `symbiosis_with()` |
| Quantum Entanglement | `⊗(a, b)` | `quantum_entangle()` |
| Resonance/Harmonics | `~(a ≈ b)` | `resonate_with()` |
| Phase Transitions | `∂phase(field, state)` | `phase_transition()` |
| Fractal Generation | `∮^n(field, depth)` | `fractal_spawn()` |
| Spatial Gradients | `∇spatial(a, b)` | `spatial_gradient_flow()` |
| Multi-Field Networks | `∇³F(a↔b↔c↔d)\|...` | Multi-field network methods |
| COBOL Full Programs | `IDENTIFICATION DIVISION...` | `COBOLBridge.execute_cobol()` |
| COBOL Inline Syntax | `COBOL:VERB args` | Parsed in `parse_expression()` |

### Physical Constraints — what is actually enforced

Do not repeat the claim that all operations conserve energy; `quantity_audit.py`
measures otherwise, and 4 of 10 operations currently satisfy their cell types.

- **Energy conservation**: checked to 1e-10 via `check_energy_conservation()`, but
  that function has **exactly one call site**, inside `execute_bidirectional_interaction`.
  Resonance and symbiosis create energy in a closed pair; `regenerate`, `decay`
  and `phase` move it with no reservoir to debit
- **Entropy**: increases in practice, not enforced by a guard
- **Quantum coherence**: clamped to [0, 1] in `regenerate` and entanglement, but
  **not in `resonate_with`** — repeated resonance reaches 1.6. `test_coherence_bounded`
  passes only because it exercises entanglement
- **Phase states**: crystalline → normal → liquid → gas → plasma (ordered transitions)

`quantity.py` encodes the seven-axis taxonomy from `QUANTITY_TAXONOMY.md`; its
`Ledger` is the missing reservoir — cells can only be raised by `transfer()`, so
an orphan credit is not expressible. Rebuilding `EnergyState` on it would change
interpreter behaviour (resonance amplification is currently a documented feature),
so treat that as a design decision, not a bug fix.

### Two quantity implementations — unresolved

`quantity.py` and `quantity_checker.py` both implement the same taxonomy and
neither strictly dominates the other:

- `quantity.py` has immutable values, a per-axis error class, the `Ledger`,
  `weighted_mean`, the transcendental dimensionless check, and `erase_cost`
- `quantity_checker.py` has mutable `QuantityVar` with bounds-checked writes,
  and `__mul__`/`__truediv__` that compose dimensions — which `quantity.py`
  does not have at all

`quantity_audit.py` and the taxonomy tests import the first; the four
playground modules import the second. Consolidating means picking a direction
and porting what the loser has, so it is a design decision, not cleanup. Until
then, **fix any taxonomy rule in both** — `quantity_checker` silently allowed
`RELATIVE + RELATIVE`, monotone decrements, and arithmetic on a `convention`
residue until those were added to match `quantity.py`.

### COBOL-Inspired Bridge

The `COBOLBridge` provides COBOL-inspired structured syntax as an alternative way
to express Cyclic operations. It is **not** a COBOL compiler — it borrows COBOL's
division/verb structure while mapping to Cyclic physics semantics.

**DIVISION structure:**

| COBOL Construct | Cyclic Mapping |
|---|---|
| `IDENTIFICATION DIVISION` | Program metadata (`PROGRAM-ID`) |
| `DATA DIVISION` / `WORKING-STORAGE` | Field creation with PIC constraints |
| `PROCEDURE DIVISION` | Operations via verbs and named paragraphs |

**PIC clause semantics** (not cosmetic — enforced at runtime):

| PIC Clause | Meaning | Effect |
|---|---|---|
| `PIC 9(3)` | 3-digit numeric | Energy capped at 999 |
| `PIC 9(5)` | 5-digit numeric | Energy capped at 99999 |
| `PIC 9(3)V99` | 3 digits + 2 decimal | Energy capped at 999.99, rounded to 2 decimals |
| `PIC X(n)` | Alphanumeric | No energy cap (unconstrained) |

**Supported verbs:**

| COBOL Verb | Example | Cyclic Equivalent |
|---|---|---|
| `MOVE` | `MOVE 10 FROM A TO B` | `directed_transfer()` — A loses 10, B gains 10 |
| `COMPUTE` | `COMPUTE A = REGENERATE 30` | `∮regenerate(a, 30)` |
| `ENTANGLE` | `ENTANGLE A WITH B` | `⊗(a, b)` |
| `RESONATE` | `RESONATE A WITH B` | `~(a ≈ b)` |
| `TRANSITION` | `TRANSITION A TO PLASMA` | `∂phase(a, plasma)` |
| `DECAY` | `DECAY A BY 0.05` | `∂decay(a, 0.05)` |
| `SYMBIOSIS` | `SYMBIOSIS A WITH B` | `∇∇(a⇄b)` |
| `PERFORM` | `PERFORM PARA-NAME 3 TIMES` | Execute named paragraph N times |
| `DISPLAY` | `DISPLAY A` | Pretty-print field state + PIC constraints |
| `STOP RUN` | `STOP RUN` | End execution |

**Paragraphs:** Define reusable procedure blocks in the PROCEDURE DIVISION. A paragraph is
a label ending with `.` followed by indented statements. Invoke with `PERFORM`:
```
PROCEDURE DIVISION.

BOOST-NETWORK.
    COMPUTE NETWORK = REGENERATE 15.
    SYMBIOSIS TERMINAL WITH NETWORK.

MAIN-LOGIC.
    PERFORM BOOST-NETWORK 3 TIMES.
    STOP RUN.
```

**COBOL inline syntax** — use `COBOL:VERB args` directly in the Cyclic interpreter:
```python
interp = CyclicalInterpreter()

# Directed transfer (source loses, target gains)
interp.execute("COBOL:MOVE 20 FROM server TO client")

# Other verbs
interp.execute("COBOL:ENTANGLE fieldA WITH fieldB")
interp.execute("COBOL:COMPUTE fieldA = REGENERATE 30")
```

**Full program usage:**
```python
interp = CyclicalInterpreter()
bridge = interp.cobol_bridge()
bridge.execute_cobol(cobol_source_string)
```

## Development Workflow

### Installation

```bash
# Install in development mode
pip install -e .

# Or install with dev dependencies (pytest)
pip install -e ".[dev]"
```

### Running

```bash
# Interactive REPL
python3 cyclic_interpreter.py
# or after pip install:
cyclic

# Run the built-in demo
python3 cyclic_interpreter.py --demo

# Execute a single expression
python3 cyclic_interpreter.py -e "⊗(fieldA, fieldB)"

# Execute a source file (.cyc or .cob)
python3 cyclic_interpreter.py myprogram.cyc

# Run the full feature showcase
python3 demo.py

# Cascade model: the two worked examples
python3 component_repurpose.py
python3 language_ecosystem.py

# Show which declared cross-repo sources are vendored
python3 fieldlink.py
```

### REPL Commands

| Command | Action |
|---|---|
| `create <name> <energy> [freq]` | Create a field |
| `state` | Show all field states |
| `fields` | List field names |
| `reset` | Clear all fields |
| `cobol` | Enter multi-line COBOL mode (end with `END.`) |
| `help` | Show available commands and syntax |
| `quit` / `exit` | Exit |

Any Cyclic expression or `COBOL:VERB` inline command can be typed directly at the `cyclic>` prompt.

### Dependencies

**Runtime:** Pure Python 3.9+ standard library only (`re`, `math`, `typing`, `dataclasses`, `enum`).
**Dev:** `pytest>=7.0` (optional, for running tests).

### Testing

```bash
python3 -m pytest tests/ -v
```

The cascade-model modules also carry assert-based self-tests that run without pytest — `python3 harm.py`, `python3 simulator.py`, `python3 repurpose_controller.py`, and so on. New modules in that family should follow the same pattern: `_t_*` functions plus a `_run()` that calls them.

Tests cover:
- Field creation and state management
- Energy conservation (bidirectional, directed transfer, spatial gradient)
- Entropy increase (2nd law)
- Quantum operations (entanglement, coherence bounding)
- Resonance (frequency matching, amplification)
- Phase transitions (state changes, energy cost, insufficient energy)
- Regeneration, decay, symbiosis
- Fractal generation
- Multi-field networks
- Directed transfer (COBOL MOVE)
- COBOL bridge (PIC constraints, paragraphs, name normalization)
- Parser (all expression types)
- EnergyState dataclass methods

## Code Conventions

- **Language**: Python 3 with dataclasses and type hints
- **Unicode operators**: The language uses mathematical Unicode symbols (`∇`, `∂`, `⇄`, `⊗`, `∮`, `≈`) both in syntax and source code
- **Immutable-style updates**: Methods return new `FieldState` instances rather than mutating existing ones
- **Docstrings**: All major methods have docstrings explaining the physics
- **Comments**: Explain physical principles and conservation laws
- **Error handling**: Custom `ConservationViolation` exception for physics violations
- **Output formatting**: Pretty-printed results with separator lines and clear labels

## Important Notes for AI Assistants

- `cyclic_interpreter.py` is the interpreter; there is exactly one, and nothing outside `cyclic_repurpose_adapter.py` should import it directly
- Run `python3 -m pytest tests/ -v` before pushing changes to verify nothing is broken
- **Units matter and have caused real bugs.** `FieldState.decay()` takes a *rate* (a fraction of current energy), while `CyclicRepurposeEngine.draw_down()` takes an *absolute amount*; the adapter converts between them. `FieldState.energy` is an `EnergyState`, not a float — the scalar is `field.energy.total_energy`
- Prose in the README and docs should stay plain. No emoji headers, no "revolutionary"/"consciousness-level" framing, no invented metrics tables. Say what the code does and what is a modeling assumption
- All operations must maintain energy conservation — any new feature must track and preserve total system energy
- Entropy must never decrease in any operation (thermodynamic validity)
- When adding new features, follow the existing pattern: add a method to `CyclicalInterpreter`, register any new syntax in the parser regex, and add a demo to `epic_demo.py`
- COBOL field names use hyphens in source (e.g., `MAINFRAME-NODE`) but are converted to underscores internally (e.g., `mainframe_node`) via `COBOLBridge._normalize_name()`, which also detects collisions where different COBOL names would map to the same internal name
- PIC clauses are enforced: `PIC 9(n)` caps energy at `10^n - 1`, `V99` adds decimal precision. Constraints are checked after every operation via `_enforce_constraints()`
- `MOVE` is a **directed transfer** (source loses, target gains) — it does NOT use bidirectional `interact_with()`. The `FieldState.directed_transfer()` method handles this
- New COBOL verbs should be added to both `COBOLBridge._parse_procedure_line()` (for full programs) and `CyclicalInterpreter.parse_expression()` under the `COBOL:` prefix (for inline usage)
- COBOL paragraphs are stored in `COBOLBridge.paragraphs` and executed via `_execute_paragraph()` when invoked by `PERFORM`
