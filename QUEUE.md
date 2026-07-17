# Queue

Updated 2026-07-17. Claims → `DECISIONS.md`; framing → `FRAMING.md`; narrative → `LAB_NOTEBOOK.md`.

## THE FRAME (D056 — read FRAMING.md §0)

**Not** "test Frank in a spiking network." **Map a REPERTOIRE of learning behaviours in spiking
networks under varying constraints and stimuli.** The brain is not a deep network; a brain is
neither an organism nor a population. Some architectures may show classical double descent
(cerebellum); some classical encoding (primary sensory); much of the brain is multi-specific and
flexible — **and whether it shows these patterns is OPEN; nobody has looked in association cortex.**
**Frank's insight — the parameter axis is where to look — is our INSTRUMENT. Double descent is the
DIAGNOSTIC, not the phenomenon.**

**Three coordinates determine position in the repertoire** (= our three axes): **environment
structure** (learnable fraction) · **cost** (`c_syn`; 0 = Frank's assumed regime) · **dynamical
regime** (tonic vs balanced).

**The distinction everything rests on (D055): REGULARIZATION ≠ REGULATION.** Regularization =
machinery that prevents overfitting (abundant literature). Regulation = a level that **modulates
another level** (**origin unexplained**). **The constructive question: why did regulatory hierarchy
evolve? Candidate answer: because encoding saturates.**

**The tension nobody has noticed (D054):** Frank needs biology to be **unregularized** ("biology
tends not to penalize complexity... likely to experience the full consequences of the double descent
learning curve"). **Contradicted on both timescales** — brains regularize heavily (Hoel, priors,
homeostasis); **selection itself regularizes** (R&N's Occam factor). **Prevent overfitting and you
prevent the peak, definitionally.** *Is Frank's regime even reachable? The `c_syn` sweep asks.*

**KNOWN RISK (D053):** **Wang & Pope (2025, ICAART)** looked for double descent in SNNs — *"did not
show a clear pattern"* (feedforward, gradient, width sweep, MNIST/CIFAR — differs from ours on every
axis, and "no clear pattern" ≠ null). **But spiking physics may itself regularize** (bounded rates,
thresholds, sparsity). **If so Frank's import fails at the level of the neuron** — which would be a
finding, not a failure.

## Where the project stands

**The hypothesis is now mechanistic (D044–D046, FRAMING §0):** the waist is a point in the
**evolutionary trajectory** where encoding saturates and **regulation begins**. The second descent
is the added parameters **switching function**. Trajectory waist and architectural waist are the
same event from two angles.

**Both rivals re-diagnosed (D045):** Friedlander (waist = goal rank r) and R&N (q ≈ q*) find the
same thing by two mechanisms — but **their environments are FLAT**, so their convergence is forced
by design, not discovered. **Neither asks what excess parameters do once the system matches the
environment.** That is our question.

**Our model currently cannot test it.** Three concrete blockers below.

---

## BLOCKERS — B1/B2/B3/B3a now FIXED & VALIDATED (D057). Kept for the record.

**Status:** product-rule mutation is default; `tasks.hierarchical_environments` validated —
context in covariance not mean (means ≈0 across contexts), rank-3 level-1 maps, **headroom 0.62**
(memoryless 0.819 vs oracle 0.197). **`headroom()` is a required pre-run check** — if ≈0 the task
cannot pay for regulation.

### (original blockers)

### B1. Mutation operator is wrong → switch to PRODUCT rule
`evonet.mutate()` uses **sum-rule** (`mag + N(0,σ)`). Friedlander: sum-rule **fails 94–97%** of the
time to evolve a waist. **Fix:** `mag *= N(1, σ)`. Two lines. Without this we cannot see the thing
we are looking for.

### B2. Task is FULL RANK → a bow-tie is mathematically impossible
`tasks.profile_environments` builds E→profile from a random (K×d) matrix. Full rank ⇒ no waist,
ever (rank(AB) ≤ min(rank A, rank B)). **Fix:** make the level-1 map **rank-deficient** (rank r₁ ≪
min(K,d)).

### B3a. **Context must change stimulus STATISTICS, not the mean** (D048 — sharpest constraint)
If context shifts the *mean*, the encoder detects it directly and **no regulation is needed** — the
same collapse as signalling it. Context must be a change in the **distribution** stimuli are drawn
from (variance, correlation), so that **mean-over-short-window = level 1** and
**variance-over-long-window = context = level 2**. **The fluctuation channel is then literally
where the second-level regularity lives.**

### B3. Task is FLAT → the second descent is forbidden by construction
A single map E → tanh(E·Q·Wc) has **no higher-order structure to level up to**. We would reproduce
R&N exactly and wrongly conclude the second descent does not exist. **Fix — hierarchical
environments:**
- **Level 1:** within a context, E → response follows a rank-r₁ regularity.
- **Level 2:** *which* regularity applies depends on **context**; contexts have structure.
- Encoding-only systems converge on r₁ and stall. **Leveling up requires detecting context and
  MODULATING the level-1 map = regulation.**
*(Lineage: Kashtan & Alon's modularly varying goals established that structured goals drive
modularity. Ours is the claim that the transition **IS** the second descent.)*

---

## Critical path  (full chain: `BRIDGE.md`)

**Hypotheses now stated in model quantities (D047):** **H-A** error vs P peaks at P\*; **H-B** P\*
set by **r₁ not n** (*what distinguishes us from ML*); **H-C** descent iff modulating structure
emerges; **H-D** **no fluctuation-driven regime ⇒ no second descent** (**the spiking test — an
internal ON/OFF switch for the mechanism**).

**New stimulus requirement (D047):** **context must be INFERRED FROM HISTORY, not signalled** —
otherwise detecting it is a switch, not regulation. ⇒ environments need **two timescales**: fast
stimuli, slow context drift. *This is where the chain first requires dynamics.*

0. ✅ **GATE C PASSED (D058)** — 31/36 fluctuation-driven, CV_ISI up to 1.07. Required TWO fixes:
   **inhibitory gain** (`inh_gain = ei_split/(1-ei_split) = 4`, Brunel balance — E/I was 24:1) and
   **`noise_sigma > 0`** (recurrent fluctuations were too slow vs τ_m; noise is a *condition* real
   neurons have, not a bolted-on mechanism). **H-D now has both arms via ONE knob:** noise 0.2 →
   CV≈0.5 (tonic, gain control unavailable) vs noise 1.0 → CV≈1.0 (balanced, divisive gain
   available). Operating point: bias 0.6, gain 1.0, w0 0.6, density 0.3.

0b. ~~**GATE C moves UP** — it is now a prerequisite, not a follow-up.** Without a reachable
   fluctuation-driven balanced regime, **H-D has no treatment arm and gain-control regulation does
   not exist in the model at all** (D039/D047). `noise_sigma = 0` + tonic bias currently put us in
   the regime where inhibition is purely subtractive.

1. **Fix B1–B3.** Product mutations; rank-deficient level-1 map; hierarchical (context-dependent)
   environments.
2. **`ddescent/evolve.py`** — population, product-rule mutation on the Dale genome (D038),
   tournament selection, spawn-parallel, provenanced.
2b. **GATE B0 — does training error reach ~0 at high |W|?** (D049) **Before Gate B.** Classical
    double descent needs the optimizer to **reach interpolation** — guaranteed for least-squares
    readouts, achieved by SGD in deep nets, **unknown for a GA on a nonlinear spiking network**. No
    interpolation ⇒ **no threshold ⇒ no peak, by construction** — and we would misread a design
    failure as a finding about biology. *(A fourth null-guarantee alongside B1–B3.)*
    **Positive control (PJM):** bolt a linear readout onto the evolved net and sweep its width —
    textbook double descent should appear. If not, the apparatus is broken, not the hypothesis.

3. **GATE A — baseline per density arm** (D030). Can an evolved network beat a trivial baseline?
   Doubles as the activity check (D037).
4. **GATE B — does a peak appear at all?** Sweep density (P: 0.1×→9.9× constraints). **Where the
   project lives or dies.** No peak ⇒ no phenomenon.
5. **THE EXPERIMENT — THREE curves on one axis** (D046/D050): generalization error ·
   **regulatory emergence** · **sloppiness** (eigenvalues of local fitness curvature).
   **Sloppiness is Bartlett's condition, and it is a RIVAL mechanism with independent support** —
   biological networks are famously sloppy (Gutenkunst), so noise-hiding may be *better* satisfied
   in biology than in ML, predicting a second descent **with no regulation**. More parsimonious
   than ours. Include it or the fight is not fair. *(Frank cites Gutenkunst AND benign overfitting
   and never connects them.)*

5b. **THE DISCRIMINATING SWEEP (D051):** vary the **fraction of unexplained variance that is
   LEARNABLE** — not the noise level. *All true noise* → noise-hiding only, plateaus at the noise
   floor. *All level-2 structure* → PC only, descent continues. **Mixed → both routes available;
   which does selection take?** The corner cells are tautological (PJM); **the contested cell —
   hierarchical + zero cost — is the experiment**. And: **does adding cost CAUSE the switch from
   hiding to reading?**
   *Prediction against the ML taxonomy:* **"tempered overfitting" is what noise-hiding looks like
   when the noise is secretly structured** — stuck at the context-average. **PC breaks the temper.** Coincidence ⇒ same process, two
   descriptions. Second descent without regulation ⇒ our framing dies cleanly. Regulation without
   second descent ⇒ both accounts need work.
6. **The discriminating prediction (D044):** the peak tracks **r₁** (environment rank), **not n**
   (number of environments). Vary independently; see which moves it. *This is not double descent
   as ML understands it.*

## SEARCH BEFORE BUILDING (standing rule; 5 prior hits)

- **Is the H-E feedback loop predictive coding rediscovered?** Higher levels modelling lower
  levels' statistics and feeding back = **Rao & Ballard / Friston**. The *architecture* is theirs.
  **Ours would be:** it **emerges under selection at a specific parameter count**, and its
  emergence **IS** the second descent. **Check before building** (D048 problem 1).

## CONTROLS ARE GRADED SERIES (D052) — the study is a MAP, not a test

Each control is a **dial toward the conditions where the phenomenon is guaranteed**, not a pass/fail
gate. If the native SNN + selection fails to show the effect, **make it more control-ly**: add
gradient training → bolt on a linear readout → the published setup. **Where the phenomenon first
appears names its precondition.** "Optimizer was binding" vs "model class was binding" is the
question under everything we have argued about — **this answers it empirically instead of by
argument.** *Cannot produce a null we must explain away: "it needed X" IS the answer.*

**Six controls, each killing a specific alternative:** bolt-on readout (apparatus) · no-selection
drift (D021) · **Gate B0** (interpolation reached?) · **Gate A** (beats baseline?) · **all-noise
arm** (Bartlett's expectation, graded) · **all-structure + cost arm** (Ali's expectation, graded).

**The 2×2 (D050/D051):** all-noise+no-cost and all-structure+cost are **literature replications
serving as positive controls**; **mixed+no-cost is THE EXPERIMENT** (both routes available, nothing
in the design decides); mixed+cost asks **does cost cause the switch from hiding to reading?**

## Open

- **H-E's two readings (D048 problem 2):** (a) variance *rises* from encoding overflow then is
  exploited; (b) variance *always* carried context and regulation **unlocks** it. D033 hints at (a)
  but came from the retired reservoir **with no context structure**, so it cannot bear on this.
  **Predict (b); measure whether (a) adds.**
- **Regulatory measurement (D040):** potent/null **screen** → functional contribution **filter** →
  **gain-vs-offset** mechanism criterion. Needs the fluctuation-driven regime (D039: `noise_sigma
  = 0` and tonic bias put us where gain control is unavailable — **Gate C**).
- **Is PR the wrong measure?** Superposed features are non-orthogonal; PR measures linear
  dimensionality. Interference vs abstraction both lower PR and **PR cannot tell them apart**.
  Feature-recovery (sparse coding) may be the right instrument. Challenges D002/D016.
- **N as a gene** — needs high per-node cost (PJM). Separable: *does growing N produce a second
  descent?* needs only fixed-N arms across N (tractable now). *Would evolution grow N?* needs the
  gene.
- **Which neurons express the phenotype?** d is a niche property, fixed per arm (D037). Whether the
  network chooses *which* cells are outputs is topology, and biologically real.

## Deferred
Crossed net×task design; Protocol T; systematic related-work review (D017); E7 scaling/invariants;
H2 restatement as a w0×density interaction; "cells" → "conditions" rename.

## Standing rules (earned)
- **Search before building.** Five times a PJM-requested search overturned my reasoning: D014,
  D031, D034, D039, D043.
- **Prove the system beats a trivial baseline before interpreting any representational metric**
  (D030).
- **Check the environment permits the phenomenon before concluding it is absent** (D045).
- Log-transform heavy-tailed outcomes; treat convergence warnings as results (D028).
- Don't raise structural alarms from smoke-preset numbers (D033).
- Don't bolt on mechanisms; make the architecture capable and let selection build them (D038).
- Geometry does not imply mechanism (D040).
- Commit before `reg` runs; PR stays confirmatory, the rest exploratory (D025).
