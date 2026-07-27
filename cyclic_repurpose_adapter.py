# cyclic_repurpose_adapter.py — the one bridge to the cyclic interpreter.
# CC0. stdlib only.
#
# Everything else talks to this, not to CyclicalInterpreter directly, so the
# interpreter stays swappable. If it is not importable the adapter falls back
# to a plain energy-conserving model with the same interface, which is what
# makes this file safe to vendor into a repo that does not ship the
# interpreter (see .fieldlink.json).
#
# Note on units: the interpreter's decay() takes a *rate* (a fraction of
# current energy), while this adapter's draw_down() takes an *amount*. The
# conversion happens here rather than at every call site.

import os
import sys

try:
    # installed, on sys.path, or vendored alongside by a consuming repo
    _VENDORED = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "vendor", "cyclic")
    if os.path.isdir(_VENDORED) and _VENDORED not in sys.path:
        sys.path.insert(0, _VENDORED)
    from cyclic_interpreter import CyclicalInterpreter
    CYCLIC_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on install layout
    CyclicalInterpreter = None
    CYCLIC_AVAILABLE = False


class CyclicRepurposeEngine:
    """
    Energy bookkeeping for a set of named nodes.

    Backed by the cyclic interpreter when it is importable, by a simple
    conserving model otherwise. Both paths honour the same rule: energy is
    never created except by an explicit regenerate() call, and draw_down()
    never pushes a node below zero.
    """

    def __init__(self, force_fallback=False):
        self.using_interpreter = CYCLIC_AVAILABLE and not force_fallback
        self.interp = CyclicalInterpreter() if self.using_interpreter else None
        # draw and starting energy are tracked here in both modes: they are
        # this model's concepts, not the interpreter's.
        self._meta = {}

    def create_node(self, name, draw, regen):
        """Create a node holding `regen` energy and drawing `draw` per tick."""
        if self.using_interpreter:
            self.interp.create_field(name, regen)
        self._meta[name] = {"draw": draw, "initial": regen, "energy": regen}

    def energy(self, name):
        """Current energy held by the node."""
        if self.using_interpreter:
            return self.interp.fields[name].energy.total_energy
        return self._meta[name]["energy"]

    def draw(self, name):
        return self._meta[name]["draw"]

    def surplus(self, name):
        """Energy minus draw. Positive means the node is still carrying itself."""
        return self.energy(name) - self._meta[name]["draw"]

    def reversal(self, name):
        """Capacity lost against where the node started. Never negative."""
        return max(0.0, self._meta[name]["initial"] - self.energy(name))

    def draw_down(self, name, amount):
        """Remove `amount` of energy, floored at zero. Returns what was removed."""
        current = self.energy(name)
        actual = min(current, max(0.0, amount))
        if self.using_interpreter and current > 0:
            # decay() takes a fraction of current energy, so convert
            self.interp.execute(f"∂decay({name}, {actual / current})")
        else:
            self._meta[name]["energy"] = current - actual
        return actual

    def regenerate(self, name, amount):
        """Add capacity back to a node."""
        if amount <= 0:
            return
        if self.using_interpreter:
            self.interp.execute(f"∮regenerate({name}, {amount})")
        else:
            self._meta[name]["energy"] += amount

    def transfer(self, source, target, amount):
        """Directed transfer: source loses, target gains. Returns amount moved."""
        actual = min(self.energy(source), max(0.0, amount))
        if actual <= 0:
            return 0.0
        if self.using_interpreter:
            self.interp.execute(f"COBOL:MOVE {actual} FROM {source} TO {target}")
        else:
            self._meta[source]["energy"] -= actual
            self._meta[target]["energy"] += actual
        return actual

    def entangle(self, a, b):
        """
        Correlate two nodes. Returns True if the link was actually established.

        Only the interpreter implements this; the fallback model has no
        equivalent and reports False rather than pretending.
        """
        if self.using_interpreter:
            self.interp.execute(f"⊗({a}, {b})")
            return True
        return False

    def total_energy(self):
        return sum(self.energy(name) for name in self._meta)

    def degrees_of_freedom(self):
        """How many nodes are still in surplus — the off-ramps still open."""
        return sum(1 for name in self._meta if self.surplus(name) > 0)


# --- self-test -------------------------------------------------------------

def _engines():
    """Both backends, so the interface is verified identical."""
    engines = [CyclicRepurposeEngine(force_fallback=True)]
    if CYCLIC_AVAILABLE:
        engines.append(CyclicRepurposeEngine())
    return engines


def _t_create_and_read_back():
    for e in _engines():
        e.create_node("a", draw=2.0, regen=10.0)
        assert abs(e.energy("a") - 10.0) < 1e-9
        assert abs(e.surplus("a") - 8.0) < 1e-9
        assert e.reversal("a") == 0.0


def _t_draw_down_floors_at_zero():
    for e in _engines():
        e.create_node("a", draw=1.0, regen=5.0)
        removed = e.draw_down("a", 50.0)
        assert abs(removed - 5.0) < 1e-9
        assert e.energy("a") < 1e-9
        assert e.draw_down("a", 1.0) == 0.0


def _t_transfer_conserves_total():
    for e in _engines():
        e.create_node("a", draw=1.0, regen=10.0)
        e.create_node("b", draw=1.0, regen=10.0)
        before = e.total_energy()
        moved = e.transfer("a", "b", 4.0)
        assert moved > 0
        assert abs(e.total_energy() - before) < 1e-6   # nothing created or lost


def _t_transfer_cannot_overdraw():
    for e in _engines():
        e.create_node("a", draw=1.0, regen=2.0)
        e.create_node("b", draw=1.0, regen=2.0)
        moved = e.transfer("a", "b", 100.0)
        assert moved <= 2.0 + 1e-9
        assert e.energy("a") >= -1e-9


def _t_degrees_of_freedom_tracks_surplus():
    for e in _engines():
        e.create_node("a", draw=1.0, regen=5.0)
        e.create_node("b", draw=9.0, regen=5.0)
        assert e.degrees_of_freedom() == 1        # only 'a' carries itself


def _t_fallback_entangle_reports_false():
    e = CyclicRepurposeEngine(force_fallback=True)
    e.create_node("a", 1.0, 5.0)
    e.create_node("b", 1.0, 5.0)
    assert e.entangle("a", "b") is False          # honest about the no-op


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print(f"all pass (interpreter available: {CYCLIC_AVAILABLE})")


if __name__ == "__main__":
    _run()
