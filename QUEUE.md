# Queue

Updated 2026-07-17 (D068–D070). Claims → `DECISIONS.md` · framing → `FRAMING.md` ·
chain → `BRIDGE.md` · narrative → `LAB_NOTEBOOK.md`.

---

# ⛔ THE BLOCKING QUESTION: can a RANDOM network see anything? (D069)

**The N decision is CANCELLED (D068).** D067 priced each N assuming per-eval cost ∝ |W|. **It is
∝ TIMESTEPS**, which N does not touch: 50 env × 150 ms ÷ 0.5 ms × 2 (train+test) = **30,000
timesteps/eval**; 3.4 s serial ÷ 30,000 ≈ **113 µs/timestep to update 50 floats** — pure Python
dispatch. **N=20 gives ~9 h/arm, not 1.5 h. It never rescued anything.** ⇒ **N=50 stands** (the
scale Gate C was validated at; N=20 at density 0.3 gives ~6 recurrent inputs/neuron, which is not
a balanced regime). *The real lever is batching — engineering, not scale.*

**D067's SHORTFALL DIAGNOSIS STILL STANDS:** |W| = 1,221 optimized with 3,000 evaluations, ~40×
short of the ~100 × n_params an ES needs. **But it may not be the binding constraint** — and that
is what the diagnostics decide.

**⇒ THE FOUR MEASUREMENTS THAT COME BEFORE ANY MORE CODE (~15 min total):**

| # | measurement | what it decides | cost |
|---|---|---|---|
| **1** | **decode E from `state`** — D030's ACTUAL gate | is the encoder fine? (D069 says yes; this proves it) | 2 min |
| **2** | **decode E from `rates`** (the last d of N) | fitness reads d neurons. **Does E reach them?** *This is Gate A, sharpened: it separates "encoder broken" from "encoder fine, nothing reaches fitness".* | 2 min |
| **3** | **decode CONTEXT from `state`** (chance = 0.25) | **`BRIDGE.md` Level 5 lists this and it has NEVER been run.** *Is the system doing Level 2(iii) at all?* | 2 min |
| **4** | **`mean_train` vs `best_train`** from the existing parquet | we record both (D059). **If mean is flat while best declines, D067's "learning" was selection on noise** — `EvoNetConfig.seed=None` ⇒ fresh noise every eval ⇒ `best_train` is a min over 30 noisy draws. | 1 min |

**THE HONEST STATE:** D063's "the states never beat raw input" is **not** evidence of a broken
network (D069: `baseline ≡ memoryless_floor`, so that bar **is** the whole experiment). The
encoder reaches the memoryless floor lossily (0.835 vs 0.791) — exactly what a network with no
context inference must look like. **Gate A is open. It was never answered, only misread.**

---

## Where the project stands

**THE FRAME (D056 — `FRAMING.md` §0).** Not "test Frank in a spiking network." **Map a REPERTOIRE
of learning behaviours in spiking networks under varying constraints and stimuli.** The brain is not
a deep network; a brain is neither an organism nor a population. **Frank's insight — the parameter
axis is where to look — is our INSTRUMENT. Double descent is the DIAGNOSTIC, not the phenomenon.**
Three coordinates (= our three axes): **environment structure** (learnable fraction) · **cost**
(`c_syn`; 0 = Frank's assumed regime) · **dynamical regime** (tonic vs balanced).
**REGULARIZATION ≠ REGULATION (D055).** Regularization = machinery that prevents overfitting
(abundant literature). Regulation = a level that **modulates another level** (**origin
unexplained**). **The constructive question: why did regulatory hierarchy evolve? Candidate answer:
because encoding saturates.**

**What is BUILT and VALIDATED:**
- `evonet.py` — W is the genome; Dale's law with **evolvable per-neuron identity** (D038);
  **inh_gain** for E/I balance (D058); no trained readout; phenotype = behaviour (D036).
- `tasks.hierarchical_environments` — **context in the COVARIANCE, never the mean** (D048/D057);
  rank-r₁ level-1 maps (B2); **headroom 0.62** verified (memoryless 0.819 vs oracle 0.197 — note
  the oracle is a **ridge-LINEAR** per-context fit against a `tanh` target, so it does **not** cap
  a nonlinear network, and `best_train < 0.05` was never forbidden by the task);
  `learnable_frac` = the D051 axis. **`headroom()` is a required pre-run check.**
  *At `learnable_frac=1.0` (Gate B0's setting) `noise_sd = 0`: training targets are DETERMINISTIC
  given (E, context). Interpolation is permitted by the task.*
- `evolve.py` — **selection scheme is an ARM** (replicator has the Occam factor; tournament does
  not — *Friedlander used tournament, R&N used replicator*); **density mode is an ARM** (fixed =
  "does the curve have a peak?"; evolvable = "where does evolution LAND?"); product-rule mutation
  (D043); crossover OFF (competing conventions); parallel + progress/ETA (D064–D066).
- ⚠️ **GATE C PASSED ON CV_ISI ONLY (D058) — and that is D030's error, one level up (D069).**
  31/36 fluctuation-driven, CV_ISI to 1.07; **H-D has both arms via ONE knob** (noise 0.2 → CV≈0.5
  tonic; noise 1.0 → CV≈1.0 balanced). **But Gate C never asked whether the state encodes the
  input**, and its operating point (bias 0.6, **gain 1.0**, w0 0.6) is the **worst cell** in the
  gain × σ table (0.935 / 0.993 ≈ predicting the mean). **Gate C needs a v2 that gates on skill AND
  CV_ISI jointly.**
- ✅ **POSITIVE CONTROL PASSES (D061/D063/D067)** — peak at **M/n = 1.00 exactly**, second descent
  202 → 2.50. **The apparatus can express double descent** ⇒ a later null is attributable to the
  evolutionary setting, not broken plumbing. *But the DD lives entirely in the **readout over random
  features** (Belkin's setting) — it says nothing about the network.*

**Suggestive, not leanable:** the classical **optimum sits at M=2** (r₁=3) while the **peak sits at
M/n=1.00** — two quantities, two places, **as H-B predicts**. First descent is trivial (0.3%).

## The hypotheses (D047, `BRIDGE.md`)
- **H-A** error vs **P=|W|** peaks at **P\***.
- **H-B** **P\* is set by r₁, NOT n** ← *what distinguishes us from ML*. Vary r₁ and n independently.
- **H-C** past P\*, error descends **only if** modulating (not driving) structure emerges.
- **H-D** **no fluctuation-driven regime ⇒ no second descent** ← **the spiking test; an INTERNAL
  on/off switch for the mechanism.** ⚠️ **CONFOUNDED — see below.**
- **H-E (D048)** variance is where the **second-level regularity lives**; past the waist its **role
  changes** from encoding-overflow to the **medium of regulation**. *Not an hourglass — a **LOOP**:
  the regulator reads the encoder's fluctuation statistics and modulates back into it.*

## ⚠️ H-D IS CONFOUNDED IN FOUR WAYS

`noise_sigma` is not a knob that changes only gain-control availability. Tonic (0.2) vs balanced
(1.0) also differ in:

1. **gain-control availability** — the intended manipulation (D039).
2. **fitness signal-to-noise** — `EvoNetConfig.seed=None` ⇒ **fresh noise every evaluation** ⇒
   fitness is a noisy random variable, and the **balanced arm is noisier BY CONSTRUCTION**.
   *Fix: **common random numbers** — one noise seed shared by all individuals within a generation,
   varying across generations. Free; standard variance reduction for noisy ES; keeps the dynamics
   stochastic while making comparisons BETWEEN genomes clean.*
3. **encoding fidelity** — **0.835 (σ=0.2) vs 0.869 (σ=1.0)** at gain 10, measured.
   *Fix, and it is one line: at **gain=30** the arms read **0.835 vs 0.840** — an **iso-encoding
   tonic/balanced pair**. Run H-D there.*
4. **slow-mode retention** — σ=1.0 kicks any slow collective mode at every timestep, and slow modes
   are the only route to context inference (see Open).

**But (3)'s fix must be RE-GATED:** gain=30 is strong mean drive, which pushes CV_ISI **down** in
both arms and may collapse the H-D contrast entirely. **Encoding fidelity and fluctuation-drivenness
are in opposition — D030's opposition, third appearance.**
⇒ **GATE C v2 = a 2D sweep over (gain × σ) measuring BOTH E-decode skill AND CV_ISI**, looking for
a region where both hold. *That is Gate C with D030's gate applied.* **If the region is empty, H-D
is unrunnable — and that is a real finding about the substrate, not a design failure.**

## After the diagnostics
1. **Gate C v2** — gain × σ, jointly gated on skill and CV_ISI. Add **fixed-heterogeneous τ_m** as
   an arm if measurement 3 comes back at chance (see Open).
2. **Gate A** — does evolution beat the raw-input baseline? (per density arm; D030)
3. **Gate B** — does a peak appear at all? *Where the project lives or dies.*
4. **The map** — three curves on one axis (D046/D050): error · **regulatory emergence** (D040's
   three stages) · **sloppiness** (Bartlett's condition — a **rival mechanism with independent
   support**; Frank cites Gutenkunst AND benign overfitting and never connects them).
5. **The discriminating sweep (D051):** vary the **learnable fraction** of unexplained variance —
   not the noise level. Corners are **literature-replication controls** (Bartlett; Ali et al.);
   **mixed + no cost is THE EXPERIMENT.**
6. **Graded controls (D052):** each control is a **dial**, not pass/fail — native SNN+selection →
   +gradient → +linear readout. **Wherever the phenomenon first appears names its precondition**
   ("optimizer was binding" vs "model class was binding").

## The performance work (D068) — deliberately LAST
Batching · common random numbers · drop the discarded test eval · fixed topology / build once ·
hoist the StateMonitor. **None of the diagnostics or Gate C v2 need it**, and if the design cannot
pass at any budget, it is wasted. Projected pop30×100gens **85 min → ~5 min**; one N=50 arm at
required depth **~4 h**; Gate B's 6-arm sweep **~17 h**. **MEASURE the per-generation time before
believing any of that** (D068: four consecutive runtime estimates were wrong).

## Open
- **⚠️ THE TIMESCALE AUDIT — unverified arithmetic, but it is only config constants:**
  | quantity | value |
  |---|---|
  | longest state variable in the substrate | **τ_r = 30 ms** |
  | one stimulus | `present_ms` = 150 ms = **5 τ_r** |
  | settling before the readout opens | 150 − 60 = 90 ms = **3 τ_r** (previous trace ~5%) |
  | **the context timescale** | `context_dwell` 10 × 150 ms = **1,500 ms = 50 τ_r** |

  **`BRIDGE.md` Level 3 marks intrinsic timescales ✅ "inherent to LIF". 5–30 ms is not "inherent
  to" 1,500 ms.** The 60 ms terminal readout window makes it worse: it deliberately samples the
  **stationary response to the current stimulus**, after any single-neuron trace of the previous
  one is gone. *Counterargument (why Arm 1 is not provably dead): a recurrent network CAN hold state
  longer than its neurons — slow collective modes, line attractors. But that is the hardest object
  in the search space, and σ=1.0 kicks it at every timestep.* **This also explains the gain table
  better than "the encoder is broken": no gain buys MEMORY, and beating the memoryless floor
  requires memory.** ⇒ **Measurement 3 (decode context from state) is the test. Predict chance.**
- **Does D059's τ_m tier INVERT?** D059 tiers τ_m as an **"alternative route — could BYPASS
  regulation."** But `tasks.py`'s own docstring says: *"a one-hot context fed additively can only
  SHIFT the output, never change the E→Y mapping."* **A slow neuron produces a running average —
  drive, not gain. Additive. Useless by the task's own construction.** So integration and modulation
  may not be alternatives but **sequential**: τ gives step 1 (a context estimate); regulation is
  step 2 (using it multiplicatively). **If so, withholding τ does not force regulation — it removes
  its prerequisite**, and Arm 1 is "step 1 unavailable while step 2 is required."
  ⇒ **PJM's fixed-but-heterogeneous τ_m would be the minimal RESCUE of Arm 1, not a garnish**:
  *drawn, not evolved* ⇒ step 1 is a capability, evolution gets no tunable shortcut, regulation
  remains the only route to step 2. D059 already calls it *"cheap to test in Gate C's existing
  harness."* **Promote from footnote to Gate C v2 arm if measurement 3 is at chance.** Perez-Nieves
  is already in `REFERENCES.md`. *Sharper Arm 2 signature than D059's: if τ is the prerequisite
  rather than the alternative, Arm 2 should show **long τ AND regulatory motifs — both, not either.***
- **Is the H-E loop predictive coding rediscovered?** Rao & Ballard / Friston. **Emergence is
  already shown** — Ali et al. (energy efficiency, RNNs) and a 2025 multi-compartment **SNN** paper.
  **Ours would be:** it emerges **under selection**, and its emergence **IS the second descent**
  (search found **zero** hits linking DD to PC). *`c_syn` is our energy cost — the same lever.*
- **Is PR the wrong measure?** Superposed features are non-orthogonal. **Interference vs abstraction
  both lower PR and PR cannot tell them apart.** Feature-recovery (sparse coding) may be right.
- **r₂** — contexts are currently drawn independently, so level 2 has **no rank structure**. If the
  hierarchy is real, **r₂ should be a knob** — and the natural place to look for a *second* waist.
- **Arm 2 genome (D059):** + τ_m / v_thresh — regulation then **competes** with timescale tuning.
- **N as a gene** — next study; needs high per-node cost.
- **`tasks.py` dead code:** the `learnable_frac < 1.0` branch contains a `for arr, E_, C_ in
  ((None, E_tr, C_tr),): pass` no-op, and applies the blend **after** the noise is added (so noise
  is scaled by `blend` too). Harmless at `learnable_frac=1.0`; **a live bug for the D051 sweep,
  which is the study's main axis.**

## Standing rules (earned the hard way)
- **Search before building.** Six times a PJM-requested search overturned my reasoning: D014, D031,
  D034, D039, D043, D053.
- **Name the quantity your cost model assumes cost scales with, and MEASURE it before deciding on
  it** (D068). Four consecutive runtime estimates — D060 (arms), D064 (nesting), D065 (workers),
  D067 (parameters) — were each wrong because of an unnamed scaling assumption.
- **Watch the process count, not just the wall clock** (D065). **Any run > a few minutes must print
  progress, an ETA, and its parallelism state** (D066).
- **Prove the system beats a trivial baseline before interpreting any representational metric**
  (D030) — **and check what the baseline IS: if it is an identity, it is not a gate** (D069).
  **Check the environment PERMITS the phenomenon before concluding it is absent** (D045).
  **`headroom()` before any run** (D057).
- **Docstrings state RULES; results carry a D-number or run_id** (D070).
- **Log-transform heavy-tailed outcomes; treat convergence warnings as results** (D028).
- **Don't raise structural alarms from smoke-preset numbers** (D033).
- **Don't bolt on mechanisms; make the architecture capable and let selection build them** (D038).
- **Geometry does not imply mechanism** (D040).
- **Minimal genome = maximum attribution** (D059). **`noise_sigma` is NEVER a gene** — it is H-D's
  treatment variable.
