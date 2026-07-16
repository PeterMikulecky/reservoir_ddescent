# Queue

Updated 2026-07-17. Claims → `DECISIONS.md`; framing → `FRAMING.md`; narrative → `LAB_NOTEBOOK.md`.

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

## BLOCKERS — fix before any run (D043/D045)

### B1. Mutation operator is wrong → switch to PRODUCT rule
`evonet.mutate()` uses **sum-rule** (`mag + N(0,σ)`). Friedlander: sum-rule **fails 94–97%** of the
time to evolve a waist. **Fix:** `mag *= N(1, σ)`. Two lines. Without this we cannot see the thing
we are looking for.

### B2. Task is FULL RANK → a bow-tie is mathematically impossible
`tasks.profile_environments` builds E→profile from a random (K×d) matrix. Full rank ⇒ no waist,
ever (rank(AB) ≤ min(rank A, rank B)). **Fix:** make the level-1 map **rank-deficient** (rank r₁ ≪
min(K,d)).

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

0. **GATE C moves UP — it is now a prerequisite, not a follow-up.** Without a reachable
   fluctuation-driven balanced regime, **H-D has no treatment arm and gain-control regulation does
   not exist in the model at all** (D039/D047). `noise_sigma = 0` + tonic bias currently put us in
   the regime where inhibition is purely subtractive.

1. **Fix B1–B3.** Product mutations; rank-deficient level-1 map; hierarchical (context-dependent)
   environments.
2. **`ddescent/evolve.py`** — population, product-rule mutation on the Dale genome (D038),
   tournament selection, spawn-parallel, provenanced.
3. **GATE A — baseline per density arm** (D030). Can an evolved network beat a trivial baseline?
   Doubles as the activity check (D037).
4. **GATE B — does a peak appear at all?** Sweep density (P: 0.1×→9.9× constraints). **Where the
   project lives or dies.** No peak ⇒ no phenomenon.
5. **THE EXPERIMENT — measure BOTH curves against the same parameter axis** (D046):
   generalization error **and** regulatory emergence. Coincidence ⇒ same process, two
   descriptions. Second descent without regulation ⇒ our framing dies cleanly. Regulation without
   second descent ⇒ both accounts need work.
6. **The discriminating prediction (D044):** the peak tracks **r₁** (environment rank), **not n**
   (number of environments). Vary independently; see which moves it. *This is not double descent
   as ML understands it.*

## Open

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
