# Queue

Updated 2026-07-17 (D072/D073). Claims → `DECISIONS.md` · framing → `FRAMING.md` ·
chain → `BRIDGE.md` · narrative → `LAB_NOTEBOOK.md`.

---

# ⛔ THE BLOCKING QUESTION: can a slow SYNAPTIC timescale reach `mem_d10`? (D073)

**THE DIAGNOSTICS ARE DONE AND THE ANSWER IS ARITHMETIC. The network holds ~30 ms. Context needs
1,500 ms.**

- **`mem_d1` = 1.000 in all 8 trailing cells** — not 0.99, exactly 1.0, at every gain and noise.
  **`order/noise` = 0.98–1.16.** Two independent measures, same answer: **memoryless.**
- **Rung 1** (read the onset, not the settled response) recovers d1 → **0.531**, MC → 0.47,
  order/noise → 6.09. **But `mem_d2` = 1.000 in EVERY leading cell.** A **cliff, not a decay**:
  d1's window has a **zero gap** from the previous presentation's end; d2 is 150 ms back =
  e^(−150/30) = **0.7%**. ⇒ **window overlap catching `r`'s filter tail, NOT a collective mode.
  There is no hidden long memory.**
- **And rung 1 is not adoptable:** `E|state` 0.225 → 0.492, `E|rates` 0.730 → **0.931**. It halves
  encoding and starves what fitness reads.

**⇒ GATE B0 COULD NOT HAVE PASSED AT ANY N, ANY POPULATION, ANY NUMBER OF GENERATIONS.** D067's
~40× evaluation shortfall was **real and not binding**. *We diagnosed the wrong constraint twice:
not the budget (D067), not a broken encoder (D069).*

**THE ENCODER WORKS.** `E|state` = **0.225** (1.0 = blind). `E|rates` = **0.730** — E is in the
state and barely reaches the output neurons. **Gate A is a ROUTING problem, and routing is exactly
what selection is for.** *Not a broken network. Gate A was answerable all along; D067 declared it
"unanswerable until Gate B0 passes" and that was wrong.*

**⇒ THE NEXT MEASUREMENT — 4 min, NO GA, and the gate is `mem_d10`:**

| change | why |
|---|---|
| **τ_syn per-neuron**, bimodal **AMPA(~5 ms) / NMDA(~100 ms)**-like, **DRAWN not evolved** | D073. The only knob that spans 1,500 ms. **τ_m = 200 ms is NOT physiological** (cortical τ_m is 10–50 ms); `dI_syn/dt = -I_syn/tau_syn` is already in the equations at 5 ms = AMPA. Only the SCOPE changes. |
| **`present_ms` 150 → 50**, `readout_window_ms` reduced below it | D073: **neither knob works alone.** τ=200 alone → e^(−1500/200) = 0.06%. `present_ms`=50 alone → e^(−500/30) ≈ 0%. **Both → e^(−500/200) = 8%.** τ=300 → **19%.** *And it is D068's **3× compute win** — the one lever that is both a scientific fix and a speedup.* |
| **gate = `mem_d10`**, not `mem_d1` | d1 is free (window overlap). d10 is the task. |

**Validated WITHOUT evolution** — which is why it comes before the batching work, not after.

---

## Where the project stands

**THE FRAME (D056 — `FRAMING.md` §0).** Not "test Frank in a spiking network." **Map a REPERTOIRE
of learning behaviours in spiking networks under varying constraints and stimuli.** **Frank's
insight — the parameter axis is where to look — is our INSTRUMENT. Double descent is the
DIAGNOSTIC, not the phenomenon.** Three coordinates: **environment structure** (learnable
fraction) · **cost** (`c_syn`; 0 = Frank's assumed regime) · **dynamical regime** (tonic vs
balanced). **REGULARIZATION ≠ REGULATION (D055).** **The constructive question: why did regulatory
hierarchy evolve? Candidate answer: because encoding saturates.**

### THE TWO LEVELS — the structure that organises everything (D048; sharpened by D072)
- **Level 1** = *given this stimulus, what is the right response?* **Needs no memory.** `f_c(E)`,
  rank r₁.
- **Level 2** = *which map applies right now?* **Needs memory**, because context lives in the
  statistics across `context_dwell`=10 stimuli — never in any single one, and never in the mean
  (D048/D057).

**The hypotheses split cleanly on it, and so does the blocker:**

| | needs memory? | status |
|---|---|---|
| **H-A** error vs **P=\|W\|** peaks at **P\*** | **no** — level 1 | **unaffected** |
| **H-B** **P\* is set by r₁, NOT n** ← *what distinguishes us from ML* | **no** — level 1 | **unaffected** |
| **H-C** past P\*, error descends **only if** modulating (not driving) structure emerges | yes — level 2 | **blocked** |
| **H-D** no fluctuation-driven regime ⇒ no second descent ← *the spiking test* | yes — level 2 | **blocked** + confounded (below) |
| **H-E** variance is where the second-level regularity lives; past the waist its **role changes** — *a LOOP, not an hourglass* | yes — level 2 | **blocked** |

**Layering is an ORDERING, not an escape: D056's frame is level 2.** The memory gap must close.

**What is BUILT and VALIDATED:**
- `evonet.py` — W is the genome; Dale's law with **evolvable per-neuron identity** (D038);
  **inh_gain** for E/I balance (D058); no trained readout; phenotype = behaviour (D036);
  **`readout_pos`** trailing|leading (D072, default unchanged).
- `tasks.hierarchical_environments` — **context in the COVARIANCE, never the mean** (D048/D057);
  rank-r₁ level-1 maps; `learnable_frac` = the D051 axis. **`headroom()` required before any run**
  (D057). *The oracle is a ridge-LINEAR per-context fit against a `tanh` target, so it does NOT cap
  a nonlinear network — `best_train < 0.05` was never forbidden. At `learnable_frac`=1.0,
  `noise_sd`=0: targets are DETERMINISTIC given (E, context).*
- `evolve.py` — **selection scheme is an ARM** (replicator has the Occam factor; tournament does
  not — *Friedlander used tournament, R&N used replicator*); **density mode is an ARM**;
  product-rule mutation (D043); crossover OFF (competing conventions).
- `provenance.py` — **`run.start_log()`** finally writes `logs/run.log` (D072). *NAMING.md §3
  specified it since the scaffold and nothing ever wrote to it.*
- ⚠️ **GATE C PASSED ON CV_ISI ONLY (D058) — D030's error one level up (D069).** Its operating
  point (bias 0.6, **gain 1.0**, w0 0.6) is the **worst cell** in the gain × σ grid: `E|state`
  0.605, `E|rates` **1.001** — the output neurons carry *nothing*. **Gate C needs a v2 gated on
  skill AND CV_ISI jointly.**
- ✅ **POSITIVE CONTROL PASSES (D061/D063)** — peak at **M/n = 1.00**, second descent 202 → 2.50.
  **The apparatus can express double descent** ⇒ a later null is attributable to the evolutionary
  setting, not broken plumbing. *But the DD lives entirely in the **readout over random features**
  (Belkin's setting) — it says nothing about the network.*

## ⚠️ H-D IS CONFOUNDED FOUR WAYS
`noise_sigma` does not change only gain-control availability. Tonic (0.2) vs balanced (1.0) differ in:
1. **gain-control availability** — the intended manipulation (D039).
2. **fitness signal-to-noise** — `EvoNetConfig.seed=None` ⇒ **fresh noise every eval** ⇒ the
   balanced arm is noisier **by construction**. *Fix: **common random numbers** — one seed shared
   within a generation, varying across generations. Free; standard for noisy ES.*
3. **encoding fidelity** — measured. *Fix, one line: at **gain=30** the arms read `E|state`
   **0.228 vs 0.239** — an **iso-encoding tonic/balanced pair**. Run H-D there.*
4. **slow-mode retention** — σ=1.0 kicks any slow collective mode every timestep.

**But (3)'s fix must be RE-GATED:** gain=30 is strong mean drive, pushing CV_ISI **down** in both
arms and possibly collapsing the contrast. **Encoding and fluctuation-drivenness are in
opposition.** ⇒ **GATE C v2 = a 2D sweep over (gain × σ) measuring BOTH E-decode skill AND
CV_ISI**, looking for a region where both hold. **If it is empty, H-D is unrunnable — a finding
about the substrate, not a design failure.** *(CV_ISI needs a SpikeMonitor in `behave()`; the skill
axis already exists in `run_E9_diagnostics.py`.)*

## D030's OPPOSITION, FOUR APPEARANCES — watch this
| | the level-2 property | costs the level-1 property |
|---|---|---|
| D030 | PR responsiveness | input encoding |
| D069 | CV_ISI (fluctuation-driven) | input encoding |
| **D072** | **memory (carryover)** | **input encoding** |

*Every knob that buys a level-2 property costs level-1 encoding.* **Candidate explanation
(SPECULATIVE — recorded to be tested, not leaned on):** the state has finite capacity, and current
input / recurrent dynamics / noise / history compete for it. **If true this is not an annoyance but
the precondition for D056's frame** — encoding saturates, which is *why* leveling up needs new
structure rather than more of the same.

## After `mem_d10`
1. **Gate C v2** — gain × σ, jointly gated on skill and CV_ISI.
2. **The performance work (D068)** — see below. **Nothing conclusive runs without it.**
3. **Gate A** — does evolution route E to the output neurons? (per density arm; D030)
4. **Gate B** — does a peak appear at all? *Where the project lives or dies.*
5. **The map** — three curves on one axis (D046/D050): error · **regulatory emergence** (D040's
   three stages) · **sloppiness** (Bartlett's condition — a **rival mechanism with independent
   support**).
6. **The discriminating sweep (D051):** vary the **learnable fraction** of unexplained variance.
   Corners are **literature-replication controls**; **mixed + no cost is THE EXPERIMENT.**
7. **Graded controls (D052):** each control is a **dial** — native SNN+selection → +gradient →
   +linear readout. **Wherever the phenomenon first appears names its precondition.**

## The performance work (D068) — PARKED, and this is what un-parks it
Batching · common random numbers · drop the discarded test eval · pre-allocated synapses (absent = weight 0), built once ·
hoist the StateMonitor. **~17×, all of it still on paper.**
**The parking was right for a reason we could not have known:** the diagnostics cost 4 minutes and
showed Gate B0 could not have passed at any speed — building the 17× first would have made an
impossible run 17× faster.
**⇒ UN-PARKS THE MOMENT `mem_d10` COMES BACK POSITIVE.** The next step after that is a GA run, and
that run is **~69 h unbatched, ~4 h batched**. *Projected: pop30×100gens 85 min → ~5 min; Gate B's
6-arm sweep ~17 h. **MEASURE the per-generation time before believing any of it** (D068: four
consecutive runtime estimates were wrong).*
*Also lands with it: **D066 fixes 2–3** (per-gen ETA, pool announcement), never implemented (D071),
and `run.start_log()` in `run_GateB0_interpolation.py`.*

## Open
- **`FRAMING.md` §3 NEEDS REWRITING (D072).** It justifies the spiking substrate on **one** finding
  of our own — PR_mean compresses, PR_var expands, PR_var predicts generalization. That is
  D028/D033: **N=1000 reservoir, K=20, `anisotropic_regression`, trained readout — all four retired
  by D032/§2c, in the SAME SESSION §3 was written.** Measured on `evonet`: **PR_input 5.86 →
  PR_mean 6.95–7.18 — mild EXPANSION. Compression does NOT transfer.** And PR_var **tracks σ**
  (12.67 → 26.67 as σ goes 0.2 → 1.0); read the onset and it collapses to **8.4–9.4 regardless of
  σ**, next to PR_mean ≈ 7. **The dissociation largely evaporates.** *§3's real claim is about
  PREDICTION, which remains untested — it needs generalization measured across conditions.*
- **`tasks.py` dead code:** the `learnable_frac < 1.0` branch has a `for ...: pass` no-op and
  applies the blend **after** the noise is added (so noise is scaled by `blend`). Harmless at 1.0;
  **a live bug for the D051 sweep, which is the study's main axis.**
- **Is the H-E loop predictive coding rediscovered?** Rao & Ballard / Friston. **Ours would be:** it
  emerges **under selection**, and its emergence **IS the second descent** (search found **zero**
  hits linking DD to PC). *`c_syn` is our energy cost — the same lever.*
- **Is PR the wrong measure?** **Interference vs abstraction both lower PR and PR cannot tell them
  apart.** Feature-recovery (sparse coding) may be right.
- **r₂** — contexts are drawn independently, so level 2 has **no rank structure**. If the hierarchy
  is real, **r₂ should be a knob** — the natural place to look for a *second* waist.
- **Arm 2 genome (D059):** + τ / v_thresh. **D073 flips the signature:** if τ is regulation's
  PREREQUISITE rather than its alternative, Arm 2 should show **long τ AND regulatory motifs —
  both, not either.** Bimodality would be a step toward regulation, not a substitute.
- **N as a gene** — next study; needs high per-node cost.

## Standing rules (earned the hard way)
- **Search before building.** Six times a PJM-requested search overturned my reasoning: D014, D031,
  D034, D039, D043, D053.
- **Name the quantity your cost model assumes cost scales with, and MEASURE it before deciding on
  it** (D068). Four consecutive runtime estimates — D060 (arms), D064 (nesting), D065 (workers),
  D067 (parameters) — each wrong because of an unnamed scaling assumption.
- **Watch the process count, not just the wall clock** (D065). **Any run > a few minutes must print
  progress, an ETA, and its parallelism state** (D066) — *still unimplemented*.
- **Prove the system beats a trivial baseline before interpreting any representational metric**
  (D030) — **and check what the baseline IS: if it is an identity, it is not a gate** (D069).
  **Check the environment PERMITS the phenomenon before concluding it is absent** (D045).
  **`headroom()` before any run** (D057).
- **Docstrings state RULES; results carry a D-number or run_id** (D070). **And the reverse: a
  decision that specifies code is NOT DONE until the code exists — cite the D-number in the commit
  that implements it** (D071: D066 was never built; D067 planned around it anyway).
- **Measure the substrate before blaming the optimizer** (D072). *Four minutes of diagnostics
  overturned a decision that was about to shrink the network.*
- **Log-transform heavy-tailed outcomes; treat convergence warnings as results** (D028).
- **Don't raise structural alarms from smoke-preset numbers** (D033).
- **Don't bolt on mechanisms; make the architecture capable and let selection build them** (D038).
  **And the corollary (D073): withholding a CAPABILITY does not force the mechanism if the
  capability is the mechanism's PREREQUISITE — it just removes both.**
- **Geometry does not imply mechanism** (D040).
- **Minimal genome = maximum attribution** (D059). **`noise_sigma` is NEVER a gene** — it is H-D's
  treatment variable.
