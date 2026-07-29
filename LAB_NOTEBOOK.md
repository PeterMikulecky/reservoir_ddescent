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

## 2026-07-20 05:09 — `E9-evolve__20260720-050929__exp__g9894167__ceiling-validation`  <!-- auto -->
- type `exp` · stage `E9` · git `g9894167` (Add scripts/run_ceiling_validation.py: runnable, provenanced validation of the engineered ceiling (D092b). Imports ddescent.engineered_ceiling, runs the silent-delay carry test, persists a run directory + parquet table + LAB_NOTEBOOK stub. Verified end-to-end: ceiling is cue-selective (A-cue lights cluster A, B silent) and decays gracefully through silence (selectivity 3.95->1.66 over 100-600ms) - the validated memory signature (decay-across-delay), distinct from the random-net flat confound. Confirms the carry measure on the known-positive; trustworthy for step-3 developed-net testing) · status **complete**
- result: Engineered-ceiling carry validation (nmda=0.7, P=1080): selectivity 4.14(100ms)->1.70(600ms); selective=True, graceful_decay=True. VALIDATED known-positive. Carry measure = decay-across-delay (D092b).
- _interpretation:_ 

## 2026-07-21 07:25 — `E9-evolve__20260721-033119__exp__g4786765__step3-pilot`  <!-- auto -->
- type `exp` · stage `E9` · git `g4786765` (D099: build step-3 pilot harness (scripts/run_pilot.py) as a grid of independent (P,seed) cells - full apparatus (develop + 3-term fitness + D095 readout + D098b carry + selection), n_workers=6 default, provenanced per cell, VM-ready. evolve.py history now records per-generation component means/bests (enc/car/reg) so the pilot can watch whether capabilities COMPOUND under selection. Parallel determinism VERIFIED (clears D097 flag): serial==parallel bit-identical, content-hash seeds -> reproducible across worker counts and machines. Pilot grid: densities [0.2,0.4,0.6,0.8]x1seed, pop30, 50gen, ~1.1hr on 6 cores. Q: does fitness climb + components compound over 50 gens?) · status **complete**
- result: Step-3 pilot: fitness climbed 2/4 cells, capability compounded 2/4, clean=True. apparatus behaves.
- _interpretation:_ 


2026-07-21/24 — the sweep comes back flat, the diagnosis takes the apparatus apart, and the task turns out not to require memory
The intended experiment. Development × selection sweep: 16 cells, `wta_gain` 0/0.5/1/2 ×
`fitness_beta` 1/5/20/50, pop 30 × gen 40, ~18 h. Flat. `fit_slope` spanned only
[−0.0003, +0.0008] with no structure across the grid — competition-on rows did not beat
competition-off, high beta did not beat low. Best `best_test` touched 0.890 against a floor of
1.014 but no cell held it. Two real signals inside the flatness: excitatory fraction fell
reproducibly 0.80 → 0.66–0.73 in nearly every cell, and regulation drifted slightly positive in the
competition-on × higher-beta corner. Selection was moving the population, but not toward
generalisation.
Why it was flat, found three probes later. Split-half reliability of the fitness signal, n=30,
`n_assays` ∈ {1,2,4}: r(val,test) = −0.011 / +0.228 / +0.227. None significant at SE 0.192 — but
the variance decomposition is far better determined. Fitting V_obs(k) = V_true + V_noise/k gives
noise ≈ 4.6× signal in SD at `n_assays=1`, with SD(val−test) shrinking as 1/√k to within 12% of
prediction. Reliability at `n_assays=1` is ≈ 0.05. Every run to that point — including the 18-hour
sweep and the step-3 pilot whose stub records "fitness climbed 2/4 cells" — had selected on
approximately pure noise. That alone accounts for the flat landscape; no substrate story required
(D115).
Heritability probe (n=30 parent–child pairs) had pointed the same way earlier: aggregate fitness
r ≈ 0 (+0.028 / −0.025 across two conditions), regulation r ≈ +0.29. Read at the time as a
dissociation — the process looking selectionist rather than Darwinian. Withdrawn: at n=30 the SE
of a correlation is 0.192, so r = 0.29 sits 1.5 SE from zero and never differed significantly from
the aggregate. I should have computed the SE before calling it a finding (D109 → D115).
Nonlinear decodability probe (n=12, decoder ladder, chance 0.250) — the one large result that
still stands. Linear ridge 0.44/0.47; covariance-linear 0.41/0.47; random forest 0.60/0.69
(competition off/on). The covariance-linear decoder used in earlier probes, which had concluded
"context not decodable above chance", is among the worst on the same states: those nulls were a
decoder-format artifact. Competition also improved nonlinear decodability 0.60 → 0.69, which no
linear probe had detected (D110).
Regulation-only selection run (4 cells, pop 30 × gen 40). Selection strength dominated over
selection basis: at matched strength (calibrated β = 20 vs hybrid β = 5) the two were
indistinguishable, 0.0332 vs 0.0334; an advantage appeared only at β = 50, 2.5× beyond the match. The
hybrid control reproduced a prior cell to every digit — `fit_slope +0.00015`, `test_min 0.912` — so
the apparatus is deterministic across independent runs days apart. Two further results: hybrid
selection moved regulation down (−0.00008) while fitness moved up, and under hybrid fitness the
best of ten random networks beat the evolved population mean by 1.7× (0.1120 vs 0.0661). All test
numbers from this run are void — it predates the split fix, and train stagnating (0.986 → 0.993)
while test improved (0.960 → 0.928) is the leak's signature (D114).
Seven defects, all found by reading rather than running. `encoding` and `regulation` were the same
measurement offset by a constant, 1.0 − e and floor − e, r = 1.0000 exactly (D112). Fitness had been
computed from TEST error since D094, so ~1200 selective evaluations per run optimised the quantity we
report as generalisation (D113). The "memoryless floor" measured capacity, not memorylessness — a
static random 50-dim tanh expansion scored 0.9424 against the floor's 1.0197, beating it with no
network, no dynamics, no context (D116). Development at `dev_ms=800` saw 16/60 stimuli, 2 of 4
contexts, one context transition. `d=3` had collapsed the low-rank waist (r₁ = min(K,d) = 3), so
H-B was untestable. Spectral radius sat at ρ ≈ 4.42, never measured. None of these needed a long run
to find. The through-line: we had validated that code executes — smoke tests, single-cell trials,
checkpoint writes — never that it measures what it claims.
Hence `audit.py`, which asks the second question across six groups: fitness provenance (destroy a
split, confirm fitness moves iff it should), measurement identity, task invariants, exposure
coherence, config coherence, reliability and power. It reproduces every known defect — the validation
that matters — and went 6 FAIL → 0 FAIL as fixes landed. It has since found two on its own: a
train/test context-coverage mismatch (context 2 in test but absent from train and val, 17% of the
reporting split never developed on), and a degenerate fitness where all 30 genomes scored exactly
0.0000 after a zero-clip interacted with the `d=10` fix. Two of my own checks were wrong on first
writing, both because I wrote them from assumptions about the code rather than reading it — the same
failure mode the audit exists to catch.
Operating point: moved, then moved back. Calibration on developed networks against readout-free
criteria (responsiveness / health / covariance power-law α) gave 15 responsive, healthy cells with α
1.07 → 2.56 and responsiveness 0.33 → 0.74 in opposition. Picked gain 5 / noise 2.0 (responsiveness
0.360, α 1.23). The follow-up audit failed on the criterion the calibration never included:
reliability collapsed 0.465 → 0.066. Doubling `noise_sigma` quadruples measurement-noise variance in
every fitness estimate. α wants high noise, reliability wants low noise, and reliability is binding —
without it selection cannot work at all. Reverted to gain 10 / noise 1.0 (D118, D119).
Retired along the way: the RC-era skill gate, which scores a full mixing readout D095 forbids and
was the original justification for `input_gain=10`; and the "5× supercritical" framing — rescaling
magnitudes across ρ 0.5 → 4.42 moved α by < 0.1 (2.43 → 2.50), because threshold and refractoriness
clamp the loop gain. Input drive, not recurrent gain, sets dimensionality. Also measured: holding
per-synapse magnitude fixed while sweeping density scales total drive 5× (4.07 → 19.44 per neuron
from density 0.1 → 0.5), which would have confounded capacity with drive in the P sweep. Now w ∝ 1/√K.
Then the task collapsed. Bayes-optimal context inference from the covariance-context stimuli, given
the true covariances: 98.6% from a SINGLE sample, 100% from five. The task never required memory —
context was instantaneously available in every stimulus, so nothing had to be held across the dwell
window, which removes the justification for `tau_slow`, `context_dwell` and much of H-D's framing. And
the matched control built to measure context use shuffles stimulus order, which removes nothing when
each stimulus independently carries its own context. So `context_gain ≈ 0` was never evidence about
the substrate. Context use has never been validly measured on this project.
PJM's replacement: present a cue, allow a delay, then a discrimination stimulus whose response must
be modulated by the prior context. I resisted initially on the grounds that the original design
deliberately made context inferred rather than signalled — but that hazard applies to a dedicated
labelled channel, and PJM's cue is a stimulus like any other on shared channels. His four steps
(encode cue, hold it, encode probe, bind them) are the right account, and step 2 is a memory
requirement the old task simply lacked. The XOR target is load-bearing: measured over n=200, best
probe-only rule 0.500, best cue-only rule 0.500, joint 1.000. The floor is chance by
construction — unbeatable by capacity, static expansion or a lucky projection. Both controls validated:
`omit_cue` blanks the cue from the input; `scramble` permutes targets against stimuli, dropping oracle
accuracy to 0.510. (My first `scramble` permuted probe indices and recomputed the target from the
permuted pairing — a different valid trial set, removing nothing. The old shuffle control's error,
caught before use this time.) D120.
Where it stands. Audit clean at the reverted operating point: 0 FAIL, 24 PASS, with reliability
0.465 and α 1.92. New task built, controls validated, nothing run on it. Cost is ~2.7× per assay
(40 trials × 4 segments × 50 ms = 8000 ms vs 3000 ms), not cheaper as I had guessed.
Almost nothing was learned about double descent, and a great deal about the apparatus. What was
established: selection moves a population when the signal is reliable; the apparatus is deterministic
and reproducible to the digit; competition improves nonlinear decodability; dimensionality is set by
input drive rather than recurrent gain. What was un-established: every prior claim about context use,
encoding failure and heritability rested on instruments that did not measure what their names said.
Next: trial-structured `evaluate()` and development; audit C-group for the new task's invariants
(the waist and r₁/n_env checks are specific to the old task); cost re-measurement; then `wta_gain`
including 0 as a swept coordinate, since competition may suppress delay-period persistence and that is
selection's question to answer, not ours to assume.


## 2026-07-25 — Reliability-first investigation of the trial task: is trial_xor selectable? (No, at current config.)

*(Format inferred — I don't have LAB_NOTEBOOK.md in front of me; conform to the house style as needed.)*

**Where this started.** After D122 wired the trial arm, the plan was to run a first 40-gen arm. Before
spending it, applied the D115 reliability-first discipline: measure whether the trial_xor fitness carries
a selectable signal at all. It does not, at the current task + operating point. Full record: DECISIONS
D124; hypothesis update: HYPOTHESIS_LOG "SELECTABILITY" S1 (REFUTED).

**The path (each step narrowed the question):**
- Built a proper trial-task reliability probe (ICC + `V_obs(k)=V_true+V_noise/k` regression,
  cross-checked; sweeps n_assays × n_val; random + evolved populations; bases NMSE / accuracy / soft
  margin@T). Realized mid-build that a naive margin = NMSE for an in-sample LS fit, so the tanh squash is
  load-bearing — otherwise the "new basis" is the old one in disguise.
- n=30 developed-random: all bases flat at gen-0 except a whisker at n_val=80 (~0.22@a8). Walked back an
  earlier n=20 "val_acc=0.34/0.53 looks selectable" read — it was small-n_val overfitting, gone by n=30.
- Delay sweep 0/50/100 ms (trial_delay_sweep.py): flat at every delay; 0 ms actively worse; 100 ms ≈
  50 ms (passive maintenance not failing at one tau_slow). Delay is not the lever.
- Undeveloped-random n=30 (dev_ms=0): slightly MORE gen-0 variance than developed → development suppresses
  it (the (a)/(b) test lands on (a)), but weak either way.
- Overnight n=30 random + evolved (40 gens, 6 workers), developed AND undeveloped from the same evolved
  population (evolve-once, assay-both via --evolved-ckpt).

**What the overnight showed (the decisive run):**
- **40-gen trajectory FLAT.** best_test ~0.88–1.00 no trend; fit_mean ~+0.012 gen 0→39. Selection did not
  climb. Watched it happen instead of inferring it.
- **Evolved ≈ random** on every basis, both dev conditions. "Selectable once moving" refuted; the earlier
  0.53 confirmed as overfitting (didn't survive the full n_val sweep).
- **Development a secondary headwind** — real (undev evolved 0.20 > dev evolved 0.00 at n_val=80/a8) but
  not the blocker; the flat gradient is flat with dev off too.
- **`mean_exc` 0.80→0.64** — the one thing that moved monotonically. Selection grips E/I composition, not
  performance. Filed as a lead (H-Cv2 thread), not a finding.

**Read.** trial_xor is unselectable here. Every lever that keeps P's meaning intact — basis, delay, more
assays, development on/off — is now falsified. The XOR chance-floor-by-construction (what made D120
attractive) is exactly what zeroes the gen-0 gradient: arbitrary binding is not climbable from a random
start. This is the "development can't build arbitrary associations" argument from the same week, now with
numbers.

**Caveat I'm keeping honest about.** The evolve phase ran at n_assays=2 (probe cost cap), not the arm's
4. The reliability sweep says 4 wouldn't rescue it (low even at a8), so the full trial_selection_run arm
at n_assays=4 was NOT run — reliability-first says it would just confirm the null at more cost. But that
one direct test is formally unrun; the verdict rests on the sweep + the n_assays=2 flat trajectory.

**Process win worth stating plainly.** One ~6 h diagnostic overnight replaced a 40-gen science arm that
would have failed. That is exactly what the reliability discipline (D115) is for. No developed-phenotype
performance result was burned to learn the task is unselectable.

**Infrastructure touched today (all committed):** trial_reliability_probe.py gained --workers,
--evolved-ckpt population reuse, fitness-trajectory logging, tee persistence to runs/reliability/, and
the margin@T bases; trial_delay_sweep.py added. runlog.py fixed to open logs utf-8 (Windows cp1252 was
crashing runs on non-ASCII output).

**Open (decide next, a design turn — NOT decided today):** three structural levers remain, all of which
change what P means or what is selected — (i) the task's XOR chance floor (D120), (ii) the operating
point (gain/noise, D119, never moved), (iii) reframe selection onto the heritable structure that moved
(composition/regulation). Deferred deliberately; picking reactively off a null is the move the framework
guards against.

## 2026-07-27 00:06 — `E9-evolve__20260727-000625__exp__g7a01299__ceiling-validation`  <!-- auto -->
- type `exp` · stage `E9` · git `g7a01299` (20260726-161758_block_architecture_probe.log) · status **complete**
- result: Engineered-ceiling carry validation (nmda=0.7, P=1080): selectivity 4.29(100ms)->1.69(600ms); selective=True, graceful_decay=True. VALIDATED known-positive. Carry measure = decay-across-delay (D092b).
- _interpretation:_ 


# ADDITION to LAB_NOTEBOOK.md — append as the newest entry

## 2026-07-29 — The substrate gets a new mechanism, and the study shrinks: per-synapse timescales, N=100 → 30

**Where the day started.** With a closed parameter space and no way forward. D136 had swept the last
untested knob (`nmda_frac` × coupling, all 16 cells negative) and the standing conclusion was that no
operating point in this architecture lets recurrent synapses contribute. D133 had located the failure
precisely — signal dies at the first synapse — and D135 had shown recurrence actively degrading the one
thing that worked. The honest options were: write up the negative, or design a different study.

**The detour that had to be corrected first.** Two papers (Deco et al. 2013; Beiran & Ostojic 2019)
looked like they gave the working point from theory: network timescale `tau_s/(1-J_eff)`, chaos boundary
set by the coupling variance, and the two independently choosable. D138 recorded that our `w0` scales
both together, so every sweep we had run traced a *diagonal* through a two-dimensional space — which is
true, and survives. But its numbers did not: **Beiran & Ostojic's `J` is a rate-model coupling that
includes the firing-rate gain, and I compared raw weight-matrix quantities against rate-model
boundaries.** Measuring the gain (df/dI = 6.60 Hz per unit current, one short run — perturb `bias`, read
the rate) inverted both conclusions: we were not six times into chaos, we were far *below* both
bifurcations, and the fix was larger weights rather than smaller. Then the corrected target was built and
**still produced no timescale extension** — 20 ms measured, identical to a network with recurrence
removed. PJM's two corrections made the follow-up test possible at all: the inhibition ratio is a lever
that buys chaos headroom (J_eff/radius falls from 4.96 at r=0 to 0.22 at our 3.84), and longer bins, not
shorter, are what a slow mode needs. Sweeping J_eff to 0.95 at ratio 1 gave a real, monotone effect —
ac(100 ms) rising 0.11 → 0.25 — about **15× short** of the prediction. The rate-model mechanism does not
transfer to this substrate at this scale.

**Then the strategic turn.** Asked directly whether we were in a rabbit hole, the honest answer was yes:
four sweeps, an encoding redesign, two task changes and a dozen instrument corrections had produced a
precise account of what the substrate does *not* do, and the last hours were a search over explanations
for a null rather than a search for a working design. Every step since D124 had been a *repair* to a
design fixed months ago. PJM's call: design a substrate-first study, where the task is chosen to fit
measured dynamics and P is defined for that architecture.

**The variance screen that reframed P.** `P = |W|` counts recurrent synapses that D130/D135/D136 say do
not participate — so **a flat error-vs-P curve is the correct result for a parameter count over inert
components**, and the flatness may never have been about double descent at all. Screening parameter
classes for heritable variance in fitness put intrinsic parameters *above* recurrent weights (signs 0.72,
v_thresh 0.71, bias 0.67, recurrent 0.58, input_cols 0.48, as reliability at 4 draws). My verdict rule
was wrong — an sd/floor threshold rather than reliability at the number of draws a fitness actually uses
— and printed "nothing is selectable" when everything was.

**The literature search that supplied the mechanism.** Perez-Nieves et al. (2021) establish that
heterogeneous time constants help *only* on tasks where information is in precise spike timing, that
N=128 is deliberately small, and that the learned distributions are log-normal and match biology. But
HetSyn (2025) has the thing we needed: **put the time constant on the SYNAPSE, so different inputs to
the same neuron have different memory spans.** A long-tau synapse carries "then", a short-tau synapse
carries "now", and the neuron is a coincidence detector — no circuit required. That is exactly the
conjunction D128 measured at chance, and it explains *why* our substrate failed: one `tau_slow` shared by
every synapse means no neuron can compare across time.

**Step 1 passed.** A minimal Brian2 network, changing one thing — whether the probe deposits into the
fast current or shares the slow one — took match/non-match from **0.583 to 0.917 linearly decodable** at
a 400 ms delay. It failed at 800 ms because `tau_long` was 500 ms, which is a working range set by tau,
and therefore the first failure mode in this project that is a parameter the study would be sweeping.

**Step 2 passed, after a scare.** The P-group implementation (P current variables per neuron, synapses
assigned to groups, equations generated from P) initially scored 0.52 at N=30 and I briefly took it for a
broken prototype. Bisecting found the cause: **input drive, not N.** At w=0.9 the cells sit in a
compressive regime where both conditions saturate; at w=0.3 accuracy is **0.979**, better than step 1
ever reached. N=24 and N=30 gave *identical* results, which is independent support for the sizing
decision.

**And the study shrank.** N=100 was inherited from D131, where the argument was about cue-pair counts —
satisfied at any N. Sized properly against the new axis (P must bracket P_crit ≈ 72–96 training trials,
so `|W| = density·N·(N−1)` must exceed ~100) and against measured compute, **N=30 gives |W|=261 and a
4-day sweep where N=100 gives 45 days.** Perez-Nieves' own reason for staying small cuts the same way:
at larger N the homogeneous baseline nears ceiling and the effect being measured disappears.

**The process failure PJM caught at the end.** Nearly every decisive measurement today ran from `/tmp`
and was never committed — the gain measurement, the J_eff sweep, the aggregation comparison, step 1, the
prototype, the bisection. The findings entered DECISIONS; the code did not. **An entry citing a number
nobody can regenerate is a claim without evidence**, and this log's unusual care about instrument
corrections is undermined if the instruments are deleted. Now in `scripts/prototypes/` with a README
mapping each file to the finding and the entry, and a new standing rule: diagnostic code is committed in
the same commit as the entry that cites it.

**Owed before anything is swept.** The P=1 homogeneous control has not been re-run at w=0.3 — D139's
separation was measured at the *bad* operating point. If P=1 also reaches ~0.98 there, the mechanism
claim collapses and the outline fails at step 2. That single control is the next thing to run.

