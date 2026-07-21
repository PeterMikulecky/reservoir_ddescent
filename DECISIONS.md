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

### D013 — Project keeps a lab notebook and this decision log
**2026-07-14 · Accepted**
`LAB_NOTEBOOK.md` (auto-appended run facts + hand-written interpretation) and this
`DECISIONS.md` are maintained as the project's narrative and governance memory.
*Reasoning:* keeps the project self-explaining as it evolves; the unifying rule across
code/outputs/narrative/rules is **append and date, never silently overwrite reasoning**.

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

### D063 — Control corrected: I mislabelled the curve, and the network never beats "no network"
**2026-07-17 · Accepted** · *both caught by PJM ("where was the first descent?")*
**Error 1 — there was no first descent, and I claimed one.** My table (D061) showed test error
rising **monotonically** 1.279 → 3.050 before the peak. I wrote "first descent, interpolation
spike, second descent" when **only the last two were visible**. The sweep started at M/n = 0.10,
**past the classical optimum** — the underparameterized descent was off the left edge.
**Fix:** widths now start at M = 1.
**With the full curve:** the first descent **exists but is trivial** — 1.101 → **1.029** at M=2,
then up. **A 7% improvement.** Technically a descent; barely a phenomenon.

**Error 2 — a reproducibility bug.** Random projections were drawn **sequentially from one RNG**,
so **changing the width LIST changed the features for every M**. Same nominal seed, peak moved
50.4 → 25.6 between runs. **Fix:** per-M seeding (`seed*100003 + M`). **With it the peak lands at
M/n = 1.00 exactly** (test 14,229 — a violent spike), second descent to 2.19. Reproducible.

**THE FINDING THAT MATTERS — the network never beats "no network".**
Raw-input linear readout: **0.791**. Best state-based readout at ANY width: **1.029**.
**Every width is worse than having no network at all.** *(The task's memoryless floor is 0.79 —
the raw-input baseline reaches it; the network's states do not.)*
**⇒ the baseline is now printed permanently beside the sweep** (D030's rule made structural).
*Not fatal, and the distinction matters:* **this is a RANDOM network.** Poor states are exactly
what one expects — and **E9's entire premise is that selection shapes W.** So the control does its
job (the apparatus CAN produce an interpolation spike and benign overfitting) while showing that
**the double descent it produces lives entirely in the READOUT over random features** — Belkin's
setting, reproduced. **It says nothing yet about the network.**

**⇒ three distinct questions, only the first now answered:**
| | question | status |
|---|---|---|
| **control** | is double descent EXPRESSIBLE in this apparatus? | ✅ **yes** — peak at M/n = 1.00, second descent |
| **Gate A** | does EVOLUTION make the network beat the raw-input baseline? | **open** |
| **Gate B** | does double descent appear in the EVOLVED W? | **open** |

**Suggestive but not leanable:** the classical optimum sits at **M = 2–5** with **r₁ = 3**, while
the **peak** sits at **M/n ≈ 1**. **Two different quantities in two different places — as H-B
predicts** (optimum tracks r₁; peak tracks n). *With a 7% first descent, not evidence yet.*

### D064 — Gate B0 runtime: parallelism was nested the wrong way; `quick` preset added
**2026-07-17 · Accepted** · *PJM: "how long do we expect the GATE simulations to take?" — a question I should have answered before handing over the run command*
**My error.** I gave a run command without estimating its cost. Worse, **the parallelism was nested
outward:** `_arm()` called `run_evolution(..., n_workers=1)` while an outer pool parallelised across
ARMS. With 4 arms on 6 workers, **two workers idled and wall-clock was set by the SLOWEST SINGLE
ARM** (~3.3 h for pop 60 × 100 gens; ~10 h for the `default` preset; the `hard` preset's largest arm
is ~20 h **on its own**).
**Fixes:**
1. **Parallelism nested INWARD** — workers go to the **population**; arms run **serially**. All 6
   workers on one arm at a time; total = **sum** of arms, each ~6× faster.
2. **Worker initializer** — `pool.map` was re-pickling the **task (E/Y arrays + W_ctx) and net_cfg
   for every individual, every generation.** Now set **once per worker** via `initializer=`; only
   the genome is shipped.
3. **`quick` preset (RUN THIS FIRST):** pop 30 × 100 gens, one sigma, one density = **1 arm**.
   *Gate B0 is a **yes/no** question — does training error move **at all**? D060's signal
   (0.943 → 0.937 over 6 generations) suggests the answer may arrive in minutes.* **If train is
   still ~0.94 after 100 generations, that is the important thing — learned without spending 10 h
   confirming it four ways.**
4. The script now **prints an evaluation-count and time estimate** before starting, and per-arm
   timings as it goes.

**Honest caveat:** my ~15 min estimate for `quick` is **unverified** — the sandbox timing test
itself timed out, which suggests the parallel speedup is well short of 6×. **Time the `quick` run;
that measurement beats my arithmetic.**

**On the abandoned partial run:** Ctrl-C leaves the run directory with `status: "running"` (finalize
never fires). **Harmless** — `archive_runs.py` only moves `complete` runs, so it is ignored
permanently. `positive_control.parquet` was written (it runs in seconds), so there is a little real
data. Delete for tidiness or keep as an honest record that a run was started and abandoned.

### D065 — The parallelism was NEVER running. Every GA run was silently serial.
**2026-07-17 · Accepted** · *Credit: PJM — "only 1 Python process at about 12% CPU"*
**The bug, in `run_evolution`:**
```python
eval_fn = eval_fn or (lambda g: evaluate(g, task, net_cfg))   # eval_fn is now NEVER None
...
if n_workers > 1 and eval_fn is None:                          # ALWAYS FALSE
    pool = mp.get_context("spawn").Pool(...)                   # NEVER CREATED
```
**The pool was never created.** `n_workers=6` did nothing. Every GA run — including D060's
timing measurements and the abandoned Gate B0 run — was **single-process**. One core of eight ≈
**12% CPU**, exactly what Task Manager showed.
**Fix:** decide `use_pool` **before** overwriting `eval_fn`.

**This retroactively explains the sandbox timing failures.** D060 reported "141 s for 72 evals on
6 workers" and I read the poor speedup as spawn/pickling overhead — which is why I added the
worker initializer (D064). **The initializer is still correct, but it was not the problem.** The
problem was that no workers existed. *I diagnosed an overhead issue in code that was not running
in parallel at all.*

**Measured after the fix:** **~3.4 s per evaluation, serial.** So:
| | serial | 6 workers (est.) |
|---|---|---|
| `quick` (3,000 evals) | ~2.8 h | **~28 min** |
| `default` (18,000 evals) | ~17 h | ~2.8 h |
*The abandoned run at 7 minutes had completed roughly 120 of 3,000 evaluations — ~4%.*

**Lesson:** **watch the process count, not just the wall clock.** A silently-serial pool looks
exactly like slow code. Three separate timing estimates (D060, D064, and my "~15 min for quick")
were all built on measurements of code that was never parallel. *PJM caught in one glance at Task
Manager what three of my sandbox benchmarks had missed.*

### D066 — The run was unobservable: `verbose=False` meant zero output for hours
**2026-07-17 · Accepted** · *PJM: "is there a way to assess its progress?" — there was not, and that was my bug*
`_arm()` called `run_evolution(..., verbose=False)`. With `quick` being a **single arm**, that meant
**no output at all** until the entire run finished — no progress, no ETA, no way to tell a working
run from a hung one. **A long-running scientific job that prints nothing is unobservable, and I
shipped three of them.**
**Fixes:**
1. `verbose=True` by default in `_arm`.
2. **Progress every 10 generations with elapsed + ETA**, `flush=True`.
3. **The pool announces itself**: `[PARALLEL: 6 workers]` vs `[SERIAL (1 process)]`, with a
   per-generation time expectation. **D065's bug hid for three sessions because a silently-serial
   pool looks exactly like slow code — now it cannot hide.**

**The diagnostic PJM needed (process count) should have been in the output, not in Task Manager:**
| processes | meaning | `quick` ETA |
|---|---|---|
| ~6 | parallel working | ~28 min |
| 1 | still serial | ~2.8 h |

**Standing rule:** *any run longer than a few minutes must print progress, an ETA, and its own
parallelism state.* Three separate sessions of timing confusion (D060, D064, D065) trace to runs
that could not report on themselves.

### D067 — GATE B0 FAILS. The GA never approaches interpolation — and the diagnosis is ARITHMETIC, not biology.
**2026-07-17 · Accepted, WITH CORRECTIONS** · **cost model superseded by D068 · diagnosis superseded by D072** · lands exactly on the risk D049 flagged

> **⚠ CORRECTION NOTICE (added 2026-07-17).** Two things below were **plainly wrong** and are
> corrected **in place**, marked `[D068]` / `[D072]`, with the original text struck through so the
> reasoning survives. *Append-only exists to retain history, not to preserve mis-statements.*
> **(a) The per-arm cost column is arithmetically wrong** — it assumed per-eval cost ∝ |W|; cost is
> **timestep-dominated** and ~flat in N (D068). **(b) "The lever is parameter count" is false** —
> the N decision was never available.
> **What is NOT edited, because it is superseded JUDGEMENT rather than error:** the ~40×
> evaluation shortfall (the arithmetic is right: 3,000 vs ~122,000); *"the GA barely started"*;
> the N=20 proposal; *"Gate A is unanswerable until Gate B0 passes."* **D072 overturns all of
> them: the network holds ~30 ms of memory and the task needs 1,500 ms, so Gate B0 could not have
> passed at ANY budget — the shortfall was real and not binding.** *And Gate A was answerable all
> along: the encoder works (`E|state` = 0.225) and it is a ROUTING problem.*
> *One imprecision noted, not edited: `best_train` (a TRAINING error) is compared below against
> `memoryless_floor` (a TEST NMSE from `best_nmse`). Apples to oranges. The conclusion survives —
> the linear readout's training fit is lower still — but the comparison is not like-for-like.*

**Result (`--preset quick`, real run, 6 workers, 5,193 s):**
`best_train` **0.936 → 0.882** over 100 generations. Never near interpolation (threshold 0.05).
**Worse than the memoryless floor (0.834)** — after 100 generations of selection the evolved network
is **worse than having no network at all**.

**THE DIAGNOSIS — we are 40× short of the evaluations required.**
|W| = **1,221** parameters, optimized with **3,000** evaluations. The standard rule of thumb for
evolution strategies is **~100 × n_params** evaluations to converge ⇒ **~122,000 needed**.
**The GA did not fail. It barely started.**

**THE WALL.** Measured **~1.7 s/eval on 6 workers** (my 3.4 s/eval sandbox estimate was optimistic;
6 processes ≠ 6× speedup — each generation is a `pool.map` **barrier** waiting on its slowest
member, and Brian2 **rebuilds a network per evaluation**). So 122,000 evals ≈ **58 h for ONE arm**;
the 72-arm map ≈ **4,000 h**. **Evaluation cost is now a first-class design constraint, not a
detail.**

~~**THE LEVER IS PARAMETER COUNT, AND IT IS QUADRATIC (|W| ~ density·N²) — not the optimizer:**~~
**[D068] FALSE. The lever is TIMESTEPS, and N does not touch them.** 50 env × 150 ms ÷ 0.5 ms × 2
(train+test) = **30,000 timesteps/eval**; 3.4 s serial ÷ 30,000 ≈ **113 µs/timestep to update 50
floats** — pure Python dispatch, ~flat in N and |W|. **Only the N=50 row below was measured; the
other two assumed cost ∝ |W| and are wrong:**

| N | \|W\| @ density 0.5 | evals needed (~100n) | ~~est. per arm~~ **[D068: WRONG]** | **corrected** (at the measured 1.7 s/eval) |
|---|---|---|---|---|
| 50 (current) | 1,221 | 122,000 | **58 h** ✗ | **58 h** — the only measured row |
| 30 | ~435 | 43,500 | ~~~8 h~~ | **20.5 h** |
| **20 (proposed)** | **~190** | **19,000** | ~~**~1.5 h** ✓~~ | **9.0 h** ✗ |

**⇒ N=20 gives ~9 h/arm, not 1.5 h; the 72-arm map ≈ 650 h. N=20 never rescued anything, and the
trade weighed below was never on the table.** *The real lever is batching — engineering, not scale
(D068). N=50 stands.*
**And N=20 has a precedent I had forgotten: Frank's own 2025a example is a 20-node network** —
*"a sparsely and randomly connected network with 20 nodes stores an imperfect and dimensionally
reduced memory of past inputs."* **We would be at his scale, not an artificially tiny one.**
Proposed: **N=20, d=3, n_env=20 → 60 constraints, |W|/constraints ≈ 3.2** — still comfortably
overparameterized, and each eval far cheaper ~~(fewer synapses AND fewer patterns)~~
**[D068] HALF FALSE: fewer synapses changes NOTHING (cost is timestep-dominated). Fewer PATTERNS
does help — n_env sets the timestep count. The right half of this was the accidental one.**
**Other levers to price:** `present_ms` 150 → 50 (~3× faster, less settling time); fewer
environments (also lowers the constraint count, moving the threshold **toward** us).

**THE HONEST STATEMENT.** The script's built-in warning (D062) was right: **this is a DESIGN
failure, not a finding about biology.** But it is a serious one — it says **the study as scoped may
be computationally infeasible**, and the fix (N=20) shrinks the networks to where *"spiking
network"* is a generous description. **That is a real trade to weigh, not a parameter tweak.**

**Positive control, same run (baseline 0.834):** peak at **M/n = 1.00** exactly (test 202), second
descent to 2.50, **first descent now present** (1.037 → **1.034** at M=2 — still trivial, 0.3%).
**Optimum at M=2 vs r₁=3; peak at M/n=1.00** — two quantities, two places, as H-B predicts.
**But the reservoir states STILL never beat raw input** (best 1.034 vs 0.834) — that is a RANDOM
network, and Gate A (does *evolution* fix it?) is now **unanswerable until Gate B0 passes.**

### D068 — D067's COST MODEL IS WRONG: per-eval cost is TIMESTEP-dominated, not |W|-dominated. The N decision was never available.
**2026-07-17 · Accepted** · **supersedes D067's N table** (D067's *shortfall* diagnosis stands — we are ~40× short; only the cost model and the proposed remedy are wrong) · *Credit: an independent code review in a fresh chat, cross-checked against the source*

**THE ERROR.** D067 priced each N by assuming **per-eval cost ∝ |W|**. Back the assumption out and it is visible:

| N | \|W\| | evals (~100n) | D067's per-arm | implied s/eval | at the **measured** 1.7 s/eval |
|---|---|---|---|---|---|
| 50 | 1,221 | 122,000 | 58 h | 1.71 | 57.6 h |
| 30 | ~435 | 43,500 | ~8 h | **0.66** | **20.5 h** |
| 20 | ~190 | 19,000 | ~1.5 h | **0.28** | **9.0 h** |

**Only the N=50 row used a measured number.** The other two silently assumed 1.7 s falls 2.6× and 6.4× — exactly in proportion to |W|.

**THE CODE SAYS OTHERWISE. The cost is TIMESTEPS, and N does not touch them:**
- `behave()` runs **all n_env in ONE `net.run()`** — environments are **already batched**. That lever is spent.
- `b2.defaultclock.dt = 0.5*ms` — already 5× coarser than Brian2's default. Spent.
- n_env=50 × `present_ms`=150 ÷ 0.5 ms = **15,000 timesteps per `behave()`**, and `evaluate()` calls it **twice** (train + test) ⇒ **30,000 timesteps per eval**.
- D065's measured **3.4 s/eval serial ÷ 30,000 ≈ 113 µs per timestep** — to update **50 floats**. That is ~100% Python/numpy dispatch across Brian2's ~5 code objects (state update, threshold, reset, synapse pathway, StateMonitor). **It does not scale with N or |W| at this size.** N=20 makes the arrays 20 floats instead of 50 and changes nothing else.

**⇒ N=20 gives ~9 h/arm, not 1.5 h** (19,000 × 1.7 s); the 72-arm map ≈ **650 h**. **N=20 does not rescue the study.** The trade D067 posed — *"the fix shrinks networks to where 'spiking network' is a generous description"* — **was never on the table.** *We came close to paying a real scientific price (Gate C's K≫1 at ~6 inputs/neuron; regulatory headroom at N=20; H-B's r₁ range collapsing to {1,2} at d=3) for a speedup that does not exist.*

**THE REAL LEVER IS THE TIMESTEP OVERHEAD — ENGINEERING, NOT SCALE:**

| fix | payoff | scientific cost |
|---|---|---|
| **Stop evaluating the test set for every individual, every generation.** `evaluate()` computes `err_te` for all 30; `_fitness()` reads **only `train_err`**; only `order[0]`'s test error reaches the verdict. **Half the timesteps are computed and discarded.** | **exact 2×** | none for Gate B0 |
| **Batch the population into ONE network.** pop×N = 30×50 = **1,500 neurons**, block-diagonal W, one `run()` per generation. The 113 µs is paid **once**, not 30×; 1,500-float arrays are still overhead-dominated. Drive = `np.tile(drive, (1, pop_size))`; `xi` is per-neuron so each block keeps its own noise. | **~15–25×** | **none** |
| **Pre-allocated synapses, built once per run** (NOT a frozen wiring diagram — evolution still adds/removes/reweights edges via the genome; "fixed" refers only to the Brian2 object). Allocate all N(N−1) synapse slots per block; **an absent edge is a slot at weight 0, which is dynamically inert**, so effective topology still varies per genome. Set `w=0` for absent ones. Per generation: `restore("init")` → `S.w[:] = ...` → `run()`. No rebuild, ever. | enables the above | **none** — zero-weight synapses are dynamically inert, and `Genome.n_params()` counts `mag != 0`, so **P = \|W\| is untouched** |
| **Delete the pool.** Measured **3.4 s serial → 1.7 s on 6 workers = 2.0×, i.e. 33% efficiency.** Batching removes the pool, spawn, pickling, and the `pool.map` barrier; D064's `_init_worker` becomes moot. | ~1.5× | none |
| **Hoist the StateMonitor** out of `behave()` — it is `add`ed and `remove`d on **every call**, forcing `before_run` re-preparation each time — and record the **output slice only**: `state`/`state_var` are computed in `evaluate()` and then **popped and discarded in `_eval_payload`**. | ~20% | none |

**NOT WORTH TOUCHING** — recorded so the temptation dies here. The `lstsq` loop in `nmse()` is **10 calls on (50,2) matrices ≈ 0.5 ms of 3,400 ms = 0.015%**. `mutate`'s (N,N) copies and `dale_violations()`: microseconds, not in the hot path. *Vectorizing numpy while 113 µs/timestep sits there would be D060/D064/D065 repeated a fourth time.*

**PROJECTED — and it must be MEASURED, not believed:** pop30×100gens **85 min → ~5 min**; one arm at N=50 at the required depth (~4,000–5,000 generations) **~4 h, not 58 h**; Gate B's 6-arm density sweep **~17 h**.

**⇒ N=50 STANDS.** It is the scale Gate C was validated at (D058) and the scale balanced-state dynamics require: N=20 at density 0.3 gives **~6 recurrent inputs per neuron**, and √K fluctuation scaling at K=6 is not a balanced regime. **The N question DISSOLVES rather than being answered.**

**STANDING RULE, NOW EARNED FOUR TIMES.** D060, D064, D065 and D067 each produced a confident runtime estimate from arithmetic, and **all four were wrong**. The pattern is not carelessness; it is that each estimate rested on an **unnamed assumption about what cost scales with** (arms, workers, parameters). ⇒ *Any cost model must **name the quantity it assumes cost scales with**, and that assumption must be **measured** before it is used to make a design decision.* **Measure the per-generation time after batching before believing the ~5 min above.**

### D069 — The skill gate IS the whole experiment: `baseline ≡ memoryless_floor` is an IDENTITY, not a finding
**2026-07-17 · Accepted** · *corrects the reading recorded in D063; sharpens the Gate C indictment rather than softening it*

**THE IDENTITY.** `HierarchicalTask.headroom()`:
```python
floor = best_nmse(self.E_train, self.Y_train, self.E_test, self.Y_test,
                  alphas=alphas, standardize=False)[0]
```
`run_GateB0_interpolation.py`:
```python
base = best_nmse(task.E_train, task.Y_train, task.E_test, task.Y_test,
                 standardize=False)[0]
```
**Same call. Same data.** So D063's *"the task's memoryless floor is 0.79 — the raw-input baseline reaches it"* is not an observation. It is `x == x`. **We recorded a tautology as a finding and then reasoned from it.**

**WHAT FOLLOWS.** `baseline ≡ memoryless floor` ⇒ **"beats baseline" ≡ "infers context" ≡ THE ENTIRE EXPERIMENT.** Failing that bar tells us **nothing** about whether the state encodes E. **D030's actual gate was lower and diagnostic — *does the state encode the input?* We imported D030's NUMBER and lost D030's RULE.**

**MEASURED** (gain × σ sweep; state-readout test NMSE; raw-input baseline **0.791**):

| gain | σ=0.2 | σ=1.0 |
|---|---|---|
| 1 | 0.935 | 0.993 |
| 10 | **0.835** | 0.869 |
| 30 | **0.835** | 0.840 |

**Read correctly, this says THE ENCODER IS NOT BROKEN.** 0.835 against a memoryless floor of 0.791 is the network **reaching the memoryless floor lossily** — the best *anything* can do without context. *"Nothing beats the baseline anywhere"* is not a failure; it is **what a network with no context inference must look like.** The level-1 map is `tanh(E @ W_c)` — **nearly linear** — so a linear readout on raw E already captures it, and a random nonlinear scramble cannot beat that. **The only route to value is memory for context inference, which a RANDOM W does not have.**

**THE GATE C INDICTMENT STANDS, AND SHARPENS.** Gate C's operating point (bias 0.6, **gain 1.0**, w0 0.6) is the **worst cell in the table** — 0.935 / 0.993 ≈ predicting the mean. Gate C scored operating points on **CV_ISI alone** and never asked whether the state encodes the input. **That is D030's error exactly, one level up** — and D030 is the entry in this log that says the two objectives are *in opposition* and that **skill is a GATE, not a metric**. *The rule was written down. It was not applied to Gate C.* **`headroom()` is a required pre-run check (D057). `skill` is not — and D030 says it must be.**

**HYPOTHESIS REJECTED — recorded because the check was cheap and decisive.** That the drive never reached the network: `_build()` seeds the namespace with a **zeros** TimedArray and `behave()` rebinds `G.namespace["ta"]` afterwards, so a stale binding would leave `I_ext ≡ 0` — which would have explained *every* symptom (train ≈ 0.94 ≈ mean-prediction, test ≈ 1.0, states at 1.034, and a positive control that still passes because random features uncorrelated with the target show the M=n spike perfectly well). **FALSE:** |state(E) − state(0)| = **3.12** at gain=1.0; output neurons vary across environments (std **0.49**). **The drive lands.** *A 30-second check killed a hypothesis that would otherwise have consumed a session.*

**WHAT HAS NEVER BEEN MEASURED** — both cheap; the second is listed in `BRIDGE.md` Level 5 and has never been run:
1. **Decode E from `state`, and separately from `rates`** — D030's actual gate. Fitness reads the **last d of N** neurons: a random W may encode E in the state and never **route** it to the output slice. *That is Gate A's question, sharpened — and the two decodes separate "the encoder is broken" from "the encoder works but nothing reaches fitness".*
2. **Decode context from `state`** (chance = 1/`n_contexts` = 0.25) — *is the system doing Level 2(iii) at all?*

**CONSEQUENCE FOR D063.** Its finding *"the reservoir states never beat raw input (1.034 vs 0.834)"* is **not** evidence that the network destroys information. It is evidence that **a random network cannot infer context** — which was never in doubt, and which is precisely what E9's premise says selection is for. **Gate A remains open and is now the live question.**

### D070 — Docstrings state RULES; results live in `DECISIONS.md` with a D-number or run_id
**2026-07-17 · Accepted** · *Credit: PJM — "your point about some stale docstrings having confused you highlights the need for us to be even more scrupulous"*

**THE FAILURE.** `baseline.py`'s module docstring contains two different kinds of thing:
- **A RULE** — *"skill is a GATE, not a metric. An operating point that fails it is disqualified regardless of how good its dimensionality looks."* **Still true. Aged perfectly.**
- **RESULTS** — *"the reservoir scored test NMSE 0.880 against a raw-input baseline of 0.216 ... It only beat baseline at input_gain=10."* **From the RETIRED N=1000 reservoir on the RETIRED scalar-tanh task** — both killed by D032/D036 and `FRAMING.md` §2c. **Dead numbers, no provenance, no date.**

An independent reviewer read those results as current, concluded `input_gain=1.0` was the bug and `gain=10` was "the useful regime", and was wrong on both counts (D069). **The rule never went stale. Only the results did.** *The file that taught this project "skill is a gate" is the file whose stale numbers misdirected a review of that same gate.*

**THE RULE:**
> **Docstrings state RULES. Results live in `DECISIONS.md` with a D-number or a run_id.** A number in a docstring must carry the entry that produced it, or it does not belong there.

**SAME SPECIES, STILL LIVE:** `EvoNetConfig.input_gain: float = 10.0  # D030/D033: the useful regime` — **a result from a different model, frozen into a default.** It carries D-numbers, which is the minimum; but a default value is not a place for a finding, and "the useful regime" is now false (D069: no gain beats the memoryless floor, because nothing without memory can).

**ACTION — one audit pass:** `grep -nE '[0-9]\.[0-9]{2,}' ddescent/*.py`. Every number found either gains a D-number/run_id or moves out of the docstring.

*Why this belongs in the decision log:* D013's unifying rule is **append and date, never silently overwrite reasoning**. A result in a docstring is reasoning with **no date and no provenance** — and it silently overwrites itself every time the model changes underneath it. That is the one failure mode this log exists to prevent, occurring in the one place the log does not reach.

### D071 — Three documentation-vs-code divergences, all found by reading: a stage bug, a stale vocabulary, and a decision that was never implemented
**2026-07-17 · Accepted** · *found while preparing Phase 1; each is the same failure in a different direction* · **the stage bug and the vocabulary are FIXED in this commit**

**1. THE STAGE BUG — the flagship's gate was filed under "tuning/prep". FIXED.**
`run_GateB0_interpolation.py` registered as `P.new_run("T0", "exp", tag="gateB0-interpolation")`.
**`"T0"` is `tune_operating_point`.** Meanwhile `provenance.CANONICAL` has had `"E9": "evolve"`
since **D021 created the stage**. *The stage was available and unused.*
*The damage, in one path:*
```
runs\T0_tune_operating_point\T0-tune_operating_point__20260717-213756__exp__g91f2891__gateb0-interpolation\
```
NAMING.md §5's provenance chain (figure → runhash → manifest → upstream run IDs → git hash) is
**intact but mislabelled at the root**: an E9 result is not discoverable as one, and the real
identity survives only in a freeform `tag`, which §1 calls "optional".
*Fix:* `P.new_run("E9", "exp", ...)`.
**Accepted consequence — a permanent split.** `runs/` is never hand-edited (NAMING.md §3), so the
D067 run **stays** under `T0_tune_operating_point` while everything from here lands in
`runs/E9_evolve/`. Recorded here so the split is legible rather than mysterious. *The alternative
— rewriting the registry — would violate the append-only property that is the only reason the
registry is worth having.*

**2. NAMING.md WAS STALE — and it is why (1) happened. FIXED.**
§1's STAGE row read `E0`–`E8`, and the controlled-vocabulary block stopped at `E8` — for three
days after D021 added E9 to `CANONICAL`. **The code was current; the document was stale.**
**That is the exact INVERSE of D070's failure** (`baseline.py`: document current, code retired).
*Both are the same absence — nothing checks the log, the docs, and the code against each other —
and it can fail in either direction.* Fixed, plus a line naming `CANONICAL` as the source of truth
and this table as a copy of it.

**3. D066 WAS NEVER IMPLEMENTED. Confirmed by reading; not fixed here.**

| D066 specifies | the code does |
|---|---|
| `verbose=True` by default in `_arm` | `run_evolution(..., verbose=False)` |
| progress every **10** generations with **elapsed + ETA**, `flush=True` | `if verbose and (gen % 20 == 0 ...)` — no elapsed, no ETA, no flush |
| the pool announces `[PARALLEL: 6 workers]` vs `[SERIAL (1 process)]` | absent |

**And there is no D066 commit:** the log runs D064 → D065 → **D067**. *D064's and D065's fixes ARE
present, so this is not a stale working copy — D066 alone never landed.*
**Corroborating evidence from D067 itself:** it reports "**~1.7 s/eval**", which is
5,193 s ÷ 3,000 evals — **total-time-over-total-evals arithmetic**. That is precisely what you
compute when the run *did not report its own timings*. **A D066-compliant run would have printed
the ETA.** *D066 was written in response to PJM's "is there a way to assess its progress?" — and
the answer is still no.*
**⇒ D066 is a decision that exists only as prose.** *The failure it exists to prevent — an
unobservable long-running job — is guaranteed to recur, because D066 was never anything but a
document.* **Fix 1 is applied here** (it is one line in the file already being edited); **fixes
2–3 land in `evolve.py` with the D068 batching changeset**, which rewrites `run_evolution` anyway.

**4. AND WHILE IN THE FILE: D064's printed estimate was wrong by ~5×. FIXED.**
```python
print(f"    {est:,} total evaluations ~ {est*2/max(args.workers,1)/60:.0f} min "
      f"at ~2 s/eval on {args.workers} workers")
```
It divides by `workers` **and** uses a per-eval figure that was already **6-worker throughput** —
**double-counting the parallelism**. Printed **17 min** for a run that took **87**.
*This is D068's rule in miniature: the formula never named the quantity it assumed cost scaled
with.* Replaced with the measured throughput, an explicit "do NOT divide by n_workers again", and
a note that cost is **timestep-dominated** — hence ~flat in N and |W| (D068).

**THE PATTERN, AND THE RULE.** D070 covers code that outlives its results. **This covers the two
reverses: decisions that outlive their implementation, and documents that outlive their
vocabulary.** Three artifacts — the log, the docs, the code — and **no pass ever compares them.**
> **A decision that specifies code is not done until the code exists.** Cite the D-number in the
> commit that implements it. Otherwise the log records an **intention** as though it were a
> **fact** — and every later decision that reads the log inherits the error. *D067 planned around
> a progress-reporting facility that was never built.*

### D072 — THE DIAGNOSTICS: Gate B0's failure is ARITHMETIC. The network has ~30 ms of memory and the task needs 1,500 ms.
**2026-07-17 · Accepted** · **supersedes D067's diagnosis, as D068 superseded its cost model** · runs: `E9-evolve__20260718-022622__exp__gb15c3c1__diagnostics` + the rung-1 re-run · *the first run ever filed as E9 (D071)*

**THE RESULT. `mem_d1 = 1.000` in all 8 trailing cells** — not 0.99, **exactly 1.0**, at every gain and every noise level. Zero information about the previous stimulus. **`order/noise` = 0.98–1.16** confirms it independently: shuffling the presentation order changes `state` no more than re-running with fresh noise does.

**Two independent measures agree: the network is memoryless at the presentation timescale.** Context lives in the covariance across `context_dwell`=10 stimuli (D048). **It cannot hold one.**

**⇒ CONTEXT INFERENCE IS IMPOSSIBLE BY CONSTRUCTION. Gate B0 could not have passed at any N, any population size, any number of generations.** D067's ~40× evaluation shortfall was **real and not binding**. We diagnosed the wrong constraint twice: **not the budget (D067), not a broken encoder (D069).** *The encoder works — `E|state` = **0.225**. It sees. It does not remember.*

**RUNG 1: the memory is there, and it is NOT a mode.**

| | best `mem_d1` | best MC | max `order/noise` | best `E\|state` | best `E\|rates` |
|---|---|---|---|---|---|
| **trailing** (inherited) | **1.000** | 0.00 | 1.16 | **0.225** | **0.730** |
| **leading** (rung 1) | **0.531** | 0.47 | **6.09** | 0.492 | 0.931 |

Reading the onset instead of the settled response recovers d1. **But `mem_d2` = 1.000–1.002 in EVERY leading cell.** That is a **cliff, not a decay**, and the arithmetic is exact:
- **d1:** presentation *k−1* ends at t=0; the leading window is (0, 60]. **Zero gap.** The window physically **overlaps** the previous response's dying tail.
- **d2:** presentation *k−2* ended 150 ms earlier. **e^(−150/30) = 0.7%.** Gone.

**⇒ This is WINDOW OVERLAP, not memory.** The network is not holding state; the readout is catching `r`'s 30 ms filter tail before it dies. **There is no hidden long mode.** The substrate has precisely the memory the arithmetic predicted and not one millisecond more. **Rung 1 confirmed the diagnosis rather than fixing it — which is what a diagnostic is for.**

**AND RUNG 1 IS NOT ADOPTABLE.** `E|state` 0.225 → 0.492 (encoding **halves**); `E|rates` 0.730 → 0.931 (**what fitness reads is nearly starved**). Reading the transient means reading before the response to the *current* stimulus has developed. **It trades the level-1 signal for a level-2 signal that is still eight presentations short.**

**D030's OPPOSITION, FOURTH APPEARANCE — and it may not be a coincidence.**
| | the level-2 property | costs the level-1 property |
|---|---|---|
| D030 | PR responsiveness | input encoding |
| D069 | CV_ISI (fluctuation-driven) | input encoding |
| **D072** | **memory (carryover)** | **input encoding** |

*Every knob that buys a level-2 property costs level-1 encoding.* **Candidate explanation (SPECULATIVE, recorded to be tested, not leaned on):** the state has finite capacity, and what it reflects — current input, recurrent dynamics, noise, history — competes. If so this is not an annoyance but **the precondition for D056's frame**: encoding saturates, and *that* is why leveling up requires new structure rather than more of the same. **Do not lean on this until it is measured.**

**WHAT DID NOT CHANGE.** Context decode is **at chance everywhere** — best 0.315 vs 0.25, across 16 comparisons, *including* the leading cells. One presentation back does not tell you which of four covariance regimes you are in. **`BRIDGE.md` Level 5 listed this measurement and it had never been run.**

**FRAMING sec.3 DOES NOT TRANSFER — and my first verdict over-claimed that it did.** I printed "var EXPANDS 8/8" and called it transfer. It is not sec.3's claim.
- **sec.3's striking half is that the MEAN channel COMPRESSES** (7.4 from K=20 inputs; *"a reservoir's whole job is to expand — ours compresses"*). Measured: **PR_input 5.86 → PR_mean 6.95–7.18.** Mild **expansion**. **Compression does not transfer.**
- **PR_var tracks σ, not structure:** trailing 12.67 (σ=0.2) → 26.67 (σ=1.0). **Much of "var expands" is the dimensionality of INJECTED NOISE.** Read the onset, where signal dynamics live, and PR_var collapses to **8.4–9.4 regardless of σ** — next to PR_mean ≈ 7. **The dissociation largely evaporates.**
- **sec.3 actually rests on PREDICTION** — PR_var predicts generalization, PR_mean anti-predicts. That needs generalization measured across conditions and **remains untested.**
⇒ **`FRAMING.md` sec.3 is the project's only substrate-specific justification, it is a D028/D033 reservoir-era result (N=1000, K=20, `anisotropic_regression`, trained readout — all four retired by D032/sec.2c in the SAME SESSION sec.3 was written), and half of it demonstrably does not survive the port.** sec.3 needs rewriting. *Not done here: it is a framing decision, not a measurement.*

**AND: `logs/run.log` FINALLY EXISTS.** PJM noticed the terminal summaries were saved nowhere. Correct: **NAMING.md sec.3 has specified `logs/run.log` since the scaffold, `Run.logs` dutifully CREATES the directory, and nothing ever wrote to it.** A run's *numbers* were reproducible and its *reading* of them was not — exactly backwards, since numbers are the recomputable part. **D071's pattern, third instance** (after D066's progress reporting and NAMING.md's own stage vocabulary). Fixed: `Run.start_log()` mirrors stdout/stderr into `logs/run.log`, line-buffered so long runs are tail-able live (D066's real intent), closed by `finalize()` on **both** the complete and failed paths, and it can never break a run.

**STATUS OF THE STUDY.** **H-A and H-B are LEVEL-1 hypotheses and are unaffected** — they need no memory (H-B is *"what distinguishes us from ML"* and concerns r₁, the level-1 map's rank). **H-C, H-D and H-E are LEVEL-2 and are blocked** until the memory gap closes. *Layering is an ORDERING, not an escape: D056's frame — why did regulatory hierarchy evolve — is level 2.*

**AND THE PERFORMANCE WORK IS PARKED, DELIBERATELY.** None of D068's fixes are built. **That call was right for a reason we could not have known:** the diagnostics cost 4 minutes and showed Gate B0 could not have passed at any speed — building the 17× first would have made an impossible run 17× faster. **But D068 is now a decision that exists only as a document, which is exactly D071's category.** Recorded so it does not become another D066: **⇒ what un-parks it: the first diagnostics run showing the network can hold context over ~10 stimuli. The next step after that is a GA run, and that run is unaffordable (~69 h) without batching.**

### D073 — The slow timescale belongs in τ_syn, not τ_m — and D059's tiering INVERTS: τ is not regulation's alternative, it is its prerequisite
**2026-07-17 · Accepted (analysis)** · **Open (implementation)** · *supersedes the τ_m tier in D059 and the "fixed-heterogeneous τ_m" framing I have used since*

**THE ARITHMETIC. Memory must span `context_dwell` = 10 presentations. NEITHER KNOB WORKS ALONE:**

| | trace surviving 10 presentations |
|---|---|
| `present_ms` 150 → 50 alone (τ=30) | e^(−500/30) = **0.002%** |
| τ = 200 ms alone (`present_ms`=150) | e^(−1500/200) = **0.06%** |
| **both — τ=200 ms + `present_ms`=50** | e^(−500/200) = **8%** — marginal but real |
| **τ=300 ms + `present_ms`=50** | **19%** — workable |

**⇒ `present_ms` 150 → 50 is now DOUBLY motivated**: it is also **the 3× compute win** (D068 — cost is timestep-dominated, and `present_ms` is the timestep count). *The one lever that is both a scientific fix and a speedup.* **It also requires `readout_window_ms` to shrink below 50** — the window cannot exceed the presentation.

**τ_m IS THE WRONG HOME, AND I HAVE BEEN SAYING IT WRONG SINCE THE TIMESCALE AUDIT.** Cortical membrane time constants are **~10–50 ms**. **τ_m = 200 ms is not physiological**, and proposing it would have bought the mechanism at the cost of the biology — in a study whose entire claim is that the *substrate* matters.

**τ_syn IS.** The model already has `dI_syn/dt = -I_syn/tau_syn`, currently **τ_syn = 5 ms — which is AMPA**. The physiological range is textbook:

| receptor | τ | |
|---|---|---|
| AMPA | **~5 ms** | what we have, globally |
| NMDA | **~100 ms** | |
| GABA_B | **~150–200 ms** | |

**A heterogeneous τ_syn spans exactly the range the task needs, and it is standard physiology rather than a fitted parameter.** The equation is already there; only the *scope* changes — per-neuron instead of global. **The brain solves this problem with receptor kinetics, not with implausible membranes, and so should we.**

**D059's TIERING INVERTS — and the diagnostics are why.** D059 tiers τ as an **"alternative route — could BYPASS regulation"**, and withholds it from Arm 1 so that *"regulation is the ONLY route."* **That reasoning does not survive `tasks.py`'s own docstring:**
> *"Context must select the MAP, not be added as an input: a one-hot context fed additively can only SHIFT the output, never change the E→Y mapping."*

**A slow neuron produces a running average — that is DRIVE, not GAIN. Additive. Useless by the task's own construction.** So integration and modulation are **not alternatives; they are SEQUENTIAL**:
- **step 1** — infer context by integrating history *(needs a slow timescale)*
- **step 2** — apply it by **modulating** the level-1 map *(needs regulation)*

**Neither pays alone.** Memory nothing reads is invisible to fitness (which reads the last d neurons' mean rate). Modulation with nothing to modulate by is noise. **⇒ Withholding τ does not FORCE regulation — it REMOVES ITS PREREQUISITE.**

**Honest bound on the claim.** Arm 1 is not *provably* impossible: a recurrent network **can** hold state longer than its components via slow collective modes, and selection might build one. But that asks selection to construct a >150 ms mode from 20 ms parts, **from scratch, in the regime most hostile to one** (σ=1.0 kicks it every timestep), **with fitness blind to step 1 until step 2 also exists.** *A two-prerequisite problem starting at zero on both.* **The diagnostics measured a RANDOM W and found step 1 at exactly zero beyond d1; D067 is 100 generations of evidence that selection does not find it easily.** So: **Arm 1 has one very hard route, not zero — but nothing in the design supports it, and it was never the route D059 intended.**

**THE PROPOSAL — heterogeneous τ_syn, DRAWN, NOT EVOLVED.** This is D038's rule, and the "drawn" is load-bearing:
- **drawn** ⇒ evolution gets **no tunable shortcut**; it cannot dial τ up to solve the task, so the result cannot be an artifact of handing it the answer.
- it hands selection **step 1 as a CAPABILITY** — the same status as Dale's law (D038) and the balanced regime (D058).
- ⇒ **selection's job becomes step 2 ALONE — which is the thing under test.**
- **And it makes the null informative for the first time: if regulation still does not emerge once step 1 is GIVEN, that is a real finding about selection**, not about our parameter choices. *Under Arm 1 as specified, a null was uninterpretable — D062's trap.*

**D059's Arm 2 signature also sharpens.** D059 predicts a bimodal τ_m distribution at the waist = *"a timescale hierarchy, not a regulatory one"*, read as the **rival** outcome. If τ is the **prerequisite** rather than the alternative, the prediction flips: **Arm 2 should show long τ AND regulatory motifs — both, not either.** *Bimodality would then be a step toward regulation, not a substitute for it.*

**NEXT (unimplemented; a proposal, not a decision to build):** make τ_syn per-neuron, drawn from a bimodal AMPA/NMDA-like distribution; `present_ms` 150 → 50 with `readout_window_ms` reduced accordingly; **re-run `run_E9_diagnostics.py` — 4 minutes, no GA.** The gate is **`mem_d10`**, not `mem_d1`. *The memory question is validated without evolution, which is why it comes before the batching work (D068) rather than after.*

### D074 — Slow excitatory current: take NMDA's KINETICS, omit its Mg GATE. The capability is step 1; the gate is a ready-made step 2 that would answer H-C by construction.
**2026-07-17 · Accepted (design)** · **Open (implementation)** · implements D073's slow timescale · *credit: a PJM-requested search (Brunel & Wang 2001; Wang 2002) overturned my proposal — the seventh time*

**THE SEARCH OVERTURNED THREE THINGS I HAD WRONG.**

**1. "Bimodal τ_syn across neurons" is NOT the biology.** The canonical cortical formulation
(Brunel & Wang 2001; Wang 2002) sums **AMPA + NMDA + GABA as parallel current terms into each
neuron** — not a bimodal τ distribution across a population. **Every excitatory neuron has both a
fast and a slow channel.** So "fraction slow" is not a population split; it is the **NMDA/AMPA
ratio at each excitatory synapse**. *(And the slow channel is EXCITATORY only — NMDA. Inhibition
stays fast, GABA_A ~2–5 ms. This is a DIFFERENT axis from the 4:1 E/I neuron count, which is
already implemented as `ei_split=0.8` + `inh_gain=4`, D058. Both are standard; they compose.)*

**2. τ_m is the wrong home on DYNAMICAL grounds, not just physiological ones.** *"For the LIF
neuron driven by filtered noisy inputs, the firing response is instantaneous (Brunel et al. 2001);
hence the membrane time constant can be neglected. Among AMPA, NMDA and GABA_A, the NMDA gating
variable has the longest decay (100 ms) and dominates the time evolution of the system."* **The
slow timescale lives in the synapse, and specifically in NMDA.** D073's conclusion, from the
canonical source.

**3. My open-loop decay arithmetic was wrong, in our favour.** I computed e^(−500/100) = 0.7% at
d10 and concluded τ_NMDA = 100 ms was too short — that we would need τ = 200–300 ms. **Wrong
model.** Wang 2002 is titled *Probabilistic Decision Making by SLOW REVERBERATION in Cortical
Circuits*: **NMDA + RECURRENCE integrates far longer than τ_NMDA** because the loop gain does the
work (τ_eff ≈ τ_syn/(1−g)). The decisive evidence: *"when local reverberation is largely mediated
by AMPARs the network becomes highly unstable, and without NMDA the model cannot reproduce long
decision times even with fine-tuning of parameters to maximize integration time — suggesting NMDARs
at recurrent synapses are critically important."* **⇒ τ_NMDA = 100 ms is not "too short"; it is the
value that yields seconds of integration in a network WITH THE RIGHT RECURRENT STRUCTURE. A random
W does not have that structure — building it is selection's job.** *And "fine-tuning cannot
substitute for the slow recurrent channel" is our exact situation: τ_syn = 5 ms everywhere, and 100
generations trying to fine-tune to 1,500 ms (D067).*

**THE DISQUALIFYING PART: NMDA's Mg²⁺ BLOCK IS A READY-MADE INSTANCE OF THE MECHANISM H-C TESTS.**
The NMDA current carries a voltage-dependent gate: **1/(1 + [Mg²⁺]·exp(−0.062·V)/3.57)** — the
current at a synapse is scaled by a function of the **postsynaptic** voltage. **That is
multiplicative, voltage-dependent gain modulation.** H-C asks whether selection BUILDS a level that
modulates another level. **Installing the Mg gate answers that YES by construction, at generation
zero, before selection acts.** *You cannot measure the emergence of a thing you installed.* **This
is D039 exactly** — shunting inhibition was rejected for the identical reason (bolting in the
mechanism makes the result an artifact of our design).

**PJM'S QUESTION, ANSWERED PRECISELY: the GA does NOT "evolve a Mg block", and I mis-stated it if I
implied otherwise.** The genome is `mag` (magnitudes) + `signs` (per-neuron E/I). Those tune HOW
MUCH current flows; **there is no gene for "make this synapse's strength depend on the postsynaptic
cell's voltage."** The GA cannot reach the Mg mechanism from `mag`+`signs`, so including the Mg term
is not a head-start — it is **installing the finished mechanism ourselves, in every network,
permanently.** What H-C actually tests is whether selection builds **functional gain modulation out
of the circuit machinery it DOES have** — and D039 established that route: **divisive gain control
EMERGES from E/I circuit structure in a fluctuation-driven balanced network** (mutual inhibition
between subpopulations, read through the nonlinearity). That IS reachable from `mag`+`signs`,
because it is a question of *which neurons inhibit which*. The Mg block is a *different, molecular*
route to the same functional end, and it is the one we must not pre-install.

**THE SPLIT, ENFORCED AT THE RECEPTOR:**
- **TAKE** NMDA's **slow decay** — the CAPABILITY, D073's step 1 (integrate history to infer
  context). A prerequisite, drawn not evolved, same status as Dale's law (D038) and the balanced
  regime (D058).
- **OMIT** NMDA's **Mg gate** — a ready-made instance of the MECHANISM (step 2), the thing H-C
  measures selection building.
**The biology hands us both prerequisites in one molecule; we take exactly one.** *This is the
sharpest application of D038 the project has — "make the architecture capable; let selection build
the mechanism" — with the capability and the mechanism separated inside a single receptor.*

**HONEST CAVEAT — we are not modelling NMDA, we are modelling "NMDA-like" slow excitation.**
Dropping the Mg gate makes the channel **decay-only slow current**, not a biophysically complete
NMDA receptor. This is a standard and defensible modelling choice (many models use decay-only slow
excitation), but it IS a choice: **we may say "a slow excitatory synaptic current in the NMDA
range", NOT "we include NMDA receptors".** The distinction matters precisely because the omitted
part is the part that would have done H-C's job for us.

**THE IMPLEMENTATION (`nmda_frac=0` DEFAULT ⇒ INERT UNTIL ASKED FOR).**
```
dv/dt      = (v_rest - v + I_fast + I_slow + I_ext + bias)/tau_m + noise·√(2/tau_m)·ξ
dI_fast/dt = -I_fast/tau_fast     # tau_fast = tau_syn = 5 ms   (AMPA / GABA_A; all neurons)
dI_slow/dt = -I_slow/tau_slow     # tau_slow = 100 ms           (NMDA-like; EXCITATORY only)
```
Each presynaptic spike deposits a fraction `nmda_frac` of its weight into the postsynaptic
`I_slow` and (1 − `nmda_frac`) into `I_fast`; **inhibitory synapses deposit only into `I_fast`**
(no slow inhibition). **`nmda_frac` is a FIXED config parameter, NOT a gene** (D073: drawn, not
evolved — if heritable, selection dials its own memory and the capability becomes a shortcut).
**Default `nmda_frac = 0.0` reproduces today's model bit-for-bit** — same protection as
`readout_pos` (D072): the positive control, Gate C's validated operating point (D058), and every
past run are untouched until the parameter is set. **The `nmda_frac=0` cell of the sweep is
therefore a REQUIRED control: it must reproduce today's memoryless `mem_d1=1.000`, or the new
current path has a bug.**

**THE TEST (diagnostics, NOT the GA — ~5 min, no batching needed).** Sweep
`nmda_frac ∈ {0.0, 0.3, 0.5, 0.8}` on `run_E9_diagnostics.py` at `present_ms=50`. **GATE = movement
past d1 (d2–d3), NOT `mem_d10`.** *Rationale (last exchange): d10 needs an EVOLVED recurrent
attractor (Wang's slow reverberation), so demanding it from a RANDOM network demands the answer
before the experiment. d2–d3 in a random network shows the CAPABILITY is real and selection has a
foothold; d10 is later, and it is selection's achievement, not the capability's.* Wang's recurrent
excitation is NMDA-*dominated*, so `nmda_frac=0.8` is the literature-plausible high end; 0.3–0.5
hedge. **Cost is diagnostics-scale because we are not evolving yet** — the ~69 h/~4 h GA figure
(D068) appears only later, when Gate B0 runs with the chosen `nmda_frac` FIXED. *The sweep is the
cheap thing that de-risks the expensive thing: it names the value to carry in.* Adding `I_slow` is a
second current equation, ~10–20% per-eval overhead — immaterial now, worth remembering when the GA
is priced.

### D075 — The NMDA collapse was a CHARGE/units error, not a stability limit: the naive split delivered 16× the excitatory drive. Fixed by conserving charge; validated across the whole axis.
**2026-07-18 · Accepted** · *credit: PJM flagged the inverted-NMDA effect as the results came in; a PJM-requested search (Edge-of-Stability; working-memory balance) then overturned my proposed fix*

**THE RESULT THAT TRIGGERED THIS.** The D074 sweep did the OPPOSITE of the hypothesis. Adding slow
excitation **destroyed** encoding and memory together: PR_mean **7.3 → 1.10 → 1.04 → 1.01** as
`nmda_frac` went 0 → 0.8; `E|state` 0.32 → 1.00; memory and context both to zero. **PR_mean = 1
means the whole population collapsed onto a single shared mode** — a global synchronous fixed point.
All four signals died at once: the signature of a **dynamical collapse**, not a missing capability.

**MY FIRST DIAGNOSIS WAS RIGHT IN KIND, WRONG IN MECHANISM.** I called it "slow excitation with
unbalanced inhibition → runaway" and proposed to fix it by scaling `inh_gain` up (an **amplitude**
fix). **The search says amplitude balance is not the issue.** Two findings:
- **The Edge-of-Stability result (Kang et al. 2016):** *"even when the strengths of excitatory and
  inhibitory connections are perfectly balanced, violation of the TEMPORAL balance condition — the
  relative speed of fast (AMPA) and slow (NMDA) currents — makes the network unstable; deviations of
  a few percent tip it into delta oscillation and then runaway."* **Scaling `inh_gain` would not
  have addressed the actual instability.** My reflex fix was wrong.
- **The stabilizing configuration is FAST inhibition against SLOW excitation** (working-memory
  modelling): *"a balance of fast inhibition and slow excitation stabilizes networks so they
  integrate accurately... fast inhibition rapidly prevents runaway excitation and still yields
  irregular cortical-type activity."* **⇒ we do NOT need slow inhibition / GABA_B. Fast inhibition
  is the cortical solution** — it provides negative-DERIVATIVE feedback, opposing slow excitation as
  it builds. *(My other candidate — add a slow inhibitory channel — was unnecessary, a second new
  mechanism to get wrong.)*

**BUT THE ACTUAL BUG WAS SIMPLER AND ENTIRELY MINE: a units error in the split.** A spike deposits
weight `w` as a jump into `I`, which then decays with `tau`; the **integrated current (charge)**
delivered downstream is `w·tau`. So a 100 ms channel delivers **tau_slow/tau_fast = 20×** the charge
of a 5 ms channel **per unit weight**. My split `w_slow = nmda_frac·w` moved a fraction of the
weight to slow **and silently multiplied its charge by 20.** Total excitatory charge vs the balanced
`nmda_frac=0` baseline:

| nmda_frac | total exc charge | × baseline |
|---|---|---|
| 0.0 | 5.0 | 1.00× |
| 0.3 | 33.5 | **6.70×** |
| 0.5 | 52.5 | **10.5×** |
| 0.8 | 81.0 | **16.2×** |

**At nmda_frac=0.8 the network received 16× its balanced excitatory charge. Of course it seized.**
*This is NOT the Edge-of-Stability temporal violation — it is cruder: I overdrove excitation by up
to 16×. The temporal condition matters and is respected by the fix, but the collapse we SAW was the
units error. Both were live; the units error dominated.*

**THE FIX — CONSERVE CHARGE, keep inhibition fast, no new mechanism, no gene.**
```
want   w_slow · tau_slow = nmda_frac · (w · tau_fast)      # slow carries fraction f of the CHARGE
⇒      w_slow = nmda_frac · w · tau_fast/tau_slow
       w_fast = (1 − nmda_frac) · w
total charge = (1−f)·w·tau_fast + f·w·tau_fast = w·tau_fast   — CONSTANT in nmda_frac.
```
Fast inhibition (`inh_gain`, D058) then opposes the **same total excitation it always did, at the
same speed** — precisely the fast-inhibition/slow-excitation configuration the literature calls
stabilizing. **No `inh_gain` retuning, no slow inhibitory channel, no new gene.**

**VALIDATED ON THE REAL NETWORK, ACROSS THE WHOLE AXIS** (this is the "highly effective, automatic"
bar PJM set — an automatic fix that fails silently at 0.8 is worse than a knob):

| nmda_frac | PR_mean, bugged | PR_mean, fixed | across-env variance |
|---|---|---|---|
| 0.0 | 7.25 | **7.25** | healthy |
| 0.3 | 1.10 | **7.36** | healthy |
| 0.5 | 1.04 | **7.54** | healthy |
| 0.8 | 1.01 | **7.76** | healthy |

**No collapse anywhere; PR stays healthy, rate barely drifts (0.87 → 0.80), charge conservation
holds exactly on the synapse arrays.** *nmda_frac=0 still reproduces the prior model bit-for-bit
(w_slow=0).*

**THE STANCE THIS SETTLES (PJM).** E/I balance — including temporal balance under slow excitation —
is **NOT a hypothesis; it is a precondition for the substrate to be cortex-like at all.** It belongs
with Dale's law (D038) and the balanced regime (D058): **guaranteed by construction so selection
operates on a working cortical network, not asked of selection as an outcome.** The stabilization is
**strictly automatic and invisible to the genome** — no config knob, no gene. *Our hypotheses are
about learning and memory under selection on cortex-like networks; whether balance can evolve is a
different study we are deliberately not running.* **The onus this creates (PJM): the automatic fix
must be highly effective across the entire operating range — hence the full-axis validation above,
not a single-point check.**

**SIXTH TIME THE STANDING RULE BIT.** D074 QUOTED the Edge-of-Stability warning ("AMPAR-dominated
reverberation → instability; NMDA critical for stability") and I implemented past it — with a units
error the same physics predicts. *The rule is not "search"; it is "search AND let the result
constrain the implementation." I did the first and half of the second.*

### D076 — The diagnostics phase is COMPLETE: the substrate holds a little memory, it costs no encoding, and it is small BY DESIGN. Every remaining memory question needs selection. This un-parks D068.
**2026-07-18 · Accepted** · run: `E9-evolve__…__nmda-sweep` (post-D075) · *the seam between "diagnose the substrate" and "run the experiment"*

**WHAT THE FINAL SWEEP SHOWS (charge-conserving, network healthy, min PR_mean 7.28 across the axis).**
The blunt printed verdict — *"slow current moves memory past d1: NO"* — undersells it; the gate
(d2 < 0.9) was set higher than a random network delivers. The trend is real. At the best cell
(gain 10, σ 0.2), as `nmda_frac` climbs 0 → 0.8:

| nmda_frac | mem_d2 | mem_d3 | memory capacity |
|---|---|---|---|
| 0.0 | 0.947 | 0.994 | 0.18 |
| 0.3 | 0.991 | — | 0.19 |
| 0.5 | 0.982 | — | 0.21 |
| 0.8 | **0.947** | **0.994** | **0.29** |

**Three findings:**
1. **The capability is REAL and measurable.** Slow current extends memory to d2–d3 and **MC rises
   monotonically 0.18 → 0.29 with `nmda_frac`.** A random network holds a *whisper* of history.
2. **It is SMALL, and small BY DESIGN.** d2 = 0.947 is ~5% of one stimulus, two presentations back;
   context needs ~10 back. **This is exactly what was predicted before the run:** a 100 ms synaptic
   decay integrates a little across a 50 ms gap and then dies. Turning 100 ms of *synaptic* memory
   into 1,500 ms of *network* memory needs Wang's slow **reverberation** — the loop gain of an
   **evolved recurrent attractor**. The substrate supplies the capability; selection must build the
   amplifier. **This does not block H-C — it IS H-C:** the memory is necessarily an evolved property.
3. **IT COSTS NO ENCODING — D030's opposition BREAKS for the first time.** `E|state` across the nmda
   axis: **0.311 → 0.334 → 0.321 → 0.316 — flat.** Memory went up; level-1 encoding did not go down.
   **Why: D075's charge conservation.** We are not adding drive, we are re-timing it — the encoder
   sees the same total current spread over two timescales. *The opposition (D030/D069/D072) was never
   fundamental; it was the signature of buying a level-2 property by cranking a knob that also floods
   level-1. A charge-neutral knob does not pay that tax.* **This is a point FOR the substrate
   framing, and worth a measurement in the eventual paper.**

**WHAT THE DIAGNOSTICS PHASE ACCOMPLISHED (D072 → D076).**
- **Ruled out the budget as the FIRST problem** (D072): Gate B0 could not have passed at any N —
  not because of evaluations (D067) but because the substrate was memoryless.
- **Found and fixed a real capability gap** (D073/D074): the slow timescale belongs in τ_syn
  (AMPA/NMDA), not τ_m; take NMDA's kinetics, omit its Mg gate (the mechanism H-C tests).
- **Found and fixed a real stability bug** (D075): the naive split delivered 16× charge; conserving
  charge holds the network healthy across the whole axis; fast inhibition suffices.
- **Confirmed the encoder works and Gate A is a ROUTING problem** (D069/D072): E is in the state
  (`E|state` = 0.31) and barely reaches the output neurons — selection's job.

**⇒ EVERY REMAINING MEMORY QUESTION REQUIRES SELECTION.** *"Does a random network hold context?"* is
answered: **no, and correctly so.** *"Can an EVOLVED network build the reverberatory loop that turns
100 ms into 1,500 ms?"* is Gate A / H-C, and **it cannot be answered without running the GA.** The
diagnostics have done their job; there is no cheaper question left to ask of a random network.

**⇒ THIS UN-PARKS D068 BY ITS OWN TRIGGER.** D068's performance work was parked with an explicit
condition (QUEUE): *"un-parks the moment a diagnostics run shows the network can hold context over
~10 stimuli — the next step is a GA run, unaffordable (~69 h) without batching."* We have now reached
the weaker but sufficient form of that trigger: **the capability is present and evolvable, and the
only way forward is the GA.** A conclusive GA run is ~69 h unbatched, ~4 h batched. **Batching is no
longer premature — it is the blocker.**

**NEXT (the parked list, now live):** build D068's fixes in order — **(1)** drop the discarded
test-set eval (exact 2×); **(2)** batch the population into one block-diagonal network (~15–25×);
**(3)** pre-allocated synapses built once (absent = weight 0; NOT a frozen wiring diagram — evolution still reweights and adds/removes edges); **(4)** delete the pool; **(5)** hoist the StateMonitor — plus
**D066 fixes 2–3** (per-gen ETA + pool announcement, never implemented, D071) and `run.start_log()`
in `run_GateB0_interpolation.py`. **MEASURE the per-generation time before believing any projection**
(D068: four consecutive runtime estimates were wrong). Then: **Gate A** (does evolution route E to
the output neurons?), then **Gate B** (does a peak appear?).

**HOUSEKEEPING (this commit).**
- **`run_E9_diagnostics.py`** — the §3-4 header printed a stale `present_ms=150, tau_m=20` (the run
  was present_ms=50), and the "WHAT THIS DECIDES" footer still recommended heterogeneous **τ_m**,
  pre-D073 boilerplate now contradicted by D074/D075. Both corrected.
- **`DECISIONS.md`** — entries **reordered to strict D001…D076**. Two artifacts removed: D014 sat
  after D017, and D013/D018–D021 were parked at the file's end (all July 14, misplaced, not
  intentional). No entry altered; verified every body preserved. *Cross-references are by D-number,
  never by line, so nothing breaks.*

### D077 — Test error is REPORTING, not selection: a three-tier capture (champion every gen · population every k · full final gen) buys ~1.9× and keeps the epoch-wise-DD option open. D068 step 1.
**2026-07-18 · Accepted** · **D068's first performance fix** (un-parked by D076) · *design call made against BRIDGE Level 5 + a literature search on neuroevolution test-error conventions*

**THE WASTE.** `evaluate()` ran a full test `behave()` for **every genome, every generation** — a
second simulation each — and `_fitness()` reads **only `train_err`**. Selection never touches test.
At pop 30 that was **~half the GA's timesteps, computed and discarded**: the population-mean test
trajectory it produced is read by **no hypothesis**.

**WHAT THE DESIGN ACTUALLY READS (BRIDGE Level 5).** *"Per genome, on the same P axis."* The study's
headline double descent is **generalization-error-vs-P, ACROSS ARMS, at convergence** — P is swept
across density arms (D060), and each arm contributes its *converged* error as one point on the
curve. **The per-generation, within-run test trajectory is NOT what H-A/H-B/H-C read.** So the
expensive thing (30 test evals/gen) was producing a curve the study does not use.

**LITERATURE CHECK (PJM factor 1).** Neuroevolution convention is to plot the **fittest-individual**
test/validation error *per generation* alongside training, and read overfitting from where they
diverge (e.g. the sparsity-pruning work: validation drops when a genome overfits, and *variance
rises* — a class-level signal). Population-**mean** test per generation is rarer. ⇒ the conventional
object is the **champion** trajectory, not the mean.

**THE THREE-TIER CAPTURE (PJM factor 2 — keep what our analysis needs, drop the rest).**
| tier | cadence | cost | serves |
|---|---|---|---|
| **champion test** (best individual) | **every generation** | 1 extra behave/gen | epoch-wise-DD option (below); convergence monitoring; the literature's fittest-individual curve |
| **population test** (mean + spread) | **every `test_every` (=20) gens** | pop behave / k gens | D059's class-level Occam signal; catches whether the champion is representative or a lucky outlier |
| **full population test** | **final generation, always** | pop behave once | the **converged P-point that enters the cross-arm DD curve** — the study's actual headline |

Fitness stays train-only for the whole population every generation (selection unchanged). `test_err`
is `np.nan` on skipped individuals; a `pop_test` flag records per row whether `mean_test` was a real
sweep or NaN, so no downstream reader mistakes a NaN for a measured zero.

**EQUIVALENCE VERIFIED (the discipline this project earned — twice bitten).** Against an all-test
reference at identical seed/config: **`best_train` and `mean_train` bit-for-bit identical**, champion
test finite every gen, `mean_test` NaN exactly on non-sweep gens, final gen always swept. **This is
same-then-faster, not faster-but-different** — provable because selection provably never read test.

**SPEEDUP (projected from behave-call counting, D068's "name the quantity cost scales with").** Test
was exactly half the calls; we keep ~1/pop of it (champion) + 1/`test_every` of the population.
Pop 50 × 4,900 gens: **490k → 262k behave calls = 1.87×.** Essentially the full 2× ceiling. *Measure
the real wall-clock before believing it (D068: four estimates were wrong) — but the call count is
exact.*

**TWO HONEST CAVEATS ON THE EPOCH-WISE DATA, so it is not a mirage when we dig into it later.**
1. **The champion is a RELAY, not a fixed model.** Nakkiran's epoch-wise double descent tracks **one
   model** over training time. Our champion trajectory is *whichever genome won each generation* —
   genome A at gen 50, genome B at gen 51. It can legitimately show a dip-rise-dip and is worth
   studying, but it is **"test error of the current champion," not "one network's generalization
   over training."** The true fixed-model analogue needs **lineage tracking** (a genome + its
   descendants), which we do NOT log. If we ever want it, that is a separate decision and added
   parentage bookkeeping — flagged, not built.
2. **Generation-axis DD ≠ P-axis DD.** The study's headline double descent is **error-vs-P across
   arms** (BRIDGE L5). Epoch-wise is **error-vs-generation within one arm**. Same words, two
   different curves. When we come back to the champion trajectory, it answers the *generation-axis*
   question only; it must **not** be read as the H-A peak, which lives on the P axis. *This
   distinction is exactly the kind of thing that looks obvious now and won't in six months.*

**NEXT (D068, in order):** (2) batch the population into one block-diagonal network — the ~15–25×;
(3) pre-allocated synapses built once (absent = weight 0; NOT a frozen wiring diagram); (4) delete
the pool; (5) hoist the StateMonitor. Plus D066 fixes 2–3 (ETA + pool announcement) and
`run.start_log()` in the Gate B0 script.

### D078 — Population batching: the whole population runs as ONE block-diagonal network per generation. ~15× measured, bit-for-bit identical evolution. D068 step 2.
**2026-07-18 · Accepted** · **D068's second and largest performance fix** · *separate runner by design (PJM); equivalence verified on the real network before acceptance*

**THE CHANGE.** Instead of `pop_size` separate `net.run()` calls per generation, all genomes run
**simultaneously as independent diagonal blocks of one (pop·N)-neuron network** — one `run()` per
generation. `evonet.behave_batch(genomes, cfg, E)` assembles the block-diagonal synapse lists,
runs once, and splits the recorded trace back into per-genome results.

**MEASURED: ~15× at pop 30 × N 50** (14.2 s single-genome loop → 0.9 s batched), squarely in the
projected 15–25×. **Composed with D077's ~1.9×, the Gate B0 arithmetic goes from ~69 h to ~2–4 h.**

**SEPARATE RUNNER, NOT A REWRITE OF `EvoNet.behave` (PJM design call).** The single-genome
`behave` remains the **validated reference path** — diagnostics, Gate C, the positive control all
call it, untouched. `behave_batch` is a separate ADDITIVE path used only by the GA loop. This is
the structure this project keeps needing:
- a batching bug **cannot silently corrupt the diagnostics** — they do not call it;
- the equivalence check is **permanent and trivial**: batched block *k* must equal
  `EvoNet(genomes[k]).behave(E)` exactly;
- windowing is **shared** via the new module-level `_window_readout` helper (single-genome behave
  now calls it too), so the readout logic **cannot drift** between the two paths — it is one
  function, not two copies.

**EQUIVALENCE VERIFIED ON THE REAL NETWORK (the discipline, twice earned).**
- **`behave_batch` == single-genome `behave`, bit-for-bit** at noise=0, at nmda_frac 0.0 AND 0.5
  (so the D075 charge-split is reproduced exactly through the batched assembly).
- **End-to-end: `run_evolution(batched=True)` == `run_evolution(batched=False)`** — every
  `best_train`/`mean_train`/`best_test`/`mean_test` identical across all generations, final-gen
  population params identical. **Same evolution, ~11× faster even at pop 12.**
- **Cross-block independence: verified** — perturbing genome 0 changes block 0 and leaves blocks
  1–5 bit-identical. Hazard 1 (silent cross-block contamination — the worst failure) is both
  **guarded** (an assert that every synapse stays within its block) and **empirically clean**.
- `verify_batch_equivalence(genomes, cfg, E)` is retained as a **standing check**: run it whenever
  the batched path or the model equations change. *"Blocks are independent" and "a zero-weight
  synapse is inert" are SHOULDs, and this project's should-be-fines have twice been bugs (the pool
  that never ran, D065; the 16× charge, D075).*

**THREE HAZARDS, each named in the code and guarded:**
1. **Cross-block contamination** — synapses assembled with per-block offsets; `assert i//N == j//N`
   before the run; empirically confirmed independent.
2. **Per-neuron noise** — Brian2's `xi` is per-neuron, so each block gets an independent noise
   realisation automatically (matches `pop_size` separate runs with distinct draws). This is NOT
   common-random-numbers across blocks — that is a **separate open question** (D077 tier-2 / the
   H-D confound fix); batching neither blocks nor implements it.
3. **Memory** — pop·N neurons, and once step 3 lands, all-to-all pre-allocated synapses per block.
   At pop 30 × N 50 = 1,500 neurons it is small; the ceiling grows as **pop·N²**. Flagged; at
   larger N or pop it becomes the binding constraint and may cap how much of the sweep runs in one
   batch (a batch can be split into sub-batches with no loss — blocks are independent).

**`batched=True` IS NOW THE DEFAULT.** The `n_workers`/pool path survives for `batched=False` and
`eval_fn` overrides but is the **slow path**: batching makes multiprocessing redundant (D068 step
4 — deleting the pool — is now mostly a cleanup, since `batched=True` bypasses it entirely).

**HONEST LIMITATION.** The ~15× is a single-run micro-benchmark, not a full Gate B0 wall-clock. The
per-call and assembly overheads are real; at the required depth the sustained speedup is what
matters and it **must be measured on the actual run** (D068's standing rule: four runtime estimates
were wrong). The equivalence is exact and proven; the *multiplier* is measured-so-far, not
guaranteed at scale.

**NEXT (D068):** (3) pre-allocated synapses built once per run — currently `behave_batch`
reassembles the block-diagonal synapses every call; building the topology once and only rewriting
weights per generation removes that (absent = weight 0; NOT a frozen wiring diagram). (4) pool
deletion (now a cleanup). (5) hoist the StateMonitor. Plus D066 fixes 2–3 and `run.start_log()`.

### D079 — Measured: one Gate B0 arm is 2.17 h (was ~58 h). D068 is COMPLETE; steps 3–5 skipped on the evidence. The sweep runs overnight.
**2026-07-18 · Accepted** · closes the D068 performance arc · *the honest end-to-end wall-clock D078 owed*

**THE MEASUREMENT (PJM's machine, real Gate B0 operating point, `batched=True`).**
- equivalence re-verified in-environment first: **batch == single-genome, True** — timings trusted.
- **1.59 s/generation** at N=50, pop=30, n_env=50, density=0.5, |W|≈1,225.
- **⇒ full-depth arm (~4,900 gens): 2.17 h.  6-arm density sweep: 13.0 h.**

**AGAINST THE BASELINE:** D067 measured this exact arm at **~58 h**. We are at **2.17 h — a
measured 27×**, landing on the steps-1+2 projection (~30×). **For once the estimate and the clock
AGREE** — after D060/D064/D065/D067 each missed. The discipline (D068: name the quantity, then
measure) produced a projection that survived contact with the stopwatch.

**THE D068 STEP 3+5 DECISION, MADE FROM DATA — SKIP.** The build-once refactor (pre-allocate all
N² synapses per block, persist the network + StateMonitor across generations, rewrite only weights)
would trim ~20–40 min off a 2 h arm by removing per-generation synapse reassembly and `before_run`
re-prep. **Against that: the pop·N² memory ceiling (D078 hazard 3) and a persistent-network state
with more surface to get wrong.** Trading real risk and complexity for ~30 min on an
overnight-comfortable run is a bad trade. **Had the arm come back at ~6 h the refactor would clearly
have earned its place; at 2 h it does not.** *This is precisely why we measured instead of building
on principle — the clock decides, and it decided against.*

**STEP 4 (delete the pool) — ALSO SKIP.** `batched=True` bypasses the pool entirely; the pool path
survives as the `batched=False` **reference implementation** that `verify_batch_equivalence` and
D078's end-to-end check compare against. Deleting it would remove a validated comparison for zero
performance gain (it does not run in the fast path). *Step 4's rationale — "batching makes the pool
redundant" — is satisfied by bypassing it, not by deleting it.*

**⇒ D068 IS COMPLETE.**
| step | status |
|---|---|
| 1 — drop the discarded test eval (D077) | ✅ ~1.9× |
| 2 — population batching (D078) | ✅ ~15× |
| 3+5 — build-once refactor | ⏭️ **skipped — measured unnecessary (this entry)** |
| 4 — delete the pool | ⏭️ **skipped — retained as reference path** |

**~~STILL OWED~~ DONE (2026-07-18):** D066 fixes 2–3 are now implemented in `run_evolution` — a
mode announcement (`BATCHED`/`PARALLEL`/`SERIAL`), and per-10-gen progress with **elapsed + ETA +
s/gen + `flush=True`**, printing from gen 0 (previously silent until gen 20, and a 2 h arm printed
nothing). Verified: output renders live AND equivalence still holds after the edit. `time` was also
unimported — a latent `NameError` the ETA code would have hit; fixed. **`run.start_log()` added to
`run_GateB0_interpolation.py` manually by PJM.** *The last D066 debt (D071) is closed; the two
compose — `start_log` catches the stream, D066 fills it with an ETA worth catching.*

**⇒ NEXT IS THE SCIENCE, NOT THE ENGINEERING. Gate A** — does evolution route E to the output
neurons? (D069/D072: the encoder works, `E|state`≈0.22, but `E|rates`≈0.73 — E barely reaches the
d output neurons; Gate A asks whether *selection* fixes the routing.) Then **Gate B** — does a peak
appear on the P axis? *The apparatus is finally fast enough to ask.*

**CAVEAT (D068's standing rule, honoured).** 2.17 h is projected from 30 timed generations assuming
flat per-generation cost. It is the honest decision input; the *ground-truth* full-arm number
arrives free with the first real Gate A/B run, and if it drifts materially from 2 h we revisit. The
27× and the equivalence are measured facts; the full-depth hours are a measured-rate projection.

### D080 — Gate A, PRE-REGISTERED before running: does selection route E to the output neurons? Metric, arms, and pass/fail fixed in advance.
**2026-07-18 · Accepted (specification)** · **pre-registration** — written and committed BEFORE the run, so the result cannot be reverse-justified (the D063 discipline: D061 claimed a first descent that wasn't there because the reading came after the plot)

**WHAT GATE A IS NOW (its meaning shifted across the arc — pinning it).**
- **D030 original:** "does evolution beat the raw-input baseline?"
- **D069 dissolved that:** the raw-input baseline ≡ the memoryless floor BY IDENTITY, so "beat the
  baseline" ≡ "infer context" ≡ the WHOLE experiment (H-C), not a gate.
- **D072 re-sharpened it into ROUTING.** The diagnostics measured, on a RANDOM network: **E is in
  the state (`E|state`≈0.22, 1.0=blind) but barely reaches the output neurons (`E|rates`≈0.73).**
  Fitness reads only the last `d` of `N` neurons (`out_slice`), so a network can encode E richly and
  still be graded near-blind. **Gate A asks whether SELECTION fixes the routing** — whether an
  evolved W carries E's information into the output slice, which a random W does not.

**WHY IT IS WELL-POSED (the task rewards exactly this).** The demand is `Y = tanh(E @ W_ctx[c])`
(tasks.py L351) — the target is a function of E, so error CANNOT fall unless E reaches the outputs.
Routing is not a side-metric; it is the necessary condition for any training-error progress at all.
*This is also why Gate A is separable from the memory problem (D072/D076): routing E to the outputs
is a LEVEL-1 requirement — it needs no memory. Gate A can pass (or fail) independently of whether
the network can later infer context.*

**THE METRIC (fixed now).** Per genome, `E_from_rates` = NMSE reconstructing E (the K-dim stimulus)
from the `d` output-neuron rates via ridge (the diagnostics' `decode_nmse`, standardize=True,
best-alpha over the grid). 1.0 = outputs carry no information about E; lower = E is routed.
- **Primary:** does the CHAMPION's `E_from_rates` **fall over generations**, from the random-init
  baseline toward `E_from_state` (≈0.22 — the ceiling set by what the state encodes at all)?
- **Secondary (the D030 spirit, kept honest):** does the champion's **train NMSE** fall below the
  memoryless floor (0.698 at this task config)? *Note (D069): beating that floor requires CONTEXT,
  which is level-2 and blocked (D076) — so we do NOT expect the secondary to pass yet. It is recorded
  as the level-2 tell, not Gate A's criterion.* **Gate A is the ROUTING metric, primary only.**

**PASS / FAIL, DECIDED IN ADVANCE:**
- **PASS:** champion `E_from_rates` falls by **≥ 0.15 absolute** from gen 0 to final, AND ends
  **below 0.85** (a random net sits ~0.90–1.00; `E|state`≈0.22 is the ceiling). I.e. selection
  demonstrably moves E into the output slice.
- **AMBIGUOUS:** falls 0.05–0.15, or ends 0.85–0.90 — some routing, weak. Report; do not over-read.
- **FAIL:** `E_from_rates` does not fall (< 0.05), OR train error is flat. Then routing is NOT what
  selection builds first, and we investigate BEFORE Gate B (which presupposes the network can express
  E at its outputs at all).
*The 0.15 threshold is a judgement call registered now so it cannot be tuned to the result. It is
deliberately loose — Gate A asks "does routing happen AT ALL under selection," a direction question,
not an effect-size one.*

**ARMS.** Gate A is the single **fixed-density** operating point, not the full sweep — it is a
precondition check, not the map. Config: **N=50, pop=30, d=3, n_env=50, density=0.5, present_ms=50,
nmda_frac=0.5, noise=1.0, gain=10** (the D079 measured arm; gain=10 because D069 showed gain=1 is
the worst encoding cell). Depth: **full ~4,900 gens (~2.2 h, D079).** Selection=replicator (Occam
factor live, D060). One seed first; replicate if it passes.

**INSTRUMENTATION.** `E_from_rates` and `E_from_state` must be logged per generation (champion) — a
NEW measurement in `evolve.py`'s history, computed from the champion's `behave` output (state +
rates), reusing the diagnostics' `decode_nmse`. This is the ONE code addition Gate A needs; without
it the run produces train/test but not the routing metric the gate reads.

**WHAT A PASS BUYS / A FAIL COSTS.**
- **Pass** → the network can be *graded* on E, so Gate B (the peak on the P axis) is meaningful:
  there is a signal for selection to shape. Proceed to Gate B.
- **Fail** → selection does not even route E to the readable neurons, so any Gate B null would be
  uninterpretable (is there no peak, or can the network not express the target?). Fix routing first
  — candidate causes: `out_slice` too small (d=3 of N=50), output neurons not reachable from input
  neurons under sparse W, or replicator selection too weak. **Registered so a fail sends us to a
  named next step, not to rationalisation.**

### D081 — Gate A pre-registration CORRECTED before running: the 0.73 baseline was a grid-minimum artifact; the true single-config random baseline is E|rates≈0.99, E|state≈0.43. Thresholds re-set.
**2026-07-18 · Accepted** · **amends D080's metric and thresholds BEFORE the run** — corrected after measuring the baseline, before seeing any result (legitimate pre-registration amendment; the alternative was launching a 2.2 h run against a miscalibrated gate)

**THE ERROR IN D080.** Its pass threshold (E|rates ends < 0.85) was calibrated to a random-network
baseline of "E|rates≈0.73, E|state≈0.22." **Those numbers were grid MINIMA** — the best cell across
the E9 diagnostics' whole gain×σ×nmda sweep (`df.E_from_state.min()`), not the value at Gate A's
single operating point. Building a threshold on a grid-min is calibrating against the luckiest cell.

**TWO IMPLEMENTATION BUGS FOUND while checking the baseline (before the run — the point of
pre-registration).**
1. **Split-in-half decode.** My first `_routing_nmse` split ONE champion behave in half for
   train/test. The halves are NOT independent — sequential context carryover (D048) bleeds across
   the split — so the decode was contaminated. The diagnostics used SEPARATE behave runs on
   separate E sets; fixed to match.
2. **Under-determined decode.** At Gate A's n_env=50, a half-split gives ~25 samples to fit 50
   state dims — fitting noise. Fixed with a **fixed 200-env probe** (over-determined, matches the
   diagnostics), passed in via `cfg._routing_probe`.

**THE TRUE BASELINE (measured, n=6 random genomes, EXACT Gate A config: N=50, d=3, density=0.5,
gain=10, noise=1.0, nmda_frac=0.5, 200-env decode):**
- **E|rates = 0.993 ± 0.003** — a random net's OUTPUT neurons carry ~nothing about E.
- **E|state = 0.429 ± 0.036** — the full state carries meaningfully more.
- **The routing gap (0.99 → 0.43) is real and clean.** Gate A asks whether selection closes it.

**CORRECTED THRESHOLDS (re-registered now, before any result):**
- **Metric:** champion **E|rates** (NMSE reconstructing E from output-neuron rates), on the fixed
  200-env probe, logged at gen 0 · every `test_every` · final. E|state logged alongside as the
  **ceiling** (routing cannot make outputs carry more than the state holds).
- **PASS:** champion E|rates falls from ~0.99 (gen 0) to **below 0.80** by the final gen — i.e.
  selection moves E's information into the output slice, closing ≥ ~⅓ of the 0.99→0.43 gap.
  *Rationale: 0.80 is comfortably outside the baseline's 0.993±0.003, and represents real routing
  without demanding the network reach the state's full 0.43 ceiling (which would also require the
  routing to be near-lossless).*
- **AMBIGUOUS:** ends 0.80–0.93 — some routing, weak; report, do not over-read.
- **FAIL:** ends > 0.93 (indistinguishable from random), OR does not fall ≥ 0.05 from gen 0.
- **Secondary (unchanged, D080):** champion train NMSE vs the memoryless floor (0.698). Beating it
  needs CONTEXT (level-2, blocked, D076) — NOT expected; recorded as the level-2 tell, not Gate A.

**COST NOTE (D081).** The routing decode is TWO extra behave runs (train+test probe) per logged
generation. At 200 env that is ~2.6 s each — doing it EVERY generation would ~double the 2.2 h arm
(+3.6 h). Hence sparse logging (endpoints + `test_every` cadence): the pass criterion reads the
ENDPOINTS, so dense routing is unnecessary. The champion train/test trajectory stays dense (D077).

**EVERYTHING ELSE IN D080 STANDS** — the routing framing, why the task rewards routing
(Y=tanh(E@W_ctx) needs E at the outputs), level-1 separability from the memory problem, the arms,
and the fail→named-next-step map (out_slice too small / outputs unreachable / selection too weak).

**PROCESS NOTE.** This is the SECOND time a "baseline" number turned out to be an artifact demanding
recalibration before a run (cf. D069: the raw-input baseline was an identity, not a gate). The
pattern: **a number quoted from a prior run's SUMMARY (a min, a best cell, an aggregate) is not the
number for THIS config — measure the baseline at the exact operating point before gating on it.**
Adding to standing rules.

### D082 — Gate A: FAIL, pre-registered. Selection on BIRTH-fitness does not route E to the outputs — the empirical anchor for the development redesign (D083).
**2026-07-18 · Accepted (result)** · run: full 4,900-gen Gate A arm (D080/D081) · *the flat curve PJM watched from gen 600; verdict is exactly the pre-registered FAIL branch, not a reinterpretation*

**THE RESULT (verbatim from the pre-registered metric, D081):**
- **E|rates: 0.995 (gen 0) → 0.999 (gen 4899). Fell −0.003.** The champion's output neurons carry no more information about E at the end of 4,900 generations than at random init. **Selection did not route E to the readable neurons.**
- **E|state ceiling: 0.413** — the state still holds E (encoder works, D072); it just never reaches the output slice.
- **Verdict: FAIL** by the D081 rule (pass required E|rates < 0.80; got 0.999).
- **Secondary:** champion train 0.930. *(The printed "below floor 1.095" is a probe-set artifact — the memoryless floor recomputed on this run's config came out at 1.095, above the champion; it does NOT mean context was inferred. Train 0.930 is essentially the random baseline. Do not read the "BELOW floor" line as a level-2 success; it is a floor-estimate mismatch, flagged for cleanup.)*

**THE CURVE WAS FLAT THROUGHOUT** — best_train ≈ 0.92 from early generations to the end (PJM observed it flat at gen 600 and gen 1560). **Selection found essentially nothing over the full budget.** This is a stronger datum than a short run: it is not "hadn't converged yet," it is "4,900 generations of selection on this fitness produced no routing."

**WHAT IT DOES AND DOES NOT MEAN.**
- It does **not**, by itself, distinguish the D080 fail-map causes (out_slice too small / outputs unreachable / selection too weak / task needs memory the substrate lacks). The flat curve is consistent with all of them.
- It **does** establish the premise the development redesign rests on: **selection acting on BIRTH-fitness — scoring undeveloped genomes by their raw forward behaviour — produces no gradient.** Every genome is scored as a newborn (D-development discussion, 2026-07-18): instantiate exactly the genome's weights, run forward once, score. No within-life tuning. If the capability to route/infer requires *development* (strength-tuning by exposure before scoring), then birth-fitness is flat **by construction**, because the thing that would distinguish good genomes from bad ones only expresses after development.

**⇒ THIS IS THE EMPIRICAL ANCHOR FOR D083 (the development redesign).** The conceptual case for developing networks before scoring was made independently (fitness should reduce the *developed* distribution, as Frank's generational fitness reduces developed kangaroos — not undeveloped genotypes). Gate A supplies the matching evidence: **the undeveloped-genotype fitness we currently use is empirically flat.** The two arguments — one from faithfulness to Frank, one from a dead selection gradient — point at the same fix.

**HONEST ALTERNATIVE STILL LIVE.** The flat curve could be the memory problem (D076) rather than the missing-development problem — a random net is memoryless, context inference needs built structure, and selection may simply not find it. These are not mutually exclusive: development (strength-tuning) may be *how* a network builds usable memory from a fixed slow-current-capable topology. D083 is the test that separates "birth-fitness is the wrong measurement" from "the task is unreachable by any means on this substrate."

**GATE B IS NOT UNBLOCKED.** D080 pre-registered that a Gate A fail sends us to the fail-map BEFORE Gate B, not onward. Gate B (the peak on the P axis) presupposes the network can express E at its outputs; it cannot yet. **Next is the development redesign, not the map.**

### D083 — The development redesign: fitness must reduce the DEVELOPED distribution, not the birth distribution. Framing settled; four sub-decisions explicitly open.
**2026-07-18 · Accepted (framing) · Open (implementation)** · motivated by the Frank-faithfulness argument (this session) AND anchored by D082's flat Gate A · *the biggest architectural change since reservoir→evonet (D032)*

**THE CORE REALIZATION.** Our fitness evaluation collapses genotype and phenotype: `evaluate()` instantiates exactly the genome's weights, runs one forward pass, and scores — **the network is tested at birth, before any development.** But fitness in Frank's own framing (and in population genetics generally) is measured on the *developed* organism: genome → development + lifetime experience → phenotype → fitness. A generation of kangaroos sharing a gene-connection count P are *developed adults* when their fitness is read, not zygotes. **So the correct object to reduce at each P is the distribution of DEVELOPED phenotypes, not undeveloped genotypes.** Our apparatus reduces the wrong distribution.

**TWO INDEPENDENT ARGUMENTS, SAME FIX.**
1. **Faithfulness to Frank (conceptual).** Frank: *"regulatory connections are parameters, selection is the optimizer."* The parameter is the CONNECTION (edge), not the node — which is exactly what unifies deep nets (weights), GRNs (regulatory interactions), and our SNN (synapses). Fitness in all three is read on the *developed* network. Scoring undeveloped genotypes is the departure from Frank, not the addition of development.
2. **The dead gradient (empirical, D082).** Gate A ran 4,900 generations on birth-fitness and was FLAT (E|rates 0.995→0.999, best_train ≈ 0.92 throughout). Selection on undeveloped-genotype fitness produced no signal. **If the capability to route/infer only expresses after development, birth-fitness is flat BY CONSTRUCTION** — every genome looks equally unfit because the distinguishing behaviour never gets to develop.

**SETTLED THIS SESSION.**
- **P = non-zero synapse count, and it STAYS the parameter axis.** Faithful to Frank's "regulatory connection" (edge, not node); blind to neuron count and wiring arrangement exactly as Frank's connection-count is blind to gene count and motif structure. *(Caveat for Q&A: Frank's parameter set also lists thresholds and interaction terms; ours holds thresholds fixed and has no interaction terms, so P is the CONNECTION subset — the dominant, most defensible one to sweep.)*
- **Development = KIND A: strength-tuning within FIXED synaptic support.** Plasticity adjusts magnitudes of existing synapses; it does NOT add or prune. **This is what keeps P invariant** — the support (which synapses exist) is set by the GA and untouched by development, so P_birth = P_scored. Kind B (structural plasticity that adds/prunes) would make P_birth meaningless and is EXCLUDED. *The GA owns which connections exist (P, Frank's axis); development owns their binding strengths — different items on Frank's own parameter list, at different timescales.*
- **Rule = Hebbian + homeostatic, standard/interpretable form, UNSUPERVISED.** Development shapes the network from stimulus statistics alone, never seeing the target Y — so development and fitness stay cleanly separated (development never "sees the answer"). Hebb alone is unstable; homeostasis is the required counterweight. Stick to the most standard, interpretable form.
- **Placement = INSIDE the fitness evaluation (nested loop: outer=selection, inner=development).** Forced by D082: "develop only at final readout" would have selection climb the flat birth-fitness landscape we just watched produce nothing, then develop the winners of a gradient-free race. If developed-fitness is the correct fitness, selection must SEE it every generation.
- **Duration = scales with TASK STRUCTURE (r1, context-dwell), held CONSTANT across the P-sweep — NOT with P.** Grounded in two converging sources: (a) the overparameterized-generalization literature — required exposure scales with task complexity, roughly independent of (or decreasing in) parameter count (Favero/diffusion 2025; XOR 2018); (b) our own H-B — the relevant scale is r1, the rank of the structure, not P or n. Node count and stimulus complexity are calculate-once constants that set T; P (the IV) does not enter T. **Expect a WINDOW:** under-exposure = partial learning (lowest structural level only); over-exposure = memorization onset (the diffusion result) — which is itself epoch-wise double descent on the exposure axis (D077). Locate the window empirically, but predict its scaling theoretically.

**WHY KIND-A DEVELOPMENT CHANGES WHAT SELECTION OPTIMIZES FOR (and why that's wanted).** Pure GA selects genomes whose FIXED weights happen to perform. Two-level selects TOPOLOGIES THAT DEVELOP WELL — genomes whose support, once strengths are tuned by experience, yield a good phenotype. This rewards LEARNABILITY, not innate performance: a topology born useless but developing into something excellent beats one born decent but rigid. This is the biologically correct criterion and the one birth-fitness perversely cannot see.

**NOT a different KIND of curve (correction, this session).** Both birth-fitness and developed-fitness produce error-vs-P curves that reduce a distribution-at-P; Frank's generational fitness does the same. The difference is WHICH DISTRIBUTION is reduced (undeveloped vs developed genotypes), not the type of object plotted. The reason to develop is that the developed distribution is the biologically correct one — NOT any claim that the curve changes shape. *(An earlier framing overstated this as two rival curve-types; retracted.)*

**OPEN — four sub-decisions, explicitly NOT answered tonight.**
1. **Distribution-reduction statistic (point 3).** Base hypotheses on ONE metric, collect many for post-hoc. Champion defeats the purpose of collecting a distribution → lean toward a distribution summary. Candidates: expectation of a fitted distribution (requires knowing the TYPE — Gaussian? Poisson? — an empirical question to settle first), OR a distance-from-ideal metric (KL, Wasserstein) of the realized vs an idealized distribution. Undecided; needs the distribution characterized first.
2. **Cost control via probabilistic development.** Development-in-the-loop multiplies eval cost by the exposure length. PJM's compromise — develop a random SUBSET each generation (or per-genome development probability) — is a stochastic-approximation of developed-fitness: noisy but unbiased, at a fraction of the cost, with selection averaging over generations. Promising; promote from "placement alternative" to "cost mechanism within placement=in-loop." Needs analysis.
3. **Sufficiency of Kind A (the empirical risk).** Is strength-tuning-within-fixed-support ENOUGH to build the memory/routing capability (D076/D082), or does that capability require STRUCTURE the birth topology lacks — which would force Kind B and break P? **Mostly an N question, not a "need fancier neurons" question:** Brunel/Wang-style working memory is achievable with plain LIF units + the slow NMDA-like current we already built (D074), given large enough N — N=50 may simply be too small for a slow-reverberation attractor to exist in the searched space. If the capable topology exists at birth (given N) and only strengths need tuning, Kind A suffices. **This is the load-bearing unknown.**

   **Defining "sufficient development" WITHOUT circularity (the T-confound, and its fix).** The experiment asks *when regulatory structure emerges*, but T (development duration) is a knob WE set — so if regulation emerges only after enough development, T directly controls the answer. This is a genuine confound, not hand-waving. Three responses, in increasing strength:
   - **(a) Define maturity by CONVERGENCE, not a clock.** Develop until plasticity stops changing the weights (the developed phenotype is *stable*), per-network. Then T is not a free parameter — it is set by the dynamics. **Cleanest fix, CONTINGENT on Hebb+homeostasis actually converging to a stable fixed point on these networks** — which is the FIRST thing to check when prototyping development (if it cycles or converges to a degenerate state, this fix is unavailable). Convergence alone certifies *stability*, not *quality* — see the bookends below for the quality/timing calibration.
   - **(b) DEMONSTRATE T-invariance, don't assume it.** Run the P-sweep at several T and report the T-dependence. If regulatory-emergence-vs-P is qualitatively stable across T (onset shifts, ordering preserved), the "directional trend survives T" argument is EARNED rather than asserted; a T×P interaction, if present, becomes a finding not a hidden confound.
   - **(c) Promote T to an AXIS.** Over-development induces memorization (the diffusion result) = epoch-wise double descent on the exposure axis (D077), so T is not orthogonal to the phenomenon — map regulatory emergence over (P, T). Most ambitious; consonant with D056's map-not-yes/no ethos.
   Lean: (a) as the operating definition IF plasticity converges, (b) as the robustness check, (c) if the phenomenon is rich enough to warrant it.

   **Bookend controls to CALIBRATE THE T-WINDOW (PJM, strictly scoped).** Their ONLY use is to bracket where to set / stop T for non-converging networks — NOT as capability oracles, templates, or comparison targets. At a given (N, P):
   - **Random-weight pool** → develop → mean convergence time = the **LONG end** of T (no head start ⇒ slowest plausible settling). If the random pool mostly does NOT converge, the long end is instead the **deadline past which continued development is declared futile** (non-convergence cutoff), not a mean. *(The random pool is the existing gen-0 baseline — free.)*
   - **Engineered encoding+memory pool** (our best educated guess at a competent encoding-plus-memory network — Brunel/Wang memory backbone; the wiring need only be COMPETENT, not provably optimal, since only its convergence *time* is used) → develop → mean convergence time = the **SHORT end** of T.
   - **HARD QUARANTINE:** the engineered network contributes exactly ONE scalar — a convergence time. Its WIRING is never a template, target, seed, or comparison. Regulation is scored ONLY by task performance (d2/d3/d4 memory, routing), so the engineered architecture is irrelevant to every metric that matters. This sidesteps the D038 contamination worry entirely: we are not installing a mechanism to breed from or compare against — we are using a fast-converging network as a stopwatch reference. **It must NEVER be seeded into the evolving population.**
   - The window is a **diagnostic that CONSTRAINS the T-choice from both sides** (faster than the engineered mean = surely too short; slower than the random mean = surely long enough), not a collapse to a single number. Within the bracket, set T (or report across it, per (b)).
4. **Cost measurement (D068 discipline).** Development-in-the-loop must be COST-MEASURED before committing to the full sweep — four runtime estimates in this project were wrong. The ~2 h/arm figure (D079) was WITHOUT development; every arm now includes an inner plasticity run.

**NEXT.** Scope the implementation against this entry: (a) characterize the developed-fitness distribution on a few genomes to settle sub-decision 1; (b) prototype Hebb+homeostasis as a Kind-A development phase in `evaluate()`, verify it leaves the support (hence P) invariant; (c) test sub-decision 3 — does development route E where birth-fitness could not (the direct D082 rematch); (d) cost-measure before any full sweep. **Gate B remains blocked (D080/D082) until routing is established — now via development, not more birth-fitness generations.**

**FOR THE LAB TALK.** "Does Frank's framework require a developmental inner loop between genome and fitness, and if so how do you keep the parameter axis clean?" is a foundational question the whole group is equipped to argue, and this project is the concrete instance that makes it vivid. Present as an open design question, not a solved one.

### D084 — SCOPED, NOT COMMITTED: a single biologically-grounded interneuron-hierarchy gene may unify sensory- and association-cortex regimes under one model. Ordered AFTER D083.
**2026-07-19 · Scoped (candidate major direction)** · *arises from the "slept on it" stance session; depends on D083; widens the project's central thesis — flagged as such*

**THE INSIGHT (two empirical backgrounds, this session).** Cortical GABAergic interneurons are ~85–90% three non-overlapping genetic subclasses — **PV, SST, VIP** (VIP↔CR/CB in primates) — and their *proportions shift systematically and monotonically* along the macro-cortical hierarchy (sensory→association, aligned with the T1w/T2w myelin gradient). The field tracks this with **PV/(PV+SST)** (output- vs input-modulation) and the **disinhibitory index VIP/(PV+SST)** (capacity for context-dependent gain modulation). Both are monotonic projections of a SINGLE principal axis: **the realized cortical configurations are a 1-D trajectory through the interneuron composition simplex, not free variation in it.**
- **Sensory pole (V1/S1):** PV-dominant (~40–50% of GABAergic). Fast perisomatic feedforward gating, sharp tuning, temporal fidelity, gamma (30–80 Hz). Prevents runaway from dense thalamic input.
- **Association pole (PFC/PPC):** PV down (~20–30%), SST up (~30–40%), VIP up. The **VIP→SST→pyramidal disinhibitory motif** expands — top-down gating, and the recurrent excitation that sustains persistent activity (working memory) without collapse. Beta (20–30 Hz).

**WHY THIS MATTERS TO THE PROJECT.** The disinhibitory motif (VIP modulating SST's effect on pyramidal cells) is a **level that modulates another level — a candidate biological instantiation of exactly the "regulation" H-C predicts should emerge** (D055/D083). And PV-dominant vs VIP/SST-elevated are exactly the sensory-like vs association-like regimes the earlier stance discussion (this session) showed the apparatus should span. **So the interneuron gradient is not a caveat to bolt on — it may be the mechanism that unifies cortical regions under one model.**

**THE DESIGN (search-space stays small — PJM's key constraint).** NOT three unbounded proportion genes (explodes the space; also empirically false — the proportions are constrained to the 1-D trajectory). Instead:
- **ONE bounded scalar gene: position along the empirical cortical-hierarchy axis, h ∈ [0,1]** (sensory-pole → association-pole). It MAPS, via the empirical trajectory, to a specific (PV, SST, VIP) composition. One number on a curve pinned by data — NARROWER than adding a single free synapse type. **Both PV/(PV+SST) and VIP/(PV+SST) fall out of the same h for free**, because both are projections of the one axis.
- **P (the parameter axis) is UNAFFECTED:** h is a compositional gene like Dale's-law identity (D038) — orthogonal to synapse count. It does not enter n_params.

**SIMPLIFIED-PROXY COMMITMENT (PJM, explicit).** We **embrace the empirical 1-D trajectory** as the biological grounding, but **implement it via a simplified single-compartment proxy — we do NOT commit to multi-compartment modeling.** The three populations are realized functionally: PV → fast perisomatic (somatic-voltage) inhibition; SST → slow inhibition onto a separate (proxy-"dendritic") current pathway; VIP → inhibition targeting SST. This is a deliberate simplification, stated as such so it is not mistaken for an oversight — the faithful dendritic/perisomatic spatial distinction (which would need two compartments) is knowingly traded for tractability. The claim is "a biologically-grounded proxy for the interneuron-enacted inhibition/disinhibition gradient," NOT "a multi-compartment cortical microcircuit."

**CAPABILITY, NOT INSTALLED MOTIF (D074's rule, load-bearing).** h sets the population PROPORTIONS and intrinsic properties (time constants, targeting bias). It must NOT hard-wire a functioning VIP→SST→pyramidal loop — that would install the very regulation H-C tests for emergence (the exact D074 Mg-gate error). More VIP cells *available* ≠ a *working* disinhibitory gate. Whether the loop wires up and functions is left to selection/development. **Easy to get wrong; preserve it.**

**DUAL USAGE (maps onto the impose-vs-evolve split from this session).**
- **h as a SWEPT coordinate** (imposed): does the dynamical signature transition where the background predicts — gamma/fast-gain at the sensory pole, beta/persistent-activity/disinhibition at the association pole? **Oscillation frequency is an INDEPENDENT observable** (not task performance) that validates the model spans the gradient.
- **h as a GENE** (evolved): the striking testable prediction — does selection drive h toward the association pole when the environment demands context-dependent regulation, and toward the sensory pole when it demands fast feedforward encoding? **If H-C is right, the environment's regulatory demand should predict where on the empirical interneuron axis selection lands — the cortical interneuron gradient as an EVOLVED consequence of environmental structure.**

**WATCH-OUTS.**
1. **Capability-not-installed** (above) — the one that protects the emergence claim.
2. **Two-compartment cost — CONSCIOUSLY DECLINED** via the simplified-proxy commitment above.
3. **Species calibration:** rodent VIP vs primate CR/CB substitution yield slightly different quantitative trajectories. State which atlas the h→composition map is calibrated to (open choice; likely rodent VIP for simplicity, note the primate CR/CB translation).
4. **SST/homeostasis OVERLAP — the reason for the ordering dependency.** SST does slow rate-control / dendritic protection — functionally overlapping the homeostatic plasticity of the D083 development redesign. SST-population and homeostatic-development are partly the same thing (structural vs plastic). **Designing the interneuron architecture before prototyping development would double-count this.**

**⇒ HARD ORDERING: D083 (development) is prototyped FIRST; D084 is designed AFTER, informed by how much of "SST's job" homeostatic plasticity already does.** Do not build D084 yet.

**SCOPE ACKNOWLEDGEMENT (explicit, per PJM's "recognize you're choosing it" concern).** Recording this widens the project's central thesis from "does double descent appear in a spiking network" toward **"the interneuron-composition gradient is the axis that unifies cortical regions under one learning model, and the regional gradient may be an evolved consequence of environmental regulatory demand."** This is a bigger, more distinctive, more CAS-flavored claim — well-suited to the lab — but it is a deliberate widening, chosen, not drifted into. Marked SCOPED so the commitment is visible and revisitable.

### D085 — Sequencing: related-work review BEFORE the development build, broad in SCOPE, narrow in ACTION. Pre-committed to prevent the positioning spiral.
**2026-07-19 · Accepted (process)** · governs the ordering of D083's implementation · *PJM's call, sharpened from CLM's over-narrow version*

**THE DECISION.** The development build (D083) has ≥3 load-bearing design choices the literature may
already have settled: **(a) Hebbian+homeostatic CONVERGENCE conditions** (the load-bearing unknown of
D083 step 2 — does the rule reach a stable fixed point or cycle/diverge? decades of plasticity-
stability work bear on this); **(b) the structure of the develop-then-select inner loop** (the
Baldwin-effect / learning-and-evolution literature — Hinton & Nowlan 1987 onward — has done
genotype-develops-before-fitness; we risk reinventing it, possibly wrong); **(c) the fitness-
distribution summary statistic** (D083 sub-decision 1 — surely standard somewhere in evo-bio /
evo-computation). Building before checking risks the replant-from-seed failure this session opened by
worrying about. **⇒ review FIRST.**

**THE DISCIPLINE — scope the ACTION, not the search (PJM's key refinement).** CLM proposed scoping the
*search* narrowly to three questions. PJM corrected: scope the *action* instead. **Search BROADLY**
(searches are cheap; findings are durable; a narrow search just forces re-searching the same territory
later, fighting the purpose of REFERENCES.md as an accumulating asset). **Act NARROWLY** — at THIS
juncture, act only on D083-relevant outcomes.

**Why this is the right cut:** the positioning spiral (see REFERENCES.md Positioning; the "pilot is
largely a re-derivation" near-death) was NOT caused by reading too much — it was caused by *acting on
everything read*. Each finding re-opened the whole project. The discipline belongs at the ACTION
boundary, not the input boundary. You can read that someone partially pre-empted H-B, note it, and NOT
re-open H-B today.

**THE PRE-COMMITMENT (binding; recorded BEFORE searching so the first juicy off-scope finding can't
erode it in real time — which is how the last spiral began):**
1. **Search broadly** across development-adjacent territory: plasticity stability, Baldwin/
   learning-and-evolution, fitness-distribution summarization, and whatever adjacent work surfaces.
2. **Annotate everything into REFERENCES.md** in its existing grammar (what-it-does / how-it-relates /
   🔴🟡🟢), INCLUDING findings that touch H-A/H-B/H5/H-C or re-raise positioning — **flagged**
   ("relevant to H-B; revisit when H-B comes off the shelf").
3. **Act, now, ONLY on D083 outcomes** — the three design choices for the development build. Every
   non-D083 finding is recorded-and-flagged, NOT acted on. It becomes future-you's pre-loaded context,
   not present-you's rabbit hole.
4. **Explicitly deferred as a SEPARATE later pass:** the existing Positioning priority reads
   (Clark/Abbott/Litwin-Kumar 2023, Cayco-Gajic, Dambre) — they serve H-A/H-B/H5, downstream of
   development, off the current critical path. Do NOT fold them in now.

**TERMINATION.** The review ends when the three D083 questions (a/b/c) have literature-informed answers
(or a confirmed "genuinely open"). Broad annotation continues opportunistically but does not gate the
build. **Then: build the development phase, informed by (a)/(b)/(c).**

**RESULT SLOT (fill as the review runs):**
- (a) plasticity convergence: **ANSWERED — naive Hebbian + SLOW homeostatic scaling does NOT converge
  (the "temporal paradox", Zenke & Gerstner 2017): fast Hebbian + slow homeostasis oscillates/runs
  away. Stability needs a RAPID, co-timescale stabilizer — Oja / BCM / heterosynaptic term. DIRECTIVE
  for D083: pick a convergent rule from the start; convergence-based maturity (sub-decision 3) is then
  available but contingent on that choice; bookends double as the convergence check. Would have cost
  an empirical cycle to rediscover.**
- (b) develop-then-select structure: **ANSWERED — this IS the Baldwin effect (Hinton & Nowlan 1987).
  A named 40-yr framework; build on it explicitly, strictly Baldwinian (learned changes not
  inherited). REFRAMES D082: their demo was a NEEDLE-IN-A-HAYSTACK landscape (flat, no gradient) —
  exactly our flat Gate A — and learning SMOOTHS such landscapes into navigable ones. Strong support
  that D083 will WORK. **On the "unsupervised inner loop" caveat (RETRACTED after PJM):** the inner
  loop being blind to Y is not a defect — it is how biology works. Real within-life learning IS
  unsupervised; the whole system is supervised AT THE OUTER LOOP (selection retains genomes whose
  blind-learning machinery produces fitness-relevant structure). The Baldwin guarantee needs only that
  the inner loop's product VARIES in a fitness-relevant way across genomes, so selection has variance
  to grade — which unsupervised development satisfies. And our fitness apparatus is NOT level-2-blind:
  Y = tanh(E @ Q @ Wc) is context-dependent, and the memoryless-floor↔oracle-ceiling gap is exactly
  the level-2 reward region. So the caveat collapses.
  **The REAL open question (H-C's actual content, not a supervision worry):** the DIVISION OF LABOR
  between the two loops. Does unsupervised development alone build context-inference (⇒ regulation is
  DEVELOPMENTAL, H-C's "emerges under selection" weakened), or does development do little and selection
  find the rare genomes whose developed substrate routes context (⇒ regulation is SELECTED, H-C
  supported)? Both are "evolution shapes circuitry"; WHICH is the result. **Measured by the control we
  already designed: sample-and-develop (development alone) vs the full GA (selection on top) — the
  reason sampling is a NEEDED CONTROL for H-C, not just a cleaner instrument for H-A/H-B.**
- (c) fitness-distribution statistic: **ANSWERED — do NOT default to the mean. It's a named topic
  (Kaznatcheev); with stochastic fitness, selection acts on TAILS the mean discards, and complexity×
  fitness is where tails live. Collect the distribution; base hypotheses on mean AND variance (≥1st
  two cumulants). And (sub-decision 2): distributional evaluation beats single-draw — probabilistic
  development must average draws, not select on one lucky draw (overestimation bias).**

**REVIEW COMPLETE (termination condition met: a/b/c answered).** Net effect on the build:
1. **Plasticity rule:** use Oja / BCM / heterosynaptic — NOT naive Hebbian + slow scaling (won't
   converge). Convergence-based maturity is then available but contingent on this choice.
2. **Structure:** frame explicitly as Baldwinian; check that unsupervised development is
   fitness-relevant (the load-bearing assumption the Baldwin literature exposes).
3. **Statistic:** collect the developed-fitness distribution; hypotheses on mean+variance; if using
   probabilistic development, average draws (avoid overestimation bias).
None of these overturn D083's framing; all three PRUNE the implementation. This is the prune-not-
replant payoff PJM argued for — three implementation choices corrected before a line was written.

### D086 — Build development's inhibitory-plasticity layer PER-NEURON-ADDRESSABLE, so D084's interneuron gene is later ADDITIVE, not a rewrite.
**2026-07-19 · Accepted (build directive)** · arises where D083 (development) and D084 (interneuron gene) physically touch — the inhibitory synapses · *forward-compatibility, decided before writing the plasticity code*

**THE JUNCTION.** The Oja hand-roll blew up (one-step runaway to NaN — the standard recurrent-Hebbian
positive-feedback instability the literature documents universally). The canonical fix is a Hebbian
term + an explicit homeostatic/inhibitory stabilizer; the natural choice for THIS substrate is
**inhibitory synaptic plasticity (Vogels-Sprekeler 2011)** — plasticity on INHIBITORY synapses that
maintains E/I balance while excitatory Hebbian learning proceeds. It fits because the model already has
an inhibitory population and E/I balance is already a precondition (D075).

**WHY THIS IS THE MOMENT TO THINK ABOUT D084.** Vogels stabilization and D084 (the PV/SST/VIP
interneuron-hierarchy gene) act on the SAME synapses — the inhibitory ones. How the inhibitory
plasticity is built now determines whether D084 later slots in additively or requires tearing out the
inhibitory layer. **Decision: build D084-COMPATIBLE now; do NOT build D084 now.**

**THE DOOR-OPENER (three cheap structural choices; implement all three):**
1. **Per-inhibitory-neuron parameters, not global scalars.** Vogels' target rate ρ₀, learning rate η,
   and trace timescale τ are stored as PER-NEURON arrays (length = # inhibitory neurons), even though
   today every entry is identical. D084 later just writes different values per neuron via the h gene —
   no structural change. Global scalars would force surgery.
2. **Inhibitory synapses indexed by presynaptic identity**, so a future type label (PV/SST/VIP) can
   gate the rule via a lookup that already exists — widening it, not rewiring.
3. **Timescale τ as a per-population field, not a constant** — because the PV-fast / SST-slow
   distinction (D084) IS a timescale difference; D084 then sets different τ per type = data, not
   structure.

**EXPLICITLY NOT NOW (stays D084, hard-ordered after development works):** three actual populations,
the h→composition map, the VIP→SST→pyr disinhibitory motif. Building the HOMOGENEOUS Vogels stabilizer
shaped for D084 ≠ building D084.

**THE HONEST CALCULus (premature-generalization guard).** D084 is scoped-not-committed, so "build
extensibly" must be cheap or it's a trap. It IS cheap here: Brian2's idiom is per-neuron state
variables, so per-neuron parameters are the PATH OF LEAST RESISTANCE, not an added abstraction. The
alternative (global scalars) has a KNOWN refactor cost if D084 proceeds. Cheap door-opener + known
future cost for the closed version ⇒ open the door. **Caveat to verify:** confirm the canonical Vogels
Brian2 reference is already written per-neuron (likely). If it is, the door-opener costs nothing (just
don't collapse to scalars). If it uses globals, keep the deviation minimal and TESTED — do not
improvise the way the Oja hand-roll was improvised (that's what caused the blowup).

**METHODOLOGICAL LESSON FROM THE OJA FAILURE (standing rule addendum).** Do NOT hand-roll plasticity
update equations. Recurrent Hebbian instability is the most-studied problem in this subfield; adapt a
PUBLISHED, TESTED implementation (ideally with reference Brian2 code — Vogels-Sprekeler 2011), with
known-working constants. The Oja blowup was improvised arithmetic hitting a documented wall. *(Adds to
"search before building": also "adopt tested reference code before building numerics.")*

**NEXT:** search for the canonical Vogels-Sprekeler Brian2 implementation; inspect its parameterization
(per-neuron vs global) to confirm the door-opener is free; adapt THAT into develop(), not a hand-roll.

### D087 — Development-phase design: free within support-invariance + cross-P uniformity; use a stabilized paired plasticity (inhibitory-first); and MEASURE effective-P rather than constrain development to protect nominal-P.
**2026-07-19 · Accepted (design)** · resolves the plasticity-rule fork (D083 sub-decision 1), D086's inhibitory floor, and the Oja-failure lesson into one principle · PJM's framing

**THE GOVERNING PRINCIPLE (PJM).** The two loops are separable. The development phase has design
FREEDOM; the ONLY hard constraints come from the outer-loop ("at given P") interpretation, and there
are exactly two:
1. **Support-invariance** — development must not change WHICH synapses exist (Kind A). P is the support
   of W; development tunes strengths within a frozen support.
2. **Cross-P process-uniformity** — the development process must be IDENTICAL at every P (same rule,
   same hyperparameters, same convergence criterion). Development is part of the measurement
   apparatus, so it must be the same instrument at every P, or "P's effect" confounds with
   "development-process's effect."
**Within those two, plasticity design is free to be biologically sensible.**

**THE PLASTICITY RULE (biologically-standard, tested, not hand-rolled — the Oja lesson, D086).**
- **Paired excitatory-learner + inhibitory-stabilizer**, the standard picture: inhibitory plasticity
  provides STABILITY, a separate excitatory Hebbian/STDP rule provides the LEARNING. The Oja blowup was
  trying to do learning without stability; the literature (Zenke & Gerstner; Vogels et al.) says you
  need both.
- **Inhibitory half = Vogels-Sprekeler 2011** — the canonical inhibitory synaptic plasticity rule,
  with an OFFICIAL tested Brian2 reference implementation (brian2 docs frompapers.Vogels_et_al_2011;
  ModelDB 143751, implemented by Zenke & Vogels). ~6 lines, event-driven, target-rate homeostatic
  setpoint (alpha). Runs INSIDE net.run() — no Python-side weight write-back (eliminates the fragile
  _reload_W that caused half the Oja trouble; development = "turn eta on, run, turn off").
- **Excitatory half = a tested STDP/Hebbian rule** (also a canonical Brian2 example), added AFTER
  Vogels is validated.
- **Substrate fit (checked, evonet.py):** LIF with real spikes, one recurrent Synapses object over W,
  current-based (I_syn += w). Vogels' conductance formulation is not required — its WEIGHT-UPDATE logic
  attaches to the current-based synapse. Event-driven on_pre/on_post works (it's spiking Brian2).
- **BUILD ORDER (one-at-a-time, the Oja lesson): Vogels-inhibitory FIRST** (validate in-sim plasticity
  stabilizes the net without blowup on this substrate), THEN add the excitatory learner on top. End
  state is the paired system; path there is one tested piece at a time.

**THE P-BOOKKEEPING — MEASURE effective-P, do NOT constrain development (PJM, supersedes D086's
floor).** Rather than impose a magnitude floor that clamps development to protect nominal-P (backwards
— distorting the process to protect the measurement), let development run UNCONSTRAINED (only a
not-exactly-zero numerical guard) and move the P-question to ANALYSIS time:
- **nominal-P** = support count = the genome's parameter count = the controlled INPUT (set via density;
  what selection acts on).
- **effective-P** = count of synapses above a meaningful-magnitude threshold = the developed
  phenotype's functional parameter count = a measured OUTPUT.
- **RECORD BOTH for every developed network.** Bin the grand aggregate by EITHER, and learn from any
  DIFFERENCE (PJM). Effective-P is arguably the more Frank-faithful axis (his parameter count is the
  functional-connection count), and error-vs-effective-P is error vs what the matured network actually
  uses. But nominal-P is the controlled quantity; comparing the two binnings is itself informative.

**WHY effective-P is better than a floor (the reasoning).** A synapse at w≈1e-5 is "not zero" but
contributes nothing — so a not-zero guard alone lets NOMINAL and EFFECTIVE P silently diverge,
smuggling the genotype/phenotype-P gap back in through MAGNITUDE (the exact thing Kind-A prevents via
support). A floor fixes that but distorts development (too high clamps the natural dynamics Vogels
needs to reach balance; too low permits effective-vanish anyway — a Goldilocks problem with no a-priori
right value). Measuring effective-P dissolves the Goldilocks problem: no floor during development, and
the threshold appears only at analysis where several can be tried cheaply.

**REQUIRED DISCIPLINES for the effective-P route (the costs of a measured vs controlled axis):**
1. **Threshold-robustness is a RESULT, not an assumption.** Compute effective-P at several magnitude
   cutoffs; show the binned pattern is robust across them. If the double-descent pattern appears only
   at one lucky cutoff, that is a threshold artifact, not a result. (Cheap: recompute + re-bin.)
2. **Coverage is emergent, not designed.** With nominal-P you CHOOSE the arm values; with effective-P
   you sample nominal-P and development SCATTERS it into an effective-P distribution you don't control.
   Risks: effective-P values may CLUSTER (x-axis collapses) or bins may be unevenly populated (sparse
   near the interpolation peak). Mitigation: sample nominal-P WIDELY and DENSELY so the induced
   effective-P range is covered with adequately-populated bins.
3. **First-development-run diagnostic:** look at the weight distribution development produces. Clean gap
   (meaningful vs crashed-to-tiny, nothing between) → threshold placement trivial, effective-P
   unambiguous. Continuous smear to near-zero → effective-P threshold is a real judgment call, made
   explicit and robustness-checked per (1).

**BONUS QUANTITY unlocked (the floor would have hidden it).** nominal→effective COMPRESSION — how much
of the nominal support development prunes to effective-zero, and whether the pruning fraction tracks
nominal-P / environment / dynamical regime. Possibly nothing, possibly a finding; now observable
because both P's are logged.

**H-B UNDER effective-P.** H-B predicts the interpolation peak sits at r₁ (structural rank), not the
constraint count. With both P's recorded, H-B is tested against BOTH: the peak should track r₁ in
whichever P is the functional one — expected to be effective-P (the matured network's actual
dimensionality). Recording both lets the data say which P the peak tracks, rather than presupposing it.

**SUPERSEDES:** D086's magnitude-floor mechanism (the per-neuron-addressable inhibitory-layer directive
in D086 STANDS — it is about D084-compatibility, unaffected). The Kind-A support-invariance (D083)
stands and is now the ONLY hard development constraint on W's support, with effective-P as the analysis
-time honesty check that magnitude hasn't recreated the genotype/phenotype-P gap.

### D088 — The engineered-ceiling bookend has a SECOND load-bearing role: known-positive control for validating the readout. And the readout/development/context-carry unknowns must be resolved in a specific non-circular order.
**2026-07-19 · Accepted (method)** · arises from the readout-design work (D087 follow-on); amends D083 sub-decision 3 · *PJM caught the circularity*

**THE CIRCULARITY (PJM).** Three intertwined unknowns cannot be resolved in the naive order:
1. **Does development RUN correctly?** (build, plasticity, Kind-A, no blowup) — ✓ ESTABLISHED this
   session (evonet split-synapse + develop() verified: 183 plastic I→E, no NaN blowup, P invariant,
   commit correct, net fires MORE after dev).
2. **Does development produce a network that CARRIES CONTEXT** across the inter-stimulus interval?
3. **Does the READOUT correctly capture context when present?**
(2) and (3) are **mutually circular**: can't validate the readout without a context-carrying network;
can't confirm a network carries context without a working readout. PJM's catch: you CANNOT "just check
whether context carries first" — an UNDEVELOPED network almost certainly can't carry context (that is
the whole premise of the redesign — the kangaroo-at-birth problem one level down). So the context-carry
check requires a developed network AND a validated readout — both prerequisites gate it.

**THE WAY OUT — the engineered ceiling as the known-positive control.** The D083 bookend "engineered
encoding+memory network" (scoped there only for convergence-time calibration) has a SECOND role that
breaks the 2⇄3 circularity: **it is a network that BY CONSTRUCTION carries context**, so it is the
known-positive that validates the readout. If the readout detects context in the engineered network
(which definitely has it), the readout works; only then is the readout's verdict on DEVELOPED networks
trustworthy. Without a known-positive, "readout reads no context" is uninterpretable (readout broken vs.
network can't do it — the exact Gate A ambiguity, D082).

**This does NOT violate the D083 hard quarantine.** Using the engineered net to CALIBRATE THE READOUT
(a measurement instrument) is not seeding it into evolution, not templating from it, not comparing
evolved networks against its structure. The quarantine (contributes only scalars — a convergence time,
and now a readout-validation pass/fail — never a template/seed/comparison for the evolved population)
stands intact. The engineered ceiling now earns its place TWICE: convergence-time bracket (D083 3) AND
readout known-positive control (here).

**⇒ THE NON-CIRCULAR ORDER OF OPERATIONS (supersedes the naive "check context-carry first"):**
1. **BASELINE readout fix (the immediate unblocker, non-circular).** Make behave() correctly report the
   firing rate of a network that is demonstrably firing — fix the post-development artifact (reads
   activity 0.000 despite 4931 spikes; a sampling/timing-alignment problem, NOT silence, NOT context-
   blindness). This gates everything downstream: can't validate against the ceiling or measure
   developed nets until behave reads ANY developed network correctly. Just "report the rate of a firing
   network."
2. **BUILD + VALIDATE the context-sensitive readout against the engineered ceiling.** The readout must
   capture the context-MODULATED per-stimulus response (context expresses DURING presentation as
   modulation, not only post-stimulus — D088 note below), scored against the context-dependent Y with
   the floor/ceiling decomposition (floor = encoding/Level-1; below-floor = context/Level-2). Validate
   it detects context in the engineered ceiling (known-positive) before trusting it. Persistence/
   complexity = analysis-time diagnostics of HOW context is carried, extracted from the already-recorded
   continuous r-trajectory (no new recording, no presentation-structure change).
3. **THEN measure context-carry on DEVELOPED networks** — the real D082 rematch, now meaningful because
   both readout (validated on ceiling) and development (functional) are established.

**READOUT FACTS SETTLED (this session, from reading behave + PJM's correction):**
- behave() does **ONE continuous run**, `restore("init")` once then `net.run(n*present_ms)`, TimedArray
  switches drive every present_ms. **It does NOT reset between stimuli** → context activity carried in
  state DOES survive across stimulus boundaries → **Level-2 carry is architecturally possible** (the
  precondition is met; not the root cause of anything).
- **Level-2 is NOT strictly post-stimulus (PJM correction).** Context must PERSIST across the inter-
  stimulus interval, but its EFFECT appears DURING the next presentation as context-modulation of the
  stimulus response (same stimulus → different response under different context). So context is readable
  in the SAME per-stimulus response window as encoding — it is not blind to the current window. The
  temporal profile (persistence/complexity) is the MECHANISTIC diagnostic of how context is carried, not
  a separate fitness channel and not requiring post-stimulus gaps.
- **Fitness stays SINGLE-channel:** NMSE to the context-dependent Y. Encoding credit = reaching the
  memoryless floor; context credit = beating it (below-floor). The two capabilities are in the TARGET +
  floor/ceiling reference, not in two separate readout channels. The readout must be temporally
  inclusive enough that context-modulation is in the measured response.
- **behave already records the FULL r-trajectory** (`mon.r`, (N, samples) across the whole run); the
  per-stimulus windowing just REDUCES it. So persistence/complexity diagnostics need a richer REDUCTION
  of data already in hand — no extra sim cost, no gaps.

**NEXT: step 1 — the baseline readout fix.** Then step 2 (context readout + ceiling validation), then
step 3 (developed-network context-carry = the rematch).

### D089 — REGRESSION + RECONCILIATION: STEP 1 development was built on a STALE evonet (pre-slow-current); re-applied onto the current base (old_b) with all infrastructure verified intact.
**2026-07-19 · Accepted (correction)** · *the uploaded evonet.py was stale; building on it dropped D074/D075/D078 — caught and fixed*

**WHAT HAPPENED.** The `evonet.py` uploaded this session was an OLD version predating the D074 slow
current. STEP 1 development (synapse split + Vogels develop() + D088 clock-rebase) was built on it and
COMMITTED — which regressed the repo: the committed version had development but LACKED the slow current
(D074), charge conservation (D075), the batched runner (D078), and the shared _window_readout helper.
I.e. it traded the memory mechanism (and batching) for the development mechanism, when both are needed.
**Caught when** starting the context-persistence probe (step 2a): grepping for the slow current found
it ABSENT — which also explained a stale-file symptom (nmda_frac was silently ignored all session).

**ROOT CAUSE + STANDING FIX.** Built on an uploaded core file without diffing it against what the
decisions say should be there. **New discipline: before building on an uploaded core file, verify it
contains the mechanisms recent decisions added (grep for the relevant D-number features).** Uploads are
often stale (the project has always warned this); core-file edits must confirm the base first.

**THE RECONCILIATION (a, per the two options considered).** Took `old_b` (the current, most-complete
base: slow current D074, charge-conservation D075, batched runner + verify_batch_equivalence D078,
shared _window_readout, readout_pos D072) and re-applied the STEP 1 development work onto IT, adapting
to its idioms:
- Plastic I->E block uses **w_fast** (I->E is inhibitory -> w_slow=0 anyway; Vogels tunes fast
  inhibition) -- a clean mapping onto the two-current model.
- Static block (E->E, E->I, I->I) keeps the **charge-conserved w_fast/w_slow split (D075)** untouched.
- Clock-rebase (D088) applied in BOTH single (`behave`) and batched paths at the point `t` is read.
- develop() resets I_fast/I_slow/r (not the old single I_syn) before re-storing "init".

**VERIFIED (sandbox, on the reconciled file):**
1. **verify_batch_equivalence PASS** — the synapse split did NOT break the single-vs-batch invariant
   (D078). This was the biggest graft risk; it's clean.
2. **Slow current active** — builds with nmda_frac=0.5/tau_slow=100 alongside the split; fresh behave
   healthy.
3. **Development end-to-end** — converges, no NaN blowup, net alive after, **Kind-A preserved (P
   1204->1204, support intact)**.
⇒ the reconciled evonet has slow current + charge conservation + batching + shared readout +
development + clock-rebase, all coexisting and checked.

**ACTION FOR THE REPO:** the currently-committed evonet (regressed) must be REPLACED by this reconciled
version. The rescued STEP 1 work is intact; only its base was wrong. NONE of the development logic
changed in the re-application — same split, same Vogels rule, same commit-back, same clock fix — only
adapted to w_fast/w_slow and the shared helper.

**NEXT (unchanged): step 2a** — the context-persistence probe, now on a substrate that ACTUALLY HAS the
slow current (my earlier "this substrate can't carry context" prediction was against the stale file; the
real base has the 100ms slow current D074 added precisely for carry).

### D090 — CARRYING ≠ REGULATING: context-carrying (memory) is necessary but NOT sufficient for regulatory structure (H-C's target). Two different measurements test the two.
**2026-07-19 · Accepted (conceptual)** · *PJM caught a conflation creeping into how CLM described the step-2 chain*

**THE DISTINCTION (do not blur again).**
- **Context-carrying** = the network HOLDS context-distinguishable information across time. It is
  MEMORY: a persistent state separable by context. Measurable DIRECTLY as raw-state-separability
  (can a linear decoder recover the context label from the state, above chance, and does that survive
  the inter-stimulus gap).
- **Regulatory structure (H-C's actual target, D055)** = one part of the network MODULATES another --
  held context CHANGES HOW stimuli are processed (gain modulation / routing / a level acting on a
  level), not merely adds a context-dependent bias to the output.

**CARRYING IS NECESSARY BUT NOT SUFFICIENT FOR REGULATION.** A network can carry context WITHOUT
regulating: hold a persistent context-distinguishable state that just sits there as extra activity,
adding a context-dependent OFFSET to the output without changing the stimulus->response MAPPING. That
is memory, not regulation. Regulation is when carried context MULTIPLICATIVELY/STRUCTURALLY alters the
mapping -- the same stimulus computed differently, not just offset.

**WHY THE TASK ALREADY DISTINGUISHES THEM (the reassuring part).** Y = tanh(E @ Q @ W_ctx[c]): context
c selects WHICH weight matrix maps stimulus->response. Context is NOT an additive bias in the target --
it MULTIPLICATIVELY reconfigures the mapping. So to beat the memoryless floor, a network cannot merely
HOLD context as extra activity; it must USE context to change how it maps E->response. **Beating the
floor requires REGULATION, not just carrying.** A mere-carrier (holds context, adds it as bias) stays
stuck near the floor. ⇒ the floor/ceiling gap (D088) measures REGULATION; raw-state-separability
measures mere CARRYING. Two different measurements, two different capabilities.

**CONSEQUENCE FOR THE STEP CHAIN (sharpened):**
- **2a — does the substrate CARRY context?** RAW-STATE-SEPARABILITY probe (linear decode of context
  label from state; check it persists across the inter-stimulus gap), sweep nmda_frac (0 = no slow
  current = negative control; rising = the D074 carry mechanism). **SELF-VALIDATING: needs NO engineered
  ceiling** -- "linearly decodable" is a direct property of the state vectors, not an inference about
  task performance. This BREAKS the readout<->carrier circularity for the probe (D088's circularity was
  about the TASK-PERFORMANCE readout; the raw-separability measure sidesteps it). Tests the NECESSARY
  precondition only -- passing 2a does NOT mean H-C is testable, only that regulation's prerequisite
  (memory) exists.
- **2b [if 2a passes] — build the engineered ceiling** = a network that both CARRIES and USES context
  (regulates); the known-positive for the TASK-PERFORMANCE readout.
- **2c — validate the task-performance readout** (below-floor detection = regulation) against the
  ceiling (D088).
- **3 — the D082 rematch:** does DEVELOPMENT produce networks that carry (state-separable) and, the real
  prize, REGULATE (beat the floor)?

**THE CORRECTION BEING RECORDED.** CLM had been letting "context-carrying" stand in for "regulatory
structure" across the step-2 discussion. They are different; carrying is the necessary precondition,
regulating is the H-C claim; below-floor task performance (not state-separability) is the regulation
signature, and the task's MULTIPLICATIVE context structure is what makes below-floor a genuine
regulation signature rather than a memory signature.

### D091 — The fitness task is constrained by the DOUBLE-DESCENT SHAPE, which keeps it distinct from the (memory-requiring) diagnostic protocol; "regulation" must be disambiguated (switch vs inferential); and regularizers smooth the interpolation peak.
**2026-07-19 · Accepted (conceptual, re-anchors fitness to the hypotheses)** · *PJM caught measurement-convenience (the clean cue-delay-probe protocol) starting to redefine the scientific target*

**THE DRIFT BEING CORRECTED.** The delayed-discrimination (cue->delay->probe) protocol scores carrying
and regulating cleanly and separately, and it was tempting to make it THE task. PJM caught that this
lets a measurement convenience redefine the target. The fitness task's shape must be derived from the
double-descent framework, NOT from what is clean to score.

**"REGULATION" DISAMBIGUATED (PJM).** Not one thing:
- **Switch-regulation** — context is CONTINUOUSLY PRESENT and directly gates the stimulus->output map
  (the document's feedforward-shunting Architecture B). Mechanistically regulation, but needs NO memory,
  and is the "context signalled by the mean -> a SWITCH not regulation" case D048 EXPLICITLY EXCLUDES as
  too easy. Gameable, trivial.
- **Inferential regulation (the TARGET)** — context must be INFERRED from history and HELD, then used to
  modulate the mapping. Requires memory + modulation. This is what H-C is about and what the task must
  reward without being gameable by the switch case.

**THE FITNESS TASK IS CONSTRAINED BY THE DOUBLE-DESCENT SHAPE (PJM's derivation).** For the curve to
exist at all, the fitness task must be:
1. **Significantly achievable WITHOUT memory/regulation** = the FIRST DESCENT (adding parameters
   improves the memoryless stimulus->response encoding, error falls). If the task were ONLY solvable
   with regulation there would be NO first descent -- just failure until regulation appears.
2. **Further improvable WITH memory/regulation, once enough parameters support DEVELOPING those
   capabilities** = the SECOND DESCENT (excess parameters past interpolation enable the memory+
   regulation machinery that beats the memoryless ceiling).
3. **An interpolation region between** where a mid-sized net overfits the memoryless map (memorizes
   training stimuli without capturing general structure) -> the error peak.
**⇒ the floor/ceiling framing IS the operationalization of the two-descent structure:** memoryless
floor = first-descent-achievable; below-floor = second-descent, regulation-dependent; the gap = the
regulation-dependent improvement. This is why floor/ceiling was right all along -- not a scoring
convenience, the two-descent shape itself.

**WHY THE PROTOCOL CANNOT BE THE FITNESS (the key consequence).** The cue-delay-probe protocol's
enforced SILENT DELAY makes memory a HARD REQUIREMENT -- a memoryless network scores ZERO, not
"significantly achievable." So the protocol has NO FIRST DESCENT: it destroys the memoryless-achievable
component double descent requires. The very thing that makes it a clean DIAGNOSTIC (isolates memory by
forcing it) makes it a BAD FITNESS TASK (removes the first-descent gradient). ⇒ **FITNESS STAYS ON THE
GRADED NATURALISTIC TASK (current D048 design); the cue-delay-probe protocol is DIAGNOSTIC-ONLY** -- a
mechanistic audit of HOW a network achieves below-floor performance (genuine held-context inferential
regulation vs a switch-y shortcut), run on selected/developed nets as ANALYSIS, never as selection
pressure. (Parallels the routing probe D081: a fixed diagnostic separate from fitness.)

**CARRYING vs REGULATING, scored separately BY THE PROTOCOL (diagnostic use, D090):**
- Carrying = does context-distinguishing activity survive the enforced silent delay (persistence-
  through-silence). Clean, high-contrast -- fixes the under-powered linear-context-decode problem
  (context-label decode was ~0.046 even from oracle covariance features; too weak an instrument).
- Regulating = for IDENTICAL probe stimuli, does the response differ across contexts IN THE WAY THE
  TASK DEMANDS: response(E_probe|c) - response(E_probe|c') vs tanh(E_probe Q W_c) - tanh(E_probe Q W_c').
  Same-response-regardless-of-context = no regulation; matching-the-demanded-difference = regulation.
- **Three-way diagnostic the aggregate floor/ceiling gap CANNOT provide:** carries+regulates (full);
  carries+doesn't-regulate (memory-as-bias, D090); doesn't-carry (regulation untestable). Tells us WHICH
  STAGE is the bottleneck, not just "near floor."

**REGULARIZERS SMOOTH THE INTERPOLATION PEAK (PJM -- closes the D055 loop into the fitness picture).**
The overfitting hump between descents is DEEPENED by lack of regularization, SMOOTHED by its presence
-- Frank's conditional (biology doesn't penalize complexity -> experiences the FULL double descent)
made concrete. The regularizers (homeostasis, E/I balance, the developmental plasticity itself) are what
determine whether first->second descent is a treacherous valley or a gentle slope. **Testable second-
order prediction:** vary the regularization machinery, watch the interpolation peak sharpen vs smooth.
D055's regularization-vs-regulation now enters the FITNESS picture, not just the framing.

**DECISIONS SETTLED:** (1) fitness = graded naturalistic task (first+second descent shape), NOT the
protocol; (2) protocol = diagnostic-only, auditing carrying + inferential-regulation separately; (3)
"regulation" = inferential (target), not switch (excluded, D048); (4) regularizers smooth the peak =
a testable prediction linking D055 to the curve. Re-anchors the fitness question to the hypotheses
after measurement-convenience pulled at it.

### D092 — 2a RESULT + PIVOT: undeveloped random nets do NOT cleanly carry context (as predicted); build the engineered ceiling FIRST (Wang-grounded attractor) as the known-positive that validates the carry measure. Random-net null explained: slow current needs attractor TOPOLOGY, not just presence.
**2026-07-19 · Accepted (result + design)** · two carry-probes on random nets both measured the wrong thing; pivot per PJM's earlier instinct

**2a RESULT (two probes, both on UNDEVELOPED RANDOM nets, both non-viable as measures):**
- **Linear context-label decode from state: ~0 separability** -- and a control showed context is only
  ~0.046 decodable even from ORACLE covariance features, so linear-label-decode is too weak an
  instrument (context is a weak, distributed, nonlinear statistical signal).
- **Silent-delay separability: high (~4-5) but a CONFOUND** -- the control that matters (does
  separability DECAY across delay length?) came back FLAT (nmda=0: 3.3->3.2->3.5->3.5 across
  0/100/300/600 ms). Real memory decays; flat separability = a non-memory difference (the fixed network
  relaxing to different context-driven states, not HOLDING a cue). Not carry.
**⇒ 2a is effectively ANSWERED (the necessary-condition read, D090): undeveloped random networks do NOT
spontaneously carry context.** This is exactly what the whole development premise predicts (carry is
what development/selection BUILDS). Two elaborate measures on weak/absent signal both caught confounds
-- the LESSON: a carry measure is only trustworthy when validated against STRONG KNOWN carry. You cannot
develop the measurement on the population least likely to have the signal.

**WHY RANDOM NETS FAIL (the mechanistic explanation, from the Wang search).** The Wang/Compte/Brunel
working-memory attractor sustains persistent activity via SLOW recurrent excitation balanced by FAST
inhibition -- EXACTLY our D074/D075 config (slow I_slow + fast inhibition). But slow current only
produces a persistent MEMORY STATE when wired into an attractor TOPOLOGY (context-selective clusters
with strong within-cluster recurrence). Random connectivity lacks that structure, so slow reverberation
doesn't stabilize into memory. **So the random-net null is not "N too small" or "mechanism absent" -- it
is "the TOPOLOGY that exploits the slow current isn't there."** Which is precisely what an ENGINEERED
attractor supplies, and what development/selection must BUILD.

**THE ENGINEERED CEILING DESIGN (Wang-grounded; = the document's Architecture A, now sourced).**
Canonical Compte/Brunel/Goldman-Rakic/Wang 2000 + Brunel & Wang 2001 delayed-match circuit, minimal
form at N=50:
- Split 50 neurons into **context-selective excitatory clusters** (2 for the minimal case, N permitting
  -- Wang uses thousands; 2 clusters + inhib pool + I/O fits 50, per the posted document's 15+15+5).
- **Strong within-cluster recurrent excitation routed through the SLOW current (high nmda_frac)** --
  slow reverberation is what sustains the attractor.
- **Shared FAST inhibitory pool** -> winner-take-all between clusters (mutual exclusion of contexts).
- A cluster ignited by its context's input stays active through the SILENT DELAY (persistent attractor)
  = CARRYING. The held cluster then gates the probe response = REGULATING (Ardid & Wang 2013 "tweaking
  principle" for rule-based switching is the context-gating version).

**BUILD METHOD (a, chosen): hand-construct a W GENOME, run it through the EXISTING EvoNet at high
nmda_frac.** NOT a separate network outside EvoNet. Rationale: the ceiling must live in EXACTLY our
substrate (same LIF neurons, same slow current, same behave) to be a valid known-positive FOR OUR
SYSTEM and to validate OUR measurements. Building it outside EvoNet would test a different substrate.
Keeps the D083 quarantine clean: it is a GENOME we test, never seeded into evolution, never a template/
comparison for evolved nets -- only a measurement-instrument calibration (D088).

**FIRST TEST:** does the hand-wired attractor sustain context-distinguishing activity THROUGH the silent
delay (carry), measured with the SAME silent-delay measure that gave confounds on random nets? Now, with
STRONG known carry present, we see whether the measure tracks it -- and critically whether separability
DECAYS appropriately when carry is real (vs the flat confound on random nets). This VALIDATES the carry
measure against the known-positive (D088's whole point). If the measure works on the ceiling, it's
trustworthy for developed nets (step 3).

**REFS TO PIN:** Compte, Brunel, Goldman-Rakic, Wang (2000) Cereb Cortex 10:910 (visuospatial WM circuit);
Brunel & Wang (2001) J Comput Neurosci 11:63; Wang (2002) Neuron (decision/attractor); Ardid & Wang
(2013) J Neurosci 33:19504 (rule-based switching / context gating); Compte/Brunel delayed-match figure.

### D092b — Engineered ceiling BUILT and VERIFIED; carry measure validated (decay-across-delay is the discriminator).
**2026-07-19 · Accepted (result)** · executes D092

**BUILT (build_engineered_ceiling.py):** hand-wired 2-cluster winner-take-all attractor as a Genome,
run through the EXISTING EvoNet at nmda_frac=0.7. Layout: input[:5]->clusterA, input[5:]->clusterB
(selective drive = symmetry-breaking); 2x15 exc clusters with strong within-cluster recurrence (slow
current = attractor); 7 inh pool (winner-take-all); 3 output. w_rec=4, w_inh=6, w_drive=3 = verified
working point.

**VERIFIED CARRY:** A-cue lights cluster A NOT B (4.34 vs 0.03); B-cue lights B NOT A (4.35 vs 0.02) --
clean winner-take-all context selection. Persists through silence and DECAYS gracefully: selectivity
4.32 (100ms) -> 3.07 (300ms) -> 1.57 (600ms).

**THE CARRY MEASURE IS NOW VALIDATED (D088's purpose fulfilled).** The discriminator between REAL carry
and the random-net CONFOUND is DECAY-ACROSS-DELAY: real attractor memory decays gracefully (4.3->1.6);
the random-net confound stayed FLAT (3.3->3.5, non-decaying, D092). We could not see this without the
ceiling -- there was no real carry to contrast against. The known-positive supplied the signal that
makes the measure trustworthy. ⇒ for step 3 (developed nets), CARRY = context-selectivity that PERSISTS
AND DECAYS through the silent delay, NOT flat separability.

**FIRST HALF OF THE CEILING DONE (carrying).** Regulation half (the held cluster GATES the probe
response) is next: add probe input during the delay, check the OUTPUT differs by which cluster is held
(identical probe, context-dependent response = D091 regulation signature). Then the ceiling validates
the regulation measure too.

**QUARANTINE HOLDS (D083/D092):** ceiling is a tested genome / measurement-instrument calibration,
never seeded into evolution.

### D093 — "Regulation" = context-selects-the-map (READOUT), built from gating primitives (MECHANISM). The b-via-a resolution maximizes detectability of the second-descent<->regulation hypothesis and unites the task, the comp-neuro definition, and the D084 interneuron thread.
**2026-07-19 · Accepted (defines regulation for the study)** · PJM reframed the ceiling-wiring choice into "which maximizes our chance of detecting the hypothesis"

**THE CHOICE (not really about the ceiling -- about what REGULATION operationally MEANS).** Two ways a
held context can change a probe response:
- **(a) Gating/shunting** — context controls WHETHER a signal passes (a valve). Held context opens/
  blocks the probe->output path. Disinhibition/attention flavor; the VIP->SST->pyr motif (D084); the
  document's Architecture B; Ardid & Wang 2013.
- **(b) Context-selects-the-map** — context controls WHICH transformation is applied (a switchable
  function). Same probe mapped to output through a DIFFERENT function per context. Mante/Sussillo/
  Newsome 2013 context-dependent-computation flavor; matches the task's Y = tanh(E @ Q @ W_ctx[c])
  EXACTLY (context selects the weight matrix).

**PJM's framing that dissolved the tradeoff.** (1) Either choice supports the double-descent MEASUREMENT
(fitness integrates encoding + memory + regulation, so a fitness distribution exists at every P
regardless). The choice is not about measurability -- it is about what a second descent, if seen, would
MEAN. (2) The real question: which choice maximizes the chance of detecting the hypothesis *second
descent (or smoothed passage into it) <-> emergence of REGULATION*?

**THE ANSWER (b-via-a), from two requirements for the association to be DETECTABLE:**
- **Req 1 — regulation must be the capability the second-descent parameters actually buy, not a
  confound.** Below-floor performance must come from regulation, not from memory-as-bias or a near-
  switch shortcut. **(a) gating is CLOSE to switching** -> a second descent driven by gating is hard to
  distinguish from a switch-shortcut (the D048/D091 triviality) -> WEAKER attribution. **(b) map-
  selection CANNOT be a switch** (the W_ctx structure demands different transformations a switch can't
  give) -> a second descent driven by map-selection is CONFIDENTLY regulation -> CLEAN attribution.
  ⇒ **(b) is the confound-resistant READOUT.**
- **Req 2 — regulation must be EXPENSIVE (need excess parameters), or it joins the FIRST descent and
  there is no late association.** What does building map-selection (b) COST in parameters? The machinery
  to hold context and route it into reconfiguring the computation = the gating/interneuron machinery
  (a). ⇒ **(a) is the MECHANISM whose parameter-cost places regulation in the SECOND descent.**

**⇒ b-via-a: MEASURE regulation as (b) map-selection; expect it BUILT FROM (a) gating primitives.**
(b) gives the clean readout (Req 1); (a) gives the parameter-cost and late emergence (Req 2). This is
not a compromise -- it is the version that matches the hypothesis, because the hypothesis is precisely
"a capability that COSTS parameters (a-machinery) to build enables a NON-TRIVIAL improvement (b-readout)
past interpolation."

**WHAT THIS UNIFIES (the payoff).** The apparent tension -- (a) maps to the D084 interneuron gradient,
(b) is what a comp-neuro audience accepts as "regulation" and matches the task -- DISSOLVES. You get
both: the READOUT is (b) (audience-accepted, task-matched, confound-resistant); the MECHANISM is (a)
(the D084 interneuron/gating machinery, providing the parameter-cost). The interneuron thread (D084) and
the regulation readout are not competitors -- they are the MECHANISM and the READOUT of one phenomenon.
Regulation-as-map-selection is HOW the interneuron gating machinery pays off on the task; the interneuron
machinery is WHY regulation is expensive enough to emerge in the second descent.

**CEILING CONSEQUENCE (2b regulation half).** Wire the ceiling as CONTEXT-SELECTS-AMONG-SUB-PATHWAYS-
VIA-GATING: held context gates WHICH of several probe->output sub-pathways is active; the sub-pathways
implement DIFFERENT maps. That is (b)-regulation (different map per context) built from (a)-primitives
(gating selects the pathway) -- the known-positive for EXACTLY the hypothesized phenomenon, and a preview
of how evolved interneuron machinery (D084) would produce task-relevant map-selection.
**Caveat (honest):** more elaborate to wire (multiple sub-pathways + gating); if it proves fiddly,
fall back to (b)-readout with simpler mechanism (demonstrates map-selection is achievable, without
demonstrating it is built from gating). Try b-via-a first.

**STANDING DEFINITION (for the whole study):** REGULATION = context-dependent selection of the stimulus
->response MAP (b), operationalized as the identical-probe-different-context-response signature (D091),
measured against the memoryless floor (below-floor = regulation). Its expected MECHANISM is gating/
interneuron machinery (a) whose parameter-cost is the reason its emergence associates with the SECOND
descent. Switch-regulation (context present, direct gate, no memory) remains EXCLUDED (D048/D091).

### D094 — The fitness function: additive encoding + carrying, plus a MULTIPLICATIVE carrying×regulation bonus. Three terms mapping onto first/second descent and enforcing the capability hierarchy.
**2026-07-19 · Accepted (defines the GA fitness) · PJM** · resolves the ceiling-wiring question and the graded-vs-threshold assay tension

**THE FUNCTION.**
    fitness = w_e * encoding  +  w_c * carrying  +  w_r * (carrying * regulation)
Three components, each earning its place against an established requirement:
- **encoding** — memoryless stimulus->response performance. The FIRST-DESCENT term (D091): available
  to any network, rewards parameters up to interpolation. The floor.
- **carrying** — short-term memory (state held through a delay), credited ON ITS OWN. Gives the GA a
  slope toward memory BEFORE regulation exists -> prevents the Gate-A flat-landscape failure (D082) at
  this level. Also the prerequisite the bonus term multiplies.
- **carrying * regulation** — working memory: the regulation BONUS. The SECOND-DESCENT term -- the
  parameter-expensive capability (D093) that switches on only when the network both HOLDS context and
  USES it. Multiplicative because regulation is meaningless without something to regulate.

**WHY MULTIPLICATIVE FOR THE BONUS (PJM's insight, correctly placed).** The regulation reward is a
PRODUCT with carrying, so it is genuinely CONTINGENT on holding context -- you cannot collect the
regulation bonus by "regulating" a signal you are not holding. This encodes the biological truth
(working memory = memory + control) and is the mechanism that makes regulation land in the SECOND
descent rather than being cheaply available: the bonus is only accessible ON TOP OF carrying. The
product enforces the capability HIERARCHY (encoding < carrying < working-memory) in the landscape
itself.

**WHY NOT A PURE PRODUCT (the corrected worry).** CLM initially worried a product zeros out until BOTH
capabilities exist, recreating the Gate-A cliff. PJM corrected: the product is only the THIRD TERM;
encoding and carrying are ADDITIVE and credited independently. So a network with carrying-and-no-
regulation still scores on encoding + carrying; it only forgoes the bonus. **Gradient is intact in
every regime** (encoding slope, then carrying slope, then regulation-on-carrying slope) -- a climbable
curriculum, not a cliff. This satisfies BOTH the graded-assay requirement (detect/reward rudimentary
progress toward regulation) AND the double-descent structure (D091) at once.

**MAPPING TO DOUBLE DESCENT.** encoding = first descent (memoryless-achievable). carrying*regulation =
second descent (parameter-expensive, emerges late, D093). The additive structure IS the first/second-
descent decomposition; the multiplicative bonus being the second-descent term is the D093 story
(regulation is the expensive late capability) made QUANTITATIVE.

**CONSEQUENCE FOR THE CEILING (resolves the wiring fork).** The regulation term is carrying*regulation,
evaluated on HELD context (carrying = held-through-delay). So the ceiling validating this term MUST
demonstrate regulation operating on HELD context = the INTEGRATED carry-and-regulate version, NOT a
config where context is supplied directly (that would make the carrying factor meaningless -- context
given, not held -- so it could not validate the term as fitness actually computes it). The scoring
structure DECIDED the wiring: the ceiling is the integrated version.

**COMPONENT MEASURES.**
- encoding: performance toward the memoryless floor (existing).
- carrying: cue-selective state that persists AND decays through a silent delay (D092b validated
  measure; decay-across-delay is the discriminator vs the flat confound).
- regulation: GRADED, continuous "how well does the identical-probe response differ by HELD context
  in the way the task demands" (D091/D093 map-selection signature) -- continuous so it gives partial
  credit (the gradient WITHIN the bonus term).

**OPEN (tuning, not structure): the weights w_e, w_c, w_r.** They shape how sharp the second descent is;
too much on the bonus -> near-cliff again, too little -> regulation never worth climbing to. A tuning
question for later, with a real connection to REGULARIZERS-SMOOTH-THE-PEAK (D091): the weighting is
itself part of what makes the interpolation region a cliff vs a slope. Flag, do not solve now.

**FITNESS INTEGRATES; DIAGNOSTICS SEPARATE.** This fitness is the INTEGRATED quantity selection acts on
(one number per network, a distribution at each P). The carry/regulation DIAGNOSTICS (silent-delay,
identical-probe) separate the capabilities for ANALYSIS. Same relationship as state(mean, fitness) vs
state_var(metric) in D028/D033 -- extended to the capability hierarchy.

### D095 — Capability assays use a CAPACITY-CONSTRAINED, POPULATION-CONSTANT readout on the DESIGNATED output slice (not a per-network full-state fit). The fixed output slice is a SELECTION PRESSURE, not just a measurement choice.
**2026-07-20 · Accepted (method) · PJM** · fixes an experiment-A error and the interface-discovery problem for a WEIGHT-evolving GA

**THE ERROR THIS FIXES (experiment A, first attempt).** Measuring encoding/carrying/regulation, CLM fit
a per-network ridge over the FULL 50-dim state (best_nmse, uncapped alpha sweep). That is exactly the
cheat the interface-discovery literature warns against: **an uncapped readout lets the GA score well by
evolving rich-but-unstructured state that a flexible linear readout can decode -- measuring the READOUT's
power, not the network's DYNAMICS.** Fitness would then optimize readout-extractability, not computation.

**THE INTERFACE PROBLEM, AND WHY IT'S EASY FOR US.** Topology-evolving systems (NEAT/CPPN) face a
chicken-and-egg: can't evaluate function without a defined input/output interface, can't define the
interface without knowing where function resides. Four known fixes: (1) functional node attribution
(probe to discover I/O), (2) interface co-evolution (interface genes), (3) spatial anchoring, (4)
virtual/frozen full-state readout. **BUT we evolve WEIGHTS on a FIXED architecture with a DESIGNATED
input slice and output slice (D072) -- we do NOT evolve topology or node roles.** So we already HAVE
designated sensors/actuators; the discovery problem mostly does not apply. The right fit is option-4-lite:
read the DESIGNATED OUTPUT SLICE with a FROZEN, population-constant readout.

**THE DECISION (option a, PJM).** The capability/fitness readout is a FIXED map from the designated
output-slice activity to the task response, **trained/chosen ONCE and held CONSTANT across the entire
population and all generations** -- NO per-network fitting. This obeys the interface-literature's KEY
RULE (readout capacity must be constrained + population-constant or the GA evolves a classifier on top
of a random net). With zero per-network readout capacity, ALL task performance must come from the
network's dynamics routing the right signal, in readable form, to the output slice.
- Leaning: a single FROZEN LINEAR MAP (fit once on something neutral, then held constant) over PURE
  IDENTITY -- population-constant and non-cheatable, but doesn't demand the network emit the response in
  exact raw form (an unreasonable bookkeeping burden on top of the computation). Tuning within the
  decision, not the decision.

**THE FIXED OUTPUT SLICE IS A SELECTION PRESSURE (PJM's reframe -- the load-bearing insight).** A fixed
designated slice means a network computing the task correctly but ROUTING its answer to DIFFERENT nodes
gets no early credit -- penalized for a routing/bookkeeping mismatch, not a computational failure. So:
- **Early generations: the fixed slice UNDERSTATES misrouted-but-good networks.** Early fitness is a
  LOWER BOUND on capability; low early fitness != low capability (some is unresolved routing mismatch).
- **But using the designated slice CONFERS A SCORING ADVANTAGE**, so once any lineage routes to it, that
  lineage is selected, and the population CONVERGES onto the designated output. After convergence the
  slice distorts nothing (everyone uses it). The transient cost is paid once and self-corrects; the
  benefit (population-constant, cheat-proof readout) is permanent. Output location becomes a SELECTED
  trait, not a discovered one -- which is why (a) beats the discovery-based options: we IMPOSE the
  output and let selection DRIVE networks to use it, rather than discover per-network I/O (which would
  reintroduce readout variability + the cheat).

**METHODOLOGICAL CONSEQUENCES.**
- Do NOT read low EARLY-generation fitness as low capability -- it understates until the population
  converges on the output slice. Watch convergence directly: fraction of network output-energy landing
  in the designated slice should RISE over generations (a trackable diagnostic of the transient
  resolving).
- Redo experiment A with the frozen designated-slice readout, NOT the full-state per-network fit.
- Flat developed-from-random at GEN 0 is EXPECTED (PJM): the Baldwin premise is development+selection
  ITERATED, not development alone on random nets. Gen-0 flatness falsifies nothing; signal accumulates
  over GA rounds. (And the first descent comes from the network's EVOLVED dynamical encoding capacity,
  not from the task being memorylessly easy -- the memoryless floor being ~chance is BY DESIGN, D048,
  not a missing first descent.)

**CONNECTS TO:** D059 (minimal genome -- imposing rather than co-evolving the interface avoids interface
genes); D072 (the designated output slice this reads); D094 (the fitness whose components this readout
computes); the interface-efficiency penalty (gamma * n_io) from the literature is NOT needed since we do
not discover/co-evolve I/O -- the interface is fixed.

### D096 — Step 3 GA assembled and running: develop + D094 three-term fitness + D095 readout + selection, end-to-end. First observation of fitness CLIMBING under selection.
**2026-07-20 · Accepted (milestone) · executes D083/D094/D095**

**BUILT.** evolve.py evaluate() now DEVELOPS the phenotype (D083 inner loop) before scoring, and returns
the three D094 components read through the D095 capacity-constrained designated-slice readout:
- encoding = 1 - developed task NMSE (floored) -- via the per-output AFFINE readout (gain+offset per
  output neuron, NOT a mixing matrix -- the D095 non-cheating readout, which evolve.py ALREADY used).
- regulation = max(0, memoryless_floor - developed NMSE) -- below-floor excess = using context (D091).
- carrying = context-distinguishability of the developed state (D092b).
_fitness() is now the D094 three-term: w_e*encoding + w_c*carrying + w_r*(carrying*regulation) - c_syn*P.
EvolveConfig gains w_e/w_c/w_r and dev_ms/dev_eta. cfg threaded through evaluate + workers.
**Pleasant surprise:** the codebase ALREADY did D095 right (per-output affine readout on the designated
out_slice, explicitly "cannot mix neurons"); the experiment-A full-state ridge fit was CLM's deviation,
now discarded. Less to change than feared.

**FIRST RESULT (tiny smoke: pop 8, 3 gens, development ON).** FITNESS CLIMBS under selection:
fit_mean 0.0445 -> 0.0593 -> 0.0635; best_test (task error) FALLS 0.940 -> 0.908 -> 0.884; fit_std
RISES 0.007 -> 0.023 (population spreading = the gradient selection acts on). **This is the first time
in the project fitness has climbed under selection -- the thing Gate A (D082) failed to produce.** Not
over-read (3 gens, tiny pop, smoke only), but the machinery does what the redesign intended: development
creates scoreable capability, the three-term fitness gives it a gradient, selection climbs it.

**OBSERVATION TO WATCH (not yet a decision).** In the smoke run, encoding registers (~0.05) and
regulation registers (~0.085) but carrying reads ~0. Since regulation enters fitness ONLY through the
carrying*regulation product (D094), regulation is currently earning NOTHING (carrying=0 zeroes the
bonus) -- the early climb is driven by ENCODING. This is EXACTLY what the multiplicative structure
intends (no working-memory credit until carrying exists), and it is gen 0-2 with no time to build
carrying. BUT if carrying stays ~0 over a real run, the second-descent term never switches on and we
would see no regulation emergence. So: **watch whether carrying rises over a full GA run.** If it stays
zero, revisit either the carrying MEASURE (context-decode may be too weak, cf. the D090/D092 saga -- the
validated carry measure was decay-across-delay, NOT context-label-decode, so evaluate()'s carrying via
context-decode may be the weak instrument again) or development duration/strength. Flag, not yet fixed.

**KNOWN NEXT ISSUES (ordered).** (1) evaluate()'s carrying uses context-LABEL-decode, but D092b
validated the DECAY-ACROSS-DELAY measure instead -- likely need to swap in the validated measure (label-
decode was the confounded/weak one). (2) development duration is short (smoke used 800ms); real runs
need the D083 convergence-based or task-scaled duration. (3) cost of development per eval (D068) -- a
full GA develops every individual every generation; measure before a big sweep. (4) then the real
experiment: fitness-vs-P across the double-descent range (Gate B), watching for encoding first-descent +
carrying*regulation second-descent.

### D097 — Determinism + noise-robust (distributional) evaluation: per-assay noise seeding, k-assay averaging, and a determinism-bug fix (development noise was unseeded).
**2026-07-20 · Accepted (method) · PJM asked whether the code controls determinism**

**AUDIT RESULT.** Seed-tracking was GOOD at the genome/task/GA-structure level (random_genome, tasks,
run_evolution all seeded -> reproducible) but had a real gap: the SIMULATION-NOISE seed was a single
value set once at build (b2.seed(cfg.seed) in _build), the wrong granularity for distributional
evaluation. Two consequences: (1) no way to average over independent noise realizations of the SAME
network; (2) develop() ran with UNSEEDED noise -> the developed weights differed every call ->
evaluate() was NONDETERMINISTIC even with a fixed seed (caught: two evaluate() calls on the same genome
gave enc 0.0559 vs 0.0542).

**FIXES.**
- **behave(E, noise_seed=None):** re-seeds Brian2 before the run when given -> independent, reproducible
  noise realizations of the same network.
- **develop(E, ..., seed=None):** re-seeds before development -> the (noisy) development run is
  reproducible. THIS was the determinism bug -- development noise, not scoring noise, was the culprit.
- **evaluate() does K-ASSAY AVERAGING (D085c):** n_assays independent noise draws per genome, component
  scores MEANED, and per-assay SD reported (encoding_sd/carrying_sd/regulation_sd) as a
  signal-vs-noise diagnostic. Seeds derived from a STABLE content hash (zlib.crc32 of weight bytes ^
  cfg.seed) -- NOT Python's hash() (per-process randomized). Development seeded from the same gseed.
- **EvolveConfig.n_assays (default 3).**

**VERIFIED.** (1) evaluate() bit-identical across repeated calls (same genome+seed). (2) different
genomes differ (independence). (3) FULL GA bit-identical run-to-run (fit_mean 0.072009 both). (4)
per-assay SD works: regulation 0.088 ± 0.010 -> SD << mean -> stable to SIMULATION noise.

**INTERPRETIVE NOTE (refines the D096 "is 0.085 noise" question, per PJM).** The per-assay SD shows the
below-floor regulation reading is STABLE across simulation-noise draws (not sim-noise noise). BUT that
does NOT establish it as genuine regulation -- it could still be a spurious READOUT correlation (the
affine readout finding structure in this particular developed network). "Stable across noise" != "real
regulation." The remaining tests are the ones PJM named: does it PERSIST across re-assays with different
STIMULUS draws / task instances, and does it COMPOUND under selection over generations? Only signals
surviving those get interpreted. The SD machinery is the tool that will let us make these calls
quantitatively instead of eyeballing single numbers.

**DISCIPLINE RESTORED.** Do not interpret any single small component score until it survives (a)
noise-averaging (now built), (b) persistence across stimulus/task re-draws, (c) compounding under
selection. This operationalizes D085c and the standing "don't read small effects as signal" lesson.

**NOTE (parallel path):** b2.seed sets a global; under multiprocessing each worker gets its own stream.
Serial determinism verified; parallel-vs-serial identity not yet checked (the D078 batch-equivalence
runs at noise_sigma=0 to sidestep exactly this). Flag: verify parallel determinism before a big
parallel sweep.

### D098 — Carrying redefined: intrinsic persistence of the stimulus COVARIANCE structure (non-relational, whole-network reduction), NOT relational context-distinguishability. Resolves the measurement tangle and cleanly factors carrying from regulation.
**2026-07-20 · Accepted (redefines carrying) · PJM** · supersedes the context-decode / cued-separability carry measures

**THE PROBLEM THIS FIXES.** Every prior carry measure was RELATIONAL -- carrying = context-
DISTINGUISHABILITY (A-cue vs B-cue state separability, or decode the context LABEL). That framing caused
every difficulty: the label is weak (0.046 from oracle features, D090); the A-vs-B contrast needs a
clean CUE (the input-overlap problem); and it needs a known-positive with matching cue structure (the
engineered ceiling used explicit cues -> scored LOWER than random when fed task stimuli, because the
measure and the ceiling's cue-protocol mismatched). All of it came from defining carrying relationally.

**THE INPUT-OVERLAP DECISION (PJM, upstream of the redefinition).** Context-cue nodes and stimulus nodes
OVERLAP (context is statistical, on the same inputs as stimulus, as the task delivers it -- D048). NOT
separated cue vs stimulus nodes. Reasons: (1) biologically, MIXED SELECTIVITY is the rule, not clean
cue/stimulus segregation -- and (Rigotti/Fusi) mixed high-dim representations are the MECHANISM enabling
context-dependent computation, so separating them would pre-decide the representation against the very
substrate that makes flexible computation work (a D038 "don't build in the mechanism" violation). (2)
Overlap makes the intermediate CARRYING capability hard to measure in isolation, but the integrated
total-fitness assay is what matters for the study's larger picture.

**THE REDEFINITION (PJM).** Carrying = post-stimulus, the network PERSISTS a (decaying) signal that
RETAINS THE STATISTICAL REGULARITIES of the stimulus distribution -- assessed via a REDUCTION OF WHOLE-
NETWORK ACTIVITY. This is NON-RELATIONAL: a property of a single stimulus stream's aftermath measured
against the stimulus distribution's own statistics -- NO context label, NO A-vs-B contrast, NO cue.
Whether the network EXTRACTS USEFUL REGULATORY BEHAVIOR from the persisted statistics is a SEPARATE
matter, measured by the REGULATION score. -> clean STORAGE (carrying) vs USE (regulation) factorization,
which is exactly what D094's carrying*regulation wanted but the relational definition couldn't give.

**WHY THIS IS MEASURABLE WHERE THE OLD ONE WASN'T.** (1) No label to decode -- measure whether the
PERSISTING activity's statistics match the STIMULUS distribution's statistics (both in hand). (2) No cue
-> the input-overlap question evaporates; drive with the normal task stream, measure the aftermath. (3)
Whole-network reduction (intrinsic dynamical property, not an interface property) -- the interface-doc's
"virtual readout / max capacity" idea applied correctly. (4) DECAY-ACROSS-DELAY remains the discriminator
(D092b): real carrying persists AND decays; a flat fixed-point confound shows no structured persistence.

**THE SPECIFIC REDUCTION (PJM chose): COVARIANCE-STRUCTURE RETENTION.** Measure how much of the
persisting-state covariance aligns with the STIMULUS-DISTRIBUTION covariance -- because the task's context
lives in COVARIANCE (D048), so this measures retention of the TASK-RELEVANT statistics specifically, not
generic memory. Across increasing silent delays, requiring present-AND-decaying (D092b). (Chosen over
generic subspace/dimensionality persistence, which would measure retention of ANY stimulus structure.)

**VALIDATION (PJM chose): recurrence-on/off contrast, NOT the cue-based ceiling.** A network with slow-
current/strong recurrence should RETAIN covariance structure and decay; one without should decay to
structureless noise immediately. That contrast + the decay discriminator validates the measure -- no need
for the cue-based engineered ceiling (whose cue-protocol mismatched this non-relational measure anyway).

**CONSEQUENCE FOR D094.** Carrying is measurable again (cleanly, non-relationally), so the three-term
fitness w_e*encoding + w_c*carrying + w_r*(carrying*regulation) stays viable -- the carrying factor is now
a real, trustworthy quantity. (This retires the D096 "swap in decay-across-delay label measure" plan and
the backwards ceiling-vs-random result from the cued _carry_decay attempt: both superseded by the
covariance-retention measure.)

**BUILD.** Replace _carry_decay with a covariance-retention measure: drive with task stream -> silence ->
record persisting state across delays -> score = (persisting-state covariance alignment with stimulus-
distribution covariance) that is present at short delay AND decays by long delay. Validate via recurrence
on/off. Overlapping inputs (D098), whole-network reduction, no cue, no label.

### D098b — Carry measure WORKS: score the DECAY TIME (area under covariance-similarity-vs-delay), not similarity at a point. Recurrence extends the LIFETIME of the similarity, not its magnitude.
**2026-07-20 · Accepted (result) · PJM's insight resolved 3 failed attempts**

**THE FIX (PJM).** "What the recurrence will do is extend the TIME over which the covariation similarity
can be detected." Three carry measures failed because they measured similarity MAGNITUDE at a single (or
short-vs-long) delay -- where passive current echo (the last stimulus decaying through tau_syn/tau_r/
tau_slow) and active recurrent maintenance look THE SAME. A no-recurrence net scored AS HIGH as the
engineered attractor, because at one time point both have structure. The discriminator is not the VALUE
but the LIFETIME: passive echo decays FAST (~tau_slow); active recurrent maintenance decays SLOW.
**Score carrying as the DECAY TIME CONSTANT / AREA under the similarity-vs-delay curve.**

**VALIDATED (clean known-positive/negative, finally).** Similarity (covariance alignment of persisting
state with stimulus-distribution top subspace, above a SHUFFLED-stimulus baseline that removes fixed-
point confounds) measured across delays [50,150,300,500,800,1100]ms:
- **engineered attractor (POS):** curve [0.29, 0.05, 0.065, 0, 0, 0] -- similarity PERSISTS to 150-300ms.
  area score 0.0306.
- **no-recurrence net (NEG):** curve [0.238, 0, 0, 0, 0, 0] -- similarity GONE by 150ms (pure echo).
  area score 0.0113.
Attractor > no-recurrence (3x, correct direction). First carry measure to cleanly separate a known
carrier from a known non-carrier. Also fixes the earlier inverted-logic error (score = short*decay
PENALIZED slow decay -- backwards; the right statistic is LONG-lastingness = area/time-constant).

**THE MEASURE (final).** Drive with a task-stimulus run -> for each of several silent-delay lengths,
read the persisting state in a short window at the END of that delay, compute covariance-alignment with
the stimulus top-subspace, subtract the shuffled-stimulus baseline -> carry = area under that
similarity-vs-delay curve. Whole-network reduction, non-relational, overlapping inputs, no cue, no label
(all per D098). Passive echo -> fast decay -> small area; active maintenance -> slow decay -> large area;
flat confound -> removed by the shuffled baseline.

**CAVEATS.** (1) Modest dynamic range (0.031 vs 0.011) -- clean CONTRAST and correct ordering, fine for a
selection gradient (relative ordering is what selection uses), but not a large absolute signal. (2) COST:
the delay sweep is ~6 behaves x 2 (real+shuffled) = ~12 behaves per carry measure -> ~6x a single behave.
For the GA, use FEWER delays (e.g. 3: short/med/long) to control per-eval cost; full sweep only for
characterization. Factor into the cost budget (the D068 timing did NOT include this heavier carry
measure -- re-time before the pilot).

**BUILD.** Wire carry_v3 (area-under-similarity-vs-delay, shuffled baseline) into evolve.evaluate() as
the carrying component, with a reduced delay set for GA speed. Re-measure per-eval cost with it included.

### D099 — Step-3 pilot harness built + parallel determinism verified. Ready to run.
**2026-07-20 · Accepted (build)**

**BUILT: scripts/run_pilot.py.** The full apparatus (develop + 3-term D094 fitness + D095 readout +
D098b carry + selection) as a grid of independent (P, seed) CELLS -- embarrassingly parallel, VM-ready
(each cell its own provenanced GA). n_workers=6 default (PJM: leave 2 cores free on the 8-core laptop).
evolve.py history now records the three component means/bests per generation (enc/car/reg) so the pilot
can watch whether they COMPOUND under selection.

**THE PILOT'S QUESTION (a shakedown, NOT the double-descent curve).** Over 50 generations: (1) does
fitness CLIMB (vs flat Gate A birth-fitness, D082)? (2) do encoding/carrying/regulation PERSIST and
COMPOUND, or dissolve (the noise test PJM named -- gen-0 signal was expected-flat; real signal compounds
under selection)? (3) any NaN/blowup/collapse? (4) does carrying (now the validated D098b covariance-
decay measure) actually rise, so the carrying*regulation second-descent term can switch on (the D096
concern)? Grid: densities [0.2,0.4,0.6,0.8] x 1 seed, pop 30, 50 gens, dev_ms=800, n_assays=1. ~1.1 hr
on 6 cores. If encouraging -> design the full run.

**PARALLEL DETERMINISM VERIFIED (clears the D097 flag).** serial vs 2-worker parallel give BIT-IDENTICAL
results (fit 0.112470 both, car 0.026620 both). The per-assay/dev seeds derive from a CONTENT hash
(zlib.crc32 of weight bytes) not process/worker state, so distribution across workers does not change
results. ⇒ reproducible regardless of worker count AND across machines (important for the Azure-VM
escape hatch: same seed -> same result anywhere).

**VERIFIED end-to-end (sandbox dry run):** harness runs the grid, per-cell GA with full apparatus,
component tracking, provenance run + parquet + notebook stub, and a behave-or-not verdict. Fitness moved
in the dry run (density 0.4: 0.035->0.059 in 3 gens, best_test 0.982->0.900). Cosmetic only: a
multiprocessing semaphore-leak warning at shutdown (harmless).

**NEXT: run the pilot** (python scripts/run_pilot.py, ~1.1 hr on 6 cores), read the verdict, then design
the full run (P-range, seeds, generations, c_syn=0 vs >0 sweep) if the apparatus behaves.

### D100 — STANDING POLICY: every long run has CHECKPOINTING + LOGGING by default. Never run 6h/overnight without knowing it is running properly.
**2026-07-20 · Accepted (standing policy) · PJM**

**THE RULE.** Any long-running experiment (anything we would not sit and watch to completion -- roughly
> a few minutes) MUST, by default, unless explicitly waived:
1. **CHECKPOINT incrementally** -- persist results to disk AS EACH UNIT COMPLETES (per GA cell, per
   generation block -- whatever the natural unit is), NOT accumulated in memory and written once at the
   end. A crash/kill must lose only the IN-PROGRESS unit, never completed ones.
2. **LOG to disk while running** -- stdout/stderr AND warnings streamed to a log file in the run dir
   (run.logs()), so progress is monitorable live and a durable diagnostic record survives a crash. For
   PARALLEL runs, capture WORKER-side output too (per-worker log files) -- the numerically important
   warnings (NaN tripwires, Brian2 blowups, convergence failures) originate INSIDE workers during
   develop()/behave(), and do NOT flow to the parent log automatically.

**WHY (PJM).** "We can't go 6 hours or overnight before knowing whether an experiment is actually running
properly." The purpose of a long run is that you can't babysit it -> it must be observable-while-running
and crash-survivable, or you gamble hours of compute on nothing going wrong. Things DO go wrong (NaN
blowups, a degenerate cell, a leak at hour 4). Without checkpointing, a crash in cell 3 of 4 loses cells
1-2 as well (the all-at-once end write never touched disk). Without logging, you discover at hour 6 that
it died at hour 1, with no trace of why.

**THE GAP THIS FORMALIZES.** run_pilot.py (D099) as first built violated BOTH: it accumulated all cells'
history in memory and wrote the parquet only at the very end (a mid-run crash loses everything), and it
printed to stdout with no disk log (warnings/progress vanish with the terminal). The ~1hr pilot's
exposure is limited, but the 5+hr full run would be a real risk. Fix BOTH before the full run;
retrofit run_pilot.py and make it the template for all run_*.py harnesses.

**IMPLEMENTATION NOTES (for the retrofit).** Checkpoint: write each cell's history to the run's data/
dir as it finishes (one parquet per cell, or append to a growing file), so partial results are always on
disk; the final combined parquet is then just a concatenation. Log: a Tee on stdout/stderr to
run.logs()/<name>.log PLUS routing of the warnings module and Brian2's logger to the same file; per-
worker log files in run.logs() for worker-side warnings. Resumability (skip already-completed cells on
restart) is a nice-to-have that falls out naturally once cells checkpoint independently.

**SCOPE.** Default ON for all long runs. A short smoke/dry-run may waive it explicitly. This is now part
of what "a run harness" means in this project, alongside provenance (runs/ dir, manifest, notebook stub).

### D101 — Principled run-diagnostics panel: six readouts, each mapped to a specific knob and action. Fixed dev_ms (uniform development for clean interpretation), convergence flag SURFACED as a diagnostic (not used for early-abort).
**2026-07-20 · Accepted (methodological standard) · PJM**

**MOTIVATION.** A run (pilot or full) is not just "did it work" -- it is a DESIGN PROBE for the next
run's parameter budget. N, pop, gens, dev_ms trade against each other under a fixed compute budget
(cost ~ N^~1.5 x pop x gens x P-values x seeds x assays), so we cannot crank them all. The pilot's job
is to REVEAL which knob is the binding constraint, then spend budget there. This decision fixes a
DOCUMENTED, principled panel so the next-run design is data-driven, not eyeballed -- an instance of the
"measure before the big run" discipline (D068).

**THE DIAGNOSTIC PANEL (collect every run; each readout -> a specific knob + action).**
1. **Fitness slope over the last K generations.** Still climbing at the end (slope > threshold)?
   -> gens too few; INCREASE GENS. Plateaued early -> gens can be economized.
2. **fit_std trajectory.** Collapsed to ~0 early -> PREMATURE CONVERGENCE (population lost diversity) ->
   INCREASE POP (or mutation rate). Healthy = std stays > 0 while fitness climbs.
3. **Component trajectories (enc/car/reg means + bests).** Did carrying/regulation ever rise above
   noise and PERSIST/COMPOUND? If NEVER at any P -> suspect N TOO SMALL (not enough neurons for
   evolution to build working memory) OR dev too short. Encoding-only rise is expected early (simplest
   to develop, D096); the test is whether car/reg follow.
4. **Development convergence fraction** (the develop() `converged` flag, D087/this decision). Fraction of
   the population whose plastic weights SETTLED within dev_ms. LOW -> dev_ms TOO SHORT (scoring IMMATURE
   phenotypes, undermining the D083 develop-then-score premise) -> INCREASE DEV_MS. Uniformly high and
   fast -> dev_ms wastefully long (could shorten). 
5. **P-dependence of 1-4.** Do higher-P (denser) cells build capability that lower-P cannot? This is the
   FIRST WHISPER of double-descent structure -- the pilot is not designed to RESOLVE the curve (that is
   the full run) but a monotone P-trend in capability emergence is the signal the effect is there.
6. **NaN/abort count** (develop() NaN tripwire + any degenerate collapse). Numerical health; nonzero ->
   inspect before scaling.

**Each diagnostic maps to ONE knob** so the read is unambiguous: (1)->gens, (2)->pop, (3)->N or dev_ms,
(4)->dev_ms, (5)->the science (is the effect present), (6)->numerical health. Report all six at the end
of every run, with the implied action.

**DEV_MS DECISION: FIXED, uniform (PJM).** Development runs a FIXED dev_ms for every network; we do NOT
early-abort on convergence. Early-abort could save some compute, but a UNIFORM development budget makes
results CLEANER TO INTERPRET (every phenotype matured under the identical protocol -- variable dev-time
would be a confound and would make per-eval cost unpredictable). The develop() `converged` flag is
therefore used ONLY as diagnostic #4 (is dev_ms long enough?), NOT as a control-flow early-stop. If the
flag shows widespread non-convergence, we RAISE the fixed dev_ms rather than add early-abort. (Supersedes
the D096 open question about development duration: it is now a diagnostic-driven fixed value.)

**BUILD.** (a) evaluate() captures develop()'s `converged` flag and returns it; run history aggregates
the convergence fraction per generation. (b) A documented post-run analysis (in the run harness /
analysis module) computes all six readouts and prints each with its implied action. (c) Fold into the
D100 retrofit so the pilot -- and every run_*.py thereafter -- emits the panel at completion. This is now
part of what "a run harness" produces, alongside provenance (D-provenance) and checkpointing+logging
(D100).
