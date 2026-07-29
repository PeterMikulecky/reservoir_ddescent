# References

Annotated bibliography. Each entry records **what it does**, **how it relates to us**, and
where relevant an **originality flag** (🔴 anticipates a planned experiment · 🟡 overlaps
partially · 🟢 supports/enables us). Append as we read; keep annotations honest — the point
is to know where we actually sit, not to build a citation pile.

Status of this file: **incomplete**. Assembled from a first targeted search (2026-07-14) on
what controls dimensionality/dynamics in spiking reservoirs. A systematic related-work
review has NOT yet been done — see "Positioning" at the bottom.

---

## Primary target

**Frank, S. A. (2026).** Generalization as the great leap in evolvability: insights from
machine learning. *Evolution*, qpag111. https://doi.org/10.1093/evolut/qpag111
— The paper the pilot responds to. Argues natural selection is a learning algorithm, that
overparameterization → generalization (double descent), and that increasing regulatory
dimensionality drove evolutionary transitions. Our E1 tests his claim H (dimensionality
*per se*, not specific circuit features, is the primary cause of generalizing capacity).
*Note:* Frank's "parameterization" is a **parameter count**; our PR is a property of the
**representation**. That mapping (D002) is an interpretive commitment, not a neutral
measurement — see Positioning.
*Stance correction (D083–D084, 2026-07-19):* Frank's parameter is explicitly the **regulatory
CONNECTION** (edge), not the node — *"regulatory connections are parameters, selection is the
learning optimizer"* — which is exactly what licenses the deep-net↔GRN↔SNN unification, and what
justifies our **P = non-zero synapse count**. His premise is **CONDITIONAL** ("systems that don't
penalize complexity experience the full double-descent curve"), so the corrected project stance is
**test the conditional at its critical case** (a neural substrate that plausibly *does* penalize
complexity, and has a within-life inner loop his examples lack) — **not "refute Frank."** See D083.

## Double descent / generalization theory (all cited by Frank)

**Belkin, M., Hsu, D., Ma, S., Mandal, S. (2019).** Reconciling modern machine-learning
practice and the classical bias-variance trade-off. *PNAS* 116(32), 15849–15854.
— The canonical double-descent paper; source of Frank's Fig. 1. 🔴 **for E0**: double
descent in random-feature models is exactly what a reservoir readout is. E0 was always a
reproduction, not a result.

**Nakkiran, P., et al. (2021).** Deep double descent: where bigger models and more data
hurt. *JSTAT* 2021(12), 124003.
— Model-size *and* epoch-wise double descent; label-noise amplification of the
interpolation peak. Basis for E3's noise prediction and E5's temporal version.

**Wilson, A. G. (2025).** Deep learning is not so mysterious or different. PMLR.
— Implicit bias / solution-volume account. Underpins E4.

**Transtrum, M. K., Hart, G. L. W., Jarvis, T. J., Whitehead, J. P. (2025).** Generalized
aliasing explains double descent and informs model design. *Phys. Rev. Research* 7(4),
043268.
— Aliasing account of the interpolation spike. Underpins E3.

**Schaeffer, R., et al. (2023).** Double descent demystified. arXiv:2303.14151.
— Variance-geometry account. Underpins E2 and the anisotropic-environment task design.

## Dimensionality ↔ connectivity (the E1 core — READ THESE FIRST)

**Litwin-Kumar, A., Harris, K. D., Axel, R., Sompolinsky, H., Abbott, L. F. (2017).**
Optimal degrees of synaptic connectivity. *Neuron* 93(5), 1153–1164.
— 🔴 **Anticipates H2.** Feedforward cerebellum-like (mixed-layer) networks. Finds
representation dimension **grows with in-degree K, peaks at an intermediate K** that
depends on N, coding level f, and the weight distribution, then **decreases above it due to
positive average correlations** among mixed-layer neurons. Ties dimension directly to
learning/error rate. This is our H2's inverted-U, published in 2017, connected to learning
performance. *Also reframes our own result:* our density sweep (p = 0.02–0.4 at N = 300 →
K ≈ 6–120) may sit almost entirely on the **descending limb** — their optimum was K ≈ 9 at
N = 1000. We likely never saw the ascending limb. **Action: sweep much lower densities.**

**Recanatesi, S., Ocker, G. K., Buice, M. A., Shea-Brown, E. (2019).** Dimensionality in
recurrent spiking networks: global trends in activity and local origins in connectivity.
*PLOS Comput Biol* 15(7), e1006446.
— 🔴🟢 The near-parallel study, and the source of the D014 fix. Uses the **same
participation-ratio** measure. Recurrent spiking (linearized Poisson/Hawkes). Findings:
(1) dimensionality is strongly regulated by local connectivity and **decreases as connection
probability p rises**, with the effect concentrated where spectral radius → 1; (2) at
**fixed p**, dimensionality varies widely by **motif arrangement** — chains, convergent and
divergent motifs *lower* dimension, while reciprocal/trace motifs can *raise* it;
(3) stimulus-driven responses can expand or contract the input's dimensionality depending on
coupling strength. Crucially they vary p **without renormalizing gain** — the methodological
point that exposed our artifact (D014). 🟢 **Their finding (2) enables our sharpest possible
E1**: SONET networks let you hold N *and* synapse count fixed while varying motif structure
to move PR.

**Clark, D. G., Abbott, L. F., Litwin-Kumar, A. (2023).** Dimension of activity in random
neural networks. *Phys. Rev. Lett.* 131(11), 118401.
— Not yet read. Theory of activity dimension in random networks. Likely directly relevant
to how PR scales with N and coupling. **Priority read.**

**Cayco-Gajic, N. A., Clopath, C., Silver, R. A. (2017).** Sparse synaptic connectivity is
required for decorrelation and pattern separation in feedforward networks. *Nat. Commun.*
8, 1116.
— 🟡 Connectivity → decorrelation → pattern separation. Same causal chain as ours
(connectivity → dimensionality → task performance), feedforward. **Priority read.**

**Williamson, R. C., et al. (2016).** Scaling properties of dimensionality reduction for
neural populations and network models. *PLOS Comput Biol* 12(12), e1005141.
— Methodological cautions on measuring dimensionality from subsampled populations.
Relevant to our PR robustness battery.

**Hu, Y., Trousdale, J., Josić, K., Shea-Brown, E. (2013/2014).** Motif statistics and spike
correlations in neuronal networks (*JSTAT* P03012); Local paths to global coherence
(*Phys. Rev. E* 89, 032802).
— The motif-cumulant machinery Recanatesi et al. build on. Needed if we manipulate motifs.

**Zhao, L., Beverlin, B., Netoff, T., Nykamp, D. (2011); Nykamp et al. (SONET).**
— SONET = random graphs with controlled second-order motif statistics. 🟢 The generator we
would need for a fixed-count, motif-varying E1.

## Reservoir computing: regimes, measures, connectivity

**Legenstein, R., Maass, W. (2007).** Edge of chaos and prediction of computational
performance for neural circuit models. *Neural Networks* 20(3), 323–334.
— Spiking microcircuits. Edge of chaos predicts *optimal* parameter values but not
performance elsewhere; proposes **kernel quality (kernel rank)** and **generalization rank**
— rank-based cousins of our PR. 🟢 Suggests a validated alternative/complementary measure to
PR, and a precedent for "dimensionality-like measure predicts computational performance."

**Büsing, L., Schrauwen, B., Legenstein, R. (2010).** Connectivity, dynamics, and memory in
reservoir computing with binary and analog neurons. *Neural Computation* 22(5), 1272–1311.
— Binary/spiking reservoirs depend strongly on connectivity structure; analog ones much
less. High kernel quality + low generalization rank is the desirable corner. Ordered regime →
low on both; chaotic → high on both.

**Maass, W., Natschläger, T., Markram, H. (2002).** Real-time computing without stable
states. *Neural Computation* 14(11), 2531–2560.
— The original LSM paper; separation and approximation properties. Background.

**Bertschinger, N., Natschläger, T. (2004).** Real-time computation at the edge of chaos in
recurrent neural networks. *Neural Computation* 16(7), 1413–1436.
— Edge-of-chaos computation in *binary* recurrent nets. Context for why the rho ≈ 1
heuristic doesn't transfer to our LIF model (D014).

**Dambre, J., Verstraeten, D., Schrauwen, B., Massar, S. (2012).** Information processing
capacity of dynamical systems. *Sci. Rep.* 2, 514.
— Task-independent capacity measure; a principled alternative to task-specific error.
**Priority read** — could strengthen our outcome measure.

## Reservoir dynamics, capacity, and the input-scaling tradeoff (searched 2026-07-16, after D030)

**Dambre, J., Verstraeten, D., Schrauwen, B., Massar, S. (2012).** Information processing
capacity of dynamical systems. *Sci. Rep.* 2, 514.
— 🔴🟢 **Two results that bear directly on the project.**
(1) **The memory–nonlinearity tradeoff**, mediated by **input scaling**. Memory-intensive
tasks favour near-linear dynamics (low input scaling: inputs map directly into distinct
states); nonlinear tasks need much larger input weights. The optimum spans **~100x** across
tasks. **This IS our D030 gain tension** — our 0.1 -> 10 finding is a rediscovery of this
curve, and our nested-tanh task being nonlinear is why high gain wins. Reassuring: the
parameter space is mapped, we were not lost in it.
(2) **Total computational capacity is bounded by the number of linearly independent state
variables, and EQUALS it under fading memory** — "the total number of linearly independent
functions of its stimuli the system can compute." **Implication for Frank: N sets the
ceiling; connectivity determines how much of the ceiling is USED, never raises it.** Our
density->PR result reframes as *connectivity wastes capacity*, not *creates dimensionality*.

**Hülser, T., et al. (2022/2023).** Deriving task specific performance from the information
processing capacity of a reservoir computer. *Nanophotonics*.
— 🔴 **The strongest prior against H1 we have found.** Demonstrates on standard benchmarks
that **total IPC correlates POORLY with task-specific performance**. What predicts performance
is the **decomposition** of capacity across basis functions, weighted by the task's actual
requirements. A single scalar dimensionality measure is precisely what this literature has
tested and found wanting. **Our D028 wobble — PR predicting in the variance channel,
anti-predicting in the mean channel — looks less like our bug and more like this phenomenon.**
*Consequence:* H1 ("PR predicts generalization") may be answering a question the field has
already answered in the negative. See D031.

**Verstraeten, D., Dambre, J., Dutoit, X., Schrauwen, B. (2010).** Memory versus non-linearity
in reservoirs. *IJCNN*. — The tradeoff's first systematic treatment.

**"Boosting reservoir computing with brain-inspired adaptive control of E-I balance"**
(arXiv:2504.12480, 2025).
— 🟢 **A concrete fix for our saturation problem.** Adaptive inhibitory control of E/I balance
improves RC performance *across* input link scaling, with the largest gains near each task's
optimum. Directly relevant: at the useful gain (~10) our network **saturates** (activity 0.935)
and PR responsiveness collapses to 6%. `ConnectivityConfig.ei_split` exists and is **unused**.
E/I balance may restore dynamic range in the regime that actually computes — i.e. it may
dissolve the D030 tension rather than force a choice.

**Jaeger, H. (2002).** Short-term memory in echo state networks. — MC <= N for i.i.d. input;
the origin of the capacity-bounded-by-N result.

## E/I structure and heterogeneity (unexplored levers for us)

**"How the layer-dependent ratio of excitatory to inhibitory cells shapes cortical coding in
balanced networks"** (2024/25 bioRxiv 2024.11.28.625852 / eLife reviewed preprint 105162).
— Measures **PR** directly in spiking networks. Finds dimensionality *increases* as
inhibition's influence grows (lower E:I ratio, stronger I→E, lower inhibitory threshold),
and that coding capacity rises with PR (r ≈ 0.85). 🟢 **A route to RAISE PR** — the opposite
direction from density. Our `ei_split` is currently unused (None).

**Perez-Nieves, N., Leung, V. C. H., Dragotti, P. L., Goodman, D. F. M. (2021).** Neural
heterogeneity promotes robust learning. *Nat. Commun.* 12, 5791.
— Heterogeneous time constants improve task performance. Another PR lever we haven't touched.

**Gast, R., et al.** Spike-threshold heterogeneity increases dimensionality of neural
dynamics (via the E/I paper above). — Not yet located precisely. **To find.**

## The nearest neighbour — and the gap that is our project (found 2026-07-17)

**Rappeport, H. & Nitzan, M. (2025).** Fitness and Overfitness: Implicit Regularization in
Evolutionary Dynamics. arXiv:2508.03187 [q-bio.PE].
— 🔴🔴 **They built our framework.** Genotypes code for **input–output maps** φᵢ (environmental
cues → phenotypes); fitness decreases with distance to a ground-truth map φ*; **complexity q =
number of tunable parameters in the environment–phenotype map**; environmental complexity
q* = complexity of φ*. That is our design, and it is Frank's mapping made formal.

**Their result is a direct threat to Frank.** **Implicit regularization emerges from the
replicator equation itself** — no external complexity cost required — and **selected complexity
converges to environmental complexity**, ⟨q∞⟩ ≈ q*. Mechanism: the **Occam factor**. Complex
classes attain the highest per-timestep fitness but collapse onto a *different* best member each
generation, so their class growth rate is suboptimal. They name this **overfitness**. Excess
complexity is **selected against**. Also: rapidly changing environments select for **lower**
complexity; simple classes enjoy a transient early advantage. Tested on linear maps,
polynomials, and 1-hidden-layer neural networks.
*If this generalises, evolution never enters the overparameterized regime and Frank's second
descent is irrelevant to biology.*

**THE GAP — and it is large.** Their linear maps are 3×3, so **q ∈ [1,9]**, against **T = 1000**
environmental cues → **q/n ≈ 0.009**. They sit **three orders of magnitude BELOW the
interpolation threshold**, entirely inside the classical regime. **Frank's claim lives at q ≈ n
and beyond. They never go there.** Their finding is not evidence against double descent; it is
evidence from a regime where double descent is not defined.
**And they have no mutation** — stated explicitly (variability is assumed preexisting). Forced,
because the replicator–Bayes isomorphism *requires* it: the analogy holds only for pure selection
in infinite populations and **breaks when mutation is introduced**. But mutation is where
evolution's implicit bias would come from.

**Positioning.** Our density knob sweeps P from 0.1× to 9.9× the constraint count — **exactly the
range R&N could not reach**. See D041.
*Risk:* we are in their slipstream (same framework, adjacent question, possibly running now).
*Note:* their NN appendix shows the same trend — **none of this requires spiking** (see D042 for
the honest case).

**Czégel, D., Zachar, I., Szathmáry, E. (2019).** Multilevel selection as Bayesian inference,
major transitions in individuality as structure learning. *R. Soc. Open Sci.* 6, 190202.
— Multilevel selection ≅ hierarchical Bayesian inference (**isomorphic**); evolutionary
transitions in individuality = **learning the structure** of the belief network. 🟢 Our
regulatory-hierarchy question, already formalised.

**Kouvaris, K., Clune, J., Kounios, L., Brede, M., Watson, R. A. (2017).** How evolution learns
to generalise. *PLOS Comput Biol* 13, e1005358.
— 🔴 **Already did "learning theory → evolvability" in 2017**: conditions that alleviate
overfitting predict which biological conditions enhance evolvability. **So Frank's novelty is
narrower than his framing implies — it is DOUBLE DESCENT specifically**, the overparameterized
regime, which Kouvaris et al. never entered.

**Harper, M. (2010).** The Replicator Equation as an Inference Dynamic. arXiv:0911.1763.
— The isomorphism everything above rests on.

## Algorithmic simplicity bias — THE ML↔evolution bridge (searched 2026-07-16). Likely our intellectual home.

**Dingle, K., Camargo, C. Q., Louis, A. A. (2018).** Input–output maps are strongly biased
towards simple outputs. *Nature Communications* 9, 761.
— 🔴🟢 The probability that a randomly sampled input produces output *x* decays exponentially
with its approximate Kolmogorov complexity: **P(x) ≲ 2^(−aK̃(x)−b)**, with a and b predictable
from minimal knowledge of the map. Demonstrated for RNA secondary structure, coupled ODEs, and
a financial model; later shown for **gene-regulatory network concentration profiles**, protein
quaternary structures, and biomorphs.

**Valle-Pérez, G., Camargo, C. Q., Louis, A. A.** Deep learning generalizes because the
parameter-function map is biased towards simple functions. arXiv:1805.08522.
— 🔴 **Same group, the other end of the bridge.** Applies the Dingle et al. simplicity-bias
framework to neural networks: deep learning generalizes *because* the parameter-function map is
biased toward simple functions.

**Johnston, I. G., Dingle, K., Greenbury, S. F., Camargo, C. Q., Doye, J. P. K., Ahnert, S. E.,
Louis, A. A. (2022).** Symmetry and simplicity spontaneously emerge from the algorithmic nature
of evolution. *PNAS* 119, e2113883119.

**Greenbury, S. F., Louis, A. A., Ahnert, S. E. (2022).** The structure of genotype-phenotype
maps makes fitness landscapes navigable. *Nature Ecology & Evolution* 6, 1742.
**Greenbury, S. F., Schaper, S., Ahnert, S. E., Louis, A. A. (2016).** Genetic correlations
greatly increase mutational robustness and can both reduce and enhance evolvability.
*PLOS Comput Biol* 12, e1004773.

### Why this matters to us — a killed hypothesis

**The "does selection have an implicit bias?" question is ANSWERED, and against my framing.**
I argued that Frank imports double descent from ML while never checking that selection has the
implicit smoothness bias the second descent depends on — "nobody knows." **Wrong.** The Louis
group has shown simplicity bias holds in GP maps *and* in the parameter-function map of neural
networks, by the same algorithmic-information argument. And **Frank's Wilson citation — "simple
solutions occupy larger regions of parameter space, and learning dynamics are more likely to
find big regions than small ones" — IS the volume argument** this framework formalizes. His
assumption is not unexamined; it is supported.
*Consequence:* **do not build the project around implicit bias** (D034).

**What survives, and is better positioned.** The Louis group works in **genotype space**:
parameter count and *phenotype complexity* (Kolmogorov). They do **not** measure **effective
dimensionality** — capacity, PR, Dambre's bound. Their axis is output complexity; ours is
representational dimensionality. **Orthogonal.** `FRAMING.md`'s P-vs-D question stands.

**Positioning.** This is the real ML↔evolution bridge literature — more so than neuroevolution
engineering (NeuEvo, ELSM: benchmark accuracy) or spiking dimensionality (Recanatesi,
Litwin-Kumar: no selection). It is where Frank's argument actually lives and where a paper on
"what does overparameterization mean in an evolving system" would be read.

**A live connection, and a trap.** Simplicity bias implies *more parameters → larger neutral
sets for simple phenotypes → stronger bias toward simplicity* — a **mechanism** for Frank's
"more parameters → better generalization", and testable. But it is squarely the Louis group's
turf: pursuing it directly is the out-Franking trap in a new costume.

## Evolvability / evolutionary framing (Frank's lineage)

**Kouvaris, K., Clune, J., Kounios, L., Brede, M., Watson, R. A. (2017).** How evolution
learns to generalise. *PLOS Comput Biol* 13(4), e1005358.
**Parter, M., Kashtan, N., Alon, U. (2008).** Facilitated variation. *PLOS Comput Biol*
4(11), e1000206.
**Watson, R. A., Szathmáry, E. (2016).** How can evolution learn? *TREE* 31(2), 147–157.
**Xue, B. K., Sartori, P., Leibler, S. (2019).** Environment-to-phenotype mapping.
*PNAS* 116(28), 13847–13855.
**Gavrilets, S. (2004).** *Fitness landscapes and the origin of species.* PUP.
— Frank's evolutionary scaffolding. 🟢 The framing space where our contribution most
plausibly lives, and the least crowded part of the landscape.

## Development / within-life plasticity — the genotype≠phenotype inner loop (searched 2026-07-19, D083)

*Context: D082's flat Gate A + the population-genetics argument (genome→development→phenotype→fitness)
motivated adding a within-life plasticity phase before scoring. These ground the design.*

### Plasticity stability / convergence — the D083-step-2 fork (D085 question a — ANSWERED)

**🔴🟢 DIRECTLY CHANGES THE BUILD.** The naive pairing we would have reached for first —
**Hebbian + slow homeostatic synaptic scaling — is KNOWN NOT TO CONVERGE.** It oscillates or runs
away: the "temporal paradox."

**Zenke, F., Gerstner, W. (2017).** Hebbian plasticity requires compensatory processes on multiple
timescales. *Phil. Trans. R. Soc. B* 372, 20160259. — 🔴🟢 The load-bearing reference. Hebbian is fast
(seconds), homeostatic scaling slow (hours–days); the **separation of timescales causes instability** —
models using homeostatic scaling to stabilize Hebbian had to speed homeostasis to orders of magnitude
faster than experiment to get stability. **Stability requires RAPID compensatory processes on the SAME
timescale as the Hebbian term.** Their triplet-STDP + heterosynaptic-term model DOES converge to stable
weights.
**Zenke & Gerstner (2017), "The temporal paradox of Hebbian learning and homeostatic plasticity"**
(*Curr. Opin. Neurobiol.*; bioRxiv 116400) — the paradox and its candidate resolutions.
**Heterosynaptic plasticity as stabilizer** (PMC4500102, models+experiments): changes at NON-active
synapses, same timescale as Hebbian, "robustly provide stability and competition."
**Classic convergent rules:** Oja's rule, BCM — stabilization built INTO the rule (postsynaptic-
activity-driven), not a separate slow process.

**⇒ D083 DIRECTIVE (the action, per D085 scope):** do NOT use naive Hebbian + slow synaptic scaling.
Use fast, co-timescale stabilization — **Oja / BCM / Hebbian-with-heterosynaptic-term.** Convergence
(the "develop-to-maturity" definition, D083 sub-decision 3) is then AVAILABLE but is a property of the
RULE CHOICE, not automatic — the bookend controls double as a check that the chosen rule actually
converges on our networks. *The prune-not-replant payoff: the obvious implementation would not have
converged.*

### The chosen rule — Vogels-Sprekeler inhibitory plasticity (D086/D087; empirically forced 2026-07-19)

**🔴🟢🟢 THE RULE WE ARE ACTUALLY BUILDING.** Naive Oja was tried first and **blew up empirically** —
one-step runaway to NaN on the recurrent spiking substrate (activity 1.39 → NaN by epoch 2; the
standard recurrent-Hebbian positive-feedback instability the literature documents universally). Oja's
`-y²W` stabilizer is a FEEDFORWARD normalizer; applied to a recurrent matrix with rates ~1.4 it is
outside its stability regime. **Lesson (D086): do not hand-roll plasticity numerics — adopt a
published, tested implementation with known constants.**

**Vogels, T. P., Sprekeler, H., Zenke, F., Clopath, C., Gerstner, W. (2011).** Inhibitory plasticity
balances excitation and inhibition in sensory pathways and memory networks. *Science* 334(6062),
1569–1573. doi:10.1126/science.1211095. — 🔴🟢🟢 **The canonical inhibitory synaptic plasticity rule,
and our development stabilizer.** Plasticity on I→E synapses tunes inhibition to a target postsynaptic
rate (setpoint `alpha`), establishing/maintaining E/I balance in an experience-dependent way. The
built-in target-rate setpoint IS the co-timescale homeostatic stabilizer the Zenke/Gerstner result says
recurrent Hebbian learning requires. **OFFICIAL TESTED IMPLEMENTATIONS EXIST — adapt these, do not
re-derive:** Brian2 docs `examples/frompapers.Vogels_et_al_2011` (≈6-line event-driven synapse rule,
maintained across Brian2 versions); ModelDB 143751 (implemented by Zenke & Vogels themselves). Runs
INSIDE `net.run()` — eliminates the Python-side weight write-back that caused half the Oja trouble
(development = "turn eta on, run, turn off"). The rule's weight-update logic attaches to our
current-based synapse (its conductance formulation is not required). **Fits our substrate like a glove:
we already have an inhibitory population and E/I balance is already a precondition (D075); D084's
interneuron gene later differentiates this same inhibitory plasticity by subtype.**

**⇒ D087 BUILD: Vogels-inhibitory (stabilizer) FIRST, then a tested excitatory STDP/Hebbian rule
(learner) on top.** Inhibitory plasticity = stability; excitatory = learning; the standard picture
needs both (Oja failed trying to learn without stabilizing). P handled by MEASURING effective-P at
analysis, not by constraining development (D087) — so development runs unconstrained (only a
not-exactly-zero numerical guard).

### The MISSING HALF — eSTDP (learning) + competition (selectivity) (searched 2026-07-21, D103)

The flat pilot (state carries no task-usable info, G3) traced to development having ONLY its stabilizer
(Vogels) and neither the LEARNING engine nor the COMPETITION that build stimulus-selective
representation. The search confirmed PJM's two-part development model and expanded it to the standard
**trinity — Hebbian learning + competition + stability**. Rules/architectures to adopt (tested, NOT
hand-rolled — the temporal-paradox blowup risk, Zenke/Gerstner above, makes this non-negotiable; Oja
lesson D086):

**Srinivasa, N., Cho, Y. (2014).** Unsupervised discrimination of patterns in spiking neural networks
with excitatory and inhibitory synaptic plasticity. *Front. Comput. Neurosci.* 8:159.
https://doi.org/10.3389/fncom.2014.00159 — **the closest reference architecture to ours:** source
neurons → an E/I reservoir (generic cortical layer) → a readout/sink layer, STDP on all E and I
synapses. States the division of labour exactly: **long-term eSTDP learns the salient input features
(sparse, efficient); iSTDP makes that learning stable via per-neuron E/I balance.** ⇒ our Vogels rule
is the STABILIZER FOR eSTDP, not standalone development — we built the safety mechanism without the
engine. *(pin when we adopt the rule form.)*

**Diehl, P. U., Cook, M. (2015).** Unsupervised learning of digit recognition using spike-timing-
dependent plasticity. *Front. Comput. Neurosci.* 9:99. — canonical eSTDP + WTA-lateral-inhibition
reservoir (MNIST). A tested eSTDP+competition recipe to borrow rule-forms from. *(pin when adopted.)*

**Competition / selectivity via lateral inhibition (PJM's intuition — CONFIRMED):** PV vs SOM
interneurons run DIFFERENT plasticity with DIFFERENT roles — **PV mediates homeostasis in excitatory
rate (Vogels-like); SOM builds LATERAL inhibition providing COMPETITION between excitatory assemblies**
(Lagzi et al., cited in the modularity-iSTDP paper, arXiv:2405.18587). Dual-STDP (Biomimetics 2025,
doi:10.3390/biomimetics11070462): **FS-mediated lateral inhibition → winner-take-all competition →
heterogeneous E→E differentiation** (forces neurons to become selective for DIFFERENT features; without
it eSTDP collapses / LTD-bias washes out structure). ⇒ Vogels (global rate) and lateral-competition
(selectivity) are DISTINCT mechanisms; we have the first, not the second — but competition may emerge
through our EXISTING inhibitory structure once excitatory synapses can learn (test eSTDP alone first).

**Excitatory STDP self-organizes stimulus-selective structure** (Biomimetics 2025 above; Representation
Learning using event-based STDP, arXiv:1706.06699; unsupervised feature-learning SNNs, arXiv:1904.06269)
— the Hebbian competitive rule that strengthens input-correlated pathways and builds selectivity. This
is the missing engine (D103). Add as a GENERAL rule, let selectivity emerge from stimulus statistics —
do NOT hand-wire features (D038/D074).

### Develop-then-select — this IS the Baldwin effect (D085 question b — ANSWERED, and it reframes D082)

**🔴🟢 THE RICHEST FINDING OF THE REVIEW.** The D083 structure — GA at genotype level + a within-life
learning phase modifying the phenotype before fitness, learned changes NOT inherited — is exactly the
**Baldwin effect**, a named 40-year-studied framework. We instantiate a known nested loop, not a new
one.

**Hinton, G. E., Nowlan, S. J. (1987).** How learning can guide evolution. *Complex Systems* 1,
495–502. — 🔴🟢🟢 The founding instance, and it **recasts D082's flat Gate A.** Their demonstration was
a **"needle-in-a-haystack" landscape — one high-fitness spike, NO gradient, where evolution alone is
ineffective.** Result: **learning smooths the landscape, creating a basin of attraction pure selection
cannot find** — "learning gives value to a partial, otherwise useless, subset of the required genes."
**Our flat Gate A IS a needle-in-a-haystack. The Baldwin literature says that is PRECISELY where a
within-life learning phase has its largest documented effect.** ⇒ theoretical support that D083 will
*work*, not just that it is faithful — development is the textbook fix for exactly D082's failure mode.

**CAVEAT (RESOLVED after PJM).** The inner loop being UNSUPERVISED (blind to Y) is not a defect — it
is how biology works: real within-life learning is unsupervised; the system is supervised AT THE OUTER
LOOP (selection retains genomes whose blind-learning machinery yields fitness-relevant structure). The
Baldwin guarantee needs only that the inner loop's product VARIES fitness-relevantly across genomes so
selection has variance to grade — which unsupervised development satisfies. And the fitness apparatus
is NOT level-2-blind: Y = tanh(E @ Q @ Wc) is context-dependent; the memoryless-floor↔oracle-ceiling
gap is exactly the level-2 reward region. **The real open question is not supervision but the DIVISION
OF LABOR between loops:** development-alone builds context-inference (regulation is developmental, H-C
weakened) vs selection-finds-it (regulation is selected, H-C supported). Both are "evolution shapes
circuitry"; which is the result — **measured by sample-and-develop vs full-GA, the reason sampling is a
needed CONTROL for H-C.**

**Baldwinian vs Lamarckian (fork to name).** Ours is strictly **Baldwinian** — learned strengths tune
the phenotype, are NOT written to the genome, discarded each generation; only birth topology+weights
inherited. Keeps P clean, matches biology. Lamarckian is often faster in EC (someone will ask) — we
decline it for faithfulness to Frank's genotype→phenotype→fitness structure. *(Refs:
arXiv:2605.28703 Lamarckian-vs-Baldwin; Ackley & Littman 1991; Bull 1999 on learning rate/amount;
LaSER arXiv:2505.17309.)*

**Watson & Szathmáry (2016); Kouvaris et al. (2017)** *(cited below under Evolvability)* — the
evolution-as-learning lineage connecting Baldwin to Frank. 🟡 Relevant to the overall stance and H-C;
per D085 **noted, not acted on now.**

**[Sample-complexity / generalization scaling — required exposure vs task complexity, not parameter
count]** *(citations to be pinned when leaned on — flagged in D083.)* Candidates: **Favero et al.**
and the **diffusion-model generalization-then-memorization timing** work (2025); the classic **XOR
sample-complexity** result. — 🟢 **Grounds D083's development-duration rule:** the modern
overparameterized-generalization literature finds required exposure scales with **task complexity**,
roughly independent of (or decreasing in) parameter count. So developmental duration T should scale
with task structure (r₁, context-dwell), held **constant across the P-sweep** — which independently
matches our own H-B (the relevant scale is r₁, not P or n). Also: over-exposure → **memorization
onset** = epoch-wise double descent on the *time* axis (ties to Nakkiran, D077) — a principled reason
to expect a developmental *window*, not a monotone "more is better."

### Fitness-distribution summary statistic (D085 question c — ANSWERED: don't default to the mean)

**🟢🔴 Bears on D083 sub-decisions 1 AND 2.**
**Kaznatcheev, A. "Fitness distributions versus fitness as a summary statistic" (algorithmic
Darwinism; egtheory 2019, after Valiant & Xue et al.).** — 🔴 Our sub-decision 1 is a named topic.
Key: with **stochastic fitness** (ours — noisy development, sampled environments), reducing to a single
summary (the mean) can mislead, because **selection acts on the TAILS, not just the center** — a
higher-complexity type with a larger neutral set samples further into its tail and can win even with a
LOWER mean. Since our core question is complexity (P) × fitness, that is exactly where tail effects
live. **⇒ the mean may be the wrong reduction; track the distribution, not just its center.**
**Cavill/Watson et al. "Distributional Fitness Evaluation" (arXiv:2110.13609).** — 🔴 **Direct warning
for our probabilistic-development cost mechanism (D083 sub-decision 2).** With stochastic evaluation
the standard GA **overestimates and retains anomalously high sampled values** (noisy-fitness
overestimation bias) — scoring each genome on ONE noisy developed-fitness draw preferentially retains
LUCKY draws, not good genomes. *Distributional* evaluation (whole sampled distribution, not one draw)
achieves significantly higher TRUE fitness. **⇒ if we develop a random subset for cost (sub-decision
2), average multiple draws / use the distribution — do not select on a single draw.**
**Good, B. H., Desai, M. M. (travelling-wave / fitness-class formalism); Prügel-Bennett & Shapiro
(1994) noisy-fitness GA cumulants.** — 🟢 The principled object is the fitness distribution's
**cumulants** (mean = 1st, variance = 2nd); a Gram-Charlier expansion around Gaussian parameterizes it
if near-normal. **⇒ D083 directive: collect the developed-fitness distribution; base hypotheses on
mean AND variance (at least), with an explicit check on whether tail/variance effects matter — not the
mean alone.** *(Confirms PJM's "collect many, base hypotheses on one" — but the "one" is probably
mean+variance, not mean.)*

**Brunel, N., Wang, X.-J. (2001); Wang, X.-J. (2002).** Probabilistic decision making by slow
reverberation in cortical circuits. *Neuron* 36, 955–968.
— 🟢 **Two loads.** (1) Slow-reverberation working memory in E/I-balanced LIF networks;
NMDA-dominated recurrent excitation, *"NMDA critical for stability."* Basis for D073/D074 (the slow
current) and for the D083 claim that **working memory is achievable with plain LIF units at
large-enough N** — i.e. the "does memory need special structure" risk is mostly an *N* question, not
a "need fancier neurons" question. (2) The **engineered-ceiling bookend** (D083 sub-decision 3): a
competent memory backbone whose *convergence time* (only) calibrates the short end of the
development-duration window. *Quarantine:* its wiring is never a template/seed/comparison — only a
convergence-time scalar.

### Engineered-ceiling circuit basis — the Wang/Compte/Brunel attractor lineage (searched 2026-07-19, D092)

*Context: the engineered ceiling (D088/D092 known-positive control) is a hand-wired winner-take-all
context-memory attractor. Its architecture is the canonical Wang-lineage working-memory circuit, run in
OUR substrate (EvoNet at high nmda_frac). These are the sources the ceiling is built from. Quarantine
(D083/D092): the ceiling is a measurement-instrument calibration / convergence-time bracket — NEVER a
template/seed/comparison for evolved networks.*

**Compte, A., Brunel, N., Goldman-Rakic, P. S., Wang, X.-J. (2000).** Synaptic mechanisms and network
dynamics underlying spatial working memory in a cortical network model. *Cerebral Cortex* 10, 910–923.
— 🔴🟢🟢 **The canonical WM attractor and the ceiling's direct basis.** Context-selective excitatory
pools with strong within-pool recurrence sustain persistent activity (the memory); shared feedback
inhibition enforces winner-take-all. Persistent activity survives the delay and is NMDA/slow-current
dependent — **exactly our D074/D075 slow-excitation + fast-inhibition config.** Our ceiling is this
circuit at N=50 (2 clusters + inhib pool). *(Confirm page/vol when pinned.)*

**Brunel, N., Wang, X.-J. (2001).** Effects of neuromodulation in a cortical network model of object
working memory dominated by recurrent inhibition. *J. Comput. Neurosci.* 11, 63–85.
— 🟢 Object-WM attractor; the recurrent-inhibition-dominated regime. Part of the same lineage; informs
the winner-take-all inhibitory pool strength (w_inh) in the ceiling.

**Wang, X.-J. (2002).** Probabilistic decision making by slow reverberation in cortical circuits.
*Neuron* 36, 955–968.
— 🟢 The slow-reverberation-attractor mechanism: **slow recurrent excitation balanced by fast feedback
inhibition** instantiates attractor states. This IS the mechanism our slow current (D074) supplies; the
Wang-search's clearest statement of why the ceiling needs high nmda_frac (slow reverberation sustains
the attractor). *(NB: this Neuron 36 ref is also cited above under plasticity — same lineage.)*

**Ardid, S., Wang, X.-J. (2013).** A tweaking principle for executive control: neuronal circuit
mechanism for rule-based task switching and conflict resolution. *J. Neurosci.* 33, 19504–19517.
— 🟡🟢 The **context-gating / rule-switching** circuit: held context modulates which stimulus→response
mapping is active. This is the REGULATION half of the ceiling (the held cluster gates the probe
response) — the D091 inferential-regulation signature (identical probe, context-dependent output).
*(Pin when the regulation-half of the ceiling is built.)*

**Empirical note (D092):** random undeveloped nets do NOT carry context, because slow current only
yields persistent memory when wired into an attractor TOPOLOGY (context-selective clusters); random
connectivity lacks it. The ceiling supplies the topology → verified carry (cue selects matching cluster,
persists+decays through silence: selectivity 4.32→1.57 over 100–600 ms). **The carry measure is
validated by DECAY-ACROSS-DELAY: real memory decays; the random-net confound stayed flat (~3.3–3.5).**

## Regional gradient — cerebellum (anchored) → sensory (open) → association (ours) (searched 2026-07-19)

*Context: our framing orders DD-propensity cerebellum > primary sensory > association. Do the ends
already exist in the literature? Cerebellum: YES (as expansion-coding, not "double descent"). V1: NO.
This bounds our onus — cite the cerebellum end, study the association end. NB: cerebellum is
feedforward, OUTSIDE our recurrent apparatus's range — it anchors the CONCEPTUAL gradient, not our
instrument's reach.*

**Xie, M., et al. (2023).** Task-dependent optimal representations for cerebellar learning.
*eLife* 12, e82914.
— 🟢 The modern statement of the cerebellar expansion–generalization tradeoff. Low coding level
raises granule-cell representation dimension & generalization, but too sparse hurts — a peak/tradeoff
curve. **This is the double-descent phenomenon in the cerebellum, in Marr-Albus vocabulary rather than
Belkin's.** Anchors the "easy end" of our regional gradient. *(Litwin-Kumar 2017 and Cayco-Gajic 2017,
already cited above under E1, are part of this same lineage — the cerebellum end is thoroughly
established.)*

**Sanger, T. D., Yamashita, O., Kawato, M. (2020).** Expansion coding and computation in the
cerebellum: 50 years after Marr–Albus. *J. Physiol.* 598, 913–928.
— Review extending Marr-Albus to continuous (non-Boolean) functions. Cite for "cerebellar
expansion-coding is settled theory."

**[Allen Institute large-scale V1 models — Billeh et al.; the gradient-trained V1 variant.]**
*(pin exact citations when leaned on.)*
— 🔴 **The open middle.** Sophisticated, data-constrained, sometimes gradient-trained V1 models exist
— but **no double-descent analysis has been run on them.** They study efficient coding / robustness /
receptive fields. So the DD diagnostic is unopened even where the substrate is most built-out — which
*strengthens* our contribution rather than threatening it (deck A9).

*Note:* our **positive control (random-feature readout) is essentially a Marr-Albus expansion model in
disguise** — verify before leaning on it, but it may mean we already instantiate the cerebellum anchor.

## Cortical interneuron gradient — the D084 hierarchy gene (backgrounds compiled 2026-07-19)

*Context: PV/SST/VIP proportions shift monotonically sensory→association along a 1-D trajectory
(T1w/T2w myelin gradient). This is the empirical basis for D084's single scalar "hierarchy-position"
gene, from which both PV/(PV+SST) and the disinhibitory index VIP/(PV+SST) fall out. Primary citations
below are TO BE PINNED — currently held as compiled background, flagged honestly.*

**[Interneuron subclass proportions across the cortical hierarchy.]** *(primary citation TBD — a
transcriptomic atlas + a hierarchy-gradient paper.)*
— 🟢🔴 ~85–90% of cortical GABAergic cells are three non-overlapping classes (PV, SST, VIP). Their
composition traces a **1-D trajectory** through the simplex: PV-dominant at sensory poles (fast
perisomatic gating, gamma), SST/VIP-elevated at association poles (disinhibitory gating, persistent
activity, beta). **Enables D084's key economy: ONE bounded scalar gene, not three free proportions.**

**[VIP→SST→pyramidal disinhibitory motif.]** *(pin canonical reference — likely Pi et al. 2013,
Pfeffer et al. 2013 — CONFIRM.)*
— 🔴 The motif that expands toward association cortex; enables top-down gating and sustained recurrent
activity. **A candidate biological instantiation of exactly the "regulation" (a level modulating
another level) H-C predicts should emerge (D055/D084).** *Must be a CAPABILITY, not installed (D074
rule) — providing the cell types ≠ wiring the loop.*

**[Allen Human Brain Atlas / macaque transcriptomic atlases — primate CR/CB substitution for VIP.]**
— For calibrating the h→composition map to primate data (VIP↔CR, SST↔CB). D084 watch-out 3: state
which species' gradient the trajectory is calibrated to.

**Carandini, M., Heeger, D. J. (2012).** Normalization as a canonical neural computation.
*Nat. Rev. Neurosci.* 13, 51–62. *(confirm — held from background.)*
— 🟢 The canonical divisive-normalization / gain-control computation; the functional target of
"regulation." Relevant to both H-C and the PV-mediated gain control at the sensory pole.

---

## Positioning: where does our study actually sit?

**Honest first pass (2026-07-14).** The individual causal links we planned to test are
substantially established:

| Planned | Status in the literature |
|---|---|
| E0: readout double descent | 🔴 Established — random-feature double descent (Belkin 2019) |
| E1: density → dimensionality | 🔴 Established — Litwin-Kumar 2017 (feedforward, inverted-U), Recanatesi 2019 (recurrent spiking, decreasing) |
| dimensionality → task performance | 🔴 Established — Litwin-Kumar 2017; Cayco-Gajic 2017; Legenstein & Maass 2007 |
| E2/E3/E4 mechanisms | 🔴 Established — Schaeffer 2023, Transtrum 2025, Wilson 2025 (all cited *by Frank*) |
| Double descent in a spiking reservoir | 🟡 Not found directly, but a reservoir readout *is* a random-feature model, so likely a substrate change rather than a new phenomenon |

**What may still be genuinely open:**

1. **A true count/dimensionality dissociation.** Litwin-Kumar and Recanatesi both vary
   connectivity, which moves parameter count *and* dimensionality together. Recanatesi's
   finding that dimensionality varies widely **at fixed p** by motif arrangement opens a
   design nobody in what we've found has run: **hold N *and* synapse count fixed, vary only
   motif structure to move PR, then test whether generalization tracks PR.** That isolates
   dimensionality from parameter count — and it is a *sharp* test of Frank's claim H, because
   it directly pits "dimensionality per se" against "specific circuit features" (motifs are
   circuit features). Either outcome is informative.
2. **H5 — does the interpolation threshold scale with *effective* dimensionality (PR) rather
   than nominal parameter count?** Not found in the searches so far. This is the most
   Frank-specific and least crowded of our hypotheses.
3. **The evolutionary framing and the comparative ladder (E7).** Porting a common PR axis
   across the group's model systems (boolean networks, colonies, reservoirs) to test Frank's
   historical-trend claim. The framing is where the novelty most plausibly lives.

**Implication.** The pilot as originally designed is largely a re-derivation of known results
in a new substrate, wearing an evolutionary frame. That is not worthless for a group pilot —
but it is not what we said we were building. **A systematic related-work review should
precede further building**, and E1 should probably be repositioned around the fixed-count
motif dissociation (item 1) rather than the density sweep.

**Open reads (priority order):** Clark/Abbott/Litwin-Kumar 2023; Cayco-Gajic 2017;
Litwin-Kumar 2017 in full; Dambre 2012; the E/I-ratio PR paper in full.

### Jordan, Schmidt, Senn & Petrovici 2021 — "Evolving interpretable plasticity for spiking networks" (eLife 10:e66273)
E2L: evolves the plasticity RULE as a symbolic expression (Cartesian genetic programming) on a fixed
architecture — the mirror of our approach (we evolve the net, hand-design the rules). Evolve-the-rule is
out of scope for us. Mined for three transferable insights (see POST_PILOT_QUEUE E-series):
- **GA efficiency:** cache fitness for unchanged genomes (their silent-mutation caching; our analogue is
  don't re-develop unchanged elites) — E1.
- **Weight-dependent (multiplicative, soft-bound) STDP** naturally bimodalizes weights = differentiation
  we lack with additive+clip (Gütig et al. 2003 form) — E2.
- **Homeostasis as differentiator, not just stabilizer:** their evolved homeostatic terms drove weight
  DIVERGENCE (strong=signal / weak=background), explicitly beyond "maintaining a working point." Directly
  reframes our Vogels-stabilizer leg; testable hypothesis that our stabilizer may be SUPPRESSING
  differentiation — E3.
Also: task-difficulty-as-knob / evolve-on-simplified-then-transfer reinforces the curriculum thread (E5);
slow novelty-accumulator + evolutionary-hurdles as minor primitives (E4). Their cost regime (~24-48 node-
hrs/run, 10³-10⁴ sims/run) is comparable to ours, so caching is the real efficiency lever, not a magic
speedup. Their validation depends on tasks with known-optimal rules — a loop unavailable to us by design.

### Fernando, Karishma & Szathmáry 2008 — "Copying and Evolution of Neuronal Topology" (PLoS ONE 3(11):e3775)
Foundational paper of the neuronal-replicator / Darwinian-neurodynamics program. Proposes STDP + topo-
graphic maps can COPY neuronal connectivity between brain regions, enabling TRUE Darwinian evolution
(replication + heritable variation + selection) inside the brain — distinct from selectionist theories
(Edelman, Changeux), which they argue are "a population of stochastic hill-climbers" (selection WITHOUT
replication), a strictly weaker search. Key transferable findings (see POST_PILOT_QUEUE S-series):
- **Heritability is the crux + the hard part** (S1): they PROVE the process is Darwinian by plotting
  parent-vs-offspring fitness (Figs 15/16). Bare STDP copies only 2/15 motifs; needs error-correcting
  observer neurons, reverberation-limiting gating, neuromodulation, layer resetting. → test whether OUR
  develop-then-select produces HERITABLE fitness, or is merely selectionist (flat-fitness diagnosis).
- **Activity reverberation corrupts structure; sparse activation fixes it** (S2): non-local spread makes
  spurious cross-correlations (4 named failure modes); 1 Hz vs 5 Hz dramatically improves fidelity. →
  candidate mechanism for OUR funnel + third vote for the excessive-density hypothesis.
- **LTD/LTP ratio controls formed structure** (S3, Figs 7/8): an unswept knob in our eSTDP
  (estdp_Aplus/Aminus).
- **Oja + lateral-inhibition soft competition, WTA cleans up "shifts and compressions"** (S4): indep.
  arrival at our eSTDP+competition design; better vocabulary than "funnel."

### Fernando, Vasas, Szathmáry & Husbands 2011 — "Evolvable Neuronal Paths" (PLoS ONE 6(8):e23534)
Same program: neuronal PATHS (not just topology) as evolvable units — paths grow collaterals to recruit
nodes, activity spreads probabilistically along competing paths, good paths strengthened by reward. A
selection-among-paths mechanism inside the brain. Reinforces the selectionist-vs-truly-Darwinian
distinction (S5) that sharpens our three-learnings disentanglement. (Related IEEE TNN 2010
10.1109/TNN.2010.2083685 in the same cluster; not pulled — the two PLoS papers carry the core.)

**CONVERGENCE (recorded in queue):** three independent sources — PJM's pre-sweep density intuition,
E2L's weight-dependent-STDP/homeostasis-as-differentiator, and this Szathmáry reverberation/sparsity
work — now point at ONE hypothesis: too much activity/connectivity/reverberation is PREVENTING
differentiation. "Reduce activity/density, re-measure differentiation functionally" is the most-converged
post-sweep experiment.

### Loyola-Jara, Fernández-Rodríguez & Baladron 2026 — "Evolving spiking neural networks: the role of neuron models and encoding schemes in neuromorphic learning" (Front Neurosci 20:1697163)
NEAT evolving weights+topology; compares LIF vs Izhikevich across encoding schemes on classification and
RL. Izhikevich consistently outperforms LIF (one task comparable); concludes the neuron model matters as
much as the encoding scheme. **Our response (D111 extension, queue N1):** the P-axis criterion resolves
this against adopting Izhikevich — 4 parameters/neuron would be 4N fitted DOF outside the synaptic P count,
contaminating the very axis we measure. LIF's parameter-poverty is a feature. The live question becomes
landscape SMOOTHNESS (queue N2), not unit richness.

### Shen, Zhao, Dong & Zeng 2023 — "Brain-inspired neural circuit evolution for spiking neural networks" (PNAS 120(39):e2218173120)
NeuEvo: evolves biologically plausible circuit structures using excitatory–inhibitory neurons and
feedforward–feedback connections via local unsupervised learning rules, **combined with a global error
signal**. Related: Pan, Zhao, Zhao & Zeng, arXiv 2309.05263 (local modular motifs + evolved global
cross-module feedforward/feedback connectivity). **Use for us (queue N3):** a candidate structural-
descriptor vocabulary for METRIC_BATTERY §3. **Two constraints:** (1) PJM reads it as a HYPOTHESIS (likely
minicolumn-inspired) about laminar cortical organisation — so use as descriptors we COMPUTE, never as
structures we EXPECT; (2) FF/FB is undefined in our single recurrent pool (no laminae/space/hierarchy), so
only E/I motif composition, cycle/loop structure, and modularity transfer cleanly. **Caveat:** their local
rules are paired with a GLOBAL ERROR SIGNAL, a supervised channel we deliberately lack — so their success
is not evidence that evolution + purely local rules suffices, and that global signal is arguably doing work
analogous to the readout-capacity hazard D111 rejects.

### Evolutionary Spiking Neural Networks: A Survey (arXiv 2406.12552 / J Membrane Computing 2024)
Survey of evolutionary approaches to SNNs. Abstract-level only so far; positioning material for the
write-up (checking whether anyone has asked the fitness-vs-P question of a biologically-structured SNN).
Pull properly when drafting.

### Pachitariu, Zhong, Gracias, Minisi, Lopez & Stringer 2026 — "A critical initialization for biological neural networks" (Nature 655:990–996)
Large-scale mouse recordings (2p cortex, CA1, 8-probe Neuropixels) match linear dynamics under a random
SYMMETRIC matrix that is CRITICALLY NORMALIZED (largest eigenvalue ≈ 0.998). Covariance eigenvalues decay
as a power law: ~2/3 symmetric vs ~1.25 non-symmetric; cortex/brainwide give 0.7–0.85. CA1 is the
exception (0.4–0.5, an efficient uncorrelated code). **Incomplete normalization destroys long-timescale
macroscopic structure.** Survives sparse/clustered/spatial connectivity. Solves zero-shot working memory.
Code: github.com/mouseland/critical_init.

**Why it matters to us (D117).** Measured against their criteria our networks are ρ(W) ≈ 5.1 (≈5×
supercritical), E→E reciprocity at chance, and inhibition sparse/specific rather than global — three
Dale-COMPATIBLE differences. Critical normalization is their mechanism for producing long timescales from
fast units, which is exactly the 75× timescale gap our task poses (A3), so this is a concrete mechanistic
candidate for the D116 finding of ZERO context use.

**Clarification (PJM corrected Claude's first reading):** their "symmetry" does NOT conflict with Dale's
law. A is drawn all-POSITIVE (excitatory) and the mean is then subtracted — a global inhibitory feedback
term, not sign-flipped synapses. Units are "a neuron or a group of neurons," so A is an effective/
population-level matrix. The evidence for symmetry is anatomical RECIPROCITY (mesoscale connectome;
reciprocal V1 pairs), which is Dale-compatible.

**BIOLOGICAL GROUNDING OF THEIR TWO STRUCTURAL ASSUMPTIONS (PJM's challenge; D117 action 5).**
- *Reciprocal excitation:* ENRICHED but not full. Song et al. 2005 (rat V1 L5 pairs) find reciprocal
  connections ~4x overrepresented vs chance — robust — but pairwise connection probability is order 10%,
  so most connections remain unidirectional, and WEIGHT MATCHING (W_ij ~ W_ji) is not established.
- *Global inhibition:* dense nonspecific LOCAL inhibition is well grounded (PV+ "blanket of inhibition",
  Fino & Yuste); anything brain-wide is not (inhibitory axons are spatially restricted; SOM/VIP
  specificity is well documented). Their Fig. 4 actually sets inhibition proportional to LOCAL connection
  probability — the global mean-subtraction is the dense-case idealisation, not the claim.
- *Symmetry is doing mathematical work:* it yields real eigenvalues, a closed-form Lyapunov solution and
  the semicircle law, hence the analytic 2/3 exponent; they concede the non-symmetric case is "an open
  problem" (1.25 numerical only). Observed exponents 0.7–0.85 fall BETWEEN their two predictions, and the
  rotational evidence comes from SPONTANEOUS activity in darkness — they report task-driven recordings DO
  show rotational components.
- **=> We DROP reciprocity and global inhibition as design variants (adopting them would build in the
  mechanism under test, D038/D074). We KEEP critical normalisation: it is scalar, symmetry-independent,
  and has a real biological implementation (homeostatic synaptic scaling, activity-dependent pruning).**

**Two challenges to us.** (1) They benchmark ECHO-STATE networks — the class our noisy nonlinear spiking
net most resembles — and find they cannot hold memory beyond ~0.5 s due to chaotic dynamics being
noise-fragile, while symmetric critically-normalized dynamics work at multi-second lags. Our task needs
0.5–1.5 s. (2) They hypothesize that "perhaps all the learning… is on the readout or feedforward
connections" — the reservoir-computing position D111 rejected, here advanced as a claim about BIOLOGY. If
true, "P = recurrent synapses" may not be the parameter count governing generalization. A live threat to
the H-A/H-B framing worth tracking (they note an alternative: task-specific dynamics "turning on").


# ADDITION to REFERENCES.md
# Insert as a new top-level section. Placement suggestion: immediately after the
# "Engineered-ceiling circuit basis" section, since it is the direct continuation of that thread.

## Structure as a precondition, and how a GENOME can specify it (searched 2026-07-26, after D130)

*Context: D130 ablated all recurrent connectivity (`genome.mag` zeroed, `tau_slow` retained) against
intact networks on paired genomes. Where the task is solvable (50 ms delay) the ABLATED network held the
cue at 1.000 and read `quad` at 0.786-0.840 — equal to or above intact. Where passive decay fails
(200/400 ms) the intact network failed identically at every coupling. The recurrent network contributes
nothing, so P — which counts recurrent synapses — could never have mattered.*

*This independently re-derives, on the trial task, what D092 already found on the covariance task:
**random undeveloped nets do not carry context, because slow current only yields persistent memory when
wired into an attractor TOPOLOGY; random connectivity lacks it.** Two tasks, two methods, one answer. The
question is therefore no longer WHETHER structure is required — it is how a genome can specify structure
without the experimenter hand-wiring the solution (which D092's quarantine rightly forbids).*

### The minimum structure is a connectivity STATISTIC, not a hand-wired circuit

**Litwin-Kumar, A., Doiron, B. (2012).** Slow dynamics and high variability in balanced cortical networks
with clustered connections. *Nature Neuroscience* 15(11), 1498–1505.
— 🔴🔴 **The single most important reference for the post-D130 redesign.** Excitatory connections in
cortex are clustered rather than uniform. In balanced E/I networks, *even modest clustering* changes
network behaviour qualitatively: clusters transiently increase or decrease firing rate, producing SLOW
DYNAMICS alongside fast spiking variability. Stimulation biases the network toward particular activity
states and reduces firing-rate variability, matching cortical observations.
— **Why it matters to us.** This is the missing timescale. Our substrate's entire memory is single-neuron
`tau_slow` leak (D130), and clustering is the documented route to a network-level slow timescale that
leak cannot supply. Crucially it is a *statistical bias in the connection distribution*, not an
engineered attractor — which is exactly the kind of thing a genome could plausibly encode and evolution
could plausibly find. It sits between our two dead ends: random connectivity (no memory, D130) and the
hand-wired ceiling (memory, but quarantined as a template, D092).
— ⚠ **Scale caveat.** Their networks use ~1600 excitatory neurons across many clusters. At N=50 the
ceiling affords 2 clusters of ~20 E neurons; at N=100, roughly 4. Cluster SIZE, not count, is what N buys
back — and 2 clusters at N=50 is already demonstrated to work (D092).

**Recent clustered-network theory (2025), for the finite-size caveat.** Under 1/N weight scaling,
clustered spiking networks converge to deterministic mean-field dynamics only in the large-N limit; at
smaller N, stable fixed points and other attractors become METASTABLE, with finite-size fluctuations
shaping firing rates and driving transitions between states.
— **Implication for us:** at N=50–100 we should expect noisy, transition-prone attractors rather than
clean persistent states. That is a measurement problem (more trials, more genomes) and possibly a
*feature* — metastability is a plausible substrate for the regulation-level transitions we are looking
for — but it must not be mistaken for failure. *(Pin the citation before relying on it.)*

**Polk, A., Litwin-Kumar, A., Doiron, B. (2012).** Correlated neural variability in persistent state
networks. *PNAS* 109(16), 6295–6300.
— 🟡 Spiking variability causes persistent states to DRIFT, degrading memory over time; the usual
assumption of independent input fluctuations across cells is what this paper relaxes. Directly relevant
to how long a held cue can survive in a small noisy network, and to reading our delay-length axis.

### Genome encoding: why our current genome cannot express structure

*Our genome is DIRECT — per-synapse `mag` plus per-neuron `signs` (D038), ~735 free parameters at
density 0.3, N=50. Clustered topologies occupy a vanishing fraction of that space, so random draws never
contain one and single-synapse mutation almost never builds one. This is a VOCABULARY problem, not a
selection-pressure problem, and it may be sufficient on its own to explain D124/D125/D129/D130.*

**Stanley, K. O., D'Ambrosio, D. B., Gauci, J. (2009).** A hypercube-based indirect encoding for evolving
large-scale neural networks. *Artificial Life* 15(2), 185–212. *(HyperNEAT; see also Stanley 2007 on
CPPNs, Genetic Programming and Evolvable Machines 8(2), 131–162.)*
— 🟢 The canonical indirect encoding: connectivity is a FUNCTION over a coordinate space rather than a
list of synapses, so a small genome specifies large structured connectivity.

**Elbrecht, D., Schuman, C. (2020).** Neuroevolution of spiking neural networks using compositional
pattern producing networks. *ICONS / ACM.*
— 🟢🔴 CPPN indirect encoding applied specifically to SPIKING networks, which is our case. Reports the
approach's key hazard directly: **mutating a single gene can change connectivity across a large portion
of the network**, so mutation-rate and encoding hyperparameters need care. For us this is a warning about
mutational smoothness — an encoding where every mutation is catastrophic is not evolvable, and our
replicator dynamics assume graded fitness differences.

**GENE / geometric encoding (Cartesian-genetic-programming meta-evolution, 2024, arXiv:2403.14019).**
— 🟢🔴 **The closest fit to what we should build.** A connection's weight is computed as a
(pseudo-)distance between the two linked neurons' latent positions, so **genome size grows LINEARLY with
neuron count instead of quadratically.** That is precisely the property we need for an interpretable P
axis: `P_gene = N*d + const`, tunable through the latent dimension `d`, and decoupled from the synapse
count. The paper also shows the distance function itself can be optimised rather than hand-chosen.

**Evolving efficient genetic encoding for deep SNNs (2024, arXiv:2411.06792).**
— 🟡 Frames the motivation in exactly our terms: the brain's neurons and synapses develop from only
~20,000 genes, motivating encodings that regulate large networks at low genomic cost. Their method
evolves initial WIRING RULES rather than weights.
— **Relevance:** this is the genotype≠phenotype compression our project is already about (D083/D104).
An indirect encoding is not a technical convenience for us — it IS a regulatory level specifying another
level, which is the phenomenon the study exists to examine.

### The distinction this section is really about

D092 quarantines the engineered ceiling: never a template, seed, or comparison for evolved networks. That
rule is correct and stands. But it does not settle a distinction the post-D130 redesign turns on:

> **Seeding a specific solution is contamination. Enlarging the genome's VOCABULARY so that structured
> solutions are reachable is not.** A genome that can express any clustering — including none — still
> requires evolution to find which one, and can still fail. That is categorically different from handing
> evolution the ceiling's two-cluster topology.

Whether that distinction survives scrutiny is a live question, recorded in HYPOTHESIS_LOG under ENCODING.

# ADDITION to REFERENCES.md
# New top-level section. Suggested placement: after the "Structure as a precondition" section added
# 2026-07-26, which it directly continues and partly corrects.

## The dynamical working point: what sets network timescales, and what sets chaos (2026-07-28)

*Context: D138. Every operating-point sweep in this project (D129, D130, D135, D136) varied `w0`, which
scales all weights and therefore moves the coupling MEAN and VARIANCE together. These two quantities
control different things and have OPPOSITE requirements, so the sweeps traced a diagonal through a
two-dimensional space and reported its shape as the substrate's. At the study's default the spectral
radius of the connectivity is 6.28 — six times past the transition to chaos, a quantity that had never
been computed here.*

**Beiran, M., Ostojic, S. (2019).** Contrasting the effects of adaptation and synaptic filtering on the
timescales of dynamics in recurrent networks. *PLoS Comput Biol* 15(3): e1006893.
— 🔴🔴 **The most directly actionable reference this project has found.** Analyses randomly connected
E/I networks in which each unit carries one extra slow degree of freedom, either spike-frequency
ADAPTATION or SYNAPTIC FILTERING, and derives the resulting network timescales.

Four things we needed:
1. **Network dynamics do NOT inherit the timescale of adaptive currents.** The slow adaptive mode's
   amplitude falls in inverse proportion to its time constant, so its contribution is masked by the fast
   mode: a several-fold increase in adaptation time constant barely changes the response. **This closes
   a line we came close to pursuing.** Adaptation would not have rescued D130/D135/D136.
2. **Synaptic filtering DOES set the network timescale**, proportionally. Our `tau_slow` is a synaptic
   filter, so the mechanism we already have is the right one — the problem was never the mechanism.
3. **The formula.** `tau_network = tau_s / (1 - J_eff)` with `J_eff = J(C_E - g*C_I)`, the MEAN effective
   coupling. Divergence as `J_eff -> 1` is the standard fine-tuned route to slow activity, and it is the
   same working point Deco et al. identify from the other direction.
4. **Mean and variance are independent knobs.** The chaotic instability is governed by the coupling
   STANDARD DEVIATION, `J*sqrt(C_E + g^2*C_I)`, with the boundary at 1 — a different quantity from the
   mean, and the paper says explicitly that the two can be chosen independently, so population-averaged
   activity can be stable while individual neurons are not.
   **This is the point our parameterisation violates: `w0` cannot separate them.**

— *Model caveats for us:* theirs is a threshold-linear RATE model, N=3000, in-degree 100, constant
in-degree (which our per-neuron top-k already matches). Ours is conductance-based spiking at N=100,
in-degree 30. They expect the results to transfer to spiking networks via standard rate reductions, but
**the mapping from their `J` to our synaptic weights is not exact and the predicted timescale is a
target to verify, not a guarantee.** Finite-size fluctuations are also larger at our N.
— *Side result worth knowing:* strong coupling with adaptation produces a distinct dynamical state —
individual units showing mixed oscillatory and chaotic fluctuations, with damped oscillations in the
single-unit autocorrelation, and phases uncorrelated so nothing appears in the population average. If we
ever add adaptation, that signature is what to look for.

**Deco, G., Ponce-Alvarez, A., Mantini, D., Romani, G.L., Hagmann, P., Corbetta, M. (2013).**
Resting-State Functional Connectivity Emerges from Structurally and Dynamically Shaped Slow Linear
Fluctuations. *J Neurosci* 33(27): 11239–11252.
— 🔴 **Why the working point matters at all, and what development should target.** Derives a dynamic
mean-field reduction of a spiking E/I large-scale model and shows that functional connectivity emerges
as structured linear fluctuations around a stable low-activity state CLOSE TO DESTABILISATION. Best fit
to empirical FC occurs at the brink of the second bifurcation — the loss of stability of the spontaneous
state, not the appearance of multistable high-activity states. They deliberately separated the two
bifurcations to establish which one matters.

— **The mechanism gives us a measurable proxy.** As coupling increases, attraction toward the
spontaneous state weakens, the real part of some eigenvalues approaches zero, and the decay slows — so
**the autocorrelation time of spontaneous activity is a directly measurable criticality target.** No
Jacobian required.
— **On DEVELOPMENT STIMULI, which is what we asked it for.** The regime is RESTING state: no external
stimulation. The drive is an Ornstein-Uhlenbeck background (tau = 30 ms) of uncorrelated Poisson input,
and the noise must be WEAK — relative to their earlier model they cut the background intensity and
reduced the noise amplitude by ~14x, and report that stronger noise moves the bifurcation and REDUCES
the structure-function fit. Their reading: small fluctuations around the spontaneous state explain
resting dynamics better than large excursions shaped by the attractor landscape.
— **Robustness:** the best structure-function match occurs near the bifurcation across a wide range of
other parameters, which is what makes criticality a viable development TARGET rather than one more
tuning problem.
— *Incidental confirmations for us:* their local areas use N_E = 100, and they target asynchronous
spontaneous activity at ~3–10 Hz. Our networks measure 6.5–9.5 Hz — inside that band at every coupling
tested, which is why the "quiescent or paroxysmal" diagnosis from the neuroevolution scaffolding
literature does NOT describe our failure.

### What the two together imply for P (recorded because it is the load-bearing consequence)

**Noise-driven development to a dynamical target cannot inflate task-relevant capacity.** If the
development stimulus is unstructured noise and the target is a property of the dynamics, development has
no access to the task and therefore cannot encode anything task-specific. P remains the genome's
evolvable parameter count. This is structural, not an approximation — and it holds only while the
development stimulus stays task-blind.

**And Deco's central result says such development REVEALS structure rather than supplementing it.** The
covariance is determined by the eigen-decomposition of the Jacobian, which is fixed by the connectivity
evaluated at the working point; at criticality, structure is maximally expressed in function. That
inverts the H-E concern about development washing out variance: **under noise-driven criticality tuning,
differences in P should become MORE legible after development, not less.** That is a pre-registerable
prediction, and it distinguishes this scheme from D124's task-driven iSTDP, which was measured as a
headwind.

