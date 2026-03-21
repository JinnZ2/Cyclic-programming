# CLAUDE.md

## Project Overview

Cyclic Programming is a novel programming language/paradigm that combines quantum mechanics, thermodynamics, biology, and field theory into a computational language. Code "thinks in cycles," conserves energy, and builds capacity through use. This repository contains a proof-of-concept Python interpreter and comprehensive documentation.

**License:** MIT (Copyright 2025 JinnZ2)

## Repository Structure

```
├── cyclic_interpreter.py        # Main interpreter — full feature implementation + COBOL bridge
├── Cyclic_interpreter.py        # Earlier/simpler interpreter version (338 lines)
├── epic_demo.py                 # Complete feature showcase with 10 runnable examples
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

### COBOL Bridge

The `COBOLBridge` class maps COBOL division structure onto Cyclic concepts:

| COBOL Construct | Cyclic Mapping |
|---|---|
| `IDENTIFICATION DIVISION` | Program metadata |
| `DATA DIVISION` / `WORKING-STORAGE` | Field creation (`01 FIELD PIC 9 VALUE energy FREQUENCY freq`) |
| `PROCEDURE DIVISION` | Cyclic operations |

Supported COBOL verbs in the PROCEDURE DIVISION:

| COBOL Verb | Example | Cyclic Equivalent |
|---|---|---|
| `MOVE` | `MOVE 10 FROM A TO B` | `∇F(a↔b)\|∂E/∂t=0` |
| `COMPUTE` | `COMPUTE A = REGENERATE 30` | `∮regenerate(a, 30)` |
| `ENTANGLE` | `ENTANGLE A WITH B` | `⊗(a, b)` |
| `RESONATE` | `RESONATE A WITH B` | `~(a ≈ b)` |
| `TRANSITION` | `TRANSITION A TO PLASMA` | `∂phase(a, plasma)` |
| `DECAY` | `DECAY A BY 0.05` | `∂decay(a, 0.05)` |
| `SYMBIOSIS` | `SYMBIOSIS A WITH B` | `∇∇(a⇄b)` |
| `PERFORM` | `PERFORM OP 3 TIMES` | Repeated execution |
| `DISPLAY` | `DISPLAY A` | Pretty-print field state |
| `STOP RUN` | `STOP RUN` | End execution |

**COBOL Inline Syntax**: Use `COBOL:VERB args` directly in the Cyclic interpreter (e.g., `COBOL:ENTANGLE server WITH client`).

**Usage**:
```python
interp = CyclicalInterpreter()
bridge = interp.cobol_bridge()
bridge.execute_cobol(cobol_source_string)

# Or inline:
interp.execute("COBOL:ENTANGLE fieldA WITH fieldB")
```

## Development Workflow

### Running the Project

```bash
# Run the feature demo
python3 epic_demo.py

# Use the interpreter directly
python3 cyclic_interpreter.py
```

### Dependencies

**None** — pure Python 3 standard library only (`re`, `math`, `typing`, `dataclasses`, `enum`).

### Testing

No formal test framework. Validation is built into the interpreter:
- Energy conservation is checked after every operation
- `epic_demo.py` serves as the integration test suite — all 10 demos (including COBOL) should run without `ConservationViolation` errors
- Verify output shows energy conservation maintained and entropy increasing

### No Build System / CI

This is a standalone Python project with no build steps, no package manager config, and no CI/CD pipelines.

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
- The `sys.path.insert(0, '/mnt/user-data/outputs')` line in `epic_demo.py` is an artifact of the original development environment; adjust if needed locally
- All operations must maintain energy conservation — any new feature must track and preserve total system energy
- Entropy must never decrease in any operation (thermodynamic validity)
- When adding new features, follow the existing pattern: add a method to `CyclicalInterpreter`, register any new syntax in the parser regex, and add a demo to `epic_demo.py`
- COBOL field names use hyphens in source (e.g., `MAINFRAME-NODE`) but are converted to underscores internally (e.g., `mainframe_node`) — this conversion is automatic in `COBOLBridge`
- New COBOL verbs should be added to both `COBOLBridge._parse_procedure_line()` (for full programs) and `CyclicalInterpreter.parse_expression()` under the `COBOL:` prefix (for inline usage)
