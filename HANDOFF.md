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

## §1. STATE — the one-paragraph read  ·  *volatile, last updated 2026-07-26 (D132 -- task class changes)*

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

**THE ENCODING REDESIGN FAILED, AND THE SUBSTRATE IS NOT THE PROBLEM (D132).** The structured block
genome was built and its invariants pass (P_syn fixed, no dead units, unseeded prior). The engineered
ceiling VALIDATES at nmda 0.7 (selectivity 4.29 at 100 ms -> 1.69 at 600 ms), so persistent activity is
achievable here. But across four architectures -- random blocks, clustered, clustered + shared inhibitory
pool, and + cue-selective input routing -- recurrence never helped the relation, and the last and most
ceiling-like architecture made it strictly WORSE (negative in all 15 cells, monotone in routing strength,
across 3 xi draws). Mechanism: cue-selective clusters encode WHICH CUE, which is identical on match and
non-match trials, so the attractor injects variance orthogonal to the relation.

**The conceptual error was upstream of all four: attractors solve MEMORY, and the task's bottleneck is
COMPARISON.** At delay=1 leak already holds the cue at 1.000; no memory is needed. **Both retired tasks
demanded a CONJUNCTION, which is second-order in rates, and this substrate has no native second-order
operation** -- confirmed a third way in the screen's own check, where even a perfect integrator scores
0.099 on DMTS. That is why D126's swap did not help: it made the target grounded but left it
second-order. E1 is NOT refuted and D131's step-4 stop does NOT fire: the four architectures were
hand-designed by A, each failure followed by finding another component in the known-positive's source.

**NEXT ACTION: run the task screen.** `scripts/task_screen.py` tests the two properties that killed
everything so far, on random undeveloped genomes: (a) gen-0 between-genome fitness variance above
measurement noise (D115 machinery), and (b) does ablating recurrence destroy performance. A task passes
only if BOTH hold. Candidates are **accumulate** (independent evidence per segment, target is the total
-- a perfect integrator scores 1.000, a leak-only reader 0.336) and **delayed** (amplitude held past
tau_slow -- 1.000 vs 0.000), with **dmts as the known-NEGATIVE control** that should fail. N is a
variable in the screen: "this substrate cannot" and "this substrate at N=100 cannot" are different
claims and only the second has been tested.

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
