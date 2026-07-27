# token_recycling_playground.py — recycle text fragments, respecting token budgets.
# CC0. stdlib only. phone-buildable.

import os, re, random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from quantity_checker import QuantityType, Extensivity, Conservation, Datum, Transfer

# Token count is extensive, non-negative, copyable, with a ceiling (context window).
token_qtype = QuantityType(
    extensivity=Extensivity.EXTENSIVE,
    conservation=Conservation.PRODUCIBLE,
    datum=Datum.ABSOLUTE,
    transfer=Transfer.COPY,
    dimension=(0,0,0,0,0,0,0),
    floor=0,
    ceiling=4096,  # typical context limit
    signed=False
)

@dataclass
class TextFragment:
    text: str
    token_count: int     # extensive: number of tokens (approx words * 1.3)
    quality: float = 1.0 # intensive: information density (0-1)

    def __post_init__(self):
        if self.token_count < 0:
            raise ValueError("Token count cannot be negative (floor)")

class TokenCatalog:
    def __init__(self, fragments: List[TextFragment]):
        self.fragments = fragments

    @classmethod
    def from_text_files(cls, directory: str, max_files=100):
        """Scan .txt and .md files, split into sentences as fragments."""
        fragments = []
        for root, _, files in os.walk(directory):
            for fname in files:
                if fname.endswith(('.txt', '.md')) and len(fragments) < max_files:
                    path = os.path.join(root, fname)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        # Rough sentence split
                        sentences = re.split(r'[.!?]+', text)
                        for sent in sentences:
                            sent = sent.strip()
                            if len(sent) < 10:
                                continue
                            # Approximate token count (words * 1.3)
                            words = sent.split()
                            token_count = max(1, int(len(words) * 1.3))
                            fragments.append(TextFragment(sent, token_count))
                    except Exception:
                        pass
        return cls(fragments)

class TokenPlayground:
    def __init__(self, catalog: TokenCatalog, budget: int = 4096):
        self.catalog = catalog
        self.budget = budget

    def assemble_response(self, required_keywords: List[str],
                          max_fragments=5) -> List[TextFragment]:
        """Greedy selection of fragments covering keywords while staying under budget."""
        used_budget = 0
        selected = []
        # Simple keyword matching
        available = list(self.catalog.fragments)
        random.shuffle(available)
        for frag in available:
            if any(kw.lower() in frag.text.lower() for kw in required_keywords):
                if used_budget + frag.token_count <= self.budget and len(selected) < max_fragments:
                    selected.append(frag)
                    used_budget += frag.token_count
        return selected

if __name__ == "__main__":
    # Demo with synthetic catalog
    demo_frags = [
        TextFragment("Water is a liquid at room temperature.", 7),
        TextFragment("Energy conservation is a fundamental law.", 6),
        TextFragment("Mixing hot and cold water yields warm water.", 8),
        TextFragment("The pump converts electrical energy to flow.", 7),
        TextFragment("Solar radiation provides renewable energy.", 6),
    ]
    cat = TokenCatalog(demo_frags)
    pg = TokenPlayground(cat, budget=30)
    response = pg.assemble_response(["water", "energy"])
    for f in response:
        print(f"- [{f.token_count} tokens] {f.text}")
