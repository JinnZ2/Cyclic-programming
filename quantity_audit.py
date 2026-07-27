# quantity_audit.py — types the interpreter's cells and reports what leaks.
# CC0. stdlib + quantity.py + cyclic_interpreter.py.
#
# The taxonomy claims that typing a cell makes its constraints unnecessary to
# state and impossible to violate. This checks that claim against real code:
# it declares a QuantityType for each field of EnergyState, runs every
# interpreter operation, and reports which axis each one crosses.
#
# Operations are split by whether they are closed or open, because the two
# fail differently:
#
#   CLOSED — all participating cells are inside the operation, so the total
#            must be identical afterwards. Any drift is energy from nowhere.
#   OPEN   — the operation names an external source or sink (an input to
#            regenerate, a loss to decay). Drift is expected; what is missing
#            is a reservoir cell to debit, so the drift goes unaccounted.
#
# Run: python3 quantity_audit.py

from cyclic_interpreter import CyclicalInterpreter
from quantity import (
    Datum, DomainError, MonotonicityError,
    bounded_fraction, conserved_energy, entropy, relative_scale,
    DIMENSIONLESS,
)

TOLERANCE = 1e-9

# The type each EnergyState field would carry if the taxonomy were applied.
CELL_TYPES = {
    "total_energy":     conserved_energy("total_energy"),
    "entropy":          entropy("entropy"),
    "quantum_coherence": bounded_fraction("quantum_coherence"),
    "phase_angle":      relative_scale(DIMENSIONLESS, "phase_angle"),
}


def _snapshot(interp):
    """Totals and extremes across every field, for before/after comparison."""
    states = [f.energy for f in interp.fields.values()]
    return {
        "total_energy": sum(s.total_energy for s in states),
        "entropy": sum(s.entropy for s in states),
        "max_coherence": max((s.quantum_coherence for s in states), default=0.0),
        "min_coherence": min((s.quantum_coherence for s in states), default=0.0),
    }


def _violations(before, after, closed):
    """Check a before/after pair against the declared cell types."""
    found = []

    delta = after["total_energy"] - before["total_energy"]
    if closed:
        if abs(delta) > TOLERANCE:
            found.append((
                "CONSERVED", "total_energy",
                f"closed operation changed the total by {delta:+.4f}"))
    elif abs(delta) > TOLERANCE:
        found.append((
            "DEBIT_CREDIT", "total_energy",
            f"{delta:+.4f} appeared with no reservoir cell debited"))

    if after["entropy"] < before["entropy"] - TOLERANCE:
        found.append((
            "MONOTONE", "entropy",
            f"entropy fell by {before['entropy'] - after['entropy']:.4f}"))

    ceiling = CELL_TYPES["quantum_coherence"].ceiling
    floor = CELL_TYPES["quantum_coherence"].floor
    if after["max_coherence"] > ceiling + TOLERANCE:
        found.append((
            "BOUNDED[0,1]", "quantum_coherence",
            f"coherence reached {after['max_coherence']:.4f}"))
    if after["min_coherence"] < floor - TOLERANCE:
        found.append((
            "BOUNDED[0,1]", "quantum_coherence",
            f"coherence fell to {after['min_coherence']:.4f}"))

    return found


def _two_fields(energy=100.0, frequency=5.0):
    def setup():
        interp = CyclicalInterpreter()
        interp.create_field("a", energy, frequency=frequency)
        interp.create_field("b", energy, frequency=frequency)
        return interp
    return setup


# (label, closed?, setup, expression, repeats)
OPERATIONS = [
    ("bidirectional  ∇F(a↔b)", True,  _two_fields(), "∇F(a↔b)|∂E/∂t=0", 1),
    ("directed       COBOL:MOVE", True, _two_fields(), "COBOL:MOVE 20 FROM a TO b", 1),
    ("spatial        ∇spatial", True,  _two_fields(), "∇spatial(a, b)", 1),
    ("entangle       ⊗(a,b)", True,   _two_fields(), "⊗(a, b)", 1),
    ("symbiosis      ∇∇(a⇄b)", True,  _two_fields(), "∇∇(a⇄b)", 1),
    ("resonance      ~(a≈b)", True,   _two_fields(), "~(a ≈ b)", 1),
    ("resonance ×16  ~(a≈b)", True,   _two_fields(), "~(a ≈ b)", 16),
    ("regenerate     ∮regenerate", False, _two_fields(), "∮regenerate(a, 30)", 1),
    ("decay          ∂decay", False,  _two_fields(), "∂decay(a, 0.05)", 1),
    ("phase          ∂phase", False,  _two_fields(200.0), "∂phase(a, gas)", 1),
]


def audit():
    """Run every operation and collect its violations."""
    results = []
    for label, closed, setup, expression, repeats in OPERATIONS:
        interp = setup()
        before = _snapshot(interp)
        for _ in range(repeats):
            interp.execute(expression)
        after = _snapshot(interp)
        results.append({
            "label": label,
            "closed": closed,
            "before": before,
            "after": after,
            "violations": _violations(before, after, closed),
        })
    return results


def main():
    results = audit()

    print("Interpreter operations checked against the quantity taxonomy")
    print("=" * 78)
    print(f"{'operation':<26} {'kind':<7} {'energy':>18}  axis crossed")
    print("-" * 78)

    for row in results:
        kind = "closed" if row["closed"] else "open"
        movement = (f"{row['before']['total_energy']:.1f}"
                    f" -> {row['after']['total_energy']:.1f}")
        if not row["violations"]:
            print(f"{row['label']:<26} {kind:<7} {movement:>18}  ok")
            continue
        first = row["violations"][0]
        print(f"{row['label']:<26} {kind:<7} {movement:>18}  {first[0]}: {first[2]}")
        for axis, _, detail in row["violations"][1:]:
            print(f"{'':<26} {'':<7} {'':>18}  {axis}: {detail}")

    print("-" * 78)
    clean = sum(1 for r in results if not r["violations"])
    print(f"{clean}/{len(results)} operations satisfy their declared cell types")
    print()

    axes = {}
    for row in results:
        for axis, cell, _ in row["violations"]:
            axes.setdefault((axis, cell), []).append(row["label"].split()[0])
    if axes:
        print("By axis:")
        for (axis, cell), ops in sorted(axes.items()):
            print(f"  {axis:<14} {cell:<18} {', '.join(sorted(set(ops)))}")
    return 0


# --- self-test -------------------------------------------------------------

def _t_bidirectional_exchange_is_clean():
    # the one operation the interpreter already checks at runtime
    row = next(r for r in audit() if r["label"].startswith("bidirectional"))
    assert row["violations"] == [], row["violations"]


def _t_resonance_creates_energy_in_a_closed_pair():
    row = next(r for r in audit() if r["label"].startswith("resonance      "))
    assert any(axis == "CONSERVED" for axis, _, _ in row["violations"])
    assert row["after"]["total_energy"] > row["before"]["total_energy"]


def _t_repeated_resonance_breaches_the_coherence_ceiling():
    row = next(r for r in audit() if r["label"].startswith("resonance ×16"))
    assert any(axis == "BOUNDED[0,1]" for axis, _, _ in row["violations"])
    assert row["after"]["max_coherence"] > 1.0


def _t_regenerate_credits_without_a_reservoir():
    row = next(r for r in audit() if r["label"].startswith("regenerate"))
    assert any(axis == "DEBIT_CREDIT" for axis, _, _ in row["violations"])


def _t_typed_cells_would_have_refused_the_coherence_value():
    # the same number the interpreter happily stores, offered to a typed cell
    from quantity import Quantity
    interp = CyclicalInterpreter()
    interp.create_field("a", 100.0, frequency=5.0)
    interp.create_field("b", 100.0, frequency=5.0)
    for _ in range(16):
        interp.execute("~(a ≈ b)")
    reached = interp.fields["a"].energy.quantum_coherence
    assert reached > 1.0
    try:
        Quantity(reached, CELL_TYPES["quantum_coherence"])
    except DomainError:
        return
    raise AssertionError("a BOUNDED[0,1] cell must refuse this value")


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    raise SystemExit(main())
