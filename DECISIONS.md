# Decision log

Append-only record of project decisions. Each entry: date, status, the decision, the
reasoning, and alternatives rejected. **Never edit or delete a past entry.** When a
decision is reversed, add a new entry that supersedes it and link back. This is the
project's memory of *why* things are the way they are — the thing most easily lost as
a project grows or collaborators join.

Status values: **Accepted** · **Accepted-provisional** (agreed, but gated on a pending
check) · **Superseded** (link to the entry that replaces it).

**Decision authority.** PJM has autonomy over this project's scientific direction. The
complex-systems group is a stakeholder and audience — a source of comparison and critique,
and the eventual venue — not an approval gate. Decisions here are made on their merits and
recorded; group buy-in is sought where it changes what *they* do (e.g. the comparative
ladder), not as a precondition for proceeding.

---

### D001 — Brian2 uses numpy code generation, not C++ compilation
**2026-07-13 · Accepted**
Reservoir simulations run with `prefs.codegen.target = "numpy"`.
*Reasoning:* avoids C++ compile-cache contention across parallel workers, and removes
the MSVC toolchain dependency entirely (no need to launch from an x64 Native Tools
prompt). *Rejected:* Brian2's default Cython/C++ mode — faster per-sim, but the
compile churn and toolchain requirement outweigh it for a parallel sweep. *Revisit if*
per-simulation speed becomes the bottleneck and we're willing to reintroduce the
compiler.

### D002 — Participation ratio (PR) is the master dimensionality axis
**2026-07-13 · Accepted**
"Effective dimensionality" throughout the project means PR of the reservoir state
covariance. *Reasoning:* it's the measurable quantity Frank's verbal "regulatory
dimensionality" maps onto, and it dissociates from neuron count and connectivity.

### D003 — Model-size double descent is load-bearing; epoch-wise is exploratory only
**2026-07-13 · Accepted**
Confirmatory (pre-registered) claims rest only on the model-size / architectural
mapping (synapses = parameters, PR = dimensionality). The epoch-wise "training-time =
circuit-age" version is assessed separately and never carries a pre-registered
conclusion. *Reasoning:* the architectural mapping is near-literal; the temporal one
substitutes a learning process for selection and rests on a softer metaphor. *Rejected:*
making the age story load-bearing — higher ceiling, but one skeptic on the metaphor
sinks the result.

### D004 — Run provenance: run IDs, manifests, and the confirmatory firewall
**2026-07-13 · Accepted**
Every run gets a structured ID (see NAMING.md) that names its output directory; each
run writes a manifest (git hash, config snapshot, env, seeds). `reg` (confirmatory)
runs abort on a dirty git tree. *Reasoning:* makes results reproducible and prevents
confirmatory output from uncommitted code. *Rejected:* filename-based versioning of
scripts — git already carries code identity.

### D005 — Code version lives in git, not in filenames
**2026-07-14 · Accepted**
Scripts keep stable filenames across revisions; "which version" is the git commit hash,
recorded in each run's manifest (with its commit message, as of this date). *Reasoning:*
git tracks a file's evolution as one lineage; `_v2_final` filenames don't. *Discipline:*
commit before running; tag milestone versions (e.g. `git tag T0-v2-transient`).

### D006 — UTC timestamps everywhere
**2026-07-13 · Accepted**
Run-ID timestamps are UTC. *Reasoning:* avoids timezone drift once runs happen on
multiple machines / collaborators.

### D007 — One sweep = one run = one results table
**2026-07-13 · Accepted**
A parallel sweep is a single provenance run; workers only compute rows, the parent
writes the results table and the registry once. *Reasoning:* avoids concurrent-write
races on the registry, keeps run granularity meaningful.

### D008 — Code repo is local + GitHub, NOT in OneDrive
**2026-07-14 · Accepted**
The working tree (code + `.git`) lives on a local drive (`C:\dev\...`) and is backed up
via a private GitHub repo. *Reasoning:* git and OneDrive both manage the same `.git`
internals; OneDrive syncing them mid-write can corrupt the repo. GitHub does the
backup job OneDrive would, with no downside. *Note:* the earlier 6-month OneDrive
project was fine because it used **no git** — git is the new ingredient that forces
this. *Rejected:* code in OneDrive (hardening `.git` exclusion is fiddlier than just
keeping it local).

### D009 — Run data lives off the local drive; cloud folders are archive-only
**2026-07-14 · Accepted**
Live runs write to a local (or external) drive via `DDESCENT_RUNS_ROOT`. Cloud-synced
folders (OneDrive/Google Drive/Dropbox) are **never** the live write target — only a
resting archive. *Reasoning:* real-time sync collides with the pipeline's rapid,
sometimes-parallel writes (esp. the frequently-rewritten registry). Reading an archived
run is fine; writing to a synced folder is not. *Rejected:* pointing the pipeline at a
cloud folder — even hardened with atomic-retry writes, it leans on retries more than we
want.

### D010 — Archiving is move-not-copy, verify-before-delete, prompt-per-run
**2026-07-14 · Accepted**
`archive_runs.py` moves **completed** runs to the OneDrive archive, verifies every file
(size + SHA-256) at the destination before deleting the local original, and prompts y/n
per run. Re-analysis is a manual copy-back — no resolver, no breadcrumbs. *Reasoning:*
frees local space with a safety net against half-synced copies; re-analysis is rare and
deliberate, so automating it would add fragile machinery for little gain. *Rejected:* an
auto-resolver + stub-leaving system — more moving parts than the problem warrants.

### D011 — Terminal is Windows cmd, not PowerShell
**2026-07-14 · Accepted**
Scripts, `setup.bat`, and `.vscode/settings.json` assume cmd. *Reasoning:* `.bat`
scripts and the project's path/env conventions target cmd; PowerShell differs on
invocation and env syntax.

### D012 — E1 flagship pivots from static to temporal inputs
**2026-07-14 · SUPERSEDED by D014 (2026-07-14)** — the premise was a misdiagnosis; see D014.
E1 (the fixed-N dissociation) moves from static input patterns to a temporal task.
*Reasoning (as stated at the time, now known to be wrong):* the T0 tuning sweep showed that with static, settled-state reading, PR
varies <2% across the full connectivity range (and only ~3.7% even reading the
transient) — PR is anchored to input dimensionality, and recurrent connectivity is only
a second-order effect. Recurrence genuinely shapes effective dimensionality only when
the network integrates an input *history*. This is also closer to Frank's framing of
regulatory circuits processing signals over context. *Gated on:* a temporal
PR-responsiveness check — confirm connectivity strongly moves PR in the temporal regime
before rebuilding E1 around it. *Framing consequence flagged:* changes what the reservoir
models (instantaneous map → memory/trajectory system); requires re-examining whether
H1–H5 need restatement. See design_doc.md temporal-pivot revision.
*Rejected:* staying static with higher input dim K and a chaotic regime — likely fights
the same input-anchoring problem.
**Why superseded:** the flat PR was an artifact of our own weight scaling, not a property
of static inputs. With coupling in the operative range, static gives ~124–159% PR spread
across density — as good as or better than temporal. The static/temporal axis was never
the binding constraint.

### D015 — The density→PR finding is scoped narrowly; it does NOT bear on Frank's core claim
**2026-07-14 · Accepted**
Our result "PR decreases as density increases" is recorded as: *one route* to more wiring
(uniform ER density at fixed per-synapse weight), in *one* coupling regime, at N=300, one
input distribution, unstructured graph. It is **not** evidence for or against Frank.
*Reasoning:* (a) **generalization is still entirely unmeasured** — H1 (PR → generalization)
is the load-bearing claim and we have not touched it; (b) Recanatesi et al. show
dimensionality varies widely *at fixed density* by motif arrangement, and reciprocal/trace
motifs can *raise* it — so "more wiring" arranged differently may well raise PR, and ER
density is the least structured possible way to add wiring, whereas regulatory networks are
modular/hierarchical; (c) Litwin-Kumar et al. (2017) find dimension is an **inverted-U** in
in-degree — our p = 0.02–0.4 at N=300 (K ≈ 6–120) likely sits almost entirely on the
descending limb (their optimum was K ≈ 9 at N=1000), so we may simply never have observed
the ascending limb. **Action:** sweep much lower densities before making any directional
claim. *Standing rule:* no claim about Frank's thesis until generalization is measured.

### D016 — PR is our chosen operationalization of Frank's "dimensionality"; this is an interpretive commitment, not a measurement
**2026-07-14 · Accepted · refines D002**
Frank's "overparameterization" is a **parameter count** (as in the ML double-descent
literature, where the x-axis is #parameters vs #data). Our PR is a property of the
**representation**. Equating them is a substantive interpretive choice that must be argued
explicitly in any writeup, not inherited silently. *Consequence:* H5 (does the interpolation
threshold scale with PR rather than nominal count?) is not a side hypothesis — it is the test
of whether this very identification holds, and is the most Frank-specific thing we have.
*Alternative measures to consider:* kernel rank / generalization rank (Legenstein & Maass
2007), information processing capacity (Dambre et al. 2012).

### D017 — Systematic related-work review precedes further building; E1 repositions toward a fixed-count motif dissociation
**2026-07-14 · Accepted** *(the "needs group endorsement" gate is removed — see Decision
authority in the header. Reposition target itself is refined by D019 and superseded as
flagship by D021.)*
A first targeted search shows the individual links we planned to test are largely
established: readout double descent = random-feature double descent (Belkin 2019);
density → dimensionality = Litwin-Kumar (2017, feedforward, inverted-U) and Recanatesi
(2019, recurrent spiking); dimensionality → task performance = Litwin-Kumar 2017,
Cayco-Gajic 2017, Legenstein & Maass 2007; E2/E3/E4 mechanisms = the very papers Frank
cites. See REFERENCES.md "Positioning".
*Decision:* (1) do a **systematic related-work review before further building**; (2)
reposition E1 away from the density sweep toward the design that appears genuinely open —
**hold N *and* synapse count fixed, vary only motif structure (SONET) to move PR, and test
whether generalization tracks PR.** This isolates dimensionality from parameter count and
directly pits Frank's "dimensionality per se" against "specific circuit features" (motifs
*are* circuit features), so either outcome is informative. *Enabled by:* Recanatesi et al.'s
finding that PR varies widely at fixed p by arrangement.
*Reasoning:* the pilot as designed is largely a re-derivation of known results in a new
substrate wearing an evolutionary frame. Acceptable for a group pilot; not what we said we
were building. Better to learn this now than after the flagship run.
*Open:* whether the group wants novelty at the framing level (evolutionary/comparative,
E7) or at the result level (the motif dissociation, H5). These call for different investments.

### D014 — Recurrent coupling uses fixed per-synapse weights (w0), not gain renormalization
**2026-07-14 · Accepted · supersedes D012**
`ConnectivityConfig.w0` (fixed per-synapse weight, no renormalization) is the coupling
mode for E1. Operative range for this LIF model is **w0 ≈ 0.5–3.0**.

*Reasoning — two compounding faults found, both ours, not the model's:*
1. **Renormalization erased the effect under test.** Both prior modes held effective
   coupling ~constant as density varied: the `spectral_radius` mode rescales W to a fixed
   target rho; the `gain` mode divides by √(p·N), which also pins rho ≈ gain. Sweeping
   density while renormalizing gain holds constant the very quantity that mediates
   density → dimensionality. Recanatesi et al. (2019) vary connection probability
   *without* renormalizing, and dimensionality responds strongly.
2. **The weight scale was ~60× too small for recurrence to matter at all.** Control test:
   at w0 = 0.05 (≈ what spectral-radius normalization produced) PR was numerically
   identical to a network with *no recurrent synapses whatsoever* (15.06 vs 14.97).
   The "edge of chaos at rho ≈ 1" heuristic is a **rate-network** result; in this spiking
   LIF model with reset and refractoriness, the entire rho ∈ [0.5, 2.0] sweep sits in a
   dead zone where recurrence has no measurable effect on PR.

*Evidence:* with w0 in the operative range, PR spread across density = **124–159% (static)**
and **127% (temporal)**, versus ~0–4% under renormalization. Direction matches Recanatesi
et al.: **PR decreases as density increases.**

*Consequences:*
- **E1 is viable, and stays static.** No framing change; H1–H5 need no restatement on this
  account. The design_doc temporal-pivot revision is not needed.
- **H2 gains strong prior support.** Frank's intuition is that more wiring → more
  dimensionality; Recanatesi et al. and our own data both show dimensionality *decreasing*
  with connectivity. This sharpens H2 from "possibly non-monotonic" to a directional
  prediction with independent literature backing.
- `spectral_radius` is retained only for legacy comparison and is documented as unsuitable
  for E1; the ConnectivityConfig docstrings now carry the warning.
- **Methodological lesson (generalize this):** when sweeping a structural variable, verify
  no normalization is holding the mediating quantity constant, and run a
  *disconnected-network control* to confirm the manipulated component has any effect at all
  before interpreting a null. Both faults were invisible to the tuning sweep, which was
  measuring a real quantity in a regime where the independent variable did nothing.

*Credit:* found via targeted literature search (Recanatesi/Ocker/Buice/Shea-Brown 2019,
PLOS Comp Biol; Legenstein & Maass 2007; Büsing et al. 2010), not from first-principles
reasoning — which had produced a confident and wrong mechanistic story.

### D022 — Flat-landscape check: assumption confirmed, and it exposed a design flaw
**2026-07-14 · Accepted**
Measured (N=300, min-norm readout): **above threshold (n=50 ≪ M=300) training NMSE ≈ 1e-29
for every genome, including PR = 2.5** — the landscape is exactly flat, as D021 assumed.
Rank is full at min(n,M) *regardless of PR* (rank 49 at n=50), so a prior hypothesis that
low-PR genomes would fail to interpolate was **wrong**: rank and PR are different things.
**Below threshold (n=400 > M=300) training error varies ~6× (0.05–0.43) and favors high PR.**
*Bonus finding:* since rank is full regardless of PR, **PR does not relocate the interpolation
threshold** — it sits at nominal capacity. Independent confirmation of D018 (H5 retired) from
our own data rather than the RMT literature.
*The flaw it exposed:* "neutral network" *means* selection has no signal — that is the
definition. Running a GA there is drift with extra steps. Frank's claim about that regime is
that the **learning dynamics** (here: the min-norm readout solver) pick the interpolating
solution — that is E4's implicit-bias question, not an evolutionary one. The gate did its job:
found before building.

### D023 — E9 rev. C: readout capacity M becomes a heritable gene
**2026-07-14 · Accepted · revises D021**
Genome gains **`M`** (readout capacity): `(M, p, w0, recip, ei)`. The readout taps M of N
neurons; N=1000 becomes the *pool*, with **N ≫ n** the binding constraint (n ≈ 50–100).
*Reasoning:* the double-descent x-axis is the **learned**-parameter count = the readout
weights = M. Recurrent weights are structure, not learned. If the experimenter fixes M, "does
evolution find overparameterization?" is unaskable — we chose the answer. **C is the only
variant in which Frank's central claim is testable.**
*The prediction that justifies it:* below threshold selection pushes M up (training error
falls with M); above threshold training error is flat at zero so cost pushes M down. They meet
at **M ≈ n = the test-error peak** → **selection with any parameter cost parks a lineage at the
worst-generalizing capacity (G1)**. At **c_syn = 0**, the plateau is neutral with a reflecting
boundary at M = n, so M drifts *upward* and generalization improves via the second descent
(G2). **Frank's aside that biology doesn't penalize complexity turns out to be the precise
condition his thesis requires.** `c_syn` is therefore the central swept axis, not a nuisance —
the evolutionary form of E4's ridge-vs-min-norm contrast.
*Also:* C separates two readings of Frank's "parameterization" that he does not distinguish —
`M` (learned parameters) vs `p`/`w0`/`recip` (regulatory structure) — and can ask which
behaves as claimed. Sharpens D016.
*Rejected:* rev. A (below-threshold only — has signal but abandons the overparameterized
regime, i.e. Frank's distinctive claim); rev. B (accumulating environments — the crossing is
imposed by the experimenter growing n, whereas in C the lineage discovers it; B can be layered
onto C later).
*Cost concern withdrawn:* "the design grows" was filed as a cost out of a reflex toward
minimal designs. The additions (a fifth gene, M-identity question, M×p×w0 interactions) *are*
the mechanism of the experiment, not overhead.
*Credit:* PJM — the question "is that growth bad?" reversed the recommendation.

### D024 — Production scale is N = 1000
**2026-07-14 · Accepted**
N=300 was a sandbox-probe tractability choice, never a principled production decision.
*Benchmark:* per-individual cost scales **sublinearly** in N (N=800 is 1.6× N=200, not 16×)
because the D014 `w0` mode skips the O(N³) eigenvalue call the old `spectral_radius` mode
required. At N=1000, pop 50 × 100 gens ≈ **1–2 h on 6 workers**. Affordable.
*Also:* N=1000 matches the group's original brainstorm and both Litwin-Kumar (2017) and
Recanatesi (2019) — direct comparability. Prototype at N=300; scaling checks per D020.

### D025 — Metric strategy: store the spectrum, not the scalars; tier by real cost
**2026-07-14 · Accepted**
Adopt PJM's principle (collecting beats re-running), but implement it by storing **the
object the metrics derive from**, not a longer list of scalars.
*Core insight:* PR, edof, effective rank, kernel rank and spectral entropy are all
**functionals of the same eigenvalue spectrum**. So `metrics.spectrum()` stores the top-k
singular values (float32, ~320 B/individual → **1.6 MB per 5000-evaluation GA run**), and
every spectral metric — including ones we have not thought of — is recoverable post hoc
without re-running anything. Verified: PR and edof recomputed from the stored spectrum alone.
*Why this matters concretely:* at our operative point PR = 14.6 but **edof ≈ 79** — same
spectrum, two functionals, 5× disagreement. Storing only PR would have made D018's edof
question unanswerable without a full re-run.
*Cost tiers (measured):*
- **FREE** (battery = 113 ms vs 2400 ms simulation, <5% overhead): spectrum, PR, edof at
  several κ, effective rank, spectral entropy, numerical/kernel rank, rate + diversity +
  synchrony stats, weight norm, synapse count, sparse spectral radius.
- **CHEAP** (one extra sim pass): generalization rank (needs noisy input variants).
- **EXPENSIVE** (separate protocol per individual): IPC (Dambre), Lyapunov exponent,
  robustness interval. **Do NOT run per-individual in a 5000-eval GA** — run on the final
  evolved population or a curated subset, where they are informative anyway.
- **Irrelevant**: energy efficiency (not a hardware project).
*Optimizations that made it free:* derive rank from the already-computed spectrum rather than
a second SVD; subsample neurons for the O(N²) correlation; sparse `eigs` for spectral radius
instead of O(N³) full `eig`. (3× speedup, identical values.)
*On the source list:* it recommends targeting spectral radius ≈ 1 for the edge of chaos —
the **rate-network heuristic D014 disproved for this LIF model** (our whole ρ ∈ [0.5, 2.0]
sweep was a dead zone; the battery now measures ρ = 8.4 at the operative w0, independently
confirming it). ρ is retained as a *descriptor* for literature comparability (Recanatesi's
density effect concentrates near ρ→1), **not** a tuning target. The list also omits **edof**,
the most relevant quantity per D018.
*Guard against the obvious hazard:* breadth invites the garden of forking paths. **PR remains
the pre-specified confirmatory measure (D002/D016); everything else in the battery is
exploratory** and must be reported as such. The `reg` firewall and pre-registration exist to
keep this honest — a 20-metric battery mined for whichever correlates with generalization is
p-hacking with extra steps.
*Also store:* raw state matrices X for a **subsample** (e.g. best + a few random individuals
per generation), which future-proofs *non*-spectral state metrics too. Full storage is ~800 KB
per individual → ~4 GB per run; subsampling keeps that manageable.
*Credit:* PJM.

### D026 — "Settled" → "stationary"; two protocols; fitness is Protocol S; the averaging check is standing
**2026-07-14 · Accepted**  ·  spec: `PROTOCOLS.md`
**The network does not settle.** Settling test (N=200, 400 ms constant drive): within-window
temporal CV rises 0.077 → 0.20–0.26 as coupling grows; at w0=3, p=0.4 the rate trace still
fluctuates ~20% after 400 ms. There is **no fixed point** in the regime we care about, and it
is worst exactly where our headline effect lives. A protocol "designed to cleanly measure the
settled state" would target an object that does not exist.
*Reframe:* what is well-defined is a **stationary response distribution** (mean, covariance,
autocorrelation time of the occupied attractor). Better because it is always defined, still
faithful to Frank's GRN reading (a cell in a sustained environment occupies a characteristic
expression *regime*, not necessarily a static point), and it *tells us what to measure*.
**The confound this exposes.** We record only the distribution's mean (trailing-window average)
and discard the rest. Averaging destroys variance, and the amount destroyed **grows with
coupling** — a mechanism that would produce "PR falls with density/coupling" (our headline
finding) with none of it being a property of the representation. Recanatesi et al. find the
same direction by a different method with no window averaging — real evidence the effect is not
purely artifact — but their model is linearized Poisson, not spiking LIF with reset, so it does
not settle it for us. **Not demonstrated, not dismissed.**
*Therefore — standing, never optional:* Protocol S retains **three** readouts per pattern
(`X_mean`, `X_inst`, `X_var`) and every run reports PR on all three. Agreement ⇒ averaging is
innocent. Divergence ⇒ the window mean is manufacturing the effect. D025's logic applied to a
confound rather than a metric: bake the check in permanently rather than trusting one July run.
*Two protocols (PJM's proposal):* **S (stationary)** = sustained drive, the expensive one
(150 × 150 ms = 22.5 s sim). **T (temporal)** = one continuous stream, **~10% of S's cost** —
the asymmetry matters: adding T is nearly free, not a doubling.
*Metrics:* shared spectral core (D025 battery) on every state matrix; **S-specific** =
temporal_cv, autocorr_time, attractor_pr (PR of a *single* pattern's trajectory — only exists
under S), order_dependence (carryover check); **T-specific** = memory_capacity, separation,
IPC (deferred to the final population per D025 tiers).
**The thing that cannot be plural.** Metrics can be plural; **fitness cannot** — the GA needs
one number. S-fitness and T-fitness are *two different evolutionary models*, not two views of
one. **Decision: fitness = Protocol S** (Frank's core; already built in
`tasks.anisotropic_regression`); **T is characterization**, explicitly exploratory. No
forking-path risk: the confirmatory measure stays PR on `X_mean` under S (D002/D016).
*Deferred, not rejected:* two GA arms evolving on S- vs T-fitness, compared — a real experiment
about whether environmental structure shapes evolvability. Doubles the budget, adds a second
flagship. Worth wanting; not first.
*Consequence for T0:* the T0 run in flight measures PR through the window mean only. Its chosen
operating point may need revisiting once the three-way readout comparison exists.
*Credit:* PJM — the parallel-protocols proposal, and the prior question ("what do we hope to
capture from the settled state?") that prompted the settling test.

### D027 — Readout check PASSED: the averaging confound is cleared
**2026-07-14 · Accepted** · closes the open risk in D026
The D026 standing check ran (N=300, bias 0.4, gain 0.1, 9 conditions, 11 window samples/pattern).
**PR(X_inst) tracks PR(X_mean) at every condition and falls with density in every case.**
Span ratios (inst/mean) across density: 40/50%, 203/211%, 113/134% → the unaveraged readout
reproduces the effect at ~85-95% of the averaged one. **The trailing-window average is NOT
manufacturing the headline finding.** Density and coupling genuinely collapse representational
dimensionality. D014's evidence and the T0 operating point stand.
*Secondary findings (kept because D026 forced us to retain all three readouts):*
- **PR(X_inst) is consistently slightly HIGHER than PR(X_mean)** (e.g. 40.6 vs 38.3; 12.2 vs
  9.7) — the predicted variance destruction is real but second-order. Averaging costs a few
  percent of PR, not the effect.
- **PR(X_var) is systematically the HIGHEST** of the three (46.6 / 45.2 / 35.4 …). The
  *fluctuations* carry more dimensionality than the mean. Only visible because we stopped
  discarding the variance. **Open question:** is `X_var` a better feature than `X_mean` for
  the readout? Flagged, not acted on — changing the fitness feature is a D026-scale decision.
- **temporal_cv is non-monotonic in coupling** (0.195 → 0.419 at w0=0.5, but 0.059 at w0=3.0,
  p=0.1). Strong coupling does not simply mean more fluctuation; the earlier "more coupling →
  more chaos → more averaging destroyed" story was too simple. It happened to be the right
  worry for the wrong reason.
*Method note:* the check needs ~11 window samples/pattern (sample_ms=5), vs the default
sample_ms=15 which yields ~4 — too few to estimate variance or attractor PR.

### D028 — FIRST evidence for Frank's claim H — in the VARIANCE channel; D026's fitness feature is reversed
**2026-07-15 · Accepted-provisional** (gated on the task fix, D029)
First real test of H1 (D015: no claim about Frank until generalization is measured).
N=1000, 16 conditions x 10 seeds = 160 rows, log-transformed NMSE, mixed models with
net_seed random effect.

**Result — a clean dissociation between readout channels:**

| channel | M2 (screening-off), test | M2, novel |
|---|---|---|
| `X_var` | pr **-0.626 (p=0.037)**, w0 +0.248 (p=0.31), density +0.276 (p=0.26) | pr **-1.503 (p<0.0001)**, w0 (p=0.95), density (p=0.89) |
| `X_mean` | pr **+0.230 (p=0.006)**, w0 -0.234 (p=0.005) | pr **+0.383 (p=0.002)**, w0 (p<0.0001), density (p<0.0001) |

* **Variance channel: PR predicts error negatively AND screens off structure** (w0/density
  non-significant). This is D019's screening-off criterion met, i.e. **Frank's claim H
  supported** — the first support this project has found.
* **Mean channel: PR predicts error POSITIVELY** (wrong direction, significant) and fails to
  screen off structure — structure does the predicting. On the channel used for **every
  measurement in this project** (the density->PR story, D014's evidence, T0's operating
  point), dimensionality anti-predicts performance.

**The noise worry is resolved.** PR_var was suspect because noise is also high-dimensional.
But **noise cannot predict generalization**, and PR_var does (p<0.0001 novel, p=0.037 test).
The fluctuations carry real structure. With D027's finding that PR_var is highest exactly
where PR_mean collapses, the coherent reading is: **under strong coupling the representation
RELOCATES into the fluctuations, and that is where the computation lives.** The mean channel
plausibly carries input leakage — which would explain why more of it is worse.

**Consequence — D026 is reversed.** Fitness must NOT read `X_mean`: doing so would make
Frank's mechanism invisible to E9 by construction, selecting on the one channel where
dimensionality anti-predicts performance. Candidate replacement: `X_var`, or a concatenation
of both. **Do not finalize until D029 (task fix).**

**Method note (important).** The un-transformed analysis was WRONG and its output must be
discarded: NMSE spanned 1.2-180,657 (~5 orders of magnitude), so linear models fit the
catastrophic tail, producing coefficients like beta=-6156 against a median NMSE of 5.7, plus
singular covariances and non-PD Hessians. Demonstrated on synthetic data with a KNOWN
negative effect + 6% outliers: raw-NMSE model p=0.746 (misses it); log model p<0.0001
(recovers it). **Log-transform heavy-tailed error outcomes; treat convergence warnings as
results, not noise.**

**Caveats — why this is provisional, not settled:**
1. Several `var` fits flagged DID NOT CONVERGE (M1, both outcomes). M2/M3 agree, but this
   needs a robust re-fit.
2. The novel task is **extrapolation, not generalization** (D029) — its p<0.0001 is on a
   broken measure. `test` (p=0.037) is honest but marginal.
3. One operating point (bias 0.4, gain 0.1), one task family, net/task seeds aliased.
4. Q1 reported medians for `novel` only — we do not yet know which channel generalizes best
   **in-distribution**, which is the comparison that matters.
*Converging support:* test and novel agree; M2 and M3 agree; per-seed correlations agree
independently (PR_var r=-0.283+/-0.055 consistent; PR_mean r=-0.082+/-0.182 ~zero).

### D029 — The novel-environment task is broken and must be fixed before H1 is judged
**2026-07-15 · Accepted**
`tasks.anisotropic_regression` draws its novel set along the LOWEST-variance axes — the ones
training barely sampled. **Every novel NMSE in the N=1000 run exceeded 1**, i.e. nothing beat
predicting the mean. That is orthogonal **extrapolation**, not generalization.
*Why it matters:* Frank's claim is about recognizing new instances of a *learned* class
("the essence of snakeness"), not about inputs from directions never sampled. Our novel set
tests the wrong thing.
*Fix:* novel environments must be **novel-but-related** — new draws from the same structured
class, or moderate shifts along *sampled* directions, not orthogonal ones.
*Priority:* **highest in the project.** It gates H1, which is the only hypothesis that
matters, and it gates finalizing D028's fitness-feature reversal.

### D030 — THE BASELINE GATE: the reservoir was never checked against raw input, and it loses
**2026-07-16 · Accepted** · supersedes T0's objective; puts D028 and the operating point in doubt
**The most basic sanity check in reservoir computing — does a readout on the reservoir beat a
readout on the RAW INPUT? — was never run in this project.** When finally run (N=300,
K=20, density 0.15, w0 2.0, best over a ridge grid):

| input_gain | best test NMSE | vs baseline 0.216 |
|---|---|---|
| **0.1 (T0's chosen point)** | **0.880** | **4x WORSE than no reservoir** |
| 0.3 | 0.294 | worse |
| 1.0 | 0.311 | worse |
| 3.0 | 0.249 | worse |
| 10.0 | **0.131** | **finally beats it** |

At the operating point T0 selected, the reservoir **destroys information**. No ridge value
rescues it: low alpha interpolates and test explodes (2-80), high alpha collapses to
predicting the mean (~0.97).

**Root cause — a missing constraint, not a bug.** T0 scored operating points on ONE thing:
does PR move across the genome space? It never asked whether the state encodes the input.
**Those objectives are in opposition:** low input gain lets recurrent dynamics dominate, which
makes PR beautifully responsive to connectivity AND makes the state nearly independent of the
input. We optimized into a network that ignores what we feed it, then measured the
dimensionality of its daydreams. Performance improves *monotonically* with the very parameter
T0 drove to its floor.

**Fix:** new `ddescent/baseline.py`. `skill = baseline_nmse / reservoir_nmse` (>1 = helps).
T0 rev3 now runs an actual TASK per condition and **gates on skill > 1 AND healthy BEFORE
ranking by PR responsiveness**. Gain grids widened (old grids topped out at 0.6; the reservoir
first beats baseline at 10 — we were searching entirely inside the useless regime).

**What this puts in doubt:**
- **T0's operating point (bias 0.4, gain 0.1) is INVALID** — chosen by an objective that
  selects against usefulness. Discard.
- **D028 is in serious doubt.** "PR_var predicts generalization" was measured at gain 0.1,
  where nothing generalizes and every novel NMSE exceeded 1 — it may be ranking *degrees of
  failure*. Note PR_var rises monotonically with gain (8.7 -> 38.8) alongside performance, so
  at a useful operating point the relationship may hold, reverse, or vanish. **Unknown.**
- **D014 and the density->PR story stand as measurements** but characterize a regime where the
  reservoir is not computing. Their relevance is unclear.

**New tension, now empirical rather than assumed.** The T0 rev3 smoke run selects gain=10
(skill 1.24) but there PR responsiveness collapses to 6% and activity saturates (0.935).
**The regime where the reservoir computes may be the regime where PR will not move.** If that
holds at N=1000, E9's premise — a live dimensionality axis in a useful network — is in
trouble, and the model may need rethinking (rate reservoir? different readout? E/I balance to
restore dynamic range?).

**Standing rule (the real lesson).** *Before interpreting any representational metric, prove
the system performs the task better than a trivial baseline.* Dimensionality is only
interesting in a regime that computes. This is deeper than D014's normalization bug: that one
made us measure a real thing in a dead regime; this one means we were not measuring computation
at all.

*How it surfaced:* fixing D029's task generator, which required checking whether errors were
sane — they weren't, in-distribution either. D029 was correct and still needed; it just was not
the binding problem.

### D031 — The literature says our D030 tension is known, and that H1 may be asking a question already answered "no"
**2026-07-16 · Accepted** (findings) · **Open** (what to do about it)
Targeted search on spiking-reservoir parameter space, prompted by the run of surprises.

**1. The gain tension is Dambre et al.'s memory–nonlinearity tradeoff.** Mediated by input
scaling; task-dependent optimum spanning **~100x**; memory tasks want low scaling, nonlinear
tasks want high. **Our 0.1 -> 10 (D030) is a rediscovery of this curve.** Our task is nonlinear,
so high gain winning is *expected*. Reassuring: the space is mapped; we were not thrashing.

**2. Total capacity is bounded by N and equals it under fading memory** (Dambre 2012).
**Connectivity cannot raise the ceiling — only determine how much is used.** Reframes our
density->PR finding: connectivity **wastes capacity** rather than **creating dimensionality**.
Coherent with Frank's "more parameters -> more capacity" (N is the parameter), but it means
wiring *reallocates*.

**3. The serious one: total IPC correlates POORLY with task-specific performance** (Hülser et
al.). What predicts performance is the **decomposition** of capacity across basis functions,
weighted by task requirements — not any single scalar. **This is a strong prior against H1 as
operationalized** (D002/D016: PR as the measure). The field has tested "does a scalar
dimensionality measure predict performance" and found it wanting. **D028's wobble (PR predicts
in the variance channel, anti-predicts in the mean channel) now looks less like our bug and
more like this known phenomenon.**

**4. A concrete fix for the D030 tension:** adaptive E/I balance control boosts RC performance
across input scaling (arXiv:2504.12480). At our useful gain (~10) the network **saturates**
(activity 0.935, PR responsiveness 6%). `ei_split` exists and is **unused**. E/I balance may
**dissolve** the tension rather than force a choice between computing and having a live PR axis.
**Try this before concluding E9's premise fails.**

**What this opens (not yet decided).** If a scalar dimensionality measure cannot predict
performance, the sharper — and more novel — question may not be "does dimensionality predict
generalization" (largely answered, no) but **"does SELECTION ALLOCATE capacity toward
generalizable functions?"** That is E9 with an **IPC decomposition** as the measure instead of
PR. It keeps the evolutionary novelty (the literature still has no selection), uses the
field's own validated instrument, and sidesteps the objection that our measure is known not to
work. Cost: IPC is EXPENSIVE (D025 tiers it as per-population, not per-individual). Requires
thought before committing.
*Credit:* PJM's call for the search — the second time this instinct has caught something two
sessions of reasoning missed (cf. D014).

### D032 — REFRAME: the substrate separates quantities Frank fused; the model becomes an evolvable spiking network with W as genome
**2026-07-16 · Accepted** · spec: `FRAMING.md` · supersedes the reservoir approach (D021/D023 revised)
*Credit: PJM.* The governing insight: **Frank is thinking more abstractly than his words let
on.** Substrate vocabulary was leading us astray — including me, repeatedly. Default hypothesis
**H0: the process is substrate-independent and the challenge is ours, to find the mapping.**
H1 (spiking genuinely does not instantiate it) is reachable only *after* H0 is honestly
attempted. We have already mistaken a mapping error for a property of nature once (D030).

**Frank's claim, substrate-free:** a system has adjustable DOF; an optimizer tunes them against
a finite sample of challenges; at DOF ≈ sample the fit is exact and brittle; at DOF >> sample,
many equivalent fits exist and the optimizer's implicit bias selects smooth ones.

**The conflation this exposes.** Frank's "more parameters → more dimensionality → better
generalization" fuses two quantities the ML literature separates: **P** (parameter count,
double descent's x-axis) and **D** (effective capacity — Dambre's bound, RMT `edof`). In
typical ML networks both scale with width, so they are **confounded by construction** and you
cannot tell which one double descent is about.

**Why spiking is the right instrument (not an exotic detour).** In a recurrent spiking net the
two come apart **~100:1**: P = evolvable synapses ≈ p·N² (~100,000 at N=1000, p=0.1) while
D ≤ N = 1000 (Dambre). **The substrate separates the quantities Frank fused**, turning an
ambiguity in his theory into an experiment. *And it returns to his own substrate:* a GRN with G
genes has capacity ≤ G but up to G² connections — **the same separation exists in Frank's own
model**, invisible only because nobody looked through the capacity lens. So the contribution is
**a structural ambiguity in the theory that our substrate makes measurable** — not "spiking is
different," and not out-Franking Frank on his own ground.

**The experiment (three rival predictions, three independent knobs):**
- **H_param:** threshold at P ≈ n_env (p·N² ≈ n_env) — Frank's literal words
- **H_capacity:** threshold at N ≈ n_env — Dambre's bound
- **H_realized:** threshold at PR ≈ n_env — our D002/D016 operationalization
Knobs: **p** sets P (evolvable) · **N** sets D_max (experimental arm) · connectivity/gain set
realized PR. Concrete: N=100, n_env=50, sweep p 0.005→0.5 (P: ~50 → ~5,000) with D_max fixed
at 2× n_env. A peak as p crosses ~0.005 ⇒ H_param; no peak ⇒ H_capacity; peak tracking PR ⇒
H_realized.

**Model consequences:**
1. **W is the genome** — Frank's parameters are regulatory connections; a reservoir freezes
   them as architecture. This single change makes the model able to answer the question.
   **Spiking is retained** (D014: rate-network intuitions demonstrably fail here; and the
   P/D separation is a spiking property).
2. **No trained readout.** Input and output neurons; phenotype = output response; selection
   acts on the whole network. **Dissolves the entire D026/D027/D028 "which channel does fitness
   read?" tangle** — there is no separate learned component to disagree about.
3. **Density becomes Frank's x-axis literally** — Figure 1 with regulatory connections on it,
   which the reservoir structurally could not provide.
4. **Scale inverts: N ≈ 100, not 1000.** The reservoir needed a big random feature pool; an
   evolvable network with no readout does not. Threshold crossings land inside a natural
   density range; simulation gets much cheaper.
5. **Measure P, D_max, PR separately, always.** Their dissociation is the point.
6. **The baseline gate (D030) comes with us.**

**What carries over:** provenance, metrics battery + spectrum storage (D025), `baseline.py`,
the analysis pipeline, `tasks.py`, the decision log, and every method lesson (log-transform
heavy-tailed outcomes, disconnected-network control, commit-before-reg). **The infrastructure
was the bulk of the work and it is model-agnostic.** What we lose is `reservoir.py`'s streaming
machinery and the readout stack — largely workarounds for problems this design does not have.

**Literature position (D031 search + neuroevolution search).** Three-way gap is real:
evolvability theory (Wagner, Kouvaris, Watson, Frank) has selection + theory, no spiking;
spiking-dimensionality (Recanatesi, Litwin-Kumar) has spiking, no selection; neuroevolution of
SNNs (NeuEvo PNAS 2023; NEAT-SNN; **ELSM** — multi-objective Evolutionary Liquid State Machine
with small-world + criticality objectives, 97-98% on N/MNIST) has spiking + selection but is
**entirely engineering** — benchmark accuracy, no theory question. **ELSM is methodologically
almost exactly what we were about to build; the difference is purpose.**
*Honest risk:* an empty intersection may be empty because neither community wants it —
evolutionary biologists do not model spiking nets; neuroevolution reviewers want accuracy.
**This is a positioning problem, and the resolution is venue: ALife / complex systems** (the
group's actual home; cf. Kouvaris in PLOS CB, Watson & Szathmáry in TREE), where "evolve a
system, ask a theory question about evolvability" is native.
*Practical gain:* methods are mature — NEAT's direct encoding with historical markings enables
meaningful crossover, and speciation protects innovation, which addresses the "can 100
individuals search 100,000 weights?" worry.

**Retrospect, not regret.** The reservoir was chosen to answer "can a reservoir show double
descent." The question turned out to be "what does overparameterization mean in an evolving
system." D014, D026, D030 were all the instrument saying *I am not built for this* — and the
tire-kicking is what produced the clarity. It clarified the questions, the parameters, and
forced the reckoning with the literature. That was its job.

### D033 — D030's tension DISSOLVED; and the reservoir compresses in the mean channel, expands only in the variance channel
**2026-07-16 · Accepted** · closes D030's open risk
Baseline-gated T0 (N=300, 135 conditions) result:
- **baseline (raw input) test NMSE = 0.217**; reservoir **skill median 1.15, max 1.77**;
  **79/135 conditions beat baseline**. The gate works — every top-ranked point is gain=10,
  exactly the regime the old PR-only objective rejected.
- **The D030 tension is GONE.** At gain=10: **skill 1.448 AND pr_rel 49%** simultaneously —
  a live dimensionality axis *and* a computing network. My "the useful regime may have no PR
  axis" warning came from the N=120 **smoke** run and was wrong at N=300. Lesson: do not raise
  structural alarms from smoke-preset numbers.
- **The reservoir's advantage is MODEST** (median skill 1.15). For a task that is near-linear
  around the origin, the reservoir contributes some nonlinearity and little else.

**The finding that outlives the model.** At a *validated* operating point, with K=20 inputs:
**PR_mean ≈ 7.4 — the mean channel COMPRESSES 20 dimensions into ~7.** Meanwhile
**PR_var ≈ 27 — the variance channel EXPANDS beyond the input dimension.**
A reservoir's entire purpose is to expand inputs into a higher-dimensional space where the task
becomes linearly separable. **Ours compresses, in the channel we had been reading, at a
validated operating point.** Expansion happens only in the fluctuations.
*This independently corroborates D028's variance-channel story from a different direction, and
retroactively explains why PR_mean anti-predicted generalization: we were measuring the
dimensionality of a lossy compression.*
*Carry into the new model (D032):* check whether the phenotype channel we select on actually
expands or compresses relative to input dimensionality. "Does the representation expand?" is a
cheap, decisive diagnostic we did not have and should have.

**Does not disturb D032.** The reason to leave the reservoir was never "it does not work" — it
is that a reservoir **freezes W**, so it cannot test a claim about regulatory connections being
the evolved parameters. We now leave it knowing it works, modestly, at a validated operating
point: a principled exit rather than a defeat.
*Optional, not queued:* re-running the feature check at gain=10 would say whether D028's
variance-channel result survives at a valid operating point. Interesting, but the same question
gets asked with better tools in the new model.

### D034 — The implicit-bias question does NOT survive the literature; FRAMING.md stands unchanged
**2026-07-16 · Accepted** (a killed hypothesis, logged because negatives matter)
*Prompted by PJM: "test my intuitions against what's been published before we incorporate it."*
I had proposed that Frank's load-bearing assumption is unexamined — that he imports double
descent from ML without checking that **selection** possesses the implicit smoothness bias the
second descent depends on, and that "nobody knows" whether it does.
**That is wrong.** The Louis group (Oxford) has built both ends of the bridge:
- **Dingle, Camargo & Louis (2018, Nat Comms):** input–output maps are strongly biased toward
  simple outputs, P(x) ≲ 2^(−aK̃(x)−b). Shown for **GRN concentration profiles**, RNA, proteins,
  biomorphs.
- **Valle-Pérez, Camargo & Louis:** deep learning generalizes *because* the parameter-function
  map is biased toward simple functions — same framework, applied to NNs.
- **Johnston et al. (2022, PNAS):** symmetry and simplicity emerge from the algorithmic nature
  of evolution.
Moreover **Frank's own Wilson citation IS the volume argument** ("simple solutions occupy larger
regions of parameter space; learning dynamics find big regions") — precisely what this framework
formalizes and extends to GP maps. **His assumption is supported, not unexamined.**
*Decision:* **do not build the project around implicit bias.** `FRAMING.md` is unchanged.
*What survives, better positioned:* the Louis group works in **genotype space** (parameter count,
phenotype *complexity*). They do not measure **effective dimensionality** (capacity, PR, Dambre's
bound). Their axis is output complexity; ours is representational dimensionality. **Orthogonal.**
The P-vs-D question is untouched.
*Positioning gain:* this is the actual ML↔evolution bridge literature — where Frank's argument
lives, and the natural readership for "what does overparameterization mean in an evolving
system." More apt than neuroevolution engineering or spiking-dimensionality work.
*Trap noted:* simplicity bias implies *more parameters → larger neutral sets for simple
phenotypes → stronger simplicity bias*, a testable mechanism for Frank's chain — but it is the
Louis group's home turf. Pursuing it is out-Franking Frank in a new costume.
*Method note:* this is the **third** time a PJM-requested literature search has overturned my
reasoning (cf. D014 normalization, D031 memory–nonlinearity). The pattern is now unambiguous:
**search before building, not after.**

### D035 — Correction: the P/D separation does NOT justify spiking; the variance channel does
**2026-07-16 · Accepted** · corrects `FRAMING.md` §3 (written same day)
**The overclaim.** `FRAMING.md` justified the spiking substrate on the grounds that it separates
P (≈p·N² parameters) from D (≤N capacity) by ~100:1. **True but not distinguishing:** *any*
recurrent network with N units has ~N² weights and ~N state variables. A **rate** network at
N=100 gives the identical separation. **P/D dissociation is a property of RECURRENCE, not of
spiking.** It is *the question*, not the reason for the substrate. Caught by stress-testing on
PJM's prompt ("remind me why spiking is the tool for the job") rather than reciting.

**The actual justification — and it is our own finding.** D028 + D033: **D is
channel-dependent.** At a validated operating point (K=20): **PR_mean ≈ 7.4 (the mean channel
COMPRESSES); PR_var ≈ 27 (the variance channel EXPANDS)** — and PR_var *predicted*
generalization while PR_mean *anti-predicted* it. So "the dimensionality of the representation"
is not one number: it depends on the channel, and the choice **flips the sign** of the
relationship to generalization. **Frank's framework has no notion of a channel** — regulatory
dimensionality is a scalar. Our substrate forces *which dimensionality, measured on what?*
**This is intrinsic to spiking as a point process:** irregularity is a *coding channel*, not
imposed noise. A rate network's variance is something you add; a spiking network's irregularity
*is* the code.

**Supporting (weaker):** Frank explicitly names "neural wiring" and his rattlesnake/snakeness
example is neural; D014 shows rate-network heuristics (ρ≈1) are inert here, so the substrate is
not cosmetic.
**Strategic, not scientific:** a rate GRN is Wagner's turf. Worth weighing; not evidence.
**Costs of staying spiking:** speed, simplicity, and clean theory — **Dambre's bound is proved
for input-driven fading-memory systems, NOT for spiking with reset.** Our use of it is an
extrapolation and is now flagged as such in FRAMING.md.

**Net:** the case for spiking is **one real finding of ours + one strategic consideration** —
thinner than the P/D argument implied, but genuine. Defend it on the variance channel.

### D036 — Ontology: the phenotype IS the behavior; fitness and metrics are functionals of it
**2026-07-16 · Accepted** · *Credit: PJM* · adds `FRAMING.md` §2b–2c; retires the scoring half of `tasks.py`
**My error:** I spent three exchanges asking "which summary is the phenotype — mean rate? rate
vector?" **That question is malformed.** The phenotype is the network's **dynamic behavior**
under an environment. Mean rate, variance, spectrum, PR are **measurements of** it, not
candidates for being it — like asking whether an organism's phenotype is its weight or its
height.

**The three-way split I had fused:**
- **Phenotype** — the behavior itself.
- **Fitness** — a functional of (behavior × environment); what **selection** reads. **Our design
  choice**, defensible on biological grounds.
- **Metrics** — other functionals; what **we** read. Measurement.

**This dissolves the channel tangle.** "Which channel?" was two questions at once: *which
functional does fitness read* (design) and *which functional's dimensionality predicts
generalization* (experiment). D026/D027/D028 tried to answer both under one label, which is why
they never resolved.

**It also opens a sharper question than FRAMING §5 states.** If the phenotype is behavior, then
**behavior has a dimensionality too**, not just the internal state. So "what is D?" is not only
*which internal channel* but **internal representation vs expressed behavior** — and Frank's
"regulatory dimensionality" is ambiguous between them. Our substrate can measure both.

**Task triage (PJM's challenge: "is that task still ours?").** `anisotropic_regression` fused an
**environment generator** with a **scoring rule**:
- **Survives:** the anisotropic **environment structure** (some directions well-sampled, others
  barely) — Schaeffer's geometry, which **Frank explicitly invokes**; substrate-independent.
- **Dies:** the **scalar tanh target** — it existed only because a linear readout emits a number.
  A reservoir artifact. (Novel-direction construction already dead: D029.)
- **Replacement:** environments demand a **response profile** (expression pattern); fitness =
  distance between expressed behavior and demanded profile. Frank: *"Phenotypic responses are the
  outputs. The fitness landscape mirrors the training-error surface..."*
- **Two payoffs:** D029 becomes natural (novel-but-related = a new target profile from the same
  class = snakeness); and **constraints = n_env × d**, a second independent knob on the
  interpolation threshold — which the P-vs-D design needs.

**Still open (decide, do not default):** how many output neurons **d**, and is d evolvable? It is
`M` from the reservoir design in disguise — capacity as a gene.

### D037 — Minimal evolvable model built; density sweeps P as designed; ACTIVITY CONFOUND flagged
**2026-07-16 · Accepted** (build) · **Open** (the confound)
`ddescent/evonet.py` + `tasks.profile_environments`. W is the genome; no trained readout;
input neurons receive the environment; output neurons' behavior is the phenotype; fitness reads
output **rates** (a design choice per D036, defensible: expression level is the trait); metrics
read whatever channel we like on the internal state.

**It lands where designed.** N=100, d=10, n_env=50 → **constraints = 500**. Density sweeps
**P = |W|**: 0.005 → 50 (**0.1x**), 0.05 → 495 (**0.99x — the threshold**), 0.5 → 4950 (**9.9x**).
**Frank's Figure 1 x-axis made of regulatory connections, with the interpolation threshold in
the middle of a natural density range.** Cost 1.84 s/genome → pop 50 x 100 gens ≈ 25 min on 6
workers. Feasible.

**d is a NICHE property, not a gene.** The environment demands a response of a given shape;
letting the genome set d would let the organism choose what it is asked, and would let evolution
move its own interpolation threshold (constraints = n_env x d) out from under the measurement.
Also likely degenerate: more outputs = more constraints, so selection would shrink d to the
minimum. **Fixed per arm; varied across arms as the second threshold knob.**
*Genuinely open (topology, not capacity):* should the network choose WHICH neurons express the
phenotype, with d fixed? That is developmental and biologically real.

**THE CONFOUND (open).** Fixed per-synapse weights mean **density IS coupling** (D014) — so
sweeping density sweeps **activity** too: output rate 0.044 at density 0.005 vs 2.124 at 0.5.
At the underparameterized end the network is **nearly silent** and cannot express anything.
A naive density sweep would confound "parameter count" with "is the network alive" — **the D030
mistake in a new model**.
*Plausible resolution, and a real prediction:* **W is now the genome, so evolution can
compensate** — a sparse network can evolve larger weights to reach viable activity. The confound
may dissolve under selection in a way it never could with random W. **Hypothesis, not
assumption.**
*Consequence — gate order changes:* **baseline gate PER DENSITY ARM comes first**, and doubles
as the activity check. If low-density arms cannot beat a trivial baseline even after evolution,
the double-descent sweep has **no left half** and P must be varied some other way.

### D038 — Dale's law with EVOLVABLE per-neuron identity; regulatory motifs must EMERGE, not be bolted on
**2026-07-16 · Accepted** · *Credit: PJM* · corrects an error of mine about our own code
**My error, twice over.** I claimed our network "has no regulatory mode" because "every synapse
is additive — neurons drive each other." **Wrong:** our weights are *signed* — 52% of synapses
are inhibitory. There is plenty of inhibition. I then proposed bolting on shunting (divisive)
inhibition as a "regulatory mode." **PJM rejected the framing:** regulatory motifs should
**emerge under selection**, not be installed by the experimenter. The architecture's job is to
*permit* them.

**The real limitation, which PJM located precisely: no neuron-level identity.** Measured on our
own genome: **97/100 neurons had BOTH excitatory and inhibitory outputs** — no Dale's law. A
cell excites some targets and inhibits others simultaneously, which is biologically impossible
and, decisively, means **no neuron has a coherent role**. Regulatory motifs — feedforward
inhibition, disinhibition, gain control — all require a cell whose *identity* is inhibitory.
The architecture could not host the thing the theory is about. **It was not absence of
inhibition; it was absence of identity.**

**The fix (PJM's design).** Genome becomes two gene groups:
- `signs` : (N,) in {+1,-1} — each **neuron** is E or I; **all** its outgoing synapses carry
  that sign (Dale's law). **Mutable**: a neuron can *evolve into* an inhibitory cell.
- `mag` : (N,N) >= 0 — per-synapse magnitudes; zeros = absent synapses.
`mutate()` jitters magnitudes and rarely flips neuron signs (a large phenotypic jump).
*Verified:* Dale violations **97/100 → 0**; mutation flips identities (4 neurons E→I in one
round; exc fraction 0.80 → 0.78) with Dale's law intact. Activates `ei_split`, unused since
`connectivity.py` was written.

**What this buys.** We do NOT install regulation. We make the architecture **capable** of it and
ask whether selection builds it. **Whether regulatory motifs emerge — and whether their
emergence coincides with the second descent — becomes the finding, not the assumption.**
Connects to PJM's framing that "more regulatory dimensionality" means *a greater proportion of
the network in regulatory roles*, with the remainder doing basic encoding/memorization — and to
high-cost N expansion as one way to *afford* a regulatory subpopulation.

**Open caveat (flagged, NOT acted on — per PJM's "don't bolt things on").** Our inhibition is
**subtractive** (`I_syn += w`, w<0); textbook gain control is **divisive** (shunting). The
strongest form of regulation may thus be unavailable. But subtractive inhibition in a
fluctuation-driven spiking network **does** modulate effective gain near threshold, so it may
suffice. **Test after the E/I change; do not add machinery preemptively.**

**Operationalizing "regulatory fraction" (needed before it is a measurement, not an intuition):**
perturb neuron i, measure whether j's response **offset** shifts (driving/encoding) or its
**gain** shifts (regulatory). Regulatory fraction falls out without hand-labeling.

### D039 — Do NOT add shunting inhibition: the literature says it would not do what I claimed
**2026-07-16 · Accepted** · *prompted by PJM's call for a targeted search before deciding*
**My claim was backwards.** I said "textbook gain control is divisive (shunting)" and floated
adding shunting synapses so the network could regulate.
**Holt & Koch (1997, Neural Comput 9:1001):** *shunting inhibition has a SUBTRACTIVE effect on
firing rates*, not a divisive one. Averaged over interspike intervals the spiking mechanism
clamps somatic V well above rest, so current through the shunt is ~independent of firing rate.
Shunting IS divisive on subthreshold EPSPs — everyone assumed that carried to rates; **it does
not.** Adding shunting would have installed machinery that does not deliver the mechanism.

**What actually produces divisive gain control: NOISE, and CIRCUITS.**
- Chance, Abbott & Reyes (2002); Prescott & De Koninck (2003, PNAS 100:2076): divisive
  modulation of firing rate **requires synaptic noise** to smooth the rate–depolarization
  relation. Tonic conductance increases are subtractive; **fluctuation-based** conductance
  increases modulate gain **divisively**. Dendritic saturation enhances it further.
- Gain modulation is better described as **input-gain control when mutual inhibition between
  subpopulations** is present — i.e. a **circuit-level** mechanism, not a synapse type.

**Decision: no shunting.** Divisive regulation **emerges** from the fluctuation-driven balanced
regime plus circuit motifs — exactly what selection can discover with machinery we already have
(D038's Dale genome). **PJM's "don't bolt things on" was right, and the literature says the
bolt-on would not have worked.**

**But it yields an actionable precondition.** Our config has **`noise_sigma = 0.0`** and a tonic
`bias = 0.4` — the *tonic-drive* regime, where inhibition is purely subtractive and gain control
is **unavailable**. With Dale's law in place, a balanced E/I network **self-generates
fluctuations** (van Vreeswijk–Sompolinsky balanced state). So this is a **parameter-regime
question, not an architecture one**: can our network reach a balanced, fluctuation-driven state?
**That is a precondition for regulation to emerge at all**, and it is testable. Add to gates.

### D040 — Measuring "regulatory": a three-stage scheme (PJM's design + one imported criterion)
**2026-07-16 · Accepted (design)** · **Open (implementation)**
**PJM's objection to per-neuron labels:** in real networks regulatoriness is not a per-cell
property — it shows up in **subspaces of activity** or **phase relationships**. Correct.
**My proposal and its flaw:** I offered Kaufman et al. (2014) output-potent vs output-null
subspaces. **PJM: "does your approach simply assume anything output-null must be regulatory?"**
**It does, and that is wrong.** Null is **geometric** — it says activity does not reach the
output, not *why*. Null activity may be regulatory, **preparatory/memory** (which is what
Kaufman's actually IS, in motor cortex), idle, or noise. I reached for a known population-level
method without checking its criterion matched our concept.

**PJM's fix — null as a SCREEN, not a verdict.** Use potent/null to identify **candidates** and
the **graded extent** of possible regulatory behavior per neuron; then use **functional
contribution to task performance** to separate real regulators from idle activity.
**Why it works: RECURRENCE.** Output-null is null only *instantaneously*; in a recurrent network
null activity at t feeds back and shapes what is potent at t+1. So "null but functionally
important" is a coherent, measurable category — impossible in a feedforward net. And
regulatoriness becomes a **ratio** (a neuron's influence via the null path vs its direct drive)
— graded, not categorical, which is what biology looks like.

**Remaining conflation, and the third stage.** Null-but-functional could be **memory** (storing
for later readout — literally Kaufman's finding) or **regulation** (changing how others respond).
Distinguish them with the criterion the inhibition literature (D039) makes operational:
**subtractive = shifts the f–I curve (offset) = driving; divisive = changes its slope (gain) =
regulating.** Perturb along a state-space direction; ask whether the input→output map **shifts**
or **changes slope**.

**The scheme:**
1. **potent vs null** → candidates, graded per neuron *(PJM's screen)*
2. **functional contribution** → active vs idle *(PJM's filter)*
3. **gain vs offset** → regulation vs memory *(criterion imported from D039's literature)*
Each stage does one job; none assumes geometry implies mechanism.
*Ties to D039:* stage 3 needs the fluctuation-driven regime. In the tonic regime stages 1–2
might find null-functional activity that is **all memory, no regulation** — itself a finding,
not a failure.
*Deferred:* phase relationships / coherence between subpopulations — the next layer, after the
subspace version works.

### D041 — Rappeport & Nitzan (2025) built our framework, threaten Frank, and leave exactly our gap
**2026-07-17 · Accepted** · *found by PJM's "read it before building"*
**They built our design.** Genotypes = **input–output maps** (cues → phenotypes); fitness =
distance to a ground-truth map; **complexity q = tunable parameters in the environment–phenotype
map**; environmental complexity q* = complexity of φ*. Frank's mapping, made formal.

**Their result threatens Frank directly.** **Implicit regularization emerges from the replicator
equation itself** — no external cost — and **selected complexity converges to environmental
complexity** (⟨q∞⟩ ≈ q*). Mechanism: the **Occam factor** — complex classes have the highest
per-timestep fitness but collapse onto a *different* best member each generation, so their class
growth rate is suboptimal ("**overfitness**"). **Excess complexity is selected against.** If this
generalises, **evolution never enters the overparameterized regime and Frank's second descent is
biologically irrelevant.**

**THE GAP.** Their q ∈ [1,9] against T = 1000 cues → **q/n ≈ 0.009**: three orders of magnitude
**below** the interpolation threshold, wholly inside the classical regime. **Frank's claim lives
at q ≈ n and beyond; they never go there.** Not evidence against double descent — evidence from
where it is undefined. **And no mutation** (explicit; forced by the isomorphism, which breaks
under mutation — yet mutation is where evolution's implicit bias would come from).

**The project, sharply stated:**
> **Does the Occam factor keep penalizing complexity PAST the interpolation threshold, or does a
> second descent appear?** R&N-extended ⇒ Frank is wrong, evolution halts at q*. Frank ⇒ beyond
> q ≈ n generalization recovers. **Nobody has looked: nobody has run evolutionary dynamics into
> the overparameterized regime.**
Our density knob sweeps P from 0.1× to 9.9× the constraint count — **exactly their blind spot**
(D037).
**Risks:** we are in their slipstream (same framework, adjacent question, possibly running it);
and their NN appendix shows the trend, so **none of this requires spiking** — see D042.
**Also recorded:** Kouvaris et al. (2017) already did "learning theory → evolvability", so
**Frank's real novelty is double descent specifically** — narrower than his framing suggests, and
exactly what we test.

### D042 — "Why spiking", reframed: adjudicating competing theories in a substrate where parameters are NOT free
**2026-07-17 · Accepted** · *Credit: PJM* · strengthens D035
**PJM's framing:** *"Biology has selected spiking networks. There are competing ideas for how
parameterization relates to learning. How do these ideas play out in spiking networks?"*
**Why it helps:** it reframes us from **championing** Frank to **adjudicating** between Frank and
R&N — two theories making **opposite** predictions in the overparameterized regime. It makes the
substrate a **scope condition**, not a gimmick, and claims no theoretical privilege for spikes.

**And it yields a third, better plank — from PJM's earlier insight.** *Both competing theories were
developed on substrates where **parameters are dynamically inert**.* Frank's double descent comes
from feedforward ML (adding width destabilises nothing). R&N's Occam factor comes from **3×3 linear
maps and 1-hidden-layer feedforward nets** (a parameter is just another free knob). **In a
recurrent spiking network, parameters are NOT free**: more synapses → more coupling → synchrony,
saturation, pathology — which can destroy the expressiveness the parameters were meant to buy.
**That is a scope condition both theories are silent about, and every biological substrate
violates it.**
> **Frank: excess parameters buy generalization via implicit bias. R&N: excess parameters are
> penalized via the Occam factor. Both assume parameters are dynamically inert. Does either
> survive where they are not?**
*This plank is better than D035's because it applies to GRNs too* — spiking merely makes the
dynamics measurable. It also revives PJM's earlier hypothesis: a second descent here may require
the added connections to be **organized** (hierarchy/regulation), not merely numerous.

**The honest ledger (three planks, not four):**
1. **Parameters are dynamically inert in both theories' substrates; not in ours.** (strongest)
2. **D is channel-dependent** — the variance channel (D035). Ours, novel, spiking-specific.
3. Frank explicitly names **"neural wiring"**; his rattlesnake/snakeness example is neural.
*Weak:* Frank's PRIMARY substrate is the GRN. "Then test it in a GRN" is a fair reviewer
question, and part of our answer is **strategic** (Wagner's turf), not scientific. Say so plainly
rather than dress it up.

### D043 — Friedlander/Alon (2015): bow-ties evolve only under rank-deficient goals + product-rule mutations. Two flaws in our model.
**2026-07-17 · Accepted**
Friedlander, Mayo, Tlusty & Alon (2015), *Evolution of bow-tie architectures in biology* (arXiv:1404.7715).
**Finding:** bow-ties evolve spontaneously iff **(i) the goal is RANK DEFICIENT** (rank = minimal
number of input features the outputs depend on) **and (ii) mutations follow a PRODUCT rule**
(mutated element *multiplied* by a random number), not a sum rule. **The waist width EQUALS the
goal rank.** Full-rank goals → **no bow-tie ever**. Sum-rule mutations → **94–97% of runs fail**
to reach a waist matching the rank. Robust to ~1% noise; holds in a nonlinear (retina) model
(75% product vs 45% sum). Population 100, tournament selection, feedforward layered nets.

**FLAW 1 — our mutation operator is wrong.** `evonet.mutate()` adds Gaussian noise = **sum rule**,
the operator that reliably PREVENTS bow-ties. **Switch to product-rule:** `mag *= N(1, σ)`.
**FLAW 2 — our task is full-rank.** `tasks.profile_environments` builds E→profile from a random
(K×d) matrix — generically **full rank** ⇒ **a bow-tie is mathematically impossible**
(rank(AB) ≤ min(rank A, rank B)). We designed a task that forbids the thing we want to observe.

**Structural problem (dissolved by D044).** Friedlander's waist is a **layer** in a **feedforward**
net; ours is **recurrent, layerless**, so "where is the waist?" was undefined. See D044.

**The opening.** R&N: selected complexity q ≈ q*. Friedlander: waist = rank r. **These are the same
result in different clothing** — the system's dimensionality converges on the environment's —
reached by two independent mechanisms (Occam factor; product-rule mutational bias). Strong
convergent evidence, and it means our "waist tracks q*" prediction is **already established,
twice**. **But both STOP THERE.** Neither asks what excess parameters do once the system already
matches the environment. **That is our question.**

### D044 — The waist is a point in the EVOLUTIONARY TRAJECTORY, not (only) a layer
**2026-07-17 · Accepted** · *Credit: PJM* · corrects my conflation
**My error:** I quoted Frank's hourglass ("compress, which regulatory networks then expand") and
told PJM *"that is exactly your two-level structure, in his words."* **It was not.** Frank and
Friedlander describe an **anatomical** waist: a narrow layer in a feedforward path — a place in
the **architecture**. PJM's waist is a **point in the evolutionary trajectory**: a location on the
parameter axis where the *character of what evolution builds* changes — **encoding before,
regulation after** — a place in the network's **history**. Different claims; I attributed mine to him.

**PJM's version dissolves D043's structural problem.** A trajectory waist needs **no layers**. It
needs only the network's *function* to change character as parameters grow. Our recurrent
substrate can host that. My objection was against my own concept.

**And it gives the interpolation threshold a MECHANISM.** Standard double descent puts the peak
where parameters ≈ data — an accounting fact with no story. **PJM's version: the peak is where
ENCODING CAPACITY SATURATES.** The network has enough parameters to capture the environment's
invariances; further *encoding* parameters can only memorize. Past that, parameters are useful
only if they do something **else**: regulate. **That is why there is a second descent — the added
parameters switch function.**

**Trajectory and anatomical waists are the same event from two angles** (PJM, agreed): if the
transition is "stop improving the encoder, start building the expander," the architecture you end
up with **is** hourglass-shaped. Friedlander evolved networks that build the encoder and stop;
**nobody has asked what happens after.**

**Prediction that distinguishes this from standard double descent:** the peak sits where encoding
saturates — set by **r, the environment's rank** — **not** at parameters ≈ **n**. *Vary r and n
independently; see which moves the peak.*

### D045 — Convergence is LEVEL-RELATIVE; flat environments forbid the second descent by construction
**2026-07-17 · Accepted** · *Credit: PJM* · re-diagnoses both rivals; forces a task redesign
**PJM:** *"at the level of encoding statistical regularities OF ONE TYPE we find convergence, but
selection pressure means there is benefit to 'leveling up' — evolving regulatory complexity that
allows the system to learn a more complex, multilayered set of regularities. The higher-level
regularities were always there; prior to the waist the system wasn't addressing them."*
**Convergence is within-level; leveling up is across-level.** So Friedlander's r and R&N's q* are
convergence onto **one type** of regularity. **No conflict with Frank** — the camps are right
about different things, which is why the literature looked contradictory.

**This re-diagnoses the rivals better than my earlier critique.** I said R&N can't see a second
descent because q/n ≈ 0.009 — true but shallow. **The real reason: their environments are FLAT.**
R&N's ground truth is a single map φ*. Friedlander's is a single matrix G. Frank's reservoir: one
input sequence, one task. **There is no higher-order structure to level up to**, so extra
parameters could never buy anything. **Their convergence results are forced by their environment
design, not discovered about evolution.**

**Damning consequence: OUR TASK IS FLAT TOO.** `profile_environments` = a single map
E → tanh(E·Q·Wc). **We would reproduce R&N exactly** and conclude the second descent doesn't
exist — having built an environment that forbids it.

**Required redesign — hierarchical environments:**
- **Level 1:** within a context, environment → response follows a regularity (rank r₁).
- **Level 2:** *which* regularity applies depends on **context**; contexts themselves have structure.
- A system encoding only level 1 converges on r₁ and stalls — as well as any single map can do
  averaged over contexts.
- **Leveling up requires detecting context and MODULATING the level-1 map = regulation.** Not more
  encoding. Different function.
⇒ the second descent becomes **mechanistically necessary**: past the waist, extra *encoding*
parameters can only memorize, but parameters that **modulate** unlock environmental structure that
was inaccessible.
*Lineage note:* Kashtan & Alon's **modularly varying goals** (same lab) established that
structured/varying goals drive modularity. "Environment structure shapes architecture" is theirs.
**Not theirs:** that the transition to a higher level **IS** the second descent.

### D046 — The two second-descents may be ONE process, described at two levels
**2026-07-17 · Accepted** · *Credit: PJM*
**PJM:** the second-descent-within-a-system and the second-descent-as-emergence-to-a-higher-level
may be **the same process framed differently**.
**How they'd be identical.** ML's account: past the threshold many solutions interpolate and
implicit bias selects a **smooth** one. But a smooth solution is **one that captures the
generating process rather than the samples** — and capturing the generating process **is**
addressing the deeper regularity. So "implicit bias finds the simple interpolant" and "the system
levels up" are **the same event, mechanistic vs functional description**.
**This is FRAMING.md's H0** (substrate-independent process; realization varies). In a feedforward
ML net, "capture the deeper regularity" is realized as a weight configuration. **In a dynamical
network it may be realizable ONLY as regulatory structure** — to make the level-1 map
context-dependent, something must **modulate** it; weights that merely add drive cannot.
**⇒ the hierarchy is not a rival theory; it is the only available IMPLEMENTATION of the same
theory in a substrate with dynamics.** That is D042's plank (parameters are not inert here)
arriving from the other direction.

**Coincidence is TESTABLE — the experiment requires measuring BOTH curves against the same
parameter axis:**
| outcome | reading |
|---|---|
| second descent appears **exactly when** regulatory motifs emerge | same process, two descriptions. Contribution: the second descent's **biological mechanism and structural signature**, which the ML account does not predict. |
| second descent **without** regulation | the ML account is complete; regulation is decoration; **our framing dies cleanly**. |
| regulation **without** second descent | regulation is doing something else; both accounts need work. |

**Honest caution.** If they are the same, our claim is about **realization**, not a new phenomenon.
Real — it gives the second descent a mechanism where "just add parameters" cannot work — but
**smaller** than "we found a new kind of double descent." Say the smaller true thing.

### D047 — The bridge: abstraction → hypothesis → construction → measurement; and the spiking answer the chain PRODUCES
**2026-07-17 · Accepted** · spec: `BRIDGE.md` · *prompted by PJM: close the gaps and the "why spiking" answers will fall out*
Working the chain concretely does two things: it yields **four hypotheses stated in quantities the
model produces**, and it locates the places where the chain **requires** the substrate — rather
than asserting that it does.

**The hypotheses (H-A..H-D).**
- **H-A** error vs **P=|W|** peaks at **P\***.
- **H-B** **P\* is set by r₁** (rank of the level-1 regularity), **not n**. ← *what distinguishes
  us from ML, which puts the peak at parameters ≈ data. Vary r₁ and n independently.*
- **H-C** past P\*, error descends **only if** modulating (not driving) structure emerges.
- **H-D** **no fluctuation-driven regime ⇒ no second descent.** ← **the spiking test.**

**Stimulus requirement that is new and does the most work: CONTEXT MUST BE INFERRED FROM HISTORY,
not signalled.** If context arrives as an explicit channel, detecting it is a *switch*, not
regulation, and the mechanism is bypassed. If it must be inferred from recent input statistics,
the system must **integrate over time** and then **modulate** the level-1 map. **⇒ the environment
needs TWO TIMESCALES** (fast stimuli, slow context drift). *This is the first point where the chain
requires dynamics — and it is exactly why R&N's static φᵢ and Friedlander's feedforward G could not
have found this even with hierarchical goals.*

**WHY SPIKING — the answer the chain produces (not a defence):**
- **4a. Regulation-as-gain-control is dynamical, and free only here.** Holt & Koch: shunting is
  *subtractive* on rates. Divisive gain modulation **requires noise**; tonic conductance is merely
  subtractive; and it is **circuit-level** (mutual inhibition between subpopulations). So in a
  **balanced spiking network gain modulation is AVAILABLE FOR SELECTION TO FIND, with no new
  machinery**. In a deterministic rate model you must **bolt in** multiplicative interactions —
  violating D038 and making the result an artifact of the experimenter. **⇒ spiking is where "did
  evolution invent regulation?" is a real question rather than a modelling choice.**
- **4b. H-D is an ON/OFF SWITCH FOR THE MECHANISM, INSIDE ONE SUBSTRATE — the strongest thing we
  have.** Same network, same genome, same task; two arms: **tonic** (inhibition subtractive → gain
  control unavailable → predict **no** second descent) vs **balanced** (fluctuation-driven →
  divisive gain available → predict second descent). **Nothing changes but the dynamical regime.**
  A **within-substrate control**, not a cross-substrate comparison. It converts "why spiking?" from
  positioning into an experimental manipulation. **No feedforward or static-map model has this knob.**
- **4c. Timescale separation is intrinsic** (τ_m, τ_syn, τ_r, refractoriness): the environment's
  hierarchy has a native substrate. *Weaker — a rate model with two time constants does much of it.*

**Honest ledger:** 4b strong (internal, decisive); 4a strong but **contingent on Gate C** (is the
balanced regime reachable?); 4c a difference of degree. **D035's variance channel is now the
WEAKEST plank, not the argument.**

**Measurement discipline:** all quantities on **one P axis** — P, generalization error, regulatory
fraction (D040's three stages), **fluctuation index** (*which arm are we actually in?*),
context-inference accuracy, spectrum (D025). **Everything gated on baseline skill first (D030).**
**H-C is the two-curve test** (D046): do the second descent and regulatory emergence **coincide**?
All three outcomes informative — including "descent without regulation ⇒ our framing dies cleanly."

**Build order:** B1 (product mutations) → B2/B3 (hierarchical, rank-deficient, two-timescale
environments) → **Gate C** (*without a reachable balanced regime, H-D has no treatment arm and
4a's mechanism does not exist*) → `evolve.py` → Gate A → Gate B → the two-curve experiment.

### D048 — H-E: variance is where the SECOND-LEVEL regularity lives; the regulatory layer learns it and feeds back
**2026-07-17 · Accepted (hypothesis + design principle)** · *Credit: PJM* · supersedes the "variance channel" plank of D035
**PJM's correction first.** Variance coding in spiking populations is **decades-old background,
not our contribution**. D028/D033 ("variance expands while mean compresses") is a *rediscovery* in
a retired model. Using it as a **justification** for the substrate was dressing prior art as an
asset. **The responsible move is to commit to a falsifiable hypothesis about it** — which converts
a weak plank into something that can be wrong.

**PJM's framing (H-E).** Before the waist the network learns to encode statistical regularities and
**saturates**; it increasingly stores/processes information via **variance**; it transitions
(possibly gradually) through the waist; **regulatory structure emerges**; **and then the increased
variance serves as a NEW "environment" with its own statistical regularities, which the regulatory
layer learns.** Because regulation is **recurrently connected** to the encoder, those higher-order
statistics **feed back** to influence encoding — improving its efficiency/expressiveness in driving
the output.

**THE MOVE THAT DOES THE WORK — and it dictates the stimulus design.**
If context is defined as **a change in stimulus STATISTICS** rather than in individual stimuli:
- **mean over a short window** → the instantaneous stimulus → **level 1**
- **variance / higher moments over a longer window** → the *distribution* stimuli are drawn from →
  **the context** → **level 2**
**The mean CANNOT carry context, because context is not in any single stimulus — it is in their
spread.** So the fluctuation channel is not a metaphorical "new environment": **it is literally
where the second-level regularity lives**, and reading it *is* the history-integration the
plant/seasons case demands (D047 Level 2(iii)).

> **DESIGN PRINCIPLE (promoted — it changes what we build): context must change stimulus
> STATISTICS (variance, correlation), NOT the stimulus mean.** If context shifted the mean, the
> encoder could detect it directly and no regulation would be needed — the same collapse as
> signalling it. Sharper than "make it hierarchical".

**Structural consequence: we are not building an hourglass.** Friedlander's bow-tie is strictly
feedforward (in → waist → out). PJM's architecture has the regulatory layer reading the encoder's
fluctuation statistics **and modulating back into it** — **a LOOP, not a bow-tie.** Loops exist
only in a recurrent substrate. **Our architecture is a two-level recurrent system in which the
second level reads the first's fluctuation statistics and controls its gain.**

**It also becomes the mechanism UNDER H-D**, unifying them: tonic arm → no fluctuations → no
variance channel → **no medium for gain modulation** → no regulation → no second descent. H-D and
H-E stop being separate claims and become one story with a switch.

**Refinement of "phase transition" (PJM: avoid the cargo).** The claim is the **role change**, not
the sharpness. Predict the role change; **measure** whether it is abrupt or a smooth crossover.
*Non-obvious prediction:* the **encoding share** of variance may **FALL** past the waist even as
total fluctuation rises — because fluctuations get conscripted into gain control. Same physical
quantity, different job.
**Order parameter:** ratio of **encoding-variance** (stimulus information carried by `X_var`) to
**regulatory-variance** (fluctuation that modulates other neurons' *gain* — D040 stage-3
gain-vs-offset). Both already specified.

**TWO HONEST PROBLEMS (flagged, not resolved).**
1. **Is this predictive coding rediscovered?** Higher levels modelling lower levels' statistics and
   feeding back is **Rao & Ballard / Friston hierarchies**. The *architecture* is theirs. **Ours
   would be:** that it **emerges under selection at a specific parameter count**, and that its
   emergence **IS the second descent**. **MUST SEARCH BEFORE BUILDING** — the standing rule has
   caught me five times (D014, D031, D034, D039, D043).
2. **"Overflow" may be the wrong story.** Two distinguishable claims: **(a)** variance *rises*
   because encoding saturates, then is exploited; **(b)** variance *always* carried context and
   regulation merely **unlocks** it. D033's PR_var↑/PR_mean↓ hints at (a) — but that was the
   retired reservoir **with no context structure at all**, so it cannot bear on this. **Predict
   (b); measure whether (a) adds to it.**

### D049 — Corrections: what "no double descent in SNNs" does and does not mean; nonlinearity is not the issue
**2026-07-17 · Accepted** · *several errors of mine, caught by PJM*
- **"Nobody has shown double descent in SNNs" — must be stated precisely.** Double descent in a
  **reservoir readout** is expected and covered: a readout is a **random-features model** (linear
  in the swept parameters), peak at M ≈ n; the spiking is **incidental**. What is unexamined:
  double descent where **the spiking network's own W is the parameter axis**, with no trained
  readout.
- **"Untrained" was my word and it was wrong.** Our model is **not untrained** — **W is optimized
  by selection**. No trained *readout* ≠ nothing trained. **Selection is the feedback loop**
  (error → fitness → reproduction → W). The parallel is exact: classical DD sweeps weights under
  SGD; reservoir DD sweeps readout weights under least squares; **we sweep W under selection**.
- **"The mechanism relies on linearity" — WRONG.** Deep nets are wildly nonlinear in their
  parameters and show double descent (Nakkiran: ResNets, CNNs, Transformers). Linearity makes the
  **theory** tractable; it is not a precondition for the **phenomenon**. *(And "linear readout" =
  "linear in the swept parameters" — a reservoir's features are ferociously nonlinear, but with W
  frozen the model is linear in w, so the feature generator's nonlinearity is irrelevant.)*
- **The real condition is REACHING INTERPOLATION.** SGD reaches zero training error in deep nets —
  that is *why* there is a threshold to peak at. Nakkiran defines **effective model complexity via
  the training procedure** precisely because parameter counting fails for nonlinear models.
  **Whether a GA on a nonlinear spiking network reaches ~0 training error is unknown.**

**⇒ GATE B0 (before Gate B): does training error reach ~0 at high |W|?** Sweep P, plot **training**
error. If it plateaus above zero everywhere, **there is no interpolation threshold, hence no peak,
by construction** — and we would misread a design failure as a finding about biology. *(A fourth
way to guarantee a null, alongside B1–B3.)*
*Note:* **R&N sidestep this entirely** — pure selection over pre-existing variants, no optimizer to
fail.
**Positive control (PJM):** bolt a linear readout onto the evolved network and sweep its width.
Textbook double descent should appear. If it does not, the apparatus is broken, not the hypothesis.

### D050 — What separates noise-hiding from regulatory-PC: the SAME VARIANCE, TWO FATES
**2026-07-17 · Accepted** · *Credit: PJM's synthesis question* · the sharpest framing the project has
**The puzzle PJM posed:** SNNs are expected to reach a second descent via **Bartlett's noise-hiding**
(no regulation needed); SNNs are **known** to evolve regulation/PC (Ali et al., energy objective);
and PC is postulated as the source of the second descent. **What separates the two?**

**Answer — their PRECONDITIONS differ:**
- **Bartlett noise-hiding** needs **label noise** + many **low-variance parameter directions** to
  bury it in. **No cost required. Works in a FLAT environment.**
- **Ali PC** needs an **energy cost** + **predictive environments** (structure worth predicting).
**⇒ the environment and the cost decide which mechanism operates.**

**The deep version.** To a **level-1 encoder, context-driven variation LOOKS EXACTLY LIKE NOISE** —
the same stimulus yields different correct responses, which is the signature of noise from inside a
memoryless map. **But it is not noise. It is unexplained higher-order structure.**
> **Two fates for the same variance:** **hide it** (bury in sloppy directions — cheap, no new
> function, **caps out at the context-average**) or **read it** (infer context, modulate —
> expensive, but **explains** rather than absorbs).
**This is D048 from the other side:** the fluctuation channel is where the second-level regularity
lives; **whether the network hides it or reads it is the fork.**
**Discriminating prediction — different ASYMPTOTES, not just different structure:** noise-hiding's
descent **plateaus** at the context-averaged solution; PC's **keeps improving** toward the
generating process.
**Why biology has regulation:** biological environments *have* exploitable higher-order structure,
and activity is metabolically expensive. **Both of Ali's conditions are facts about biology.** In a
flat noisy world noise-hiding would suffice — and Bartlett says it would work fine.

**SLOPPINESS — the connection Frank misses.** Bartlett needs many low-variance parameter directions.
That **is sloppiness** (Gutenkunst et al., *Universally sloppy parameter sensitivities*). **Frank
cites Gutenkunst AND the benign-overfitting literature and never connects them.** The implication
runs **against us**: biological networks are famously sloppy, so **Bartlett's condition may be
BETTER satisfied in biology than in ML** — predicting a second descent via sloppiness-enabled
noise-hiding with **no regulation required**. More parsimonious than our story, with independent
support. **Measurable:** the sloppiness spectrum (eigenvalues of local fitness curvature) vs |W|.
**⇒ THREE curves on one axis, not two: error · regulatory emergence · sloppiness.** A fair fight.

### D051 — The experimental axis: fraction of unexplained variance that is LEARNABLE (not "noise level")
**2026-07-17 · Accepted** · *Credit: PJM ("record it, then search it")*
**Search result:** no hit on noise-hiding vs structure-learning as competing fates. But the ML
literature has a taxonomy — **benign / tempered / harmful** overfitting — discriminated by **SNR**
(high SNR → benign; low SNR → harmful), and benign overfitting arises *because of* noise in the
features acting as **implicit regularization**.
**The gap: in every one of those papers the noise IS noise** (label corruption by construction).
**Nobody asks whether the "noise" is learnable structure at another level.**

**⇒ the axis to sweep is not noise level but the FRACTION OF UNEXPLAINED VARIANCE THAT IS ACTUALLY
LEARNABLE.** Not signal-to-noise — **signal-to-*structured*-noise.**

| unexplained variance is… | viable route | prediction |
|---|---|---|
| **all true noise** | noise-hiding only | benign overfitting; **plateaus at the noise floor** |
| **all level-2 structure** | PC only | descent **continues** toward the generating process |
| **mixed** | **both available** | **which does selection take?** ← **the experiment** |

**PJM's deflation, and why the design survives it:** *"give the network noise and a place to hide it
and it hides noise; give it structure and an efficiency incentive and it learns structure."*
**Correct — the corner cells are tautological.** The science is in the **contested cells**, above
all **hierarchical environment + zero cost**: structure is present *and* sloppy directions exist.
**Nothing in the design decides which wins.** And: **does adding cost CAUSE the switch from hiding
to reading?** That is the mechanism claim.
**Prediction against the ML taxonomy:** **"tempered overfitting"** — non-optimal but non-trivial,
degrading with noise level — **is what noise-hiding looks like when the noise is secretly
structured.** A system stuck at the context-average would look exactly tempered. **PC breaks the
temper.**

### D052 — Controls are GRADED SERIES, not pass/fail: bookends and the map between them
**2026-07-17 · Accepted** · *Credit: PJM* · restructures the study
**PJM's two corrections, in order.**

**(1) The "tautological" cells are CONTROLS, and controls are not weaknesses.** *"Give the network
noise and a place to hide it and it hides noise"* is not a flaw — it is an **expected result
established in prior literature**, and for us it is a **control condition**. If the all-noise arm
fails to produce noise-hiding, the apparatus is broken and we learn that **before** misreading the
contested cell. **The tautological cells are how we earn the right to interpret the mixed cell.**
I had mislabelled the controls as filler. *(A study whose controls are literature replications is
in unusually good shape: they validate the port AND calibrate the contested cells.)*

| arm | expected | source | function |
|---|---|---|---|
| all true noise, no cost | noise-hiding descent, plateaus at noise floor | **Bartlett** | positive control — apparatus works |
| all level-2 structure, cost | PC emerges, descent continues | **Ali et al.** | positive control — mechanism available |
| **mixed, no cost** | **?** | **nobody** | **THE EXPERIMENT** |
| mixed, cost | ? | nobody | the mechanism claim: **does cost cause the switch?** |

**(2) Controls are GRADED, not binary — and that is the real methodology.** I worried the controls
are not guaranteed to pass (Bartlett is proved for *linear* models under *gradient*; Ali's PC
emerged under *gradient* with an *explicit energy objective*; **ours is selection on a spiking
network in both arms**). PJM: that is not a risk, it is a **dial**. If the native spiking network
fails to hide noise under noise-hiding conditions, **make it more control-ly** — add gradient-like
training, then bolt on a linear model — and see where the phenomenon appears. **We are learning
where the bookends sit for our network.**

**⇒ each control becomes an instrument for locating a BOUNDARY, and every outcome is a result:**

| noise-hiding first appears at… | reading |
|---|---|
| native SNN + selection | Bartlett's mechanism is **substrate- and optimizer-general** |
| SNN + gradient (not selection) | **THE OPTIMIZER was binding** — selection lacks what SGD has |
| SNN + linear readout only | **THE MODEL CLASS was binding** — nonlinearity in parameters blocks it |
| nowhere | Bartlett's mechanism **does not reach spiking substrates** |

**"Optimizer was binding" vs "model class was binding" is precisely the question underneath
everything we have argued about** — Frank's selection≈learning equivalence, R&N's Occam factor,
whether gradient-with-energy-objective just *is* selection (D047/D049). **The graded control answers
it empirically instead of by argument.**

**Same series for the PC control:** native SNN + selection → + gradient → + explicit energy
objective → **Ali's exact setup**. **Wherever PC first appears names its precondition.**

**Two bookends per control; the study becomes a MAP, not a test.** One end: our model. Other end:
the published setup where the result is established. **The gap between them is exactly what we are
trying to characterize.** *And it cannot produce a null we would have to explain away — "it needed
X" IS the answer.*

**Control inventory (six; each kills a specific alternative):**
1. **Bolt-on linear readout, sweep width** (PJM) — textbook DD should appear; if not, apparatus broken.
2. **No-selection drift** (D021) — did mutation bias / GP-map do it without selection?
3. **Gate B0** (D049) — does training error reach ~0? No interpolation ⇒ no threshold ⇒ no peak.
4. **Gate A** (D030) — does it beat a trivial baseline?
5. **All-noise arm** — Bartlett's expectation, graded.
6. **All-structure + cost arm** — Ali's expectation, graded.

### D053 — CORRECTION: double descent in SNNs HAS been studied (Wang & Pope 2025); and the topology dial is a THIRD axis we lack
**2026-07-17 · Accepted** · *both caught by PJM via an external document + direct challenge*
**I was wrong.** I said nobody had looked for double descent in SNNs. **Wang, H. & Pope, J. (2025),
ICAART 351–359**, *Double Descent Phenomenon in Liquid Time-Constant Networks, Quantized Neural
Networks and Spiking Neural Networks*: LTCs show a **subtle** form, QNNs a **pronounced** one on
CIFAR-10, **"the SNN models did not show a clear pattern."** (Also surfacing: *Deep Spiking Double
Descent*.)
**Their setup differs from ours on every axis:** **feedforward** SNNs (2 and 4 layers), **gradient**
training (Adam/SGD), sweeping **hidden-layer width**, on MNIST/FashionMNIST/CIFAR-10. Ours:
**recurrent**, **evolutionary**, sweeping **|W|**, hierarchical environment. And *"no clear pattern"*
is weaker than a null — they report the **learning-rate scheduler, label noise, and epochs all
significantly affect** whether double descent appears.
**But it raises real risk to Gate B**, and gives a mechanistic hypothesis worth taking seriously:
**spiking physics may itself regularize** — refractory periods bound rates, thresholds discard
sub-threshold noise (implicit L0), temporal sparsity filters. *If so, **Frank's import fails at the
level of the neuron.***

**The topology dial (my overclaim).** I said the external document's
**feedforward-random → recurrent-unstructured → recurrent-clustered** series was "essentially our
graded control series." **It is not.** Ours (D052) is an **optimizer/model-class** dial (selection →
gradient → linear readout): *what kind of fitting process is required?* Theirs is a **topology**
dial: *what kind of architecture is required?* **Orthogonal axes.** Only the *logic* is shared
(start where the phenomenon is guaranteed, walk toward the biological case). Real overlap: their
**SNN-1** (feedforward random + linear readout) ≈ **our bolt-on positive control** — it *is* a
random-features model; their SNN-2 ≈ our retired reservoir. **Topology is a THIRD dial we do not
have** — our design fixes topology and varies only parameter count. Worth noting, not assimilating.
*Assessment of the source document:* one checkable factual claim (Wang & Pope) — **correct**, which
earns credit. Most of the rest is confident assertion: the cerebellum/V1/PFC verdicts cite nothing;
*"empirically we don't see this"* for PFC is **absence of evidence where nobody has looked**; the
evolution-walks-the-swamp story is elegant and speculative.

### D054 — Frank's load-bearing premise is that BIOLOGY DOESN'T REGULARIZE — contradicted on both timescales
**2026-07-17 · Accepted** · *Credit: PJM's push ("can you have double descent without the overfitting phase?")*
**PJM's question:** if the brain tends away from overfitting, doesn't that prevent double descent?
**Answer: yes — definitionally.** The peak **IS** the overfitting; prevent overfitting and you
prevent the peak. **But you can keep the BENEFIT of overparameterization without the peak:**
regularize and the curve becomes **monotonically decreasing** (Nakkiran: optimal regularization
mitigates double descent; **Frank himself shows it in 2025a** — LASSO uses 7 of 20 nodes, no penalty
uses all 20).

**So: does Frank claim the curve or the benefit? He claims the CURVE, explicitly:**
> *"Classical statistics penalizes complexity to avoid overfitting, **effectively smoothing out the
> interpolation spike**. By contrast, **biology tends not to penalize complexity as strongly**.
> Evolutionary dynamics is therefore likely to **experience the full consequences of the double
> descent learning curve**."*

**That is a specific, falsifiable premise — and it is contradicted on BOTH timescales, by two
independent literatures that have not noticed because they use different vocabulary:**
- **Lifetime:** the brain regularizes **heavily** — evolved priors (**Wang et al. 2024**: neonate
  chicks generalize via spontaneous biases, inconsistent with an unbiased model), homeostatic
  plasticity, E/I balance, and **Hoel's Overfitted Brain Hypothesis** (*Patterns* 2021): **dreams
  evolved to prevent overfitting** by supplying "a sparse, corrupted, or randomized set of sensory
  inputs... to expand and regularize the limited and biased training set of the organism." *(Hoel's
  own reasoning — "any organism that implemented dropout during daily learning would face serious
  survival issues" — is the population-can-suffer/individual-cannot argument, from a real source.)*
- **Evolutionary:** **R&N** show **implicit regularization emerges from the replicator equation
  itself** (the Occam factor), **no external cost required**. **Selection IS a regularizer.**

**⇒ Frank needs biology to be unregularized, and everything we know says it isn't.**
**Our `c_syn` sweep is exactly this test:** `c_syn = 0` **IS** Frank's assumed regime; `c_syn > 0`
is the regularized one. We are asking whether **Frank's assumed regime is biologically reachable at
all.** *And it reframes Wang & Pope: SNNs may show no clear double descent **because the substrate
is already regularized**.*
*Caveat recorded:* the document's claim that **sparse coding** acts as a beneficial regularizer is
**contested** — *"Generalization is important to current brain models but is weak under sparse
coding"*; its advantages carry trade-offs, "with the lower capacity for generalization being
especially problematic."

### D055 — REGULARIZATION ≠ REGULATION. The distinction that rescues the project.
**2026-07-17 · Accepted** · *Credit: PJM* · *my sloppiness, exposed*
PJM: the story was collapsing into *"Frank overclaimed that biology doesn't regularize, and here is
a suite of models showing how it can"* — which is (1) already an abundant literature, and (2)
compatible with Frank being right about **populations** while we merely carve out the brain.
**The flaw is real, and the fix is a distinction I had been blurring because the words share a root:**

| | what it is | its job | literature |
|---|---|---|---|
| **Regularization** | machinery that prevents overfitting | **not fitting noise** | abundant: homeostasis, priors, dreams, weight decay, Occam factor |
| **Regulation** | a functional level that **modulates another level** | **exploiting structure the encoder cannot reach** | **the origin of it is unexplained** |

**The abundant literature is entirely about the first. Our hypothesis is entirely about the second.**
*"The brain regularizes"* says **nothing** about whether regulatory hierarchy emerges, or why.

### D056 — THE FRAME (PJM's): a repertoire of learning behaviours in spiking networks, and what determines position in it
**2026-07-17 · Accepted** · *Credit: PJM* · supersedes all prior framings
> Classical ML, neuroAI and evolutionary theory have converged on the idea that **algorithmic
> learning unites them**, and that **double descent** — first described in ML — is expected to
> pervade complex adaptive systems. Neuronal networks look like an obvious participant. **But the
> brain is not a deep network; and while organisms have brains, a brain is neither an organism nor a
> population** conforming to classical evolutionary patterns. Brain ensembles "learn", but the
> **kinds** of learning are varied and supported by varying architectures and processes. Some
> architectures may show classical overfitting/double descent (**cerebellum**); some may show
> classical encoding of environmental regularities (**primary sensory areas**); much of the brain is
> characterised instead by **multi-specificity and extreme flexibility**. **How does learning among
> the brain's networks relate to learning as described by the grand framework?** *This study maps a
> **repertoire of learning behaviours** displayed by spiking networks under varying constraints and
> stimuli.*

**Why it succeeds where every prior frame failed.** All previous frames were **adversarial** —
testing Frank, beating R&N, out-Franking Wagner. **This is constructive:** the convergence is real,
the brain is a hard case, and *how* it is hard is worth knowing. **Nobody has to be wrong.** Frank's
insight — **the parameter axis is where to look** — stays intact and becomes our **instrument**.
**It makes the design the point:** we built a 2×2 with graded controls — **a map**. The frame says we
are making a map. Wang & Pope's null becomes a data point; the cerebellum an expected positive; the
tautological cells the map's **calibrated corners**. **Nothing must be explained away.**
**It survives all four objections that killed earlier frames:** not out-Franking (his axis, our
object); not redundant with the regularization literature (**D055**); does not require Frank wrong
about populations; and **"why spiking" dissolves — the brain IS the case in question**, not a proxy.

**THE REQUIRED ADDITION (or it is merely a taxonomy).** A repertoire alone is a catalogue. The frame
needs a **predictive claim about what determines position in it** — and we have one:
> **The repertoire is not arbitrary. Three factors determine which learning behaviour obtains:**
> **(i)** whether the environment has **exploitable higher-order structure** (D045);
> **(ii)** whether there is a **metabolic cost** (`c_syn`);
> **(iii)** whether the **dynamical regime permits gain modulation** (H-D, tonic vs balanced).
> **Vary those and you can predict — and produce — each regime.**
*That converts "here is a map" into "here are the coordinates."* And they are exactly our three axes.

**One claim to soften.** *"Most of the brain displays no such patterns"* — the **mixed-selectivity**
part is well supported (Rigotti/Fusi); the **"displays no such patterns"** part comes from the AI
document, is **unsourced**, and is **absence of evidence — nobody has looked for double descent in
association cortex.** State as **open**, not established: the hallmarks have been sought in some
architectures and not others.

**The constructive question underneath (D055):** *why did regulatory hierarchy evolve?* Candidate
answer: **because encoding saturates.** **Double descent is not the phenomenon — it is the
diagnostic that reveals the transition.**

### D057 — B1/B2/B3/B3a fixed and VALIDATED; `headroom()` is now a required pre-run check
**2026-07-17 · Accepted**
**B1 — product-rule mutation is now the default** (`evonet.mutate(rule="product")`): `mag *= N(1,σ)`.
Friedlander (D043): sum-rule mutations **fail 94–97%** of the time to evolve a waist; product-rule
is also more biologically realistic. Sum-rule retained **only** as an experimental contrast — it is
a dial in the D052 graded series (*does the waist require product-rule mutation?*).

**B2/B3/B3a — `tasks.hierarchical_environments`.** Two-level environment; **context (slow) selects a
rank-r₁ map (fast)**. Validated against its own design principles:
- **[B3a] context is in the COVARIANCE, never the mean** — measured stimulus means |max| = 0.10–0.19
  (≈0) for every context, while covariance **structure** differs. *Total variance is also nearly
  equal across contexts (trace 3.9–4.25), which is stricter than intended: context cannot be read
  off overall variance, only off WHICH axes co-vary.* ⇒ the mean cannot carry context; reading it
  requires integrating history. **Regulation is forced, not invited.**
- **[B2] level-1 maps are rank-3, not rank-10** (built as A(K×r₁)·B(r₁×d)). A waist is now
  mathematically possible.
- **[B3] hierarchy verified by HEADROOM** (below).
- **[D051] `learnable_frac`** — the swept axis: fraction of unexplained variance that is
  context-driven (learnable) vs true noise. 1 → PC route only; 0 → noise-hiding only;
  **between → both available → THE EXPERIMENT.**

**`headroom()` — a required check, and it caught a fatal bug in my own validation.**
Two bounds: **memoryless floor** (best NMSE without context) and **oracle ceiling** (best NMSE with
context, **fitted as a SEPARATE MAP PER CONTEXT**). *headroom = floor − ceiling. If ≈ 0 the task has
no room for regulation to pay and the design is dead.*
**The bug:** my first oracle handed context as a **one-hot input** — memoryless 0.788 vs oracle 0.790,
**no benefit**, which looked like a dead task. Cause: a linear model can use an additive one-hot only
to **SHIFT** the output; it cannot change the **E→Y map**. **That is the offset-vs-gain distinction
(D040) biting my own test code** — and it is precisely why *context must select the map* and why
**regulation, not drive, is required.** *(My analytic floor was also wrong: tanh(E·mean(W)) ≠
mean(tanh(E·W)) — Jensen. Replaced with an empirical estimate.)*
**Validated result:** K=10, d=10, r₁=3, 4 contexts → **memoryless 0.819, oracle 0.197, headroom
0.62** — a memoryless encoder forfeits ~80% of the explainable variance. **Headroom scales with
context count** (2 ctx → 0.26; 4 → 0.62): *more contexts ⇒ more reason to level up.* A knob.

### D058 — GATE C: passed, but only after two real bugs it exposed
**2026-07-17 · Accepted** · `scripts/run_GateC_regime.py`
**Why Gate C is a prerequisite (D039/D047):** divisive gain modulation **requires** fluctuations
(Chance/Abbott/Reyes; Prescott & De Koninck); tonic conductance changes are merely subtractive. **No
reachable fluctuation-driven regime ⇒ no gain control ⇒ no regulation ⇒ H-D has no treatment arm.**
Operational definition: **mean-driven** = mean V above threshold, regular firing, CV_ISI ≪ 1;
**fluctuation-driven** = mean V below threshold, spikes caused by fluctuations crossing it, CV ≈ 1.

**FIRST RUN: FAILED 0/36, CV_ISI ≤ 0.44.** The diagnostic named the cause: **E/I current ratio up to
23.9** — excitation swamping inhibition ~24:1.
**Bug 1 — no E/I balance.** `ei_split=0.8` makes E outnumber I 4:1, but `random_genome` drew **all
magnitudes from one distribution**, so excitation dominates by the count ratio. The classic balanced
condition (Brunel 2000; van Vreeswijk & Sompolinsky 1996) scales inhibition to compensate:
**J_I = −g·J_E, g ≈ ei_split/(1−ei_split) = 4**. **Fix:** `random_genome(inh_gain=...)`, defaulting
to exactly that. *A starting condition, not a constraint — magnitudes are genes; evolution may
unbalance the network if that pays.* **Result: E/I currents 24:1 → ~0.5–0.9. Balanced.**

**SECOND RUN: still 0/36, CV ≤ 0.47** despite balance. Diagnostic again: **V_std ≈ 9.6 against
v_thresh = 1.0** — fluctuations ~10× threshold, so neurons fire at the **refractory limit**:
regular, low CV. And at the gentle end (w0=0.3, V_std 0.30 vs 0.42 to threshold) CV was still 0.16.
**Bug 2 — the fluctuations were too SLOW.** With τ_syn = 5 ms and τ_m = 20 ms, recurrent
fluctuations are smooth on the membrane timescale, so threshold crossings are regular. **Irregular
firing requires fluctuations FAST relative to τ_m.**
**Fix: `noise_sigma > 0`** — white, uncorrelated. *Not a bolted-on mechanism (contra D038) but a
CONDITION real neurons have anyway: channel noise, synaptic failure, background bombardment. Our
`noise_sigma = 0.0` default was the unphysical choice.*

**THIRD RUN: PASSED 31/36.** CV_ISI **0.50–1.07** (target ~1); rates **4–51 Hz** (physiological);
E/I currents **0.43–0.77** (balanced). Best: CV **1.07** at bias 0.6, gain 1.0, w0 0.6, density 0.3,
**noise_sigma 1.0**.
**⇒ H-D HAS BOTH ARMS, and the knob is a single parameter:**
| arm | noise_sigma | CV_ISI | inhibition acts | gain control |
|---|---|---|---|---|
| **tonic** | 0.2 | ~0.5 | subtractive (offset) | unavailable |
| **balanced** | 1.0 | ~0.9–1.07 | can be divisive (gain) | **available** |
**Same network, same genome, same task — one parameter.** That is the within-substrate control D047
called the strongest thing we have, and it is now demonstrated rather than hoped for.

*Note:* both bugs were **invisible without the diagnostics** — E/I current ratio and V_std vs
threshold. Neither would have surfaced from CV alone. **Measure the mechanism, not just the outcome.**

### D059 — GENOME PHILOSOPHY: the genome is an experimental INSTRUMENT, not a model of a genome
**2026-07-17 · Accepted** · *Credit: PJM ("what's our larger philosophy about which features are genes?")*

**The question:** some features are biologically more evolvable than others. Does that matter, or are
we sampling the full space anyway?

**"Rates don't matter, we sample the space" DOES NOT SURVIVE our own framework.** D034 established
the **genotype–phenotype map's bias is real** (Louis), and **Frank's mechanism IS implicit bias**
(via Wilson). **Mutation structure IS the implicit bias.** So relative evolvability is not a realism
garnish — **it is part of the mechanism under test**. Choose rates and you have partly chosen the
answer.
**But "use biologically realistic rates" also fails** — we cannot justify the numbers, and results
would inherit unjustifiable precision.

**THE CRITERION THAT WORKS IS NOT REALISM:**
> **Does this gene offer an ALTERNATIVE ROUTE to the phenomenon we are attributing to regulation?**

| tier | genes | rationale |
|---|---|---|
| **Core — the thing under test** | `mag` (W magnitudes) | these **are** Frank's parameters; **P = \|W\|** is the axis |
| **Enabling — makes the mechanism possible** | per-neuron `signs` (E/I) | D038: regulation needs coherent inhibitory identity |
| **Alternative route — could BYPASS regulation** | **τ_m, τ_syn, v_thresh** | Arm 2 (below) |
| **NEVER a gene** | **`noise_sigma`** | **it IS H-D's treatment variable** |
| **Out of scope** | `N`, `d` | N = next study (needs high per-node cost); **d is a niche property** (D037) |
| **Low priority / exclude** | `bias`, refractory, v_reset, v_rest | static offsets; bound rates; minor |

**Why each "alternative route" is one:**
- **τ_m / τ_syn** — context inference requires **history integration**. A network could get that by
  **evolving slow neurons**, with **no regulatory circuit at all**. Hand it τ_m and **H-C is
  confounded**: we would see a second descent without regulation and misread it as "regulation is
  epiphenomenal", when we had handed evolution a shortcut.
- **v_thresh** — threshold heterogeneity **increases dimensionality of neural dynamics** (Gast et
  al., already in REFERENCES): dimensionality **without** regulation.
- **`noise_sigma` — the trap.** It **is** the H-D manipulation. If evolution controls it, **the
  population chooses its own treatment arm** — it could evolve into the balanced regime to unlock
  gain control, and the tonic-vs-balanced contrast **collapses**. **Must stay experimenter-controlled
  permanently.**

**THE GRADED-GENOME DESIGN (D052's logic applied to the genome):**
| arm | genome | question |
|---|---|---|
| **Arm 1 (BUILD FIRST)** | `mag` + `signs` only | regulation is the **ONLY** route to context. **Does it emerge?** |
| **Arm 2** | + τ_m (and/or v_thresh) | regulation now **competes** with timescale/threshold tuning. **Which does selection take?** |
*Arm 2 is interesting in its own right — **"is regulatory hierarchy the PREFERRED solution, or merely
A solution?"** — with a clean signature (PJM): a **bimodal τ_m distribution emerging at the waist**
would mean evolution built a **timescale** hierarchy instead of a **regulatory** one.*
**Start with Arm 1** — not because τ_m is unbiological, but because **if regulation cannot emerge
when it is the only option, Arm 2 is moot.** Every added gene is both a search dimension (population
~100 against ~10,000 weights is already hard) and an analysis confound.

**THE PRINCIPLE:**
> **Minimal genome = maximum attribution.** Real biology evolves all of these; a "realistic" genome
> would make everything heritable — and then **nothing could be attributed**, because every
> phenomenon would have four available routes. **We are not modelling a genome; we are isolating a
> mechanism.** Arm 1 is minimal **so that if regulation emerges, it is because regulation was the
> only way.**

**Heterogeneity survives separately (PJM).** **Fixed-but-heterogeneous** per-neuron τ_m — *drawn, not
evolved* — is a **capability, not a route**: it decorrelates neurons (our Gate C fluctuations were
too slow partly because identical τ_m keeps responses correlated and the population drive coherent)
and may reduce reliance on injected `noise_sigma`, **without handing evolution a shortcut**.
Perez-Nieves et al. (2021) — heterogeneous time constants improve robustness — already in
REFERENCES as an unexplored lever. **Cheap to test in Gate C's existing harness.**

**Definition of record — W.** The **recurrent weight matrix**, N×N, `W[i,j]` = synapse **j → i**.
Assembled from two gene groups: `signs` (N, ±1, per **neuron**) and `mag` (N×N, ≥0), as
**W = mag × signs[presynaptic]** (Dale's law). **P = |W| = nonzero count = Frank's parameter axis.**
**There is NO input weight matrix**: the environment drives the first `n_in` neurons directly, one
channel per sensor. **W is purely recurrent, and it is the entire genome.**

**"Training" = the GA (PJM's check).** No gradient, no trained readout. **Selection is the
optimizer**: error on *encountered* environments → fitness → reproduction → W changes.
**training error** = error on environments selection acts on; **test error** = held-out environments.
*Subtlety:* classical double descent tracks **one model**; we have a **population**. So "training
error" needs a convention — **best individual** (right for Gate B0: interpolation asks whether **any**
genome can fit exactly) vs **population mean** (right for R&N's Occam factor, a **class-level**
effect). **Record both.**

### D060 — `evolve.py`: four design decisions that each silently determine an outcome
**2026-07-17 · Accepted** · *PJM: "evolve.py can enable or hamper or reveal or obscure everything — be careful"*

**1. SELECTION SCHEME IS AN ARM (PJM agreed), not a default.**
R&N's Occam factor is a **replicator-dynamics** effect: complex classes attain the highest
per-timestep fitness but collapse onto a **different best member each generation**, so their
**class growth rate** suffers. That requires **fitness-proportional** selection over a
distribution of types. **Tournament is RANK-based — it has NO Occam factor.** Defaulting to
tournament would **delete one of the two mechanisms we are adjudicating**, invisibly.
**And the tell: Friedlander used TOURNAMENT; R&N used REPLICATOR.** The two prior works we sit
between differ on exactly this — **which may partly explain their opposite answers.** ⇒ a dial in
the D052 graded series.

**2. DENSITY FIXED vs EVOLVABLE — this splits the study in two (and I had been conflating them).**
The Occam factor is **between-class competition**. With density fixed, every individual has the
same |W| — **one complexity class, no competition, the mechanism is silent by construction.**
| mode | question |
|---|---|
| **`fixed`** (swept across arms) | **does the curve have a peak and a second descent?** (Gate B — Frank's curve) |
| **`evolvable`** (structural add/remove) | **where does evolution LAND on that curve?** (R&N's question) |
**`evolvable` is the money experiment; `fixed` is the curve it lands on.** Does evolution park at
the peak (R&N: q ≈ q*) or drift past it (Frank)?

**3. CROSSOVER OFF by default.** Two networks can compute the same function with **permuted
neurons** (competing conventions); swapping rows/columns destroys both. NEAT solves this with
historical markings; we have direct encoding. **Mutation-only (evolution-strategy) is the safe
default.** A dial.

**4. THE RISK WE CANNOT DESIGN AWAY.** Can a GA optimise thousands of parameters with a population
of ~50? **Gate B0 IS that test.** Population size, generations and mutation σ are **load-bearing**.

**SCALE — I had it backwards, PJM caught it.** I implied larger N could ease the optimisation risk.
**Parameters scale as N²: larger N makes it WORSE.** N=100/density 0.3 → ~3,000 genes; N=200 →
~12,000. **The lever is SMALLER N** — but |W| must still span the threshold at n_env × d:
| N | max \|W\| | constraints | span |
|---|---|---|---|
| 100 | ~10,000 | 500 (50×10) | 0.1×–20× ✓ but ~3,000 genes at threshold |
| **50 (chosen)** | ~2,450 | **250 (50×5)** | 0.05×–**10×** ✓ and ~**250** genes at threshold |
| 30 | ~870 | 250 | too little headroom above |
**⇒ production scale: N=50, d=5.** Halves per-eval cost *and* shrinks the search dimension.
*The binding constraint is ARM COUNT, not one run:* selection (2) × density (6) × noise (2) ×
learnable_frac (3) = **72 arms** ≈ 1 h each on 6 workers ⇒ **~72 h**.

**IMPLEMENTED & VERIFIED.** Both selection schemes; both density modes (`evolvable` produces real
|W| variance ⇒ complexity classes exist ⇒ Occam factor can operate); product-rule mutation (D043);
Arm-1 genome only (D059); **`noise_sigma` is NOT a gene**; population evaluation **parallelised**
(spawn-safe, D007). Records **both** best-individual and population-mean training error (D059).
*Note on the affine alignment in `evaluate()`:* the network's rate units are arbitrary w.r.t. the
demanded profile, so we fit a **per-output gain+offset** — d scalars, **not a mixing matrix**. It
cannot mix neurons, so it is **not a trained readout** (D032 intact).

**FIRST SIGNAL — a warning, not a verdict.** N=50, d=5, |W|=735 vs **250 constraints = 2.94×
over threshold**; task headroom 0.443 (memoryless 0.791, oracle 0.348). But over 6 generations at
pop 12: **best_train 0.943 → 0.937** — NMSE ≈ 0.94 is *barely better than predicting the mean*.
Six generations at pop 12 is nothing, so this is not a result — **but it is the first hint that
Gate B0 is the binding risk (D049), exactly as predicted.** *If the GA cannot drive training error
toward 0, there is no interpolation threshold, no peak, and the design fails at the root.*

### D061 — POSITIVE CONTROL PASSES: textbook double descent on our own network. The apparatus is sane.
**2026-07-17 · Accepted** · *Credit: PJM (the bolt-on control was his suggestion)* · `scripts/run_GateB0_interpolation.py --control`
Random network + linear readout of varying width = a **random-features model**, so textbook double
descent is *expected*. **It appears, exactly:**
| M/n | train | test |
|---|---|---|
| 0.10 | 0.848 | 1.279 |
| 0.70 | 0.238 | 3.050 |
| **1.00** | **0.000** | **50.417** ← peak, precisely at the threshold |
| 1.10 | 0.000 | 9.476 |
| 3.00 | 0.000 | 2.337 |
| 8.00 | 0.000 | 1.709 |
**First descent, interpolation spike at M/n = 1.00, second descent (50.4 → 1.7 over 8× parameters)**
— on **our** network, with **our** hierarchical environments.

**Why this matters more than it looks.** If Gate B later returns a null, **we can attribute it to
the evolutionary setting rather than to broken plumbing.** That is precisely what a positive control
is for (D052: the bookend where the phenomenon is guaranteed).

**And it sharpens what Gate B0 actually asks.** Note WHERE the double descent lives: in the
**readout weights**, fit by **least squares**, where interpolation is **guaranteed by linear
algebra** (M ≥ n ⇒ an exact fit exists). **Gate B0 asks whether a GA on W can reach the same
place** — and D060's first signal (best_train 0.943 → 0.937) says that is genuinely uncertain.
**The two bookends are now concrete: least-squares on readout weights → perfect double descent;
selection on W → unknown. The gap between them IS the study** (D052's graded map).

### D062 — Gate B0 built; the honest failure protocol is written into it
**2026-07-17 · Accepted** · `scripts/run_GateB0_interpolation.py`
Evolves at **high |W|** (deep in the overparameterized regime) across GA settings — `pop_size`,
`n_generations`, `mag_sigma` are **load-bearing, not tuning** (D060) — and asks: **does best_train
approach 0?** Threshold: `best_train < 0.05` counts as interpolating. Records best-individual
(interpolation asks whether **any** genome fits exactly, D059).
**The protocol on failure is written into the script's own output**, because this is the most
likely way we fool ourselves:
> *"Do NOT interpret this as 'double descent is absent from spiking substrates'. It is a DESIGN
> failure until ruled out: try --preset hard, larger populations, an evolution strategy (CMA-ES),
> or fewer constraints (smaller n_env or d)."*
*Rationale:* Nakkiran defines **effective model complexity via the training procedure** precisely
because parameter counting fails for nonlinear models. **No interpolation ⇒ no threshold ⇒ no peak,
by construction** — a design failure that would masquerade as a finding about biology.

### D013 — Project keeps a lab notebook and this decision log
**2026-07-14 · Accepted**
`LAB_NOTEBOOK.md` (auto-appended run facts + hand-written interpretation) and this
`DECISIONS.md` are maintained as the project's narrative and governance memory.
*Reasoning:* keeps the project self-explaining as it evolves; the unifying rule across
code/outputs/narrative/rules is **append and date, never silently overwrite reasoning**.

### D018 — Retire the "PR is Frank's x-axis" interpretation test (H5) as a headline claim
**2026-07-14 · Accepted**
H5 is demoted from candidate flagship to a supporting/diagnostic measurement.
*Reasoning:* the RMT literature already establishes that **effective** dimensionality, not
nominal parameter count, sets the interpolation threshold — the peak occurs where the
normalized effective degrees of freedom η_κ = (1/n)·Tr[Σ²(Σ+κI)⁻²] → 1 (Bach 2023;
Hastie et al.; Mei & Montanari). So the abstract claim is taken. Worse, the literature also
supplies the *principled* metric (edof), which is a different functional of the same
spectrum than PR (a moment ratio). A PR-vs-edof horse race is therefore a rigged game: if
PR loses, that is the expected analytic result and not a finding; if PR wins, the natural
reading is that asymptotic assumptions fail on structured reservoir covariance — a technical
ML question, not a biological one. *Credit:* PJM's critique — "we'd need to show not only
that PR is Frank's axis but that other candidates aren't" — is what forced the check.

### D019 — The dissociation is a SCREENING-OFF test on natural scatter, not an engineered manipulation
**2026-07-14 · Accepted · refines D017**
Do **not** vary motifs *in order to* move PR. That makes structure and PR coupled by
construction and collinear as predictors — the same error class as the D014 normalization
bug (manipulating A through B, then claiming to separate them).
*Correct design:* exploit the fact that the structure → PR map is **many-to-one** (exactly
Recanatesi et al.'s finding that PR varies widely at fixed density). Build a library of
networks spanning many structural axes (density, reciprocity/motifs, E/I, heterogeneity,
coupling), let PR fall out where it falls, then locate **iso-PR networks with differing
structure** and **iso-structure networks with differing PR**. The test is conditional
independence: *given PR, does structure still predict generalization?* Frank's claim H is
precisely "**dimensionality screens off circuit features**." Natural scatter is the
instrument; a designed manipulation destroys it. *Credit:* PJM.

### D020 — E7's reference role is scoped as a scaling-and-invariants study
**2026-07-14 · Accepted · refines E7**
If the reservoir is to serve as the clean reference the group's messier systems (beehives,
colonies, boolean networks) are compared against, the deliverable is not a number but
**what scales and what doesn't**: how PR scales with N, whether the PR→generalization
relation preserves its shape across scales, and which findings are substrate-specific
versus portable. *Reasoning:* a reference point that hasn't characterized its own scaling
behaviour cannot license comparison to a colony. *Credit:* PJM.

### D021 — FLAGSHIP: evolve motif-encoded reservoirs with a genetic algorithm (new stage E9)
**2026-07-14 · Accepted · supersedes D017's reposition target as the headline**
The flagship becomes a **genetic algorithm over motif-encoded reservoir genomes**, with the
linear readout as the scoring mechanism. See `GA_DESIGN.md`.
*Reasoning:* every mechanism link we planned is already established (see REFERENCES.md
Positioning), and D018 removes the interpretation test. What the entire neuroscience/ML
literature we surveyed **lacks is selection** — no heredity, no lineage, no population.
Frank's claim is evolutionary, and a GA supplies exactly the missing ingredient. It also
makes his mapping *literal* rather than metaphorical: regulatory connections = genome,
**selective history = training environments**, selection = the optimizer, **novel
environments = test data**. No unearned analogy (contrast D003, where a learning optimizer
stood in for selection).
*Key structural insight:* in the overparameterized regime every individual interpolates the
training data, so **the fitness landscape is flat — a neutral network**. Naively this kills
selection; in fact it lands the population in precisely the regime Frank's argument is
about (his Gavrilets/neutral-space reframing: what matters is not position on a fitness
surface but which solution the dynamics find within the connected neutral region). The
central contrast therefore becomes **below vs. above the interpolation threshold**,
manipulated via the size of the selective history.
*Bonus:* the GA generates the D019 screening-off library as a byproduct — an evolved
population *is* natural scatter over structure and PR.
*Credit:* PJM's proposal.
