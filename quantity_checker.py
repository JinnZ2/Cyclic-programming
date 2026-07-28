# quantity_checker.py — prototype quantity type checker for the taxonomy.
# CC0. stdlib only. phone-buildable.

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple

class Extensivity(Enum):
    EXTENSIVE = auto()
    INTENSIVE = auto()

class Conservation(Enum):
    CONSERVED  = auto()
    MONOTONE   = auto()
    PRODUCIBLE = auto()

class Datum(Enum):
    ABSOLUTE = auto()
    RELATIVE = auto()

class Transfer(Enum):
    DEBIT_CREDIT = auto()
    COPY         = auto()
    CONSUME      = auto()
    EQUILIBRATE  = auto()

@dataclass(frozen=True)
class QuantityType:
    extensivity:  Extensivity
    conservation: Conservation
    datum:        Datum
    transfer:     Transfer
    dimension:    Tuple[int, ...]  # (M,L,T,I,Theta,N,J)
    floor:        Optional[float] = None
    ceiling:      Optional[float] = None
    signed:       bool = True
    convention:   Optional[str] = None  # residue tag, non-physical

class QuantityError(Exception):
    pass

class QuantityVar:
    """A variable with a value and a QuantityType. Operations are checked."""
    def __init__(self, name: str, value: float, qtype: QuantityType):
        self.name = name
        self.qtype = qtype
        self._val = value
        self._check_bounds()

    def _check_bounds(self):
        if self.qtype.floor is not None and self._val < self.qtype.floor:
            raise QuantityError(f"{self.name} underflow: {self._val} < floor {self.qtype.floor}")
        if self.qtype.ceiling is not None and self._val > self.qtype.ceiling:
            raise QuantityError(f"{self.name} overflow: {self._val} > ceiling {self.qtype.ceiling}")

    @property
    def value(self):
        return self._val

    @value.setter
    def value(self, new_val):
        self._val = new_val
        self._check_bounds()

    def _reject_if_residue(self, op: str):
        """
        A convention tag marks a social fact wearing a number's clothes —
        a zip code, an ISO code. The taxonomy forbids arithmetic and ordering
        on these outright. The field was declared but never enforced, so
        `zip_a + zip_b` used to return a number.
        """
        if self.qtype.convention is not None:
            raise QuantityError(
                f"{op} is meaningless on {self.name}: convention="
                f"{self.qtype.convention} is a label, not a magnitude")

    # ---- arithmetic with type checking ----

    def __add__(self, other):
        if not isinstance(other, QuantityVar):
            raise QuantityError("Can only add QuantityVar")
        self._reject_if_residue("Addition")
        other._reject_if_residue("Addition")
        # Two conventional zeros have no shared origin, so their sum
        # denominates nothing: 3pm + 4pm is not a time. Only a datum
        # *mismatch* was checked before, which let this through.
        if (self.qtype.datum == Datum.RELATIVE
                and other.qtype.datum == Datum.RELATIVE):
            raise QuantityError(
                f"Addition of RELATIVE '{self.name}' and '{other.name}' is "
                "meaningless: both zeros are conventions")
        if self.qtype.extensivity == Extensivity.INTENSIVE:
            raise QuantityError(f"Addition of intensives '{self.name}' and '{other.name}' is meaningless")
        if other.qtype.extensivity == Extensivity.INTENSIVE:
            raise QuantityError(f"Addition of intensives '{other.name}' and '{self.name}' is meaningless")
        if self.qtype.dimension != other.qtype.dimension:
            raise QuantityError(f"Dimension mismatch: {self.qtype.dimension} vs {other.qtype.dimension}")
        if self.qtype.datum != other.qtype.datum:
            raise QuantityError(f"Datum mismatch: {self.qtype.datum} vs {other.qtype.datum}")
        # result type: same as operands, floor = sum of floors if both floored? Keep simple.
        result_val = self._val + other._val
        # result type: keep extensivity, signed, etc. Assume same.
        return QuantityVar(f"({self.name}+{other.name})", result_val, self.qtype)

    def __sub__(self, other):
        if not isinstance(other, QuantityVar):
            raise QuantityError("Can only subtract QuantityVar")
        self._reject_if_residue("Subtraction")
        other._reject_if_residue("Subtraction")
        # A monotone quantity running backwards is a fault, not a value —
        # this is how a clock rollback becomes detectable rather than silent.
        if (self.qtype.conservation == Conservation.MONOTONE
                and other.value > 0):
            raise QuantityError(
                f"{self.name} is MONOTONE; decrementing by {other.value} "
                "is a fault (clock rollback)")
        # Subtraction of RELATIVE yields ABSOLUTE delta
        if self.qtype.datum == Datum.RELATIVE and other.qtype.datum == Datum.RELATIVE:
            # result is an absolute delta
            result_qtype = QuantityType(
                extensivity=self.qtype.extensivity,
                conservation=self.qtype.conservation,
                datum=Datum.ABSOLUTE,
                transfer=self.qtype.transfer,
                dimension=self.qtype.dimension,
                signed=True,
                floor=None
            )
        else:
            # general: same dimension required
            if self.qtype.dimension != other.qtype.dimension:
                raise QuantityError(f"Dimension mismatch")
            result_qtype = self.qtype
        result_val = self._val - other._val
        return QuantityVar(f"({self.name}-{other.name})", result_val, result_qtype)

    def __mul__(self, other):
        if not isinstance(other, QuantityVar):
            # allow scalar multiplication
            if isinstance(other, (int, float)):
                return QuantityVar(f"({self.name}*{other})", self._val * other, self.qtype)
            raise QuantityError("Can only multiply QuantityVar or scalar")
        # intensive * extensive = extensive
        if self.qtype.extensivity == Extensivity.INTENSIVE and other.qtype.extensivity == Extensivity.EXTENSIVE:
            pass  # result extensive, dimension combined
        elif self.qtype.extensivity == Extensivity.EXTENSIVE and other.qtype.extensivity == Extensivity.INTENSIVE:
            pass
        else:
            raise QuantityError("Multiplication only allowed between extensive and intensive")
        # combine dimensions
        new_dim = tuple(a + b for a, b in zip(self.qtype.dimension, other.qtype.dimension))
        result_qtype = QuantityType(
            extensivity=Extensivity.EXTENSIVE if (self.qtype.extensivity == Extensivity.EXTENSIVE or other.qtype.extensivity == Extensivity.EXTENSIVE) else Extensivity.INTENSIVE,
            conservation=self.qtype.conservation,  # simplified
            datum=self.qtype.datum,
            transfer=self.qtype.transfer,
            dimension=new_dim,
            signed=self.qtype.signed,
        )
        return QuantityVar(f"({self.name}*{other.name})", self._val * other._val, result_qtype)

    def __truediv__(self, other):
        # division: extensive/extensive = intensive, or extensive/intensive = extensive? Needs care.
        # For now simple: require other is extensive, result intensive dimensionless
        if not isinstance(other, QuantityVar):
            if isinstance(other, (int, float)):
                return QuantityVar(f"({self.name}/{other})", self._val / other, self.qtype)
            raise QuantityError("Can only divide by QuantityVar or scalar")
        if other.qtype.extensivity != Extensivity.EXTENSIVE:
            raise QuantityError("Denominator must be extensive")
        new_dim = tuple(a - b for a, b in zip(self.qtype.dimension, other.qtype.dimension))
        result_qtype = QuantityType(
            extensivity=Extensivity.INTENSIVE,
            conservation=self.qtype.conservation,
            datum=Datum.ABSOLUTE,
            transfer=Transfer.COPY,  # ratio is informational
            dimension=new_dim,
            signed=True
        )
        return QuantityVar(f"({self.name}/{other.name})", self._val / other._val, result_qtype)


def transfer(source: QuantityVar, target: QuantityVar, amount: float, mode: Transfer):
    """Move or copy quantity from source to target, respecting type rules."""
    if mode == Transfer.DEBIT_CREDIT:
        if source.qtype.transfer != Transfer.DEBIT_CREDIT:
            raise QuantityError(f"Source {source.name} does not support debit/credit transfer")
        if source.value < amount:
            raise QuantityError(f"Insufficient {source.name}: {source.value} < {amount}")
        source.value -= amount
        target.value += amount
    elif mode == Transfer.COPY:
        # source unchanged, target gains; cost is in the erase later.
        target.value += amount
    elif mode == Transfer.CONSUME:
        if source.value < amount:
            raise QuantityError(f"Insufficient {source.name}: {source.value} < {amount}")
        source.value -= amount
        # target may not gain anything (destruction)
    elif mode == Transfer.EQUILIBRATE:
        # intensive transfer not supported yet
        raise QuantityError("Equilibrate not implemented")

# ---- example and test ----

def demo():
    # Define types
    water_volume = QuantityType(
        extensivity=Extensivity.EXTENSIVE,
        conservation=Conservation.CONSERVED,
        datum=Datum.ABSOLUTE,
        transfer=Transfer.DEBIT_CREDIT,
        dimension=(0,3,0,0,0,0,0),  # L^3
        floor=0.0,
        signed=False
    )
    temperature = QuantityType(
        extensivity=Extensivity.INTENSIVE,
        conservation=Conservation.PRODUCIBLE,
        datum=Datum.RELATIVE,
        transfer=Transfer.EQUILIBRATE,
        dimension=(0,0,0,0,1,0,0),  # Theta
        floor=0.0,
        signed=True
    )
    # Create variables
    tank_A = QuantityVar("tank_A", 100.0, water_volume)
    tank_B = QuantityVar("tank_B", 50.0, water_volume)
    temp1 = QuantityVar("temp1", 25.0, temperature)
    temp2 = QuantityVar("temp2", 30.0, temperature)

    # Valid: transfer water
    print("Transferring 20L from tank_A to tank_B...")
    transfer(tank_A, tank_B, 20.0, Transfer.DEBIT_CREDIT)
    print(f"tank_A: {tank_A.value}L, tank_B: {tank_B.value}L")

    # Invalid: sum temperatures
    try:
        combined = temp1 + temp2
    except QuantityError as e:
        print(f"Caught error: {e}")

    # Invalid: tank_A underflow
    try:
        tank_A.value = -5.0
    except QuantityError as e:
        print(f"Caught underflow: {e}")

    # Subtraction of temperatures yields absolute delta (allowed)
    delta = temp1 - temp2
    print(f"Delta temp: {delta.value} (type datum: {delta.qtype.datum})")

    # Multiplication: intensive * extensive = extensive (e.g., price * volume = cost)
    cost_rate = QuantityType(
        extensivity=Extensivity.INTENSIVE,
        conservation=Conservation.PRODUCIBLE,
        datum=Datum.RELATIVE,
        transfer=Transfer.COPY,
        dimension=(1,0,0,0,0,0,0),  # money per volume
        signed=True
    )
    price = QuantityVar("price_per_liter", 2.0, cost_rate)
    total_cost = price * tank_B  # extensive * intensive? tank_B is extensive
    print(f"Total cost for tank_B: {total_cost.value} (type extensivity: {total_cost.qtype.extensivity})")

if __name__ == "__main__":
    demo()
