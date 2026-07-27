# quantity.py — physics-quantity types for substrate-anchored constraint checking.
# CC0. stdlib only.
#
# The claim: constraints are not programmer intent, they are properties of
# what KIND of quantity a cell holds. Type the quantity and the constraints
# fall out — no cell needs a comment saying "never negative", and no layer
# above can silently leak.
#
# A NAME reduces to (BINDING_TOPOLOGY, QUANTITY_TYPE, CONVENTION_RESIDUE).
# This module encodes the QUANTITY_TYPE part: seven axes, each of which
# forbids something specific. CONVENTION_RESIDUE is tagged and left inert —
# it means nothing to the substrate, which is why it is carried verbatim
# rather than translated.
#
# See QUANTITY_TAXONOMY.md for the vocabulary this implements.

import math
from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Optional, Sequence, Tuple


# --- errors ----------------------------------------------------------------
# One class per axis, so a caught violation names which axis was crossed.

class QuantityError(Exception):
    """Base for every constraint this module enforces."""


class ExtensivityError(QuantityError):
    """AXIS 1 — summing an intensive quantity."""


class ConservationError(QuantityError):
    """AXIS 2 — an unbalanced write to a conserved total."""


class MonotonicityError(QuantityError):
    """AXIS 2 — a monotone quantity moved backwards."""


class DomainError(QuantityError):
    """AXIS 3 — value left its floor/ceiling/bounds."""


class DatumError(QuantityError):
    """AXIS 4 — arithmetic that a relative zero makes meaningless."""


class DimensionError(QuantityError):
    """AXIS 5 — mismatched or non-dimensionless units."""


class TransferError(QuantityError):
    """AXIS 6 — a move the transfer mode does not permit."""


class ConventionError(QuantityError):
    """Residue — arithmetic on a value that is a social fact, not a magnitude."""


# --- the seven axes --------------------------------------------------------

class Extensivity(Enum):
    EXTENSIVE = auto()   # adds over subsystems: mass, energy, count, money
    INTENSIVE = auto()   # does not: temperature, density, rate, price


class Conservation(Enum):
    CONSERVED  = auto()  # total invariant under transfer (zero-sum)
    MONOTONE   = auto()  # only ever increases: entropy, counters, clocks
    PRODUCIBLE = auto()  # freely created/destroyed: log lines, requests


class Datum(Enum):
    ABSOLUTE = auto()    # zero is physical: kelvin, mass, count
    RELATIVE = auto()    # zero is a convention: celsius, epoch, x-position


class Transfer(Enum):
    DEBIT_CREDIT = auto()  # source loses exactly what target gains
    COPY         = auto()  # source unchanged, target gains — INFORMATION
    CONSUME      = auto()  # destroyed on read: token, queue message
    EQUILIBRATE  = auto()  # cannot move, only levels out — intensive


class CostFloor(Enum):
    ERASE     = auto()   # >= kT ln2 per bit destroyed (Landauer)
    COPY      = auto()   # ~0, reversible in principle
    TRANSFORM = auto()   # >= entropy produced by the map


# Dimension vectors: (M, L, T, I, Theta, N, J)
DIMENSIONLESS = (0, 0, 0, 0, 0, 0, 0)
MASS          = (1, 0, 0, 0, 0, 0, 0)
LENGTH        = (0, 1, 0, 0, 0, 0, 0)
TIME          = (0, 0, 1, 0, 0, 0, 0)
TEMPERATURE   = (0, 0, 0, 0, 1, 0, 0)
ENERGY        = (1, 2, -2, 0, 0, 0, 0)

_DIM_SYMBOLS = ("M", "L", "T", "I", "Θ", "N", "J")

# Boltzmann constant, for the Landauer floor. Joules per kelvin.
BOLTZMANN = 1.380649e-23


def format_dimension(dimension):
    """Render a dimension vector as e.g. 'M·L²·T⁻²', or '1' when dimensionless."""
    parts = []
    for symbol, power in zip(_DIM_SYMBOLS, dimension):
        if power == 0:
            continue
        parts.append(symbol if power == 1 else f"{symbol}^{power}")
    return "·".join(parts) if parts else "1"


@dataclass(frozen=True)
class QuantityType:
    """What kind of thing a cell holds. Every constraint derives from this."""

    extensivity:  Extensivity
    conservation: Conservation
    datum:        Datum
    transfer:     Transfer
    dimension:    Tuple[int, ...] = DIMENSIONLESS
    floor:        Optional[float] = None
    ceiling:      Optional[float] = None
    signed:       bool = True
    cost_floor:   CostFloor = CostFloor.TRANSFORM
    convention:   Optional[str] = None   # residue tag — non-physical, inert
    label:        str = ""

    def __post_init__(self):
        if self.floor is not None and self.ceiling is not None:
            if self.floor > self.ceiling:
                raise DomainError(
                    f"floor {self.floor} above ceiling {self.ceiling}")
        if len(self.dimension) != 7:
            raise DimensionError(
                f"dimension must be a 7-vector (M,L,T,I,Θ,N,J), got "
                f"{len(self.dimension)} components")

    @property
    def is_residue(self):
        """True when this is a social fact rather than a magnitude."""
        return self.convention is not None

    def describe(self):
        bits = [self.extensivity.name, self.conservation.name,
                self.datum.name, self.transfer.name,
                format_dimension(self.dimension)]
        if self.floor is not None or self.ceiling is not None:
            low = "-inf" if self.floor is None else self.floor
            high = "+inf" if self.ceiling is None else self.ceiling
            bits.append(f"[{low},{high}]")
        if self.convention:
            bits.append(f"convention={self.convention}")
        return " / ".join(str(b) for b in bits)


# --- the value wrapper -----------------------------------------------------

@dataclass(frozen=True)
class Quantity:
    """
    A magnitude plus its type. Every operation is checked against the axes;
    an illegal one raises rather than producing a number nobody can trust.
    """

    value: float
    type:  QuantityType

    def __post_init__(self):
        self._check_domain(self.value)

    def _check_domain(self, value):
        t = self.type
        if t.floor is not None and value < t.floor - 1e-12:
            raise DomainError(
                f"{t.label or 'quantity'} = {value} below floor {t.floor}"
                + (" (no negative water)" if t.floor == 0 else ""))
        if t.ceiling is not None and value > t.ceiling + 1e-12:
            raise DomainError(
                f"{t.label or 'quantity'} = {value} above ceiling {t.ceiling}")
        if not t.signed and value < 0:
            raise DomainError(f"{t.label or 'quantity'} = {value} is unsigned")

    def _reject_if_residue(self, operation):
        if self.type.is_residue:
            raise ConventionError(
                f"{operation} is meaningless on convention="
                f"{self.type.convention}; it is a label, not a magnitude")

    def _require_same_type(self, other, operation):
        if not isinstance(other, Quantity):
            raise QuantityError(f"cannot {operation} Quantity and {type(other).__name__}")
        self._reject_if_residue(operation)
        other._reject_if_residue(operation)
        if self.type.dimension != other.type.dimension:
            raise DimensionError(
                f"cannot {operation} {format_dimension(self.type.dimension)} and "
                f"{format_dimension(other.type.dimension)}")

    def __add__(self, other):
        self._require_same_type(other, "add")
        # AXIS 4: two relative zeros have no common origin, so their sum
        # denominates nothing. 3pm + 4pm is not a time.
        if (self.type.datum is Datum.RELATIVE
                and other.type.datum is Datum.RELATIVE):
            raise DatumError(
                "RELATIVE + RELATIVE is meaningless — both zeros are "
                "conventions, so the sum has no origin")
        return Quantity(self.value + other.value, self.type)

    def __sub__(self, other):
        self._require_same_type(other, "subtract")
        # AXIS 4: the conventional origins cancel, so a difference of two
        # relatives is an absolute delta — and a delta may be negative even
        # when both operands were floored.
        if (self.type.datum is Datum.RELATIVE
                and other.type.datum is Datum.RELATIVE):
            delta_type = replace(
                self.type, datum=Datum.ABSOLUTE, floor=None, ceiling=None,
                signed=True, label=f"Δ{self.type.label}" if self.type.label else "")
            return Quantity(self.value - other.value, delta_type)
        # AXIS 2: a monotone quantity moving backwards is a fault, not a value.
        if self.type.conservation is Conservation.MONOTONE and other.value > 0:
            raise MonotonicityError(
                f"{self.type.label or 'quantity'} is MONOTONE; "
                f"decrementing by {other.value} is a fault (clock rollback)")
        return Quantity(self.value - other.value, self.type)

    def scaled_by(self, factor):
        """Multiply by a dimensionless scalar, keeping the type."""
        self._reject_if_residue("scale")
        return Quantity(self.value * factor, self.type)

    def __lt__(self, other):
        self._reject_if_residue("ordering")
        other._reject_if_residue("ordering")
        self._require_same_type(other, "compare")
        return self.value < other.value

    def __repr__(self):
        name = self.type.label or "Quantity"
        unit = format_dimension(self.type.dimension)
        return f"{name}({self.value}{'' if unit == '1' else ' ' + unit})"


# --- operations the axes forbid or reshape ---------------------------------

def total(quantities):
    """
    Sum a collection. Legal only for EXTENSIVE quantities.

    Averaging an intensive is the classic silent-wrong answer: the mean of
    two tank temperatures is not the temperature of the combined tank unless
    the tanks are the same size. Use weighted_mean and supply the weight.
    """
    quantities = list(quantities)
    if not quantities:
        raise QuantityError("cannot total an empty collection: no type to carry")
    first = quantities[0].type
    for q in quantities:
        if q.type.extensivity is Extensivity.INTENSIVE:
            raise ExtensivityError(
                f"cannot sum INTENSIVE {q.type.label or 'quantity'} — "
                "intensives combine only as extensive-weighted averages; "
                "use weighted_mean()")
        if q.type.dimension != first.dimension:
            raise DimensionError(
                f"cannot total {format_dimension(first.dimension)} with "
                f"{format_dimension(q.type.dimension)}")
        if q.type.datum is Datum.RELATIVE:
            raise DatumError(
                f"cannot total RELATIVE {q.type.label or 'quantity'} — "
                "no common origin")
    return Quantity(sum(q.value for q in quantities), first)


def weighted_mean(pairs):
    """
    Combine intensives against their extensive weights.

    pairs is a sequence of (intensive, extensive_weight). This is the only
    legal way to average an intensive quantity.
    """
    pairs = list(pairs)
    if not pairs:
        raise QuantityError("cannot average an empty collection")
    intensive_type = pairs[0][0].type
    for intensive, weight in pairs:
        if intensive.type.extensivity is not Extensivity.INTENSIVE:
            raise ExtensivityError(
                "weighted_mean is for INTENSIVE quantities; "
                f"{intensive.type.label or 'this'} is EXTENSIVE — use total()")
        if weight.type.extensivity is not Extensivity.EXTENSIVE:
            raise ExtensivityError("the weight must be EXTENSIVE")
        if intensive.type.dimension != intensive_type.dimension:
            raise DimensionError("cannot average across dimensions")
    total_weight = sum(w.value for _, w in pairs)
    if total_weight == 0:
        raise QuantityError("total weight is zero; the average is undefined")
    return Quantity(
        sum(q.value * w.value for q, w in pairs) / total_weight,
        intensive_type)


def transcendental(fn, quantity):
    """
    Apply log/exp/sin. AXIS 5 requires a dimensionless argument — the series
    expansion would otherwise add metres to square metres.
    """
    quantity._reject_if_residue("transcendental")
    if quantity.type.dimension != DIMENSIONLESS:
        raise DimensionError(
            f"{fn.__name__} requires a DIMENSIONLESS argument, got "
            f"{format_dimension(quantity.type.dimension)}")
    return Quantity(fn(quantity.value),
                    replace(quantity.type, floor=None, ceiling=None))


def erase_cost(bits, temperature_kelvin=300.0):
    """
    Landauer floor: the joules that destroying `bits` of information must
    dissipate. This is the price COPY defers and ERASE finally pays.
    """
    if bits < 0:
        raise DomainError("cannot erase a negative number of bits")
    return bits * BOLTZMANN * temperature_kelvin * math.log(2)


# --- the ledger: CONSERVED + DEBIT_CREDIT ----------------------------------

class Ledger:
    """
    Named cells holding one conserved quantity, where the total is invariant.

    This is the piece a system creates energy without: if the only way to
    raise a cell is transfer(), then every credit has a matching debit and an
    orphan credit cannot be written. Conservation stops being a check that
    runs afterwards and becomes a thing the API cannot express a violation of.
    """

    def __init__(self, quantity_type, name="ledger"):
        if quantity_type.conservation is not Conservation.CONSERVED:
            raise ConservationError(
                "a Ledger holds CONSERVED quantities; "
                f"{quantity_type.label or 'this type'} is "
                f"{quantity_type.conservation.name}")
        if quantity_type.transfer is not Transfer.DEBIT_CREDIT:
            raise TransferError(
                "a Ledger requires DEBIT_CREDIT transfer; "
                f"{quantity_type.transfer.name} cannot balance")
        self.type = quantity_type
        self.name = name
        self._cells = {}
        self._opening_total = 0.0
        self.journal = []

    def open_cell(self, cell, amount):
        """
        Endow a cell at creation. This is the only unbalanced write allowed,
        and it is recorded in the opening total so the invariant accounts
        for it rather than being blind to it.
        """
        if cell in self._cells:
            raise ConservationError(f"cell {cell!r} already exists")
        quantity = Quantity(amount, self.type)
        self._cells[cell] = quantity
        self._opening_total += quantity.value
        self.journal.append(("open", cell, quantity.value))
        return quantity

    def balance(self, cell):
        if cell not in self._cells:
            raise ConservationError(f"no such cell {cell!r}")
        return self._cells[cell]

    def transfer(self, source, target, amount):
        """
        Move `amount` from source to target as one paired write.

        Both sides land or neither does, so the total cannot drift. A move
        that would take the source below its floor is refused outright rather
        than silently clamped — clamping is how a ledger loses track.
        """
        if source == target:
            raise TransferError("cannot transfer a cell to itself")
        if amount < 0:
            raise TransferError(
                "transfer amount must be non-negative; "
                "reverse the source and target instead")
        debit = self.balance(source)
        credit = self.balance(target)
        remaining = debit.value - amount
        if self.type.floor is not None and remaining < self.type.floor - 1e-12:
            raise ConservationError(
                f"{source} holds {debit.value}, cannot yield {amount} "
                f"without breaching floor {self.type.floor}")
        self._cells[source] = Quantity(remaining, self.type)
        self._cells[target] = Quantity(credit.value + amount, self.type)
        self.journal.append(("transfer", (source, target), amount))
        return amount

    def total(self):
        return total(list(self._cells.values()))

    def check(self):
        """Assert the invariant. Raises if the total has drifted."""
        current = self.total().value
        if abs(current - self._opening_total) > 1e-9:
            raise ConservationError(
                f"{self.name} total drifted: opened at {self._opening_total}, "
                f"now {current}")
        return current

    def cells(self):
        return dict(self._cells)


# --- common types ----------------------------------------------------------

def conserved_energy(label="energy"):
    """Energy in a closed ledger: extensive, conserved, floored at zero."""
    return QuantityType(
        extensivity=Extensivity.EXTENSIVE,
        conservation=Conservation.CONSERVED,
        datum=Datum.ABSOLUTE,
        transfer=Transfer.DEBIT_CREDIT,
        dimension=ENERGY,
        floor=0.0,
        cost_floor=CostFloor.TRANSFORM,
        label=label)


def entropy(label="entropy"):
    """Monotone: it may rise, and a decrease is a fault rather than a value."""
    return QuantityType(
        extensivity=Extensivity.EXTENSIVE,
        conservation=Conservation.MONOTONE,
        datum=Datum.ABSOLUTE,
        transfer=Transfer.DEBIT_CREDIT,
        dimension=DIMENSIONLESS,
        floor=0.0,
        cost_floor=CostFloor.ERASE,
        label=label)


def bounded_fraction(label="fraction"):
    """A probability, ratio or coherence: intensive and hard-bounded to [0,1]."""
    return QuantityType(
        extensivity=Extensivity.INTENSIVE,
        conservation=Conservation.PRODUCIBLE,
        datum=Datum.ABSOLUTE,
        transfer=Transfer.EQUILIBRATE,
        dimension=DIMENSIONLESS,
        floor=0.0,
        ceiling=1.0,
        label=label)


def counter(label="count"):
    """A count: extensive, monotone, floored at zero, dimensionless."""
    return QuantityType(
        extensivity=Extensivity.EXTENSIVE,
        conservation=Conservation.MONOTONE,
        datum=Datum.ABSOLUTE,
        transfer=Transfer.DEBIT_CREDIT,
        dimension=DIMENSIONLESS,
        floor=0.0,
        signed=False,
        label=label)


def information(label="information"):
    """
    The quantity whose transfer does not debit the source.

    That asymmetry is the waste thesis in one type: copying is free, so
    nobody accounts for it, so it accumulates. Landauer restores the price
    at erase time, which is why cost_floor is ERASE and not COPY.
    """
    return QuantityType(
        extensivity=Extensivity.EXTENSIVE,
        conservation=Conservation.PRODUCIBLE,
        datum=Datum.ABSOLUTE,
        transfer=Transfer.COPY,
        dimension=DIMENSIONLESS,
        floor=0.0,
        cost_floor=CostFloor.ERASE,
        label=label)


def relative_scale(dimension, label="reading"):
    """A reading on a conventional zero: celsius, epoch time, x-position."""
    return QuantityType(
        extensivity=Extensivity.INTENSIVE,
        conservation=Conservation.PRODUCIBLE,
        datum=Datum.RELATIVE,
        transfer=Transfer.EQUILIBRATE,
        dimension=dimension,
        label=label)


def residue(tag, label="label"):
    """
    A social fact wearing a number's clothes: zip code, ISO country code.

    Not reducible, not physical. Tag it and stop — arithmetic and ordering
    are both rejected, which is the whole point of naming it.
    """
    return QuantityType(
        extensivity=Extensivity.EXTENSIVE,
        conservation=Conservation.PRODUCIBLE,
        datum=Datum.ABSOLUTE,
        transfer=Transfer.COPY,
        dimension=DIMENSIONLESS,
        convention=tag,
        label=label)


# --- self-test -------------------------------------------------------------

def _t_floored_quantity_rejects_underflow():
    water = Quantity(5.0, conserved_energy("water"))
    try:
        water - Quantity(9.0, conserved_energy("water"))
    except DomainError:
        return
    raise AssertionError("expected DomainError: there is no negative water")


def _t_intensive_cannot_be_summed():
    hot = Quantity(0.9, bounded_fraction("density"))
    try:
        total([hot, hot])
    except ExtensivityError:
        return
    raise AssertionError("expected ExtensivityError")


def _t_intensive_averages_against_extensive_weight():
    small = (Quantity(0.9, bounded_fraction("temp")), Quantity(1.0, counter("kg")))
    large = (Quantity(0.1, bounded_fraction("temp")), Quantity(9.0, counter("kg")))
    mixed = weighted_mean([small, large])
    # the big cold mass dominates; a naive mean would have said 0.5
    assert abs(mixed.value - 0.18) < 1e-9, mixed.value


def _t_relative_plus_relative_is_rejected():
    noon = Quantity(12.0, relative_scale(TIME, "clock"))
    try:
        noon + noon
    except DatumError:
        return
    raise AssertionError("expected DatumError: 3pm + 4pm is not a time")


def _t_relative_minus_relative_yields_absolute_delta():
    start = Quantity(9.0, relative_scale(TIME, "clock"))
    end = Quantity(17.0, relative_scale(TIME, "clock"))
    elapsed = end - start
    assert elapsed.value == 8.0
    assert elapsed.type.datum is Datum.ABSOLUTE     # the conventions cancelled
    assert (start - end).value == -8.0              # and the delta may be negative


def _t_dimension_mismatch_is_rejected():
    metres = Quantity(1.0, QuantityType(
        Extensivity.EXTENSIVE, Conservation.PRODUCIBLE, Datum.ABSOLUTE,
        Transfer.DEBIT_CREDIT, LENGTH, label="length"))
    seconds = Quantity(1.0, QuantityType(
        Extensivity.EXTENSIVE, Conservation.PRODUCIBLE, Datum.ABSOLUTE,
        Transfer.DEBIT_CREDIT, TIME, label="duration"))
    try:
        metres + seconds
    except DimensionError:
        return
    raise AssertionError("expected DimensionError (Mars Climate Orbiter class)")


def _t_monotone_cannot_run_backwards():
    clock = Quantity(100.0, entropy("clock"))
    try:
        clock - Quantity(1.0, entropy("clock"))
    except MonotonicityError:
        return
    raise AssertionError("expected MonotonicityError: clock rollback")


def _t_bounded_fraction_cannot_leave_its_interval():
    coherence = Quantity(0.95, bounded_fraction("coherence"))
    try:
        coherence + Quantity(0.2, bounded_fraction("coherence"))
    except DomainError:
        return
    raise AssertionError("expected DomainError: coherence cannot exceed 1")


def _t_transcendental_requires_dimensionless():
    joules = Quantity(2.0, conserved_energy())
    try:
        transcendental(math.log, joules)
    except DimensionError:
        pass
    else:
        raise AssertionError("expected DimensionError")
    ratio = Quantity(1.0, bounded_fraction("ratio"))
    assert transcendental(math.exp, ratio).value == math.e


def _t_residue_forbids_arithmetic_and_ordering():
    zip_a = Quantity(90210.0, residue("US_ZIP", "zip"))
    zip_b = Quantity(10001.0, residue("US_ZIP", "zip"))
    for operation in (lambda: zip_a + zip_b, lambda: zip_a < zip_b):
        try:
            operation()
        except ConventionError:
            continue
        raise AssertionError("expected ConventionError on a convention residue")


def _t_ledger_conserves_across_transfer():
    ledger = Ledger(conserved_energy(), "closed system")
    ledger.open_cell("a", 100.0)
    ledger.open_cell("b", 100.0)
    ledger.transfer("a", "b", 40.0)
    assert ledger.balance("a").value == 60.0
    assert ledger.balance("b").value == 140.0
    assert ledger.check() == 200.0          # total never moved


def _t_ledger_refuses_to_overdraw():
    ledger = Ledger(conserved_energy())
    ledger.open_cell("a", 10.0)
    ledger.open_cell("b", 0.0)
    try:
        ledger.transfer("a", "b", 25.0)
    except ConservationError:
        assert ledger.check() == 10.0       # the failed move left no trace
        return
    raise AssertionError("expected ConservationError")


def _t_ledger_has_no_way_to_write_an_orphan_credit():
    # the point of the type: amplification is not forbidden by a check that
    # runs afterwards, it is unreachable because the API cannot express it
    ledger = Ledger(conserved_energy())
    ledger.open_cell("a", 100.0)
    assert not any(name for name in dir(ledger)
                   if name in ("credit", "amplify", "add", "regenerate"))
    assert ledger.check() == 100.0


def _t_ledger_rejects_non_conserved_types():
    for bad in (entropy(), information()):
        try:
            Ledger(bad)
        except (ConservationError, TransferError):
            continue
        raise AssertionError(f"expected refusal for {bad.label}")


def _t_information_copies_without_debiting_source():
    info = information()
    assert info.transfer is Transfer.COPY
    assert info.cost_floor is CostFloor.ERASE   # the price is deferred, not waived
    assert erase_cost(1) > 0
    assert erase_cost(0) == 0


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    _run()
