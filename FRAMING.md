# Framing: what is Frank's claim, independent of substrate?

Per PJM (2026-07-16). The governing insight: **Frank is almost certainly thinking more
abstractly than his chosen words let on.** His vocabulary is borrowed from ML and from gene
regulation, and when we map that vocabulary onto a different substrate, *the terminology
leads us astray*. Our job is not to check whether his words apply to spiking networks — it is
to work out how a spiking substrate instantiates the **abstract process**, and to expect that
we will have to reconceive terms like "parameter" as we go.

- **H0 (default):** the process Frank describes is **substrate-independent**. The challenge is
  ours: learn the correct mapping.
- **H1 (alternative):** the mapping fails — something about spiking substrates genuinely does
  not instantiate the process.

H1 is only reachable *after* a serious attempt at H0. Declaring H1 early would just be
mistaking our own mapping errors for a property of nature. (We have already done this once:
see D030, where we concluded the model was broken when we had merely tuned it into a regime
where it ignored its input.)

---

## 1. The claim, stated without genes, synapses, or spikes

> A system has **adjustable degrees of freedom**. An **optimizer** tunes them against a
> **finite sample of challenges**. When DOF ≈ sample size, the system fits the sample exactly
> with no slack — brittle, memorizing, maximally aliased. When DOF ≫ sample size, many
> equivalent fits exist and the optimizer's **implicit bias** selects smooth ones. Therefore
> **more DOF → better generalization, past a threshold.**

Nothing here mentions a substrate. **This is the thing to test.**

## 2. The conflation at the heart of it

Frank's chain is: *more parameters → more dimensionality → better generalization*.

That silently fuses **two quantities the ML literature carefully separates**:

| | symbol | what it is |
|---|---|---|
| **Parameter count** | **P** | number of adjustable degrees of freedom. The x-axis of double descent in ML. |
| **Effective capacity** | **D** | dimensionality of what the system can actually express. Dambre's bound; the RMT `edof` that sets threshold location (D018). |

**Frank treats these as one thing. They are not.**

In a typical ML network, P and D both scale with width, so they move together and you cannot
tell which one double descent is *about*. **They are confounded by construction.**

## 3. Why a spiking substrate? — stated honestly (corrected 2026-07-16, D035)

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
