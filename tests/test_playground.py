"""
Tests for the snippet-repurposing playground modules and the prototype
quantity checker they are built on.

These cover the four defects found when the playground files were first run
against the cleaned-up repo, so none of them can return quietly.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import code_playground
import quantity_checker
import recycling_playground
from code_playground import CodeSnippet, Playground
from quantity_checker import (
    Conservation, Datum, Extensivity, QuantityError, QuantityType,
    QuantityVar, Transfer,
)

ENERGY = QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED, Datum.ABSOLUTE,
                      Transfer.DEBIT_CREDIT, (1, 2, -2, 0, 0, 0, 0), floor=0.0)
VOLUME = QuantityType(Extensivity.EXTENSIVE, Conservation.CONSERVED, Datum.ABSOLUTE,
                      Transfer.DEBIT_CREDIT, (0, 3, 0, 0, 0, 0, 0), floor=0.0)
RELATIVE_TIME = QuantityType(Extensivity.EXTENSIVE, Conservation.PRODUCIBLE,
                             Datum.RELATIVE, Transfer.COPY, (0, 0, 1, 0, 0, 0, 0))
MONOTONE = QuantityType(Extensivity.EXTENSIVE, Conservation.MONOTONE, Datum.ABSOLUTE,
                        Transfer.DEBIT_CREDIT, (0,) * 7, floor=0.0)
ZIP = QuantityType(Extensivity.EXTENSIVE, Conservation.PRODUCIBLE, Datum.ABSOLUTE,
                   Transfer.COPY, (0,) * 7, convention="US_ZIP")


# --- the modules load at all -----------------------------------------------

@pytest.mark.parametrize("name", [
    "quantity_checker", "code_playground", "recycling_playground",
    "repurpose_workshop", "vector_recycling_playground",
    "token_recycling_playground",
])
def test_playground_module_imports(name):
    # three of these failed on a missing language_translation_table, which the
    # cleanup had merged into repurpose_table
    __import__(name)


def test_translation_table_resolves_to_the_merged_module():
    from repurpose_table import DEFAULT_LANGUAGE_TABLE
    assert code_playground.TRANSLATION_TABLE == DEFAULT_LANGUAGE_TABLE


def test_quantity_type_has_no_bounded_field():
    # two call sites passed bounded=(0,1), which is not a field; the interval
    # is expressed as floor/ceiling
    import dataclasses
    fields = {f.name for f in dataclasses.fields(QuantityType)}
    assert "bounded" not in fields
    assert {"floor", "ceiling"} <= fields


# --- chains match on type, not on name -------------------------------------

def _pump():
    return CodeSnippet("Python", "pump", "", {"electric_energy_in": ENERGY},
                       {"water_out": VOLUME})


def test_chain_search_ignores_variable_names():
    # the reduction rule says names differing is not a difference, so a
    # snippet wanting `electric_energy_in` must fire on a variable called
    # `sunlight` carrying the same type
    playground = Playground([_pump()])
    chains = playground.find_chains({"sunlight": ENERGY}, {"water_out": VOLUME},
                                    max_depth=2)
    assert chains


def test_chain_search_still_respects_type():
    playground = Playground([_pump()])
    # right name, wrong type: must not fire
    assert playground.find_chains({"electric_energy_in": VOLUME},
                                  {"water_out": VOLUME}, max_depth=2) == []


def test_one_variable_cannot_satisfy_two_parameters():
    mixer = CodeSnippet("COBOL", "mixer", "",
                        {"hot_vol": VOLUME, "cold_vol": VOLUME},
                        {"mixed_vol": VOLUME})
    playground = Playground([mixer])
    # a single stream is not two streams
    assert playground._match_inputs(mixer, {"only_one": VOLUME}) is None
    binding = playground._match_inputs(mixer, {"a": VOLUME, "b": VOLUME})
    assert binding is not None
    assert len(set(binding.values())) == 2


def test_chains_come_back_cheapest_first():
    playground = Playground([_pump()])
    chains = playground.find_chains({"sunlight": ENERGY}, {"water_out": VOLUME},
                                    max_depth=3, max_chains=5)
    costs = [c.total_cost for c in chains]
    assert costs == sorted(costs)


# --- name inference survives snake_case ------------------------------------

@pytest.mark.parametrize("name", [
    "water_out", "pump_water", "energy_in", "temp_rise", "total_mass",
])
def test_snake_case_names_are_typed(name):
    # \b treats "_" as a word character, so these all failed to match and
    # every inferred output type came back empty
    assert recycling_playground.infer_type_from_name(name) is not None


def test_unrelated_names_are_still_untyped():
    for name in ("foo_bar", "handler", "xyzzy"):
        assert recycling_playground.infer_type_from_name(name) is None


def test_extracted_snippets_carry_output_types(tmp_path):
    source = tmp_path / "pump_utils.py"
    source.write_text(
        "def pump_water(energy_in, efficiency):\n"
        "    water_out = energy_in * efficiency / 9.81\n"
        "    return water_out\n")
    snippets = recycling_playground.extract_snippets_from_file(str(source))
    assert snippets
    assert any(s.output_types for s in snippets)


# --- the checker enforces what the taxonomy says ---------------------------

def test_relative_plus_relative_is_rejected():
    with pytest.raises(QuantityError):
        QuantityVar("3pm", 15.0, RELATIVE_TIME) + QuantityVar("4pm", 16.0, RELATIVE_TIME)


def test_relative_minus_relative_still_yields_an_absolute_delta():
    delta = QuantityVar("t1", 17.0, RELATIVE_TIME) - QuantityVar("t2", 9.0, RELATIVE_TIME)
    assert delta.value == 8.0
    assert delta.qtype.datum is Datum.ABSOLUTE


def test_monotone_cannot_be_decremented():
    with pytest.raises(QuantityError):
        QuantityVar("clock", 100.0, MONOTONE) - QuantityVar("d", 1.0, MONOTONE)


def test_convention_residue_rejects_arithmetic():
    with pytest.raises(QuantityError):
        QuantityVar("a", 90210.0, ZIP) + QuantityVar("b", 10001.0, ZIP)
    with pytest.raises(QuantityError):
        QuantityVar("a", 90210.0, ZIP) - QuantityVar("b", 10001.0, ZIP)


def test_intensive_addition_still_rejected():
    temp = QuantityType(Extensivity.INTENSIVE, Conservation.PRODUCIBLE, Datum.ABSOLUTE,
                        Transfer.EQUILIBRATE, (0, 0, 0, 0, 1, 0, 0))
    with pytest.raises(QuantityError):
        QuantityVar("t1", 25.0, temp) + QuantityVar("t2", 30.0, temp)


def test_debit_credit_transfer_conserves_the_total():
    a = QuantityVar("a", 100.0, VOLUME)
    b = QuantityVar("b", 50.0, VOLUME)
    quantity_checker.transfer(a, b, 20.0, Transfer.DEBIT_CREDIT)
    assert a.value == 80.0 and b.value == 70.0
    assert a.value + b.value == 150.0


def test_transfer_refuses_to_overdraw():
    a = QuantityVar("a", 10.0, VOLUME)
    b = QuantityVar("b", 0.0, VOLUME)
    with pytest.raises(QuantityError):
        quantity_checker.transfer(a, b, 25.0, Transfer.DEBIT_CREDIT)
    assert a.value == 10.0
