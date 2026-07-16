# The bridge: from abstraction → hypothesis → construction → measurement

Per PJM (2026-07-17): the gaps that need closing are (a) abstraction → model-based hypothesis,
and (b) hypothesis → model, stimuli, measurements. Working the chain concretely is also where the
"why spiking?" and "what about the dynamics?" questions get answered — **not by asserting that
spiking is special, but by finding the places where the chain requires it.**

---

## LEVEL 0 — The abstraction (FRAMING §0)

> A system has **adjustable degrees of freedom**. An **optimizer** tunes them against a **finite
> sample of challenges**. When DOF exceed what the challenge requires, the optimizer's **implicit
> bias** selects solutions that capture the **generating process** rather than the samples.
> **In a dynamical substrate, capturing higher-order structure may be realizable only as
> regulation** — because making a map context-dependent requires something to *modulate* it, and
> parameters that merely add drive cannot (D046).

## LEVEL 1 — The model-based hypotheses

Each is stated in quantities the model actually produces.

| | hypothesis | measured against |
|---|---|---|
| **H-A** | Generalization error vs **P = \|W\|** has a peak at **P\*** | sweep density |
| **H-B** | **P\* is set by r₁** (the rank of the level-1 regularity), **not by n** (number of environments) | vary r₁ and n **independently** |
| **H-C** | Past P\*, error descends **only if** structure emerges that **modulates** rather than drives | regulatory fraction (D040) vs P, **same axis** |
| **H-D** | **If the network cannot reach the fluctuation-driven regime, there is no second descent** | tonic vs balanced arms |

**H-B is what distinguishes us from ML.** Standard double descent puts the peak at parameters ≈
data. We predict it at **encoding saturation**, set by the *environment's rank*. Those are
different numbers, and the experiment separates them.

**H-D is the spiking test — and it is an INTERNAL manipulation.** See Level 4.

## LEVEL 2 — Stimuli: what the environment must be

Three requirements, each forced by a hypothesis (and each a fix to a current blocker).

**(i) Level-1 map must be RANK-DEFICIENT (rank r₁ ≪ min(K,d)).**
Forced by H-B: P\* is *defined* by r₁, so r₁ must exist and be tunable. Also forced by D043: a
full-rank goal makes a waist mathematically impossible. *(Current blocker B2.)*

**(ii) The environment must be HIERARCHICAL: context selects the level-1 map.**
Within context *c*: response = f_c(E), with f_c of rank r₁. Across contexts: *which* f_c applies
varies, and the contexts themselves have structure. Forced by H-C: with a flat environment there
is nothing to level up to, extra parameters can never help, and we would reproduce R&N by
construction. *(Current blocker B3.)*

**(iii) Context must be INFERRED FROM HISTORY, not signalled.**
This is the requirement that does the most work, and it is new.
- If context arrives as an **explicit input channel**, detecting it is trivial — a switch, not
  regulation. The hypothesis would be untestable because the interesting mechanism is bypassed.
- If context must be **inferred from the recent statistics of the input stream**, the system must
  **integrate over time** and then **apply** the inference by modulating the level-1 map.
- **⇒ the environment must have TWO TIMESCALES**: fast (E fluctuates stimulus-to-stimulus) and
  slow (context drifts over many stimuli).

**This is the first place the chain requires dynamics.** Context-inference-from-history is a
temporal computation. A static input→output map cannot do it — which is precisely why R&N's φᵢ
(no internal state, no time) and Friedlander's feedforward G *could not* have found this even had
their goals been hierarchical.

## LEVEL 3 — Construction: what the model must have

| requirement | why | status |
|---|---|---|
| **W is the genome**, P = \|W\| swept by density | H-A needs P as the axis | ✅ `evonet.py` (D037) |
| **Product-rule mutation** (`mag *= N(1,σ)`) | D043: sum-rule prevents waists 94–97% of the time | ❌ **blocker B1** |
| **Dale's law, evolvable neuron sign** | regulation needs coherent inhibitory identity | ✅ D038 |
| **Intrinsic timescales** (τ_m, τ_syn, τ_r) | Level 2(iii): integrate history to infer context | ✅ inherent to LIF |
| **Reachable fluctuation-driven regime** | H-D: gain modulation requires it (D039) | ❌ **Gate C** (`noise_sigma = 0`, tonic bias) |
| **No trained readout** | selection acts on the whole network (D032/D036) | ✅ |

## LEVEL 4 — WHY SPIKING: the answer the chain produces

Not "biology chose it." Three specific places where the chain **requires** the substrate — and one
of them is a decisive internal experiment.

### 4a. Regulation-as-gain-control is a DYNAMICAL phenomenon, available for free only here

D039's literature: **shunting inhibition is subtractive on firing rates** (Holt & Koch 1997).
**Divisive gain modulation requires synaptic NOISE** — fluctuation-based conductance changes
modulate gain divisively; tonic changes are merely subtractive (Chance/Abbott/Reyes 2002; Prescott
& De Koninck 2003). And it is better described as **input-gain control when mutual inhibition
between subpopulations** is present — a **circuit-level** mechanism.

So in a **balanced, fluctuation-driven spiking network, gain modulation is AVAILABLE FOR
SELECTION TO DISCOVER** — from E/I circuit structure, with no new machinery. In a **deterministic
rate model you would have to BOLT IN multiplicative interactions** — which violates D038's
principle (*make the architecture capable; let selection build it*) and would make the result an
artifact of the experimenter's design.

**⇒ The spiking substrate is where "did evolution invent regulation?" is a real question rather
than a modelling choice.**

### 4b. H-D: the regulatory mechanism has an ON/OFF switch — inside one substrate

**This is the strongest thing we have.** The same network, same genome space, same task, run in
two dynamical regimes:

| arm | dynamics | inhibition acts | gain control | prediction |
|---|---|---|---|---|
| **tonic** | strong tonic bias, low fluctuation | **subtractive** (offset) | **unavailable** | **NO second descent** |
| **balanced** | E/I balanced, fluctuation-driven | can be **divisive** (gain) | **available** | **second descent** |

**Nothing changes but the dynamical regime.** Not the architecture, not the task, not the genome,
not the optimizer. If the second descent appears **only** in the balanced arm, we have shown that
**the second descent depends on the dynamical availability of regulation** — which no feedforward
or static-map model can even ask, because they have no such knob.

That is a **within-substrate control**, not a cross-substrate comparison. It converts "why
spiking?" from a positioning argument into an experimental manipulation.

### 4c. Timescale separation is intrinsic, not imposed

Level 2(iii) needs the system to separate a **fast** stimulus stream from a **slow** context drift.
A LIF network *has* τ_m, τ_syn, τ_r, refractoriness, and (if we allow it) adaptation — a native
hierarchy of timescales that selection can exploit or ignore. In a static map there is no time; in
a rate model, timescales must be chosen by the experimenter. **The environment's hierarchy has a
native substrate to be mapped onto.**

**Honest ledger.** 4b is the strong claim: an internal, decisive manipulation. 4a is strong but
depends on gain control actually being reachable (Gate C). 4c is real but a difference of degree —
a rate model with two time constants would do much of it. **D035's variance channel remains, but
it is now the *weakest* plank, not the argument.**

## LEVEL 5 — Measurements

**Per genome, on the same P axis:**

| quantity | how | serves |
|---|---|---|
| **P** | \|W\| = nonzero synapses | H-A axis |
| **generalization error** | response vs demanded profile, held-out (E, context) pairs | H-A, H-B |
| **baseline skill** | vs a linear readout on raw input (`baseline.py`) | D030 gate — **before any of the above means anything** |
| **regulatory fraction** | D040's three stages: potent/null **screen** → functional-contribution **filter** → **gain-vs-offset** criterion | H-C |
| **fluctuation index** | CV of membrane potential; fraction of spikes fluctuation-driven | H-D, Gate C — *which arm are we actually in?* |
| **context-inference accuracy** | can context be decoded from internal state? | is the system doing 2(iii) at all? |
| **spectrum** (top-k singular values) | D025 — every spectral metric recoverable post hoc | exploratory |

**Two curves, one axis.** H-C is tested by plotting **generalization error** and **regulatory
fraction** against **P** and asking whether the second descent and the emergence of regulation
**coincide** (D046). Three outcomes, all informative:
- **coincide** → same process, two descriptions. Contribution: the second descent's **mechanism
  and structural signature**.
- **descent without regulation** → the ML account is complete; **our framing dies cleanly**.
- **regulation without descent** → regulation does something else; both accounts need work.

## The chain, end to end

```
DOF tuned against finite challenges; past saturation, implicit bias finds the generating process
  └─ in a dynamical substrate that may be realizable ONLY as regulation            (D046)
       └─ H-A: error vs P peaks at P*
          H-B: P* set by r₁, not n                    → stimuli need rank-deficient level-1
          H-C: descent iff regulation emerges          → stimuli need hierarchy + inferred context
          H-D: no fluctuation-driven regime, no descent → THE SPIKING TEST, internal control
            └─ construction: W as genome · product mutations · Dale · reachable balanced regime
                 └─ measure: P · error · regulatory fraction · fluctuation index — ONE axis
                      └─ gate everything on baseline skill first                    (D030)
```

## What must be built (in order)

1. **B1** — product-rule mutation (two lines).
2. **B2/B3** — hierarchical, rank-deficient environments with slow context drift and fast stimuli.
3. **Gate C** — verify the balanced/fluctuation-driven regime is reachable. *Without it H-D has no
   treatment arm and 4a's mechanism is unavailable.*
4. `evolve.py`, then Gate A (baseline), Gate B (does a peak appear at all).
5. The two-curve experiment.
