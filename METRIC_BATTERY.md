# METRIC BATTERY — measurement specification (post-2026-07-22 turn)

**Purpose.** Specifies what we measure and store, in light of the H-C→H-Cv2 turn (see HYPOTHESIS_LOG)
and the move to **regulation-only selection read with the EXISTING LINEAR readout** (see §0). Built on one
architectural principle (PJM):

> **Separate MEASUREMENT from METRIC.** Capture a comprehensive, raw, theory-neutral CORE MEASUREMENT SET
> now. DERIVE metrics / spaces / distance functions later, empirically, FROM the stored core
> measurements — and only once a GA run shows a meaningful performance gain worth characterizing.

Consequences: (a) any candidate metric is a function of stored core measurements, so we can explore
metric-spaces retrospectively WITHOUT re-running GAs; (b) we discover which structural/dynamical
dimensions index "refinement" by looking at runs with CONFIRMED signal, not by guessing ahead of time
(the anti-"measured-the-wrong-signature" discipline, applied to the whole analysis); (c) the raw layer is
theory-neutral, so derived metrics can be honestly labeled EXPLORATORY (found by looking) vs CONFIRMATORY
(pre-registered H-Cv2 signatures) — protecting pre-registration integrity.

**The one thing that must be right NOW is the CORE MEASUREMENT SET** — you cannot retrospectively derive a
metric from data you didn't capture. So the core set errs toward OVER-capture within "rapidly measurable +
storable."

---

## 0a. ⚠️ DATA-SPLIT DISCIPLINE — three-way split REQUIRED (D113)

**Non-negotiable, and it precedes every other measurement decision.** Since D094, fitness components were
computed from TEST error, so selection optimised the exact quantity reported as generalisation (D113).
That is test-set leakage through model selection (~1200 selective evaluations against `E_test` per run) and
it invalidates any formal use of D094-onward absolute test numbers.

**Required split, for all runs from here:**
| split | used by | never used by |
|---|---|---|
| `E_train` | DEVELOPMENT (the network's within-lifetime plasticity) | reporting |
| `E_val` (NEW) | SELECTION — all fitness components computed here | reporting |
| `E_test` | REPORTING ONLY — the double-descent y-axis | development, selection, any tuning |

**Rules.**
- No quantity computed from `E_test` may enter the selection signal, directly or via a component.
- Audit `task.headroom()` (`memoryless_floor`, `oracle_ceiling`): `floor` enters the fitness expression, so
  if it is derived from test data that is a smaller leak of the same family.
- Add a MECHANICAL GUARD (assertion / unit test) that `_fitness()`'s inputs trace only to train/validation
  data, so this regression cannot recur silently. Names are not measurements; trace every fitness input to
  its data source.
- Exploratory CONTRASTS from the leaked era remain readable (all modes leak identically, so between-
  condition comparisons are not differentially biased) — but no absolute number from that era is
  publication-grade.

---

## 0. THE SELECTION READOUT — decided by the P-AXIS criterion (supersedes the earlier nonlinear-readout premise)

**The governing constraint (PJM).** The project's earliest incarnation took a reservoir-computing approach
and ABANDONED it, because **RC sidesteps the core question of the study.** In RC you train a linear decoder
on a rich but tangled reservoir; better RCs get better *because the decoder improved*, NOT because of
structure imparted to the reservoir. So fitness-vs-P becomes **meaningless**: you plot fitness against the
NETWORK's parameter count while the parameters actually doing the generalization work — the ones a
double-descent curve is ABOUT — live in the DECODER.

**Therefore the criterion is not "keep the readout weak so the network still matters" (a fitness-sensitivity
worry) but: READOUT PARAMETERS ARE UNCOUNTED P.** Every fitted degree of freedom in the readout is P we are
not counting, contaminating the exact axis H-A and H-B live on. This is a MEASUREMENT-VALIDITY constraint on
the study's central claim, not a nuisance.

**Consequences (what this disqualifies):** random-forest / MLP / any flexible learned readout as a SELECTION
basis (enormous uncounted capacity). Also disqualifies "mixtures of decoders" — more decoders = more
uncounted parameters, strictly worse.

**The empirical point that decides it (PJM).** The LINEAR regulation readout we have been using **already
detects regulation capability** — it found regulation heritable (r≈0.29, D109) and meaningfully varying, at a
time when encoding showed nothing. So regulation IS linearly detectable. The D110 nonlinear result shows the
*context* information is present-but-distributed (correcting our INTERPRETATION — "encoding at floor" was a
decoder artifact, the substrate isn't failing); it does NOT follow that the SELECTION readout must go
nonlinear. Two distinct roles, different constraints:
- **Nonlinear decoding as a DIAGNOSTIC** (D110-style): valuable, costs nothing on the P axis (it is a
  measurement, never a selection basis). KEEP, permanently confined to this role.
- **Nonlinear readout as the SELECTION basis:** costs uncounted P, risks the abandoned RC failure mode, and
  appears UNNECESSARY since the linear regulation readout already works. REJECTED unless it earns its way in.

**DECIDED — the change is what we SELECT ON, not how we read it:**
1. **Select on REGULATION ONLY, with the EXISTING LINEAR readout.** (Not the encoding+memory+regulation
   hybrid.) Minimal change, ZERO added uncounted P, directly motivated by D109: regulation is the heritable,
   substrate-native component; encoding is the ordered target the substrate structurally resists; the hybrid
   has been diluting a transmissible signal with a non-transmissible one.
2. **Only if (1) stalls:** test a **fixed-form, ZERO-FITTED-PARAMETER** nonlinearity (e.g. a specified
   quadratic feature map applied identically to every genome). A fixed feature expansion adds no fitted DOF —
   it re-presents the same state — so it is the ONLY form of nonlinearity compatible with the P-axis
   criterion. Gated on necessity AND on the readout-power audit below.
3. **Powerful nonlinear decoders remain DIAGNOSTIC ONLY**, permanently outside the P accounting.

**READOUT-POWER AUDIT (standing control, promoted to a core measurement).** Score RANDOM / SCRAMBLED networks
with the same readout. If a random network scores nearly as well as an evolved one, the readout is doing the
network's job. The gap (evolved − random) is the headroom the NETWORK is actually contributing. This converts
"is the readout too powerful?" from a design worry into a measured quantity, and it is the direct empirical
guard against the abandoned RC failure mode. Run it whenever readout form changes.

**Open hypothesis worth testing:** readout power and heritability may be COUPLED — a too-powerful reader can
compensate for whatever the network does, so mutating the network barely changes achievable performance and
fitness fails to transmit. If so, weakening/narrowing the readout (as in (1)) might itself RESTORE
heritability. Testable, and it would link two open problems (D109 non-heritability ↔ readout capacity).

---

## 1. CORE MEASUREMENT SET (captured on every measured instance; comprehensively on the top-k cohort)

**Storage tiering (PJM decision):**
- **Top-k cohort each generation → FULL raw capture** (comprehensive; this is what trajectory/refinement
  analysis consumes).
- **Rest of the population → rich SUMMARY** (covariance / top PCs / per-context centroids; cheap).
- Err GREEDY on the raw layer for the cohort — under-capture is the one failure this architecture cannot
  recover from without re-running.

### 1a. Genome / structural (parameter side)
- **Full weight matrix W** (the genome; everything structural derives from it).
- **E/I identity vector** (Dale's-law assignments per neuron).
- Cheap derived, stored for convenience: density; per-type connection counts (E→E, E→I, I→E, I→I);
  excitatory fraction; full weight distribution (small — store it, don't just summarize).
- **DYNAMICAL INVARIANTS (D117; the N5 requirement, now with a target value).** Stringer et al. 2026 show
  that CRITICAL NORMALIZATION (largest eigenvalue ≈ 1) is what produces long timescales from fast units,
  and that incomplete normalization DESTROYS long-timescale macroscopic structure. Ours measured at
  ρ(W) ≈ 5.1 — about 5× supercritical, never previously measured or controlled. Now core:
  · **spectral radius ρ(W)** — raw, and an EFFECTIVE/linearized ρ at the operating point (the raw value
    overstates gain in a spiking net with threshold/refractoriness/saturation, so both are needed).
  · **E→E reciprocity** — fraction of excitatory connections that are reciprocal, vs the chance rate given
    density; plus the weight correlation on reciprocal pairs. (Ours: 0.29 = chance, i.e. independent
    draws. Theirs: fully reciprocal. NOTE this is Dale-COMPATIBLE — symmetry here means reciprocal
    EXCITATORY interactions, not sign-flipped synapses.)
  · **inhibitory fan-out** — how GLOBAL is our inhibition? (Ours: 0.30 ≈ density, i.e. sparse and
    specific. Theirs: global, entering as a uniform mean-subtraction.)
  These give "how dense is dense" an operational answer in dynamical terms (N4/N5) without putting a
  non-count quantity on the P axis.

### 1b. Dynamical / activity (phenotype side; developed network under the assay)
- **Full developed state matrix** (states × neurons) under test stimuli — cohort: full; population: summary.
- **Per-context activity** (states conditioned on context) — REQUIRED for any regulation/separability
  metric; cohort: full per-context; population: per-context centroids + covariances.
- **Spike rasters (cohort)** or high-fidelity temporal summary — enables temporal/dynamical descriptors
  and direct raster observation; population: rate-level.
- **Regime indicators** — CV(ISI), synchrony measures, mean rate — where the instance sits on the
  tonic↔fluctuation-driven axis (serves H-D and the reframe's fluctuation-driven-native claim).

### 1c. Performance (fitness side)
- **Regulation score, LINEAR readout — the SELECTION BASIS** (§0). Zero added uncounted P.
- **Hybrid fitness (encoding+memory+regulation)** — retained as CONTRAST (continuity with all prior runs;
  the hybrid-vs-regulation-only difference is itself informative).
- **Readout-power audit:** the same readout applied to RANDOM/SCRAMBLED networks (§0) — the evolved−random
  gap is the network's actual contribution. Core, not occasional.
- **Nonlinear-decodability (DIAGNOSTIC ONLY, never a selection basis)** and linear-decodability, stored
  separately; their GAP indexes how distributed/nonlinear the representation is (D110).
- **Component scores** (encoding / carrying / regulation) — continuity with prior runs + needed for the
  reversal test.
- **Nonlinear- AND linear-decodability of context** (the D110 decoder-ladder metrics), stored separately.

### 1d. Provenance / bookkeeping
- generation, genome-hash, seed, config-hash (reproducibility + locatability), cohort-membership flag.

---

## 2. FIRST-PASS SCALAR METRICS (always computed; these GATE the derived-metric work)

The same performance/fitness scalars we have always tracked, PLUS the nonlinear-regulation readout. Their
job is to answer ONE question: **is there a meaningful performance gain in this run worth characterizing?**
- fitness / performance trajectory (best + cohort-mean, per generation)
- the LINEAR regulation readout (selection basis, §0) and the hybrid fitness (contrast)
- the readout-power audit gap (evolved − random/scrambled) — is the network contributing?
- component scores (enc/car/reg) per generation
- population-distribution summaries of the above (mean, SD, tail) per generation

**Gate:** only when these show a real, sustained gain do we proceed to derive structural/dynamical metrics
(Section 3). No gain → the diagnostic question is "why not," not "characterize the refinement."

---

## 3. DERIVED-METRIC LAYER — EXPLICITLY DEFERRED (approach, not a committed set)

We do NOT pre-commit distance functions, trajectory-spaces, or structural descriptors. When a run shows
confirmed gain (Section 2 gate), we compute candidate metrics FROM the stored core measurements and
EMPIRICALLY identify which ones track the gain. Stated approach:

- **Structural descriptors (agnostic; PJM decision 1a):** we hypothesize refinement-associated structures
  are DETECTABLE without pre-specifying their type. Compute generic structural descriptors from W
  (modularity/community structure, assembly organization, subpopulation context-selectivity, effective
  connectivity) — agnostic about mechanism. We do NOT commit to specific gating motifs (held for later;
  committing now risks measuring for a mechanism the network doesn't use).
- **Dynamical/representational descriptors:** context-conditioned manifold separation, coding-subspace
  dimensionality/stability, linear-vs-nonlinear decodability profile — all derived from stored state
  matrices and per-context activity.
- **Cohort-trajectory framing (PJM):** rather than track individual LINEAGES (intractable prospectively —
  can't know which ancestors lead to the best; and uninformative — a single lineage is dominated by
  historical contingency + mutation stochasticity), characterize the TOP-k COHORT each generation and
  measure how the cohort's distribution MOVES through a chosen space generation-to-generation. The
  sequence of cohort distributions = a trajectory ascending the performance peak. Distance function(s)
  and space(s) (genetic / structural / dynamical) to be chosen EMPIRICALLY from the stored cohort
  measurements once there's real signal — because any such metric is computed from the core set, we can
  try many retrospectively without re-running.
- **Heritability, cheaply (PJM):** = whether a property's DISTRIBUTION in the offspring cohort tracks the
  parent cohort's, across generations. Falls out of the cohort-distribution measurements already taken —
  no parent-child pairing infrastructure needed (the D109 per-pair probe was the right ONE-OFF tool;
  cohort-distribution-across-generations is the efficient ONGOING form).
- **What the cohort-trajectory apparatus yields (once signal exists):** trajectory speed (fast→slow =
  ascending+converging), directionality (directed = selection climbing a gradient; diffusive = drift, the
  D108 signature), cohort convergence/tightening (refinement toward a structural attractor), and the
  COUPLINGS among genetic/structural/dynamical/performance movement (structural refinement tracking
  performance = refinement-of-structure made visible = direct H-Cv2 evidence).

**Pre-registration hygiene:** metrics discovered by looking at signal-bearing runs are EXPLORATORY; the
H-Cv2 discriminating predictions (Section 4) are CONFIRMATORY. Label each honestly when reported.

---

## 4. HYPOTHESIS KEYING — which measurements serve which hypothesis, with DISCRIMINATING predictions

A metric earns "core/confirmatory" status only if it can DISTINGUISH hypothesis versions.

- **H-A (peak exists):** error-vs-P on the REGULATION-ONLY (linear-readout) fitness — the axis is only
  meaningful if the readout adds no uncounted P (§0). Requires P swept (density-evolvable or explicit density
  arms — note the D108 frozen-density problem).
- **H-B (peak tracks r₁ not data count):** r₁-vs-n_env contrast on the regulation-only error axis (r₁/n_env
  independently manipulable — confirmed in code).
- **H-Cv2 (second descent = REFINEMENT of native regulation):** discriminating signatures vs H-C v1 —
  · nonlinear-decodability ABOVE chance even at LOW P / no selection (native), CLIMBING with P/selection
    (refinement).  [v1 predicts near-floor until high-P emergence.]
  · regulation more heritable/selectable than encoding or aggregate fitness.  [v1 predicts the opposite.]
  · cohort structural trajectory moves systematically (coupled to performance) as the cohort ascends.
    [v1 predicts a discontinuous appearance of structure, not gradual refinement.]
  · linear-vs-nonlinear decodability gap as a function of P (does refinement linearize, or sharpen-while-
    staying-distributed? — either is refinement; which one is itself a finding).
- **H-D (fluctuation-driven regime needed):** regime indicators (1b) vs performance; is the computation
  carried in the fluctuation-driven regime?

## 5. REFRAME-VALIDATION GATES (first-class; gate H-Cv2 promotion PROVISIONAL→SUPPORTED)
- **Reversal test:** does encoding-selection evolve WORSE (lower heritability, less climbing) than
  regulation-selection? (v2 predicts yes; v1 predicts no/opposite.) Computable once selection-on-component
  runs exist.
- **Regulation range-artifact control:** is regulation's higher heritability a depth fact, or an artifact
  of regulation varying LESS (smaller SD) than fitness (less range for mutation to disrupt)? Must be ruled
  out. Checkable from stored component-score distributions.

## 6. MEASUREMENT DISCIPLINE (hard-won this project)
- Measure the CONTRAST, not single instances (refined vs unrefined, high-P vs low-P, selected vs
  unselected, cohort-round-N vs round-N+1). Single instances/lineages are anecdotes.
- Measure FUNCTIONALLY, not by pre-formed scalar proxies (the weight-variance and linear-decodability
  mistakes — wrong signature, wrong format). Derived metrics come from raw core measurements + confirmed
  signal, not from guesses.
- Population-confirm before believing: a structural pattern seen in one cohort member is a hypothesis;
  the cohort-DISTRIBUTION is the evidence.
- Store enough to re-derive: the raw core set is the durable record; metrics are recomputable.
