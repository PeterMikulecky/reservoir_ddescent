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

## §0. MAINTENANCE — how to keep this cheap to update

Only **§1 and §2 are volatile.** They are short by design: update them at every memorialization (i.e.
whenever a `### D` entry is written), which makes updating a two-minute edit rather than a rewrite.
§3–§6 change rarely — when a standing rule is earned, a lever is closed, or an artifact is identified.

**The rule: a DECISIONS entry and a §1/§2 refresh land in the same commit.** If §1 disagrees with the
newest `### D` entry, the D entry wins and this file is stale — say so rather than trusting it.

---

## §1. STATE — the one-paragraph read  ·  *volatile, last updated 2026-07-25 (D127)*

The trial task is built, correct, and **unselectable**. The `cue→delay→probe` XOR task (D120) works
exactly as designed — chance floor by construction, controls that remove what they claim, clock-aligned
assays (D121), a GA driver that runs it end to end (D122). But a well-powered reliability investigation
(D124) found no selectable gradient anywhere in it: forty generations flat, evolved indistinguishable
from random, and every lever that leaves P's meaning intact — fitness basis (five tried), delay
(0/50/100 ms), assay count, development on/off — falsified. The last surviving alternative was that this
was an artifact of scoring one arbitrary neuron; **D125 tested and rejected it** — no neuron among 50
carries the task in an unselected population, so the all-neuron-aggregate arm is ruled out. The
diagnosis is now task-design, not measurement and not the plasticity rule: `trial_xor`'s target is
arbitrary by construction, hence orthogonal to every dynamics-native property an E/I reservoir produces,
and unsupervised development is target-blind. **H-A…H-D are not refuted; they are BLOCKED on
selectability**, because no error-vs-P curve can be measured while selection has no gradient to follow.

**THE PATH FORWARD IS DECIDED AND PRE-REGISTERED (D126).** `trial_xor` is replaced by **DMTS
(match / non-match)** via a **shared cue/probe pattern set** — one line in `cue_delay_probe`, which
turns the existing target into a natural relation the substrate can compute as trace overlap. The
chance floor survives by construction, and the controls, trial structure, D095 readout and GA driver
are untouched. D126 also pre-registers the complexity axis (plain → variable delay → K≥4 → distractor),
the triggers for moving up it, the sweep design (`n_seeds` = 5, staged, with a per-seed consistency
requirement on any peak), and the read of every outcome. Rung 1's numeric dimensioning is deliberately
left open, to be set from calibration data — reliability and low-P solvability — never from a curve.

**NEXT ACTION — execute D126's sequence, each step gating the next.** (1) **Task-construction half
DONE** (D126 amendment): `shared_patterns=True` ships, rung 0's floor is verified held-out over 20 seeds
(cue-only 0.4996, probe-only 0.5000, constant 0.500, joint 1.000; match trials have <cue,probe>=1.0), and
a correction was made — the (cue,probe) type grid loses the floor for `n_cues>2`, so the family is now
relation-balanced. **Still owed on step 1: the network-level controls** — `omit_cue` and `scramble` on a
developed net plus the leakage check. The oracle cannot test `omit_cue` at all (blanking the cue stimulus
leaves the cue INDEX intact), so it is network-level by nature. (2) `trial_reliability_probe` at
rung 0, n=30 — is there a gen-0 gradient? Hours, not overnight. (3) The **low-P solvability screen** —
a few arms at the bottom of the P range only, NOT a sweep; answers "too simple?" cheaply and measures
the arm-to-arm SD that sets `n_seeds`. (4) Dimension rung 1 from (2)+(3), probe it, lock both. (5) Sweep
one rung. Also owed alongside the edit: parameterize variable-delay sampling and an optional in-delay
distractor so the rungs are config rows rather than code paths, and add the **mild firing-rate penalty**
to fitness (`mean_exc` drifting 0.80→0.64 was the only thing selection gripped, and nothing currently
penalizes a degenerate rate regime).

## §2. OPEN THREADS — *volatile*

- **Network-level controls on DMTS not yet run** — `omit_cue`, `scramble`, leakage, on a developed net.
  Gates the reliability probe; nothing about the network has been measured on DMTS.
- **The D127 localization measurement is DECIDED but NOT BUILT.** All-neuron scoring, PR + its
  scrambled-target null, on the `report_fn` hook and post-arm in the runner. Must ship before sweep one —
  retrofitting means re-running arms. Touches `trial_eval.py` and `trial_selection_run.py`; end-to-end
  verification needs Brian2, so the real check is a short run on PJM's machine.
- **Parallel mean-selected arm** (D127): committed design, NOT part of sweep one. Trigger is fixed —
  run it iff sweep one produces a peak meeting D126's criterion.
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
