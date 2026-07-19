# Lab notebook

Running record of what we did, found, and decided. Two kinds of entry:

- **Auto stubs** (`<!-- auto -->`) — appended automatically by `provenance.py` when a
  run finalizes: run ID, git commit + message, config, headline result, and a blank
  `_interpretation:_` line. *Fill that line in* — the facts are automatic, the meaning
  is not.
- **Prose entries** — hand-written notes: what a session concluded, what we decided,
  why. These carry the reasoning that stubs can't.

Newest entries at the bottom. Decisions referenced as `Dxxx` live in `DECISIONS.md`.

---

## 2026-07-13/14 — Project scaffold and environment
Built the reservoir engine (Brian2 LIF, numpy codegen — D001), the experiment/analysis
package, and the provenance system (run IDs, manifests, confirmatory firewall — D004).
Set up the working environment: local repo on `C:\dev\` + private GitHub (D008), run
data off the local drive via `DDESCENT_RUNS_ROOT` with cloud folders as archive-only
(D009), cmd terminal (D011). Smoke test passed and reproduced sandbox numbers exactly
(`pr_mean 9.212`) — seeded reproducibility confirmed.

## 2026-07-14 — T0 tuning: the static regime cannot support E1
Goal: find an operating point where PR is large **and responsive to connectivity** — the
independent variable E1 needs.

Coarse sweep (N=500, 48 operating points): activity spanned 0.11–0.90 with 44/48 in the
healthy band, peak PR ≈ 46 — so the dynamical regime is *fine*. But the best PR
responsiveness was `pr_range` ≈ 0.7 against `pr_mean` ≈ 37, i.e. **PR varies < 2% across
the full connectivity range.** Best candidates all sat at the lowest input gain (0.1),
with low-to-mid bias.

Follow-up: added `present_ms` as a swept axis to test reading the recurrent **transient**
instead of the settled fixed point. It helped in the predicted direction — responsiveness
roughly 2–3× better at `present_ms=20` vs `150` — but topped out around **3.7%**. Still
far too flat for E1.

**Interpretation.** With a static input read at (or near) the settled state, the reservoir
is essentially a random feature map of the input vector, so PR is anchored to the input
dimensionality (K=20) and recurrent connectivity is only a second-order perturbation. No
amount of bias/gain/timing tuning moves that anchor. Recurrence genuinely shapes effective
dimensionality only when the network integrates an input **history** — the temporal
regime, which is also the standard reservoir-computing setup and closer to Frank's picture
of regulatory circuits processing signals over context.

**Decision.** Pivot E1 to temporal inputs (D012), *provisionally* — gated on a temporal
PR-responsiveness check: confirm connectivity strongly moves PR with temporal inputs before
rebuilding E1. Flagged as a possible framing change (instantaneous map → memory/trajectory
system); H1–H5 to be re-examined in a design_doc revision.

**Value of the negative result.** Tuning did its job: it ruled out the static setup *before*
a flagship run that couldn't have worked.

*Next:* build a temporal task + a temporal PR-responsiveness diagnostic; run it as the
go/no-go for the pivot.

## 2026-07-14 — Literature search overturns the temporal pivot: the flat PR was our own artifact
Before building the temporal diagnostic, ran a targeted literature search on what controls
dynamics/dimensionality in spiking reservoirs. It immediately overturned the previous
session's conclusion.

**Key sources.** Recanatesi, Ocker, Buice & Shea-Brown (2019, PLOS Comp Biol),
*Dimensionality in recurrent spiking networks* — uses the **same participation-ratio**
measure, and sweeps connection probability *p* to show dimensionality is strongly
regulated by connectivity, **decreasing as p rises**, with the effect concentrated where
the spectral radius approaches 1. Also: dimensionality varies widely *at fixed p*
depending on how connections are arranged (motif structure), and most motif types
(chains, convergent, divergent) *lower* dimensionality, while reciprocal/trace motifs can
raise it. Supporting: Legenstein & Maass (2007) kernel-rank / generalization-rank
measures; Büsing et al. (2010) on connectivity dependence in binary vs analog reservoirs.

**The realization.** Recanatesi et al. vary p *without renormalizing gain*. We were
renormalizing — in **both** available modes (`spectral_radius` rescales to a fixed rho;
`gain` divides by √(p·N), pinning rho ≈ gain). So sweeping density while holding coupling
constant erased the density → dimensionality pathway by construction.

**Control test (the smoking gun).** At w0 = 0.05 — roughly what the spectral-radius
normalization produced — PR was *numerically identical* to a network with **no recurrent
synapses at all** (15.06 vs 14.97). The recurrence was effectively disabled. Only at
w0 ≈ 3.0 (60× larger) did PR move (15 → 7.6). The "edge of chaos at rho ≈ 1" heuristic is
a **rate-network** result; this spiking LIF model with reset/refractoriness needs far
stronger coupling, so the whole rho ∈ [0.5, 2.0] sweep sat in a dead zone.

**Result after the fix** (fixed per-synapse w0, no renormalization), PR spread across
density:

| regime | w0 = 0.05 (old scaling) | w0 = 1.5 | w0 = 3.0 |
|---|---|---|---|
| static  | 0% | 124% | 159% |
| temporal | — | 127% | — |

Direction matches Recanatesi et al.: **PR decreases with density.**

**Interpretation.** My previous mechanistic story — "static input anchors PR to input
dimensionality; only temporal recurrence can shape the representation" — was plausible and
**wrong**. Static works fine (better than temporal, in fact). The static/temporal axis was
never the binding constraint; effective coupling was. D012 (temporal pivot) is superseded
by D014. E1 stays static; no framing change; H1–H5 stand.

**Bonus for the science.** Frank's intuition is more wiring → more dimensionality. Both the
literature and our data show dimensionality *decreasing* with connectivity — sharpening H2
into a directional prediction with independent backing.

**Methodological lesson.** Two faults compounded and were both invisible to the tuning
sweep, which faithfully measured a real quantity in a regime where the independent variable
did nothing: (1) a normalization holding the mediating quantity constant, (2) a parameter
range where the manipulated component had no effect. Standing rules going forward: when
sweeping a structural variable, check that no normalization pins the mediator; and run a
**disconnected-network control** to confirm the component does anything at all before
interpreting a null.

*Next:* re-run the T0 tuning sweep in the w0 parameterization (sweep w0 × density × bias/
input_gain) to pick an operating point with high, responsive PR and healthy activity —
then E1 (static, as originally designed) is unblocked.

## 2026-07-14 — Reframe: the flagship becomes an evolutionary model (E9)
Four critiques from PJM, each landing, reshaped the project.

**Interpretation test retired (D018).** Checked the RMT literature: the interpolation peak
occurs where normalized effective degrees of freedom η_κ → 1 (Bach 2023; Hastie et al.).
So "effective dimensionality, not nominal count, sets the threshold" is *already
established*, and the literature supplies the principled metric (edof) — a different
functional of the spectrum than PR. PJM's critique ("we'd need to show other candidates
*aren't* the axis") forced the check. H5 demoted to a diagnostic.

**Dissociation reframed (D019).** PJM caught that varying motifs *in order to* move PR
couples them by construction — collinear predictors, same error class as the D014
normalization bug. Correct design exploits the many-to-one structure→PR map (Recanatesi:
PR varies widely at fixed density): build natural scatter, then test whether **PR screens
off structure** for generalization. That *is* Frank's claim H.

**E7 scoped (D020).** A reference point for messier systems must characterize its own
scaling — what's invariant, what's substrate-specific.

**Flagship = GA over motif-encoded reservoirs (D021, PJM's proposal).** The entire surveyed
literature lacks **selection**. A GA supplies heredity, lineage, population, and makes
Frank's mapping literal (selective history = training data; novel environments = test data)
rather than metaphorical. Genome v1 = (p, w0, recip, ei); readout = scoring mechanism;
metabolic cost on synapses makes "biology doesn't penalize complexity" a manipulable axis.

**The structural insight.** Above the interpolation threshold every individual interpolates,
so the fitness landscape is **flat — a neutral network**. Not a bug: it lands the population
exactly in the regime Frank's Gavrilets/neutral-space reframing is about. Central contrast
becomes below vs. above threshold, manipulated via size of selective history. The GA also
generates the D019 screening-off library as a byproduct.

**Where the project now stands.** It was "does dimensionality drive generalization"
(answered, by others, 2017). It is now: **does selection over heritable regulatory structure
produce general solutions, and does dimensionality mediate it?** The established literature
becomes the calibrated instrument — PJM's original instinct — rather than the result.

*Next:* (1) re-run T0 in the w0 parameterization; (2) **flat-landscape check** — verify
training NMSE ≈ 0 across the genome range above threshold, the load-bearing assumption of
E9; (3) build `evolve.py`. See GA_DESIGN.md.

## 2026-07-15 — First generalization measurement: Frank's claim H holds, in a channel we weren't looking at
Ran T0 rev2 (w0 parameterization) at N=1000: **200% PR responsiveness**, 20/20 healthy
operating points, PR span 7.7-57.1. The D014 fix confirmed at production scale (~100x better
than the 1.9% the spectral-radius version reported). E9 has a live dimensionality axis.
Chose bias=0.4, gain=0.1 provisionally — note the argmax sat on the grid boundary (all top
points at the lowest gain), and the top three differed by 0.8% with **no seed replication**.
The robust reading is "gain=0.1 matters; bias is free in 0.2-0.5."

**Readout check (D027): the averaging confound is cleared.** PR(X_inst) tracks PR(X_mean) at
every condition and falls with density in every case (span ratios ~85-95%). The trailing-window
average is not manufacturing the density effect. But at N=1000 the check also showed density ->
PR is **not** a main effect: it is a **w0 x density interaction**, U-shaped at w0=3.0. H2 needs
restating.

**Feature check (D028): the first time this project measured generalization.** 160 rows
(16 conditions x 10 seeds), log-transformed NMSE, mixed models.

A clean dissociation between readout channels:
- **`X_var`: PR predicts error negatively AND screens off structure** (test: pr -0.626 p=0.037,
  w0/density n.s.; novel: pr -1.503 p<0.0001, w0/density n.s.). **D019's screening-off criterion
  met = Frank's claim H supported.** First support the project has found.
- **`X_mean`: PR predicts error POSITIVELY** (test +0.230 p=0.006; novel +0.383 p=0.002) and
  fails to screen off structure — w0/density do the predicting. On the channel used for **every
  prior measurement**, dimensionality anti-predicts performance.

**The noise worry is resolved:** PR_var was suspect because noise is high-dimensional too — but
noise cannot predict generalization, and PR_var does. With D027's finding that PR_var peaks
exactly where PR_mean collapses, the reading is: **under strong coupling the representation
relocates into the fluctuations, and that is where the computation lives.** The mean channel
plausibly carries input leakage, explaining why more of it is worse.

**This reverses D026's fitness feature.** Reading `X_mean` would have made Frank's mechanism
invisible to E9 by construction.

**Method lesson, learned painfully.** The first analysis was WRONG: NMSE spanned 1.2-180,657, so
linear models fit the catastrophic tail (beta=-6156 against a median of 5.7) with singular
covariances everywhere. Demonstrated on synthetic data with a known effect + 6% outliers: raw
model p=0.746 (misses it), log model p<0.0001 (recovers it). **Log-transform heavy-tailed
outcomes; treat convergence warnings as results.**

**Not settled.** The novel task measures **extrapolation, not generalization** (D029) — every
novel NMSE > 1, i.e. nothing beat predicting the mean. Fixing it is tomorrow's first job and the
project's top priority: it gates H1, the only hypothesis that matters.

**Credit where due.** This finding exists because of three PJM interventions, none of them mine:
"what do we hope to capture from the settled state?" (prompted the settling test), "only two
seeds?" (forced real replication), and the parallel-protocols proposal (forced us to KEEP X_var
instead of discarding it). Without any one of them, the variance channel would still be invisible.

*Next:* fix `tasks.anisotropic_regression` -> re-run feature check -> finalize fitness feature ->
E9. See QUEUE.md.

## 2026-07-16 — The session the project changed: the reservoir loses to raw input, and the question turns out to be a different one

Started intending to fix the novel-environment task (D029). Fixing it required checking the
errors were sane — and they weren't, **in-distribution either**. Pulling that thread took the
project apart and rebuilt it.

**D030 — the reservoir loses to a linear readout on the raw input.** Baseline raw-input test
NMSE 0.217; at T0's chosen operating point (gain 0.1) the reservoir scored **0.880 — four times
worse than having no reservoir at all.** No ridge value rescued it. It first beat baseline at
gain=10, **100x** the gain T0 selected. **Root cause: T0 scored operating points on PR
responsiveness alone and never asked whether the state encodes the input.** Those objectives are
in *opposition* — low gain lets recurrence dominate, which makes PR beautifully responsive to
connectivity AND makes the state nearly independent of the input. **We optimized into a network
that ignores what we feed it, then measured the dimensionality of its daydreams.**
*The check we never ran, for the entire project life: does the reservoir beat a trivial
baseline?* Deeper than D014's normalization bug — that one made us measure a real thing in a
dead regime; this one meant we were not measuring computation at all.

**D031 — the literature had it mapped since 2012.** PJM called for a search. Our gain tension IS
**Dambre's memory–nonlinearity tradeoff**, mediated by input scaling, task-dependent optimum
across ~100x. We were rediscovering a known curve. Two more findings landed harder: **total
capacity is bounded by N and equals it under fading memory** (so connectivity *wastes* capacity,
never creates it), and **total IPC correlates POORLY with task-specific performance** (Hülser) —
a strong prior against H1 as we had operationalized it.

**D033 — the baseline-gated re-tune: tension dissolved, and a finding that outlives the model.**
At gain=10: **skill 1.448 AND pr_rel 49%** — computing *and* a live PR axis. My "the useful
regime may have no PR axis" alarm came from a **smoke** run and was wrong. But: at a validated
operating point, with K=20 inputs, **PR_mean ≈ 7.4 — the mean channel COMPRESSES 20 dimensions
into 7 — while PR_var ≈ 27 EXPANDS.** A reservoir's whole job is to expand. Ours compresses, in
the channel we had been reading. Independent corroboration of D028 from a new direction, and a
retroactive explanation of why PR_mean anti-predicted generalization: **we were measuring the
dimensionality of a lossy compression.**

**D032 — the reframe.** PJM: *"if we were to start from scratch, would we still pick a
reservoir?"* No. A reservoir **freezes W** — but Frank says *"regulatory connections are
parameters, selective history is training data, selection is the learning optimizer."* Our
recurrent synapses were architecture, not parameters. The only trained parameters were readout
weights, which are not regulatory connections. And our genome was **five numbers** — the far
left of Figure 1, with no capacity to overfit. **Genome-level double descent was impossible by
construction.** Every hard-won lesson (D014, D026, D030) was spiking-reservoir plumbing, not
Frank's question. *The instrument had been saying "I am not built for this" for two sessions.*

**PJM's governing insight, which reorganized everything:** *Frank is thinking more abstractly
than his words let on; substrate terminology leads us astray; the default hypothesis is that the
process is substrate-independent and the challenge is OURS — to find the mapping.* That became
`FRAMING.md`.

**The question, restated:** Frank's "more parameters → more dimensionality → better
generalization" **fuses P (parameter count) with D (effective capacity)**. ML networks confound
them by construction. A recurrent network separates them ~100:1. **That ambiguity, made
measurable, is the project.** *(D035: the separation is a property of RECURRENCE, not spiking —
I overclaimed. Spiking's real justification is our own finding: **D is channel-dependent**, and
the channel flips the sign of the relationship to generalization. Frank's framework has no
notion of a channel.)*

**D034 — a killed hypothesis.** I proposed that Frank never checks whether *selection* has the
implicit bias the second descent depends on. PJM: test it against the literature first. **The
Louis group built both ends of the bridge**: GP maps are biased toward simple outputs
(P(x) ≲ 2^-aK(x)), *and* deep learning generalizes because the parameter-function map has the
same bias. Frank's Wilson citation IS that volume argument. **His assumption is supported, not
unexamined.** Killed — and it found our intellectual home.

**D036 — PJM's ontology correction.** I spent three exchanges asking "which summary is the
phenotype — mean rate? rate vector?" **Malformed.** The phenotype is the **behavior**; rate and
variance and PR are *measurements of* it. Splitting phenotype / fitness / metrics **dissolved the
entire D026–D028 channel tangle**: those were two questions (what does fitness read? what
predicts generalization?) wearing one label.

**D037–D038 — the new model.** `evonet.py`: **W is the genome**, no readout, phenotype = output
behavior, environments demand **profiles**. N=100, d=10, n_env=50 → constraints 500; density
sweeps P from 50 to 4950 (0.1x → 9.9x). **Frank's Figure 1 x-axis made of regulatory
connections.** Then PJM caught that I was wrong about our own code: I said "no regulatory mode,
neurons only drive each other" — but 52% of our synapses were inhibitory. The real gap was
**no neuron-level identity**: 97/100 neurons excited some targets and inhibited others. **Dale's
law with evolvable per-neuron sign** fixed it (violations → 0). PJM's principle: *don't bolt on
a regulatory mode — make the architecture capable and let selection build it.*

**D039 — the search vindicated "don't bolt on," and killed my mechanism.** I'd claimed textbook
gain control is divisive (shunting). **Holt & Koch (1997): shunting is SUBTRACTIVE on firing
rates.** Divisive gain control needs **noise** (fluctuation-driven regime) plus **circuit
motifs** — not a synapse type. Adding shunting would have installed machinery that doesn't work.
*But it left a live problem:* `noise_sigma = 0` and tonic bias put us where gain control is
**unavailable**. Now Gate C.

**D040 — PJM's three-stage regulatory measure.** My Kaufman potent/null proposal assumed
**geometry implies mechanism** — PJM: *"does your approach simply assume anything output-null
must be regulatory?"* It did. Fix: null is a **screen** (candidates, graded), functional
contribution is the **filter** (real vs idle), gain-vs-offset is the **mechanism criterion**.
Works because of **recurrence**: null is null only instantaneously.

**Where the project stands.** It began as "can a reservoir show double descent." It is now:
**what does overparameterization mean in an evolving system — and which quantity is Frank's
x-axis?** Three modes of adding capacity (grow nodes / densify / reorganize) leave different
fingerprints on (P, D_max, D); which mode selection uses should depend on environments, tasks,
and **cost structure**. The reservoir did its job: it clarified the question and forced the
reckoning with the literature. It just wasn't the instrument to answer it.

**The pattern that should govern from here.** Four times this session a PJM-requested literature
search overturned something I was confident about: D014 (normalization), D031
(memory–nonlinearity), D034 (implicit bias), D039 (shunting). Plus three conceptual corrections
that were his and not mine: the reservoir question (D032), phenotype-is-behavior (D036),
null-as-screen (D040). **Search before building. And when the model keeps surprising you, suspect
the frame, not the parameters.**

*Next:* `evolve.py` → Gate A (baseline per density arm) → **Gate B (does a peak appear at all —
where this lives or dies)** → Gate C (balanced regime) → three modes × cost structure.
See QUEUE.md.

## 2026-07-17 — The frame arrives; the model is built; Gate B0 fails on arithmetic

**The frame (D056, PJM's).** Every earlier framing was **adversarial** (test Frank / beat R&N /
avoid Wagner) and each broke on a different objection. PJM's is **constructive**: ML, neuroAI and
evolutionary theory have converged on algorithmic learning, and double descent is expected to
pervade complex adaptive systems — **but the brain is not a deep network, and a brain is neither an
organism nor a population.** So: **map a REPERTOIRE of learning behaviours in spiking networks under
varying constraints and stimuli.** Frank's insight — *the parameter axis is where to look* — becomes
our **instrument**; **double descent becomes the DIAGNOSTIC, not the phenomenon.** Nobody has to be
wrong. Wang & Pope's SNN null becomes a data point; the tautological cells become **calibrated
corners** of the map.

**The distinction that rescued it (D055, PJM).** The story was collapsing into "Frank overclaimed
that biology doesn't regularize, here's a model showing how it can" — which is (1) an abundant
literature and (2) compatible with Frank being right about populations. **Fix: REGULARIZATION ≠
REGULATION.** Regularization prevents overfitting (well studied). **Regulation is a level that
modulates another level — its origin is unexplained.** The constructive question: **why did
regulatory hierarchy evolve? Because encoding saturates.**

**The tension nobody noticed (D054).** Frank claims the **curve**, explicitly: *"biology tends not to
penalize complexity... likely to experience the full consequences of the double descent learning
curve."* **Prevent overfitting and you prevent the peak — definitionally** (PJM's push). And his
premise is contradicted **on both timescales**: brains regularize heavily (Hoel's dreams-as-
regularization, evolved priors, homeostasis) and **selection itself regularizes** (R&N's Occam
factor). Two literatures, no contact, different vocabulary. **Our `c_syn` sweep asks whether Frank's
assumed regime is reachable at all.**

**Built and validated.** `evonet.py` (W as genome; Dale's law with evolvable identity; **inh_gain**
for E/I balance); `hierarchical_environments` (**context in the covariance, never the mean** —
PJM's sharpest constraint; rank-r₁ maps; **headroom 0.62** verified); `evolve.py` (**selection scheme
and density mode as ARMS** — *Friedlander used tournament, R&N replicator; the rivals differ on
exactly this*). **Gate C PASSED** — 31/36 fluctuation-driven, CV to 1.07, after two real bugs
(E/I unbalanced 24:1; fluctuations too slow vs τ_m). **H-D now has both arms via one knob.**
**Positive control PASSED** — peak at M/n = 1.00 exactly, second descent 202 → 2.50.

**GATE B0 FAILED (D067) — and the diagnosis is arithmetic.** best_train **0.936 → 0.882** over 100
generations; **worse than the memoryless floor (0.834)**. |W| = 1,221 params, **3,000 evaluations**
— evolution strategies need **~100n ⇒ 122,000. We are 40× short.** At 1.7 s/eval on 6 workers that
is **58 h per arm**, ~4,000 h for the map. **Evaluation cost is now a first-class design
constraint.** The lever is **quadratic**: N=20 → |W| ≈ 190 → ~1.5 h/arm. **And N=20 is Frank's own
scale** (2025a: "a sparsely and randomly connected network with 20 nodes"). **The honest trade:**
this is a **design failure, not a finding about biology** (as the script's own warning says) — but a
serious one, because the fix shrinks networks to where "spiking network" is generous.

**My errors this session, all caught by PJM.** Claimed a first descent that wasn't there (sweep
started past the optimum). A reproducibility bug (projections drawn sequentially — same seed, peak
moved 50→25). **The parallel pool was NEVER created** (`eval_fn` set before the `is None` test) — so
three sessions of timing estimates measured serial code, and I diagnosed a pickling-overhead problem
in code that wasn't parallel. **PJM found it in one glance at Task Manager.** And I shipped three
long jobs that printed **nothing** — a silently-serial pool looks exactly like slow code.

*Next:* **decide N before writing any more code.** N=20/d=3/n_env=20 → 60 constraints,
|W|/constraints ≈ 3.2. Alternatives: CMA-ES, cheaper fitness, fewer arms, or reconsider the
substrate. See QUEUE.md.

<!-- Future run stubs will be auto-appended below this line. -->

## 2026-07-18 02:29 — `E9-evolve__20260718-022622__exp__gb15c3c1__diagnostics`  <!-- auto -->
- type `exp` · stage `E9` · git `gb15c3c1` (E9 diagnostics: D030's actual gate (decode E from state and rates), FRAMING sec3 channel check on evonet, memory-vs-delay, carryover vs noise floor, context decode) · status **complete**
- result: E|state=0.218 E|rates=0.737; PR_var>PR_mean in 8/8; MC=0.00; order/noise=1.16; ctx=0.34 vs chance 0.25
- _interpretation:_ 

## 2026-07-18 04:09 — `E9-evolve__20260718-040319__exp__g16039fd__diagnostics`  <!-- auto -->
- type `exp` · stage `E9` · git `g16039fd` (rung 1: readout_pos knob (trailing default unchanged) to separate 'memory absent' from 'memory unread'; readout position as a diagnostics grid axis; correct the PR verdict - compression did not transfer and prediction was never tested) · status **complete**
- result: rung1: best mem_d1 trailing=1.000 leading=0.531; E|state=0.225 E|rates=0.730; PR_in=5.86 PR_mean_min=6.95; MC=0.47; ord/noise=6.09; ctx=0.32/0.25
- _interpretation:_ 

## 2026-07-18 05:13 — `E9-evolve__20260718-051032__exp__gf82d585__nmda-sweep`  <!-- auto -->
- type `exp` · stage `E9` · git `gf82d585` (D074: slow NMDA-like excitatory current (tau_slow=100ms, exc-only, no Mg gate), inert at nmda_frac=0 default; diagnostics sweep nmda_frac at present_ms=50, gate on d2-d3 movement) · status **complete**
- result: rung1: best mem_d1 trailing=0.826 leading=nan; E|state=0.316 E|rates=0.884; PR_in=5.86 PR_mean_min=1.01; MC=0.18; ord/noise=3.61; ctx=0.33/0.25
- _interpretation:_ 

## 2026-07-18 05:39 — `E9-evolve__20260718-053700__exp__ga6d1c98__nmda-sweep`  <!-- auto -->
- type `exp` · stage `E9` · git `ga6d1c98` (D075: charge-conserving fast/slow split (w_slow = f*w*tau_fast/tau_slow) - validated no collapse across nmda_frac axis, PR_mean stays ~7; fix diagnostics control check to test PR-collapse not hardcoded d1) · status **complete**
- result: rung1: best mem_d1 trailing=0.766 leading=nan; E|state=0.311 E|rates=0.893; PR_in=5.86 PR_mean_min=7.28; MC=0.29; ord/noise=2.14; ctx=0.32/0.25
- _interpretation:_ 

## 2026-07-19 02:09 — `E9-evolve__20260718-195534__exp__g46960f0__gatea-routing`  <!-- auto -->
- type `exp` · stage `E9` · git `g46960f0` (Gate A pre-registered (D080) and corrected before running (D081): metric = champion E|rates on fixed 200-env probe, true random baseline 0.99/0.43 not the 0.73 grid-min artifact; two decode bugs fixed; PASS = E|rates falls below 0.80. Runner + routing instrumentation in evolve.py) · status **complete**
- result: Gate A: E|rates 0.995->0.999 (fell -0.003); FAIL
- _interpretation:_ 
