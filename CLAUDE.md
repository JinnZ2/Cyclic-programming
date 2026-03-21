# CLAUDE.md

## Project Overview

Cyclic Programming is a novel programming language/paradigm that combines quantum mechanics, thermodynamics, biology, and field theory into a computational language. Code "thinks in cycles," conserves energy, and builds capacity through use. This repository contains a proof-of-concept Python interpreter and comprehensive documentation.

**License:** MIT (Copyright 2025 JinnZ2)

## Repository Structure

```
├── cyclic_interpreter.py        # Main interpreter, COBOL bridge, REPL, and CLI
├── Cyclic_interpreter.py        # Earlier/simpler interpreter version
├── epic_demo.py                 # Complete feature showcase with 10 runnable examples
├── pyproject.toml               # Python packaging config (pip install -e .)
├── tests/
│   └── test_interpreter.py      # pytest test suite (40 tests)
├── README.md                    # Project overview and quick start
├── Specifications.md            # Core language specification and principles
├── QUICK_REFERENCE.md           # Syntax quick reference guide
├── Cyclic_language_complete.md  # Full feature matrix with verified results
├── Expanded.md                  # Extended features documentation
└── LICENSE                      # MIT License
```

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

### Physical Constraints Enforced at Runtime

- **Energy conservation**: Verified to 1e-10 tolerance via `check_energy_conservation()`
- **Entropy**: Always increases (2nd law of thermodynamics)
- **Quantum coherence**: Bounded to [0, 1]
- **Phase states**: crystalline → normal → liquid → gas → plasma (ordered transitions)

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
python3 epic_demo.py
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

40 tests covering:
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

- `cyclic_interpreter.py` (lowercase 'c') is the main/current interpreter — `Cyclic_interpreter.py` (uppercase 'C') is an earlier version
- The `sys.path.insert(0, '/mnt/user-data/outputs')` line in `epic_demo.py` is an artifact of the original development environment; it can be removed
- Run `python3 -m pytest tests/ -v` before pushing changes to verify nothing is broken
- All operations must maintain energy conservation — any new feature must track and preserve total system energy
- Entropy must never decrease in any operation (thermodynamic validity)
- When adding new features, follow the existing pattern: add a method to `CyclicalInterpreter`, register any new syntax in the parser regex, and add a demo to `epic_demo.py`
- COBOL field names use hyphens in source (e.g., `MAINFRAME-NODE`) but are converted to underscores internally (e.g., `mainframe_node`) via `COBOLBridge._normalize_name()`, which also detects collisions where different COBOL names would map to the same internal name
- PIC clauses are enforced: `PIC 9(n)` caps energy at `10^n - 1`, `V99` adds decimal precision. Constraints are checked after every operation via `_enforce_constraints()`
- `MOVE` is a **directed transfer** (source loses, target gains) — it does NOT use bidirectional `interact_with()`. The `FieldState.directed_transfer()` method handles this
- New COBOL verbs should be added to both `COBOLBridge._parse_procedure_line()` (for full programs) and `CyclicalInterpreter.parse_expression()` under the `COBOL:` prefix (for inline usage)
- COBOL paragraphs are stored in `COBOLBridge.paragraphs` and executed via `_execute_paragraph()` when invoked by `PERFORM`
