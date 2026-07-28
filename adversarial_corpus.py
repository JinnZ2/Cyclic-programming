#!/usr/bin/env python3
"""
adversarial_corpus.py — bias probe for any substrate reducer
CC0-1.0.  stdlib only.  single file.

WHAT THIS IS FOR
    A reducer that grounds EVERYTHING in physics and a reducer that
    calls EVERYTHING inert are both broken, in opposite directions,
    and neither can detect its own failure from success rate alone.

    A 100% grounding rate is not evidence the substrate claim is true.
    It is exactly what you would see if the reducer refuses to report
    failure. Same shape as a constraint "satisfied" by silent clamping:
    the overflow did not go away, it went somewhere unlogged.

    So this corpus is built with an ANSWER KEY and cases pointing BOTH
    directions. Scoring reports the two error types separately. The
    asymmetry between them IS the bias measurement.

FIVE CATEGORIES
    GROUNDED    real physics. calling these inert = under-grounding.
    INERT       real convention. grounding these = forced fit.
    TRAP_FAKE   convention wearing physics clothing.
    TRAP_REAL   physics wearing convention clothing.
    UNDECIDABLE insufficient information. a confident answer here is
                a hallucination, and "unknown" is the CORRECT answer.

    UNDECIDABLE is the calibration test. Without it you only measure
    accuracy, never honesty.

HOW THIS TEST CAN ITSELF BE WRONG
    - The key is my judgement, not ground truth. Entries marked
      key_confidence="contested" are ones I can argue both ways.
      If your reducer disagrees there, the KEY may be the thing at fault.
    - The corpus is small and hand-built, so it can only detect gross
      bias, not fine miscalibration.
    - Cases are Python-shaped. A reducer tuned on Python may score well
      here and fail on COBOL or Forth.
    Report these limits alongside any score. A benchmark that hides its
    own failure modes is the thing it was built to catch.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict
from collections import Counter
import ast
import random
import sys


# ─────────────────────────────────────────────────────────────────────
# CASE STRUCTURE
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Case:
    cid: str
    category: str          # GROUNDED | INERT | TRAP_FAKE | TRAP_REAL | UNDECIDABLE
    binding: str           # which name is under test
    source: str
    key_grounded: Optional[bool]   # True | False | None(=undecidable)
    key_axes: Dict[str, str] = field(default_factory=dict)
    why: str = ""
    key_confidence: str = "firm"   # firm | contested
    permutable: bool = False       # behavior test available


CORPUS: List[Case] = []


def case(**kw):
    CORPUS.append(Case(**kw))


# ─────────────────────────────────────────────────────────────────────
# GROUNDED — must reduce. calling these inert = under-grounding bias.
# ─────────────────────────────────────────────────────────────────────

case(
    cid="G1", category="GROUNDED", binding="balance",
    source="""
def transfer(src, dst, amt):
    src.balance -= amt
    dst.balance += amt
    return src.balance + dst.balance
""",
    key_grounded=True,
    key_axes={"extensivity": "EXTENSIVE", "conservation": "CONSERVED",
              "transfer": "DEBIT_CREDIT"},
    why="paired debit/credit, sum invariant. textbook conserved extensive.",
)

case(
    cid="G2", category="GROUNDED", binding="total_mass",
    source="""
total_mass = 0.0
for part in parts:
    total_mass += part.kg
""",
    key_grounded=True,
    key_axes={"extensivity": "EXTENSIVE", "domain": "FLOORED",
              "dimension": "DIMENSIONED", "datum": "ABSOLUTE"},
    why="additive over subsystems, hard floor at 0, real zero, M dimension.",
)

case(
    cid="G3", category="GROUNDED", binding="seq",
    source="""
seq = 0
def next_id():
    global seq
    seq += 1
    return seq
""",
    key_grounded=True,
    key_axes={"conservation": "MONOTONE", "domain": "FLOORED"},
    why="strictly increasing, never decremented. monotone is a real axis value.",
)

case(
    cid="G4", category="GROUNDED", binding="temp_c",
    source="""
temp_c = read_sensor()
delta = temp_c - baseline_c
avg = (a_temp * a_mass + b_temp * b_mass) / (a_mass + b_mass)
""",
    key_grounded=True,
    key_axes={"extensivity": "INTENSIVE", "datum": "RELATIVE",
              "transfer": "EQUILIBRATE"},
    why="intensive, arbitrary zero, correctly mass-weighted when combined.",
)


# ─────────────────────────────────────────────────────────────────────
# INERT — must be reported as residue. grounding these = forced fit.
# ─────────────────────────────────────────────────────────────────────

case(
    cid="I1", category="INERT", binding="COUNTRY",
    source="""
COUNTRY = "SE"
if COUNTRY in ("SE", "NO", "FI"):
    region = "nordic"
""",
    key_grounded=False,
    key_axes={}, why="ISO 3166 label. membership test only. no metric, no order.",
)

case(
    cid="I2", category="INERT", binding="ENDPOINT",
    source="""
ENDPOINT = "/api/v2/orders"
resp = client.get(ENDPOINT)
""",
    key_grounded=False,
    key_axes={}, why="pure naming convention. the string could be anything.",
)

case(
    cid="I3", category="INERT", binding="user_uuid",
    source="""
user_uuid = "550e8400-e29b-41d4-a716-446655440000"
row = table[user_uuid]
""",
    key_grounded=False, permutable=True,
    key_axes={}, why="opaque key. only identity/equality used. value carries nothing.",
)


# ─────────────────────────────────────────────────────────────────────
# TRAP_FAKE — looks like a quantity. is not. grounding it = forced fit.
# ─────────────────────────────────────────────────────────────────────

case(
    cid="F1", category="TRAP_FAKE", binding="zip_code",
    source="""
zip_code = 55802
if 55000 <= zip_code <= 56000:
    zone = "MN"
avg_zip = sum(all_zips) / len(all_zips)
""",
    key_grounded=False, permutable=True,
    key_axes={},
    why=("int-shaped, ordered-looking, arithmetic runs without error and is "
         "meaningless. avg_zip is the tell. a reducer that types this FLOORED "
         "EXTENSIVE has been fooled by the storage type."),
)

case(
    cid="F2", category="TRAP_FAKE", binding="priority",
    source="""
LOW, MED, HIGH = 1, 2, 3
priority = MED
score = priority * weight
""",
    key_grounded=False,
    key_axes={},
    why=("ordinal labels, not a magnitude. HIGH is not 3x LOW. multiplication "
         "is a category error the type system permits."),
    key_confidence="contested",
)

case(
    cid="F3", category="TRAP_FAKE", binding="version",
    source="""
version = 311
if version > 39:
    use_new_parser()
""",
    key_grounded=False,
    key_axes={},
    why=("looks monotone. 3.11 > 3.9 is TRUE by version order and FALSE by "
         "decimal order. the int encoding smuggles a broken comparison."),
)

case(
    cid="F4", category="TRAP_FAKE", binding="heading",
    source="""
heading = 350
heading = heading + 20
if heading > start:
    turned_right = True
""",
    key_grounded=False,
    key_axes={},
    why=("cyclic quantity treated as linear. 350+20=370, not 10. the comparison "
         "is unsound on a circle. cyclic topology is not in the 7 axes at all."),
    key_confidence="contested",
)


# ─────────────────────────────────────────────────────────────────────
# TRAP_REAL — looks arbitrary. is grounded. calling it inert = miss.
# this pair (I3 vs R1) is the whole ID question, made behavioral.
# ─────────────────────────────────────────────────────────────────────

case(
    cid="R1", category="TRAP_REAL", binding="cell",
    source="""
cell = "9q8yyk"
neighbors = [c for c in index if c[:4] == cell[:4]]
dist = shared_prefix_len(cell, other)
""",
    key_grounded=True, permutable=True,
    key_axes={"dimension": "DIMENSIONED", "datum": "RELATIVE"},
    why=("geohash. string-shaped, opaque-looking, IDENTICAL surface form to a "
         "UUID. but prefix length encodes spatial locality. permute the values "
         "and behavior changes. this is why 'int(id) -> all residue' is wrong: "
         "I3 and R1 are the same syntactic type with opposite answers."),
)

case(
    cid="R2", category="TRAP_REAL", binding="level",
    source="""
level = "n2"
occupancy[level] += 1
emitted = energy_of(level) - energy_of(ground)
""",
    key_grounded=True,
    key_axes={"extensivity": "INTENSIVE", "datum": "RELATIVE"},
    why="string label indexes a real ordered energy spectrum. differences are physical.",
)

case(
    cid="R3", category="TRAP_REAL", binding="flag_bits",
    source="""
flag_bits = 0
flag_bits |= DIRTY
flag_bits &= ~CACHED
""",
    key_grounded=True,
    key_axes={"dimension": "DIMENSIONLESS", "cost": "ERASE"},
    why=("looks like arbitrary bookkeeping. is literally bits. the &= ~ is an "
         "erasure with a kT ln2 floor. one of the few places Landauer is exact."),
)


# ─────────────────────────────────────────────────────────────────────
# UNDECIDABLE — "unknown" is the CORRECT answer. confidence here = lie.
# ─────────────────────────────────────────────────────────────────────

case(
    cid="U1", category="UNDECIDABLE", binding="x",
    source="""
x = 5
""",
    key_grounded=None, key_axes={},
    why="no usage, no unit, no neighbor. any typing is invented.",
)

case(
    cid="U2", category="UNDECIDABLE", binding="rate",
    source="""
rate = load_config()["rate"]
apply(rate)
""",
    key_grounded=None, key_axes={},
    why=("name suggests INTENSIVE. the name is exactly what the reduction "
         "claims to discard. typing this from the name is the failure mode "
         "under test, dressed as a success."),
)

case(
    cid="U3", category="UNDECIDABLE", binding="count",
    source="""
count = fetch(remote)
merged = count + other_count
""",
    key_grounded=None, key_axes={},
    why=("addition suggests EXTENSIVE, but the addition may itself be the bug. "
         "cannot distinguish correct summation from a category error without "
         "knowing the source semantics."),
    key_confidence="contested",
)


# ─────────────────────────────────────────────────────────────────────
# ADAPTER INTERFACE — wire your playground in here
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Verdict:
    grounded: Optional[bool]        # True | False | None(="cannot determine")
    axes: Dict[str, str] = field(default_factory=dict)
    note: str = ""


Reducer = Callable[[str, str], Verdict]   # (source, binding) -> Verdict


def null_reducer(source, binding):
    """Control: refuses everything. should score as CONVENTION-BIASED."""
    return Verdict(grounded=False, note="baseline: refuse all")


def credulous_reducer(source, binding):
    """Control: grounds everything. should score as PHYSICS-BIASED.
    run this first. if your real reducer scores like this one,
    it is not reducing, it is asserting."""
    return Verdict(grounded=True, axes={"extensivity": "EXTENSIVE"},
                   note="baseline: ground all")


def pretype_reducer(source, binding):
    """
    This repo's actual reducer: taxonomy_lab.pretype, the heuristic pre-typer.

    Mapping to the Verdict interface, stated explicitly because it affects
    the score: pretype has no way to output "inert" — it emits axis values or
    UNTYPED, and there is no residue verdict in its vocabulary. So any axis it
    infers is read as grounded=True, and inferring nothing is read as an
    abstention rather than as a claim of convention. That is the charitable
    reading; the uncharitable one would score every abstention as a miss.
    """
    import taxonomy_lab as T

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return Verdict(grounded=None, note=f"parse failed: {exc}")

    extractor = T.BindingExtractor("<case>")
    extractor.visit(tree)
    sites = [s for (_scope, name), s in extractor.sites.items() if name == binding]
    if not sites:
        return Verdict(grounded=None, note=f"binding {binding!r} not found")

    # a name may bind in several scopes (e.g. a global rebound in a function);
    # merge so the reducer sees every use, as it would in a real corpus
    site = max(sites, key=lambda s: (s.n_writes + s.n_reads))
    for other in sites:
        if other is site:
            continue
        site.n_writes += other.n_writes
        site.n_reads += other.n_reads
        site.augmented = site.augmented or other.augmented
        site.is_loop_var = site.is_loop_var or other.is_loop_var
        site.literal_kinds = site.literal_kinds + other.literal_kinds

    axes = T.pretype(site)
    inferred = {a: v for a, v in axes.items() if v != T.UNTYPED}
    if not inferred:
        return Verdict(grounded=None, axes={}, note="no axis inferred")
    return Verdict(grounded=True, axes=inferred,
                   note=f"inferred {len(inferred)} axis value(s)")


# ─────────────────────────────────────────────────────────────────────
# SCORING — two error types, reported separately. the gap is the bias.
# ─────────────────────────────────────────────────────────────────────

def score(reducer: Reducer, corpus=CORPUS, verbose=True):
    tally = Counter()
    rows = []

    for c in corpus:
        v = reducer(c.source, c.binding)
        g, k = v.grounded, c.key_grounded

        if k is None:
            outcome = "OK_ABSTAIN" if g is None else "OVERCONFIDENT"
        elif g is None:
            outcome = "ABSTAIN_ON_DECIDABLE"
        elif g == k:
            outcome = "OK"
        elif k is False and g is True:
            outcome = "FORCED_FIT"
        else:
            outcome = "MISSED_GROUNDING"

        tally[outcome] += 1
        rows.append((c, v, outcome))

    if verbose:
        print(f"\n{'id':<5}{'category':<13}{'key':<7}{'said':<7}{'outcome':<22}conf")
        for c, v, o in rows:
            ks = {True: "phys", False: "inert", None: "?"}[c.key_grounded]
            gs = {True: "phys", False: "inert", None: "?"}[v.grounded]
            flag = "*" if c.key_confidence == "contested" else ""
            print(f"{c.cid:<5}{c.category:<13}{ks:<7}{gs:<7}{o:<22}{flag}")

    ff = tally["FORCED_FIT"]
    mg = tally["MISSED_GROUNDING"]
    oc = tally["OVERCONFIDENT"]
    ok = tally["OK"] + tally["OK_ABSTAIN"]
    n = len(corpus)

    print(f"\n  correct              {ok}/{n}")
    print(f"  FORCED_FIT           {ff}   (called convention 'physics')")
    print(f"  MISSED_GROUNDING     {mg}   (called physics 'convention')")
    print(f"  OVERCONFIDENT        {oc}   (answered an undecidable case)")
    print(f"  abstain-on-decidable {tally['ABSTAIN_ON_DECIDABLE']}")

    print("\n  BIAS READING")
    if ff == mg == 0:
        print("    balanced on direction.")
    elif ff > mg:
        print(f"    PHYSICS-BIASED. forces fits {ff}:{mg}.")
        print("    a perfect grounding rate from this reducer is not evidence.")
    elif mg > ff:
        print(f"    CONVENTION-BIASED. refuses to ground {mg}:{ff}.")
    if oc:
        print(f"    MISCALIBRATED. answered {oc} case(s) that carry no answer.")
        print("    it cannot say 'I don't know', so its confidence means nothing.")

    contested = sum(1 for c, v, o in rows
                    if c.key_confidence == "contested" and not o.startswith("OK"))
    if contested:
        print(f"\n  note: {contested} miss(es) fall on CONTESTED key entries.")
        print("  those may be the key's fault, not the reducer's. argue them.")

    return tally


# ─────────────────────────────────────────────────────────────────────
# BEHAVIORAL CHECK — settles TRAP cases without appeal to the key
# ─────────────────────────────────────────────────────────────────────

def permutation_note():
    print("""
BEHAVIORAL SETTLEMENT (no key required)

  For any case marked permutable, the argument does not need my
  judgement. Permute the literal values, hold topology fixed, rerun:

      behavior identical  -> value was inert. edge only.
      behavior changed    -> value carried a quantity. inert was wrong.

  I3  uuid    -> permute: dict still maps. INERT confirmed.
  R1  geohash -> permute: prefix neighbors dissolve. GROUNDED confirmed.
  F1  zip     -> permute: the range test misfires. the int was fake.

  I3 and R1 are the same surface type with opposite verdicts, decided
  by behavior rather than by naming. That is the ID question answered:
  labels are not a uniform category, so 'int(id) -> all residue' in the
  taxonomy is false as written and needs splitting into
  OPAQUE_LABEL vs ENCODED_POSITION.
""")


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(__doc__.split("HOW THIS TEST")[0])
    print(f"corpus: {len(CORPUS)} cases  "
          f"{dict(Counter(c.category for c in CORPUS))}")

    print("\n" + "=" * 62)
    print("CONTROL 1 — credulous reducer (grounds everything)")
    print("=" * 62)
    score(credulous_reducer)

    print("\n" + "=" * 62)
    print("CONTROL 2 — null reducer (refuses everything)")
    print("=" * 62)
    score(null_reducer)

    print("\n" + "=" * 62)
    print("UNDER TEST — taxonomy_lab.pretype (this repo's reducer)")
    print("=" * 62)
    score(pretype_reducer)

    permutation_note()
