# language_repurpose_loader.py — load translation table from CSV.
# CC0. stdlib only. phone-buildable.
#
# Expected CSV format:
#   source,target,cost,effectiveness
#   Python,COBOL,0.2,0.7
#   Python,Rust,0.3,0.8
#   Rust,JavaScript,0.15,0.9
#   ...

import csv
import os

DEFAULT_TABLE = {
    ("Python", "COBOL"):      (0.2, 0.7),
    ("Python", "Rust"):       (0.3, 0.8),
    ("Rust", "JavaScript"):   (0.15, 0.9),
    ("Rust", "COBOL"):        (0.5, 0.3),
    ("JavaScript", "COBOL"):  (0.4, 0.4),
    ("Python", "JavaScript"): (0.1, 0.85),
}

def load_translation_table(filepath=None):
    """
    Load translation table from a CSV file. If filepath is None or not found,
    return DEFAULT_TABLE.
    Returns dict: (source, target) -> (cost, effectiveness).
    """
    if filepath is None or not os.path.isfile(filepath):
        return dict(DEFAULT_TABLE)  # return a copy

    table = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip header
        for row in reader:
            if len(row) < 4:
                continue
            source, target, cost_str, eff_str = row[0], row[1], row[2], row[3]
            try:
                cost = float(cost_str)
                eff = float(eff_str)
            except ValueError:
                continue
            table[(source.strip(), target.strip())] = (cost, eff)
    return table
