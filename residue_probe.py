#!/usr/bin/env python3
"""
residue_probe.py — E3 fixture. Tests whether label residue is actually inert.
CC0-1.0. stdlib only.

The taxonomy's residue policy says a convention label "means nothing to the
substrate" and "may be carried across languages verbatim". This probe holds
two labels of exactly the kind the construct table calls pure residue — the
"Component/Failure Mode" keys this repo reads from the component database —
and uses them the two ways a label actually gets used.

Run under the harness:
    python3 taxonomy_lab.py e3 residue_probe.py SPEC_A,SPEC_B

The harness permutes the literal values and re-runs. Whatever survives
permutation was genuinely inert; whatever changes was load-bearing.
"""

SPEC_A = "Diode (Silicon)/Short Circuit"
SPEC_B = "Resistor (Carbon Film)/Value Drift"

# The same shape repurpose_table.load_component_matrix produces.
EFFECTIVENESS = {
    "Diode (Silicon)/Short Circuit": 0.9,
    "Resistor (Carbon Film)/Value Drift": 0.6,
}


def identity_only():
    """
    Uses the labels as opaque tokens: equality and distinctness, nothing else.

    This is residue behaving as the policy describes. Permuting which literal
    sits behind which name cannot change the answer, because no property of
    the string is consulted.
    """
    return {
        "distinct": len({SPEC_A, SPEC_B}),
        "same": SPEC_A == SPEC_B,
    }


def used_as_a_key():
    """
    Uses the labels to index the matrix — which is what this repo does.

    The label now selects a magnitude. Permuting the literals sends the same
    name to a different number, so the label is carrying information after
    all. It is inert only until something looks it up.
    """
    return EFFECTIVENESS[SPEC_A]


def main():
    result = identity_only()
    print(f"identity_only  distinct={result['distinct']} same={result['same']}")
    print(f"used_as_a_key  SPEC_A resolves to {used_as_a_key()}")


if __name__ == "__main__":
    main()
