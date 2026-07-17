# Queue

Updated 2026-07-17 (end of session). Claims → `DECISIONS.md` · framing → `FRAMING.md` ·
chain → `BRIDGE.md` · narrative → `LAB_NOTEBOOK.md`.

---

# ⛔ THE BLOCKING RESULT: GATE B0 FAILED (D067)

**`best_train` 0.936 → 0.882 over 100 generations. Never near interpolation. Worse than the
memoryless floor (0.834)** — after 100 generations of selection the evolved network is worse than
having no network at all.

**The diagnosis is ARITHMETIC, not biology.** |W| = 1,221 params optimized with 3,000 evaluations.
Evolution strategies need **~100 × n_params ⇒ ~122,000**. **We are 40× short. The GA did not fail —
it barely started.**

**The wall:** ~1.7 s/eval on 6 workers ⇒ 122,000 evals ≈ **58 h for ONE arm**; the 72-arm map ≈
**4,000 h.** *Evaluation cost is now a first-class design constraint.*

**⇒ THE DECISION THAT MUST BE MADE FIRST, BEFORE ANY MORE CODE:**

| N | \|W\| @ dens 0.5 | evals (~100n) | per arm | verdict |
|---|---|---|---|---|
| 50 (current) | 1,221 | 122,000 | **58 h** | ✗ infeasible |
| 30 | ~435 | 43,500 | ~8 h | marginal |
| **20 (proposed)** | **~190** | **19,000** | **~1.5 h** | ✓ feasible |

**N=20 is Frank's own scale** — 2025a: *"a sparsely and randomly connected network with 20 nodes
stores an imperfect and dimensionally reduced memory of past inputs."*
Proposed: **N=20, d=3, n_env=20 → 60 constraints, |W|/constraints ≈ 3.2** (still overparameterized).
Other levers to price: `present_ms` 150→50 (~3× faster); fewer environments (also lowers the
constraint count, moving the threshold *toward* us).

**THE HONEST TRADE (weigh deliberately — not a parameter tweak):** the script's own warning (D062)
was right — **this is a DESIGN failure, not a finding about biology.** But it says **the study as
scoped may be computationally infeasible**, and the fix shrinks networks to where *"spiking network"*
is a generous description.

**Alternatives if N=20 is unacceptable:** CMA-ES or a stronger ES · surrogate/cheaper fitness ·
fewer constraints · accept ~58 h/arm and run far fewer arms · reconsider the substrate.

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
  rank-r₁ level-1 maps (B2); **headroom 0.62** verified (memoryless 0.819 vs oracle 0.197);
  `learnable_frac` = the D051 axis. **`headroom()` is a required pre-run check.**
- `evolve.py` — **selection scheme is an ARM** (replicator has the Occam factor; tournament does
  not — *Friedlander used tournament, R&N used replicator*); **density mode is an ARM** (fixed =
  "does the curve have a peak?"; evolvable = "where does evolution LAND?"); product-rule mutation
  (D043); crossover OFF (competing conventions); parallel + progress/ETA (D064–D066).
- ✅ **GATE C PASSED (D058)** — 31/36 fluctuation-driven, CV_ISI to 1.07. **H-D has both arms via
  ONE knob:** noise 0.2 → CV≈0.5 (tonic, gain control unavailable) vs noise 1.0 → CV≈1.0 (balanced,
  divisive gain available). Operating point: bias 0.6, gain 1.0, w0 0.6, density 0.3.
- ✅ **POSITIVE CONTROL PASSES (D061/D063/D067)** — peak at **M/n = 1.00 exactly**, second descent
  202 → 2.50. **The apparatus can express double descent** ⇒ a later null is attributable to the
  evolutionary setting, not broken plumbing. *But the DD lives entirely in the **readout over random
  features** (Belkin's setting) — it says nothing about the network.*

**Suggestive, not leanable:** the classical **optimum sits at M=2** (r₁=3) while the **peak sits at
M/n=1.00** — two quantities, two places, **as H-B predicts**. First descent is trivial (0.3%).

**Unresolved and now unanswerable until B0 passes:** **Gate A** — the reservoir states **never beat
the raw-input baseline** (best 1.034 vs 0.834). That is a RANDOM network; **E9's premise is that
selection fixes it.**

## The hypotheses (D047, `BRIDGE.md`)
- **H-A** error vs **P=|W|** peaks at **P\***.
- **H-B** **P\* is set by r₁, NOT n** ← *what distinguishes us from ML*. Vary r₁ and n independently.
- **H-C** past P\*, error descends **only if** modulating (not driving) structure emerges.
- **H-D** **no fluctuation-driven regime ⇒ no second descent** ← **the spiking test; an INTERNAL
  on/off switch for the mechanism** (Gate C proved both arms reachable).
- **H-E (D048)** variance is where the **second-level regularity lives**; past the waist its **role
  changes** from encoding-overflow to the **medium of regulation**. *Not an hourglass — a **LOOP**:
  the regulator reads the encoder's fluctuation statistics and modulates back into it.*

## After B0 is unblocked
1. **Gate A** — does evolution beat the raw-input baseline? (per density arm; D030)
2. **Gate B** — does a peak appear at all? *Where the project lives or dies.*
3. **The map** — three curves on one axis (D046/D050): error · **regulatory emergence** (D040's
   three stages) · **sloppiness** (Bartlett's condition — a **rival mechanism with independent
   support**; Frank cites Gutenkunst AND benign overfitting and never connects them).
4. **The discriminating sweep (D051):** vary the **learnable fraction** of unexplained variance —
   not the noise level. Corners are **literature-replication controls** (Bartlett; Ali et al.);
   **mixed + no cost is THE EXPERIMENT.**
5. **Graded controls (D052):** each control is a **dial**, not pass/fail — native SNN+selection →
   +gradient → +linear readout. **Wherever the phenomenon first appears names its precondition**
   ("optimizer was binding" vs "model class was binding").

## Open
- **Is the H-E loop predictive coding rediscovered?** Rao & Ballard / Friston. **Emergence is
  already shown** — Ali et al. (energy efficiency, RNNs) and a 2025 multi-compartment **SNN** paper.
  **Ours would be:** it emerges **under selection**, and its emergence **IS the second descent**
  (search found **zero** hits linking DD to PC). *`c_syn` is our energy cost — the same lever.*
- **Is PR the wrong measure?** Superposed features are non-orthogonal. **Interference vs abstraction
  both lower PR and PR cannot tell them apart.** Feature-recovery (sparse coding) may be right.
- **r₂** — contexts are currently drawn independently, so level 2 has **no rank structure**. If the
  hierarchy is real, **r₂ should be a knob** — and the natural place to look for a *second* waist.
- **Arm 2 genome (D059):** + τ_m / v_thresh — regulation then **competes** with timescale tuning.
  *Signature: a bimodal τ_m distribution at the waist = a timescale hierarchy, not a regulatory one.*
- **Fixed-but-heterogeneous τ_m** — a **capability, not a route**; may reduce reliance on injected
  noise. Cheap to test in Gate C's harness.
- **N as a gene** — next study; needs high per-node cost.

## Standing rules (earned the hard way)
- **Search before building.** Six times a PJM-requested search overturned my reasoning: D014, D031,
  D034, D039, D043, D053.
- **Watch the process count, not just the wall clock** (D065) — a silently-serial pool looks exactly
  like slow code. **Any run > a few minutes must print progress, an ETA, and its parallelism state**
  (D066).
- **Prove the system beats a trivial baseline before interpreting any representational metric**
  (D030). **Check the environment PERMITS the phenomenon before concluding it is absent** (D045).
  **`headroom()` before any run** (D057).
- **Log-transform heavy-tailed outcomes; treat convergence warnings as results** (D028).
- **Don't raise structural alarms from smoke-preset numbers** (D033).
- **Don't bolt on mechanisms; make the architecture capable and let selection build them** (D038).
- **Geometry does not imply mechanism** (D040).
- **Minimal genome = maximum attribution** (D059). **`noise_sigma` is NEVER a gene** — it is H-D's
  treatment variable.
