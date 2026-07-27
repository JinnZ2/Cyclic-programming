# language_ecosystem.py — the same cascade model, applied to languages.
# CC0. stdlib + harm.py + repurpose_controller.py + repurpose_table.py.
#
# Companion to component_repurpose.py. There the nodes are degraded parts and
# repurposing is finding the part a new job; here the nodes are language
# communities and repurposing is a transpiler moving maintenance capacity
# from a healthy ecosystem to a struggling one.
#
# The arithmetic is identical, which is the argument: "cheaper to let it die"
# is a threshold, and a repurposing path is what keeps a system on the near
# side of it. names_no: [intent, actor, should].

from harm import Coupling, Node, System
from repurpose_controller import RepurposeReserve, run_with_repurposing
from repurpose_table import DEFAULT_LANGUAGE_TABLE, best_donor_for

# draw = maintenance burden, regen = contributor capacity. Hand-set to put
# COBOL in deficit and Python in surplus; they are illustrative, not measured.
LANGUAGES = {
    "Python":     Node(draw=2.0, regen=3.0),   # large, healthy
    "Rust":       Node(draw=2.5, regen=2.2),   # growing, slightly stressed
    "JavaScript": Node(draw=2.8, regen=2.5),   # large but churn hurts
    "COBOL":      Node(draw=1.8, regen=1.0),   # legacy, in deficit
}

# Decline in one ecosystem pulls attention out of its neighbours.
COUPLINGS = [
    Coupling("COBOL", "Python", transfer=0.3, sensitivity=0.2),
    Coupling("JavaScript", "Rust", transfer=0.2, sensitivity=0.3),
]


def build_ecosystem():
    """Fresh System — Node is mutable, so each run needs its own copy."""
    nodes = {name: Node(draw=n.draw, regen=n.regen)
             for name, n in LANGUAGES.items()}
    return System(nodes, list(COUPLINGS))


def table_controller(table=None, share=0.2):
    """
    Move capacity from surplus languages to deficit ones via the best
    available translation path.

    For each language in deficit, pick the most effective donor that still has
    surplus to give, then hand over `share` of that surplus scaled by how well
    the translation actually works. A language with no translation path to it
    gets nothing — an unreachable ecosystem cannot be rescued by tooling, and
    the model should say so rather than smoothing it over.

    Each donor's surplus is budgeted once per tick and drawn down as it is
    committed, so serving three struggling languages cannot spend the same
    contributor capacity three times.
    """
    table = table if table is not None else DEFAULT_LANGUAGE_TABLE

    def controller(t, system, reserve):
        nodes = system.nodes
        budget = {n: nd.regen - nd.draw
                  for n, nd in nodes.items() if nd.regen > nd.draw}
        deficit = [n for n, nd in nodes.items() if nd.regen <= nd.draw]

        actions = []
        for target in deficit:
            donors = [s for s in budget if s != target and budget[s] > 0]
            if not donors:
                continue
            best = best_donor_for(target, donors, table=table)
            if best is None:
                continue
            source, cost, effectiveness = best
            amount = min(budget[source] * share, budget[source])
            if amount <= 0:
                continue
            budget[source] -= amount
            # the donor pays a maintenance overhead for carrying the bridge
            nodes[source].regen -= amount * cost * 0.1
            actions.append((target, amount * effectiveness))
        return actions

    return controller


def compare(ticks=30, reserve=5.0, table=None):
    """Run the ecosystem with and without cross-language repurposing."""
    results = {}
    for label, use_table in (("isolated", False), ("repurposing", True)):
        trace, locked_at, log = run_with_repurposing(
            build_ecosystem(), ticks=ticks, erosion=1.0, regen_rate=0.05,
            repurpose_reserve=RepurposeReserve(initial=reserve, decay_rate=0.02),
            controller=table_controller(table) if use_table else None)
        results[label] = {
            "trace": trace,
            "locked_at": locked_at,
            "final_dof": trace[-1]["dof"],
            "actions": log,
        }
    return results


def main():
    results = compare()
    print(f"{'':<14} {'locked at':>9} {'languages in surplus':>21}")
    for label in ("isolated", "repurposing"):
        row = results[label]
        lock = row["locked_at"] if row["locked_at"] is not None else "never"
        surplus = f"{row['final_dof']}/{len(LANGUAGES)}"
        print(f"  {label:<12} {str(lock):>9} {surplus:>21}")
    print()

    helped = results["repurposing"]
    if helped["locked_at"] is None:
        print("with repurposing the threshold is never crossed — the "
              "ecosystem stays reversible")
    else:
        row = helped["trace"][helped["locked_at"]]
        print(f"locked at t={helped['locked_at']}: "
              f"reversal={row['reversal']} continuation={row['continuation']}")

    moved = sum(a["amount"] for a in helped["actions"])
    print(f"{moved:.2f} capacity moved across {len(helped['actions'])} transfers")


# --- self-test -------------------------------------------------------------

def _t_each_run_starts_from_the_same_state():
    a, b = build_ecosystem(), build_ecosystem()
    a.nodes["Python"].regen = 99.0
    assert b.nodes["Python"].regen == LANGUAGES["Python"].regen


def _t_repurposing_keeps_more_languages_in_surplus():
    results = compare()
    assert results["isolated"]["final_dof"] < results["repurposing"]["final_dof"]


def _t_controller_only_targets_deficit_languages():
    system = build_ecosystem()
    for node in system.nodes.values():
        node.regen = node.draw + 1.0
    assert table_controller()(0, system, None) == []


def _t_unreachable_language_gets_nothing():
    # Haskell has no translation path in the table, so it cannot be helped
    system = build_ecosystem()
    system.nodes["Haskell"] = Node(draw=5.0, regen=0.5)
    targets = [name for name, _ in table_controller()(0, system, None)]
    assert "Haskell" not in targets


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    main()
