# CLAUDE.md

## Project Overview

Cyclic Programming is a novel programming language/paradigm that combines quantum mechanics, thermodynamics, biology, and field theory into a computational language. Code "thinks in cycles," conserves energy, and builds capacity through use. This repository contains a proof-of-concept Python interpreter and comprehensive documentation.

**License:** MIT (Copyright 2025 JinnZ2)

## Repository Structure

```
├── cyclic_interpreter.py        # Main interpreter (1019 lines) — full 10-feature implementation
├── Cyclic_interpreter.py        # Earlier/simpler interpreter version (338 lines)
├── epic_demo.py                 # Complete feature showcase with 8 runnable examples
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

### 10 Language Features

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

### Physical Constraints Enforced at Runtime

- **Energy conservation**: Verified to 1e-10 tolerance via `check_energy_conservation()`
- **Entropy**: Always increases (2nd law of thermodynamics)
- **Quantum coherence**: Bounded to [0, 1]
- **Phase states**: crystalline → normal → liquid → gas → plasma (ordered transitions)

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
- `epic_demo.py` serves as the integration test suite — all 8 demos should run without `ConservationViolation` errors
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
