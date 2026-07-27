#!/usr/bin/env python3
# repurpose_workshop.py — unified recycling and creative playground.
# CC0. stdlib only. phone‑buildable.
#
# Usage:
#   python repurpose_workshop.py /path/to/waste_code_dir
#   Then enter problem specs at the prompt (or modify main()).

import os
import sys
import json
from recycling_playground import WasteCatalog
from code_playground import Playground
from quantity_checker import QuantityType, Extensivity, Conservation, Datum, Transfer

# ----------------------------------------------------------------------
# Helper to define quantity types from a simple JSON-like dict for CLI
# ----------------------------------------------------------------------
def qtype_from_dict(d: dict) -> QuantityType:
    return QuantityType(
        extensivity=getattr(Extensivity, d.get("extensivity", "EXTENSIVE")),
        conservation=getattr(Conservation, d.get("conservation", "PRODUCIBLE")),
        datum=getattr(Datum, d.get("datum", "ABSOLUTE")),
        transfer=getattr(Transfer, d.get("transfer", "COPY")),
        dimension=tuple(d.get("dimension", (0,0,0,0,0,0,0))),
        floor=d.get("floor"),
        ceiling=d.get("ceiling"),
        signed=d.get("signed", True),
    )

# ----------------------------------------------------------------------
# Default problem: water/energy repurpose
# ----------------------------------------------------------------------
DEFAULT_INITIAL = {
    "energy_in": {
        "extensivity": "EXTENSIVE", "conservation": "CONSERVED",
        "datum": "ABSOLUTE", "transfer": "DEBIT_CREDIT",
        "dimension": [1,2,-2,0,0,0,0], "floor": 0.0
    },
    "cold_vol": {
        "extensivity": "EXTENSIVE", "conservation": "CONSERVED",
        "datum": "ABSOLUTE", "transfer": "DEBIT_CREDIT",
        "dimension": [0,3,0,0,0,0,0], "floor": 0.0
    },
    "cold_temp": {
        "extensivity": "INTENSIVE", "conservation": "PRODUCIBLE",
        "datum": "RELATIVE", "transfer": "EQUILIBRATE",
        "dimension": [0,0,0,0,1,0,0]
    },
}

DEFAULT_TARGET = {
    "mixed_vol": {
        "extensivity": "EXTENSIVE", "conservation": "CONSERVED",
        "datum": "ABSOLUTE", "transfer": "DEBIT_CREDIT",
        "dimension": [0,3,0,0,0,0,0], "floor": 0.0
    },
    "mixed_temp": {
        "extensivity": "INTENSIVE", "conservation": "PRODUCIBLE",
        "datum": "RELATIVE", "transfer": "EQUILIBRATE",
        "dimension": [0,0,0,0,1,0,0]
    },
}

# ----------------------------------------------------------------------
# Main workshop runner
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python repurpose_workshop.py <waste_code_directory>")
        sys.exit(1)
    waste_dir = sys.argv[1]
    if not os.path.isdir(waste_dir):
        print(f"Error: {waste_dir} not found.")
        sys.exit(1)

    print(f"Scanning waste in {waste_dir} ...")
    catalog = WasteCatalog(waste_dir)
    print(f"Found {len(catalog.snippets)} reusable snippets.\n")

    # Load problem definition (from stdin or defaults)
    # In a real tool, you'd load a JSON file; here we use built‑ins.
    initial = {name: qtype_from_dict(spec) for name, spec in DEFAULT_INITIAL.items()}
    target = {name: qtype_from_dict(spec) for name, spec in DEFAULT_TARGET.items()}

    # Build playground from waste catalog
    playground = Playground(catalog.snippets)
    chains = playground.find_chains(initial, target, max_depth=4, max_chains=5)

    if not chains:
        print("No repurpose chain found for the given problem. Try a larger waste base or different specs.")
    else:
        print(f"Found {len(chains)} repurpose chain(s):\n")
        for i, chain in enumerate(chains):
            print(f"--- Chain {i+1} (cost {chain.total_cost:.3f}) ---")
            for step in chain.steps:
                print(f"  [{step.language}] {step.name}")
                if step.description:
                    print(f"      {step.description}")
            print()

    # Optionally, output as JSON for further processing
    if "--json" in sys.argv:
        output = []
        for chain in chains:
            output.append([{
                "language": s.language,
                "name": s.name,
                "code": s.code[:200] + "..." if len(s.code) > 200 else s.code
            } for s in chain.steps])
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
