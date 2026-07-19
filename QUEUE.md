# Queue

Updated 2026-07-19 (D082–D087). Claims → `DECISIONS.md` · framing → `FRAMING.md` ·
chain → `BRIDGE.md` · narrative → `LAB_NOTEBOOK.md` · citations → `REFERENCES.md`.

---

# ⛔ THE BLOCKING RESULT: Gate A FAILED — selection on BIRTH-fitness routes nothing (D082)

**The full 4,900-gen Gate A arm ran and is a pre-registered FAIL (D081 criterion).**
- **E|rates: 0.995 (gen 0) → 0.999 (gen 4899). Fell −0.003.** Champion output neurons carry no more
  information about E than at random init. `best_train` flat at ~0.92 throughout.
- **E|state ceiling 0.413** — the state holds E (encoder works); it never reaches the output slice.
- **Selection did not route E.** Not "hadn't converged" — 4,900 generations produced no gradient.

**THE DIAGNOSIS (D083): we are scoring UNDEVELOPED genotypes.** `evaluate()` instantiates exactly
the genome's weights, runs one forward pass, scores. **No within-life tuning.** But fitness — in
Frank's own population-genetics framing — is measured on the *developed* organism (genome →
development + experience → phenotype → fitness). A generation of kangaroos sharing a gene-connection
count are *developed adults* when scored. **We score them at birth.** If the capability to route/infer
only expresses after development, birth-fitness is flat **by construction** — every genome looks
equally unfit because the distinguishing behaviour never develops.

**⇒ THE FIX IS THE DEVELOPMENT REDESIGN (D083), NOW THE CRITICAL PATH.** Everything downstream of
Gate A — Gate B, the map, the coordinate sweeps — is blocked behind it, because all of it
presupposes selection can produce functional networks, which D082 shows it cannot on birth-fitness.

---

# THE CRITICAL PATH: build & test the development redesign (D083→D087)

**Settled:** fitness reduces the DEVELOPED distribution, not the birth one (D083). Development =
**Kind A** (strength-tuning within FIXED synaptic support; nominal-P invariant). Placement = **inside
every fitness eval** (forced by D082 — "develop only at readout" selects on the flat birth landscape).
**Design freedom is bounded ONLY by (a) support-invariance and (b) cross-P process-uniformity** — same
development instrument at every P (D087). Within that, use the biologically-standard rule.

**THE RULE (D086/D087 — empirically forced):** naive Oja was tried and **blew up** (one-step NaN
runaway on the recurrent substrate — Oja's feedforward normalizer is unstable here). **Lesson: do NOT
hand-roll plasticity numerics; adapt a tested implementation.** ⇒ **Vogels-Sprekeler 2011 inhibitory
plasticity** (canonical, homeostatic setpoint, official Brian2 reference + ModelDB 143751), run
**inside `net.run()`** (no Python-side weight write-back — that fragility caused half the Oja trouble).
Paired system: **inhibitory = stabilizer, excitatory = learner** (Oja failed trying to learn without
stabilizing; the literature says you need both).

**THE ORDERED BUILD (each step gates the next; one tested piece at a time — the Oja lesson):**

1. **Vogels inhibitory plasticity, validated in ISOLATION.** Plastic I→E synapses (presyn inhibitory,
   postsyn excitatory — a subset of W), tuned to a target rate; event-driven, in-simulation. Warm-up
   run eta=0, then development run eta>0. **Verdict = converges + Kind-A holds + network stays ALIVE**
   (the thing Oja failed). This is the convergence probe, redone with a rule that has a setpoint.
   - **Guards (assert in code, don't assume):** support-freeze `(developed.mag!=0)==(birth.mag!=0)`
     bit-for-bit (Kind A); **not-zero epsilon** on the weight clip (`clip(w, w_eps, gmax)`) so an
     existing synapse can weaken but never leave the support — but **NO magnitude floor** (development
     runs unconstrained; effective-P is measured at analysis, D087); **NaN tripwire** (abort loud on
     non-finite — never grind on garbage, the Oja lesson); network activity finite/non-collapsed.
   - **D086 forward-compat:** declare `alpha`/`tau_stdp`/`eta` as PER-NEURON state variables (Brian2
     idiom, ~free), so D084's interneuron gene later differentiates by subtype without a rewrite.
2. **Add the excitatory learner** (tested STDP/Hebbian Brian2 example) on E→E/E→I, stabilized by the
   now-working Vogels inhibition. Re-validate convergence + Kind-A with both active (the pairing is the
   point). This is the half that builds representation (encoding/memory); Vogels alone only balances.
3. **Integrate into `evaluate()`** — `EvoNet → develop → behave → score`; routing/test machinery
   (D077/D081) reads the developed net unchanged. **THE D082 REMATCH: does development route E where
   birth-fitness could not?** The load-bearing test. PASS (E|rates falls) → diagnosis right, proceed.
   FAIL (still flat) → not missing-development; it's the memory/substrate problem (D076) or N too small
   (Brunel: WM needs N>50). Either way informative.
4. **COST-MEASURE before any full sweep** (D068 — four runtime estimates were wrong). Development adds
   in-sim time per eval; the ~2 h/arm figure (D079) was WITHOUT it. **Probabilistic/subset development**
   for cost (D083 sub-decision 2) must use **distributional evaluation** — average draws, not a single
   noisy draw (overestimation bias, D085 c).

**P BOOKKEEPING IS ANALYSIS-TIME (D087):** record BOTH nominal-P (support count, the controlled input)
and effective-P (count of |w| above a magnitude threshold, the developed phenotype's functional count).
**Bin the aggregate by EITHER; learn from the difference** (PJM). Threshold-robustness is a REQUIRED
check (pattern must hold across cutoffs, else it's an artifact). Sample nominal-P widely/densely
(effective-P coverage is emergent, not designed). Log nominal→effective compression (possible finding).

*(Superseded: the Oja prototype scripts `run_dev_convergence_probe.py` / `_probe_silence_check.py` —
kept only as the record of the failure that forced Vogels. `DEVELOPMENT_BUILD_SPEC.md` was folded into
this section and removed.)*

**Open sub-decisions (D083, settle during the build):**
- **Distribution-reduction statistic:** collect the developed-fitness distribution; base hypotheses on
  mean AND variance (selection acts on tails the mean discards — D085 c), not the mean alone.
- **Duration:** scales with task structure (r₁, dwell), constant across P — OR, better, defined by
  CONVERGENCE now that Vogels has a setpoint that should converge (D083 3a).
- **Bookend controls (T-window calibration only):** random pool = long-end/non-convergence deadline;
  engineered pool = short-end. **HARD QUARANTINE** — engineered net contributes only a convergence-time
  scalar, never a template/seed/comparison (protects the D038 emergence claim).

---

## DEFERRED EXTENSION (scoped, NOT committed): the interneuron-hierarchy gene (D084)

**Ordered strictly AFTER D083** — because SST's slow rate-control overlaps functionally with
homeostatic plasticity, so development must be prototyped first to see how much of "SST's job" it
already does. **Do not build yet.**

The insight: PV/SST/VIP proportions trace a 1-D trajectory sensory→association. **ONE bounded scalar
gene** (hierarchy position h ∈ [0,1]) maps to a composition; both PV/(PV+SST) and the disinhibitory
index VIP/(PV+SST) fall out of it. Brings V1-like AND association-like regimes under one model.
**Simplified single-compartment proxy — multi-compartment consciously declined.** The VIP→SST→pyr
disinhibitory motif is a candidate biological instantiation of H-C regulation — so it must be a
**CAPABILITY, not an installed circuit** (D074 rule): h sets proportions, selection must build the
loop. P is unaffected (h is compositional like Dale's-law identity, orthogonal to synapse count).
**Widens the central thesis** toward "the interneuron gradient unifies cortical regions" — chosen,
flagged, revisitable.

---

## Where the project stands

**THE FRAME (D056 — `FRAMING.md` §0).** Not "test Frank in a spiking network." **Map a REPERTOIRE
of learning behaviours in spiking networks under varying constraints and stimuli.** Frank's insight
— the parameter axis is where to look — is our INSTRUMENT. Double descent is the DIAGNOSTIC, not the
phenomenon. **REGULARIZATION ≠ REGULATION (D055).** Constructive question: *why does regulatory
hierarchy emerge? Candidate: because encoding saturates.*

**STANCE CORRECTION (D083, this round).** Frank's premise is **CONDITIONAL** — double descent appears
in systems that *don't penalize complexity*. So the stance is **test the conditional at its critical
case** (a neural substrate that plausibly DOES penalize complexity, with a within-life inner loop his
examples lack) — **not "refute Frank."** His parameter is the **regulatory CONNECTION** (edge, not
node), which is what unifies deep-nets/GRNs/SNNs and justifies **P = non-zero synapse count**.

### THE TWO LEVELS (D048; sharpened D072)
- **Level 1** — given this stimulus, what response? **No memory.** `f_c(E)`, rank r₁.
- **Level 2** — which map applies? **Needs memory** (context lives in statistics across dwell=10,
  never a single stimulus, never the mean).

| | needs memory? | status |
|---|---|---|
| **H-A** error vs **P=\|W\|** peaks at **P\*** | no — level 1 | live once routing works |
| **H-B** **P\* set by r₁, NOT the constraint count** ← *what distinguishes us from ML* | no — level 1 | live once routing works; r₁-independent-of-n_env CONFIRMED in tasks.py |
| **H-C** past P\*, error descends **only if** modulating (not driving) structure emerges | yes — level 2 | blocked on development |
| **H-D** no fluctuation-driven regime ⇒ no second descent ← *the spiking test* | yes — level 2 | blocked + confounded (below) |
| **H-E** variance is the medium of regulation — a LOOP, not an hourglass | yes — level 2 | blocked on development |

**WHY THE GA AT ALL (D083 stance session).** For H-A/H-B (curve SHAPE) random-sample-and-develop is
arguably CLEANER than the GA — selection biases which networks you sample. **The GA's essential job is
H-C: emergence UNDER SELECTION** (a sample shows regulation is *possible*, not that selection *drives
toward* it — Frank's actual claim). ⇒ probable design: **sample-and-develop for H-A/H-B and as the
H-C baseline; GA on top for H-C.** Sampling is a needed CONTROL, not a replacement.

**REGIONAL GRADIENT (this round).** DD-propensity ordered cerebellum > sensory > association.
- **cerebellum** — feedforward random expansion; DD-equivalent (expansion-coding) is ESTABLISHED
  (Marr-Albus → Litwin-Kumar → Xie 2023). **Cite it; outside our recurrent apparatus's range.** Our
  positive control may already instantiate it (verify).
- **primary sensory (V1)** — biologically-grounded models exist (Allen); **DD never analyzed on
  them** — genuinely open.
- **association** — **ours.** The apparatus (recurrent + regulated inhibition) spans V1→association;
  the environment-structure axis plausibly moves it along that span. Cerebellum is the one region it
  cannot reach.

**BUILT & VALIDATED:**
- `evonet.py` — W is the genome; Dale's law, evolvable identity (D038); `inh_gain` E/I balance
  (D058); slow NMDA-like current `nmda_frac` charge-conserved (D074/D075); `readout_pos` (D072); no
  trained readout; phenotype = behaviour (D036). **`behave_batch` block-diagonal runner, bit-for-bit
  verified (D078).**
- `evolve.py` — selection scheme & density are ARMS; product-rule mutation (D043); crossover off;
  **three-tier test capture (D077); batched default (D078); routing metric `_routing_nmse` on a fixed
  200-env probe (D081); progress+ETA+mode announcement (D066, finally).**
- `tasks.hierarchical_environments` — context in COVARIANCE not mean (D048/D057); rank-r₁ maps;
  **r₁ independent of n_env CONFIRMED**; `headroom()` required (D057).
- `provenance.py` — `run.start_log()` writes `logs/run.log` (D072).
- ✅ **POSITIVE CONTROL PASSES (D061/D063)** — apparatus can express DD ⇒ a later null is the biology,
  not broken plumbing. *(DD lives in the random-feature readout — Belkin's setting — says nothing
  about the network yet.)*
- ⚠️ **GATE C PASSED ON CV_ISI ONLY (D058/D069)** — worst-cell operating point; needs a v2 gated on
  skill AND CV_ISI jointly.
- ⛔ **GATE A FAILED (D082)** — routing not established on birth-fitness; the current blocker.

## ⚠️ H-D IS CONFOUNDED FOUR WAYS (unchanged; still live for when H-D runs)
`noise_sigma` (tonic 0.2 vs balanced 1.0) changes: (1) gain-control availability — intended (D039);
(2) fitness signal-to-noise — fresh noise every eval makes the balanced arm noisier by construction
(*fix: common random numbers*); (3) encoding fidelity — *fix: gain=30 gives an iso-encoding pair,
E|state 0.228 vs 0.239*; (4) slow-mode retention — σ=1.0 kicks slow modes every step.
**(3)'s fix RE-GATES:** gain=30 pushes CV_ISI down, may collapse the contrast. ⇒ **Gate C v2 = 2D
(gain × σ) sweep on BOTH skill AND CV_ISI**; if empty, H-D is unrunnable — a finding, not a failure.

## D030's OPPOSITION — now FOUR appearances, but D076 found the BREAK
| | level-2 property | costs level-1 encoding |
|---|---|---|
| D030 | PR responsiveness | ✓ |
| D069 | CV_ISI | ✓ |
| D072 | memory (carryover) | ✓ |
| **D076** | **slow current (memory)** | **✗ — encoding-NEUTRAL via charge conservation** |
*The opposition was buying level-2 by cranking a knob that also floods level-1. A charge-neutral knob
(D075) does not pay the tax. This is a point FOR the substrate framing — worth a measurement.*

## Open (non-blocking; address as they become relevant)
- **`FRAMING.md` §3 NEEDS REWRITING (D072)** — banner added; the PR_mean/PR_var substrate
  justification is reservoir-era and does not transfer. Rewrite pending generalization measured on
  evonet (needs the GA, i.e. needs development first).
- **`tasks.py` dead code:** `learnable_frac < 1.0` branch has a `for…: pass` no-op and applies the
  blend AFTER noise (noise scaled by blend). Harmless at 1.0; **live bug for the D051 sweep.**
- **Deck (`CLL_double_descent.pptx`)** — fold in the corrected stance and the interneuron direction at
  its NEXT revision (after development work; fine to present as-is meanwhile — it's a project-in-
  progress).
- **Is the H-E loop predictive coding rediscovered?** (Rao & Ballard / Friston.) Ours emerges under
  selection and its emergence IS the second descent (search: zero DD↔PC hits).
- **r₂** — contexts drawn independently ⇒ level 2 has no rank structure. If the hierarchy is real, r₂
  should be a knob — the natural place for a *second* waist.
- **N as a gene** — next study; needs high per-node cost. *(Also: is N=50 large enough for a
  slow-reverberation memory attractor? Brunel suggests maybe not — a live question for the D082
  rematch.)*

## Standing rules (earned the hard way)
- **Search before building.** Repeatedly a PJM-requested search overturned my reasoning: D014, D031,
  D034, D039, D043, D053, and the Brunel/Wang search behind D074.
- **Name the quantity your cost model assumes cost scales with, and MEASURE it before deciding**
  (D068). Four runtime estimates in a row were wrong (D060/D064/D065/D067). The 27× batching win was
  measured, not assumed (D079).
- **Watch the parallelism state, not just the wall clock** (D065/D066).
- **Prove the system beats a trivial baseline before interpreting a metric** (D030); **check what the
  baseline IS — an identity is not a gate** (D069); **measure the baseline at the EXACT operating
  point before gating on it** (D081: the 0.73 "baseline" was a grid-min artifact). **`headroom()`
  before any run** (D057).
- **Docstrings state RULES; results carry a D-number/run_id** (D070). **A decision that specifies code
  is NOT done until the code exists** (D071).
- **Measure the substrate before blaming the optimizer** (D072).
- **Don't bolt on mechanisms; make the architecture capable and let selection build them** (D038).
  Corollary (D073): withholding a CAPABILITY doesn't force the mechanism if the capability is its
  PREREQUISITE. Corollary (D074): don't install a ready-made instance of the mechanism under test (the
  NMDA Mg-gate; the wired VIP→SST loop).
- **E/I balance (incl. temporal balance) is a PRECONDITION, not a hypothesis** (D075).
- **Verify equivalence (bit-for-bit) before trusting any speedup** (D078) — should-be-fines have twice
  been bugs (the pool that never ran D065; the 16× charge D075).
- **Fitness must reduce the DEVELOPED distribution, not the birth one** (D083) — the newest rule, and
  the reason Gate A was flat.
- **Minimal genome = maximum attribution** (D059). **`noise_sigma` is NEVER a gene.**
