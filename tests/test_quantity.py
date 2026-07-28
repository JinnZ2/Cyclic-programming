"""
Tests for the quantity taxonomy, the interpreter audit, and the falsification
harness.

The modules under test carry their own assert-based self-tests so they stay
runnable without pytest; this file re-runs those and adds the cases that are
easier to express here.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import quantity
import quantity_audit
import taxonomy_lab
from quantity import (
    ConventionError, Datum, DatumError, DimensionError, DomainError, ExtensivityError,
    Ledger, MonotonicityError, Quantity, ConservationError,
    bounded_fraction, conserved_energy, counter, entropy, information,
    relative_scale, residue, total, weighted_mean, DIMENSIONLESS, TIME,
)

SELFTEST_MODULES = [quantity, quantity_audit]


def _selftests(module):
    return [(name, fn) for name, fn in sorted(vars(module).items())
            if name.startswith("_t_") and callable(fn)]


@pytest.mark.parametrize("module", SELFTEST_MODULES, ids=lambda m: m.__name__)
def test_module_selftests_pass(module):
    checks = _selftests(module)
    assert checks, f"{module.__name__} declares no _t_* self-tests"
    for _, fn in checks:
        fn()


# --- the axes --------------------------------------------------------------

def test_floored_quantity_rejects_underflow():
    water = conserved_energy("water")
    with pytest.raises(DomainError):
        Quantity(5.0, water) - Quantity(9.0, water)


def test_intensive_cannot_be_summed():
    hot = Quantity(0.9, bounded_fraction("density"))
    with pytest.raises(ExtensivityError):
        total([hot, hot])


def test_intensive_averages_against_its_extensive_weight():
    pairs = [
        (Quantity(0.9, bounded_fraction("temp")), Quantity(1.0, counter("kg"))),
        (Quantity(0.1, bounded_fraction("temp")), Quantity(9.0, counter("kg"))),
    ]
    # the naive mean would say 0.5; the big cold mass dominates
    assert weighted_mean(pairs).value == pytest.approx(0.18)


def test_relative_datum_forbids_addition_but_allows_difference():
    # EXTENSIVE so the datum rule is what fires, not intensive-addition
    clock = quantity.QuantityType(
        quantity.Extensivity.EXTENSIVE, quantity.Conservation.PRODUCIBLE,
        Datum.RELATIVE, quantity.Transfer.DEBIT_CREDIT, TIME, label="clock")
    with pytest.raises(DatumError):
        Quantity(12.0, clock) + Quantity(12.0, clock)
    elapsed = Quantity(17.0, clock) - Quantity(9.0, clock)
    assert elapsed.value == 8.0
    assert elapsed.type.datum is Datum.ABSOLUTE


def test_relative_difference_may_go_negative():
    clock = relative_scale(TIME, "clock")
    assert (Quantity(9.0, clock) - Quantity(17.0, clock)).value == -8.0


def test_intensives_cannot_be_added_pairwise():
    # the rule held for total() but not for `+` until the conformance
    # suite compared the two implementations
    coherence = bounded_fraction("coherence")
    with pytest.raises(ExtensivityError):
        Quantity(0.4, coherence) + Quantity(0.5, coherence)


def test_dimension_mismatch_is_rejected():
    joules = Quantity(1.0, conserved_energy())
    ratio = Quantity(1.0, bounded_fraction("ratio"))
    with pytest.raises(DimensionError):
        joules + ratio


def test_monotone_cannot_run_backwards():
    clock = entropy("clock")
    with pytest.raises(MonotonicityError):
        Quantity(100.0, clock) - Quantity(1.0, clock)


def test_bounded_quantity_refuses_to_leave_its_interval():
    # EXTENSIVE bounded type: this checks the ceiling, one axis at a time
    ratio = quantity.QuantityType(
        quantity.Extensivity.EXTENSIVE, quantity.Conservation.PRODUCIBLE,
        Datum.ABSOLUTE, quantity.Transfer.DEBIT_CREDIT,
        DIMENSIONLESS, floor=0.0, ceiling=1.0, label="ratio")
    with pytest.raises(DomainError):
        Quantity(0.95, ratio) + Quantity(0.2, ratio)
    with pytest.raises(DomainError):
        Quantity(1.6, ratio)


def test_residue_forbids_arithmetic_and_ordering():
    zip_type = residue("US_ZIP", "zip")
    a, b = Quantity(90210.0, zip_type), Quantity(10001.0, zip_type)
    with pytest.raises(ConventionError):
        a + b
    with pytest.raises(ConventionError):
        a < b


# --- the ledger ------------------------------------------------------------

def test_ledger_total_is_invariant_under_transfer():
    ledger = Ledger(conserved_energy(), "closed")
    ledger.open_cell("a", 100.0)
    ledger.open_cell("b", 100.0)
    ledger.transfer("a", "b", 40.0)
    assert ledger.balance("a").value == 60.0
    assert ledger.balance("b").value == 140.0
    assert ledger.check() == 200.0


def test_ledger_refuses_to_overdraw_and_leaves_no_trace():
    ledger = Ledger(conserved_energy())
    ledger.open_cell("a", 10.0)
    ledger.open_cell("b", 0.0)
    with pytest.raises(ConservationError):
        ledger.transfer("a", "b", 25.0)
    assert ledger.check() == 10.0


def test_ledger_exposes_no_way_to_credit_without_debiting():
    ledger = Ledger(conserved_energy())
    ledger.open_cell("a", 100.0)
    for forbidden in ("credit", "amplify", "regenerate"):
        assert not hasattr(ledger, forbidden)


def test_ledger_rejects_producible_and_monotone_types():
    for bad in (entropy(), information()):
        with pytest.raises((ConservationError, quantity.TransferError)):
            Ledger(bad)


# --- the interpreter audit -------------------------------------------------

def test_bidirectional_exchange_satisfies_its_types():
    row = next(r for r in quantity_audit.audit()
               if r["label"].startswith("bidirectional"))
    assert row["violations"] == []


def test_resonance_creates_energy_in_a_closed_pair():
    row = next(r for r in quantity_audit.audit()
               if r["label"].startswith("resonance      "))
    assert any(axis == "CONSERVED" for axis, _, _ in row["violations"])
    assert row["after"]["total_energy"] > row["before"]["total_energy"]


def test_repeated_resonance_breaches_the_coherence_ceiling():
    row = next(r for r in quantity_audit.audit()
               if r["label"].startswith("resonance ×16"))
    assert row["after"]["max_coherence"] > 1.0
    assert any(axis == "BOUNDED[0,1]" for axis, _, _ in row["violations"])


def test_open_operations_move_energy_with_no_reservoir():
    rows = [r for r in quantity_audit.audit() if not r["closed"]]
    assert rows
    for row in rows:
        assert any(axis == "DEBIT_CREDIT" for axis, _, _ in row["violations"])


def test_a_typed_cell_refuses_the_coherence_value_the_interpreter_stores():
    from cyclic_interpreter import CyclicalInterpreter
    interp = CyclicalInterpreter()
    interp.create_field("a", 100.0, frequency=5.0)
    interp.create_field("b", 100.0, frequency=5.0)
    for _ in range(16):
        interp.execute("~(a ≈ b)")
    reached = interp.fields["a"].energy.quantum_coherence
    assert reached > 1.0
    with pytest.raises(DomainError):
        Quantity(reached, quantity_audit.CELL_TYPES["quantum_coherence"])


# --- the falsification harness ---------------------------------------------

def test_extractor_recovers_binding_topology():
    sites = taxonomy_lab.extract([taxonomy_lab.__file__])
    assert sites
    by_name = {s.name for s in sites}
    assert "AXES" in by_name                      # module-level constant
    accumulators = [s for s in sites if s.augmented]
    assert accumulators                           # x += ... shape detected


def test_degenerate_axis_pair_reports_no_data_not_a_p_value(capsys):
    # regression: a constant axis gives H=0, so U is nan; nan fails every
    # `>=` in the null loop, which pinned p at 1/(trials+1) and reported
    # every degenerate pair as a significant coupling
    rows = [{"axes": {a: "EXTENSIVE" if a == "extensivity" else "MONOTONE"
                      for a in taxonomy_lab.AXES}} for _ in range(20)]
    results = taxonomy_lab.experiment_orthogonality(rows, trials=50)
    assert results
    assert all(verdict == "degenerate" for *_, verdict in results)
    assert all(p is None for *_, p, _ in results)
    assert "cannot test" in capsys.readouterr().out


def test_orthogonality_detects_a_genuinely_redundant_axis():
    # extensivity perfectly determines conservation here, and both vary
    rows = []
    for i in range(40):
        extensive = i % 2 == 0
        axes = {a: "NONE" for a in taxonomy_lab.AXES}
        axes["extensivity"] = "EXTENSIVE" if extensive else "INTENSIVE"
        axes["conservation"] = "CONSERVED" if extensive else "PRODUCIBLE"
        rows.append({"axes": axes})
    results = taxonomy_lab.experiment_orthogonality(rows, trials=200)
    pair = next(r for r in results
                if {r[0], r[1]} == {"extensivity", "conservation"})
    assert pair[5] == "REDUNDANT — collapse these"


def test_residue_probe_is_load_bearing_under_permutation():
    probe = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "residue_probe.py")
    verdicts = taxonomy_lab.experiment_residue(probe, ["SPEC_A", "SPEC_B"])
    assert verdicts is not None
    assert not all(verdicts), "permuting a dereferenced label must change output"


def test_residue_probe_identity_use_survives_permutation():
    import residue_probe
    # equality and distinctness consult no property of the string, so these
    # are the parts the residue policy correctly describes as inert
    assert residue_probe.identity_only() == {"distinct": 2, "same": False}


# --- the adversarial corpus ------------------------------------------------

def test_corpus_controls_are_mirror_images():
    import adversarial_corpus as AC
    credulous = AC.score(AC.credulous_reducer, verbose=False)
    null = AC.score(AC.null_reducer, verbose=False)
    # the corpus is balanced: forcing everything and refusing everything
    # must fail by the same amount in opposite directions
    assert credulous["FORCED_FIT"] == null["MISSED_GROUNDING"]
    assert credulous["MISSED_GROUNDING"] == null["FORCED_FIT"] == 0
    # neither control can abstain, so both fail the calibration cases
    assert credulous["OVERCONFIDENT"] == null["OVERCONFIDENT"] == 3


def test_corpus_has_cases_pointing_both_directions():
    import adversarial_corpus as AC
    keys = [c.key_grounded for c in AC.CORPUS]
    assert True in keys and False in keys and None in keys


def test_pretype_cannot_tell_a_uuid_from_a_geohash():
    # the corpus's central pair: same surface type, opposite answers.
    # pretype fires one rule on "a string was assigned" and so returns
    # identical inference for both — it scores 50% here by construction
    import adversarial_corpus as AC
    by_id = {c.cid: c for c in AC.CORPUS}
    uuid_axes = AC.pretype_reducer(by_id["I3"].source, "user_uuid").axes
    geohash_axes = AC.pretype_reducer(by_id["R1"].source, "cell").axes
    assert uuid_axes == geohash_axes
    assert by_id["I3"].key_grounded != by_id["R1"].key_grounded


def test_pretype_abstention_is_a_read_count_threshold_not_calibration():
    # OVERCONFIDENT=0 looks like calibration; it is the n_reads>1 cutoff.
    # one more read of the same name, no change in decidability, flips it
    import adversarial_corpus as AC
    u2 = next(c for c in AC.CORPUS if c.cid == "U2")
    assert AC.pretype_reducer(u2.source, "rate").grounded is None
    assert AC.pretype_reducer(u2.source + "log(rate)\n", "rate").grounded is True


def test_pretype_is_mildly_physics_biased_not_balanced():
    import adversarial_corpus as AC
    tally = AC.score(AC.pretype_reducer, verbose=False)
    assert tally["FORCED_FIT"] > tally["MISSED_GROUNDING"]
    # it has no residue verdict at all, so it can never miss a grounding
    assert tally["MISSED_GROUNDING"] == 0


# --- shared conformance across implementations -----------------------------

def _conformance_ids():
    import taxonomy_conformance as tc
    return [(a.__name__, r.rid) for a in tc.ADAPTERS for r in tc.RULES]


@pytest.mark.parametrize("adapter_name,rule_id", _conformance_ids())
def test_every_implementation_satisfies_every_taxonomy_rule(adapter_name, rule_id):
    # One spec, run against both implementations. Neither is the reference:
    # quantity_checker was missing the relative/monotone/residue rules, and
    # quantity allowed adding intensives with `+` while total() rejected it.
    import taxonomy_conformance as tc
    adapter = next(a for a in tc.ADAPTERS if a.__name__ == adapter_name)()
    rule = next(r for r in tc.RULES if r.rid == rule_id)
    assert rule.check(adapter), f"{adapter.name} violates: {rule.statement}"


def test_declared_capabilities_actually_exist():
    import taxonomy_conformance as tc
    for name, entries in tc.capabilities().items():
        for label, present in entries:
            assert present, f"{name} claims {label!r} but it is missing"


def test_each_implementation_has_capabilities_the_other_lacks():
    # the reason both exist: they answer different questions
    import taxonomy_conformance as tc
    caps = tc.CAPABILITIES
    assert caps["quantity.py"] and caps["quantity_checker.py"]
    labels_a = {label for label, _ in caps["quantity.py"]}
    labels_b = {label for label, _ in caps["quantity_checker.py"]}
    assert labels_a - labels_b and labels_b - labels_a


# --- the auditor contract: coverage is not a pass rate ---------------------

def test_every_declared_cell_gets_an_axis_record():
    # nothing is omitted silently: a declared cell either reports a measured
    # delta or reports itself unmeasured
    for row in quantity_audit.audit():
        cells = {a.cell for a in row["axes"]}
        assert cells == set(quantity_audit.CELL_TYPES)


def test_unmeasured_axes_never_count_as_a_pass():
    for row in quantity_audit.audit():
        for axis in row["axes"]:
            if not axis.measured:
                assert axis.ok is None       # not True, not False
                assert axis.detail           # and it says why


def test_every_axis_record_declares_its_boundary():
    # "conservation over WHAT system" must always be answered
    for row in quantity_audit.audit():
        for axis in row["axes"]:
            assert axis.boundary


def test_measured_axes_carry_a_signed_delta():
    for row in quantity_audit.audit():
        for axis in row["axes"]:
            if axis.measured:
                assert isinstance(axis.delta, float)


def test_phase_angle_is_reported_unmeasured_not_passing():
    assert "phase_angle" in quantity_audit.UNMEASURED
    row = quantity_audit.audit()[0]
    phase = next(a for a in row["axes"] if a.cell == "phase_angle")
    assert phase.measured is False
    # the reason is the missing CYCLIC domain value, not an oversight
    assert "cyclic" in phase.detail.lower()


def test_the_unmeasured_axis_hides_a_real_bug():
    # resonate_with takes a linear mean of a cyclic quantity, so two fields
    # 20 degrees apart phase-lock to the opposite direction
    import math
    from cyclic_interpreter import CyclicalInterpreter
    interp = CyclicalInterpreter()
    interp.create_field("a", 100.0, frequency=5.0)
    interp.create_field("b", 100.0, frequency=5.0)
    interp.fields["a"].energy.phase_angle = math.radians(10)
    interp.fields["b"].energy.phase_angle = math.radians(350)
    interp.execute("~(a ≈ b)")
    locked = math.degrees(interp.fields["a"].energy.phase_angle) % 360
    # the circular mean of 10 and 350 is 0; a linear mean gives 180
    assert abs(locked - 180.0) < 1.0, locked


# --- the claim audit composes with the corpus ------------------------------

def test_claim_audit_verdicts_are_from_the_declared_vocabulary():
    import claim_audit_spin as ca
    allowed = {"VERIFIED", "SOURCE_OK_MECH_FALSE", "CATEGORY_ERROR",
               "FORBIDDEN", "KNOWN_ART", "UNDECIDABLE"}
    assert ca.CLAIMS
    for claim in ca.CLAIMS:
        assert claim.verdict in allowed
        assert claim.why


def test_every_non_verified_claim_carries_a_fix():
    import claim_audit_spin as ca
    for claim in ca.CLAIMS:
        if claim.verdict != "VERIFIED":
            assert claim.fix, f"{claim.cid} has no stated remedy"
