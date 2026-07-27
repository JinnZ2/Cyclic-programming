# Quantity Taxonomy

Physics-quantity type vocabulary for substrate-anchored code reduction.

License: CC0-1.0

Implemented in `quantity.py`. Applied to this repo's interpreter in
`quantity_audit.py`.

---

## Thesis

```
Legacy waste = every layer re-derives physical constraints
               that were never written down once at the bottom.

Anchor: constraints are not programmer intent.
        Constraints are properties of what KIND of quantity a cell holds.

        Type the quantity -> the constraints fall out for free.
        Nothing above can silently leak.
```

## Reduction rule

```
NAME  ──reduces to──►  ( BINDING_TOPOLOGY , QUANTITY_TYPE , CONVENTION_RESIDUE )

  BINDING_TOPOLOGY   : who writes, who reads, lifetime, scope
                       language-independent, recoverable from code
  QUANTITY_TYPE      : the 7 axes below
                       language-independent, currently smuggled in the name
  CONVENTION_RESIDUE : pure social fact (zip code, ISO country code)
                       NOT recoverable, NOT physical, mark and move on

Two programs with identical topology + quantity types ARE the same program.
Names differing is not a difference.
```

## The seven axes

**Axis 1 — Extensivity.** Does it add over subsystems?

| | |
|---|---|
| `EXTENSIVE` | mass, energy, count, inventory, money — `SUM` is legal |
| `INTENSIVE` | temperature, density, rate, ratio, price — `SUM` is a category error |

Intensives combine only as extensive-weighted averages.

**Axis 2 — Conservation.** Behavior of the system total.

| | |
|---|---|
| `CONSERVED` | total invariant under transfer (zero-sum) |
| `MONOTONE` | only ever increases — entropy, counters, clocks |
| `PRODUCIBLE` | freely created/destroyed — log lines, requests |

**Axis 3 — Domain.** Where the value lives.

| | |
|---|---|
| `FLOORED` | hard bottom, usually 0 — water, count, mass |
| `SIGNED` | negative is meaningful — delta, position, net balance |
| `BOUNDED[a,b]` | hard interval — probability, fraction, coherence |
| `CEILINGED` | capacity-limited — buffer, tank, `PIC 9(n)` |

**Axis 4 — Datum.** Is the zero real or arbitrary?

| | |
|---|---|
| `ABSOLUTE` | zero is physical — kelvin, mass, count |
| `RELATIVE` | zero is a convention — celsius, epoch time, x-position |

`RELATIVE - RELATIVE = ABSOLUTE(delta)`. `RELATIVE + RELATIVE = MEANINGLESS`.

**Axis 5 — Dimension.** The unit vector `(M,L,T,I,Θ,N,J)`.

Addition requires identical dimension; multiplication composes dimension;
transcendental functions (`log`, `exp`, `sin`) require a dimensionless argument.

**Axis 6 — Transfer.** How it moves between cells.

| | |
|---|---|
| `DEBIT_CREDIT` | source loses exactly what target gains — matter, money |
| `COPY` | source unchanged, target gains — **information** |
| `CONSUME` | destroyed on read — token, queue message |
| `EQUILIBRATE` | cannot move, only levels out — intensive |

**Axis 7 — Cost floor.** Thermodynamic price of operating on it.

| | |
|---|---|
| `ERASE` | ≥ `kT ln2` per bit destroyed (Landauer) |
| `COPY` | ~0, reversible in principle |
| `TRANSFORM` | ≥ entropy produced by the map |

## What falls out free

| Given | Derived without declaration |
|---|---|
| `floor=0` | underflow is a type error; "never negative" needs no comment (no negative water) |
| `INTENSIVE` | `sum()` rejected; mean-of-means rejected; must supply extensive weight |
| `CONSERVED` + `DEBIT_CREDIT` | every write demands a paired write; orphan credit = unbalanced ledger |
| `RELATIVE` datum | `a + b` rejected; `a - b` legal, yields `ABSOLUTE` (why dates subtract but never add) |
| dimension mismatch | addition rejected — Mars Climate Orbiter class of bug |
| `MONOTONE` | any decrement is a fault; clock rollback detectable |
| `BOUNDED[0,1]` | the coherence overflow cannot be written |
| `COPY` transfer | flags the waste thesis directly: information is the only quantity whose transfer does not debit the source, which is exactly why nobody accounts for it, which is exactly why it piles up. Landauer restores the price at `ERASE`. |

## Construct reduction table

| Language construct | Substrate form | Residue |
|---|---|---|
| `bool` | binary state, 1 bit; erase cost `kT ln2` | none |
| `int` (counter) | `EXTENSIVE` / `MONOTONE` / `floor=0`, dimensionless | none |
| `int` (id) | pure label; ordering and addition must be **rejected** | all of it |
| `float` (measure) | carries dimension + datum; precision is the PIC-clause analogue | unit choice |
| `string` | sequence over alphabet + encoding; length is `EXTENSIVE` | encoding, collation, locale |
| `enum` | finite state set, no metric | the labels |
| conditional | logic gate, branch; cost floor at the erasure | none |
| loop | repeated traversal; iteration count `EXTENSIVE` `MONOTONE` | none |
| function | map between typed quantities; must preserve or declare dimension | the name |
| reference | edge in `BINDING_TOPOLOGY` | none |
| `null` | absence, distinct from zero (dry soil is not negative water) | none |

## Residue policy

After typing, what remains is genuinely non-physical. It is small. Do not
attempt to reduce it — tag it and stop.

```
convention="US_ZIP"     integer-shaped, arithmetic FORBIDDEN
convention="ISO3166"    string-shaped, ordering meaningless
convention="UTF8"       encoding choice, not a property of the text
```

Residue is inert. It may be carried across languages verbatim because it means
nothing to the substrate. That is why it is recyclable rather than translatable.

In `quantity.py` a residue tag makes both arithmetic and ordering raise
`ConventionError`.

---

## Applying it here

`quantity_audit.py` declares a `QuantityType` for each field of the
interpreter's `EnergyState` and runs every operation against it:

| Cell | Declared type |
|---|---|
| `total_energy` | `EXTENSIVE` / `CONSERVED` / `ABSOLUTE` / `DEBIT_CREDIT` / `M·L²·T⁻²` / `floor=0` |
| `entropy` | `EXTENSIVE` / `MONOTONE` / `ABSOLUTE` / `floor=0` |
| `quantum_coherence` | `INTENSIVE` / `PRODUCIBLE` / `EQUILIBRATE` / `BOUNDED[0,1]` |
| `phase_angle` | `INTENSIVE` / `RELATIVE` / `EQUILIBRATE` |

Operations are split by whether they are closed (all participating cells are
inside the operation, so the total must be identical afterwards) or open (an
external source or sink is named, so drift is expected but needs a reservoir
cell to debit).

Result as of this commit — 4 of 10 operations satisfy their declared types:

```
operation                  kind                energy  axis crossed
bidirectional  ∇F(a↔b)     closed      200.0 -> 200.0  ok
directed       COBOL:MOVE  closed      200.0 -> 200.0  ok
spatial        ∇spatial    closed      200.0 -> 200.0  ok
entangle       ⊗(a,b)      closed      200.0 -> 200.0  ok
symbiosis      ∇∇(a⇄b)     closed      200.0 -> 210.0  CONSERVED: +10.0050
resonance      ~(a≈b)      closed      200.0 -> 240.0  CONSERVED: +40.0000
resonance ×16  ~(a≈b)      closed     200.0 -> 3697.7  CONSERVED: +3497.6852
                                                       BOUNDED[0,1]: coherence 1.6000
regenerate     ∮regenerate open        200.0 -> 231.9  DEBIT_CREDIT: no reservoir debited
decay          ∂decay      open        200.0 -> 195.0  DEBIT_CREDIT: no reservoir debited
phase          ∂phase      open        400.0 -> 380.0  DEBIT_CREDIT: no reservoir debited
```

Three findings worth stating plainly:

1. **`check_energy_conservation()` has exactly one call site** — inside
   `execute_bidirectional_interaction`. Every other operation is unchecked,
   which is why the four clean rows are clean and the rest were never tested.
2. **Resonance and symbiosis create energy in a closed pair.** Resonance
   multiplies both fields by `1 + 0.2·resonance_strength` with nothing
   debited; sixteen applications turn 200 units into 3697.
3. **Coherence is clamped in `regenerate` but not in `resonate_with`**, so
   repeated resonance carries it to 1.6. The existing `test_coherence_bounded`
   passes because it exercises entanglement, which does clamp.

The `Ledger` in `quantity.py` is the missing reservoir: cells can only be
raised by `transfer()`, so a credit without a matching debit is not something
the API can express. Conservation stops being a check that runs afterwards and
becomes a property of the type.

## Falsification results

`taxonomy_lab.py` tests the reduction claim three ways. Run:

```bash
python3 taxonomy_lab.py extract worksheet.json *.py   # recover topology
python3 taxonomy_lab.py e1 worksheet.json             # coverage
python3 taxonomy_lab.py e2 worksheet.json             # axis independence
python3 taxonomy_lab.py e3 residue_probe.py SPEC_A,SPEC_B
```

**E1 — coverage.** 534 bindings extracted from this repo's ten non-interpreter
modules. Heuristic pretyping reaches `transfer` 240/534 and `extensivity`
86/534, but `domain` 0/534 and `cost` 1/534. No binding came back `FAIL`,
so no missing axis is indicated yet — but that is a statement about how
little the guesser attempts, not evidence the seven axes are sufficient.
The coverage question stays open until a corpus is annotated by hand.

**E2 — orthogonality.** Not yet answerable, and not for want of data. The
pretyper assigns axes in bundles: one rule sets `extensivity`, `conservation`
and `domain` together, another sets `extensivity`, `conservation` and `datum`
together. Any two axes written by the same rule are perfectly correlated by
construction, so E2 measures the guesser rather than the taxonomy — at n=534
exactly as much as at n=155. Hand annotation is a precondition for this
experiment, not an improvement to it.

The harness originally reported six significant couplings here. That was an
artifact: when an axis has no variation among the co-judged rows its entropy
is zero, `U` is undefined, and the resulting `nan` fails every `>=` comparison
in the null loop, driving the count to zero and pinning *p* at `1/(trials+1)`.
Degenerate pairs now report "cannot test" instead of a p-value.

**E3 — residue inertness.** Falsified as stated, and the failure is precise.
`residue_probe.py` holds two `"Component/Failure Mode"` labels — pure residue
by the construct table — and uses them the two ways labels get used. Permuting
which literal sits behind which name:

```
SAME     identity_only  distinct=2 same=False
CHANGED  used_as_a_key  SPEC_A resolves to 0.9
         -> used_as_a_key  SPEC_A resolves to 0.6
```

Residue is inert under identity and equality, and load-bearing the moment
anything dereferences it. "May be carried across languages verbatim" holds
only for the first use.

What this locates is not a missing eighth axis. Both lines hold the *same*
label with the same quantity type; only the topology differs — whether an edge
dereferences it. So residue inertness is decided by `BINDING_TOPOLOGY`, not by
`QUANTITY_TYPE`, which means the three-way split is not independent: the third
term's status is a function of the first. A label used as a key is a real
edge in the topology and should be recovered as one, rather than tagged inert
and set aside.

## Bias probe

`adversarial_corpus.py` scores a reducer against a 17-case answer key built in
both directions, so the two error types can be reported separately. Its
`UNDECIDABLE` cases are the calibration test: there, abstaining is the correct
answer and any confident verdict is a hallucination.

```bash
python3 adversarial_corpus.py
```

| Reducer | correct | FORCED_FIT | MISSED_GROUNDING | OVERCONFIDENT |
|---|---|---|---|---|
| credulous (grounds all) | 7/17 | 7 | 0 | 3 |
| null (refuses all) | 7/17 | 0 | 7 | 3 |
| `taxonomy_lab.pretype` | 7/17 | 3 | 0 | 0 |

The controls mirror each other exactly, which is the corpus working. The real
reducer scores the same 7/17 by a different route, and both of its flattering
numbers fail inspection:

**It does not discriminate.** The corpus's central pair — `I3` a UUID (inert)
and `R1` a geohash (grounded) — is two identical-looking strings with opposite
answers. `pretype` returns byte-identical inference for both:

```
I3 (user_uuid, key=INERT)     ->  {'dimension': 'NONE', 'transfer': 'COPY'}
R1 (cell,      key=GROUNDED)  ->  {'dimension': 'NONE', 'transfer': 'COPY'}
```

One rule fires on "a string literal was assigned", so the pair is scored 50%
by construction. Getting `R1` right is not a success; it is the same guess
that got `I3` wrong.

**Its calibration is an accident.** `OVERCONFIDENT 0` looks like the one place
`pretype` beats both controls, but the three abstentions come from the
`n_writes == 1 and n_reads > 1` threshold, not from recognising insufficiency.
Appending a single extra read to `U2` — which changes nothing about whether
the case is decidable — flips it from abstain to grounded:

```
U2 as written                     -> None   (abstains)
U2 with one extra read of `rate`  -> True   {'transfer': 'COPY'}
```

So the clean calibration column is not a property of the reducer.

`pretype` was **not** tuned against this corpus, and should not be. Seventeen
hand-built Python cases are enough to detect gross bias and far too few to fit
against; a reducer trained to pass them would score well and mean less. The
corpus is a check on the reducer, not a target for it.

**`F4` is the first concrete missing-axis candidate.** A compass heading is
cyclic: `350 + 20` is `10`, not `370`, and `>` is unsound on a circle. No axis
value expresses this. `BOUNDED[a,b]` is the near miss, but bounded means
clamped, and a clamp is exactly the wrong behaviour — wraparound is not
saturation. This is the `FAIL` outcome E1 was built to surface and did not
find, because the heuristics never attempt `domain`. Axis 3 appears to need a
`CYCLIC[a,b)` value distinct from `BOUNDED`.

**Where the corpus corrects my earlier reading.** After E3 I concluded that
residue inertness is decided by `BINDING_TOPOLOGY` — whether an edge
dereferences the label. The `I3`/`R1` pair shows that is not sufficient: both
labels are dereferenced, and they still differ. What separates them is whether
the *internal structure* of the value is consulted — `I3` uses whole-value
identity, `R1` reads a prefix. So the distinction is not "is it dereferenced"
but "is it dereferenced as an atom or as a composite", which splits the
construct table's `int (id) -> ALL residue` row into `OPAQUE_LABEL` and
`ENCODED_POSITION`.

## Open

- [ ] Hand-annotate a corpus so E2 can run at all. Until then axis
      independence is untested, not confirmed. The worksheet from
      `taxonomy_lab.py extract` is the input; set each axis or mark `FAIL`.
- [ ] Split the construct table's `int (id) -> ALL residue` row into
      `OPAQUE_LABEL` (whole-value identity only, inert) and `ENCODED_POSITION`
      (internal structure consulted, grounded). The `I3`/`R1` pair is the
      fixture; E3's topology-only reading was not sufficient to separate them.
- [ ] Add `CYCLIC[a,b)` to Axis 3, distinct from `BOUNDED`. Wraparound is not
      saturation, and `F4` currently has no correct typing.
- [ ] Give the reducer a way to *say* "inert". `pretype` has no residue
      verdict in its vocabulary, so it cannot score anything but abstain or
      ground — which is why `MISSED_GROUNDING` is structurally 0 for it and
      that column carries no information.
- [ ] Intensive-quantity algebra: full rule set for legal combinations.
      `weighted_mean` covers the common case; products of intensives
      (pressure × volume) are not yet typed.
- [ ] Does `BINDING_TOPOLOGY` need a time axis of its own, or is lifetime enough?
- [ ] Where PIC-clause precision sits: Axis 3 ceiling, or its own axis.
      `PIC 9(3)` is a clean ceiling; `V99` is a quantisation, which is
      arguably a different property.
- [ ] Cost floor for `TRANSFORM` — needs the entropy of the map, not yet
      specified. `erase_cost()` implements only the Landauer floor.
- [ ] Rebuilding `EnergyState` on the `Ledger` so the six failing operations
      become unwritable rather than merely reported. This changes interpreter
      behaviour — resonance amplification is currently a documented feature —
      so it is a design decision, not a bug fix.
