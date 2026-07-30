# HANDOFF — resuming the Frank double-descent project in a fresh chat

**Purpose.** A chat that grows too long is terminated without warning. This file exists so the next chat
resumes in one read instead of re-deriving. It is the ONLY file whose job is orientation.

**What this file is NOT.** It is not a file map, not a code summary, not a decision index. The repo is
public and clonable (`git clone https://github.com/PeterMikulecky/reservoir_ddescent`), so an assistant
can read `DECISIONS.md`, `HYPOTHESIS_LOG.md`, `FRAMING.md`, `BRIDGE.md`, `LAB_NOTEBOOK.md` and the code
directly, at HEAD, with no staleness. Duplicating any of that here would create a second source of truth
that drifts. **This file carries only what the repo cannot give: which way the fork points, what has been
ruled out and by what evidence, and which numbers are trustworthy.**

**Opening move for a fresh chat.** Clone the repo, `git log --oneline -15`, read §1–§2 below, then read
the last two or three `### D` entries in `DECISIONS.md`. That is sufficient to resume.

---

## §0. MAINTENANCE — when to update, and why the trigger is loss-based

Only **§1 and §2 are volatile**, and they are short by design so a refresh is a two-minute edit.
§3–§6 change rarely — when a standing rule is earned, a branch closes, or an artifact is identified.

**The trigger is not a cadence. Update after a significant move or development whose loss to a frozen
chat would meaningfully hamper resumption.** (PJM, 2026-07-25.) The reasoning: once something is in
`DECISIONS.md` and committed, a freeze does not lose it. What a freeze destroys is the state that exists
ONLY in the conversation — a conclusion reached but not yet memorialized, and the next move, which is
obvious in context and invisible to a fresh reader. So the question is always **"is this chat carrying
something the repo isn't, and would re-deriving it cost real work?"**

**Fires when:** the NEXT ACTION changes (a step completes, a blocker appears); a result lands that
changes how the state should be read; a branch closes or a lever is ruled out; a decision redirects the
work; or something was discovered in passing that would be expensive to rediscover.

**Does not fire for:** a memorialization whose content §1 already reflects; routine code edits; any
entry after which the next action is unchanged.

If §1 disagrees with the newest `### D` entry, the D entry wins and this file is stale — say so rather
than trusting it. And when in doubt, refresh: the cost is two minutes, the cost of being wrong is a
re-derivation.

---

## §1. STATE — the one-paragraph read  ·  *volatile, last updated 2026-07-29 (D142 -- P does NOT give a first descent; commensurability unexcluded)*

**The recurrent network has never contributed anything, and that explains everything else.** D130
ablated all recurrent connectivity (`genome.mag` zeroed, `tau_slow` retained) against intact networks on
paired genomes, across couplings 1x-4x and delays 50/200/400 ms. Where the task is solvable (50 ms) the
ABLATED network holds the cue at **1.000** and reads `quad` at 0.786-0.840 -- equal to or ABOVE intact;
the only significant `quad` difference anywhere is NEGATIVE, recurrence degrading it. Where passive decay
fails (200, 400 ms) the intact network fails identically, everything at ~0.50 in both arms at every
coupling. **There is no delay at which recurrence does something the isolated neurons do not.** The
substrate's entire working memory is single-neuron `tau_slow` leak.

**Consequence: D129's flat density sweep was a necessity, not a null.** P counts recurrent synapses;
those synapses do nothing; so P cannot matter. The study's independent variable is disconnected from the
computation it is meant to modulate. `loc_best` has sat at its measured noise floor in every condition of
every sweep -- a 45x P range, a 100x gain range, and now 3 couplings x 3 delays x ablation.

**THE SIGNAL DIES AT THE FIRST SYNAPSE, AND THAT IS ONE FACT BEHIND FIVE PRIOR NULLS (D133).** Driven
neurons carry the target at ~0.44; one hop out it is AT CHANCE, at every N from 8 to 100 and with or
without autapses. The synaptic INPUT to hop-1 neurons DOES carry signal (0.16-0.24, above chance), so
E/I cancellation is refuted -- the neuron's own transfer fails, `corr(input, output)` only 0.18-0.28.
Structural suspect, visible in the code: `drive[:, :n_in] = input_gain * E` amplifies external input 10x
while recurrent input is plain `W @ state` with NO gain, so downstream neurons never get the boost the
driven ones do.

**The fitness has always read a neuron at least one hop from the input.** That single fact accounts for
D124 (unselectable), D125 (`loc_best` at its noise floor), D129 (flat density sweep), D130 (recurrence
"contributes nothing" -- now reframed: recurrent synapses do not TRANSMIT at this operating point, so
whether recurrence would be useful was never testable), and the screen (`single` 0.054 vs `inputs`
0.475). Not five findings -- one, seen five ways.

**A lever exists, with an interior optimum, and the study sits on the dead side of it.** Sweeping w0 as a
multiplier on `w0_for_density` at N=50/n=3: `corr(in,out)` rises 0.211 -> 0.346 by w0x4, hop1 crosses
chance, and the DESIGNATED FITNESS CELL reaches 0.195 at w0x8 -- above chance for the first time since
D125. Past x8 recurrence swamps the external drive and the DRIVEN neurons degrade (hop0 0.426 -> 0.075
by x32). Narrow band; the study runs at w0x1.

**THE FITNESS READOUT CHANGED (D134 + amendment).** Fitness is now N independent HELD-OUT two-parameter
affine reads, one per neuron, aggregated as the MEAN PREDICTION -- not the mean of scores, which measured
0.114, BELOW chance, because ten driven cells get diluted among ninety at chance. Mean-of-predictions
reads 0.517. Weights are fixed at 1/N and never fitted, so D095's capacity bound is untouched.

**AND THEN D135 CLOSED THE LAST ROUTE.** Ablating recurrence IMPROVES driven-neuron integration: 0.542
ablated against 0.436-0.530 intact, monotonically worse as coupling rises across 16x. The fitness is
measuring passive leak exactly -- tau_slow=100ms covers ~2 of 8 segments and sqrt(2/8)=0.500 predicts the
observed 0.542. Worse, between-genome sd RISES with coupling (0.002 -> 0.104) while the mean falls, so
selection would grip variation in HOW MUCH RECURRENCE HURTS. With D133 (signal does not cross the first
synapse), every route by which P could matter is closed.

**D136 CLOSED THE PARAMETER SPACE.** `nmda_frac` x coupling: all 16 cells NEGATIVE (best -0.011,
several at |t| 3-7 in the negative direction). Across D129-D136 the swept space is `input_gain` 0.5-50,
coupling 0.25-8x, density 0.02-0.9, N 8-100, autapses, nmda_frac 0.5-0.98, four block architectures,
three task classes, two readouts. **No condition exists in which recurrent synapses contribute.** No
more parameters -- that was committed before the run and it holds.

**THE PROJECT HAS A NEW SUBSTRATE HYPOTHESIS, AND STEP 1 PASSED (D139).** From HetSyn
(arXiv 2508.11644): put the time constant on the SYNAPSE, not the membrane, so different inputs to the
SAME neuron have different memory spans -- a long-tau synapse carries "then", a short-tau synapse carries
"now", and the neuron is a coincidence detector. **That is the D128 conjunction, and our substrate could
not compute it because ONE `tau_slow` is shared by every synapse.**

Tested minimally: routing the probe into the fast current instead of sharing the slow one takes
match/non-match from **0.583 to 0.917 LINEARLY decodable** at a 400 ms delay (0.683 -> 0.950 at 200 ms).
It fails at 800 ms because tau_long was 500 ms -- a working range set by tau, which is why **tau must be
evolvable**, and the first failure mode in this project that is a parameter the study would sweep.
CAVEAT: hand-built, feedforward, routing GIVEN not discovered, one seed. It shows the mechanism EXISTS,
not that evolution finds it. **D132's retirement of DMTS is partially reversed** -- correct for one
shared timescale, false for per-synapse timescales.

**P IS REDEFINED: the number of independently tunable time constants** (synapses partitioned into P
groups, 1..|W|). HetSyn's Propositions 1-3 prove that axis is a nested hierarchy of published models
(vanilla LIF at P=1, neuron-level heterogeneity at P=N, full HetSyn at P=|W|). It counts parameters the
variance screen showed actually move fitness, unlike |W|.

**N DROPS FROM 100 TO 30, and this is the key tractability decision.** Two constraints: P must bracket
P_crit (~72-96 training trials), so |W| = density*N*(N-1) must exceed ~100 -- N=20 gives 114 (marginal),
**N=30 gives 261 (comfortable)**; and compute, where a full P-sweep costs **4 days at N=30 versus ~45
days at N=100.** N=100 makes the study impossible and was an unexamined inheritance from D131, whose
pair-split argument is satisfied at ANY N. Literature support: HetSyn's DMTS works at N=5, Yaqoob &
Wrobel at 3-4 interneurons, and Perez-Nieves chose 128 deliberately because at larger N the homogeneous
baseline nears ceiling and the heterogeneity effect becomes invisible -- **the ceiling argument cuts FOR
small N.**

**STEP 2 IS DONE (D140).** P-group implementation works: P current variables per neuron, synapses
assigned to groups, equations generated from P, and **P=2 reproduces the existing I_fast/I_slow structure
exactly** -- the current substrate is the P=2 point on the new axis. DMTS at 400 ms reaches **0.979** at
N=30. **N=24 and N=30 gave IDENTICAL results**, independent support for the sizing decision.

**But input DRIVE is a newly-discovered sensitive parameter:** the same network scores 0.521 at w=0.9 and
0.979 at w=0.3, because at high drive the cells saturate and both conditions squash together. It must be
FIXED before the sweep, not tuned after -- "adjust the weight and re-run" is the reactive-easing move
D136 closed the parameter space to prevent.

**D142: SWEPT PROPERLY, P DOES NOT PRODUCE A FIRST DESCENT.** With every condition given its own best
tau (4 seeds, delays [200,800]): **P=1 0.707 > P=3 0.662 > P=2 0.534.** Non-monotone with P=1 on top --
`P ~ m + 1` is REFUTED. D141's rising 0.495/0.509/0.690 came from HAND-PICKED taus; swept, P=1 goes
0.495 -> 0.707. **The apparent first descent was P=1 being handicapped** -- the same error the D139
amendment caught, recurring two entries later.

**What matters is tau MAGNITUDE, not tau COUNT.** tau=1600 ms is P=1's best and the long constant in all
four top P=3 rows: at 1600 ms the cue trace is 0.61 at the long delay and 0.88 at the short one, so the
amplitude difference nearly vanishes and one boundary works. Not spanning -- making the delays
irrelevant. P=2 is worst because it diverts half the cue synapses to the fast group and gains nothing;
the ordering 1 > 3 > 2 is what DRIVE-SPLITTING predicts, not timescale coverage.

**⚠ AND THE TABLE MAY BE A LATTICE ARTIFACT (PJM).** Delays [200,400,800] and taus [100..1600] are all
powers of two apart. Aliasing or ENTRAINMENT (tau_m=20 ms, 40 Hz input) could let the readout use PHASE
rather than trace amplitude. **Not excluded.**

**NEXT ACTION: `scripts/prototypes/hetsyn_phase_check.py --workers 6`** (~28 min, 96 jobs). Test (A) is
the cheap discriminator -- 400 vs 420 ms at a single delay: if a 5% delay change barely moves performance
the mechanism is amplitude, not phase. Test (B) re-runs the P ordering on incommensurate delays
(230, 370, 610) with taus off the powers-of-two lattice. **If the ordering changes, D142's table is an
artifact; if it holds, D142 stands.**

**AND THE LARGER FACT:** every condition in D142 is far below the **0.963** P=2 reached at a SINGLE fixed
delay. Variable delay costs ~0.25 at every P -- larger than any difference between P values. **The
delay-based task was adopted because it appeared to create demand for multiple timescales. It does not.
No first descent has been observed on any P definition in this project.**

**SUPERSEDED (kept for the record): `scripts/coupling_band_sweep.py`** at the study's real configuration (N=100, n_in=10),
finer resolution across x1..x16, 8 genomes, reporting the D095 fitness AND ITS RELIABILITY -- a mean
above chance is not a gradient (D115/D124). A tiny N=50 smoke run already returned "no overlap"
(w0x8: fitness 0.142, reliability 0.611, but hop0 down to 0.262), so the two curves may not overlap at
all. If they do not, the response is to change the READOUT (D127's all-neuron arm) or the input wiring,
not the operating point. **Then the actual GA arm on `accumulate` with the D134 readout** -- a
diagnostic, not another diagnostic, is what is owed next.

**DO NOT** resume D126's sweep sequence. A P-sweep whose fitness cannot read the task's discriminating
quantity would repeat D124 at far greater cost. **DO NOT** push `input_gain` past ~50: PR is already 1.31
there (one effective dimension) and the network is plausibly degenerating toward feedforward behaviour,
which is trivial to induce and useless to study (PJM).

**SCREEN EVERY CANDIDATE FITNESS AGAINST P.** D129 killed the `cos(delay, test)` scalar because it scored
0.961 at P=49 -- a 49-synapse network -- and stayed flat across a 45x range. It was reading stimulus
geometry, not network function. The D120 controls do NOT catch this: `omit_cue` and `scramble` both sit at
chance for it. Capacity-bounded is necessary but NOT sufficient; the readout's FORM must also be
task-agnostic, and `cos(delay, test)` *is* the DMTS comparison.

## §2. OPEN THREADS — *volatile*

- **Every headline result under the new encoding must replicate across >=3 independent xi draws** (D131).
  If a P-curve's shape changes with xi, the shared scaffold is doing hidden work and the finding does not
  stand.
- **If the band exists, D124/D129/D130 must be RE-RUN in it** before any of them is trusted as a
  statement about this substrate; all three were run at w0x1, where nothing crosses the first synapse.
- **`readout_window_ms = 60` exceeds `present_ms = 50`.** Every stage sample carries 10 ms of its
  predecessor -- inherited from the era when `present_ms` was 150. Affects every trial-task measurement,
  not just these checks. Needs a deliberate value and its own entry, not a quiet edit.
- **Developed condition at the PROBE stage is unmeasured.** CHECK 2e ran undeveloped only.
- **The input-neuron localisation check is unrun**: decode the relation from neurons 0-9 alone at probe.
  Absent there means saturation eats it at entry; present there but absent downstream means the
  recurrent network discards it.
- **D127 localization is BUILT but UNRUN end-to-end.** `trial_eval.localization_report` on the
  `report_fn` hook, `trial_selection_run.post_arm_localization` over the final population. Metric logic
  verified against synthetic states of known concentration; the network path has never executed (no
  Brian2 in the authoring sandbox). Eyeball the `loc_*` keys on the first real arm before any sweep
  depends on them. NOTE: D127's pre-registered PR formula was WRONG (referenced theoretical chance, not
  the measured null) and was corrected before any data — see the D127 amendment.
- **`trial_allneuron_probe.py` carries a mislabel**: its `single(n0)` column reads state column 0, an
  INPUT neuron, not the fitness cell (outputs are the LAST d units). D125's conclusion is unaffected —
  it rests on the all-neuron distribution — but fix or retire the script before running it again.
- **Parallel mean-selected arm** (D127): committed design, NOT part of sweep one. Trigger is fixed —
  run it iff sweep one produces a peak meeting D126's criterion.
- **⚠ UNTESTED LEAD, recorded because it exists nowhere else: DEVELOPMENT MAY DESTROY THE HELD CUE.** A
  2026-07-24 sandbox run (frozen chat, never committed, never memorialised) reported cue decode ~1.00
  undeveloped falling to ~0.45 after development on the RETIRED task, with competition ruled out as the
  cause. Provenance is weak — reconstruction sandbox, stubbed `tasks.py`, old task, never verified
  against committed code — so treat it as a lead, not a finding. But it is consistent with D124
  (development a headwind) and D125 (undeveloped carried more signal than developed in both random
  bases), and it is the observation that most directly predicts whether ANY task change can work.
  `delay_persistence_probe.persistence_contrast()` now measures it; it has NOT been run.
- **Task-family parameterization** — variable-delay sampling and an optional in-delay distractor, so
  D126's rungs are config rows rather than separate code paths. Small, and owed before rung 1.
- **`behave_batch` is stale relative to D103** (omits `I_wta` and the eSTDP synapses) and dormant — it is
  called only by `verify_batch_equivalence`, never by `run_evolution`. Do NOT wire it into the GA or
  revive it as a speedup until it is brought up to the D103 substrate and re-passes equivalence at the
  real operating point. D123 was skipped, so this follow-up currently has no number.
- **`mean_exc` 0.80→0.64** over 40 generations — the one non-null. Selection gripped something heritable
  that was not task performance. Logged as an untested lead (SE not computed), reconnects to H-Cv2.
- **Suspected readout overfitting at small `n_val`** — inferred from n_val-nonmonotonicity, never tested
  directly. A clean check is in-sample vs held-out affine scoring.
- **RL-in-development** — set aside deliberately, not refuted. Biologically well-justified on its own
  merits (organismal development includes reinforcement), but adopting it to escape a null is the move
  the framework guards against, and "partial reward" has no principled setting, which manufactures a
  confound at the centre of the measurement. Revisit as a deliberate design choice, never as a rescue.

---

## §3. THE FRAME — *stable; full statement in FRAMING.md §0 and HYPOTHESIS_LOG*

Not "test Frank in a spiking network." **Map a repertoire of learning behaviours in spiking networks
under varying constraints and stimuli.** Frank's insight — that the parameter axis is where to look — is
the INSTRUMENT; double descent is the DIAGNOSTIC, not the phenomenon. **Regularization ≠ regulation:**
regularization prevents overfitting (abundant literature); regulation is a level that modulates another
level (origin unexplained). The constructive question is why a regulatory hierarchy evolved, with
encoding saturation as the candidate answer — under which the second descent *is* the emergence of a new
functional level. Read `FRAMING.md` for the full statement and `HYPOTHESIS_LOG.md` for H-A…H-D as
pre-registered claims with their revision history. Do not restate them here.

Two design constraints, both already committed, that govern everything downstream:

- **The two-failure-mode frame** (FRAMING §Task design). A flat error-vs-P curve is ambiguous: TOO HARD
  (no gen-0 gradient, unselectable) or TOO SIMPLE (P_crit below the operational range, no interpolation
  peak). Good task design threads between them.
- **Do not assume the peak exists.** The ML literature and both outside advisors reason as though P_crit
  sits somewhere on the axis and only its location is in question. For this project that IS the driving
  question. Dimensioning a task to *position* a peak is premature until a peak has been *observed* on
  some selectable task.

## §4. WHAT IS CLOSED — *semi-stable; append when a branch closes*

Recorded so no future turn re-opens them by accident. Each is closed by evidence, not by preference.

- The **covariance-context task** (retired, D120): context was ~99% inferable from a single stimulus, so
  nothing had to be held, and its "matched control" shuffled stimulus order, which removes nothing.
  Context use had never been validly measured before D120.
- **Tuning-level levers on `trial_xor`** (D124): fitness basis, delay, assay count, development on/off.
- **The all-neuron-aggregate arm** (D125): no gen-0 toehold at any of 50 neurons.
- **The clock-offset explanation** for the old task's flatness (D121): falsified on re-measurement.
- The RC-era **skill gate** and the **"5× supercritical" framing** (D118/D119).

## §5. NUMBERS THAT ARE NOT WHAT THEY LOOK LIKE — *stable; this section earns its keep*

- **evolved `val_acc` reliability ≈ 0.53 at n=20** — an artifact. In-sample affine-readout overfitting at
  small `n_val`; it vanishes at n_val=40/80, which is backwards for real signal. Withdrawn in D124.
- **random/undeveloped `val_acc` `single(n0)` ≈ 0.41** — not a finding. Inconsistent across conditions
  (0.206 developed, 0.000 evolved), wide ICC error bars at G=30, and one percentage point of spread on a
  scale where chance is 0.5. Same shape as the number above. Do not promote it.
- **D109's heritability r = 0.29** — withdrawn (D115): never significant at n=30, and measured at
  fitness reliability ≈ 0.05.
- **`best(all)` across neurons** — always looks impressive, always a lottery. Max-over-N rises with
  in-degree at fixed N and has no between-genome consistency. Read `mean`, not `max`.
- **Any developed-phenotype result predating D121** — invalid (stimuli were time-shifted).
  Undeveloped/birth-scored numbers are unaffected.
- **Any test-error number from a run between D094 and D113** — void (fitness was computed from test
  error, so selection optimized the reported generalization).
- **The operating-point conclusions of D129, D130, D135 and D136** — their MEASUREMENTS stand, but each
  swept a one-dimensional diagonal (`w0` scales coupling mean and variance together) through a
  two-dimensional space whose directions have opposite requirements. Correct statement: *along the `w0`
  diagonal*, no operating point supports recurrent contribution. Not a statement about the substrate.
- **Any "recurrence contributes" claim from a difference test alone** — a difference between two
  chance-level values is noise, not a contribution (D130 flagged +0.040 between 0.523 and 0.483, both at
  chance). STANDING RULE: a difference test is meaningful only when at least one arm clears its own null.
- **`cos`/`corr`/`eucl` self-referential scalars** — NOT fitness candidates (D129). 0.961 at P=49, flat
  across a 45x P range: they read stimulus geometry at the input neurons, not network function. They
  pass `omit_cue` and `scramble`, so the D120 controls do not catch them.
- **`PR_state ~ 7`** — a property of `input_gain = 10`, not of the network (D129). It runs 25.8 at gain
  0.5 and 1.31 at gain 50. D075's `PR_mean ~ 7` was measuring the regime.
- **Any "clears its null" claim from a bare `>` comparison** — not a test (D129). Requires exceeding the
  null by more than ~2 across-genome sds; the unguarded rule flagged 0.555 against 0.554.

## §6. STANDING RULES — *stable; each was earned by a specific failure*

- **Validate that code MEASURES WHAT IT CLAIMS, not just that it executes.** The audit found seven silent
  defects by reading, not running. Run `preflight.py` / `audit.py` before anything expensive.
- **Before sweeping a parameter, ask what quantities it moves and whether they need to move together.**
  `w0` looked like the coupling knob; it was a diagonal through (mean, variance), which control the
  network timescale and the chaos boundary respectively and must move in OPPOSITE directions. Four
  entries reported that diagonal's shape as the substrate's. A parameter is not an axis.
- **Diagnostic code that produces a number entering DECISIONS is committed IN THE SAME COMMIT as the
  entry.** Most of the 2026-07-29 session's decisive measurements ran from /tmp and were irreproducible
  until the end of the day: the f-I gain that corrected D138, the J_eff sweep, the aggregation comparison
  behind D134's amendment, step 1, the P-group prototype. An entry citing a number nobody can regenerate
  is a claim without evidence. See `scripts/prototypes/`.
- **Sweep every arm, including the one you expect to lose.** A baseline must be granted its best
  configuration before any margin over it is claimed. Established in the D139 amendment (P=1's 0.583
  became 0.850 when swept), restated in D141's for P=3, and STILL not applied to P=1 until D142 -- where
  P=1 went 0.495 -> 0.707 and reversed the entire ordering.
- **Size the architecture from the axis you intend to sweep and the compute you actually have.** N=100
  came from D131's pair-split argument, which is satisfied at ANY N, and survived unexamined into a
  regime where it makes a P-sweep cost 45 days instead of 4. Re-derive N whenever the axis or the
  question changes.
- **Ablate the mechanism before sweeping its parameter.** D130 answered in one run what three parameter
  sweeps could not: the recurrent network contributes nothing, so P — which counts recurrent synapses —
  could never have mattered. A sweep can only tell you a parameter does not move the outcome; an
  ablation tells you whether the thing it parameterises is participating at all.
- **A difference test needs a chance-level precondition.** Only compare arms when at least one clears
  its own null. Earned three times over: a bare `>` (0.555 vs 0.554), a hardcoded 0.05 threshold
  (+0.047 at n=3), and a correctly-thresholded paired t applied to two chance-level values.
- **Reliability before science.** Selection cannot work on a fitness whose between-genome signal is below
  its measurement noise (D115). One ~6 h diagnostic replaced a 40-generation arm that would have failed.
- **Compute the SE before calling a number a finding**, and check it survives more power (D115).
- **Measure per-generation time before believing any projection.** Four-plus runtime estimates in a row
  were wrong.
- **Search AND let the result constrain the implementation.** This rule has bitten six times, most
  memorably D075's 16× charge error, implemented straight past a warning that predicted it.
- **Equivalence-check before trusting any speedup.** This project's should-be-fines have twice been bugs.
- **A trustworthy zero point is worth a task redesign** (D116 → D120).
- **Any run over a few minutes must print progress, an ETA, and its parallelism state** (D066) — and
  watch the process count, not just the wall clock (D065: a silently serial pool looks like slow code).
- **Do not pick a lever reactively off a null.** Choose the fixed point once, up front, and write down
  why, before seeing the curve. Reactive easing is a curriculum in disguise and invalidates the P-curve.
- **`noise_sigma` is NEVER a gene** — it is H-D's treatment variable (D059).

## §7. ORIENTATION — *stable*

Repo is ground truth: `DECISIONS.md` (the claim log, strict `### D001`…), `HYPOTHESIS_LOG.md`
(pre-registered predictions + revision history), `FRAMING.md` (the frame and the task-design criteria),
`BRIDGE.md` (abstraction → measurement chain), `LAB_NOTEBOOK.md` (running narrative), `REFERENCES.md`.
Code in `ddescent/`, runnable probes and runners in `scripts/`, all outputs under `runs/` (tracked;
only bulk `.pkl`/`.npy`/`.parquet` are gitignored, so large checkpoints exist locally only).

Convention in the logs: **H:** = the human / PI, credited as **PJM** for design calls. **A:** = the
assistant. `QUEUE.md` was deleted 2026-07-25 as stale and superfluous; its role is now §1–§2 here.
