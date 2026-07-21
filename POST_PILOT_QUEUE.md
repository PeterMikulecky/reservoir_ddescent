# Post-Pilot Review Queue

Everything that accumulated while the step-3 pilot ran, whose resolution is informed by the pilot
results. Walk this list once the pilot finishes and the D101 diagnostic panel is in hand. Grouped by
theme; each item notes what pilot readout informs it and the candidate action(s).

---

## A. THE DENSITY AXIS — is our sweep even in the right neighborhood? (highest priority)

**A1. Where is the interpolation threshold on the density axis?**
- The open question PJM raised: we assumed [0.2..0.8] brackets the interesting regime, but the
  threshold could be *below* 0.2 (e.g. ~0.03), meaning the whole sweep sits in the overparameterized
  tail and misses the rise/peak/descent entirely. A flat result would then be AMBIGUOUS ("no double
  descent" vs "we sampled the wrong part of the x-axis").
- **Pilot readout that informs it:** `best_train` (training error) vs density across the 4 cells.
  Train error ~0 at 0.2 -> already past interpolation -> sweep must go SPARSER. Train error high at
  0.8 -> underparameterized throughout -> denser. Crosses zero within [0.2,0.8] -> threshold found.
- **Candidate build:** add an interpolation-threshold-locator readout (#7) to the diagnostics panel
  (train-error-vs-density crossing). PJM flagged this as arguably MORE important than the capability
  trajectories for full-run design.
- **Candidate decision:** full-run density range — likely WIDER and LOG-SPACED, including very sparse
  values (e.g. [0.02, 0.05, 0.1, 0.2, 0.4, 0.7]) to BRACKET the threshold, with denser sampling near
  it (where the peak lives). Biological grounding: cortical local connectivity ~0.1-0.2, so the
  interesting regime may be sparse.

**A2. Is density even the right parameterization of "P"?**
- Double-descent x-axis is parameters relative to task/data complexity. We use nominal density.
  Effective-P (post-development active synapses, D087) may differ from nominal. Revisit whether to
  bin/plot by nominal density or effective-P.

---

## B. SELECTION PRESSURE — is it strong enough to climb?

**B1. fitness_beta may be too low for the tiny fitness values we're seeing.**
- Fitnesses are ~0.03-0.04 with genome-to-genome differences ~0.001-0.01. With replicator softmax at
  beta=1.0, exp(1.0*0.04) vs exp(1.0*0.03) is nearly identical -> selection is nearly a RANDOM WALK
  (weak pressure). The low-density cell DRIFTED (fit 0.0412->0.0393, slightly DOWN) rather than climbed
  — consistent with near-zero effective selection pressure.
- **Pilot readout that informs it:** does fitness climb in ANY cell? If no cell climbs and fit_std
  stays healthy (diversity present but not being selected on), suspect weak selection, not absent
  capability.
- **Candidate action:** raise `fitness_beta` so the softmax discriminates among small fitness
  differences. Interacts with the small-absolute-fitness situation. (Keep replicator, per D060 — it's
  chosen so the Occam factor lives; don't switch to tournament, which deletes it.)
- **Related:** could also normalize/standardize fitness within a generation before the softmax, so
  pressure is scale-invariant to the tiny absolute values. Design choice to weigh.

---

## C. N, POP, GENS, DEV_MS — the budget knobs (D101 panel drives these)

**C1. gens** — D101 readout #1 (fitness slope over last K gens). Still climbing -> increase gens.
Corrected cost: at ~6.35s/eval, +10 gens ~= +50 min on the full run.

**C2. pop** — D101 readout #2 (fit_std collapse). Premature convergence -> increase pop/mutation.

**C3. N** — D101 readout #3 (component emergence). If car/reg NEVER emerge at ANY density, suspect
N=50 too small for evolution to build working memory. EXPENSIVE fix: N=75 might push eval to ~10-12s
(superlinear), full run to 14+ hrs. Consider only if #3 says so AND #4 (dev convergence) is fine.
Could become a scientific axis (does capability emergence depend on N?) rather than a nuisance knob.

**C4. dev_ms** — D101 readout #4 (dev convergence fraction). DECIDED FIXED/uniform (D101, no early
abort). If convergence fraction is low -> raise the fixed dev_ms (scoring immature phenotypes
undermines D083). Especially check at LOW density (fewest I->E synapses — may converge trivially or
fail to develop, a confound for the flat low-density result).

---

## D. COST & FEASIBILITY (correct the record)

**D1. Cost projection was ~60% low.** Measured 6.35s/eval at pilot settings (dev_ms=800), not the 4.0s
projected (that was dev_ms=500, warm cache, no pool startup). Corrected: pilot ~1.75 hr (not 1);
full run (pop50 x 100gen x 6P / 6 cores) ~8.8 hr (not 5.6). Per-eval cost is CONSTANT (~6.35±0.5s),
not erratic -> no recompilation bug, just an underestimate.
- **Action:** update the cost figures in the record (D068/D099 projections) to the measured numbers.
- **Consequence:** full run ~8.8 hr overnight -> D100 checkpointing/logging is now MANDATORY, not
  optional. And N-increase (C3) or gens-increase (C1) could push past a day -> may need Azure VM to
  parallelize (P,seed) cells across more cores.

---

## E. RUN-HARNESS ROBUSTNESS (the D100 retrofit — mostly decided, needs building)

**E1. Per-cell checkpointing** — write each cell's history to disk AS IT COMPLETES (not all-at-once at
the end). Current run_pilot.py accumulates in memory -> a crash loses everything. REQUIRED before the
~8.8hr full run. (D100)

**E2. Logging to disk** — stdout/stderr + warnings to run.logs()/<name>.log, PLUS per-worker log files
(worker-side NaN/Brian2 warnings don't reach the parent). (D100)

**E3. Per-generation heartbeat** — turn on per-gen progress (or a lighter heartbeat) streamed to
stdout+log, so a long run is continuously observable (no 25-min silent gaps). (D100/PJM)

**E4. Source-freeze during a run (workflow rule, proposed).** Once a run launches, don't edit the
source files it imports — spawn workers re-import from disk per cell, so mid-run edits can mix versions
across cells. (We got away with it this pilot because the edits were diagnostic-only.) Candidate: add
to D100 as a workflow corollary, OR have the harness snapshot/import-lock its code at launch.

---

## F. INTERPRETATION DISCIPLINE (carry forward, not new builds)

**F1. Single cells are uninformative in isolation** — the P-CONTRAST is the signal (D101 #5). Low-
density flat is plausibly expected underfit, OR the null; only the cross-density pattern distinguishes.
Don't over-read any one cell (the standing D085c/D097 discipline).

**F2. Components vs fitness** — regulation enters fitness only via carrying*regulation (D094), so a
nonzero raw regulation with zero carrying contributes nothing. Read the FITNESS climb, not raw
component values, for "is selection working."

**F3. Distinguish "apparatus broken" from "hypothesis null"** — if ALL cells flat: check in order
(a) dev convergence #4 (immature phenotypes?), (b) selection pressure B1 (too weak?), (c) density
range A1 (wrong part of x-axis?), (d) N C3 (too small?) BEFORE concluding the effect is absent.

**F4. SUBSTRATE hypothesis — homogeneous inhibition may cap the WHOLE capability stack (not a build
decision yet; a watch-item).** The current model gives every neuron GLOBAL, identical time constants
(tau_slow, fast constants, nmda_frac) — ZERO inhibitory decay-constant diversity. Biological
inhibition is strongly diverse in timescale (PV fast, SST slower, VIP), scoped as the D084 interneuron-
hierarchy gene (h in [0,1]) but DEFERRED (hard-ordered after the core build). Candidate explanation for
flat results — but BROADER than first framed:
- Not just "carrying/regulation need slow inhibition." PJM: even ENCODING may be inhibition-timescale-
  limited. Auditory TONOTOPIC MAPS (pure encoding — faithful frequency representation) are severely
  disrupted by targeted PV-interneuron ablation: fast, temporally-precise PV inhibition SHARPENS tuning
  (gain control, WTA-like selectivity sharpening, temporal precision that keeps the map from smearing).
- ⇒ Reframe: computation ACROSS THE BOARD exploits inhibitory temporal DIVERSITY, different computations
  recruiting different timescales (fast/PV for sharp encoding + gain control; slow/SST for sustained
  gating/maintenance = carrying/regulation). The DIVERSITY itself is the resource; a homogeneous
  inhibitory population can serve one regime well but not several at once.
- ⇒ Consequence for interpretation: homogeneous inhibition could quietly cap ALL components, including
  the modest encoding (~0.02-0.03) we've treated as the working baseline — that encoding may itself be
  DEGRADED vs what temporally-diverse inhibition would allow. So the whole fitness ceiling (not just the
  second-descent terms) may be depressed by the substrate. Add this as a branch of F3: before concluding
  null / N-too-small / selection-too-weak, consider the inhibitory substrate is temporally impoverished.
- **NOT a build decision yet** (PJM): premature to decide how/when. D084 ordering (core apparatus
  working + interpretable first) still holds. When built, do it the PRINCIPLED way (D038/D074): make
  inhibitory time constants an EVOLVABLE per-neuron/per-type degree of freedom (the D084 h-gene), so
  selection DISCOVERS the diversity — do NOT hand-install biological PV/SST tau values (that would build
  in the mechanism under test). For now: a watch-item that likely becomes a real issue.
- **DEMOTED below B1 (selection-pressure) — the ceiling is an EXISTENCE PROOF (PJM).** Both engineered
  ceilings (carry attractor + integrated carry-and-regulate) were built ENTIRELY from CURRENT-substrate
  primitives — homogeneous inhibition, global time constants, NO temporal diversity — and WORKED. So the
  current substrate is DEMONSTRABLY CAPABLE of carrying/regulating/encoding at a meaningful level with
  homogeneous inhibition. ⇒ substrate incapacity CANNOT be the reason evolved nets are flat; if the
  substrate can express it but evolution isn't finding it, the problem is in the SEARCH (selection,
  density range, N, development landscape), NOT the substrate. F4 is therefore NOT the blocking issue —
  demoted below the search-side fixes. (Caveat: the ceiling proves REPRESENTABILITY, not REACHABILITY by
  this GA's dynamics — but that too is a search problem, reinforcing the same conclusion. F4 may still
  HELP later by raising the ceiling or smoothing the landscape; it's just not the first thing to reach
  for.) ⇒ **Tune beta (B1) BEFORE layering in inhibitory temporal diversity.**

---

## SUGGESTED WALK ORDER (once pilot + panel are in hand)
1. **A1 first** — is the density range even right? (best_train vs density). Everything else is moot if
   we sampled the wrong part of the x-axis.
2. **F3 triage** — if flat everywhere, walk the checklist. NOTE (PJM): the engineered ceiling is an
   EXISTENCE PROOF that the current substrate CAN carry/regulate/encode -> substrate incapacity (F4) is
   NOT the blocker -> focus SEARCH-side fixes. Order: (a) selection pressure B1, (b) density range A1,
   (c) dev convergence C4, (d) N C3. Inhibitory diversity F4 is demoted (later enhancement, not blocker).
3. **B1 — selection pressure (tune beta) — likely the FIRST real fix.** The three-cell signature (tiny
   fitnesses ~0.04-0.06, changes within noise ~0.01, cells drifting in DIFFERENT directions, peak at 0.4
   plausibly a lucky random walk) is the textbook look of near-zero effective selection pressure.
   Cheapest fix (one parameter), and the ceiling argument says the substrate isn't to blame. Do this
   BEFORE layering in inhibitory temporal diversity.
4. **C1-C4** — budget knobs from the D101 panel.
5. **D1** — lock corrected cost, decide full-run size / Azure.
6. **E1-E4** — build the D100 retrofit before launching the full run.
7. **F4** — inhibitory temporal diversity: only after search-side fixes are exhausted and IF capability
   still fails to emerge (or as a deliberate enhancement to raise the ceiling), built the evolvable way.

---

## G. MAJOR PIVOT (post-pilot probes, 2026-07-21): the root is ENCODING/REPRESENTATION, not density/readout/selection

Two diagnostic probes (sparse_sweep.py, check_readout.py; logged in analysis_logs/) reframed the problem:

**G1. Density is NOT the lever (both our hypotheses wrong).** Sparse sweep [0.02..0.4], 20x range:
train error FLAT at the floor (~0.99) at EVERY density. Mean firing rate identical (~1.17), input-
drivenness R2 if anything slightly LOWER when sparse. => NOT underparameterized (mine: mispredicts,
train err doesn't fall with density) AND NOT quenching (PJM: sparse didn't escape any saturated regime;
dynamics uniform across density). Density is settled: learning is INSENSITIVE to it. Stop debating range.

**G2. Readout is NOT the bottleneck.** For a random developed net on the task: affine readout (D095) =
0.973, FULL uncapped ridge on whole state = 1.007, per-context ORACLE (context given free, full ridge) =
1.029 -- ALL at floor. Even with maximal readout power AND context handed over, the state can't beat the
floor. => the signal isn't being lost by a weak readout; it's NOT THERE to extract.

**G3. THE ROOT: the network state does not carry task-usable information.** Encoding isn't happening --
the stimulus->response structure the task demands isn't present in the activity. Carrying/regulation/
selection are all DOWNSTREAM of an encoding that never forms. This is upstream of density, dev_ms,
selection, beta -- all the levers we'd queued.

**G4. UNRESOLVED - two clean tests needed (do NOT flurry; one each):**
  (a) Does the ENGINEERED CEILING beat the floor on the task through these readouts? Existence proof:
      if yes -> substrate CAN represent it, evolution fails to FIND it (search problem after all).
      if even the ceiling can't -> task-as-posed isn't representable through this input/readout path
      (substrate/task-config problem). [The check_readout.py script botched this -- ran a random net,
      not the ceiling. Rerun with the ceiling.]
  (b) Reconcile the DEV-CONVERGENCE CONTRADICTION: pilot panel said "dev_ms too short / not converged"
      in all cells; sparse sweep says dev_conv=1.00 everywhere (fresh random genomes). Until reconciled,
      the dev-convergence flag is NOT trustworthy and the "development is the root" claim is WITHDRAWN.
      Candidate: evolved/mutated genomes vs fresh random genomes converge differently? or the flag
      measures different things in the two contexts?

**G5. Candidate roots for G3 (encoding failure), once G4a discriminates:**
  - N=50 too small to REPRESENT the task (substrate-capacity limit -- now for ENCODING itself, echoing
    F4/PJM: even encoding may be substrate-limited).
  - Input not richly expanded (reservoir kernel too weak -- dynamics collapse, not enough nonlinear
    mixing of the 10-d input into a usable high-d state).
  - Task hard even in principle (oracle ceiling only 0.575; large gap from random ~1.0).
  - Selection STILL a factor (G2 shows even free context doesn't help a RANDOM net, but evolution might
    build representation over generations IF selection had a gradient -- which needs the encoding to
    start forming first. Circular; G4a breaks the circle).

**REVISED WALK:** G4a (ceiling existence proof) FIRST -- it discriminates substrate-can't from evolution-
can't, the fork everything else hangs on. Then G4b (reconcile dev flag). Then, per G4a's answer: if
substrate-can't -> G5 (N / input-expansion / task difficulty); if evolution-can't -> back to selection
pressure (B1) with the encoding-gradient question. beta optimization (B1) remains important but is
downstream of establishing that a representable signal EXISTS to select on.

---

## H. ROOT CAUSE IDENTIFIED (2026-07-21, D103): development is missing its LEARNING + COMPETITION halves

The G-series localized the flat pilot to "state carries no task-usable info" (encoding not forming).
PJM's development model + a literature search (D103) identified WHY: development has only its STABILIZER
(Vogels iSTDP) and lacks the two mechanisms that build stimulus-selective representation. This is the
root; it MOOTS or REORDERS much of A-G.

**H1. THE FIX (primary): add the missing development mechanisms (D103, = D087 step-2, now THE missing
half not an enhancement).** Development = a TRINITY: eSTDP (learning engine, builds selective
representation) + competition via lateral inhibition (selectivity/differentiation) + iSTDP/Vogels
(stabilizer — what we have). Adopt TESTED rule combos (temporal-paradox blowup risk; Oja lesson D086):
Srinivasa & Cho 2014 (closest architecture), Diehl & Cook 2015 (eSTDP+WTA), Brian2 canonical STDP.

**H2. Build/validate sequence (next session):**
  (a) Add eSTDP (E->E, maybe E->I) as a general Hebbian rule (D038/D074: let selectivity emerge, don't
      hand-wire). Pair with the existing Vogels iSTDP for stability (they're a PAIR — iSTDP stabilizes
      eSTDP; we had the stabilizer alone).
  (b) Test whether COMPETITION emerges through EXISTING inhibitory structure once excitatory synapses
      learn, BEFORE building a separate hand-built WTA. Add explicit lateral-competition only if needed.
  (c) Handle the timescale separation (Hebbian fast vs homeostatic slow) via the tested combo, not a
      hand-rolled interaction.
  (d) VALIDATE before wiring into the GA: does a developed network's state now BEAT THE FLOOR (does
      representation actually form)? This is the direct test of G3/H1 — the thing that was failing.
      Validate against a control (random/undeveloped, and/or the ceiling-style known-positive).
  (e) Only THEN re-run the pilot with real development, and only then does beta/B1 become meaningful
      (a fitness gradient must EXIST before selection strength matters).

**H3. How H reorders A-G:**
  - **G4a (ceiling existence proof)** — LOWER priority now. We already know (ceiling controls) the
    substrate CAN express fitness; the diagnosis is that DEVELOPMENT can't draw it out. G4a would confirm
    "evolution/development can't find it," which D103 now explains mechanistically. Still a nice
    confirmation but no longer the fork everything hangs on.
  - **G4b (dev-convergence contradiction)** — may RESOLVE once eSTDP is added: the pilot's "not
    converged" vs sweep's "converged" both measured only the INHIBITORY weights; with eSTDP the relevant
    convergence is different. Revisit after H1.
  - **B1 (beta/selection pressure)** — still real, but DOWNSTREAM of H1. No gradient to select on until
    development expresses latent potential. Do H1 first, then B1.
  - **A (density), C3 (N), readout (G2)** — all deprioritized: none is the blocker (ceiling proves
    substrate; sweep proves density-insensitive; G2 proves readout isn't the cap). Revisit only as
    fine-tuning AFTER development works.
  - **F4 (inhibitory temporal diversity / D084)** — still a later enhancement; note it OVERLAPS H1's
    competition mechanism (PV-homeostasis vs SOM-competition is literally the F4 interneuron-type
    distinction). May fold together eventually, but H1 first with the SIMPLEST version (don't front-load
    the D084 gene).

**REVISED TOP OF WALK:** H1/H2 (add eSTDP + test competition + validate representation forms) is now the
single highest-priority action — the identified root cause. Everything else waits behind "does
development now produce a network whose state beats the floor."
