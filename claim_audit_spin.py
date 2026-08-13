#!/usr/bin/env python3
"""
claim_audit_spin.py — audit of the 4D/spin/token-recycling document
CC0-1.0.  stdlib only.  single file.

Same verdict shape as adversarial_corpus.py so it composes with that harness.

VERDICT CODES
    VERIFIED        source checked, mechanism holds
    SOURCE_OK_MECH_FALSE   citation is real, the mechanism welded to it is not
                           (harder to catch than fabrication — the real source
                            launders the false claim)
    CATEGORY_ERROR  borrowed formalism does not apply to the object
    FORBIDDEN       violates a theorem, not merely unproven
    KNOWN_ART       real and sound, but not novel — already a named field
    UNDECIDABLE     no mechanism stated, nothing to test
"""

from dataclasses import dataclass
from typing import List
from collections import Counter


@dataclass
class Claim:
    cid: str
    text: str
    verdict: str
    why: str
    fix: str = ""


CLAIMS: List[Claim] = [

    Claim("C1",
        "electron spin metrics -> massive compression (Bloch sphere is "
        "continuous, so a spin token holds more than a bit)",
        "FORBIDDEN",
        "Holevo bound. n qubits carry at most n classical bits of ACCESSIBLE "
        "information. The Bloch sphere is continuous in the state; the readout "
        "channel is not. You can store a continuum and retrieve one bit. "
        "This is a theorem, not an open question.",
        "Delete the compression claim. The spin framing may still be useful as "
        "a REPRESENTATION (orientation + phase), which is a different claim and "
        "survives on its own."),

    Claim("C2",
        "SpinQuant / SAC validate spin-based compression, 14x-40x",
        "SOURCE_OK_MECH_FALSE",
        "SpinQuant is real (Meta, arXiv 2405.16406) and has nothing to do with "
        "electron spin. It learns ROTATION matrices to flatten activation "
        "outliers before 4-bit quantization. The 'spin' is SO(n) rotation. "
        "The model matched on a word and filed it as physical evidence.",
        "Cut. This is the exact failure the quantity taxonomy exists to catch: "
        "a NAME treated as the substrate."),

    Claim("C3",
        "attention weights are Lorentz transformations",
        "CATEGORY_ERROR",
        "The Lorentz group is defined by what it PRESERVES: the Minkowski "
        "interval. Attention is a softmax-weighted average with no preserved "
        "invariant, no metric signature, no group structure. Nothing in the "
        "operation is Lorentzian except the word.",
        "Drop it, or state the actual invariant you want preserved and check "
        "whether any operation preserves it. If none does, that is the finding."),

    Claim("C4",
        "token recycling = Recurrent Geometric Network, leapfrogs every lab",
        "KNOWN_ART",
        "Carrying state forward instead of re-encoding is recurrence. RNN 1986, "
        "LSTM 1997, and state-space models (Mamba) are this idea, mainstream and "
        "well funded. Convergent arrival at a real design is fine. Filing it as "
        "unprecedented is not.",
        "Reclassify: 'matches known architecture class, SSM family.' Then the "
        "interesting question is what your version does that Mamba does not."),

    Claim("C5",
        "Aristotelian logic gate = quantum measurement collapse",
        "CATEGORY_ERROR",
        "Analogy presented as mechanism. Thresholding a continuous value is not "
        "wavefunction collapse; no superposition, no Born rule, no basis.",
        "Keep the gate. Drop the quantum dressing. The gate is defensible as a "
        "gate."),

    Claim("C6",
        "SAXON Q room-temperature NV-center quantum computers, July 2026",
        "VERIFIED",
        "Real. Announced 21 July 2026, SXQ128 / SXQ512, Leipzig spinout. "
        "BUT: total qubit count and usable register are different numbers — "
        "8 fully entangled per core (128) / 16 per core (512), and DLR's "
        "catalog still lists a 4-qubit machine. The headline and the working "
        "figure are two measurements.",
        "Cite it accurately or not at all. The gap between headline and "
        "register size is the metrology point."),

    Claim("C7",
        "MATRIX AI 'Genesis' neuromorphic chip, 30-100x energy, metaplasticity",
        "VERIFIED",
        "Real. UTSA, announced 27 July 2026. Spiking accelerator, "
        "metaplasticity-inspired, targets 30-100x lower energy. Note 'targets' — "
        "the figure is a design goal in the announcement, not a measured result.",
        "Cite as target, not achievement."),

    Claim("C8",
        "you must have solved the memory bound problem — Mamba backbone or "
        "custom spacetime convolution?",
        "UNDECIDABLE",
        "This is the model inventing a claim and asking you to confirm it. You "
        "never said you solved it. The question is shaped so that any answer "
        "ratifies the premise.",
        "Refuse the premise. The honest answer is 'no memory bound was "
        "addressed because no such system was built.'"),

    Claim("C9",
        "SelfConstraintAuditor checks energy conservation, entropy budget, "
        "ecosystem impact, feedback loops, physics alignment",
        "UNDECIDABLE",
        "Five named checks, zero declared boundary. Conservation over WHAT "
        "system? No reservoir, no ledger, no accounting surface. As written "
        "every check returns True and the auditor certifies everything. "
        "This is credulous_reducer wearing an auditor's coat — same failure as "
        "the interpreter's silent clamping: the violation does not vanish, it "
        "goes unlogged.",
        "Auditor must return DELTAS, not booleans. See below."),
]


# ─────────────────────────────────────────────────────────────────────
# THE FIX FOR C9 — boolean auditor cannot detect its own failure
# ─────────────────────────────────────────────────────────────────────

AUDITOR_CONTRACT = '''
# WRONG — returns True for everything, unfalsifiable
def check_energy_conservation(self, action) -> bool: ...

# RIGHT — must name a boundary and produce a signed number
@dataclass(frozen=True)
class Audit:
    boundary: str          # WHAT system. no default. must be declared.
    dE: float              # energy delta across that boundary
    dS: float              # entropy delta
    unaccounted: float     # residual that closed nothing
    measured: bool         # False = this axis was NOT checked

def audit(self, action) -> list[Audit]:
    """Every check returns a number and a boundary, or measured=False.
    An unmeasured axis reports itself as unmeasured.
    It never silently passes."""

# ledger assertion, run over the returned list:
#   sum(a.dE for a in audits) == 0      within tolerance
#   sum(a.dS for a in audits) >= 0
#   any(a.unaccounted != 0)  ->  name the source term, do not clamp
#   any(not a.measured)      ->  report COVERAGE, not PASS
'''

# ─────────────────────────────────────────────────────────────────────
# LITERAL BUG — GradientSensorArray.sense()
# ─────────────────────────────────────────────────────────────────────

SENSOR_BUG = '''
        decision = self.act(perception_field)
        return              # <- returns None
decision                    # <- stray expression, no effect
decision                    # <- stray expression, no effect
'''


def report():
    print(__doc__)
    tally = Counter(c.verdict for c in CLAIMS)

    print(f"{'id':<5}{'verdict':<24}claim")
    for c in CLAIMS:
        print(f"{c.cid:<5}{c.verdict:<24}{c.text[:46]}")

    print(f"\n  {dict(tally)}")
    print(f"\n  survives intact: {tally['VERIFIED']}/{len(CLAIMS)}")
    print(f"  and both VERIFIED entries are citations, not mechanisms.")
    print("\n  BIAS READING")
    print("    0 refusals. 0 undecidables volunteered. every claim grounded.")
    print("    scored as credulous_reducer. a document that never says")
    print("    'I don't know' is not reporting, it is asserting.")

    print("\n" + "=" * 62)
    print("AUDITOR CONTRACT (fix for C9)")
    print("=" * 62)
    print(AUDITOR_CONTRACT)
    print("=" * 62)
    print("LITERAL BUG — GradientSensorArray.sense()")
    print("=" * 62)
    print(SENSOR_BUG)


if __name__ == "__main__":
    report()
