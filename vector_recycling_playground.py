# vector_recycling_playground.py — recycle vector transforms, respect intensive types.
# CC0. stdlib only. phone-buildable.

import json, os, math, random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from quantity_checker import QuantityType, Extensivity, Conservation, Datum, Transfer, QuantityError

# A vector is an intensive quantity with a specific dimension (embedding length).
def vector_qtype(dim: int) -> QuantityType:
    return QuantityType(
        extensivity=Extensivity.INTENSIVE,
        conservation=Conservation.PRODUCIBLE,
        datum=Datum.RELATIVE,          # arbitrary origin
        transfer=Transfer.COPY,        # copying a vector doesn't drain the source
        dimension=(0, 0, 0, 0, 0, 0, dim),  # last slot = embedding dim, or use a dedicated axis
        signed=True
    )

@dataclass
class VectorSnippet:
    name: str
    input_dims: Dict[str, int]   # var name -> embedding dimension
    output_dims: Dict[str, int]  # var name -> embedding dimension
    # In practice, the actual transform function; here we just simulate with scaling
    transform_cost: float = 1.0  # cost in "vector ops" proportional to total dims

    def apply(self, inputs: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """Simulate transformation: outputs are random but dimension-consistent."""
        outputs = {}
        for name, dim in self.output_dims.items():
            # Simple: weighted average of inputs? For demo, just random unit vector.
            outputs[name] = [random.random() for _ in range(dim)]
        return outputs

class VectorCatalog:
    def __init__(self, snippets: List[VectorSnippet]):
        self.snippets = snippets

    @classmethod
    def from_directory(cls, path: str):
        # For demo, generate synthetic snippets.
        # In real use, load from JSON files describing vector ops (e.g., "project_768_to_256").
        return cls([
            VectorSnippet("normalize", {"v": 768}, {"v_norm": 768}, 0.5),
            VectorSnippet("concat", {"a": 512, "b": 256}, {"ab": 768}, 1.0),
            VectorSnippet("project_high", {"x": 1024}, {"x_proj": 256}, 0.8),
            VectorSnippet("blend", {"v1": 768, "v2": 768}, {"v_blend": 768}, 0.6),
        ])

class VectorPlayground:
    def __init__(self, catalog: VectorCatalog):
        self.catalog = catalog

    def find_chain(self,
                   initial_dims: Dict[str, int],
                   target_dims: Dict[str, int],
                   max_depth=3) -> List[List[VectorSnippet]]:
        """BFS search for sequence of vector transforms that reach target dimensions."""
        from collections import deque
        state = (initial_dims.copy(), [])
        queue = deque([state])
        results = []
        while queue:
            dims, chain = queue.popleft()
            if len(chain) >= max_depth:
                continue
            for snip in self.catalog.snippets:
                # Check if all input names are present with the correct dim
                if not all(v in dims and dims[v] == d for v, d in snip.input_dims.items()):
                    continue
                new_dims = dims.copy()
                new_dims.update(snip.output_dims)
                new_chain = chain + [snip]
                # Check if target is subset
                if all(t in new_dims and new_dims[t] == d for t, d in target_dims.items()):
                    results.append(new_chain)
                else:
                    queue.append((new_dims, new_chain))
        return results

if __name__ == "__main__":
    cat = VectorCatalog.from_directory("dummy")
    pg = VectorPlayground(cat)
    chains = pg.find_chain({"raw_text_emb": 1024}, {"normalized_emb": 768}, max_depth=3)
    for i, chain in enumerate(chains):
        print(f"Chain {i+1}:")
        for step in chain:
            print(f"  {step.name} (in:{step.input_dims} -> out:{step.output_dims})")
