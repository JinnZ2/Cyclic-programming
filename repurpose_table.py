# repurpose_table.py — what can be repurposed into what, and at what cost.
# CC0. stdlib only.
#
# One table shape serves both domains this repo models:
#   (source, target) -> (cost, effectiveness)
#     cost          : share of the donor's surplus spent making the swap
#     effectiveness : capacity delivered to the target per unit spent
#
# For languages, source/target are language names and a transpiler is the
# swap. For hardware, source is "Component/Failure Mode" and target is the
# job the degraded part can still do. Same arithmetic either way, which is
# the point — see component_repurpose.py.

import csv
import os

# Fallback used when no CSV is supplied. Costs here are hand-estimates of
# transpiler maturity, not measurements.
DEFAULT_LANGUAGE_TABLE = {
    ("Python", "COBOL"):      (0.2, 0.7),   # transpilers exist, decent mapping
    ("Python", "Rust"):       (0.3, 0.8),   # PyO3/maturin
    ("Python", "JavaScript"): (0.1, 0.85),  # Transcrypt/Pyodide
    ("Rust", "JavaScript"):   (0.15, 0.9),  # wasm-bindgen
    ("Rust", "COBOL"):        (0.5, 0.3),   # rare, mostly manual
    ("JavaScript", "COBOL"):  (0.4, 0.4),   # possible via a Node bridge
}

# The component database grades effectiveness qualitatively; these are the
# numeric stand-ins. Cost is not a column in that data, so it is derived as
# (1 - effectiveness): a poorer repurpose takes more work to press into service.
GRADE_TO_EFFECTIVENESS = {"high": 0.9, "medium": 0.6, "low": 0.3}


def load_csv(path=None):
    """
    Load a table from a CSV with columns: source,target,cost,effectiveness.

    Returns a dict of (source, target) -> (cost, effectiveness). Falls back to
    DEFAULT_LANGUAGE_TABLE when path is None or missing, so callers can run
    offline without special-casing.
    """
    if path is None or not os.path.isfile(path):
        return dict(DEFAULT_LANGUAGE_TABLE)

    table = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                table[(row["source"].strip(), row["target"].strip())] = (
                    float(row["cost"]), float(row["effectiveness"]))
            except (KeyError, ValueError, AttributeError):
                continue  # skip malformed rows rather than failing the load
    return table


def load_component_matrix(path):
    """
    Load matrices/repurpose_effectiveness.csv from the component-failure
    database into the same (source, target) -> (cost, effectiveness) shape.

    Source keys are "Component/Failure Mode" so that the same physical part
    appears once per way it can fail — a shorted diode and an open one are
    different donors offering different jobs.

    Raises FileNotFoundError if the matrix is not vendored locally; see
    fieldlink.py for where it is expected to live.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"component matrix not found at {path} — run fieldlink.py to see "
            "which sources are missing")

    table = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            component = (row.get("Component") or "").strip()
            mode = (row.get("Failure Mode") or "").strip()
            target = (row.get("Repurpose Application") or "").strip()
            grade = (row.get("Effectiveness") or "").strip().lower()
            if not (component and mode and target):
                continue
            effectiveness = GRADE_TO_EFFECTIVENESS.get(grade)
            if effectiveness is None:
                continue
            table[(f"{component}/{mode}", target)] = (
                round(1.0 - effectiveness, 2), effectiveness)
    return table


def get_translation(source, target, table=None):
    """Look up one pair. Returns (cost, effectiveness) or None."""
    return (table if table is not None else DEFAULT_LANGUAGE_TABLE).get(
        (source, target))


def best_donor_for(target, available_sources, max_cost=1.0, table=None):
    """
    Pick the most effective affordable donor for target from available_sources.

    Returns (source, cost, effectiveness), or None when nothing in
    available_sources can be converted into target within max_cost.
    """
    best = None
    best_eff = -1.0
    for source in available_sources:
        entry = get_translation(source, target, table)
        if entry is None:
            continue
        cost, eff = entry
        if cost <= max_cost and eff > best_eff:
            best, best_eff = (source, cost, eff), eff
    return best


def targets_for(source, table):
    """Every job `source` can be repurposed into, best effectiveness first."""
    hits = [(tgt, cost, eff) for (src, tgt), (cost, eff) in table.items()
            if src == source]
    return sorted(hits, key=lambda row: -row[2])


# --- self-test -------------------------------------------------------------

def _t_default_table_used_when_path_missing():
    assert load_csv(None) == DEFAULT_LANGUAGE_TABLE
    assert load_csv("/nonexistent/table.csv") == DEFAULT_LANGUAGE_TABLE
    # returns a copy — mutating it must not poison the module default
    t = load_csv(None)
    t[("X", "Y")] = (0.0, 0.0)
    assert ("X", "Y") not in DEFAULT_LANGUAGE_TABLE


def _t_best_donor_prefers_effectiveness():
    # Python->COBOL is 0.7, Rust->COBOL is 0.3, so Python wins
    assert best_donor_for("COBOL", ["Python", "Rust"])[0] == "Python"


def _t_best_donor_respects_max_cost():
    # Rust->COBOL costs 0.5; capping below that leaves no donor
    assert best_donor_for("COBOL", ["Rust"], max_cost=0.4) is None
    assert best_donor_for("COBOL", ["Rust"], max_cost=0.5)[0] == "Rust"


def _t_unknown_pair_returns_none():
    assert get_translation("COBOL", "Haskell") is None
    assert best_donor_for("Haskell", ["Python", "Rust"]) is None


def _t_component_matrix_missing_file_raises():
    try:
        load_component_matrix("/nonexistent/matrix.csv")
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


def _run():
    for name, fn in sorted(globals().items()):
        if name.startswith("_t_"):
            fn()
            print("ok", name)
    print("all pass")


if __name__ == "__main__":
    _run()
