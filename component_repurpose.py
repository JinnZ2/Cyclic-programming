# component_repurpose.py — runs real component-failure data through the
# cascade model. CC0. stdlib + harm.py + repurpose_controller.py.
#
# This is the join between two repos. The failure data comes from
# Component-failure-repurposing-database (vendored, see .fieldlink.json);
# the cascade arithmetic comes from harm.py and repurpose_controller.py.
#
# The claim being tested is the sibling repo's premise: a degraded part is
# not waste, it is a part with a different job. Modeled here, that premise
# is the difference between a board that sheds every degree of freedom and
# one that holds some open. names_no: [intent, actor, should].

from dataclasses import dataclass

from fieldlink import MissingSource, component_matrix_path
from harm import Coupling, Node, System
from repurpose_controller import RepurposeReserve, run_with_repurposing
from repurpose_table import best_donor_for, load_component_matrix, targets_for


@dataclass
class Part:
    """A board position, its failure mode, and what it costs vs. supplies."""

    name: str      # position on the board, e.g. "rail_cap"
    spec: str      # "Component/Failure Mode" — the key into the matrix
    draw: float    # capacity this position consumes
    regen: float   # capacity it supplies while healthy


# A small board whose parts are all degrading. Every spec below is a real row
# in matrices/repurpose_effectiveness.csv; the draw/regen numbers are the
# modeling assumption, not upstream data.
BOARD = [
    Part("rail_cap",  "Capacitor (Electrolytic)/Increased ESR",       2.0, 1.5),
    Part("bias_diode", "Diode (Silicon)/Parametric Degradation",      1.0, 2.0),
    Part("sense_res", "Resistor (Carbon Film)/Value Drift",           1.0, 2.0),
    Part("switch_fet", "Transistor (MOSFET)/Parameter Drift",         1.0, 2.0),
]

# The rail capacitor's degradation stresses everything downstream of it.
COUPLINGS = [
    Coupling("rail_cap", "bias_diode", transfer=1.0, sensitivity=2.0),
    Coupling("bias_diode", "sense_res", transfer=1.0, sensitivity=2.0),
    Coupling("sense_res", "switch_fet", transfer=1.0, sensitivity=2.0),
]


def build_board(parts=None, couplings=None):
    """Return (System, {node_name: spec}) for the cascade model."""
    parts = parts if parts is not None else BOARD
    couplings = couplings if couplings is not None else COUPLINGS
    system = System(
        {p.name: Node(draw=p.draw, regen=p.regen) for p in parts},
        list(couplings),
    )
    return system, {p.name: p.spec for p in parts}


def matrix_controller(specs, table, max_cost=1.0):
    """
    Build a controller that repurposes degraded parts using the matrix.

    For each node that has fallen into deficit, look up what its component and
    failure mode can still be used for and grant capacity equal to the best
    available effectiveness. A part with no listed repurpose gets nothing —
    that is the honest outcome, and it is what makes the matrix load-bearing
    rather than decorative.
    """
    def controller(t, system, reserve):
        actions = []
        for name, node in system.nodes.items():
            if node.regen > node.draw:
                continue  # still in surplus, nothing to reclaim
            options = targets_for(specs.get(name, ""), table)
            affordable = [o for o in options if o[1] <= max_cost]
            if not affordable:
                continue
            _, _, effectiveness = affordable[0]
            actions.append((name, effectiveness))
        return actions

    return controller


def compare(ticks=20, reserve=12.0, table=None):
    """
    Run the board twice: scrapping failures, then repurposing them.

    Returns {"scrap": ..., "repurpose": ...}, each a dict with the trace, the
    lock tick, and the final count of parts still in surplus.
    """
    table = table if table is not None else load_component_matrix(
        component_matrix_path())

    results = {}
    for label, use_matrix in (("scrap", False), ("repurpose", True)):
        system, specs = build_board()
        controller = matrix_controller(specs, table) if use_matrix else None
        trace, locked_at, log = run_with_repurposing(
            system, ticks=ticks, erosion=1.0, regen_rate=0.05,
            repurpose_reserve=RepurposeReserve(initial=reserve, decay_rate=0.01),
            controller=controller)
        results[label] = {
            "trace": trace,
            "locked_at": locked_at,
            "final_dof": trace[-1]["dof"],
            "actions": log,
        }
    return results


def options_for(spec, table=None):
    """Every job a given component/failure-mode can still do, best first."""
    table = table if table is not None else load_component_matrix(
        component_matrix_path())
    return targets_for(spec, table)


def main():
    try:
        table = load_component_matrix(component_matrix_path())
    except (MissingSource, FileNotFoundError) as exc:
        print("cannot run:", exc)
        return 1

    sources = {src for src, _ in table}
    print(f"matrix: {len(table)} repurpose paths across {len(sources)} "
          "component/failure-mode pairs")
    print()

    print("board:")
    for part in BOARD:
        options = targets_for(part.spec, table)
        best = f"{options[0][0]} ({options[0][2]:.1f})" if options else "none listed"
        print(f"  {part.name:<11} {part.spec:<45} best repurpose: {best}")
    print()

    results = compare(table=table)
    print(f"{'':<12} {'locked at':>9} {'parts in surplus':>18}")
    for label in ("scrap", "repurpose"):
        row = results[label]
        lock = row["locked_at"] if row["locked_at"] is not None else "never"
        surplus = f"{row['final_dof']}/{len(BOARD)}"
        print(f"  {label:<10} {str(lock):>9} {surplus:>18}")
    print()

    granted = sum(a["amount"] for a in results["repurpose"]["actions"])
    print(f"repurposing spent {granted:.2f} capacity from the reserve and kept "
          f"{results['repurpose']['final_dof'] - results['scrap']['final_dof']} "
          "more part(s) in surplus")
    return 0


# --- self-test -------------------------------------------------------------

def _t_every_board_spec_exists_in_the_matrix():
    # guards against the vendored CSV drifting out from under the demo
    table = load_component_matrix(component_matrix_path())
    sources = {src for src, _ in table}
    for part in BOARD:
        assert part.spec in sources, f"{part.spec} missing from matrix"


def _t_repurposing_beats_scrapping():
    results = compare()
    assert results["scrap"]["final_dof"] < results["repurpose"]["final_dof"]


def _t_controller_ignores_parts_in_surplus():
    table = load_component_matrix(component_matrix_path())
    system, specs = build_board()
    for node in system.nodes.values():
        node.regen = node.draw + 1.0        # everything healthy
    assert matrix_controller(specs, table)(0, system, None) == []


def _t_unlisted_part_gets_no_capacity():
    table = load_component_matrix(component_matrix_path())
    system, _ = build_board()
    for node in system.nodes.values():
        node.regen = 0.0                    # everything in deficit
    specs = {name: "Nonexistent/Failure" for name in system.nodes}
    assert matrix_controller(specs, table)(0, system, None) == []


def _t_options_are_ordered_by_effectiveness():
    options = options_for("Diode (Silicon)/Parametric Degradation")
    assert options
    assert options == sorted(options, key=lambda row: -row[2])


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    raise SystemExit(main())
