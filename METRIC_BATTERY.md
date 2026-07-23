# METRIC BATTERY — measurement specification (post-2026-07-22 turn)

**Purpose.** Specifies what we measure and store, in light of the H-C→H-Cv2 turn (see HYPOTHESIS_LOG)
and the move to a nonlinear-regulation readout as the selection basis. Built on one architectural
principle (PJM):

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

### 1b. Dynamical / activity (phenotype side; developed network under the assay)
- **Full developed state matrix** (states × neurons) under test stimuli — cohort: full; population: summary.
- **Per-context activity** (states conditioned on context) — REQUIRED for any regulation/separability
  metric; cohort: full per-context; population: per-context centroids + covariances.
- **Spike rasters (cohort)** or high-fidelity temporal summary — enables temporal/dynamical descriptors
  and direct raster observation; population: rate-level.
- **Regime indicators** — CV(ISI), synchrony measures, mean rate — where the instance sits on the
  tonic↔fluctuation-driven axis (serves H-D and the reframe's fluctuation-driven-native claim).

### 1c. Performance (fitness side)
- **Nonlinear-regulation readout score** — the new selection basis (H-Cv2).
- **Linear readout score** — kept as CONTRAST, not target. The linear-vs-nonlinear GAP is itself a core
  metric (indexes how distributed/nonlinear the representation is).
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
- the nonlinear-regulation readout (selection basis) and the linear readout (contrast) + their gap
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

- **H-A (peak exists):** error-vs-P on the NONLINEAR readout (the clean curve the linear readout hid).
  Requires P swept (density-evolvable or explicit density arms — note the D108 frozen-density problem).
- **H-B (peak tracks r₁ not data count):** r₁-vs-n_env contrast on the nonlinear error axis (r₁/n_env
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
