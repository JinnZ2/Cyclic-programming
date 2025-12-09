# Cyclical Language - Quick Reference

## Basic Operations

```python
# Bidirectional interaction (energy conserved)
∇F(field1↔field2)|∂E/∂t=0

# Regenerative growth
∮regenerate(field_name, energy_input)

# Natural decay
∂decay(field_name, decay_rate)

# Symbiotic relationship (mutual benefit)
∇∇(field1⇄field2)
```

## Quantum Operations

```python
# Quantum entanglement
⊗(particle1, particle2)

# Check if fields are entangled
field.entangled_with  # Returns partner name or None
```

## Resonance & Harmonics

```python
# Resonant coupling (amplifies when frequencies match)
~(oscillator1 ≈ oscillator2)

# Fields with similar frequencies gain energy through resonance
# Amplification = 1 + k * exp(-|freq1 - freq2|)
```

## Phase Transitions

```python
# Change phase state (costs energy)
∂phase(field_name, target_phase)

# Phases: crystalline → normal → liquid → gas → plasma
# Each transition increases entropy
```

## Fractal Generation

```python
# Create self-similar structures
∮^iterations(field_name, depth)

# depth=1: creates 2 fractals
# depth=2: creates 4 fractals  
# depth=n: creates 2^n fractals

# Fractals have:
# - Smaller energy (divided by 2^depth)
# - Higher frequency (multiplied by 2^depth)
# - Same phase state as parent
# - Spatial distribution
```

## Spatial Dynamics

```python
# Energy flows based on spatial gradient
∇spatial(field1, field2)

# Flow rate proportional to:
# - Energy difference
# - Distance between fields
# gradient_strength = ΔE / distance
```

## Multi-Field Networks

```python
# Network with 3+ fields
∇³F(field1↔field2↔field3)|∂E/∂t=0

# Creates pairwise interactions between all fields
# 3 fields = 3 interactions
# 4 fields = 6 interactions
# n fields = n(n-1)/2 interactions
```

## Field Properties

```python
field.energy.total_energy      # Total energy (J)
field.energy.kinetic           # Active energy
field.energy.potential         # Stored energy
field.energy.entropy           # Disorder measure
field.energy.quantum_coherence # Superposition (0-1)
field.energy.phase_angle       # Oscillation phase (rad)
field.capacity                 # Regenerative capacity
field.age                      # Cycles since creation
field.phase_state             # Phase of matter
field.frequency               # Oscillation rate (Hz)
field.fractal_depth           # Recursive level
field.entangled_with          # Quantum partner
field.position                # (x, y, z)
field.gradient                # (gx, gy, gz)
```

## Constraints

```python
|∂E/∂t=0    # Energy conservation required
|∂S/∂t≥0    # Entropy must increase
|ΔE=0       # No energy creation/destruction
```

## Example Combinations

### Quantum-Enhanced Regeneration

```python
⊗(seed, environment)              # Entangle
∮regenerate(seed, 50)             # Grow
~(seed ≈ environment)             # Resonate
# Result: High coherence + capacity + amplification
```

### Phase-Based Evolution

```python
∂phase(system, liquid)            # Increase mobility
∮regenerate(system, 30)           # Build capacity  
∂phase(system, plasma)            # Achieve emergence
# Result: Higher-order state with regenerative capacity
```

### Fractal Network

```python
∮^1(node, 2)                      # Create 4 fractals
∇³F(node↔fractal0↔fractal1↔...)|∂E/∂t=0  # Network them
# Result: Self-similar distributed system
```

### Symbiotic Resonance

```python
∇∇(organism1⇄organism2)           # Establish symbiosis
~(organism1 ≈ organism2)          # Frequency lock
# Result: Mutually amplifying partnership
```

## Common Patterns

### Growth Cycle

```
for i in range(n):
    ∮regenerate(field, energy)
    ~(field ≈ environment)
```

### Decay-Regeneration Balance

```
∂decay(old_system, 0.1)
∮regenerate(new_system, recovered_energy)
```

### Quantum Network

```
⊗(node1, node2)
⊗(node2, node3)  
⊗(node3, node1)
# Creates entangled triangle
```

### Fractal Ecosystem

```
∮^1(seed, 2)  # Create level 1
∮^1(fractal_0, 1)  # Create level 2 from one branch
# Result: Multi-scale nested structure
```

## Physical Constants

- Energy units: Joules (J)
- Frequency units: Hertz (Hz)
- Phase angle: Radians (0 to 2π)
- Coherence: Dimensionless (0 to 1)
- Capacity: Dimensionless (starts at 1.0)
- Entropy: Dimensionless (increases over time)

## Tips

1. **Start simple**: Use basic interactions first
1. **Check conservation**: Energy should remain constant
1. **Watch entropy**: Should always increase
1. **Experiment**: Combine features in new ways
1. **Think cyclically**: Everything returns and regenerates
1. **Embrace emergence**: Complex behavior from simple rules

## Common Mistakes

❌ Trying to decrease entropy
❌ Expecting energy from nothing
❌ Forgetting spatial positions for gradients
❌ Mixing incompatible frequencies without resonance
❌ Phase transitions without enough energy

✅ Energy always conserved
✅ Entropy always increases
✅ Fields need initialization
✅ Resonance amplifies matching frequencies
✅ Phase transitions cost energy

## Quick Test

```python
from cyclical_interpreter import CyclicalInterpreter

interp = CyclicalInterpreter()
interp.create_field("test", 100.0, frequency=5.0)
interp.execute("∮regenerate(test, 20)")
interp.execute("~(test ≈ test)")  # Self-resonance!
interp.display_state()
```

-----

**Remember**: This language thinks in cycles, conserves energy, and builds capacity!
