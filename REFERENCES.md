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
