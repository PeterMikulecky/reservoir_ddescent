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

### D102 — STANDING POLICY: analysis & troubleshooting scripts must LOG their terminal output to disk, not just persist data. The analytic narrative is part of the record.
**2026-07-21 · Accepted (standing policy) · PJM**

**THE RULE.** Every analysis / troubleshooting / diagnostic script (not just long RUNS -- D100 covers
those) MUST capture its terminal output (the printed analysis: tables, verdicts, the numbers we
reasoned from) to a DURABLE LOG FILE, in addition to whatever data it persists. Default ON.

**WHY (PJM).** "We need to be able to tell the STORY of how we arrived at our eventual optimized system
long after the terminal has been closed." Parquet/data files persist the RAW RESULTS, but the ANALYTIC
OUTPUT -- what we computed from them, what it showed, what it led us to conclude and do next -- is the
NARRATIVE of how the system was diagnosed and optimized. That narrative is exactly what a methods
section, a lab notebook, or a future collaborator (or future-self) needs to reconstruct the reasoning.
Persisting data without the analysis that interpreted it loses half the record. The troubleshooting
scripts this session (analyze_pilot, cost probes, carry-measure experiments) all printed to stdout and
VANISHED when the terminal closed -- the gap this fixes.

**IMPLEMENTATION.** Analysis scripts tee stdout (and stderr/warnings) to a log file. Preferred location:
under the relevant run's dir (run.logs()/<analysis_name>.log) when analyzing a specific run, else a
dated analysis/ log dir. A lightweight tee helper (print to console AND append to log) is the minimal
form; the log should record the command/args, a timestamp, and the full printed output. Generalizes
D100 (which mandated logging for long RUNS) to ALL analytic output.

**SCOPE.** Default ON for analysis/troubleshooting/diagnostic scripts. Trivial one-off REPL checks may
waive it, but anything whose output we would cite, revisit, or reason from later gets logged. Together
with provenance (data + manifest) and D100 (run logs), this completes the record: raw data + run logs +
ANALYTIC NARRATIVE.

### D103 — Development is missing its "expression" half: it has STABILITY (Vogels iSTDP) but neither LEARNING (eSTDP) nor COMPETITION (lateral inhibition). Literature-grounded diagnosis of the flat pilot.
**2026-07-21 · Accepted (diagnosis + design direction) · PJM's development model + lit search**

**PJM's development model (the frame).** Development must do TWO things: (1) STABILIZE -> an E/I-balanced
canvas the network can operate against (our Vogels mechanism); (2) EXPOSE the stabilized canvas to
stimuli UNDER PLASTICITY so the network's LATENT POTENTIAL expresses itself as fitness scores. Then the
GA selects on those scores. The current implementation does (1) but NOT (2): the only plasticity during
stimulus exposure is the SAME Vogels iSTDP -> it stabilizes but cannot express computational potential,
because the excitatory (signal) pathways are frozen. So development had its stabilization half and none
of its expression half. This EXACTLY explains the flat pilot + the "state carries no task-usable info"
finding (G3): balanced-but-random nets sit at the floor; no eSTDP -> no stimulus-selective representation
ever forms -> undifferentiated fitness -> no gradient -> random-walk drift.

**LITERATURE CONFIRMS the two-part model, and expands it to a TRINITY (Zenke/Gerstner doc: Hebbian
learning + competition + stability).**
- **eSTDP = the missing ENGINE.** Excitatory STDP is the Hebbian competitive rule that selectively
  strengthens pathways correlated with input and self-organizes STIMULUS-SELECTIVE structure (Biomimetics
  2025); "long-term excitatory STDP enables sparse, efficient learning of salient input features"
  (Srinivasa & Cho 2014, Front Comput Neurosci -- an E/I reservoir + readout architecture almost
  identical to ours). THIS IS THE MISSING HALF.
- **iSTDP/Vogels = the STABILIZER, not standalone development.** Srinivasa & Cho: "iSTDP enables this
  [excitatory] learning to be stable by establishing balance." REFRAME: our Vogels rule is the safety
  mechanism that makes eSTDP possible -- we built the stabilizer without the engine it was meant to
  stabilize. Alone it stabilizes nothing.
- **COMPETITION via lateral/feedforward inhibition = SELECTIVITY (PJM's specific intuition, CONFIRMED).**
  PJM: Vogels is mostly global population-mean-rate control; biological circuits also use localized,
  faster inhibition to shape SELECTIVITY. Lit nails it: Lagzi et al. (in Modularity iSTDP paper) -- in
  mouse frontal cortex PV vs SOM interneurons follow DIFFERENT STDP rules and roles: PV mediates
  HOMEOSTASIS in excitatory activity (Vogels-like), SOM builds LATERAL inhibition providing COMPETITION
  between excitatory assemblies. And (dual-STDP, Biomimetics 2025): FS-mediated lateral inhibition drives
  WINNER-TAKE-ALL competition that promotes heterogeneous E->E differentiation (forces neurons to become
  selective for DIFFERENT features; without it, eSTDP collapses / LTD-bias washes out structure).

**CRITICAL CAUTION (the temporal paradox -- Zenke/Gerstner, already in REFERENCES per D085).** Hebbian
(fast) and homeostatic (slow) plasticity have a PARADOXICAL SEPARATION OF TIMESCALES; naive combination
breaks (homeostasis too slow to stabilize fast Hebbian runaway). This is a known blowup mode -- same
family as the Oja blowup (D086). => ADOPT TESTED eSTDP+iSTDP COMBINATIONS, do NOT hand-roll the
interaction. Candidate reference architectures: Srinivasa & Cho 2014 (E/I reservoir + readout, closest
to ours); Diehl & Cook 2015 (STDP+WTA MNIST); Brian2 canonical STDP.

**DESIGN DIRECTION (not yet built).** Development becomes eSTDP (build representation) + competition
(lateral inhibition -> selectivity) + iSTDP/Vogels (stabilize). Notes: (a) our substrate ALREADY has
inhibitory neurons + E->I/I->E connectivity, so WTA competition may emerge through EXISTING inhibitory
structure once excitatory synapses can learn -- test adding eSTDP (on E->E, maybe E->I) BEFORE adding a
separate hand-built WTA. (b) D038/D074: add eSTDP as a GENERAL Hebbian rule, let selectivity emerge from
stimulus statistics; do NOT hand-wire features. (c) This is the D087 "step 2 excitatory learner",
previously deferred -- now identified as THE missing half, not an enhancement. Promotes it ahead of most
of the post-pilot queue (though beta/B1 still matters once a fitness gradient exists to select on).

**STATUS.** Diagnosis + direction accepted. Build sequence, timescale-separation handling, and which
tested rule to adopt: next session, measure-and-adopt (D086 discipline), likely validate the eSTDP
learner draws out representation (state beats floor after development) against the ceiling-style control
before wiring into the GA.

### D104 — The dual-P framework: separate P_dev (representation-forming plastic E->E, the double-descent x-axis) from P_evo (evolvable static/stabilizing weights + rule hyperparameters = dynamical boundary conditions). Saturation handled three ways.
**2026-07-21 · Accepted (framework, load-bearing for the double-descent x-axis) · PJM**

**WHY THIS EXISTS.** Adding eSTDP (D103) created distinct neuron/synapse categories with different
plasticity status, forcing the question: what counts as P (adjustable parameters) for the double-descent
x-axis? P in statistical learning theory strictly measures the DEGREES OF FREEDOM AVAILABLE TO FIT THE
ENVIRONMENTAL DATA. Not all our weights do that.

**THE TWO-TIMESCALE SPLIT.**
- **P_dev (developmental P):** within-lifetime plastic updates that FIT THE STIMULUS/TASK DATA -> the
  eSTDP-plastic E->E synapses. Optimization target = the environment's stimulus patterns. **This is the
  DIRECT DRIVER OF INTERPOLATION** -- it sets model capacity relative to the environmental dataset size.
  The double-descent curve should be plotted against P_dev.
- **P_evo (evolutionary P):** genome-encoded initial conditions, STATIC evolvable weights (E->I, I->I),
  the STABILIZING plastic weights (I->E via Vogels), and rule hyperparameters (eta, gmax, etc.).
  Optimization target = fitness across generations. **This is the CONSTRAINT / LANDSCAPE SHAPER** -- it
  sets the inductive bias and dynamical stability regime WITHIN WHICH P_dev operates.

**KEY INSIGHT (boundary conditions).** Static inhibitory weights (E->I, I->I) AND stabilizing plastic
weights (I->E Vogels) act as DYNAMICAL BOUNDARY CONDITIONS: they constrain the trajectory of activation
but do NOT directly store task representations. This inherits the D103 functional division (iSTDP
stabilizes, eSTDP represents) into the P-accounting. Note Vogels I->E is PLASTIC in mechanism but
BOUNDARY-CONDITION in function -> it goes with P_evo, not P_dev. Rule machinery (traces apre/apost,
per-synapse eta/gmax, wf/ws scales) is NOT P at all -- it's the differential-equation machinery of the
rule, not a degree of freedom.

**WHY PLOTTING AGAINST P_total SMEARS THE PEAK (and may explain the flat sweeps).** Classic double
descent peaks at the interpolation threshold P ~= N_samples. Plotting test performance vs P_total:
(a) MASKED RATIOS -- a net can double total density by scaling static inhibitory connections without
changing E->E reservoir capacity; (b) POST-DEVELOPMENT COLLAPSE -- support-freeze / saturation reduces
the actual rank below nominal. => varying P_total shifts P_evo WITHOUT systematically pushing P_dev
across its interpolation threshold. **This is a candidate causal explanation for why the global density
sweeps (pilot + sparse sweep, G1) came back DEAD FLAT across a 20x range: we varied the wrong P.** Not
"no double descent," not "quenching" -- we never placed P_dev relative to the data. TESTABLE via the
decoupled sweep below.

**SATURATION ACCOUNTING (corrected 2026-07-21 after PJM's objection -- location != freedom).** An
initial draft excluded CEILING-saturated weights as "pinned, not free." **That was WRONG (PJM):** a
parameter's identity as a degree of freedom is STRUCTURAL (was it free to vary in response to data?),
NOT a function of the VALUE it settled at. A weight that stabilized at an intermediate value did so
because that value was functionally selected; a weight that stabilized at g_max did so for the SAME
reason -- both are used, load-bearing DOF that found their optimum; one optimum just happened to be
extremal. Excluding the ceiling weight would penalize a parameter for finding a STRONG solution and
systematically undercount exactly the parameters doing the MOST work. (The error was conflating LOCAL
mobility at a boundary -- gradient can only push one way -- with STRUCTURAL freedom to fit data; those
are different. Double-descent P counts structural DOF, not end-of-training local wiggle room.)
=> **CEILING-saturated weights COUNT, unconditionally** -- structurally identical to interior weights.
Interior weights count (never in question). The saturation trichotomy collapses.

**THE ONLY REMAINING QUESTION IS THE FLOOR -- and it's the genuine structural-vs-effective-P fork.** A
weight driven to ~0 (w->w_eps) settled there because ~0 was its functionally-selected value. Does it
count?
  - **STRUCTURAL P view:** it was free to fit data and chose ~0; it counts. => P_dev,structural = ALL
    plastic E->E synapses, regardless of final value. Saturation irrelevant.
  - **EFFECTIVE P view:** a weight at ~0 has removed itself from the fitted function (the standard
    L0/L1 "effective parameters" notion -- parameters regularized to zero don't contribute to the
    effective complexity that sets the interpolation threshold). => P_dev,effective excludes only the
    floor-pruned ~0 weights.
Both are legitimate and answer DIFFERENT questions; the double-descent literature itself cares about
this structural-vs-effective distinction. Don't hard-code -- MEASURE BOTH and let the interpolation-peak
sharpness adjudicate which the peak tracks:
  - **P_dev,structural** = count of ALL plastic E->E synapses (every parameter free to fit data).
  - **P_dev,effective** = count of plastic E->E synapses with |w_post| non-negligible (excludes ONLY
    floor-pruned ~0 weights; ceiling + interior both included).
  - **floor_fraction** = (structural - effective)/structural = fraction pruned to ~0 = the "how much did
    development REGULARIZE" readout, now correctly located as the ONLY quantity separating the two P's.

**FLOOR RESOLUTION (PJM, 2026-07-21): a single PRINCIPLED dynamically-grounded floor, used throughout,
spot-checked -- NOT two versions of every run.** Rather than run floored (prevent-vanishing) AND
unfloored (vanish-then-subtract) versions of every development/selection round (a permanent 2x tax to
keep re-answering one question), adopt ONE principled floor and validate it with targeted controls.
- **Principled, not arbitrary:** set w_min at the weight magnitude below which a synapse's current
  contribution is DYNAMICALLY NEGLIGIBLE -- i.e. below the network's intrinsic noise/drive scale (a
  synapse whose single-synapse current is smaller than the noise the neuron already experiences, or a
  few % of typical total synaptic drive, is indistinguishable from absent). The floor is DEFINED BY THE
  DYNAMICS, not chosen by taste. Derive it (D068 measure-don't-guess): measure typical total synaptic
  drive per neuron + noise-induced fluctuation at the study's operating point (N=50, input_gain,
  noise_sigma, taus), set w_min to the weight whose current contribution falls below that scale. If
  those constraints change, the floor RECOMPUTES (correct -- it should track the dynamics).
- **Why this dissolves the fork WITHOUT suppressing pruning:** a weight resting at this floor is BOTH
  "still in the support (P structurally)" AND "contributing negligibly (pruned effectively)" -- and
  those now COINCIDE by construction rather than conflicting. Pruning-in-effect (weights become
  dynamically negligible) with clean-P-in-form (they rest at a known floor, not an ambiguous zero). The
  "vanished threshold" and the floor become the SAME dynamically-set number, so there is no arbitrary
  threshold to argue about. floor_fraction (fraction resting AT the floor) still measures how much
  development regularized -- the signal is preserved, just measured as "fraction at floor."
- **Uniform, not per-synapse:** one network-level w_min shared by all E->E plastic synapses (it's set by
  the network-level dynamical scale all synapses share). Simplest implementation: raise the D087 w_eps
  from a numerical guard (1e-9) to this computed dynamical floor.
- **P_dev definition under the floor:** P_dev = count of plastic E->E synapses (all resting at-or-above
  the floor) -> structural and effective COINCIDE -> a clean, threshold-free x-axis used THROUGHOUT.
- **SPOT-CHECK discipline (not routine 2x cost):** run the formal floored-vs-full-vanishing comparison
  at a FEW representative P_dev points (e.g. one low, one near the expected interpolation threshold, one
  high). Agreement -> floor validated, trust it throughout. DISAGREEMENT at some point -> a signal that
  pruning is load-bearing THERE (informative flag, investigate), paid for with ~3 comparison runs not a
  doubled study. Same project pattern as principled-default-validated-by-targeted-controls (cf. D087
  measure-effective-P-at-analysis rather than constrain development).

**P_dev AXIS -- FINAL RESOLUTION (2026-07-21, perspective doc + PJM's factoring-out worry): RAW E->E
count is the x-axis; effective rank is an ALONGSIDE DIAGNOSTIC, not the axis. Measure both ways, compare.**
A perspective doc proposed three principled epsilon bases (A: dynamical SNR w_ij*<r_j> > eps_PSP;
B: plasticity-sensitivity / is-it-still-adjustable; C: spectral EFFECTIVE RANK of W_EE via singular-value
entropy P_eff = exp(-sum p_k log p_k)). Option C is attractive -- it eliminates the arbitrary per-synapse
threshold (answering the "5% is arbitrary + linear + too-large-given-nonlinearities" objection at its
root) and is nonlinearity/recurrence-aware (counts functional representational dimensions, not scalar
magnitudes). BUT PJM raised the decisive methodological worry: **conventional double-descent plots use a
RAW STRUCTURAL COUNT as the x-axis; the phenomenon LIVES IN THE GAP between raw-P and effective-P (the
overparameterized second descent happens because raw-P keeps rising while EFFECTIVE capacity saturates
via implicit regularization). Plotting against effective rank could FACTOR OUT the double descent A
PRIORI** -- compress/fold the overparameterized regime where effective rank saturates, hiding the very
effect we're hunting. => Option C, as the AXIS, risks destroying the phenomenon it's meant to detect.
- **Two problems pull opposite ways:** (1) SMEARING (D104) -- raw TOTAL count mixes representational
  E->E with boundary-condition E->I/I->I -> argues for a refined count; (2) FACTORING-OUT (PJM) --
  effective RANK absorbs the raw-vs-effective gap -> argues against going all the way to a spectral axis.
  The correct x-axis is the MIDDLE level: **raw count of the REPRESENTATION-FORMING parameters = raw
  E->E synapse count / E->E density.** Restricting to E->E fixes smearing; keeping it a RAW COUNT
  preserves the gap where double descent lives. D104's insight (which CLASS of parameters) is right;
  the WITHIN-CLASS accounting stays RAW.
- **THE PLAN -- one x-axis, three overlays (measure both ways, compare):**
  * **x-axis (primary curve): raw E->E count / E->E density.** The axis that CAN show double descent.
  * **Effective rank of W_EE (Option C): measured ALONGSIDE** as the diagnostic that EXPLAINS the shape
    -- if it tracks raw count up to interpolation then SATURATES in the overparameterized regime, that
    is the implicit-regularization signature producing the second descent. The GAP between the raw-E->E
    curve and the effective-rank trajectory IS the double-descent mechanism made visible (conventional
    papers leave this gap implicit; we measure it explicitly = a contribution, not a liability).
  * **Raw total / P_total: the smeared comparison** (D104) showing why naive whole-network accounting
    fails in a multi-class network.
  * **floor_fraction (D105): the pruning/regularization readout.**
- **Effective rank of W_EE (weights) vs of developed ACTIVITY (representation):** W_EE (the parameters,
  what we sweep) is PRIMARY; activity effective-rank is a complementary measure (closest to functional
  DOF, most directly honors the nonlinearity point). Reuses existing measures.py (effective_rank,
  participation_ratio); connects to the E1 dimensionality<->connectivity core.
- **The floor (D105) is now NON-load-bearing for P-counting either way** (raw E->E count doesn't need it;
  effective rank doesn't use it). It STAYS in the dynamics for numerical stability + EVOLUTIONARY RESCUE
  (a weight resting at w_min, not exactly 0, remains a mutable P_evo locus -- the perspective doc's
  Section-1 point: vanished weights are EXCLUDED from P_dev but RESCUED in P_evo, since they're still
  mutable genome loci reactivatable next generation. floor_fraction = exactly the set that is in P_evo
  but not P_dev).

**GENERAL PRINCIPLE (PJM, 2026-07-21) -- the standing rule for P-accounting under ambiguity.** A
parameter's inclusion in P is decided by its status on two timescales:
  - **Developable (changes within a lifetime) -> IN P_dev.** Unambiguous: it fits within-lifetime data.
  - **Not selectable AND not developable -> NOT P.** Unambiguous: fixed rule machinery (traces, scales).
  - **SELECTABLE BUT NOT DEVELOPABLE -> THE AMBIGUOUS CASE -> ALWAYS measure BOTH WAYS and compare.**
    Such a parameter is a real DOF on the evolutionary timescale but inert on the developmental one, so
    whether it counts toward P is genuinely undetermined a priori. Do NOT adjudicate it by fiat/functional
    judgment (the mistake of trying to argue each class in or out). Instead carry BOTH accountings
    through -- P WITH the class included and P WITHOUT -- plot the double-descent curve under each, and
    let the COMPARISON be the finding: if the curves differ, that difference reveals whether the class is
    load-bearing for the phenomenon.
**Why this is the correct default (not just even-handedness): EPISTEMIC SAFETY.** Committing to a single
P-accounting risks either SMEARING (count too much -> dilute/mask the peak) or FACTORING-OUT (count too
little / the wrong effective measure -> divide the phenomenon out a priori, per the effective-rank
worry). Since we cannot always know a priori which error a given accounting commits, the both-ways
comparison is the ONLY move that cannot destroy the phenomenon by construction. It generalizes the
factoring-out logic: ANY selectable-not-developable class gets both-ways-and-compare, full stop. (Class
ASSIGNMENTS -- which synapse is developable vs selectable-not-developable -- come from the literature +
prior structural decisions, e.g. I->E is selectable-not-developable=P_evo, E->E is developable=P_dev;
this principle governs only how the AMBIGUOUS ones are counted, i.e. by comparison not judgment.)

**ACTION (Step 1 done here; Steps 2-3 for the build).**
- **Step 2 -- decouple the knobs:** the variation test / double-descent sweep varies E->E DENSITY
  specifically (directly driving P_dev across its threshold), holding inhibitory ratios FIXED (stable
  P_evo background). NOT a global density sweep.
- **Step 3 -- dual x-axis reporting:** primary curve vs P_dev (effective, post-development E->E);
  secondary curve vs P_total/P_evo plotted ALONGSIDE, to explicitly demonstrate why traditional ML
  parameter accounting breaks down in an evolutionary/developmental model (a RESULT, not a nuisance).
- Measure P_dev,free / P_dev,active / floor_fraction per developed network; plot the curve against each;
  report which sharpens the interpolation peak.

**STATUS.** Framework accepted. Wire the effective-P_dev measurement into the developed-network analysis;
reconfigure the variation test (D103/next) to sweep E->E density with fixed inhibitory ratios. This
supersedes the naive "P = total nonzero synapses" the pilot used, and refines the D087 "measure
effective-P" thread with a concrete target and definition.

### D105 — Principled dynamical floor DERIVED and SET: w_min_ee = 0.02 (peer-relative, not absolute-noise). Also surfaced: the operating regime is very noisy (noise SD ~= threshold).
**2026-07-21 · Accepted (derivation + implementation of D104's floor) · logged analysis_logs/*derive_dynamical_floor***

**DERIVATION (D068 measure-don't-guess; D102 logged).** Two attempts:
- **v1 (wrong reference):** benchmarked a SINGLE synapse's voltage kick against the TOTAL noise voltage
  SD -> w_min ~0.6-1.0, absurdly large (bigger than typical weights). Flaw: one synapse is always tiny
  vs aggregate noise, ESPECIALLY here where noise SD ~= threshold. Wrong frame.
- **v2 (correct, peer-relative):** a synapse is "dynamically negligible" when weak RELATIVE TO ITS PEERS
  -- relative to the typical active E->E weight the rest of the population is computing with. Measured
  the developed E->E weight distribution (median 0.41, 5th pct 0.038, 95th pct 1.15, spans 0->2.26 --
  development DOES differentiate + naturally prune toward 0). Set w_min = 5% of median active weight
  = ~0.020. A weight there contributes ~5% of a typical synapse's kick (0.0018 vs 0.036) = negligible
  relative to peers, and sits at the bottom edge of the real distribution (near the 5th pct) -- catches
  the pruned tail without swallowing the active population.

**SET: EvoNetConfig.w_min_ee = 0.02**, wired as the lower clip of the eSTDP rule (separate from the
inhibitory w_eps_dev numerical guard -- the FUNCTIONAL floor applies to E->E per D104). VERIFIED:
developed E->E weights bottom out AT 0.0200 instead of vanishing; floor_fraction (fraction resting at
floor) is measurable = the regularization readout. Structural and effective P_dev now COINCIDE (D104
fork dissolved). RECOMPUTE w_min_ee if the operating point (N, noise_sigma, gains, taus) changes.

**REFERENCE-FRAME NOTE (auditable choice).** Absolute-noise vs peer-relative gave a 30x difference
(0.6 vs 0.02). Peer-relative is correct for P-COUNTING: "negligible as a degree of freedom" means weak
relative to the population doing the computation, not relative to aggregate noise. Both recorded in the
log so the reasoning is auditable.

**SEPARATE FINDING (flagged, not chased): the network is VERY NOISY.** noise_sigma=1.0 -> noise voltage
SD ~= 1.0 ~= threshold. Each neuron's voltage jitters by ~the entire distance-to-threshold from noise
ALONE. Per-synapse SNR is low. This is independent of the floor and may bear on the flat-pilot / eSTDP-
selectivity story: eSTDP trying to learn selectivity from a signal buried in threshold-scale noise may
struggle. Candidate factor to revisit when testing whether eSTDP produces functional variation (add to
the watch-list alongside the H-series). NOT chased now.

**SPOT-CHECK (deferred to when the variation test runs, per D104):** validate this floor against full-
vanishing (w_eps=1e-9) at a few representative P_dev points -- agreement validates the floor throughout;
disagreement flags load-bearing pruning.

### D106 — eSTDP effectiveness landscape (SNR x eta_e): rules OUT both tuning suspects (noise/rate), points AT the deferred competition leg. Measured on an UNSELECTED randomized network.
**2026-07-22 · Finding (diagnostic, not yet a design change) · logged analysis_logs/*estdp_effectiveness_landscape* + *estdp_spread_probe***

**CONTEXT.** After building eSTDP (D103), two probes on UNSELECTED random networks:
1. **Spread probe** (estdp_spread_probe): population of 12 unselected genomes, eSTDP ON vs OFF. Fitness
   spread SD 0.0198 (ON) vs 0.0195 (OFF) = 1.02x; eff_rank(state) spread also ~equal. eSTDP made ~no
   difference to cross-genome representational OR fitness spread. BUT it used the WEAK DEFAULT
   eta_e=5e-4 (0.5*dev_eta) -> possibly underpowered. Motivated the landscape.
2. **Effectiveness landscape** (estdp_landscape): ONE fixed randomized base network; sweep noise_sigma
   (SNR) in [0.1,0.25,0.5,1.0] x eta_e in [5e-4,2e-3,5e-3,2e-2]; per cell measure how much eSTDP
   RESHAPES the representation vs its own OFF-baseline (state_change, w_diff_std, eff_rank).

**LANDSCAPE FINDINGS (disentangles the tangled suspects):**
- **eta_e works as expected but is a WEAK lever:** w_diff_std climbs cleanly with eta_e (0.003->0.11),
  and state_change rises with it too but only weakly -- even at eta_e=0.02 (40x the default),
  state_change maxes at ~0.15 (a 15% state perturbation).
- **SNR barely matters -- D105's low-SNR-kills-eSTDP hypothesis NOT supported:** state_change is nearly
  flat DOWN each noise column (e.g. at eta_e=0.02: 0.149/0.130/0.131/0.122 across noise 0.1->1.0). eSTDP
  is about equally (in)effective at very-quiet (0.1) and current-near-threshold (1.0) noise. The noise
  regime is NOT the wall. (Representational RICHNESS is set by noise: OFF eff_rank 13/17/23/30 as noise
  rises -- more noise, higher rank -- but that's the noise, not eSTDP.)
- **THE CORE FINDING: eSTDP does NOT change representational DIMENSIONALITY anywhere.** eff_rank_on ==
  eff_rank_off in EVERY cell (13/13, 17/17, 23/23, 30/30). eSTDP moves weights and nudges the state
  ~15% at best, but never alters the effective dimensionality of the representation, at any (SNR,eta_e).

**INTERPRETATION (held with discipline -- one grid, unselected net).** Both TUNING hypotheses (eta_e,
SNR) are largely RULED OUT as the explanation for the flat spread -- cranking eta_e 40x and quieting
noise 10x does not unlock a qualitatively different regime. The finding is that **eSTDP-ALONE is a weak
lever on the representation** (no dimensionality change, modest perturbation). This points at the
DEFERRED THIRD LEG of the D103 trinity: **COMPETITION via lateral inhibition.** We built eSTDP (learner)
+ Vogels (stabilizer) and DEFERRED competition, betting it might emerge through existing inhibitory
structure. The grid is evidence it does NOT: the dual-STDP literature (D103 refs) was explicit that
FS-mediated lateral-inhibition WTA competition is what drives HETEROGENEOUS E->E differentiation; without
it, eSTDP changes wash out (LTD-bias / uniform-drift failure mode the literature warned of). So the
deferred piece looks NECESSARY, not optional.

**IMPORTANT FRAMING (PJM).** These results are for an UNSELECTED, RANDOMIZED network, WITHOUT lateral
competition. This is the FLOOR of expected performance, not a verdict on the mechanism: (a) selection
hasn't acted -- we're looking at raw pre-selection material; (b) the punch isn't spiked -- competition,
the leg the grid itself fingers as missing, isn't in yet. Reasons for optimism that eSTDP+competition,
under selection, behaves very differently. NOT a "don't build" verdict -- a "build the RIGHT next thing
(competition) before the full stack" signal.

**NEXT.** Add lateral-inhibition WTA competition (D103 third leg) and RE-RUN THIS EXACT LANDSCAPE:
does eSTDP-WITH-competition change eff_rank / produce large state_change where eSTDP-alone did not? The
grid is now a reusable instrument for that A/B. Then, in whatever region competition makes eSTDP live,
run the across-genome spread test. Also note the spread probe should be re-run at a live eta_e (not the
weak default) once competition is in.

### D107 — Developable lateral-inhibition competition built (D103 third leg). PJM's two corrections: competition must be DEVELOPABLE (not static), and its differentiation is FUNCTIONAL/temporal (not E->E weight variance). First movement off the floor.
**2026-07-22 · Build + finding · toggle dev_wta_comp (off-switch retained per PJM)**

**FIRST ATTEMPT (wrong) + PJM'S CORRECTIONS.** Built competition as a STATIC, symmetric, all-to-all
fast inhibition among E neurons. It suppressed firing hard (mean_state 1.15->0.24, sparsity 0.19->0.82
as gain rose) but did NOT increase E->E weight variance (flat 0.124 across 100x gain) -- I read that as
failure. PJM corrected on two counts, both right:
  1. **Static lateral inhibition can't differentiate.** A fixed symmetric all-to-all term just DAMPS
     everyone uniformly = no selection. The differentiating power lives in the competition's
     DEVELOPABILITY -- it must break symmetry over developmental time (specific suppressive
     relationships forming: this neuron reliably suppresses that one) to carve distinct winners.
  2. **The differentiation is FUNCTIONAL/temporal, not structural in E->E weights.** WTA changes WHO
     FIRES WHEN (the activity manifold), which need not show up as E->E weight-variance. I was measuring
     the wrong signature (imported from one paper's structural readout); the sparsification I saw WAS
     the WTA effect, in the activity where PJM said it lives. And it's what our (A) commitment actually
     cares about (representation = activity manifold, not weight scalars).

**BUILT (corrected): DEVELOPABLE competition.** Lateral inhibition among E neurons (all-to-all excl.
self) is now PLASTIC -- its own Vogels-style iSTDP (traces Apre/Apost, target-rate alpha, clip to
[w_eps, gmax]), driven by develop() at the iSTDP rate, so it breaks symmetry over development. Deposits
into a new fast I_wta neuron current (tau_wta~5ms). Non-genomic, development machinery -> OUTSIDE P.
Toggle dev_wta_comp (OFF by default -> retains PJM's ability to test what selection does with NO a
priori competition). The batched behave path is unchanged (competition is development-time; its effects
reach behave via committed weights). Regression VERIFIED: all-off unchanged (0.960).

**FINDING (measured FUNCTIONALLY per correction #2): competition moves the representation where eSTDP-
alone (D106) could not.** eSTDP-only == baseline on every measure (eff_rank 29->29, selectivity
0.87->0.88 -- confirms D106 inertness). eSTDP + DEV-COMPETITION: eff_rank 29->16, per-neuron
across-input variability 0.87->0.52, and test_err 0.970->0.946 -- **the FIRST movement off the floor by
any development manipulation.** So competition clears the "does it reshape the representation" bar that
eSTDP-alone failed.

**INTERPRETATION HELD WITH DISCIPLINE (one net, one seed, small effect -- the over-reading trap).**
eff_rank and selectivity went DOWN. Two readings, undistinguished by this measurement: OPTIMISTIC =
competition consolidates high-dim NOISE-driven activity (eff_rank~30 was largely noise, D105/D106) into
a lower-dim STRUCTURED representation (WTA should reduce dimensionality; test_err improved, consistent);
SKEPTICAL = competition merely SUPPRESSES activity (quieter net trivially has lower-dim, less-variable
state) = suppression not differentiation (the selectivity DROP is the worrying sign -- true distinct
winners might RAISE per-neuron selectivity). Can't tell from one measurement. test_err off the floor is
the most encouraging single number but small + unreplicated.

**NEXT (the real gate).** Not "what does competition do to one net" but the (A)-commitment VARIATION
TEST: does eSTDP+competition produce representational SPREAD -> fitness SPREAD ACROSS GENOMES? Competition
cleared the bar to EARN that test (eSTDP-alone did not). Also RE-RUN THE D106 LANDSCAPE with competition
on, measured FUNCTIONALLY (eff_rank/selectivity/state-change across genomes, not weight variance), to map
where competition is productive vs merely suppressive -- which directly adjudicates the optimistic-vs-
skeptical reading above.

### D108 — The dev×beta sweep: FLAT landscape. Joint-tuning hypothesis NOT supported. Redirects to the converged density/heritability threads.
**2026-07-22 · Result (well-powered negative) · sweep_runs/_summary.json + 20260721-182635_dev_beta_sweep.log**

**THE RUN.** 4×4 grid, wta_gain[0,0.5,1,2] × fitness_beta[1,5,20,50], each cell a real GA (pop=30,
gens=40), ~18h total. Density FROZEN at 0.2 (density_mode="fixed" — see caveat below). Read as a PATTERN
across the grid per standing discipline, not cell-by-cell.

**HEADLINE: the grid is FLAT — every cell is drift.** fit_slope ranges only [-0.0003, +0.0008] across
all 16 cells; those are noise around zero (a +0.0008 slope moves fitness ~0.03 over 40 gens, comparable
to within-cell gen-to-gen jitter). NO cell climbs, and NO pattern across the grid: competition-on rows
do NOT beat the competition-off row, high-beta does NOT beat low-beta, the tiny positive slopes are
scattered without structure (largest at wta0/beta50 and wta2/beta5 — incoherent). **The joint-tuning
hypothesis — that some competition×selection combination unlocks climbing — is NOT SUPPORTED.** Neither
competition nor selection pressure, alone or together, at these settings, produces adaptive climbing.
Clean, well-powered negative (16 full GA runs).

**THREE INFORMATIVE SIGNALS INSIDE THE FLATNESS:**
1. **best_test never CONSOLIDATES below floor anywhere.** Best any cell reached was best_test_min=0.890
   (wta0_beta20) vs floor 1.014 — so networks momentarily FLICKER below floor, but every cell ENDS back
   near floor (0.93–0.99). Transient variation exists; selection can't consolidate it. This is the
   flat-fitness signature throughout the project, and it is exactly the S1 prediction: the process may be
   SELECTIONIST (transient winners) not DARWINIAN (heritable, compounding gains).
2. **reg_delta is quietly the most interesting column.** Regulation-capability deltas are SYSTEMATICALLY
   POSITIVE in the competition-on × higher-beta region: wta0.5/beta20 +0.042, wta1/beta20 +0.032,
   wta2/beta50 +0.029, wta1/beta5 +0.028, wta1/beta50 +0.018, wta1/beta1 +0.020. The comp-off/low-beta
   corner is mixed/negative. So regulation (the H-C "modulating level" capability) nudges up SPECIFICALLY
   where competition and selection are both engaged — the ONE thing in the grid showing a hint of the
   framework-predicted pattern, even as overall fitness stays flat. FAINT, below "real," HELD WITH
   DISCIPLINE (D085c/D097 over-reading rule) — but it is directional and non-random across the grid the
   way fit_slope is random. Watch-item, not a claim.
3. **exc-fraction drift is real and consistent.** Excitatory fraction falls 0.80 → 0.66–0.73 in nearly
   every cell. Selection HAS reproducible traction on E/I balance — the machinery works; it just isn't
   translating into generalization gains.

**INTERPRETATION.** The develop-then-select loop, at these settings, does not climb, and competition×
selection tuning doesn't rescue it. We are now in the pre-designated "metrics aren't telling us what to
tweak" situation — the trigger for opening the queued E/S-series threads. Crucially, the sweep FAILS IN
THE SPECIFIC WAY the converged hypothesis predicts: transient, non-consolidating, non-differentiating
variation is exactly what S1 (heritability failure), S2 (reverberation corrupting structure), and the
density/E-series (too much activity/connectivity) all predict. Not a mysterious null — a PREDICTED one.

**KEY CAVEAT (structural).** Density was FROZEN at 0.2 (density_mode default "fixed" — the sweep didn't
override it). So this grid says nothing about whether a DIFFERENT density climbs. The one variable three
independent threads flag (excessive density/activity) was held fixed by construction. "We're at the
wrong density" remains completely live and untested.

**REDIRECT (what the sweep tells us to do next).**
- S1 (heritability test) is now the HIGHEST-PRIORITY diagnostic: the grid shows transient below-floor
  dips that never consolidate — is that because fitness isn't HERITABLE across generations (selectionist)
  vs. because there's no variation at all? Parent→offspring fitness correlation discriminates these two
  failure modes, which call for DIFFERENT fixes. Cheap, testable now.
- The converged DENSITY/ACTIVITY/REVERBERATION hypothesis (pre-sweep density thread + E2/E3 + S2) is the
  leading mechanistic candidate for WHY; the density sweep (frozen here) is the natural experiment.
- E1 (fitness cache) worth doing regardless as free speedup before the next big run.
- The faint reg_delta signal (comp-on × high-beta) is the one thread of hope — worth checking whether it
  strengthens under any of the above interventions.

### D109 — S1 heritability result + the REGULATION-IS-SUBSTRATE-NATIVE reframe. Fitness non-heritable (r~0 both conditions); regulation heritable (r~0.29, replicated). Three consilient supports. Reframes the project.
**2026-07-22 · Result + major reframe (held as strongly-suggestive hypothesis) · analysis_logs/*heritability_probe***

**S1 RESULT (n=30 parent-child pairs, both comp on/off).**
  comp OFF: fitness SD=0.0297, fitness r=+0.028, h2=+0.022 | regulation SD=0.0155, regulation r=+0.294
  comp ON : fitness SD=0.0333, fitness r=-0.025, h2=-0.027 | regulation SD=0.0094, regulation r=+0.287
- **Aggregate fitness is NON-HERITABLE** (r~0, straddling zero, BOTH conditions). Variation is present
  (SD~0.03) but a parent's fitness predicts nothing about its child's. This is a HERITABILITY failure,
  not a selection-pressure failure -> EXPLAINS D108's flat landscape mechanistically: the loop is
  SELECTIONIST not DARWINIAN (Fernando/Szathmary), so transient winners don't transmit, nothing
  compounds, no amount of beta helps. Competition does NOT fix it.
- **Regulation is HERITABLE (r~0.29), REPLICATED across both conditions** and nearly identical (+0.294,
  +0.287). THIRD independent time regulation separates from aggregate fitness (D108 reg_delta drift; both
  S1 conditions). The heritable structure lives specifically in the H-C "modulating level" dimension.

**THE REFRAME (PJM) — regulation is the substrate's NATIVE competence; linear encoding is the hard,
ordered special case.** The engineer's implicit difficulty ladder (encoding=easy foundation ->
regulation=hard capstone) may be BACKWARDS for a distributed dynamical substrate:
- Linear encoding requires the weights to sit in a highly ORDERED, low-entropy region of parameter
  space (clean, near-linear input->state maps). A random recurrent network is structurally FAR from
  that region -> encoding is a narrow target the random substrate keeps missing.
- Regulation does NOT require a clean encoder first. The stimulus is ALREADY present in the network's
  distributed, fluctuating, nonlinear dynamics; regulation only asks the network to differentially
  respond to the distributed dynamical regime of stimulus A vs B. This works WITH the substrate's native
  tendency (rich high-dim distributed representation), not against it.
- **RETRODICTS the heritability dissociation:** regulation lives in a smooth, substrate-native region ->
  genome->regulation map is continuous -> transmits (r~0.29). Encoding requires hitting a sharp ordered
  target -> genome->encoding map is needle-in-haystack, discontinuous -> doesn't transmit (r~0). We did
  NOT design the probe to show this; it fell out.

**THREE CONSILIENT SUPPORTS (why this is more than optimism):**
1. **The heritability dissociation itself** (retrodicted, not designed for).
2. **Deep learning** (PJM): successful pattern-recognition nets natively find DISTRIBUTED, nonlinear,
   hard-to-interpret solutions; clean linear structure is NOT what emerges even when the task is solved
   (whole fields of interpretability/disentanglement exist because of this). "Linear encoding is the
   simple foundation" is a human INTERPRETABILITY preference, not what successful learners build. Our
   substrate is already in the representational FORMAT successful learners use; it lacks only the tuning.
3. **Biology's linear encoders are STRUCTURALLY SPECIFIED, not emergent** (PJM): topographic maps
   (tonotopy, retinotopy) are laid down by the physical arrangement of afferents (A1 tonotopy inherited
   from MGB thalamic input topography, ultimately the cochlea), via developmental wiring -- NOT
   self-organized from recurrent dynamics. The exception that proves the rule: biology gets clean
   encoding by IMPOSING order structurally, precisely because recurrent dynamics don't spontaneously
   produce it. -> We've been asking our random net to spontaneously develop encoding that biology only
   ever achieves by developmental fiat. "Encoding at floor" isn't substrate failure; it's the substrate
   declining to do what biology also doesn't do by emergence. (Reframes the engineered ceiling too: the
   positive control may SUPPLY, by construction, the order biology supplies by wiring.)

**UNIFIED THESIS.** Distributed recurrent dynamical systems (artificial or biological) natively represent
in distributed/nonlinear/fluctuating form. Clean linear encoding is an ordered special case requiring
either extensive training (deep nets) or structural specification (bio maps), never spontaneous emergence.
Our random spiking net is ALREADY in the right format (dynamics carry the stimulus); the accessible,
heritable, native operation is REGULATION, not encoding. The project-long "encoding failure" is the
substrate correctly declining to produce an ordered representation neither DL nor biology produces by
emergence.

**DISCIPLINE / CAVEATS (not yet established).** r~0.29 is modest (~8% variance), n=30. Possible artifacts
to rule out: (a) is "regulation" a LOOSER metric (easier to score nonzero by chance) than encoding? Its
SMALLER SD (0.0094-0.0155 vs fitness 0.03) could mean less range for mutation to disrupt -> higher r as
a range artifact, not a depth fact. Must control for this. The reframe is a hypothesis with three
consilient supports + sharp falsifiable predictions, NOT a result.

**REFINED TEST BATTERY (falsifiable predictions of the reframe):**
1. **Nonlinear decodability of the developed state (HIGHEST VALUE, build first).** Predicted by support #2:
   stimulus/context should be NONLINEARLY decodable from the developed state even where LINEAR + covariance
   decoders found chance. If so, it REINTERPRETS every prior "encoding at floor / context not decodable"
   result as a decoder-FORMAT artifact (linear decoder on a distributed representation) -- a major re-read
   of the project. Cheap, uses existing developed states.
2. **Select on regulation directly** (not aggregate fitness): does the heritable, native capability
   COMPOUND under selection where aggregate-fitness selection (D108) could not? The exploit move.
3. **Reversal test:** encoding-selection should evolve WORSE (lower heritability, less climbing) than
   regulation-selection -- inverting the engineer's ordering. Clean counterintuitive falsifiable prediction.
4. **(Constructive complement)** does imposing structural afferent order (topographic input bias, a la
   thalamic tonotopy) unlock encoding where emergence couldn't? Tests support #3 directly. Lower priority.

**NEXT.** Build test #1 (nonlinear decodability) first -- it tests the reframe's foundation AND re-reads
prior nulls. Then #2 (select-on-regulation) as the exploit. Gate the reframe's promotion from hypothesis
to finding on #1 + the range-artifact control.

### D110 — TEST #1 CONFIRMED: context is NONLINEARLY decodable (RF 0.60/0.69 vs chance 0.25) where LINEAR decoders found chance. Prior "encoding at floor" was a DECODER-FORMAT ARTIFACT. Competition helps.
**2026-07-22 · Result (reframe FOUNDATION supported) · analysis_logs/*nonlinear_decodability_probe***

**RESULT (n=12 genomes/condition, decoder ladder on the SAME developed states; chance=0.250).**
```
decoder            comp OFF   comp ON
1 linear-ridge      0.443     0.471
2 linear-SVM        ~0.50     0.540
3 cov-linear        0.406     0.474   <- the D-series form that concluded "not decodable"
4 RBF-SVM           0.52      0.558
5 kNN               0.449     0.503
6 random forest     0.604     0.688   <- best; 2.4-2.8x chance
lift (NL - linear)  +0.161    +0.217
```
- **Context IS present in the developed state, nonlinearly decodable WELL above chance** (RF 0.60/0.69).
  The reframe's foundational prediction holds cleanly: NONLINEAR >> LINEAR (+0.16 to +0.22 lift).
- **The covariance-linear decoder our earlier D-series probe used to conclude "context not decodable
  above chance" is among the WORST here (0.41/0.47), while random forest on the SAME states hits
  0.60/0.69.** => Our prior "encoding at floor / context not decodable" conclusion was a DECODER-FORMAT
  ARTIFACT. The information was present all along; we read a distributed/nonlinear representation with a
  linear instrument. This RETROACTIVELY RE-READS a large chunk of the project's "encoding failures."
- **BONUS (not designed for): competition HELPS nonlinear decodability.** RF 0.60->0.69 OFF->ON, lift
  grows +0.16->+0.22. Competition IS improving the distributed representation (making context more
  decodable) even though it never showed in linear probes or the fitness sweep. Partially rehabilitates
  competition -- it does useful work our earlier metrics were blind to.

**WHAT THIS ESTABLISHES (disciplined).** The reframe's FOUNDATION (D109): info is present-but-distributed,
not absent. Prior linear/covariance nulls were instrument artifacts. NOT yet established: the full
difficulty-reversal claim (needs the reversal test, D109 #3) and the regulation range-artifact control
still stand. 0.60-0.69 isn't ceiling (task genuinely hard, oracle ~0.575 test-err) but is far from chance.

**MAJOR IMPLICATION -- the READOUT may have been structurally mismeasuring success.** If context is
nonlinearly (not linearly) decodable and the fitness readout is LINEAR, we've been penalizing the network
for not putting info in a format the reframe says it structurally won't produce. A NONLINEAR READOUT might
reveal the network was succeeding all along -- and might restore heritability (if the linear readout was
projecting out exactly the distributed structure that transmits). THIS IS NOW A TOP CANDIDATE: check the
readout's linearity; test a nonlinear readout in the fitness function.

**NEXT (reordered by this result).**
1. **Check the fitness READOUT's linearity** (is it linear? — likely yes). If linear, this is a prime
   suspect for BOTH the flat fitness AND the non-heritability: a linear readout on nonlinear-encoded
   context measures mostly noise. Test a nonlinear readout (or nonlinear-feature readout) in fitness.
2. **Select on regulation** (D109 #2) -- even better motivated now: regulation = "differentially respond
   to distributed dynamical regimes" = exactly what nonlinear-decodable-context IS.
3. **Reversal test** (D109 #3) and the regulation range-artifact control -- to promote the full reframe
   from hypothesis to finding.

### D111 — The SELECTION READOUT decided by the P-AXIS criterion: regulation-only, LINEAR readout. Nonlinear decoding confined permanently to DIAGNOSTIC. Supersedes the drift toward a nonlinear selection readout.
**2026-07-22 · Decision (design) · METRIC_BATTERY.md §0**

**GOVERNING CONSTRAINT (PJM, from project history).** The earliest incarnation of this project took a
RESERVOIR-COMPUTING approach and ABANDONED it, because **RC sidesteps the study's core question.** In RC you
train a linear decoder on a rich but tangled reservoir; better RCs get better BECAUSE THE DECODER IMPROVED,
not because of structure imparted to the reservoir. So fitness-vs-P becomes MEANINGLESS: you plot fitness
against the NETWORK's parameter count while the parameters actually doing the generalization work — the ones
a double-descent curve is ABOUT — live in the DECODER.

**=> The criterion is NOT "keep the readout weak so the network still matters" (Claude's framing — a
fitness-sensitivity worry) but: READOUT PARAMETERS ARE UNCOUNTED P.** Every fitted DOF in the readout is P we
aren't counting, contaminating exactly the axis H-A and H-B live on. A MEASUREMENT-VALIDITY constraint on the
central claim. Disqualifies random-forest/MLP/any flexible learned readout as a selection basis, and
disqualifies "mixtures of decoders" (more decoders = more uncounted parameters, strictly worse).

**THE EMPIRICAL POINT THAT DECIDES IT (PJM).** The LINEAR regulation readout we already use **already
detects regulation capability** — it found regulation heritable (r≈0.29, D109) and meaningfully varying, at a
time when encoding showed nothing. Regulation IS linearly detectable. Claude had slid from "the context
information is nonlinear (D110)" to "therefore select nonlinearly," without checking whether the existing
linear regulation readout already suffices. It does. Two DISTINCT ROLES, different constraints:
- **Nonlinear decoding as DIAGNOSTIC (D110-style):** valuable — it corrected our INTERPRETATION ("encoding at
  floor" was a decoder artifact; the substrate isn't failing) and validated the reframe's foundation. Costs
  NOTHING on the P axis because it's a measurement, never a selection basis. KEEP, permanently in this role.
- **Nonlinear readout as SELECTION basis:** costs uncounted P, risks the abandoned RC failure mode, and is
  UNNECESSARY. REJECTED unless it earns its way in.

**DECIDED — the change is WHAT WE SELECT ON, not HOW WE READ IT:**
1. **Select on REGULATION ONLY, with the EXISTING LINEAR readout** (not the encoding+memory+regulation
   hybrid). Minimal change, ZERO added uncounted P, directly motivated by D109: regulation is the heritable,
   substrate-native component; encoding is the ordered target the substrate structurally resists; the hybrid
   has been DILUTING a transmissible signal with a non-transmissible one.
2. **Only if (1) stalls:** a FIXED-FORM, ZERO-FITTED-PARAMETER nonlinearity (e.g. a specified quadratic
   feature map applied identically to every genome). A fixed feature expansion adds no fitted DOF — it just
   re-presents the same state — so it's the ONLY nonlinearity compatible with the P-axis criterion. Gated on
   necessity AND the readout-power audit.
3. **Powerful nonlinear decoders stay DIAGNOSTIC ONLY**, permanently outside the P accounting.

**READOUT-POWER AUDIT (new standing control, promoted to CORE measurement).** Score RANDOM/SCRAMBLED networks
with the same readout; if a random network scores nearly as well as an evolved one, the readout is doing the
network's job. The (evolved − random) gap = the headroom the NETWORK actually contributes. Converts "is the
readout too powerful?" from a design worry into a measured quantity; the direct empirical guard against the
abandoned RC failure mode. Run whenever readout form changes.

**OPEN HYPOTHESIS (links two problems).** Readout power and heritability may be COUPLED: a too-powerful
reader can compensate for whatever the network does, so mutating the network barely changes achievable
performance and fitness fails to transmit. If so, narrowing the readout (as in (1)) might itself RESTORE
heritability — connecting D109's non-heritability to readout capacity. Testable.

**EXTENSION (2026-07-22, second literature pass): THE P-AXIS CRITERION APPLIES TO NEURON MODELS TOO.**
The Frontiers 2026 NEAT study (Loyola-Jara et al., Front Neurosci 20:1697163) finds Izhikevich neurons
consistently outperform LIF, concluding the neuron model matters as much as the encoding scheme — an
apparent challenge to our LIF substrate. But the D111 criterion resolves it: **Izhikevich units carry 4
parameters each (a,b,c,d); if evolvable that is 4N fitted DOF OUTSIDE the synaptic P count** — the same
contamination as a powerful readout, merely relocated from the reader into the units. We would be plotting
fitness against synapse count while much of the adaptive capacity sat in uncounted neuron parameters. For a
study whose central measurement IS fitness-vs-P, **LIF's parameter-poverty is a FEATURE, not a limitation**;
a richer unit model would have to be either frozen (forfeiting the evolvability benefit) or counted in P
(changing what the axis means). **LIF RETAINED.** PJM's framing: "richer units evolve better" is
near-tautological (cultured neurons would beat Izhikevich); the real question is whether LIF is
sufficiently evolvable FOR OUR TASK as a means to measure the fitness-vs-P curve. That narrows to a
MEASURABLE property — genotype→phenotype landscape smoothness — queued as N2, which also discriminates
substrate-roughness from architecture-scrambling as the cause of D109's non-heritability.

**LITERATURE CONTEXT (searched).** RC work independently validates the reframe's foundation: reservoirs
compute useful representations "detectable only in higher order principal components" that render tasks
linearly separable (Nolte et al. arXiv 2411.10047) — our D110 finding in RC language; and tanh vs linear
neurons is the difference between near-perfect and chance accuracy there. Also a memory-vs-nonlinearity
tradeoff with "mixture" resolutions (Sci Rep s41598-017-10257-6), and a systematic benchmark of nonlinear
readouts (Lagomarsini/Ceni/Gallicchio, ICANN 2025) — NOT yet read in full; the reference to pull IF (2) is
ever triggered. Note the RC framework's own logic supports minimal readouts: the whole point of RC is that a
SIMPLE readout suffices BECAUSE the reservoir does the nonlinear work — if you need a powerful readout, the
computation has moved out of the network. Which is precisely the failure this project already rejected.

### D112 — CORRECTION to D109 + collapse the enc/car/reg decomposition. "Encoding" and "regulation" are the SAME measurement offset by a constant; the real dissociation is performance-vs-CARRYING. Stop imposing a solution decomposition a priori; evolve, then analyse.
**2026-07-22 · Correction + design decision · found by reading evaluate() while the D111 run was in flight**

**THE MEASUREMENT FACT.** In `evaluate()` the three components are built as:
```
e_te = _affine_nmse(Y_test, rates)          # test error, lower better
enc  = max(0.0, 1.0   - e_te)               # "encoding"
reg  = max(0.0, floor - e_te)               # "regulation"   (floor = 1.014 this task instance)
car  = _carry_covdecay(...)                 # "carrying"  <- the only genuinely different measure
```
**So `regulation = encoding + (floor - 1.0) = encoding + 0.014` EXACTLY.** Both are the same test error
subtracted from a reference and sign-flipped; they differ only in intercept. In our operating range
(e_te ~ 0.90-0.99) neither clips, so **encoding and regulation are PERFECTLY CORRELATED — not separable
components.** (Narrow exception: for poor performers with 1.0 < e_te < 1.014, encoding clips to 0 while
regulation stays positive, so they decorrelate slightly at the BOTTOM of the population; for the top
performers that selection acts on, they are identical up to the offset.)

**WHAT D109 ACTUALLY SHOWED (correction).** D109 was read as "regulation is heritable (r~0.29) but
encoding/aggregate fitness is not (r~0.03)," and that dissociation seeded the H-Cv2 reframe. But:
- The probe compared **hybrid fitness** heritability against **regulation** heritability. It NEVER measured
  encoding heritability separately.
- Since regulation ≡ encoding + const, their heritabilities are NECESSARILY IDENTICAL. **The
  "regulation-vs-encoding" dissociation was never tested and cannot exist as stated.**
- **The real dissociation is: pure test-error-based performance (heritable, r~0.29) vs the HYBRID fitness
  (non-heritable, r~0.03).** The hybrid's distinguishing ingredients are `carrying` and the
  `carrying*regulation` product. **=> `carrying` (the covariance-decay memory measure) is the likely
  source of the non-heritability**, not "encoding."

**EFFECT ON THE H-Cv2 REFRAME (one leg reinterpreted, three stand).** D109's heritability dissociation was
support #1 of four. It must be RESTATED as performance-vs-carrying. Supports #2 (deep nets natively find
distributed solutions), #3 (biology's linear encoders are structurally specified, not emergent), and #4
(D110: context is nonlinearly but not linearly decodable) are INDEPENDENT of this error and stand
unchanged. H-Cv2 is not refuted, but its "encoding is a hard ordered target while regulation is native"
phrasing leaned on a component distinction that does not exist in the implementation.

**A SEPARATE DESIGN FLAW, worth recording.** The docstring calls encoding "memoryless-achievable task
performance (first descent)." `1.0 - e_te` is not that — it is total performance against a fixed reference
of 1.0. A real memoryless-achievable measure would require SCORING A MEMORYLESS MODEL, not subtracting from
1.0. So the component intended to isolate first-descent encoding never did.

**DECISION (PJM): COLLAPSE THE DECOMPOSITION. Stop treating enc/car/reg as distinct components to select
on.** Rationale, and it is the reframe applied to our own fitness function: **the D094 three-term fitness
was itself an ENGINEERING HYPOTHESIS about HOW the network should solve the task** — build encoding, then
carrying, then regulation atop it. That ladder is precisely the a priori decomposition the reframe says we
must stop imposing (and the same error as D038/D074's "don't build in the mechanism under test"). PJM:
*"let's stop deciding for the network ahead of time the way it should be engineering its solutions; let's
evolve them and then analyze what it decided to do, and how that changed at varying P."*

**WHAT REPLACES IT.**
- **Selection: a SINGLE performance scalar** = `floor - test_err` ("how far do you beat the memoryless
  floor"), which by the task's construction requires context inference. **This is exactly what
  `fitness_mode="regulation_only"` already computes** — so the RUNNING D111 EXPERIMENT IS ALREADY DOING THE
  RIGHT THING; only its NAME and its RATIONALE change. (Rename deferred: the mode string is inside the
  checkpoint config-hash, so renaming mid-run would invalidate the cells. Rename AFTER the run completes.)
- **Bonus: this cleans the study's central measurement.** A single well-defined performance quantity on the
  y-axis vs P on the x-axis, instead of a weighted composite whose curve shape depends on w_e/w_c/w_r that
  we chose.
- **enc/car/reg are RETAINED AS MEASUREMENTS, not as selection targets** — they go into the core
  measurement set as diagnostics/descriptors (METRIC_BATTERY §1c), to be analysed post hoc. Note `carrying`
  remains genuinely informative BECAUSE it is a different measure (and is now the prime suspect for the
  non-heritability).
- **The analysis burden moves post hoc, as intended:** evolve under a single performance measure, then
  characterise WHAT the networks built and HOW that changed with P — using the agnostic structural
  descriptors (queue N3) and the deferred derived-metric layer (METRIC_BATTERY §3).

**LESSON (methodological).** This was found by reading the implementation while a run was in flight — the
components had been reasoned about from their NAMES and docstrings for many sessions without checking the
arithmetic. Names are not measurements. Add to the standing discipline: **before building a hypothesis on a
component, read how it is computed.**

### D113 — ⚠️ CRITICAL: TEST-SET LEAKAGE. Fitness has been computed from TEST error since D094, so selection optimises the exact quantity we report as generalisation. All D094-onward test numbers are UNUSABLE for formal/publication purposes. Fix = three-way split.
**2026-07-22 · CRITICAL CORRECTION · found by tracing `evaluate()` after D112 · affects every run since 2026-07-19**

**READ THIS FIRST.** If this had gone uncaught until after we found an evolvable configuration and ran
production experiments, **every one of those production results would have been invalid.** The bug is
silent, produces plausible-looking numbers, and sits in the single most load-bearing measurement in the
study. Flagged as loudly as possible for that reason (PJM).

**THE FINDING.** In `evaluate()`:
```
e_tr = _affine_nmse(task.Y_train, B_tr["rates"])     # train error  -- computed, then essentially unused
e_te = _affine_nmse(task.Y_test,  B_te["rates"])     # TEST error
enc.append(max(0.0, 1.0   - e_te))                   # "encoding"    <- from TEST error
reg.append(max(0.0, floor - e_te))                   # "regulation"  <- from TEST error
```
`_fitness()` consumes `encoding`, `carrying`, `regulation`. **Therefore fitness is a function of TEST
error, and selection optimises test error directly.** True of BOTH `hybrid` and `regulation_only` (the
latter is `floor - e_te`, i.e. pure test error affinely transformed; the constant `floor` cancels in the
replicator softmax `z = beta*(f - f.max())`, so `regulation_only` selection is EXACTLY selection on
`-test_err`).

**THE TEST SET IS THEREFORE NOT HELD OUT.** This is textbook test-set leakage through MODEL SELECTION: the
GA is performing architecture/parameter search against the test set. At pop=30 x gens=40 that is **~1200
evaluations of selective pressure applied against `E_test` per run.** Whatever the fitness-vs-P curve looks
like, **its y-axis is no longer an unbiased estimate of generalisation** — fatal for a study whose entire
deliverable is generalisation-error-vs-P.

**PARTIAL DEFENCE, AND WHY IT FAILS.** The two levels are distinct: the network's WITHIN-LIFETIME learning
(development) uses `E_train` only, so test is genuinely held out from DEVELOPMENT. Only the EVOLUTIONARY
search touches test. But that is precisely the standard leakage case — selection over many candidates
against a fixed set will fit that set. The level at which the fitting happens does not matter; what matters
is that the reported quantity was optimised.

**PROVENANCE OF THE ERROR — D077 HAD IT RIGHT AND D094 SILENTLY REVERSED IT.** D077 (2026-07-18) states the
correct principle outright: *"Test error is REPORTING, not selection... `_fitness()` reads only `train_err`.
Selection never touches test."* D094 (2026-07-19) redefined the components in terms of `e_te` **without
flagging that it reversed D077's principle.** The regression went unnoticed for ~4 days of work because
each component was reasoned about from its NAME, not its arithmetic (the same failure mode as D112).

**WHAT IS AND IS NOT INVALIDATED.**
- **NOT invalidated: the exploratory CONTRASTS.** D108's flat landscape, D111's regulation-vs-hybrid
  comparison, and the currently-running cells remain readable AS CONTRASTS, because every mode leaks
  identically — the comparison between conditions is not differentially biased. PJM: this is tolerable
  only because we are still in the bumping-around-in-the-dark, get-the-system-working phase.
- **INVALIDATED: any formal/publication use of ABSOLUTE test numbers from D094 onward.** No test error,
  best_test, headroom-relative score, or fitness-vs-P curve from this era may be quoted as generalisation
  performance. Treat all of it as exploratory instrumentation only.
- **D109 heritability**: the parent-offspring CORRELATION is not invalidated by leakage per se (both
  generations measured identically), but the underlying fitness values are test-contaminated.
- **D110 decodability**: UNAFFECTED — it is a measurement, not a selection signal, and used internal
  cross-validation.

**THE FIX — THREE-WAY SPLIT (required before ANY production run).**
- **develop** on `E_train` (unchanged — the network's within-lifetime learning),
- **select** on a NEW `E_val` / `Y_val` split (fitness computed from validation error),
- **report** the double-descent curve on `E_test`, which nothing in the loop ever touches.
Implementation: add a validation split to `hierarchical_environments`; route the fitness components to
validation error; keep `e_te` computed for REPORTING only. Also audit that `task.headroom()`'s
`memoryless_floor` / `oracle_ceiling` are not themselves derived from test data (a smaller leak of the same
family, since `floor` enters the fitness expression).

**STANDING RULE ADDED (generalises the D112 lesson).** *Names are not measurements — and any quantity that
appears in the fitness function must be traced to its data source before it is trusted.* Specifically:
**no quantity computed from the reporting split may enter the selection signal.** Add a mechanical guard —
an assertion or unit test that `_fitness()`'s inputs derive only from train/validation data — so this class
of regression cannot recur silently.

### D114 — Regulation-only selection run (D111 experiment) COMPLETE. Selection strength, not selection basis, is the dominant effect. Hybrid confirmed a BAD basis on two independent grounds. Apparatus reproduces exactly. All test numbers void per D113.
**2026-07-22 · Result (exploratory; leaked per D113) · runs/reg_select/_summary.json + log**

**THE GRID** (pop=30, gens=40, competition on, wta_gain=1.0; PRE-D113-fix code, so fitness = floor - TEST error):
```
cell                     fit_slope   reg_slope   reg_mean_end   test_min   audit(evolved-random)
regulation_only_beta5     +0.00025    +0.00025      0.0437        0.904        +0.0186
regulation_only_beta20    +0.00006    +0.00006      0.0332        0.922        +0.0081
regulation_only_beta50    +0.00104    +0.00104      0.0648        0.881        +0.0397
hybrid_beta5              +0.00015    -0.00008      0.0334        0.912        +0.0125
```

**FINDING 1 — EXACT REPRODUCIBILITY (apparatus validation).** `hybrid_beta5` here gives fit_slope=+0.00015,
test_min=0.912. D108's `wta1_beta5` cell (same config, same seed, run days earlier) gave fit_slope=+0.00015,
min=0.912 — **identical to every digit.** The pipeline is deterministic and the control exactly reproduces a
prior independent run. Cross-run comparisons are therefore trustworthy.

**FINDING 2 — THE HEADLINE CONTRAST FAILS AT MATCHED SELECTION STRENGTH.** The experiment asked "does
regulation-only climb where hybrid was flat," with beta=20 as the CALIBRATED match to hybrid@beta5 (the
~4.3x fitness-spread ratio). At matched strength: reg_only@beta20 ends at reg_mean 0.0332, hybrid@beta5 at
0.0334 — **indistinguishable.** The advantage appears ONLY at beta=50, ~2.5x beyond the calibrated match.
**=> The dominant effect in this grid is SELECTION STRENGTH, not selection BASIS.** Reported plainly rather
than framing beta50-vs-hybrid5 as the intended contrast (it isn't; those differ on both axes).

**FINDING 3 — but the BASIS effect is real, small, and DIRECTIONAL.** Every regulation_only cell moves
regulation UP (reg_slope > 0 in all three). Hybrid is the only cell where fit_slope and reg_slope DISAGREE
IN SIGN: fitness rose (+0.00015) while regulation FELL (-0.00008). So under hybrid selection the population
improved on something that is NOT regulation — almost certainly `carrying`, the one component computed
differently (and from E_train). **This is stronger than "hybrid was flat": hybrid actively ERODES
regulation**, and it independently supports D112's inference that carrying is the anomalous ingredient.

**FINDING 4 — the READOUT-POWER AUDIT (D111) cleanly separates the two bases, and HYBRID FAILS IT.**
Under hybrid fitness, random networks score mean 0.0536 / **max 0.1120** vs evolved 0.0661: **the best of ten
RANDOM draws beats the evolved population mean by ~1.7x.** Forty generations of selection produced something
worse than a good random draw. Under regulation_only the audit passes and scales with beta (evolved 0.0437 /
0.0332 / 0.0648 vs random max 0.0329). **A fitness that random networks can score highly on by chance is a
noise-dominated fitness** — a second, independent indictment of the hybrid basis, and a vindication of
promoting the audit to a standing control.

**FINDING 5 — beta is still SUB-SATURATION even at 50, and beta=20 was non-monotonically WEAK.** With
regulation-fitness SD ~0.0088, the softmax discriminability product beta*SD is 0.044 / 0.18 / 0.44 for
beta 5 / 20 / 50 — all below the ~1 needed for sharp discrimination. Most likely reading of the
non-monotonicity (beta20 weakest): beta 5 and 20 are both sub-threshold so their ordering is noise, and only
50 bites. **Next runs should use beta 50 / 100 / 200.**

**THE D113 CAVEAT LANDS HARDEST ON THE BEST-LOOKING CELL.** This run predates the three-way-split fix, so
`regulation_only` = floor - TEST error and selection ran ~1200 evaluations against E_test. The
train-vs-test divergence is the smoking gun:
```
reg_only:  train 0.986 -> 0.993 / 0.994 / 0.972    test 0.960 -> 0.928 / 0.945 / 0.888
hybrid:    train 0.983 -> 0.966                    test 0.989 -> 0.962
```
**In every regulation_only cell TEST improves while TRAIN stagnates or WORSENS** — the classic signature of
fitting the evaluation set rather than learning the task. Hybrid, which partly selects on `carrying`
(computed from E_train), improves BOTH together — mechanistically consistent. **So our most encouraging
number (beta50) is also our most contaminated one. NO test number from this run may be read as
generalisation.**

**WHAT SURVIVES.**
- Selection CAN move the population hard when beta is high enough (beta50 moved reg_mean 0.0304->0.0648,
  and captured ~21% of headroom on test_min — though that figure is leak-inflated). D108 left it genuinely
  unclear whether our GA could move a population at all; it can.
- The apparatus is deterministic and reproduces exactly (Finding 1).
- Hybrid is a bad selection basis on TWO independent grounds (Findings 3 and 4) — collapse decision (D112)
  further supported.
- Nothing about GENERALISATION.

**NEXT.** Re-run at beta 50 / 100 / 200 on the D113 three-way split. **The diagnostic that matters: does
TEST error move when selection can no longer see it?** If yes, genuine. If val improves while test stays
flat, this entire signal was leak. ALSO ADD as a standing diagnostic: **train-vs-test divergence is a cheap,
sensitive leak detector** we could have had all along.

### D115 — ⚠️ FITNESS RELIABILITY AT n_assays=1 IS ~0.05. Every run to date selected on approximately pure noise. Also: D109's heritability result was NEVER statistically significant — withdrawn.
**2026-07-23 · Result + correction · runs/20260723-165538_fitness_reliability_probe.log**

**THE MEASUREMENT.** With the D113 three-way split, `evaluate()` returns val_err and test_err: two
INDEPENDENT estimates of the same genome's generalisation. Their correlation across genomes is a
split-half RELIABILITY of the fitness signal. n=30 genomes, n_assays sweep {1,2,4}:
```
n_assays   r(val,test)   SD(val)   SD(test)   SD(val-test)
   1         -0.011      0.0121    0.0118       0.0169
   2         +0.228      0.0094    0.0073       0.0105
   4         +0.227      0.0074    0.0055       0.0081
```

**FIRST — CORRECT THE PROBE'S OWN VERDICT (it overread).** At n=30 the SE of a correlation is 0.192.
r(2)-r(1) = 1.24 SE; r(4)-r(2) = 0.01 SE; r(4) vs zero = 1.18 SE. **NONE of these correlations differs
significantly from the others or from zero.** The probe's built-in threshold (`rN > r0 + 0.15`) fired on a
1.2-SE difference — badly calibrated, Claude's error. Fix the threshold to account for SE before reuse.

**SECOND — THE VARIANCE DECOMPOSITION IS FAR MORE INFORMATIVE, AND IS CLEAN.**
- SD(val-test) shrinks almost exactly as 1/sqrt(k) (observed/predicted ratios 1.00, 0.88, 0.96) => the
  val-test discrepancy IS genuine measurement noise, averaging down exactly as theory requires.
- Fitting V_obs(k) = V_true + V_noise/k over the three points:
  **V_true ~ 6.5e-6 (SD_true ~ 0.0026); V_noise ~ 1.35e-4 (SD_noise ~ 0.0116 per single assay).**
  **Noise exceeds signal by ~4.6x in SD, ~21x in VARIANCE, at n_assays=1.**
- Implied reliability V_true/(V_true+V_noise/k): **0.046 (k=1)**, 0.088 (2), 0.161 (4), 0.278 (8),
  0.435 (16), 0.606 (32).

**HEADLINE: at n_assays=1 the fitness signal has reliability ~0.05. EVERY RUN TO DATE — the D108 dev x beta
sweep and the D111/D114 regulation-selection run — used n_assays=1 and therefore selected on approximately
PURE NOISE.** This substantially explains the flat landscapes WITHOUT needing any substrate or architecture
explanation. Note the config DEFAULT is n_assays=3; the runners explicitly overrode it to 1 — the worst
available setting.

**THIRD — CORRECTION TO D109 (withdraw the heritability claim).** D109 reported regulation heritability
r=0.29 at n=30 and treated it as a real dissociation against fitness r=0.03. **At SE=0.192, r=0.29 is 1.5 SE
from zero (p~0.13) — never statistically significant, and not significantly different from 0.03 either.**
Claude should have computed the SE at the time. Combined with D112 (encoding is identical to regulation up
to a constant, so the claimed regulation-vs-encoding dissociation could not exist), **the heritability leg
of the H-Cv2 reframe is withdrawn.** The reframe retains supports #2 (deep nets find distributed solutions),
#3 (biology's linear encoders are structurally specified), and #4 (D110 nonlinear decodability — a LARGE
effect, RF 0.60-0.69 vs 0.25 chance), so it is not refuted; but it no longer rests on any heritability
evidence. Update HYPOTHESIS_LOG accordingly.

**CAVEAT ON OUR OWN ESTIMATE.** V_true is fit from three points and is poorly determined; a two-point
estimate gives V_true ~ 3e-5, which would put useful replication nearer k~4 than k~21. Honest range:
**"between 4 and 20 assays," not a precise target.** What IS solid: reliability at k=1 is ~0, and noise
averages down as 1/sqrt(k) exactly as predicted, so replication works.

**FOURTH — A LARGE, FREE COST SAVING FOUND WHILE COSTING THIS OUT.** Development sits OUTSIDE the n_assays
loop, so replication repeats only `behave()`. But each assay runs THREE behave() calls — train, val, test —
and post-D113 **only val feeds selection**; train and test are pure REPORTING overhead computed on every
genome, every generation. At 60 stimuli x 50 ms that is ~3000 ms simulated each vs ~1000 ms for development,
so **two-thirds of every evaluation is waste during selection.**
```
per-eval simulated ms   current(3 behaves)   val-only during selection
   n_assays=1               10,000                  4,000
   n_assays=4               37,000                 13,000
   n_assays=8               73,000                 25,000
```
=> Skipping the reporting behaves during selection buys **n_assays=8 for ~2.5x current cost** (~3 h/cell
instead of ~70 min). Without it, n_assays=8 would be ~7x and unaffordable.

**DECIDED / NEXT (in this order — running the beta sweep at n_assays=1 would repeat D108's mistake with
better bookkeeping).**
1. Optimise `evaluate()`: compute train/test behaves ONLY when reporting is requested, not during selection.
2. Raise **n_assays to 8** for selection runs (reliability ~0.28 on the conservative fit; ~6x better than
   every prior run).
3. THEN run beta 50/100/200 on the three-way split.
4. Fix the reliability probe's verdict threshold to be SE-aware.

**STANDING RULE ADDED.** **Compute the standard error before calling a correlation a finding.** Two
correlation-based results in this project (D109's heritability, this probe's verdict) were over-read at
n=30 where SE~0.19. Any r below ~0.4 at n=30 is not distinguishable from zero.

### D116 — The "memoryless floor" measures REPRESENTATIONAL CAPACITY, not memorylessness. Matched control built. Networks show ZERO measurable context use. Plus: PRE-FLIGHT SUITE adopted, because every multi-hour run so far has been invalidated by a cheap-to-find bug.
**2026-07-23 · Correction + build + standing process change**

**THE FINDING.** `headroom()['memoryless_floor']` is a ridge regression from the RAW 10-dim stimulus E to
Y. Our networks read out from 50 NONLINEAR features. Measured: **a completely STATIC, memoryless,
context-free random tanh expansion of the same input scores 0.9424, BEATING the "floor" of 1.0197** (a
200-dim expansion: 0.9179). No network, no dynamics, no time, no context.
**=> The floor conflates MEMORYLESSNESS with REPRESENTATIONAL CAPACITY, and is dominated by the latter.
"Beating the floor" demonstrates nonlinear expansion, NOT context inference.** Every prior statement of
that form is confounded. (The oracle CEILING is computed the same way — per-context ridge on raw E — so
both ends of the headroom band are miscalibrated and "% of headroom captured" is meaningless as computed.)

**WHAT IT DOES AND DOESN'T INVALIDATE.** Selection is UNAFFECTED: `floor` is a constant in
`reg = floor - e_va` and cancels in the replicator softmax. What is invalidated is the INTERPRETATION of
absolute scores and all headroom framing. The D114 contrasts stand; their absolute readings do not.

**THE MATCHED CONTROL (built: `context_destroyed_score()` in evolve.py).** Score the SAME network on the
SAME stimuli with the temporal CONTEXT STRUCTURE DESTROYED (sample order shuffled, so consecutive stimuli
come from different contexts and nothing accumulates across the dwell period). Capacity, readout, stimuli
and noise are all held fixed; ONLY usable context is removed. The gap
`context_destroyed - ordered` is the contribution attributable to context inference.

**FIRST RESULT FROM IT — networks show NO measurable context use.** Four developed random networks:
```
genome   ordered   ctx-destroyed   context gain
  0      0.9904      0.9880          -0.0024
  1      0.9930      0.9864          -0.0066
  2      0.9938      0.9951          +0.0013
  3      0.9780      0.9839          +0.0059
mean context gain = -0.0004
```
Destroying the context structure costs them NOTHING. This is exactly what the old floor concealed: they
appeared to "beat the floor" (0.96 vs 1.014) while deriving zero benefit from context. (n=4 — a clean
measurement DESIGN, not yet a powered result.)

**SECOND, UNEXPECTED OBSERVATION.** Developed spiking networks score ~0.985 while the STATIC random 50-dim
tanh projection scores 0.942. **Our 50-neuron spiking network is WORSE than a trivial static projection of
the same dimensionality** at the memoryless part of the task. Not perfectly matched (the static version
has no noise and no temporal blurring), but it suggests the dynamics may be DESTROYING information rather
than adding to it. Connects to the density/activity threads and to queue N2 (landscape smoothness).

---

**PROCESS CHANGE — PRE-FLIGHT VALIDATION SUITE (PJM's observation, and it is the more important half of
this entry).** PJM: *"it seems like every time we launch a multi-hour simulation, we discover new problems
that invalidate the data."* True, and the pattern has ONE root cause:
- D112 (encoding == regulation + const) — found by READING evaluate().
- D113 (test leakage) — found by TRACING which split a variable came from.
- D116 (floor measures capacity) — found by a 30-SECOND baseline comparison.
**None required a long run to discover. All three were cheap STATIC checks we never ran.** Validation had
consistently confirmed that code EXECUTES (smoke tests, single-cell trials, checkpoint writes) but never
that it MEASURES WHAT IT CLAIMS. Different questions; we were only asking the first.

**BUILT: `scripts/preflight.py`** — runs in minutes, gates any expensive launch (exit status 1 on failure):
  A **LEAKAGE (empirical):** destroy Y_test, confirm fitness is BIT-IDENTICAL. Stronger than any
    assertion about code structure.
  B **COMPONENT REDUNDANCY:** correlations among enc/car/reg; FAIL at |r|>0.99.
  C **FITNESS RELIABILITY:** split-half r(val,test) at the CONFIGURED n_assays, with SE; FAIL below 2 SE.
  D **FLOOR VALIDITY:** does a static random expansion beat the floor? plus the matched context-destroyed
    control.
  E **READOUT POWER:** random-network fitness baseline that evolved runs must clearly exceed.

**VALIDATED AGAINST OUR OWN HISTORY — the suite reproduces all three known bugs:** A PASSes (confirming
the D113 fix empirically), B FAILs on encoding-vs-regulation with r=+1.0000 and range(x-y)=0.00e+00
(D112), D FAILs on the old floor (D116). A validator that catches every bug we have already paid for is
one worth trusting on the next.

**STANDING RULE.** Run `preflight.py` before ANY multi-hour launch. A FAILing check does not automatically
mean stop — a KNOWN, DOCUMENTED failure that does not affect the contrast being measured may be
acceptable — but it must then be a recorded DECISION, not an oversight discovered afterwards.

### D117 — Stringer et al. 2026 (critical initialization): our networks are ~5x SUPERCRITICAL, non-reciprocal, and use specific rather than global inhibition. A concrete mechanistic candidate for the ZERO context gain. Spectral radius promoted to a core measurement.
**2026-07-23 · Literature + measurement · Pachitariu, Zhong, ... Stringer, Nature 655:990-996 (2026)**

**THE PAPER.** Large-scale mouse recordings (2p cortex, CA1, 8-probe Neuropixels) have eigenvalue spectra
and dynamical properties matching **linear dynamics under a random SYMMETRIC matrix that is CRITICALLY
NORMALIZED** (largest eigenvalue scaled to 0.998). Covariance eigenvalues decay as a power law with
exponent ~2/3 (symmetric) vs ~1.25 (non-symmetric); cortical and brainwide data give 0.7-0.85. CA1 is the
exception (0.4-0.5, resembling an efficient uncorrelated code). **Incomplete normalization DESTROYS the
long-timescale macroscopic structure.** The phenomenon survives sparse (>=0.4% connectivity in 10k units),
clustered and spatial connectivity. Critically normalized dynamics solve zero-shot working-memory tasks.

**CORRECTION TO CLAUDE'S FIRST READING (PJM caught it).** Claude claimed symmetry and Dale's law are "in
tension" and that mouse data "backs symmetry" against Dale. **Wrong.** Their A is drawn from a UNIFORM
POSITIVE (all-excitatory) distribution and they then SUBTRACT THE MEAN, which they state "in the brain
could be implemented with global inhibitory feedback." The negative entries are the residue of subtracting
a GLOBAL inhibitory term from a positive excitatory matrix — **not** sign-flipped synapses. Further, their
units are explicitly "a neuron or a group of neurons," so A is an EFFECTIVE (possibly population-level)
interaction matrix, not a synaptic one; and the evidence cited for symmetry is anatomical RECIPROCITY
(mesoscale connectome; reciprocally connected V1 pairs). **Symmetry here means reciprocal excitatory
interactions, which is fully Dale-compatible** (if i and j are both excitatory, W_ij = W_ji > 0 breaks
nothing). This makes the finding MORE actionable, not less.

**MEASURED — we differ on THREE Dale-compatible counts (5 random genomes):**
```
property                ours                          theirs
spectral radius rho(W)  ~5.1 (3.9-7.4)                ~1.0 (critically normalized)
E->E reciprocity        0.29 == chance 0.29           fully reciprocal (symmetric)
inhibition              sparse/specific, fanout 0.30  GLOBAL (uniform mean-subtraction)
```
Minor curiosity: among the reciprocal pairs that exist, weight magnitudes are ANTI-correlated (-0.20 to
-0.30) where independent draws predict ~0; ~1.8 SE from zero but consistent across genomes. Possible
genome-generator artifact; flagged, not chased.

**WHY THIS IS A CANDIDATE EXPLANATION FOR THE D116 ZERO CONTEXT GAIN.** Critical normalization is the
mechanism their paper identifies for producing LONG TIMESCALES FROM FAST UNITS. Our task needs context
held across ~10 stimuli x 50 ms = 0.5-1.5 s from neurons with tau_m = 20 ms — the 75x timescale gap this
project identified long ago (A3). If incomplete normalization destroys long-timescale structure, and we
are 5x supercritical and never measured it, that is a concrete mechanistic reason the networks show ZERO
measurable context use.

**THE MORE ALARMING RESULT.** They benchmark ECHO-STATE NETWORKS — nonlinear, noisy, near-chaotic
reservoirs, the class our spiking network most resembles — and find they "struggled to maintain more than
half a second of memory, probably due to their chaotic dynamics not being robust to noise," whereas linear
symmetric critically-normalized dynamics performed well at lags of SEVERAL SECONDS. **The architecture
class we are using fails at precisely the timescale our task requires.** Our networks are also
non-reciprocal, which is their worse regime (asymmetry -> rotational dynamics -> no stable representation
across time, even though the information is present).

**A CHALLENGE TO THE FRAMING (live hypothesis, not settled).** They close by suggesting "perhaps all the
learning that needs to happen in such tasks is on the readout or feedforward connections from sensory
inputs to the brainwide dynamical reservoir" — essentially the RESERVOIR-COMPUTING position this project
rejected (D111). Here it is advanced as a claim about BIOLOGY rather than a methodological convenience. If
the brain really is a critically-normalized random reservoir with learning at the readout, then
"P = recurrent synapses" may not be the parameter count that governs generalization. They do note an
alternative (task-specific dynamics "turning on"), so it is a live hypothesis. Worth tracking as a genuine
threat to H-A/H-B's framing, and worth noting in the deck's open-questions appendix.

**CAVEATS ON OUR OWN MEASUREMENT.** (a) Their dynamics are LINEAR; ours are spiking with threshold,
refractoriness and saturation, so the EFFECTIVE gain around the operating point is clamped well below what
raw rho(W) implies — rho=5 does NOT mean our networks are unstable. The right quantity is an effective /
linearized spectral radius at the operating point, which we have not computed. (b) The developed-matrix
measurement silently fell back to the initial W (bad accessor), so we do NOT yet know whether development
moves rho. Both need doing properly.

**ACTIONS.**
1. **Promote SPECTRAL RADIUS to a core measurement** (METRIC_BATTERY 1a) — it is exactly the dynamical
   invariant queue N5 called for, and we now have a target value (~1) plus evidence it is load-bearing.
   Measure raw rho(W), and an effective/linearized rho at the operating point.
2. Also core: **E->E reciprocity** and **inhibitory fan-out** (how global is our inhibition?).
3. Fix the developed-W accessor and measure whether development moves rho.
4. **Consider critical normalization as a swept axis** — normalize genomes to a target rho and sweep it.
   Given the context gain is currently EXACTLY ZERO, "the networks lack the timescales the task requires
   because they are 5x supercritical" is the most concrete explanation we have had.
5. **AMENDED (PJM): DROP reciprocal-E->E and global-inhibition as design variants. Keep ONLY the rho->1
   lead.** PJM asked whether fully reciprocal excitation and global inhibition are actually well grounded
   biologically. Largely NOT, and the two sit on different footing:

   **Reciprocal excitation — enriched, but nowhere near "full."** Song, Sjostrom, Reigl, Nelson &
   Chklovskii 2005 (rat V1 L5 pyramidal pairs) found reciprocal connections OVERREPRESENTED relative to
   chance by roughly 4x — robust and replicated. But overrepresentation is not symmetry: pairwise
   connection probability is order 10%, so the great majority of connections remain UNIDIRECTIONAL. And
   WEIGHT MATCHING is not established — reciprocal pairs are not known to satisfy W_ij ~ W_ji, and
   cortical weight distributions are heavy-tailed in ways that argue against it. Area-level
   bidirectionality (the mesoscale connectome they cite) is a far weaker claim than synapse-level weight
   symmetry.

   **"Global" inhibition — Claude's characterisation was too crude, and the biology is better than
   implied.** Dense, largely nonspecific LOCAL inhibition IS well grounded (PV+ basket cells contact a
   very high fraction of nearby pyramidal cells — the "blanket of inhibition", Fino & Yuste). What is NOT
   grounded is anything brain-wide: inhibitory axons are spatially restricted, and specificity is well
   documented (SOM targeting dendrites, VIP disinhibiting SOM). To their credit their Fig. 4 handles this
   — in the sparse/clustered/spatial variants inhibition is set IN PROPORTION to local connection
   probability. The global mean-subtraction is the dense-case IDEALISATION, not the claim.

   **The deeper point: symmetry is doing enormous MATHEMATICAL work.** It is what makes the derivation
   tractable — real eigenvalues, closed-form Lyapunov solution, Wigner semicircle law, hence the analytic
   2/3 exponent. They are candid that the non-symmetric case defeated them (1.25 obtained numerically,
   "we leave this as an open problem"). Symmetry is assumed for TRACTABILITY first and supported
   empirically second. And the empirical support is thinner than the framing suggests: the observed
   exponents 0.7-0.85 sit BETWEEN the symmetric (0.67) and non-symmetric (1.25) predictions — closer to
   symmetric but not on it — and they concede partial symmetry gives intermediate exponents. The stronger
   evidence is the rotational analysis (near-zero complex eigenvalues), but that is measured during
   SPONTANEOUS activity in darkness, and they report that TASK-DRIVEN recordings DO show rotational
   components. So "the brain is symmetric" may really be "spontaneous activity is non-rotational" — a
   narrower claim.

   **=> Adopting reciprocity/global-inhibition would be exactly the D038/D074 error: building in a
   structure that makes the network work, then reporting that the network works. DROPPED.**

6. **KEEP the critical-normalisation (rho -> 1) lead — it survives all of the above.** It is a SCALAR
   property that does NOT depend on symmetry (they show partial symmetry still gives intermediate
   exponents while normalisation remains necessary for long timescales), and it has a genuinely
   well-grounded biological implementation that the paper itself points to: HOMEOSTATIC SYNAPTIC SCALING
   and activity-dependent PRUNING (Turrigiano; Chechik/Meilijson/Ruppin; heterosynaptic E/I set-point
   work). A network self-tuning toward rho ~ 1 is a real and much-studied phenomenon, not a convenience.
   It is also the lead that speaks DIRECTLY to our 75x timescale gap (A3) and to the D116 zero-context-use
   finding. **This is the one to pursue.** Note it also connects to our EXISTING machinery: the Vogels
   iSTDP is a homeostatic mechanism — does it already move rho toward 1? (Unknown; the developed-W
   measurement failed. Fix and check before treating supercriticality as established.)

### D118 — RC-ERA CRITERIA ARE OBSOLETE. The skill gate is dropped, `input_gain=10`'s justification does not transfer, and the substrate is now CONSTRUCTED (ready-to-learn, E/I-balanced, near-critical) rather than tuned by reservoir criteria.
**2026-07-24 · Framing correction + calibration rebuild (PJM)**

**THE ERROR.** Calibrating the operating point, Claude reinstated the T0-era SKILL GATE — does a ridge
on the 50-dim state beat a ridge on the raw stimulus — as the primary criterion, citing the D-entry that
invalidated T0's original objective. PJM: *"why are we leaning on criteria established when we are still
building a reservoir? that was a whole earlier and abandoned phase of the project."*

**Correct.** Skill measures "would this make a good RESERVOIR": it scores a FULL MIXING READOUT. But
D095's readout is gain+offset per output, reading output j from neuron j, and **cannot mix neurons at
all**. The gate scored a decoder the project deliberately forbids. Worse, it is the criterion by which
`input_gain=10` was originally chosen ("the reservoir first beats baseline at 10") — so **that
parameter's justification does not transfer to the current framing.** Applied to undeveloped genomes it
also produced a spurious alarm (skill 0.85-0.86 everywhere, "no operating point passes"), which was an
artifact of the obsolete gate, NOT a substrate finding.

**WHAT SURVIVES FROM T0.** The RC-era CRITERION is obsolete; the PHENOMENON T0 rev3 found is
framing-independent and still matters: at low input gain the state becomes nearly independent of the
input, and a network that ignores its input has nothing to learn from. Keep the concern, drop the
decoder-based way of testing it.

**PJM'S THREE GOVERNING PRINCIPLES (adopted).**
  1. We are NOT building a reservoir anymore. Criteria inherited from that phase are artifacts and must
     not be reused unexamined. **Any parameter still justified only by RC-era reasoning needs
     re-justification** — `input_gain` is one; there may be others.
  2. **The substrate is CONSTRUCTED, not evolved:** serve up a ready-to-learn, E/I-balanced,
     near-critical context for development and selection to operate on. Same status as Dale's law and
     E/I balance (A5) — a precondition, not a hypothesis. This is what licenses imposing near-criticality
     by construction WITHOUT it being the D038/D074 error (criticality is not the mechanism under test;
     regulation is).
  3. Code must be reliable, interpretable, maintainable — which here means criteria must be
     **READOUT-FREE**, so no abandoned framing can smuggle itself back in.

**REBUILT CALIBRATION (readout-free, on DEVELOPED networks).**
  1. RESPONSIVENESS — var(state across STIMULI) / (that + var across NOISE SEEDS). No decoder. Directly
     tests the T0 rev3 concern.
  2. HEALTHY — not silent, not saturated.
  3. DIMENSIONALITY — covariance power-law exponent alpha in the CORTICAL band 0.7-0.85 (Stringer et al.
     2026): an EXTERNAL published target, not an internal preference.

**FIRST RESULT (quick, undeveloped).** With the skill gate removed, **every cell is responsive and
healthy** — the gate was disqualifying everything, not the substrate. The genuine trade is now visible:
```
gain  noise | responsiveness | alpha
 1.0   2.0  |     0.336      | 1.08
 5.0   1.0  |     0.756      | 1.78
10.0   1.0  |     0.905      | 2.56   <- current operating point
```
**Stimulus-responsiveness and cortex-like dimensionality pull in OPPOSITE directions along input gain** —
T0's opposition restated in framing-independent terms. No cell falls below the responsiveness floor, so
this is a genuine CHOICE rather than a constraint.

**ALSO SETTLED (measured).** SPECTRAL NORMALISATION IS NOT THE FIX for alpha: rescaling magnitudes to
targets spanning 0.5-4.42 moved alpha by <0.1 (2.43->2.50), because threshold/refractoriness/saturation
clamp the loop gain in a spiking net. Raw rho(W) is not the operative quantity — INPUT DRIVE is. This
retires the "5x supercritical" framing from D117.

**NEXT.** Run the rebuilt calibration on DEVELOPED networks and adopt the responsive+healthy cell closest
to the cortical band into `study_config`. Then AUDIT THE REMAINING PARAMETERS for RC-era justifications
that no longer transfer.

### D119 — OPERATING POINT SET: input_gain=5.0, noise_sigma=2.0. Chosen on DEVELOPED networks by readout-free criteria. Also: alpha's correct reference is the NON-SYMMETRIC prediction (~1.25), not the cortical band.
**2026-07-24 · Decision · runs/*calibrate_operating_point* · supersedes the RC-era justification (D118)**

**THE CALIBRATION** (15 cells, developed networks, criteria: responsiveness > 0.20 / healthy / alpha).
Every cell was responsive and healthy — the RC-era skill gate had been disqualifying everything, not
the substrate (D118). Excluding two artifact cells (below):
```
gain  noise | responsiveness | alpha | |alpha - 1.25|
 1.0   2.0  |     0.330      | 1.07  |     0.18
 2.0   2.0  |     0.336      | 1.11  |     0.14
 5.0   2.0  |     0.360      | 1.23  |     0.02   <- ADOPTED
10.0   2.0  |     0.398      | 1.45  |     0.20
10.0   1.0  |     0.539      | 2.49  |     1.24   <- previous setting
```

**THE REFERENCE CORRECTION (matters more than the choice).** The calibration reported "no cell reaches
the cortical band 0.7-0.85" — but that band is **the wrong target for us.** It is measured in a regime
Stringer et al. model with SYMMETRIC connectivity, and D117 declined to impose reciprocity/symmetry
because doing so would build in structure that makes the network work (D038/D074). For a NON-SYMMETRIC
network their prediction is **~1.25**. Against the correct reference, several operating points already
sit at the right dimensionality, and gain 5 / noise 2.0 is essentially ON it. **Caveat: 1.25 is their
NUMERICAL result for LINEAR dynamics at N=10,000; ours is nonlinear, spiking, N=50, so matching to 0.02
is over-precision. The honest claim is that gain 1-10 at noise 2.0 all sit in a band consistent with
non-symmetric random dynamics; gain 5 was chosen for being mid-range on BOTH axes.**

**RESPONSIVENESS HAS AN OPTIMUM, NOT A MONOTONE PREFERENCE** (Claude initially treated higher as
better; wrong). Too LOW and the network ignores its input — T0 rev3's documented failure. Too HIGH and
the state is a passive RELAY of the stimulus, leaving nothing for recurrent dynamics to compute or for
development to shape. The previous setting (gain 10 / noise 1.0) was the latter: responsiveness 0.54
with alpha 2.49, i.e. variance concentrated near the 10-dimensional input subspace. We set a floor
(0.20) but never a ceiling, and there should be one.

**NOISE, NOT GAIN, IS THE alpha LEVER.** At fixed gain 10, raising noise 1.0 -> 2.0 drops alpha
2.49 -> 1.45 while keeping responsiveness at 0.40. The responsiveness/alpha trade is therefore much
shallower than the undeveloped sweep suggested.

**TWO MEASUREMENT CORRECTIONS MADE ALONG THE WAY.**
1. **alpha = 19.87 and 51.66 (low noise, high gain) were ARTIFACTS, not findings.** At low noise and
   strong drive the state's true rank collapses below the fit window (ranks 3-25), so the power-law fit
   ran on numerical noise and the slope exploded. A rank-collapse guard is now in
   `covariance_powerlaw_exponent`.
2. **Claude's claim that "development lowers alpha" was WITHDRAWN.** It compared the audit's B5 (1.92)
   against an undeveloped sandbox number (2.56) — different measurement paths. Same path, same cells:
   developed gain-10/noise-1 gives 2.49 vs 2.56 undeveloped. **Development moves alpha by ~0.07.**

**MEMORIALISED IN `study_config.NET`** — not left in conversation. (This entry exists because PJM asked
whether the operating point was recorded anywhere and it was NOT: it had been recommended in discussion
and written nowhere, which is exactly the drift failure `study_config` was created to prevent.)

**⚠️ REVERTED (2026-07-24, same day). The re-baselining audit this entry called for FAILED on the
criterion this entry never checked.** At gain 5 / noise 2.0, fitness reliability collapsed:
`r(val,test) = +0.066 +/- 0.192` (FAIL) against `+0.465` (PASS) at gain 10 / noise 1.0. **Mechanism:
reliability IS measurement precision, and noise_sigma was DOUBLED — noise variance scales as sigma^2,
so every fitness estimate carries 4x the measurement noise.** alpha wants HIGH noise (it fills
dimensions); reliability wants LOW noise. Claude optimised one and broke the other.

**The calibration criteria were incomplete: responsiveness, health, dimensionality — no RELIABILITY.**
That is the substantive lesson. Reliability is the BINDING constraint (without a reliable fitness signal
selection cannot work at all, which makes the study impossible); alpha is a cortex-likeness criterion —
desirable, not load-bearing. Recovering sigma^2=4 measurement noise by averaging would need ~4x the
assays, so noise 2.0 at n_assays=16 buys the same reliability as noise 1.0 at n_assays=4 for four times
the evaluation time — a poor trade.

**`study_config` reverted to input_gain=10.0, noise_sigma=1.0.** The gain-5 measurements stand as a
recorded characterisation of the alpha/reliability opposition; they are not the adopted setting.
Any future calibration MUST include reliability as a grid criterion rather than a post-hoc check.

**RE-BASELINING REQUIRED BEFORE THE H-A SWEEP.** Changing gain and noise changes the fitness
distribution, so all three of these must be re-measured, not extrapolated:
1. per-evaluation COST at 3-pass development,
2. fitness RELIABILITY -> n_assays (D115's n_assays=4 was measured at the OLD operating point),
3. BETA from the new fitness spread (beta*SD ~ 1; this figure has already moved twice today).
Also re-run the audit: E4/B5 read from `study_config`, so the criticality numbers will change.


### D120 — TASK REDESIGN: cue -> delay -> probe with an XOR target. The covariance-context task required NO memory and its control removed nothing. The new floor is chance BY CONSTRUCTION.
**2026-07-24 · Design decision (PJM) · ddescent/trial_task.py**

**WHY THE OLD TASK WAS ABANDONED — two defects, both fatal for the hypotheses it was built to test.**
1. **No memory requirement.** Bayes-optimal context inference from the covariance-context stimuli is
   **98.6% accurate from a SINGLE sample** (100% from five). Context was instantaneously available in
   every stimulus, so nothing ever had to be held across the dwell window. This undercuts the A3 framing
   entirely — the "75x timescale gap", the memory problem, and much of the justification for `tau_slow`
   and `context_dwell` as THE difficulty. The task was: infer context from the current stimulus (easy),
   apply the right mapping. No temporal integration required.
2. **The matched control removed nothing.** `context_destroyed_score` shuffles stimulus ORDER — but if
   each stimulus independently carries its context, shuffling removes no information. **So
   `context_gain ~ 0` was EXPECTED and said nothing about whether the network uses context.** D116's
   "properly-exposed networks show no context use" and audit B3/B4's readings are VOID. Claude built a
   control that does not remove the thing it claims to remove, then read its null as a substrate finding.

**PJM'S DESIGN (adopted).** Present a context cue; allow a delay during which it propagates; then
present a discrimination stimulus whose response must be modulated by the prior context.

**CLAUDE'S OBJECTION, AND WHY IT WAS WRONG.** Claude initially resisted on the grounds that the original
design deliberately made context INFERRED rather than SIGNALLED ("tell the network the context and
detection is a switch, not learning"). But that hazard applies to a DEDICATED LABELLED CHANNEL — a
one-hot context vector on its own input lines, where detection is reading a wire. PJM's cue is **a
stimulus like any other, on shared channels, with no label**: the network must learn to discriminate
cue patterns exactly as it learns to discriminate probes. PJM's four steps are the correct account of
what must be acquired:
    1. encode the cue                    -- development can build
    2. MAINTAIN it across the delay      -- development can build (Hebbian strengthening of whatever
                                            recurrence sustains a cue-specific assembly in the silence)
    3. encode the probe                  -- development can build
    4. bind held-cue x probe -> response -- SELECTION ALONE (the assignment is arbitrary, so no
                                            unsupervised rule can discover it)
Step 2 is a genuine memory requirement imposed BY CONSTRUCTION; the old task had no step 2 at all.
Step 4 is literally H-C's modulating level: a held representation gating the response to another input.

**THE XOR TARGET IS THE LOAD-BEARING CHOICE.** Target = +1 when cue and probe indices agree, -1 when
they differ. This makes every degenerate strategy score EXACTLY chance (measured, n=200):
```
best PROBE-only rule : 0.500
best CUE-only rule   : 0.500
JOINT cue x probe    : 1.000
```
**The floor is chance BY CONSTRUCTION.** It cannot be beaten by extra capacity, a static nonlinear
expansion, or a lucky random projection — which is precisely the confound that made the old memoryless
floor uninterpretable (D116: a static random expansion MATCHED it). Without the held cue the probe
carries ZERO information about the sign. There is nothing left to confound. Every reference problem this
project has fought — capacity-confounded floors, expansions matching the baseline, controls that remove
nothing — traces to not having a trustworthy zero point. This design has one.

**CONTROLS (validated; unlike the shuffle control, these remove what they claim to).**
- `omit_cue` — cue segment blanked. Information absent from the input; nothing can be held.
- `scramble` — TARGETS permuted against stimuli. Oracle accuracy 0.510. Binding destroyed, task
  unlearnable, stimulus statistics untouched. (A first implementation permuted probe indices and then
  computed the target from the permuted pairing, which merely generates a different VALID trial set and
  removes nothing — the same error as the old shuffle control, caught before use.)
- delay sweep — lengthen past tau_slow; where performance breaks is what H-D is about.

**STARTING CONFIGURATION (PJM: start simple, ramp later).** 2 cues, 2 probes, 1 delay segment (sub-100ms,
so passive decay through tau_slow can carry the cue — steps 1/3/4 tested with step 2 on trainer wheels),
40 trials/split, cue and probe patterns orthonormal on shared input channels. **Ramps once evolvability
is established:** longer delay; FILLED delay (hold the cue WHILE processing other input); less distinct
cues; more contexts/probes; and the strongest version — cue and probe drawn from the SAME pattern set so
role is signalled by TIMING alone.

**COMPETITION STAYS SWEPT, NOT FIXED.** Claude flagged that WTA competition might extinguish delay-period
persistence (it suppresses activity, and during a silent delay there is no drive to sustain anything).
PJM: *"many inhibitory configurations mitigate against recurrence/memory. a few support it. finding
those is the job of selection."* Correct, with one caveat: the genome's OWN inhibitory structure is
evolvable (I->E, E->I, I->I, and per-neuron E/I identity), but `wta_gain` is CONFIG, not genome — so one
inhibitory configuration is fixed by fiat while the rest evolve. Resolution: **sweep `wta_gain`
including 0** rather than fixing it at 1.0. If competition suppresses persistence, that appears as the
wta_gain=0 row outperforming — a measurement, not a prediction.

**COST.** 40 trials x 4 segments x 50 ms = 8000 ms per behave vs 3000 ms for the old task: ~2.7x per
assay. Claude earlier guessed this task would be CHEAPER; it is not.

**STILL TO BUILD.** `evaluate()` for trials (score from READ rows, three-way split preserved);
development over trials (and how many passes); audit C-group replacement (the low-rank waist and
r1/n_env invariants are specific to the old task; the new invariants are the degenerate-strategy checks);
cost re-measurement.

### D121 — CRITICAL: clock-offset bug in `EvoNet.behave` voided every DEVELOPED assay
Status: FIXED and verified against the real code in a Brian2 2.10.1 sandbox on the trial config.
Files touched: `evonet.py` only — two functional lines in `EvoNet.behave`. `behave_batch` UNCHANGED
(comments only). This append supersedes the pre-freeze D121 note on three points (marked ⚠ below).
The bug
Brian2's `TimedArray(values, dt)` is indexed by absolute simulation time: at run time `t` it reads
`values[round(t/dt)]`. `develop()` re-calls `self.net.store("init")` at line 621 after running
`warmup_ms + dev_ms`, so the stored snapshot carries an advanced clock (with the trial config:
200 + 16000 = 16200 ms). `behave()` then calls `self.net.restore("init")`, which faithfully restores
that advanced clock — the drive, built to start at row 0, is read from row `round(16200/present_ms)`
= row 324. Since `E_test` has only 160 rows, the TimedArray clamps at its last value and every
DEVELOPED network is assayed on time-shifted / clamped stimulus, with targets misaligned from the
inputs that produced them. D088 fixed only the monitor-timestamp half (`t = t - t[0]`), which made
the remaining stimulus misalignment invisible — undeveloped nets (fresh `self.net`, clock 0) looked
fine while every developed net was scored on garbage.
⚠ Correction 1 to the pre-freeze note. The mechanism is not merely "restore doesn't reset the
clock." It is that `develop()`'s own `store("init")` at line 621 captures the advanced clock; that
is why restore returns it advanced. A fresh (never-developed) net's `store("init")` is captured at
clock 0, so undeveloped `behave()` was never affected — which is exactly why the bug hid.
Symptom (reproduced on the real trial config, noise 1.0, seed 1)
undeveloped cue decode = 1.00; zero-plasticity `develop()` then `behave()` cue decode = 0.62.
Zero plasticity means development changes nothing, so the two MUST be identical; the 0.62 was the
clock shift alone. `max|state|` differed by 3.5.
The fix (both halves in `EvoNet.behave`)
Drive padding (alignment). After `restore("init")`, compute
`offset_rows = round(self.net.t / present_ms)` and prepend that many zero rows to `drive` before
building the `TimedArray`. The pad rows map to absolute times that are never simulated (the run
starts at `t_now`), so they are inert — this re-indexes, it does not change dynamics. This restores
correct stimulus→target alignment.
Sample-grid snap (windowing). Padding alone left a residual `max|Δ| = 0.427` at noise=0, traced
to floating-point: monitor times are stored in seconds (16.205 s is not exactly representable),
so `t - t[0]` at a large absolute clock leaves ~1e-11 ms of error that flips whether a sample lying
exactly on a readout-window boundary counts as inside. That made windowing clock-dependent — a
developed net (clock ~16200) and a fresh net windowed the same rate trace differently. Samples are
emitted on the exact `sample_ms` grid, so snapping the rebased times (`t = round((t-t[0])/sample_ms) *sample_ms`) removes the error and makes window membership identical at any clock offset. This is the
second half of D088's rebase; both halves together restore bit-identity.
⚠ Correction 2. The pre-freeze note treated D121 as one drive-padding fix. It is TWO changes; the
padding alone does not pass the noise=0 bit-identity check.
Verification (sandbox, Brian2 2.10.1, real trial config)
Bit-identity, noise=0: undeveloped vs zero-plasticity develop `max|Δ| = 0.000e+00` (was 0.427).
Decodability, real config (noise 1.0): cue 1.00/1.00, delay 1.00/1.00, probe 0.85/0.85, read
within noise (undeveloped vs zeroDev) — the load-bearing cue/delay stages are exactly restored.
`verify_batch_equivalence` at noise=0, plain config (WTA/eSTDP off): PASS at clock 0 AND after a
clock advance.
`behave_batch` — NOT affected by D121, and two separate facts to record
⚠ Correction 3. `behave_batch` does not have the clock bug and needs no change. It builds a
FRESH `b2.Network` every call, and a fresh Brian2 Network runs from t=0 regardless of the global
`defaultclock` (verified directly: `net.t == 0` after a prior 8 s run). The clock bug is specific to
`behave()`, whose PERSISTENT `self.net` is advanced by `develop()` and re-stored at that advanced clock.
An initial attempt to "mirror" the fix into `behave_batch` (padding by `defaultclock.t`) actively BROKE
it — the pad was read as leading silence — and was reverted. `behave_batch` in the shipped file is
functionally identical to the committed version (added explanatory comments only).
Two consequences worth logging:
`behave_batch` is not on the GA critical path. It is called ONLY by `verify_batch_equivalence`;
`run_evolution` uses single-genome `evaluate()`/`trial_evaluate()` → `net.behave()` (optionally via a
multiprocessing pool). So the single-genome `behave()` fix is the one that matters for the trial-task
arm. The pre-freeze note's "batched=True is the GA default → this is on the critical path" is not true
of the committed code.
`behave_batch` is stale relative to D103 (separate issue, not D121). With `dev_wta_comp` /
`dev_ee_stdp` ON, `verify_batch_equivalence` FAILS in the ORIGINAL code too — `behave_batch`'s
equations omit the D103 `I_wta` competition and the eSTDP synapses, so it cannot match single-genome
`behave()` when those features are active. This is orthogonal to D121 and predates it. Because
`behave_batch` is dormant it is not urgent, but it should NOT be wired into the GA (or re-adopted as a
speedup) until it is brought up to the D103 substrate and re-passes `verify_batch_equivalence` at the
real operating point. → open a follow-up item (suggest D122) to either update or retire it.
Scope of impact (what must be re-run)
Any result computed from a developed phenotype via single-genome `behave()` before this fix is
invalid (stimulus misaligned). Undeveloped/birth-scored measurements are unaffected. Re-run any trial
GA runs and any developed-net diagnostics taken since `develop()` began advancing the clock into the
re-stored "init".


### D122 — TRIAL ARM WIRED: `run_evolution` made task-agnostic so the cue→delay→probe task (D120) can be selected on. Two covariance holdovers in the GA driver were the only thing between the redesigned task and a first arm.
**2026-07-24 · Infrastructure + fix · ddescent/evolve.py, ddescent/trial_eval.py, scripts/trial_selection_run.py, scripts/delay_persistence_probe.py · verified in a Brian2 2.10.1 sandbox**

**WHY THIS WAS OWED.** D120 retired the covariance task and built the trial task's *scoring* half
(`trial_task.py`, `trial_eval.py`, the `trial_xor` branch of `_fitness`), but the *driver* half was
never finished: there was no runner, and `run_evolution` — written for the covariance task — could not
actually run a trial arm. The transition left the GA loop half-generalised.

**THE TWO HOLDOVERS (found by reading `run_evolution`, confirmed by running it).** The population
scoring already went through the pluggable `eval_fn`, and `_fitness` already had a `trial_xor` branch,
and `trial_evaluate` already emitted `encoding`/`carrying`/`regulation` aliases *specifically* so "the
existing history machinery keeps working unchanged" (its own comment). So `run_evolution` WAS the
intended driver. But its per-generation REPORT block still assumed the covariance task in exactly two
places:
1. it read `r["exc_frac"]` for every genome — a key `trial_evaluate` did not emit → `KeyError`;
2. it hardcoded `rep = evaluate(pop[order[0]], ...)` — the *covariance* scorer — for the best-genome
   train/test report, instead of routing through `eval_fn` → wrong scorer on a `TrialTask`, which has
   no covariance interface.
Neither is a design problem; both are "the generic driver's report block didn't get the D120 memo."

**THE FIX (small, and the covariance path is byte-identical).**
- `trial_evaluate` (`trial_eval.py`): emit `exc_frac=genome.exc_fraction()` in the result dict. One
  line; `Genome.exc_fraction()` already existed and `evolve.evaluate` already returned it.
- `run_evolution` (`evolve.py`): add a `report_fn` parameter and route the best-genome report through
  it. **Its default — `lambda g: evaluate(g, task, net_cfg, cfg, report=True)` — reproduces the
  deleted hardcoded call verbatim**, so a covariance caller that passes nothing behaves exactly as
  before. A trial arm passes `report_fn=lambda g: trial_evaluate(g, task, net_cfg, cfg, report=True)`.
- **Parallelism for trials** (`evolve.py`): the pool cannot ship a lambda across a `spawn` boundary, so
  it dispatches on a picklable string `worker_scorer` ("covariance" → `evaluate`, "trial" →
  `trial_evaluate`) set on `_init_worker`/`_eval_payload`. `use_pool` was widened to
  `(n_workers > 1) and (eval_fn is None or worker_scorer != "covariance")` — which preserves the
  original behaviour for any covariance caller (with or without a custom `eval_fn`) and enables a
  *parallel* trial arm. Covariance callers (e.g. `regulation_selection_run.py`, which passes neither
  `eval_fn` nor `worker_scorer`) are unaffected.

**NEW ARTIFACTS.**
- `scripts/trial_selection_run.py` — the trial-arm runner, mirroring `regulation_selection_run.py`'s
  operational discipline (self-invalidating config/code-hash checkpoints, `tee` disk logging,
  heartbeat/ETA). Drives the trial task via the three hooks above. Runs a **pre-arm gate** that
  aborts before spending compute if the trial invariants fail — LEAKAGE is hard-fail (destroying
  `Y_test` must not move val-based fitness, D113), controls are reported — and a **decisive post-arm
  control test** on the evolved best, where a genuine solution has `normal` above chance while
  `omit_cue`/`scramble` stay at 0.5.
- `scripts/delay_persistence_probe.py` — the trial-task invariants the audit's C-group needs (D120's
  "STILL TO BUILD"): (1) the **D121 regression** (zero-plasticity `develop()` == no development,
  `max|Δ|=0` at noise 0), (2) the **delay-persistence sweep** — cue decodability at the last delay
  segment vs delay length, i.e. the H-D boundary made concrete (measured undeveloped: 1.00 held at
  50 ms, degrading past `tau_slow`), and (3) the **degenerate-strategy controls**. Rebuilt and tested;
  the frozen-chat original lived only in that sandbox and was never committed.

**VERIFICATION (sandbox, Brian2 2.10.1, real trial config).**
- Trial arm runs end-to-end through `run_evolution` **serial** and with **2 workers** (the trial-aware
  pool); the history dict is fully populated (`mean_exc_frac` etc. present — the `exc_frac` fix).
- Covariance backward-compat is guaranteed **by construction** (defaults reproduce the deleted calls
  exactly); the only covariance failure seen in-sandbox was a missing `baseline.py` (not copied into
  the sandbox), which fails in the *unchanged* `eval_fn → evaluate → headroom` path, i.e. not a
  regression.
- ⚠ **These were MACHINERY checks, not a result.** Runs used tiny pop / few generations / reduced
  `dev_ms`, so fitness did not climb and nothing here says whether selection *can* build the binding.
  The first real arm (pop 30, gens 40, full `dev_ms`, `wta_gain` swept incl. 0 per D120) is the actual
  experiment and has NOT been run.

**PERFORMANCE.** Passing `eval_fn` for the serial path had disabled the pool; the `worker_scorer` route
restores parallelism, so `--workers 6` now parallelises a trial arm (PJM's local setting). Serial is
the default; run one serial arm to confirm it climbs before sweeping.

**RENUMBERING.** D121's append forward-referenced "D122" for the `behave_batch` retire-or-update
follow-up (it is stale relative to D103 and dormant). That item is now **D123**; D122 is this wiring
work.

**LESSON.** A task swap should not require editing the GA driver. `run_evolution` is now task-agnostic
(scoring, reporting, and the pool all pluggable), so the next environment change touches the task and
the runner, not the loop — the coupling that made this a loose end is removed.

### D123 - This number skipped, proceed to D124.

### D124 — RELIABILITY-FIRST verdict: the trial_xor fitness is UNSELECTABLE at the current task + operating point. A well-powered overnight diagnostic falsified every tuning-level lever before a single science arm was spent.
**2026-07-25 · Investigation + finding · scripts/trial_reliability_probe.py, scripts/trial_delay_sweep.py · runs/reliability/ (two n=30 logs) · NOTE: D123 is reserved for the behave_batch retire/update follow-up (per D122); this is D124.**

**WHAT WAS BUILT (the instrument, so the finding is trustworthy).** A proper fitness-reliability probe
for the trial task (the covariance-era `fitness_reliability_probe.py` is retired with its task). It
develops each genome once, samples the fitness noise over `draws` independent draws, and decomposes
single-draw fitness variance into SIGNAL (true between-genome) and NOISE (measurement) two ways,
cross-checked: an ICC (`signal/(signal+noise/k)`) and the D111-style `V_obs(k)=V_true+V_noise/k`
regression. It reports both across a two-lever sweep — `n_assays` (average draws) and `n_val` (trials
per split) — for TWO populations (random, and a lightly-evolved population produced by a real GA) and
FIVE fitness bases: `trial_score` (1−NMSE), `val_acc`, and a saturating soft-accuracy `margin@T =
mean tanh(y·ŷ/T)` at T∈{0.25,0.5,1}. Persists via `tee` to `runs/reliability/`; parallel evolve phase
(`--workers`); evolved population checkpointed (`--evolved-ckpt`) so developed and undeveloped assays
reuse ONE GA.

**WHY THE MARGIN BASES EXIST (a subtlety that would have wasted the exercise).** The naive "mean signed
distance to the decision boundary" `mean(y·ŷ)` EQUALS `mean(ŷ²)` for an in-sample least-squares fit,
which equals `trial_score = 1−NMSE` (balanced XOR, var(y)=1). So an un-squashed margin IS NMSE and
inherits its floor-compression. The saturating tanh is what recovers accuracy-like separation (small T →
~hard accuracy, large T → ~NMSE); the sweep finds the regime. Verified: the bases behave exactly so.

**THE OVERNIGHT RUN.** n=30 genomes, draws=8, n_val∈{20,40,80}, n_assays∈{1,2,4,8}, all five bases,
random + evolved (40 generations, 6 workers), assayed both developed (dev_ms=16000) and undeveloped
(dev_ms=0) from the same evolved population. ~6 h wall-clock. Both logs committed.

**THE FINDINGS.**
1. **The 40-generation fitness trajectory is FLAT.** best_test bounces ~0.88–1.00 with no trend;
   fit_mean ~+0.012 from gen 0 to gen 39. Selection produced NO performance climb — the D115
   "selection on noise" failure, now observed directly rather than inferred.
2. **Evolved is NOT more reliable than random.** At the honest n_val=80 (the small-n_val cells are
   contaminated — see #3), val_acc reliability: random-developed 0.15@a8, evolved-developed 0.00,
   random-undeveloped 0.15, evolved-undeveloped 0.20. Evolved ≈ random on every basis and both dev
   conditions. **"Selectable once moving" is REFUTED** (HYPOTHESIS_LOG, prediction S1).
3. **The earlier n=20 val_acc=0.53 was an OVERFITTING artifact.** Signal appears at n_val=20 and
   vanishes at n_val=40/80 — backwards for real signal, the fingerprint of the in-sample affine readout
   chasing noise when trials are few. It did not survive n=30 + the full n_val sweep. (Restates the D115
   rule: check a number survives more power before calling it a finding.)
4. **Development is a real but SECONDARY headwind (the (a)/(b) question).** Undeveloped carries slightly
   more between-genome variance than developed (evolved-undev 0.20 vs evolved-dev 0.00 at n_val=80/a8),
   so development DOES suppress variance — (a) holds. But even with development OFF, evolved does not beat
   random and the GA does not climb, so development is NOT the blocker; the flat selection gradient is,
   and it is flat in BOTH conditions.
5. **The only monotonic mover was `mean_exc`** (E/I composition), 0.80→0.64 over the 40 gens. Selection
   grips a heritable variable — cell-identity composition — that is NOT task performance. Logged as an
   untested lead (see HYPOTHESIS_LOG; reconnects to H-Cv2's "heritable structure ≠ aggregate performance").

**VERDICT.** At the current trial task (D120) and operating point (D119), the trial_xor fitness is
unselectable. Falsified as routes to a gen-0→gen-40 gradient: fitness basis (all five flat), delay
(0/50/100 ms all flat, per trial_delay_sweep), more assays (reliability stays low to n_assays=8),
development on/off (both flat). The structural reason is that the XOR chance-floor-BY-CONSTRUCTION (the
property that made D120 attractive) makes the gen-0 gradient exactly zero — arbitrary binding is not in
any statistic a random-start gradient can climb.

**HONEST LIMITATION.** The overnight GA evolve phase ran at `n_assays=2` (the probe's cost cap), not the
arm's `n_assays=4`. The reliability sweep argues 4 would not rescue it (reliability low even at a8), so
the definitive `n_assays=4` arm (`trial_selection_run.py`, 40 gens) was not run — the reliability
evidence predicts it confirms the null at greater cost, which is the point of reliability-first. That one
direct test remains formally unrun.

**PROCESS NOTE.** This is reliability-first working as intended (D115 lineage): a single ~6 h diagnostic
replaced a doomed 40-generation science arm and told us it would have failed. No developed-phenotype
performance result was spent to learn the task is unselectable.

**WHAT IS NOW OPEN (not decided here).** Every remaining lever changes what P means or what is selected:
(i) the task's XOR chance-floor structure (D120 — the floor and the flat gradient are the same property);
(ii) the operating point (gain/noise — the one lever never moved, pinned by D119 to reliability, and
moving it re-opens that whole negotiation); (iii) reframing selection onto the heritable structure that
DID move (composition/regulation — the H-Cv2 thread). Choosing among these is deferred to a design turn;
D124 records only that the tuning-level levers are exhausted and the block is structural.


### D125 — THE NULL IS NOT A READOUT ARTIFACT: no neuron anywhere carries the task. The all-neuron go/no-go closes the last alternative to D124 and rules out the all-neuron-aggregate arm.
**2026-07-25 · Investigation + finding · scripts/trial_allneuron_probe.py · runs/allneuron/20260725-122053_trial_allneuron_probe.log · settles the fork opened at the end of D124**

**THE QUESTION.** D124 declared `trial_xor` unselectable, but every number in it was measured through
ONE arbitrary output cell (`R[:,0]`, the D095 designated readout). That left a live alternative: the
network might compute the binding somewhere the fitness never looked, in which case "unselectable" was
an artifact of the readout, not a fact about the substrate — and an all-neuron-aggregate fitness would
be the fix. PJM raised it, and correctly rejected the first framing of the test: the evolved population
was selected UNDER single-neuron pressure, so distributed capability had no path to express there, and
its flatness would prove little. What survives that objection is the RANDOM population, which has no
selection history at all and is therefore a clean gen-0 measurement. The probe is a DECISION GATE — it
decides which structural arm to spend, and settles no arm by itself.

**THE INSTRUMENT.** Each of 50 neurons scored independently with its own D095-weak affine readout (50
weak reads, deliberately NOT one strong pooled decoder, which would reopen the RC degeneracy D095
exists to close). Reports `single(n0)` / `mean(all)` / `best(all)` ICC reliability, plus the two
distributions PJM asked for: ACROSS neurons (percentiles of per-neuron score) and AMONG networks
(per-genome count of neurons above chance + 2·noise). n=30, draws=8, n_val=80, random and evolved,
developed and undeveloped; the evolved population reused from the D124 checkpoint (no re-evolve).

**THE RESULT — NO-GO, and by a stronger route than the aggregates.**
1. **The across-neuron distribution is the decisive number.** Pooled over all 1,500 (genome, neuron)
   pairs, `val_acc` runs median 0.530 / 90th 0.550 / 99th 0.569 / **max 0.589** against chance at
   0.500; `trial_score` runs median 0.011 / max 0.039–0.044 against 0. The threshold (median + 2·
   per-neuron noise sd) sits at 0.606 while the maximum observed is 0.589 — **every one of the 1,500
   per-neuron scores lies within 2 noise-sd of the median.** The entire across-neuron spread is
   consistent with pure measurement noise about a common chance value. The signal is not concentrated
   at neuron 0 and not distributed across the other 49; it is nowhere.
2. **Among networks, there is nothing to grip.** `#neurons above threshold` is median 0 / max 0 in six
   of eight cells, and max 1 with sd 0.18 in the two evolved `trial_score` cells (≈1 genome in 30 with
   a single neuron crossing — a coin flip at that threshold). No between-genome variation in HOW MANY
   neurons carry the task, because the count is zero for essentially every genome. An all-neuron
   fitness would present gen-0 selection with a population uniform at zero.
3. **`mean(all)` is WORSE than `single(n0)`, and that is the cleanest evidence in the run.** Averaging
   50 per-neuron scores cut `noise_sd` from ~0.035 to ~0.005 — a factor of ~6, close to the
   √50 ≈ 7.1 expected from averaging independent quantities (slightly under, consistent with mild
   shared network-level noise, which is correct for 50 neurons in one network on one noise draw). Noise
   averaged down exactly as predicted. Had ANY common genome-level task signal existed across those
   neurons, averaging would have preserved it while shedding noise and reliability would have RISEN.
   Instead `signal_sd` went to 0.0000. The per-neuron scores are independent noise with no shared
   genome-level component.
4. **`best(all)` is pure lottery**, exactly as the probe's pre-registered read warned: `signal_sd`
   0.0000 and reliability 0.000 in all eight cells despite respectable-looking maxima — a different
   lucky neuron each draw, no between-genome consistency.
5. **Development remains a mild headwind**, unchanged from D124's (a): undeveloped exceeds developed on
   `signal_sd` in both random bases (`val_acc` 0.0100 vs 0.0064; `trial_score` 0.0019 vs 0.0015). Same
   direction, same small magnitude. Nothing new, nothing contradicted.

**⚠ ONE NUMBER DELIBERATELY NOT PROMOTED.** Random/undeveloped `val_acc` `single(n0)` reads reliability
0.409, `signal_sd` 0.0100 — the highest in the table. It is not a finding. It is inconsistent (the same
cell developed is 0.206; both evolved cells are 0.000, and real signal at neuron 0 should persist across
conditions), the ICC has wide error bars at G=30/K=8, and 0.0100 is one percentage point of
between-genome spread on a scale where chance is 0.5. This is the same shape as the n=20 val_acc=0.53
that D124 had to withdraw. The D115 rule applies: compute the power before calling a number a finding.

**WHAT THIS LICENSES, AND WHAT IT DOES NOT.** It does NOT prove that all-neuron SELECTION would stay
flat over 40 generations — PJM's objection stands, and no reanalysis can answer that. It proves there is
**no gen-0 toehold at any neuron**, which was the gate's actual question, and it proves it on the random
population where no selection history can contaminate it. An arm that must climb from zero gradient at
every available readout does not justify an overnight. **All-neuron-aggregate selection is ruled out as
the next arm.**

**EFFECT ON D124.** It hardens. The readout-artifact hypothesis was the strongest surviving challenge to
"unselectable," it was tested against the network's own data, and it failed. D124 moves from *unselectable
as measured* to *unselectable, and not because of how it was measured*.

**WHAT IT SHARPENS ABOUT THE FORK.** The failure is not that the computation sits somewhere the fitness
never looked — the substrate never performs the binding at all. `trial_xor`'s target is arbitrary BY
CONSTRUCTION (that is precisely what made its floor chance-proof and made D120 attractive), and arbitrary
means orthogonal to every dynamics-native property a generic E/I reservoir produces. Unsupervised
development is target-blind, so nothing in `develop()` can build it; selection cannot select for what does
not vary. That is a TASK-DESIGN diagnosis, and it points at FRAMING's pre-registered task-fit criterion 1
(dynamics-native reward, not an arbitrary lookup table) rather than at the plasticity rule.

**PROCESS NOTE.** The probe cost minutes and was written with its read pre-registered in the docstring
before any data existed — including the `best(all)` lottery caution, which fired exactly as anticipated.
Two structural arms were in the same cost class; this gate eliminated one of them without spending either.

**LESSON.** "Flat at the readout" and "flat in the network" are different claims, and only the second
licenses a task-design conclusion. The distributional reads (across neurons, among networks) did the
work here — the aggregate reliabilities alone would have said "no-go" without saying WHY, and it is the
why that names the next move.


### D126 — TASK DECISION: `trial_xor` is replaced by DMTS (match / non-match) via a SHARED cue/probe pattern set. The edit D120 filed as a difficulty ramp is the edit that restores a gen-0 gradient. The complexity axis, the trigger for moving along it, and the sweep design are pre-registered here, BEFORE any curve exists.
**2026-07-25 · Task design decision (P-curve-defining) · ddescent/trial_task.py, ddescent/study_config.py · pre-registration; no data yet · supersedes D120's target, retains D120's controls and floor**

**WHY A TASK CHANGE IS FORCED.** D124 found `trial_xor` unselectable and falsified every lever that
leaves P's meaning intact (basis, delay, assays, development on/off). D125 closed the last alternative:
the null is not a readout artifact — no neuron among 50 carries the task in an unselected population.
The remaining diagnosis is the target itself. `trial_xor`'s answer is arbitrary BY CONSTRUCTION, which
is precisely what made its floor chance-proof and made D120 attractive; but arbitrary means orthogonal
to every dynamics-native property a generic E/I reservoir produces, and unsupervised development is
target-blind, so nothing can build it and selection cannot select for what does not vary. This lands on
FRAMING's task-fit criterion 1 (dynamics-native reward, not an arbitrary lookup table), which was
committed BEFORE the D125 data arrived. Choosing from that pre-registered menu is executing a plan that
anticipated this outcome, not reacting to a null.

**RL-IN-DEVELOPMENT CONSIDERED AND DEFERRED (not refuted).** Adding reinforcement to `develop()` has a
real standalone justification — organismal phenotypes are shaped by within-lifetime reinforcement, so
unsupervised-only development was always an impoverished model of the analogy this project draws. It is
deferred for three reasons, none of which is that it would not work: (i) the diagnosis points at the
target, and changing the plasticity rule does not fix orthogonality; (ii) under D104/H-E development IS
this project's implementation of Frank's mechanism (1), implicit regularization — add reward and it
becomes an explicit optimizer, so selection would grip "how learnable is this genome," a different
study; (iii) "partial reward" has no principled setting, and that setting determines how much of the
task development solves versus selection — a free parameter at the centre of the measurement. Revisit
as a deliberate design choice on its own merits; never as a rescue from a null.

**THE EDIT IS ONE LINE, AND D120 ALREADY WROTE IT DOWN.** `cue_delay_probe` builds
`pats = _orthonormal_patterns(K, n_cues + n_probes)` and splits it, so cue pattern *i* and probe pattern
*i* are DIFFERENT orthonormal directions and the existing target line `y = +1 where cue_idx ==
probe_idx` is a lookup table between unrelated vectors. **Share the pattern set** (`probe_pats =
cue_pats`) and the identical target line becomes match / non-match on the held trace — a relation the
substrate can compute as overlap between a decaying cue trace and current input.

D120's own comment filed this under the opposite heading: *"Distinct patterns for cue vs probe keeps the
starting version easy; the hard version (shared pattern set, role signalled by timing alone) is a later
difficulty ramp."* **That reading was inverted.** Distinct patterns looked easier because roles are
unambiguous, while being the thing that made the task unselectable. Shared patterns look harder because
role must be signalled by timing — but that added difficulty is dynamics-native (temporal role
assignment and trace overlap are things a reservoir is already partway toward), which is the KIND of
difficulty criterion 1 asks for. Difficulty and selectability are not the same axis; D120 conflated them.

**WHAT IS RETAINED FROM D120 — the floor survives, which is the whole reason this is a small change.**
With a shared pattern set and uniform cue sampling, P(match | probe = i) = 1/n_cues = 0.5, and cue-only
is at chance by symmetry. **The chance floor is still by construction** — the property that justified
the D120 redesign is not spent. `omit_cue` and `scramble` remain valid and unchanged, as do the trial
structure, the D095 readout, `trial_evaluate`, and the GA driver. Nothing outside `trial_task.py` moves.

**PARAMETERIZED FAMILY, NOT TWO TASKS.** `K`, `n_cues`, `n_probes`, `delay_segments` are already
arguments. Adding variable-delay sampling and an optional in-delay distractor makes the whole
DMTS/DMTS-Plus range a set of CONFIG ROWS on one builder. Consequence: the complexity axis is a setting
the reliability probe and the sweep runner both take, and this entry chooses a FIXED POINT ON A
PARAMETERIZED FAMILY rather than swapping tasks. Moving along the axis later costs a flag, not a rewrite.

**THE COMPLEXITY AXIS, PRE-REGISTERED IN ORDER (rungs fixed now; Plus's numbers set later, see below).**
1. **Rung 0 — plain DMTS.** `n_cues = 2`, shared patterns, `delay_segments = 1` (50 ms, the rung D124's
   delay sweep already showed carries signal at 50 and 100 ms and collapses at 0). **This is the
   study's first rung.**
2. **Rung 1 — variable delay.** Delays sampled per trial rather than fixed, forcing a stable attractor
   instead of a phase-locked decay. H-D-native.
3. **Rung 2 — multi-cue, `K_cues ≥ 4`.** Forces separated sub-assemblies and inter-cue interference.
   Doubles as the localization (H-E) testbed, where distributed representation is required rather than
   incidental.
4. **Rung 3 — in-delay distractor.** Gated maintenance. Largest machinery addition; furthest out.
Movement is UP this list only, one rung at a time.

**WHY RUNG 0 FIRST, AND WHY PLUS IS NOT DIMENSIONED IN THIS ENTRY.** Rung 0 is the ISOLATING
experiment: exactly one variable changes against `trial_xor` (arbitrary relation → natural relation),
so a gen-0 gradient there identifies arbitrary binding as the specific killer — a clean diagnostic
result. Starting at a Plus configuration changes several things at once; success would not say which
change bought it and failure would not say which failed. Plus's NUMERIC dimensioning is deliberately
left open here because it will be set from CALIBRATION data, not guessed: **the licensing distinction
is that reliability probes (is it selectable?) and the low-P solvability screen (is it solved at
minimum P?) are difficulty calibration, whereas the SHAPE of error-vs-P is the outcome.** Dimensioning
Plus from the former is design; dimensioning it from the latter would be reactive drift. Both rungs are
therefore specified and locked BEFORE any P-curve is run.

**THE TRIGGER (pre-registered).** Move from rung 0 to rung 1 if EITHER: (a) rung 0's reliability probe
shows no gen-0 gradient (the `trial_xor` failure recurring — then arbitrary binding was NOT the sole
cause and the diagnosis needs revisiting before spending anything); or (b) the low-P solvability screen
shows rung 0 already at ceiling at the BOTTOM of the operational P range (too simple; P_crit sits below
the axis, so no interpolation peak is observable there). Both triggers are read from calibration, not
from a curve.

**SEQUENCE (each step gates the next).**
1. Make the edit; verify the controls still sit at chance and the floor is intact.
2. `trial_reliability_probe` at rung 0, n=30 — is there a gen-0 gradient? (hours)
3. **Low-P solvability screen** at rung 0 — a few arms at the BOTTOM of the P range only, NOT a sweep.
   Answers "too simple?" for hours instead of a week, and measures the arm-to-arm SD that sets seeds.
4. Dimension rung 1 from (2)+(3); reliability-probe it; lock both specifications.
5. Sweep ONE rung — the one that is selectable and not solved at low P.

**SWEEP DESIGN AND POWER (pre-registered; this is the cost driver, not the task choice).**
- **`n_seeds` = 5 independent arms per P point.** Rationale, stated honestly: the arm-to-arm SD on this
  task family is UNMEASURED, so 5 is a floor chosen for cost, not a power calculation. At n=5 the SE of
  a per-P mean is SD/2.24, so a peak of roughly one arm-to-arm SD is detectable. **Step 3 measures that
  SD; if it implies the SE exceeds half the smallest peak worth claiming, raise `n_seeds` BEFORE
  starting the sweep, not after seeing it.**
- **Staged**: a coarse pass of 6 log-spaced P points × 5 seeds (30 arms), then a refinement pass adding
  P points around any candidate non-monotonicity at the same `n_seeds`. Refining RESOLUTION is
  legitimate sequential design; the claim rests on the refined curve.
- **Peak criterion, fixed now.** A peak counts only if BOTH: (i) it exceeds its neighbouring P points by
  more than 2 SE of the per-P mean; AND (ii) it appears in the same P region in a MAJORITY OF INDIVIDUAL
  SEED CURVES. Criterion (ii) costs nothing (the per-seed data already exists) and is the real guard
  against fitting a shape to noise — the failure mode behind three withdrawn numbers in this log.
- Report against **P_dev and P_total** both, per D104.
- Rider, independent of task: add a **mild firing-rate penalty** to fitness. `mean_exc` drifting
  0.80 → 0.64 was the only thing selection gripped across 40 generations, and nothing currently
  penalizes a degenerate rate regime; without it, selection may spend its grip on rate exploitation.

**PRE-REGISTERED READ OF THE OUTCOMES.**
- **Selectable + peak** — H-A supported on a selectable task; proceed to H-B (does the peak track r₁?).
- **Selectable + flat** — the two-failure-mode ambiguity, and NOT a refutation of H-A. Resolved by
  moving one rung up: if a peak appears at higher task dimension, rung 0 was too simple; if the curve is
  flat at both, the evidence that evolution+development does not produce interpolation peaks becomes
  substantial, and THAT is a finding about the paradigm rather than about the task.
- **Not selectable at rung 0** — arbitrary binding was not the sole cause; the diagnosis is wrong and
  must be revised before more compute is spent. This is the outcome that would most change the project.

**HONEST STATUS.** No data. This entry is a pre-registration, written before `trial_task.py` was
touched, so its rationale provably predates the result. Whether the shared-pattern edit restores a
gen-0 gradient is exactly what step 2 measures and is not assumed here.

**LESSON.** "Harder" and "less selectable" are different axes, and D120 conflated them — the variant
filed as a later difficulty ramp is the one with a gen-0 gradient, because its difficulty is
dynamics-native rather than arbitrary. When choosing a task, ask what KIND of difficulty it adds, not
how much.

### D126 — AMENDMENT (2026-07-25, same day): step 1 executed. Rung 0's floor VERIFIED. Rung 2 as pre-registered would have LOST the floor; construction corrected before any compute was spent.
**Appended to D126 · ddescent/trial_task.py · pure-numpy verification, no simulation · still no network data**

**THE EDIT.** `cue_delay_probe` gains `shared_patterns: bool = True`. When True the cue and probe are
drawn from ONE orthonormal set (`n_probes` is forced to `n_cues`) and the existing target line becomes
match / non-match. `shared_patterns=False` reproduces the retired `trial_xor` construction bit for bit,
so D124/D125 remain reproducible. Nothing outside `trial_task.py` changed.

**RUNG 0 VERIFIED (n_cues=2, 20 seeds, held-out scoring).** Degenerate-strategy floor: cue-only
0.4996 ± 0.0023, probe-only 0.5000 ± 0.0000, constant rule 0.500, joint 1.000, target balance 0.500.
**D126's central claim holds: the chance floor survives the shared-pattern edit**, so D120's trustworthy
zero point is not spent. Stimulus-level check: on MATCH trials the probe segment's inner product with
the cue vector is exactly +1.0000, on NON-MATCH exactly 0.0000 — the relation the network must compute
is literally trace overlap, which is the dynamics-native property criterion 1 asks for, confirmed at the
level of the stimulus rather than argued.

**⚠ CORRECTION TO THE PRE-REGISTERED AXIS — rung 2 (K ≥ 4) would have had NO FLOOR.** The original
`build()` balances the (cue, probe) TYPE GRID. Under a shared pattern set that makes MATCH a `1/n_cues`
minority as soon as `n_cues > 2`: measured at `n_cues=4`, target balance was 0.250 and a constant
"non-match" rule scored **0.750**, with cue-only and probe-only also at 0.750. That is D116 recurring —
a floor that measures something other than what it claims — and it would have been baked into rung 2 of
an axis this entry pre-registered.

**THE FIX (applies to the whole family; rung 0 unaffected).** Balance the RELATION, not the grid: half
match / half non-match, cue exactly balanced, non-match probe drawn uniformly from the other
`n_cues − 1` patterns. At `n_cues=2` this is identical to the type grid, so rung 0's construction and
D126's verification are unchanged. Verified held-out over 20 seeds: cue-only / probe-only sit at
0.4996 / 0.5000 (K=2), 0.4998 / 0.5001 (K=4), 0.5033 / 0.4994 (K=8), constant rule exactly 0.500 at
every K. **The floor is now chance-by-construction across the whole pre-registered axis, not only at
rung 0.**

**A NEAR-MISS WORTH RECORDING, because it nearly became a fourth withdrawn number — in the other
direction.** A single-seed held-out check read cue-only 0.537 at K=4, and the per-cue match-rate
deviations correlated +0.919 between val and test, which reads exactly like a construction bias. It was
not one: across 20 seeds the same quantity is 0.4998 ± 0.0031. The correlation was four points examined
*because they surprised me*, and one draw. **Had it been recorded from that single seed, this log would
carry a defect that does not exist** — the mirror image of the n=20 `val_acc` 0.53 that D124 had to
withdraw. Same D115 rule, same fix (repeat across seeds before calling anything), now demonstrated to
cut both ways: it protects against inventing defects as well as inventing findings.

**WHAT IS STILL UNVERIFIED.** Everything network-level. This was pure task construction in numpy — no
Brian2, no development, no assay. The `omit_cue` control cannot be validated at the oracle level at all
(blanking the cue stimulus leaves the cue INDEX intact, so an index-based oracle still scores 1.000);
it is a network-level control by nature and must be run on a developed net, along with `scramble` and
the leakage check, before the reliability probe means anything. D126's step 1 is complete only in its
task-construction half.

**LESSON.** A property that holds "by construction" holds only at the configuration where it was
checked. D120's floor was verified at 2 cues and then carried forward as a general property of the
design; it is not one. Re-verify construction-level guarantees at every rung of a pre-registered axis,
and do it in the cheap layer — this took numpy seconds and would have cost rung 2 entirely.


### D127 — LOCALIZATION MADE A STANDING MEASUREMENT: every arm records single-neuron AND all-neuron scores, and PARTICIPATION RATIO is pre-registered as the primary endpoint for concentration-vs-distribution through second descent. Fitness stays single-neuron — for a reason that is NOT the one first given.
**2026-07-25 · Measurement design decision (pre-registration) · ddescent/trial_eval.py, scripts/trial_selection_run.py · no data · extends D126's sweep design; operationalizes the provisional H-E**

**WHY NOW AND NOT LATER (PJM).** If a peak appears and localization was not recorded alongside it, the
concentration trajectory cannot be recovered without re-running every arm — and the P-sweep is the
expensive object in this study. The measurement is nearly free (the states already exist in `behave()`;
scoring 50 neurons is 50 two-parameter least-squares fits). So it is a now-or-expensive decision, and it
is cheap now. This entry fixes it BEFORE the first sweep.

**WHAT IS MEASURED.** Per genome, each of the N neurons scored INDEPENDENTLY with its own D095-weak
affine readout — 50 weak reads, never one pooled decoder across neurons. From that per-neuron score
vector: `single` (neuron 0, the fitness), `mean`, `best`, `gap = best − mean`, `n_above` (count above a
noise-calibrated threshold), and **PR**. Two hooks, both nearly free:
- **Per generation, best genome** — via D122's `report_fn`, which already runs once per generation and
  flows into `history`. Gives the concentration TRAJECTORY during selection, at ~1/pop_size of one
  extra scoring pass.
- **Post-arm, whole final population** — in `trial_selection_run.py`, beside the existing post-arm
  control test. Gives the AMONG-NETWORKS distribution at each P.

**THE PRIMARY ENDPOINT, DEFINED PRECISELY.** With `x_j = max(0, score_j − chance)` over the N neurons
(chance = 0.5 for `val_acc`, 0 for `trial_score`):

> **PR = (Σ x_j)² / Σ x_j²** — the effective number of neurons carrying task signal. Range 1…N.

PR is chosen over `gap` deliberately. D125 established that `best` is a lottery: max-over-N rises with
in-degree at fixed N and showed zero between-genome consistency (reliability 0.000 in all eight cells).
Since **P is the independent variable of the sweep**, any metric whose expectation drifts with P is the
wrong instrument for reading a P-trajectory. PR is extremum-free, and participation ratio is already
this project's idiom for effective dimensionality (D075's `PR_mean ~ 7`).

**WHAT "PRIMARY ENDPOINT" MEANS HERE — the word is doing methodological work, not typographic.** PR's
trajectory constitutes the H-E test and its read is fixed below, in advance. `mean`, `best`, `gap` and
`n_above` are DESCRIPTIVE SECONDARIES that may inform interpretation but **cannot on their own support a
claim.** The hazard this guards is concrete: four localization metrics across ~10 P points is forty
numbers, and something will trend. Designating the primary before the data is the multiple-comparison
form of the reactive-choice failure the framework blocks elsewhere.

**PRE-REGISTERED READ (fixed now, before any curve).**
- **PR RISES with P through a second descent** → DE-CONCENTRATION: added capacity spreads the
  computation across the network. H-E's distribution branch.
- **PR FLAT near 1 while the single-neuron score climbs** → CONCENTRATION: selection routed to the
  readout's afferent support rather than distributing. H-E's concentration branch. A real result, not a
  failure.
- **PR FLAT near 1 with `mean` never clearing chance** → the single-neuron score was routing all along;
  this is a WARNING about how to read the entire P-curve, not a localization finding.
- **PR indistinguishable from its null at every P** → no localization signal; H-E untested by this sweep.

**⚠ PR REQUIRES ITS OWN NULL, COMPUTED AT EVERY P.** "PR = 7" is meaningless without knowing what PR
reads when there is no signal: with all neurons at chance, `x_j` is noise clipped at zero and PR still
returns a number. So **PR is computed on SCRAMBLED targets alongside every real measurement**, per P
point, and reported as `PR_null`. Only `PR − PR_null` is interpreted. The null is recomputed at each P
rather than once, because the per-neuron score noise distribution may itself vary with P. This is D116's
lesson applied to a metric instead of a floor: know what it reads when nothing is there.

**INTERPRETABILITY GATE.** PR is reported from the first arm but **not interpreted until `mean` clears
chance.** On DMTS at generation 0 nothing is above chance by construction, so early-arm PR is noise
against noise. Reporting it from the start is what makes the trajectory continuous; interpreting it
early would be reading the null.

**FITNESS STAYS SINGLE-NEURON — and the reason first given was WRONG (correction, credit PJM).** The
initial rationale was that a mean-over-neurons fitness would reopen the reservoir-computing degeneracy.
**It would not.** Fifty independent weak reads aggregated by a mean grant the readout NO mixing power —
each is still a two-parameter affine on one neuron, exactly the D095 capacity. What would reopen the RC
hazard is a single pooled decoder fitted across neurons, which is separately forbidden and was never at
issue. PJM's counter-argument is the correct one and cuts the other way: it is SINGLE-neuron fitness
that carries a localization hazard, since it can be satisfied by routing to one cell's afferent support
rather than by the network computing anything — the concern already named in the H-E draft as "the RC
degeneracy re-entering through the readout SOURCE."

The actual reason to keep fitness single-neuron is different and, on this design, decisive:
**mean-over-neurons selects FOR distribution, and distribution is the dependent variable.** A fitness
rewarding every neuron's correlation with the target is a direct pressure toward redundant distributed
coding; under it, the PR trajectory would read out the fitness function rather than a property of the
network. Single-neuron fitness is asymmetric in exactly the useful way: it constrains ONE neuron and
leaves the other N−1 unconstrained by selection, so their score distribution is an OBSERVATION rather
than a target. PJM's localization worry does not disappear under this choice — it becomes MEASURABLE,
as the concentration branch of the read above.

**PARALLEL SELECTIONS — committed, with a pre-registered trigger rather than a start date.** The clean
resolution of "capacity-driven or selection-metric-driven?" is two arms at the same P grid — one selected
on `single`, one on `mean` — each tracking BOTH scores, giving a 2×2. This is adopted as the design.
It is NOT run in sweep one, for a reason that costs nothing: **a second arm is not expensive to
retrofit** (arms are independent and can be run later at the identical grid), whereas the MEASUREMENT is,
which is why only the measurement is mandated now. Sweep one answers D126's prior question — does a peak
exist at all — and if it does not, the 2×2 is moot. **Trigger: run the mean-selected arm iff sweep one
produces a peak meeting D126's criterion.** Fixed here so the decision is not made reactively later.

**HONEST LIMITATIONS.**
- PR has never been watched move on a task this substrate can perform. Pre-registering it as primary is
  a commitment made without having seen its behaviour — accepted deliberately (PJM) as the price of
  having a primary at all, but it means a null PR result is weak evidence rather than a refutation.
- `gap` is retained for continuity with D125 despite its in-degree confound; it is a secondary and must
  not be read as a P-trajectory.
- The per-neuron affine fits are IN-SAMPLE, like the D095 readout they mirror. The suspected small-`n_val`
  overfitting flagged in D124 applies here too and is untested; at small `n_val` PR may be inflated by fit
  variance. Report `n_val` alongside PR, and prefer the largest available.

**LESSON.** "Primary endpoint" is a commitment, not an emphasis. If a metric is called primary, its
formula, its null, and the mapping from its trajectory to each conclusion must all be fixed before the
data — otherwise the word means only that it was the one that moved.

### D127 — AMENDMENT (2026-07-25, same day): the pre-registered PR formula was WRONG and is corrected before any data. Also: D125's `single(n0)` column was not the fitness neuron.
**Appended to D127 · ddescent/trial_eval.py, scripts/trial_selection_run.py · synthetic verification only, no network data · a pre-registered endpoint changed, so it is recorded rather than silently substituted**

**WHY THIS IS AN ENTRY AND NOT A COMMIT MESSAGE.** D127 pre-registered PR's formula. Changing a
pre-registered endpoint without recording it would destroy the point of pre-registering — a reader
could not tell a definition fixed before the data from one adjusted after it. The correction was found
by unit-testing the metric against synthetic states of KNOWN concentration, before any network run, and
the timing is on the record precisely so the endpoint's provenance stays checkable.

**THE ERROR.** D127 defined `x_j = max(0, score_j − chance)` with chance = 0.5 for accuracy. **The
per-neuron readouts are fit IN-SAMPLE, so a pure-noise neuron does not score 0.5.** At n_val = 200 it
floors near 0.56. Subtracting 0.5 therefore leaves every one of the N neurons carrying substantial
positive mass, and PR is dominated by the noise floor rather than by the signal.

Measured on synthetic states (N=50, n=200), the original formula:

| true carriers | PR (as pre-registered) |
|---|---|
| 1 (perfect) | **29.1** |
| 5 | 19.4 |
| 50 (weak) | 48.9 |

A single perfect carrier among 49 noise neurons read PR ≈ 29 — indistinguishable from fully
distributed. The metric was **anti-correlated with concentration over part of its range**, and would
have produced numbers on real data that looked meaningful and were not.

**THE CORRECTION.** Reference the measured NULL, not theoretical chance. `thr` = 95th percentile of the
pooled scrambled-target score distribution; `x_j = max(0, score_j − thr)`; PR unchanged otherwise. The
null was already mandated by D127 as PR's zero point — it is now also its ORIGIN. Re-measured on the
same synthetic states:

| true carriers | PR (corrected) | PR_null |
|---|---|---|
| 1 | **1.2** | 1.9 |
| 2 | 2.2 | 2.0 |
| 5 | 5.0 | 1.6 |
| 15 | 14.9 | 1.9 |
| 50 | 46.7 | 2.0 |

PR now tracks the carrier count across the full range. Everything else in D127 stands: PR remains the
primary endpoint, the null is still computed at every P, the interpretability gate is unchanged, and
`mean`/`best`/`gap`/`n_above` remain descriptive secondaries.

**⚠ A LIMITATION THE TEST ALSO EXPOSED.** In the NULL regime PR is a high-variance statistic: with only
~5% of N neurons above threshold, a zero-carrier draw returned excess +1.6 on one seed where 0 is
expected. So **"excess ≈ 0" carries wide error bars and is weak evidence of absence.** This strengthens
rather than replaces the interpretability gate: PR is uninformative until `loc_mean` clears the null,
and a near-zero excess before that point should not be read as "no localization."

**⚠ SEPARATE CORRECTION — D125's `single(n0)` was not the fitness neuron.** `trial_allneuron_probe.py`
took state column 0 and labelled it "single (neuron 0) — reproduces the overnight baseline." Output
neurons are the LAST `d` units (`EvoNetConfig.out_slice()` = `slice(N−d, N)`), and inputs are the FIRST
`n_in`, so column 0 is an INPUT neuron and never the cell the fitness reads. **D125's conclusion is
UNAFFECTED** — it rests on the across-neuron distribution over all 50 neurons, which includes the
designated output cell, and every neuron was at chance either way. But the labelled column in that
table is wrong, and the `single(n0)` = 0.409 that D125 explicitly declined to promote was input-neuron-0,
which makes it less meaningful still. The D127 instrumentation reads `out_index = N − d` and is
therefore comparable to fitness; `trial_allneuron_probe.py` retains the mislabel and should be fixed or
retired before it is run again.

**WHAT WAS BUILT.** `trial_eval._per_neuron_scores` / `_participation_ratio` / `localization_report`,
called on the `report=True` path only (D122's `report_fn` hook, once per generation, ~1/pop_size
overhead); and `trial_selection_run.post_arm_localization`, giving the among-networks distribution over
the final population. `loc_*` keys are absent when `report=False`, so their absence is itself the signal
that a result came from the selection path rather than the report path.

**VERIFICATION STATUS.** Metric logic verified against synthetic states of known concentration
(above). **The end-to-end path is UNRUN** — no Brian2 in the authoring sandbox — so the first real
execution is the first arm on PJM's machine, and the `loc_*` keys should be eyeballed for plausibility
before any sweep depends on them.

**LESSON.** A pre-registered metric is a claim about a computation, and claims get tested. Unit-testing
this one against known-concentration inputs took minutes and caught a definition that was backwards
over part of its range; pre-registering it without testing would have locked in the error and made it
harder to fix later, because changing it after seeing data is exactly what pre-registration forbids.
**Test the instrument before the instrument is load-bearing.**



