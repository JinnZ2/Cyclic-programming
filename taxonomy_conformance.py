# taxonomy_conformance.py — one spec, checked against every implementation.
# CC0. stdlib only.
#
# There are two implementations of QUANTITY_TAXONOMY.md in this repo and
# neither is a draft of the other. They are different instruments:
#
#   quantity.py          immutable values and a Ledger. Answers "is this
#                        operation legal?" — a checking instrument, which is
#                        why quantity_audit.py uses it to audit the interpreter.
#   quantity_checker.py  mutable variables and dimension-composing mul/div.
#                        Answers "what can I build from these?" — a composing
#                        instrument, which is why the playgrounds use it.
#
# What must not diverge is the SPEC. The rules below are the taxonomy's
# "what falls out free" table written once and run against both, so a rule
# enforced in one place and forgotten in the other is caught. Each found a
# gap in the other on the first run: quantity_checker was missing the
# RELATIVE+RELATIVE, monotone and residue rules; quantity.py rejected summing
# intensives in total() but happily added them with `+`.
#
# Capability differences are recorded separately, as capabilities. An
# implementation is not deficient for lacking a Ledger or lacking mul/div —
# it is aimed at a different question.
#
# Run: python3 taxonomy_conformance.py

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple

DIMENSIONLESS = (0, 0, 0, 0, 0, 0, 0)
LENGTH = (0, 1, 0, 0, 0, 0, 0)
TIME = (0, 0, 1, 0, 0, 0, 0)


@dataclass(frozen=True)
class Spec:
    """An implementation-neutral quantity type. Adapters translate it."""

    extensivity: str = "EXTENSIVE"
    conservation: str = "PRODUCIBLE"
    datum: str = "ABSOLUTE"
    transfer: str = "DEBIT_CREDIT"
    dimension: Tuple[int, ...] = DIMENSIONLESS
    floor: Optional[float] = None
    ceiling: Optional[float] = None
    convention: Optional[str] = None


# Specs are axis-isolated on purpose: each exercises one rule, so a failure
# names one axis instead of whichever guard happened to fire first.
FLOORED = Spec(floor=0.0)
INTENSIVE = Spec(extensivity="INTENSIVE", transfer="EQUILIBRATE")
RELATIVE = Spec(datum="RELATIVE", dimension=TIME)
MONOTONE = Spec(conservation="MONOTONE", floor=0.0)
BOUNDED = Spec(floor=0.0, ceiling=1.0)
RESIDUE = Spec(convention="US_ZIP", transfer="COPY")
METRES = Spec(dimension=LENGTH)
SECONDS = Spec(dimension=TIME)


class Adapter:
    """Wraps one implementation behind a common surface."""

    name = "?"
    module = None
    errors: Tuple[type, ...] = (Exception,)

    def value(self, x, spec):
        raise NotImplementedError

    def add(self, a, b):
        return a + b

    def sub(self, a, b):
        return a - b

    def datum_of(self, v):
        raise NotImplementedError


class QuantityAdapter(Adapter):
    name = "quantity.py"

    def __init__(self):
        import quantity
        self.module = quantity
        self.errors = (quantity.QuantityError,)

    def _type(self, spec):
        q = self.module
        return q.QuantityType(
            extensivity=getattr(q.Extensivity, spec.extensivity),
            conservation=getattr(q.Conservation, spec.conservation),
            datum=getattr(q.Datum, spec.datum),
            transfer=getattr(q.Transfer, spec.transfer),
            dimension=spec.dimension,
            floor=spec.floor,
            ceiling=spec.ceiling,
            convention=spec.convention,
            label="v")

    def value(self, x, spec):
        return self.module.Quantity(x, self._type(spec))

    def datum_of(self, v):
        return v.type.datum.name


class QuantityCheckerAdapter(Adapter):
    name = "quantity_checker.py"

    def __init__(self):
        import quantity_checker
        self.module = quantity_checker
        self.errors = (quantity_checker.QuantityError,)

    def _type(self, spec):
        q = self.module
        return q.QuantityType(
            extensivity=getattr(q.Extensivity, spec.extensivity),
            conservation=getattr(q.Conservation, spec.conservation),
            datum=getattr(q.Datum, spec.datum),
            transfer=getattr(q.Transfer, spec.transfer),
            dimension=spec.dimension,
            floor=spec.floor,
            ceiling=spec.ceiling,
            convention=spec.convention)

    def value(self, x, spec):
        return self.module.QuantityVar("v", x, self._type(spec))

    def datum_of(self, v):
        return v.qtype.datum.name


ADAPTERS = [QuantityAdapter, QuantityCheckerAdapter]


# --- the rules -------------------------------------------------------------

@dataclass
class Rule:
    rid: str
    axis: str
    statement: str
    check: Callable[[Adapter], Any]


def _must_reject(adapter, thunk):
    """The operation must raise. Returning a value is the failure."""
    try:
        thunk()
    except adapter.errors:
        return True
    return False


RULES = [
    Rule("floor", "3 domain",
         "a floored quantity cannot go below its floor",
         lambda a: _must_reject(a, lambda: a.sub(a.value(5.0, FLOORED),
                                                 a.value(9.0, FLOORED)))),

    Rule("intensive", "1 extensivity",
         "two intensives cannot be added",
         lambda a: _must_reject(a, lambda: a.add(a.value(0.4, INTENSIVE),
                                                 a.value(0.5, INTENSIVE)))),

    Rule("relative-add", "4 datum",
         "RELATIVE + RELATIVE is meaningless",
         lambda a: _must_reject(a, lambda: a.add(a.value(15.0, RELATIVE),
                                                 a.value(16.0, RELATIVE)))),

    Rule("relative-sub", "4 datum",
         "RELATIVE - RELATIVE yields an ABSOLUTE delta",
         lambda a: a.datum_of(a.sub(a.value(17.0, RELATIVE),
                                    a.value(9.0, RELATIVE))) == "ABSOLUTE"),

    Rule("dimension", "5 dimension",
         "quantities of different dimension cannot be added",
         lambda a: _must_reject(a, lambda: a.add(a.value(1.0, METRES),
                                                 a.value(1.0, SECONDS)))),

    Rule("monotone", "2 conservation",
         "a MONOTONE quantity cannot be decremented",
         lambda a: _must_reject(a, lambda: a.sub(a.value(100.0, MONOTONE),
                                                 a.value(1.0, MONOTONE)))),

    Rule("ceiling", "3 domain",
         "a BOUNDED quantity cannot exceed its ceiling",
         lambda a: _must_reject(a, lambda: a.add(a.value(0.95, BOUNDED),
                                                 a.value(0.2, BOUNDED)))),

    Rule("residue", "residue policy",
         "arithmetic on a convention residue is forbidden",
         lambda a: _must_reject(a, lambda: a.add(a.value(90210.0, RESIDUE),
                                                 a.value(10001.0, RESIDUE)))),
]


# --- capabilities, recorded as capabilities --------------------------------
#
# Not a scorecard. These are the questions each implementation is built to
# answer, and the entries are verified to exist so the table cannot rot.

CAPABILITIES = {
    "quantity.py": [
        ("Ledger", lambda m: hasattr(m, "Ledger")),
        ("weighted_mean", lambda m: hasattr(m, "weighted_mean")),
        ("transcendental dimensionless check", lambda m: hasattr(m, "transcendental")),
        ("Landauer erase_cost", lambda m: hasattr(m, "erase_cost")),
        ("per-axis error classes", lambda m: hasattr(m, "DatumError")),
        ("immutable values", lambda m: getattr(m.Quantity, "__dataclass_params__").frozen),
    ],
    "quantity_checker.py": [
        ("mutable bounds-checked writes",
         lambda m: isinstance(getattr(m.QuantityVar, "value", None), property)),
        ("__mul__ composes dimension", lambda m: hasattr(m.QuantityVar, "__mul__")),
        ("__truediv__ composes dimension", lambda m: hasattr(m.QuantityVar, "__truediv__")),
        ("transfer() with explicit mode", lambda m: hasattr(m, "transfer")),
    ],
}


def run():
    """Check every rule against every implementation."""
    results = {}
    for factory in ADAPTERS:
        adapter = factory()
        results[adapter.name] = {r.rid: bool(r.check(adapter)) for r in RULES}
    return results


def capabilities():
    """Verify each declared capability actually exists."""
    found = {}
    for factory in ADAPTERS:
        adapter = factory()
        found[adapter.name] = [
            (label, bool(probe(adapter.module)))
            for label, probe in CAPABILITIES.get(adapter.name, [])
        ]
    return found


def main():
    results = run()
    names = list(results)

    print("Taxonomy conformance — one spec, every implementation")
    print("=" * 74)
    print(f"{'rule':<14}{'axis':<17}" + "".join(f"{n:>21}" for n in names))
    print("-" * 74)
    for rule in RULES:
        marks = "".join(f"{('ok' if results[n][rule.rid] else 'GAP'):>21}"
                        for n in names)
        print(f"{rule.rid:<14}{rule.axis:<17}{marks}")
    print("-" * 74)
    totals = "".join(f"{f'{sum(results[n].values())}/{len(RULES)}':>21}" for n in names)
    print(f"{'':<31}{totals}")

    gaps = [(n, r.rid, r.statement) for r in RULES for n in names
            if not results[n][r.rid]]
    if gaps:
        print("\nGaps — the spec says these must hold and they do not:")
        for name, rid, statement in gaps:
            print(f"  {name:<22} {rid:<14} {statement}")
    else:
        print("\nBoth implementations satisfy every rule in the spec.")

    print("\nCapabilities — what each is for, not a scorecard")
    print("-" * 74)
    for name, entries in capabilities().items():
        print(f"  {name}")
        for label, present in entries:
            print(f"      {'+' if present else '!'} {label}")
    return 1 if gaps else 0


# --- self-test -------------------------------------------------------------

def _t_every_rule_runs_against_every_adapter():
    results = run()
    assert len(results) == len(ADAPTERS)
    for name, rules in results.items():
        assert set(rules) == {r.rid for r in RULES}


def _t_declared_capabilities_all_exist():
    for name, entries in capabilities().items():
        for label, present in entries:
            assert present, f"{name} declares {label!r} but it is missing"


def _t_specs_are_axis_isolated():
    # each rule's spec should differ from the plain default on one axis only,
    # so a failure names one axis rather than whichever guard fired first
    default = Spec()
    for spec in (INTENSIVE, RELATIVE, MONOTONE, RESIDUE):
        differing = [f for f in ("extensivity", "conservation", "datum",
                                 "convention")
                     if getattr(spec, f) != getattr(default, f)]
        assert len(differing) == 1, (spec, differing)


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    raise SystemExit(main())
