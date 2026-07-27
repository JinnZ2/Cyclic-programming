# repurpose_controller.py — steers displaced cost back into the system.
# CC0. stdlib + harm.py + simulator.py.
#
# simulator.run lets a cascade run to completion. this adds the two things
# that let a system pull out of one: passive recovery, and a finite reserve
# a controller can spend to top up nodes that are shedding capacity.
#
# the reserve is finite and decays. that is the point — repurposing is not
# free, so a controller that spends indiscriminately runs dry before the
# cascade stops. names_no: [intent, actor, should].

from dataclasses import dataclass
from typing import Optional

from simulator import step


@dataclass
class RepurposeReserve:
    """Finite pool a controller spends to restore regen. Decays if unspent."""

    initial: float = 5.0
    decay_rate: float = 0.0
    value: Optional[float] = None

    def __post_init__(self):
        if self.value is None:
            self.value = self.initial

    def spend(self, amount):
        """Draw down the reserve. Returns what was actually available."""
        actual = min(self.value, max(0.0, amount))
        self.value -= actual
        return actual

    def tick(self):
        # capacity held idle degrades too — an unspent reserve is not preserved.
        self.value = max(0.0, self.value * (1.0 - self.decay_rate))


def run_with_repurposing(system, ticks=20, erosion=1.0, regen_rate=0.0,
                         repurpose_reserve=None, controller=None):
    """
    Step the system with recovery and optional controller intervention.

    Per tick, in order:
      1. cascade   — displaced cost erodes regen (simulator.step)
      2. recovery  — every node regains regen_rate, capped at its start value
      3. controller— may spend reserve to add regen to chosen nodes
      4. decay     — the unspent reserve shrinks

    Recovery is capped at each node's starting regen: passive healing restores
    capacity, it does not manufacture new capacity. Controller actions are not
    capped — repurposing can leave a node doing more than it originally did,
    which is the whole premise, but every unit of it is charged to the reserve.
    Recovery therefore only ever raises a node toward its starting capacity; it
    never pulls one back down to it.

    controller is called as controller(t, system, reserve) and returns a list
    of (node_name, amount) actions. The runner charges the reserve, so a
    controller should not decrement reserve.value itself.

    Returns (trace, locked_at, actions_log), where locked_at is the first tick
    at which reversal both exceeds and outpaces continuation.
    """
    regen0 = {n: nd.regen for n, nd in system.nodes.items()}
    trace = []
    actions_log = []
    locked_at = None

    for t in range(ticks):
        exported, _ = step(system, erosion)

        # passive recovery, capped at the node's original capacity. the guard
        # matters: without it the cap also claws back capacity a controller
        # deliberately added above the starting point, silently undoing every
        # grant to a node that began in deficit.
        if regen_rate:
            for n, nd in system.nodes.items():
                if nd.regen < regen0[n]:
                    nd.regen = min(regen0[n], nd.regen + regen_rate)

        # controller spends the reserve to restore capacity where it chooses
        if controller is not None and repurpose_reserve is not None:
            for name, amount in controller(t, system, repurpose_reserve) or []:
                if name not in system.nodes or amount <= 0:
                    continue
                granted = repurpose_reserve.spend(amount)
                if granted > 0:
                    system.nodes[name].regen += granted
                    actions_log.append({"t": t, "node": name, "amount": granted})

        if repurpose_reserve is not None:
            repurpose_reserve.tick()

        continuation = sum(exported.values())
        reversal = sum(max(0.0, regen0[n] - nd.regen)
                       for n, nd in system.nodes.items())
        dof = sum(1 for nd in system.nodes.values() if nd.regen > nd.draw)

        prev = trace[-1] if trace else None
        d_cont = continuation - prev["continuation"] if prev else continuation
        d_rev = reversal - prev["reversal"] if prev else reversal

        trace.append({
            "t": t,
            "dof": dof,
            "continuation": round(continuation, 4),
            "reversal": round(reversal, 4),
            "d_continuation": round(d_cont, 4),
            "d_reversal": round(d_rev, 4),
            "reserve": round(repurpose_reserve.value, 4) if repurpose_reserve else 0.0,
        })

        if locked_at is None and reversal > continuation and d_rev > d_cont:
            locked_at = t

    return trace, locked_at, actions_log


# --- self-test -------------------------------------------------------------

def _t_reserve_spend_is_bounded_by_value():
    r = RepurposeReserve(initial=1.0)
    assert r.spend(5.0) == 1.0
    assert r.value == 0.0
    assert r.spend(1.0) == 0.0


def _t_unspent_reserve_decays():
    r = RepurposeReserve(initial=10.0, decay_rate=0.5)
    r.tick()
    assert r.value == 5.0


def _t_recovery_cannot_exceed_starting_capacity():
    from harm import Node, System
    s = System({"a": Node(draw=1.0, regen=2.0)})
    trace, _, _ = run_with_repurposing(s, ticks=10, regen_rate=1.0)
    assert s.nodes["a"].regen <= 2.0
    assert trace[-1]["reversal"] == 0.0        # nothing eroded, nothing to undo


def _t_recovery_does_not_claw_back_granted_capacity():
    # regression: capping recovery at the starting regen used to also drag
    # nodes back down to it, silently erasing every controller grant to a
    # node that began in deficit.
    from harm import Node, System
    s = System({"a": Node(draw=2.0, regen=1.0)})
    _, _, log = run_with_repurposing(
        s, ticks=10, regen_rate=0.05,
        repurpose_reserve=RepurposeReserve(initial=10.0),
        controller=lambda t, sys, res: [("a", 0.3)])
    granted = sum(a["amount"] for a in log)
    assert granted > 0
    assert s.nodes["a"].regen > 1.0        # grants accumulate above the start
    assert s.nodes["a"].regen > s.nodes["a"].draw   # and lift it out of deficit


def _t_repurposing_keeps_off_ramps_open():
    from harm import Coupling, Node, System

    def build():
        # 'a' starts in mild deficit, seeding a cascade the others amplify
        return System(
            {"a": Node(2.0, 1.5), "b": Node(1.0, 2.0), "c": Node(1.0, 2.0)},
            [Coupling("a", "b", 1.0, 2.0), Coupling("b", "c", 1.0, 2.0)],
        )

    def prop_up(t, system, reserve):
        # top up whichever nodes have fallen into deficit
        return [(n, 0.5) for n, nd in system.nodes.items() if nd.regen <= nd.draw]

    bare, bare_lock, _ = run_with_repurposing(build(), ticks=15, regen_rate=0.05)
    helped, _, log = run_with_repurposing(
        build(), ticks=15, regen_rate=0.05,
        repurpose_reserve=RepurposeReserve(initial=20.0), controller=prop_up)

    assert bare_lock is not None                     # bare system locks up
    assert log                                       # controller actually acted
    assert bare[-1]["dof"] == 0                      # bare sheds every off-ramp
    assert helped[-1]["dof"] > bare[-1]["dof"]       # repurposing keeps some open


def _t_controller_cannot_overspend_reserve():
    from harm import Node, System
    s = System({"a": Node(5.0, 1.0)})
    reserve = RepurposeReserve(initial=2.0)
    _, _, log = run_with_repurposing(
        s, ticks=10, repurpose_reserve=reserve,
        controller=lambda t, sys, res: [("a", 100.0)])
    assert reserve.value == 0.0
    assert sum(a["amount"] for a in log) == 2.0      # never granted more than held


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    _run()
