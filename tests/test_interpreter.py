"""Tests for the Cyclical Programming Language interpreter."""

import sys
import os
import math
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cyclic_interpreter import (
    CyclicalInterpreter, COBOLBridge, EnergyState, FieldState,
    FieldOperator, ConservationViolation,
)


# ── Field creation and basic state ──────────────────────────────────────────

class TestFieldCreation:
    def test_create_field_defaults(self):
        interp = CyclicalInterpreter()
        interp.create_field("test")
        assert "test" in interp.fields
        assert interp.fields["test"].energy.total_energy == 10.0
        assert interp.fields["test"].frequency == 1.0

    def test_create_field_custom(self):
        interp = CyclicalInterpreter()
        interp.create_field("star", 200.0, frequency=5.0)
        field = interp.fields["star"]
        assert field.energy.total_energy == 200.0
        assert field.frequency == 5.0
        assert field.phase_state == "normal"
        assert field.capacity == 1.0

    def test_create_via_expression(self):
        interp = CyclicalInterpreter()
        interp.execute("energy_field = 75")
        assert "energy_field" in interp.fields
        assert interp.fields["energy_field"].energy.total_energy == 75.0


# ── Energy conservation ─────────────────────────────────────────────────────

class TestEnergyConservation:
    def test_bidirectional_conserves_energy(self):
        interp = CyclicalInterpreter()
        interp.create_field("a", 100.0)
        interp.create_field("b", 50.0)
        initial = sum(f.energy.total_energy for f in interp.fields.values())
        interp.execute("∇F(a↔b)|∂E/∂t=0")
        final = sum(f.energy.total_energy for f in interp.fields.values())
        assert abs(initial - final) < 1e-10

    def test_directed_transfer_conserves_energy(self):
        interp = CyclicalInterpreter()
        interp.create_field("src", 100.0)
        interp.create_field("dst", 50.0)
        initial = sum(f.energy.total_energy for f in interp.fields.values())
        interp.execute("COBOL:MOVE 20 FROM src TO dst")
        final = sum(f.energy.total_energy for f in interp.fields.values())
        assert abs(initial - final) < 1e-10

    def test_spatial_gradient_conserves_energy(self):
        interp = CyclicalInterpreter()
        interp.create_field("hot", 200.0)
        interp.create_field("cold", 50.0)
        interp.fields["hot"].position = (0.0, 0.0, 0.0)
        interp.fields["cold"].position = (1.0, 1.0, 1.0)
        initial = sum(f.energy.total_energy for f in interp.fields.values())
        interp.execute("∇spatial(hot, cold)")
        final = sum(f.energy.total_energy for f in interp.fields.values())
        assert abs(initial - final) < 1e-10


# ── Entropy (2nd law) ───────────────────────────────────────────────────────

class TestEntropy:
    def test_entropy_increases_on_interaction(self):
        interp = CyclicalInterpreter()
        interp.create_field("a", 100.0)
        interp.create_field("b", 50.0)
        initial_entropy = sum(f.energy.entropy for f in interp.fields.values())
        interp.execute("∇F(a↔b)|∂E/∂t=0")
        final_entropy = sum(f.energy.entropy for f in interp.fields.values())
        assert final_entropy >= initial_entropy

    def test_entropy_increases_on_decay(self):
        interp = CyclicalInterpreter()
        interp.create_field("system", 100.0)
        initial_entropy = interp.fields["system"].energy.entropy
        interp.execute("∂decay(system, 0.1)")
        assert interp.fields["system"].energy.entropy > initial_entropy


# ── Quantum operations ───────────────────────────────────────────────────────

class TestQuantum:
    def test_entanglement_links_fields(self):
        interp = CyclicalInterpreter()
        interp.create_field("p1", 50.0)
        interp.create_field("p2", 50.0)
        interp.execute("⊗(p1, p2)")
        assert interp.fields["p1"].entangled_with == "p2"
        assert interp.fields["p2"].entangled_with == "p1"

    def test_entanglement_boosts_coherence(self):
        interp = CyclicalInterpreter()
        interp.create_field("p1", 50.0)
        interp.create_field("p2", 50.0)
        interp.execute("⊗(p1, p2)")
        assert interp.fields["p1"].energy.quantum_coherence > 0
        assert interp.fields["p2"].energy.quantum_coherence > 0

    def test_coherence_bounded(self):
        interp = CyclicalInterpreter()
        interp.create_field("a", 50.0)
        interp.create_field("b", 50.0)
        # Entangle many times
        for _ in range(20):
            interp.execute("⊗(a, b)")
        assert interp.fields["a"].energy.quantum_coherence <= 1.0


# ── Resonance ────────────────────────────────────────────────────────────────

class TestResonance:
    def test_matching_frequencies_amplify(self):
        interp = CyclicalInterpreter()
        interp.create_field("osc1", 100.0, frequency=5.0)
        interp.create_field("osc2", 100.0, frequency=5.0)
        initial = sum(f.energy.total_energy for f in interp.fields.values())
        interp.execute("~(osc1 ≈ osc2)")
        final = sum(f.energy.total_energy for f in interp.fields.values())
        assert final > initial  # Resonance amplifies

    def test_mismatched_frequencies_weaker(self):
        interp1 = CyclicalInterpreter()
        interp1.create_field("a", 100.0, frequency=5.0)
        interp1.create_field("b", 100.0, frequency=5.0)
        interp1.execute("~(a ≈ b)")
        matched_energy = sum(f.energy.total_energy for f in interp1.fields.values())

        interp2 = CyclicalInterpreter()
        interp2.create_field("a", 100.0, frequency=1.0)
        interp2.create_field("b", 100.0, frequency=10.0)
        interp2.execute("~(a ≈ b)")
        mismatched_energy = sum(f.energy.total_energy for f in interp2.fields.values())

        assert matched_energy > mismatched_energy


# ── Phase transitions ────────────────────────────────────────────────────────

class TestPhaseTransitions:
    def test_transition_changes_state(self):
        interp = CyclicalInterpreter()
        interp.create_field("water", 150.0)
        interp.execute("∂phase(water, gas)")
        assert interp.fields["water"].phase_state == "gas"

    def test_transition_costs_energy(self):
        interp = CyclicalInterpreter()
        interp.create_field("water", 150.0)
        initial = interp.fields["water"].energy.total_energy
        interp.execute("∂phase(water, plasma)")
        assert interp.fields["water"].energy.total_energy < initial

    def test_insufficient_energy_no_transition(self):
        interp = CyclicalInterpreter()
        interp.create_field("ice", 5.0)  # Very low energy
        interp.execute("∂phase(ice, plasma)")
        assert interp.fields["ice"].phase_state == "normal"  # Unchanged


# ── Regeneration and decay ───────────────────────────────────────────────────

class TestRegenAndDecay:
    def test_regenerate_increases_capacity(self):
        interp = CyclicalInterpreter()
        interp.create_field("plant", 100.0)
        initial_cap = interp.fields["plant"].capacity
        interp.execute("∮regenerate(plant, 20)")
        assert interp.fields["plant"].capacity > initial_cap

    def test_decay_reduces_energy(self):
        interp = CyclicalInterpreter()
        interp.create_field("system", 100.0)
        initial = interp.fields["system"].energy.total_energy
        interp.execute("∂decay(system, 0.1)")
        assert interp.fields["system"].energy.total_energy < initial

    def test_symbiosis_benefits_both(self):
        interp = CyclicalInterpreter()
        interp.create_field("fungus", 100.0)
        interp.create_field("tree", 100.0)
        cap_f = interp.fields["fungus"].capacity
        cap_t = interp.fields["tree"].capacity
        interp.execute("∇∇(fungus⇄tree)")
        assert interp.fields["fungus"].capacity > cap_f
        assert interp.fields["tree"].capacity > cap_t


# ── Fractal generation ───────────────────────────────────────────────────────

class TestFractal:
    def test_fractal_creates_children(self):
        interp = CyclicalInterpreter()
        interp.create_field("seed", 128.0)
        interp.execute("∮^1(seed, 2)")
        # depth 2 should create 2^2 = 4 children
        fractal_fields = [n for n in interp.fields if "fractal" in n]
        assert len(fractal_fields) == 4


# ── Multi-field networks ─────────────────────────────────────────────────────

class TestMultiFieldNetwork:
    def test_network_creates_fields(self):
        interp = CyclicalInterpreter()
        interp.execute("∇³F(node_A↔node_B↔node_C)|∂E/∂t=0")
        assert "node_A" in interp.fields
        assert "node_B" in interp.fields
        assert "node_C" in interp.fields


# ── Directed transfer ────────────────────────────────────────────────────────

class TestDirectedTransfer:
    def test_move_transfers_exact_amount(self):
        interp = CyclicalInterpreter()
        interp.create_field("src", 100.0)
        interp.create_field("dst", 50.0)
        interp.execute("COBOL:MOVE 30 FROM src TO dst")
        assert abs(interp.fields["src"].energy.total_energy - 70.0) < 1e-10
        assert abs(interp.fields["dst"].energy.total_energy - 80.0) < 1e-10

    def test_move_clamped_to_available(self):
        interp = CyclicalInterpreter()
        interp.create_field("src", 10.0)
        interp.create_field("dst", 50.0)
        interp.execute("COBOL:MOVE 100 FROM src TO dst")
        # Should transfer at most 90% of source energy (9.0), not 100
        assert interp.fields["src"].energy.total_energy > 0


# ── COBOL bridge ─────────────────────────────────────────────────────────────

class TestCOBOLBridge:
    def test_pic_constraint_caps_energy(self):
        interp = CyclicalInterpreter()
        bridge = interp.cobol_bridge()
        cobol = """
        DATA DIVISION.
        WORKING-STORAGE SECTION.
        01 SMALL-FIELD PIC 9(2) VALUE 50 FREQUENCY 1.0.

        PROCEDURE DIVISION.
        STOP RUN.
        """
        bridge.execute_cobol(cobol)
        assert interp.fields["small_field"].energy.total_energy <= 99

    def test_pic_rejects_over_max(self):
        interp = CyclicalInterpreter()
        bridge = interp.cobol_bridge()
        cobol = """
        DATA DIVISION.
        WORKING-STORAGE SECTION.
        01 TINY PIC 9(1) VALUE 500.

        PROCEDURE DIVISION.
        STOP RUN.
        """
        bridge.execute_cobol(cobol)
        # PIC 9(1) max is 9, so 500 should be capped
        assert interp.fields["tiny"].energy.total_energy <= 9

    def test_paragraph_execution(self):
        interp = CyclicalInterpreter()
        bridge = interp.cobol_bridge()
        cobol = """
        DATA DIVISION.
        WORKING-STORAGE SECTION.
        01 FIELD-A PIC 9(5) VALUE 100.

        PROCEDURE DIVISION.

        GROW-PARA.
            COMPUTE FIELD-A = REGENERATE 10.

        MAIN-LOGIC.
            PERFORM GROW-PARA 3 TIMES.
            STOP RUN.
        """
        bridge.execute_cobol(cobol)
        # After 3 regenerations, capacity should have grown
        assert interp.fields["field_a"].capacity > 1.0

    def test_name_normalization(self):
        interp = CyclicalInterpreter()
        bridge = interp.cobol_bridge()
        cobol = """
        DATA DIVISION.
        WORKING-STORAGE SECTION.
        01 MY-FIELD PIC 9(5) VALUE 100.

        PROCEDURE DIVISION.
        DISPLAY MY-FIELD.
        STOP RUN.
        """
        bridge.execute_cobol(cobol)
        assert "my_field" in interp.fields

    def test_directed_move(self):
        interp = CyclicalInterpreter()
        bridge = interp.cobol_bridge()
        cobol = """
        DATA DIVISION.
        WORKING-STORAGE SECTION.
        01 SOURCE PIC 9(5) VALUE 200.
        01 TARGET PIC 9(5) VALUE 100.

        PROCEDURE DIVISION.
        MOVE 50 FROM SOURCE TO TARGET.
        STOP RUN.
        """
        bridge.execute_cobol(cobol)
        assert interp.fields["source"].energy.total_energy < 200
        assert interp.fields["target"].energy.total_energy > 100


# ── EnergyState dataclass ────────────────────────────────────────────────────

class TestEnergyState:
    def test_add(self):
        e1 = EnergyState(total_energy=10.0, entropy=1.0)
        e2 = EnergyState(total_energy=20.0, entropy=2.0)
        result = e1 + e2
        assert result.total_energy == 30.0
        assert result.entropy == 3.0

    def test_conserved_with(self):
        e1 = EnergyState(total_energy=100.0)
        e2 = EnergyState(total_energy=100.0)
        assert e1.conserved_with(e2)

    def test_not_conserved(self):
        e1 = EnergyState(total_energy=100.0)
        e2 = EnergyState(total_energy=50.0)
        assert not e1.conserved_with(e2)

    def test_in_phase(self):
        e1 = EnergyState(phase_angle=0.0)
        e2 = EnergyState(phase_angle=0.05)
        assert e1.in_phase_with(e2)

    def test_out_of_phase(self):
        e1 = EnergyState(phase_angle=0.0)
        e2 = EnergyState(phase_angle=math.pi)
        assert not e1.in_phase_with(e2)


# ── Parser ────────────────────────────────────────────────────────────────────

class TestParser:
    def test_parse_entanglement(self):
        interp = CyclicalInterpreter()
        result = interp.parse_expression("⊗(fieldA, fieldB)")
        assert result['type'] == 'quantum_entangle'
        assert result['fields'] == ['fieldA', 'fieldB']

    def test_parse_resonance(self):
        interp = CyclicalInterpreter()
        result = interp.parse_expression("~(osc1 ≈ osc2)")
        assert result['type'] == 'resonance'

    def test_parse_phase_transition(self):
        interp = CyclicalInterpreter()
        result = interp.parse_expression("∂phase(water, gas)")
        assert result['type'] == 'phase_transition'
        assert result['target_phase'] == 'gas'

    def test_parse_cobol_inline_move(self):
        interp = CyclicalInterpreter()
        result = interp.parse_expression("COBOL:MOVE 20 FROM server TO client")
        assert result['type'] == 'directed_transfer'
        assert result['amount'] == 20.0

    def test_parse_unknown(self):
        interp = CyclicalInterpreter()
        result = interp.parse_expression("gibberish nonsense")
        assert result['type'] == 'unknown'

    def test_parse_regenerate(self):
        interp = CyclicalInterpreter()
        result = interp.parse_expression("∮regenerate(plant, 20)")
        assert result['type'] == 'regenerate'
        assert result['energy'] == 20.0

    def test_parse_decay(self):
        interp = CyclicalInterpreter()
        result = interp.parse_expression("∂decay(system, 0.1)")
        assert result['type'] == 'decay'
        assert result['rate'] == 0.1
