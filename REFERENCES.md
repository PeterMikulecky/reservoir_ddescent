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
