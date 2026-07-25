# Framing

> **UPDATED 2026-07-17 (D056).** The frame below supersedes all earlier ones. Prior versions were
> **adversarial** (test Frank / beat R&N / avoid Wagner). This one is **constructive**: nobody has
> to be wrong.

## 0. The frame

Classical ML, neuroAI and evolutionary theory have converged on the idea that **algorithmic
learning unites them**, and that **double descent** — first described in ML — is expected to pervade
complex adaptive systems. Neuronal networks look like an obvious participant.

**But the brain is not a deep network. And while organisms have brains, a brain is neither an
organism nor a population** conforming to classical evolutionary patterns. Brain ensembles "learn",
but the **kinds** of learning are varied, supported by varying architectures and processes. Some
architectures may show classical overfitting and double descent (**cerebellum** — a feedforward
random-expansion machine, ≈ a random-feature kernel regressor). Some may show classical encoding of
environmental regularities (**primary sensory areas**). Much of the brain is characterised instead
by **multi-specificity and extreme flexibility** — and **whether it shows these patterns is OPEN,
not settled: nobody has looked for double descent in association cortex.**

> **How does learning among the brain's networks relate to learning as described by the grand
> framework?**
> **This study maps a REPERTOIRE of learning behaviours displayed by spiking networks under varying
> constraints and stimuli.**

**Frank's insight stays intact and becomes our instrument:** *the parameter axis is where to look.*
**Double descent is not the phenomenon — it is the DIAGNOSTIC** that reveals transitions between
kinds of learning.

## 0a. The repertoire is not arbitrary — three coordinates

A map without coordinates is a catalogue. **Three factors determine which learning behaviour
obtains**, and they are our three experimental axes:

| coordinate | question | axis |
|---|---|---|
| **environment structure** | is there **exploitable higher-order structure**, or only noise? | D045/D051 — the *learnable fraction* of unexplained variance |
| **cost** | is complexity **penalized**? | `c_syn` sweep (0 = **Frank's assumed regime**) |
| **dynamical regime** | does the substrate **permit gain modulation**? | H-D — tonic vs balanced (fluctuation-driven) |

**Vary these and you can predict — and produce — each regime.**

## 0b. The distinction everything rests on (D055)

| | what it is | its job |
|---|---|---|
| **Regularization** | machinery that prevents overfitting — homeostasis, priors, dreams, weight decay, the Occam factor | **not fitting noise** |
| **Regulation** | a functional level that **modulates another level** — context-dependent gain control | **exploiting structure the encoder cannot reach** |

**There is an abundant literature on the first. The ORIGIN of the second is unexplained.**
*"The brain regularizes" says nothing about whether regulatory hierarchy emerges, or why.*

**The constructive question:** **why did regulatory hierarchy evolve?** Candidate answer:
**because encoding saturates** — past that point additional *encoding* capacity buys nothing, and
**modulating what you have is the only remaining move.**

## 0c. The tension the field has not noticed (D054)

**Frank's load-bearing premise**, in his words: *"biology tends not to penalize complexity as
strongly... Evolutionary dynamics is therefore likely to experience the full consequences of the
double descent learning curve."* **He claims the CURVE, not merely the benefit** — and you can have
the benefit without the peak (regularize → monotonic decrease; Nakkiran; **Frank's own 2025a LASSO
result**).

**That premise is contradicted on both timescales, by literatures that have not noticed each other:**
- **Lifetime:** the brain regularizes heavily — evolved priors (neonate chicks), homeostasis, E/I
  balance, **Hoel's Overfitted Brain Hypothesis** (dreams evolved to prevent overfitting).
- **Evolutionary:** **R&N** — implicit regularization emerges from the replicator equation itself
  (the Occam factor), **no external cost needed. Selection IS a regularizer.**

**Prevent overfitting and you prevent the peak — definitionally.** So: **is Frank's assumed regime
biologically reachable at all?** *That is what the `c_syn` sweep asks.*
*Also reframes **Wang & Pope (2025)**, who found SNNs "did not show a clear pattern" for double
descent: **the substrate may already be regularized** — bounded rates, thresholds, temporal sparsity.
If so, Frank's import fails **at the level of the neuron**.*

---

## 2b. Ontology: phenotype, fitness, metrics (PJM, 2026-07-16 — corrects a confusion of mine)

**The phenotype is the network's dynamic behavior in response to an environment. The behavior
itself.** Mean rate, rate vector, variance, spectrum, PR — these are **measurements of** the
phenotype, not candidates for **being** it. Asking "which summary is the phenotype?" is
malformed, like asking whether an organism's phenotype is its weight or its height.

Three things I had fused, now separate:

| | what it is | who chooses |
|---|---|---|
| **Phenotype** | the network's behavior under an environment — the thing itself | nature |
| **Fitness** | a functional of (behavior × environment). What **selection** reads. | **us — a design choice** |
| **Metrics** | other functionals of behavior. What **we** read. | us — measurement |

**This dissolves the channel tangle.** "Which channel?" was ontological-sounding and
unanswerable because it was two questions at once:
1. *Which functional does **fitness** read?* — a design decision, defensible on biological grounds.
2. *Which functional's **dimensionality** predicts generalization?* — the experiment.
D026/D027/D028 were an attempt to answer both under one label. They come apart cleanly now.

**And it opens the sharper question.** If the phenotype is behavior, then **behavior has a
dimensionality too** — not only the internal state. So "what is D?" is not merely *which
internal channel*, but **internal representation, or expressed behavior?** Frank's "regulatory
dimensionality" is ambiguous between them, and our substrate can measure both. That is a
sharper form of the P-vs-D question than §5 states.

## 2c. What survives of the task (and what was a reservoir artifact)

`tasks.anisotropic_regression` fused an **environment generator** with a **scoring rule**. They
have different fates.

**Survives — the anisotropic environment structure.** Some directions of environmental
variation well-sampled, others barely. That is Schaeffer's (2023) geometry, which **Frank
explicitly invokes**, and it is substrate-independent: a claim about what environments *are*,
not about how anything reads them.

**Dies — the scalar tanh target.** It existed only because a linear readout emits a number, so
the task had to demand a number. A reservoir artifact wearing a task's clothes. (The
novel-direction construction was already dead — D029.)

**What environments should demand instead.** Frank: *"Phenotypic responses are the outputs. The
fitness landscape mirrors the training-error surface, ranking parameters by their performance in
encountered environments."* Each environment demands a **response profile** — an expression
pattern — because that is what a phenotype is. Fitness = distance between expressed behavior and
demanded profile.
*Consequences:* (a) **D029 becomes natural** — a novel-but-related environment is a **new target
profile from the same class**, i.e. Frank's snakeness, instead of a geometric hack about
displacing along sampled axes; (b) **constraints = n_env × d**, not n_env, giving a second
independent knob on where |W| crosses the threshold — exactly what the P-vs-D design needs.

## 3. Why a spiking substrate? — stated honestly (corrected 2026-07-16, D035)

> ⚠️ **UNDER REVISION (D072, 2026-07-18).** The PR_mean/PR_var evidence in this section is
> **reservoir-era** (D028/D033: N=1000, K=20, `anisotropic_regression`, trained readout — all four
> retired by D032/§2c). Measured on `evonet` (D072): **PR_mean EXPANDS rather than compresses**
> (PR_input 5.86 → PR_mean ~7), so the compression claim below **does not transfer**; and PR_var's
> "expansion" partly tracks injected noise. §3's real claim — that PR_var *predicts* generalization
> — remains **untested on evonet** and needs generalization measured across conditions, i.e. the
> GA. **Do not cite §3's numbers as current.** The substrate justification is being rebuilt on
> evonet, not assumed from the reservoir.

**The P/D separation is NOT the reason.** An earlier draft of this document claimed the
justification for spiking was that it pulls P and D apart by ~100:1. That is true but **not
distinguishing**: *any* recurrent network with N units has ~N² adjustable weights and ~N state
variables. A **rate** network at N=100 gives the identical separation. The P/D dissociation is
a property of **recurrence**, not of spiking. It is **the question** (§5), not the reason for
the substrate.

**The real reason is something we found ourselves: D is channel-dependent.**

D028 and D033, at a *validated* operating point with K=20 inputs:
- **PR_mean ≈ 7.4** — the mean channel **compresses** 20 input dimensions into ~7.
- **PR_var ≈ 27** — the variance channel **expands** beyond the input dimension.
- **PR_var predicted generalization; PR_mean anti-predicted it** (M2 screening-off: `var`
  pr −0.626 p=0.037 with w0/density n.s.; `mean` pr **+0.230** p=0.006 with structure doing the
  predicting).

So **"the dimensionality of the representation" is not one number.** It depends on which
channel you read, and the choice **flips the sign** of the relationship to generalization.
Frank's framework has no notion of a channel — "regulatory dimensionality" is a scalar. Our
substrate forces the question *which dimensionality, measured on what?* — and answers that it
matters more than the scalar's value.

**This is intrinsic to spiking as a point process.** Irregularity is a **coding channel**, not
imposed noise. A rate network has a mean, and a variance if you *add* noise — but you put it
there. In a spiking network the irregularity **is part of the code**. That is the
substrate-specific contribution, and it is a candidate answer to "what is D?" that Frank's
vocabulary cannot express.

**Supporting reasons (weaker, stated as such):**
- Frank explicitly names **"neural wiring"**, and his opening example — rattlesnake vs.
  snakeness — is neural. A neural substrate tests what he actually said.
- D014: rate-network intuitions (ρ≈1 edge of chaos) are **inert** in our LIF model; the
  operative regime was ρ≈8. Standard heuristics do not transfer, so the substrate is not a
  cosmetic choice.

**A strategic reason, not a scientific one:** a rate GRN puts us directly on Wagner's turf
(and Frank cites Wagner). That is the out-Franking risk. Worth weighing; not evidence.

**What we give up by staying spiking:** speed; simplicity; and clean theory — **Dambre's bound
is proved for input-driven systems with fading memory, not for spiking with reset**. Our use of
it is an extrapolation and must be flagged as one.
**What we would gain by going rate:** all of the above, at the cost of the variance channel,
the neural claim, and independence from Wagner.

**Honest summary:** spiking is justified by **one real finding of our own** (channel-dependent
D, which is ours and is novel) **plus one strategic consideration**. That is a thinner case than
the P/D argument implied. It is still a case worth backing — but it should be defended on the
variance channel, not on a separation that any recurrent network provides.

## 4. The mapping table

| Abstract | ML (random features / MLP) | Frank's GRN | Evolvable spiking net (ours) |
|---|---|---|---|
| Adjustable DOF (**P**) | weights | regulatory connections | **evolvable synapses ≈ p·N²** |
| Capacity ceiling (**D_max**) | ~width | # genes G | **# neurons N** (Dambre) |
| Realized dimensionality (**D**) | `edof` of feature covariance | — | **PR of state covariance** |
| Optimizer | SGD / least squares | natural selection | **GA** |
| Sample of challenges | training set | selective history | **n environments** |
| Implicit bias | min-norm / SGD bias | mutation bias? GP-map bias? | **GA dynamics + mutation bias** |
| Test | held-out data | novel environments | **held-out environments** |

Two cells deserve attention. **"Realized dimensionality" is blank for Frank** — he has no such
measure, which is precisely why P and D stay fused in his account. And **"implicit bias" is a
question mark for him too**: in ML it is min-norm; in evolution it is presumably mutation bias
and genotype–phenotype structure, and *nobody has measured it*. That is where the neutral-space
story (Gavrilets, Wagner) meets Frank's reframing — and it is a second thing our instrument can
see.

## 5. The competing predictions — this is the experiment

The interpolation threshold sits where "DOF ≈ sample size". But **which DOF?** Three rival
hypotheses make **different, separable** predictions about where the peak in test error falls:

| hypothesis | threshold at | reading |
|---|---|---|
| **H_param** | **P ≈ n_env**, i.e. p·N² ≈ n_env | Frank's literal words: connections are the parameters |
| **H_capacity** | **N ≈ n_env** | Dambre: state variables bound what can be expressed |
| **H_realized** | **PR ≈ n_env** | our D002/D016 operationalization: effective dimensionality |

They are separable because **we have three independent knobs**:
- **p** sets P (parameter count) — evolvable
- **N** sets D_max (capacity ceiling) — an experimental arm
- **connectivity / input gain** set realized PR — partly evolvable

**A concrete design.** Fix N=100, n_env=50. Then D_max = 100 = 2× n_env, held constant.
Sweep p from 0.005 to 0.5: P moves from ~50 (≈ n_env, i.e. at threshold) to ~5,000 (100× over).
- If a double-descent peak appears as p crosses ~0.005 → **H_param**.
- If no peak appears (because D_max already exceeds n_env) → **H_capacity**.
- If the peak tracks measured PR rather than either → **H_realized**.

Varying N across arms then tests H_capacity directly.

**Note the scale inversion.** N ≈ 100, not 1000. The reservoir needed a large random feature
pool; an evolvable network with no trained readout does not. Small networks, fast simulation,
and the threshold crossings land inside a natural density range.

## 6. What this implies for the model

1. **W is the genome.** Frank's parameters are the regulatory connections; in a reservoir they
   are frozen architecture. This single change is what makes the model able to answer the
   question. (Does not require abandoning spiking — see D032.)
2. **No trained readout.** Designate input and output neurons; the phenotype is the output
   neurons' response; selection acts on the whole network. This dissolves the entire
   D026/D027/D028 tangle about which channel fitness should read, because there is no separate
   learned component to disagree about.
3. **Density is Frank's x-axis, literally.** P = p·N². Sweeping p sweeps parameter count across
   n_env. **This is Figure 1 with regulatory connections on the x-axis** — the thing the
   reservoir structurally could not provide.
4. **Measure P, D_max and PR separately, always.** The whole point is that they dissociate.
5. **Keep the baseline gate (D030).** An evolved network must beat a trivial baseline before
   any dimensionality claim means anything. That rule was expensive; it comes with us.

## 7. What this project is, in one sentence

**An evolvable spiking network used as an instrument to disambiguate what "overparameterization"
means in an evolving system** — because the substrate separates two quantities that Frank's
theory (and the ML literature it borrows from) leave fused.

H0 says the abstract process is substrate-independent and the work is finding the mapping.
H1 — that spiking genuinely fails to instantiate it — is the fallback, reachable only after H0
is honestly attempted.


# Task design for the double-descent test: the two-failure-mode frame and task-fit criteria

**2026-07-25 · design rationale · assembled after SELECTABILITY S1 (trial_xor refuted as unselectable, HYPOTHESIS_LOG) and two independent outside-view task critiques. This is design VOCABULARY prepared in advance, NOT a task decision — the task fork is gated on the all-neuron go/no-go.**

*(Format inferred — I don't have FRAMING.md in front of me; conform to house style.)*

## The two-failure-mode frame

An error-vs-P (equivalently fitness-vs-P) curve comes back FLAT for two OPPOSITE reasons, and the curve
alone cannot tell them apart. Both have now been observed or named in this project:

- **TOO HARD — no gen-0 gradient → unselectable.** If random genomes sit at chance BY CONSTRUCTION
  (arbitrary binding: the trial_xor XOR target has no statistic a random-start gradient can climb),
  selection never moves and error-vs-P is flat-at-chance for every P. This is the mode the 2026-07-25
  reliability investigation refuted the current task into (SELECTABILITY S1; DECISIONS D124): a
  well-powered 40-generation run did not climb, on any readout basis or delay, with or without
  development.
- **TOO SIMPLE — P_crit too low → no interpolation peak.** If the task is solved at trivially low P
  (a 50-neuron reservoir can solve 2-cue fixed-delay maintenance at perhaps P ~ 50–100 synapses), the
  curve is a smooth first descent that plateaus, with the interpolation peak — if any — sitting BELOW
  the operational P range. Also flat, opposite cause. (Named by the second outside view; the standing
  risk for any DMTS-family replacement.)

**Good task design threads BETWEEN these:** hard enough to have a gen-0 gradient AND to push P_crit into
the operational synapse range (~100–1500 active synapses), yet simple enough to stay selectable. The two
failure modes are the guard rails; the target is the corridor between them.

## The premise this project must NOT assume

Both the ML double-descent literature and the outside advisors reason as though P_crit EXISTS somewhere
on the axis and the only question is WHERE it lands (too-low-boring vs mid-range-interesting). For this
project that is exactly the driving question's "does the network show the signature — a peak — AT ALL?"
Whether the interpolation phenomenology transfers to EVOLUTIONARY search (selection is like SGD but is
not SGD — Frank is careful about this) with a DEVELOPMENTAL contraction sitting between dialed-P and
effective-P (D104's P_dev) is UNTESTED. D104 showed the global-density sweeps came back flat but
attributed it to varying the wrong P (P_total, which smears the peak); whether varying the RIGHT P
(P_dev) produces a peak at all, under evolution+development, is the prior, unconfirmed question.
**Designing a task to POSITION a peak (e.g. "DMTS Plus tuned so P_crit lands mid-range") is premature
until a peak has been OBSERVED on some selectable task.** Establish that the paradigm produces
interpolation peaks before dimensioning a task around placing one.

## Task-fit criteria for the machinery we have built (N=50 / develop / assay / GA)

A task is a good challenge for THIS substrate if it:
1. **Has a gen-0 gradient** — dynamics-native rewards (timing, maintenance, sequence order, rhythm) that a
   generic E/I reservoir is already partway toward; NOT arbitrary lookup-table associations, which are the
   trial_xor failure and which unsupervised development provably cannot build.
2. **Is not trivially solved at low P** — enough effective task dimension that P_crit plausibly lands
   inside the operational range, so capacity actually binds somewhere you can measure.
3. **Stays inside the built machinery** — cue→segment→readout trial structure, single-lifetime
   development, the D095 readout, `trial_evaluate`/`_fitness` scoring, the delay axis already swept. A
   closed-loop controller (cart-pole, phototaxis) would mean building an environment simulator + motor
   interface — a much larger commitment than a task swap.
4. **Exercises the hypotheses' phenomena** — maintenance across a delay (H-D), and representational
   structure that is FORCED to distribute or cluster (the localization thread / provisional H-E).

## Candidate menu (ranked by machinery cost + directness of hypothesis test), IF a task change is forced

- **DMTS (match / non-match)** — the minimal edit: swaps the arbitrary XOR binding for a NATURAL relation
  (is the probe the same as the held cue?). Same segments, same delay, same readout; only the target
  changes. Directly tests "was arbitrary binding the specific killer?" and restores a gen-0 gradient with
  almost no new machinery.
- **Variable-delay DMTS** — H-D-native: uniformly sampled delays force a stable line attractor rather than
  a fixed-delay decay/phase-lock. You already sweep delay; this makes attractor stability across
  timescales the thing selection must build.
- **Multi-cue / interference DMTS (K ≥ 4, or a distractor in the delay)** — the localization (H-E)
  testbed: K distinct cues requiring separated sub-assemblies FORCE the representation to distribute or
  fail on interference, making "does P drive concentration → distribution" measurable rather than
  incidental.
- *(further out, larger machinery commitments: continuous-feature DMTS; closed-loop sensorimotor control.)*

## Discipline

Any task change is a **P-curve-DEFINING decision** — choose it deliberately, before seeing the P-curve,
and memorialize it (DECISIONS) with its rationale. Do NOT drift into a task because an outside view called
it "well-suited" or because a null made the current one frustrating; picking reactively off a null is the
move this discipline exists to prevent. The immediate sequence is unchanged: the all-neuron go/no-go
decides first — if the current task is selectable through a better (all-neuron) readout, the task question
may be moot and the first move is the P_dev sweep on the current task to answer the D104-open "does a peak
exist at all"; only if that is null does this menu become the live fork.

