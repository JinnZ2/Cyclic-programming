"""
Tests for the cascade model and the cross-repo link.

The modules under test also carry their own assert-based self-tests so they
stay runnable without pytest; this file re-runs those and adds the cases that
are easier to express with pytest.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import component_repurpose
import cyclic_repurpose_adapter
import fieldlink
import harm
import language_ecosystem
import repurpose_controller
import repurpose_table
import simulator
from cyclic_repurpose_adapter import CyclicRepurposeEngine
from harm import Coupling, Node, System
from repurpose_controller import RepurposeReserve, run_with_repurposing


SELFTEST_MODULES = [
    harm,
    simulator,
    repurpose_controller,
    repurpose_table,
    cyclic_repurpose_adapter,
    fieldlink,
    component_repurpose,
    language_ecosystem,
]


def _selftests(module):
    return [(name, fn) for name, fn in sorted(vars(module).items())
            if name.startswith("_t_") and callable(fn)]


@pytest.mark.parametrize("module", SELFTEST_MODULES, ids=lambda m: m.__name__)
def test_module_selftests_pass(module):
    checks = _selftests(module)
    assert checks, f"{module.__name__} declares no _t_* self-tests"
    for _, fn in checks:
        fn()


# --- harm / simulator ------------------------------------------------------

def test_surplus_node_exports_nothing():
    signature = harm.read(System({"a": Node(draw=1.0, regen=3.0)}))
    assert signature["local"]["a"] == 0.0
    assert not signature["displaced"]


def test_amplifying_chain_inflates_per_order():
    system = System(
        {"a": Node(3.0, 1.0), "b": Node(1.0, 1.0), "c": Node(1.0, 1.0)},
        [Coupling("a", "b", 1.0, 2.0), Coupling("b", "c", 1.0, 2.0)],
    )
    signature = harm.read(system)
    assert signature["inflates"]
    assert signature["per_order"][2] > signature["per_order"][1]


def test_simulator_locks_and_sheds_degrees_of_freedom():
    system = System(
        {"a": Node(3.0, 1.0), "b": Node(1.0, 2.0), "c": Node(1.0, 2.0)},
        [Coupling("a", "b", 1.0, 2.0), Coupling("b", "c", 1.0, 2.0)],
    )
    out = simulator.run(system, ticks=15)
    assert out["locked_at"] is not None
    assert out["trace"][-1]["dof"] < out["trace"][0]["dof"]


# --- reserve and controller ------------------------------------------------

def test_reserve_never_grants_more_than_it_holds():
    reserve = RepurposeReserve(initial=2.0)
    system = System({"a": Node(5.0, 1.0)})
    _, _, log = run_with_repurposing(
        system, ticks=10, repurpose_reserve=reserve,
        controller=lambda t, sys, res: [("a", 100.0)])
    assert reserve.value == 0.0
    assert sum(action["amount"] for action in log) == pytest.approx(2.0)


def test_recovery_does_not_erase_controller_grants():
    # regression: the recovery cap used to drag nodes back to their starting
    # regen, silently undoing every grant to a node that began in deficit
    system = System({"a": Node(draw=2.0, regen=1.0)})
    run_with_repurposing(
        system, ticks=10, regen_rate=0.05,
        repurpose_reserve=RepurposeReserve(initial=10.0),
        controller=lambda t, sys, res: [("a", 0.3)])
    assert system.nodes["a"].regen > system.nodes["a"].draw


def test_passive_recovery_cannot_exceed_starting_capacity():
    system = System({"a": Node(draw=1.0, regen=2.0)})
    run_with_repurposing(system, ticks=10, regen_rate=1.0)
    assert system.nodes["a"].regen == pytest.approx(2.0)


def test_controller_actions_are_ignored_without_a_reserve():
    system = System({"a": Node(5.0, 1.0)})
    _, _, log = run_with_repurposing(
        system, ticks=5, controller=lambda t, sys, res: [("a", 1.0)])
    assert log == []


# --- repurpose table -------------------------------------------------------

def test_missing_csv_falls_back_to_default_table():
    assert repurpose_table.load_csv("/nonexistent.csv") == \
        repurpose_table.DEFAULT_LANGUAGE_TABLE


def test_best_donor_prefers_effectiveness_within_budget():
    assert repurpose_table.best_donor_for("COBOL", ["Python", "Rust"])[0] == "Python"
    assert repurpose_table.best_donor_for("COBOL", ["Rust"], max_cost=0.4) is None


def test_component_matrix_load_requires_the_file():
    with pytest.raises(FileNotFoundError):
        repurpose_table.load_component_matrix("/nonexistent/matrix.csv")


# --- cross-repo link -------------------------------------------------------

def test_fieldlink_declares_the_component_database():
    source = fieldlink.get_source("component-failure-db")
    assert source is not None
    assert "Component-failure-repurposing-database" in source["repo"]


def test_unvendored_source_reports_instead_of_fetching():
    with pytest.raises(fieldlink.MissingSource) as excinfo:
        fieldlink.resolve("geometric-bridge", "GEIS/encoder.py")
    assert "github.com" in str(excinfo.value)


def test_component_matrix_is_vendored_and_parses():
    table = repurpose_table.load_component_matrix(fieldlink.component_matrix_path())
    assert len(table) > 100
    for (source, target), (cost, effectiveness) in table.items():
        assert "/" in source                      # "Component/Failure Mode"
        assert target
        assert 0.0 <= effectiveness <= 1.0
        assert cost == pytest.approx(1.0 - effectiveness)


def test_board_specs_exist_in_the_matrix():
    table = repurpose_table.load_component_matrix(fieldlink.component_matrix_path())
    sources = {source for source, _ in table}
    for part in component_repurpose.BOARD:
        assert part.spec in sources


# --- worked examples -------------------------------------------------------

def test_repurposing_beats_scrapping_on_the_component_board():
    results = component_repurpose.compare()
    assert results["repurpose"]["final_dof"] > results["scrap"]["final_dof"]
    assert results["repurpose"]["actions"]


def test_repurposing_beats_isolation_in_the_language_ecosystem():
    results = language_ecosystem.compare()
    assert results["repurposing"]["final_dof"] > results["isolated"]["final_dof"]


def test_unlisted_component_receives_no_capacity():
    table = repurpose_table.load_component_matrix(fieldlink.component_matrix_path())
    system, _ = component_repurpose.build_board()
    for node in system.nodes.values():
        node.regen = 0.0
    specs = {name: "Nonexistent/Failure" for name in system.nodes}
    assert component_repurpose.matrix_controller(specs, table)(0, system, None) == []


# --- adapter ---------------------------------------------------------------

@pytest.fixture(params=[True, False], ids=["fallback", "interpreter"])
def engine(request):
    if not request.param and not cyclic_repurpose_adapter.CYCLIC_AVAILABLE:
        pytest.skip("interpreter not importable")
    return CyclicRepurposeEngine(force_fallback=request.param)


def test_engine_reports_created_state(engine):
    engine.create_node("a", draw=2.0, regen=10.0)
    assert engine.energy("a") == pytest.approx(10.0)
    assert engine.surplus("a") == pytest.approx(8.0)
    assert engine.reversal("a") == 0.0


def test_engine_transfer_conserves_total(engine):
    engine.create_node("a", draw=1.0, regen=10.0)
    engine.create_node("b", draw=1.0, regen=10.0)
    before = engine.total_energy()
    assert engine.transfer("a", "b", 4.0) > 0
    assert engine.total_energy() == pytest.approx(before)


def test_engine_draw_down_floors_at_zero(engine):
    engine.create_node("a", draw=1.0, regen=5.0)
    assert engine.draw_down("a", 50.0) == pytest.approx(5.0)
    assert engine.energy("a") == pytest.approx(0.0)
    assert engine.draw_down("a", 1.0) == 0.0


def test_engine_counts_open_off_ramps(engine):
    engine.create_node("a", draw=1.0, regen=5.0)
    engine.create_node("b", draw=9.0, regen=5.0)
    assert engine.degrees_of_freedom() == 1
