# language_translation_table.py — translation effort and effectiveness.
# CC0. stdlib only. Replace with YAML loading if you prefer.

# Table: key = (source_lang, target_lang)
# value = (cost_factor, effectiveness)
#   cost_factor: how much surplus the source must spend (0.1 = cheap)
#   effectiveness: regen gain in target per unit of source surplus (1.0 = perfect)

TRANSLATION_TABLE = {
    ("Python", "COBOL"):   (0.2, 0.7),   # transpiler exists, decent mapping
    ("Python", "Rust"):    (0.3, 0.8),   # PyO3/maturin, good mapping
    ("Rust", "JavaScript"):(0.15, 0.9),  # wasm-bindgen, very efficient
    ("Rust", "COBOL"):     (0.5, 0.3),   # rare, mostly manual
    ("JavaScript", "COBOL"):(0.4, 0.4),  # possible via Node.js bridge
    ("Python", "JavaScript"):(0.1, 0.85),# Transcrypt/Pyodide, excellent
    # Add more as you build your database
}

def get_translation(source, target):
    return TRANSLATION_TABLE.get((source, target), None)

def best_donor_for(target, available_sources, max_cost=1.0):
    """
    Given a target language, find the source with the highest effectiveness
    and a cost <= max_cost that is in the available_sources list.
    Returns (source_lang, cost, effectiveness) or None.
    """
    best = None
    best_eff = -1
    for src in available_sources:
        entry = get_translation(src, target)
        if entry:
            cost, eff = entry
            if cost <= max_cost and eff > best_eff:
                best = (src, cost, eff)
                best_eff = eff
    return best
