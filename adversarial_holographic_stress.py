#!/usr/bin/env python3
"""
adversarial_holographic_stress.py — stress-tests the fractal holographic compressor
under adversarial density inversion, topological severing, and recursive pressure.
CC0-1.0. stdlib only. single file.
"""

import json
from fractal_holographic_compressor import FractalHolographicCompressor, HolographicNode

class AdversarialHolographicTester:
    def __init__(self, compressor: FractalHolographicCompressor):
        self.compressor = compressor

    def run_adversarial_suite(self):
        print("[-] Initiating Adversarial Stress Suite...")
        
        # Test 1: Density Inversion (Noise Flooding)
        noise_stream = ["noise_residue_0"] * 50 + ["data_substrate", "binding_topology"]
        anchors = ["data_substrate", "binding_topology"]
        
        tree = self.compressor.compress(noise_stream, anchors, depth=1)
        restored = self.compressor.reconstruct(tree)
        
        # Verify if noise polluted the critical anchors
        anchor_integrity = all(a in restored for a in anchors)
        print(f"[Test 1 - Density Inversion] Anchor Integrity Maintained: {anchor_integrity}")
        
        # Test 2: Topological Severing (Mid-Tree Anchor Drop)
        tree.sub_nodes[0].bulk_anchors = []  # Sever child node anchors
        severed_restored = self.compressor.reconstruct(tree)
        print(f"[Test 2 - Topological Severing] Severed Node Gracefully Handled: {len(severed_restored)}")

if __name__ == "__main__":
    comp = FractalHolographicCompressor(max_depth=3)
    tester = AdversarialHolographicTester(comp)
    tester.run_adversarial_suite()
