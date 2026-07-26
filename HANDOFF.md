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

## §1. STATE — the one-paragraph read  ·  *volatile, last updated 2026-07-25 (D128 -- the conjunction exists)*

**The conjunction exists, and the fitness has been looking in the wrong place for it.** D128 is the
turn: second-order decode of match/non-match reads **0.783 at the PROBE segment** (null 0.539, sd 0.014
over 3 genomes) and **0.524 at the READ segment**, where `response_rows()` samples. The signal is
sustained across the probe window, not transient, and it is available only to a QUADRATIC readout --
linear decode at probe is 0.479, chance. So the flat results of D124 and D125 are now mechanically
explained by two separable faults: a **TIMING** error (the fitness samples ~50 ms after the information
has decayed) and an **ORDER** mismatch (the relation is quadratic in the rates; D095's readout is a
two-parameter affine). Neither is "the substrate cannot bind." Upstream of both, the substrate is
healthy: the cue is held at ~1.00 through every stage, undeveloped and developed alike (D128 / CHECK 2c),
so memory and encoding are not the problem and development is not the blocker.

**WHY THE RELATION IS SECOND-ORDER (structural, not incidental).** Cue and probe enter through the SAME
ten input neurons -- the architecture has one environment pathway -- so role is carried by timing alone.
Match puts `(a+b, 0)` in the pattern basis, non-match `(a, b)`: not linearly separable, and the only
discriminating features are the norm and the cross term, both quadratic. `state` is additionally a 60 ms
mean of a 5 ms-sampled rate trace, so spike timing and synchrony are averaged away and rate structure is
the sole remaining channel.

**NEXT ACTION.** The operating point (D119), untouched since it was recorded as a live lever. Under the
reservoir premise the network should convert a conjunction into a rate difference a linear reader can
see; D128 shows the conjunction forms and that conversion does not happen. `input_gain = 10.0` is
annotated in the config as "the useful regime; NOT the PR-optimal one," and D075 measured `PR_mean ~ 7`
of 50 -- a network operating close to linearly. If the input neurons saturate, doubled drive yields the
same rate as single drive and the amplitude channel is shut at entry. **The decisive cheap test: sweep
`input_gain` and measure whether the relation becomes LINEARLY decodable at the probe stage.**
Undeveloped, no `develop()` calls, minutes. Also owed and NOT yet done: the developed condition at the
probe stage (CHECK 2e ran undeveloped only), and a decision on `readout_window_ms=60` against
`present_ms=50`.

**DO NOT** resume D126's sweep sequence until the order problem is resolved. A P-sweep whose fitness
cannot read the task's discriminating quantity would repeat D124 at far greater cost.

## §2. OPEN THREADS — *volatile*

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

## §6. STANDING RULES — *stable; each was earned by a specific failure*

- **Validate that code MEASURES WHAT IT CLAIMS, not just that it executes.** The audit found seven silent
  defects by reading, not running. Run `preflight.py` / `audit.py` before anything expensive.
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
