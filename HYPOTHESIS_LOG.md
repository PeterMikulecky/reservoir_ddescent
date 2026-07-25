# HYPOTHESIS LOG — pre-registration and revision history

**Purpose.** This file memorializes the project's driving hypotheses AS PREDICTIONS, with a versioned
revision history. It is distinct from DECISIONS.md: DECISIONS records *what we did and found*
(chronological, methodological); this file records *what we predicted and how the predictions evolved
in response to evidence*. The point is pre-registration discipline — so that when we eventually report an
outcome, the path from original prediction → evidence → revised prediction is legible, and no mid-study
update can be mistaken for a prediction made from the start. Original hypothesis text is preserved
VERBATIM in its original strong (falsifiable) form; revisions are appended, never overwritten.

**Status conventions.** Each hypothesis version carries a status: PRE-REGISTERED (stated before the
relevant evidence), PROVISIONAL (advanced mid-study on partial evidence, not yet validated), SUPPORTED,
REFUTED, or SUPERSEDED (revised into a later version — but retained in the record). A superseded
hypothesis is NOT deleted and NOT declared "wrong" unless evidence refutes it; superseding a hypothesis
records that a revised version has been advanced, while keeping the original live until validation tests
adjudicate.

---

## The driving question (v1, PRE-REGISTERED)
Where does neural learning sit on the double-descent map — and does a biologically-structured spiking
network show the framework's signature (a peak, a second descent tied to a modulating level) at all?
Double descent is treated as a DIAGNOSTIC (a way to read transitions between kinds of learning), not the
phenomenon of interest itself. The deliverable is the map, not a yes/no.
*(Status: PRE-REGISTERED. Not revised by the 2026-07-22 turn — the turn revises H-C, the mechanism
underneath, not the comparative-map framing. See H-C revision below for how the mechanism shifted.)*

---

## H-A — a peak exists
**v1 (PRE-REGISTERED).** Generalization error vs a principled parameter count P has a peak at some P*.
(Does the error-vs-P curve even have the classic double-descent shape?)
- **Status: PRE-REGISTERED, measurement rebuilt (not revised as a claim).** The 2026-07-22 turn (D110)
  showed our error axis had been measured with a LINEAR readout, which the reframe says structurally
  mismeasures a distributed/nonlinear substrate — so any peak would have been buried in decoder-artifact
  noise. The CLAIM stands; the MEASUREMENT is rebuilt to a nonlinear (regulation) readout. First
  genuinely clean test of H-A becomes possible only after that rebuild.

## H-B — the peak tracks STRUCTURE, not data count
**v1 (PRE-REGISTERED).** The interpolation peak sits at r₁ (the size/rank of the shared generative
structure of the environments), NOT at the point where parameters match the number of training examples.
This is the prediction that distinguishes the structured-biology account from vanilla ML.
- **Status: PRE-REGISTERED, unrevised, possibly strengthened.** The reframe doesn't touch the r₁ logic; a
  regulation readout may make H-B MORE cleanly testable (regulation is sensitive to exactly the shared
  structure r₁ indexes). Confirmed in code that r₁ and n_env are independently manipulable (see DECISIONS).

## H-C — descent needs a modulating level  [REVISED → H-Cv2]
**v1 (PRE-REGISTERED — preserved verbatim as the original strong prediction).**
> Past the interpolation peak, generalization error descends again only if structure emerges that
> MODULATES rather than DRIVES. Specifically: the first descent builds ENCODING structure (the network
> learns to represent its input); encoding then SATURATES; and the second descent corresponds to the
> EMERGENCE, ATOP the encoding, of a REGULATORY / context-modulating level — a second level that gates or
> modulates the encoding level. The ordering is a ladder: encoding first (easier, foundational),
> regulation second (harder, emergent capstone). No modulating level → no second descent.

**Evidence that forced revision (2026-07-22 turn; DECISIONS D108–D110):**
- D108: a well-powered dev×selection sweep was FLAT — no climbing on aggregate fitness at any setting.
- D109: heritability probe — aggregate FITNESS is non-heritable (r≈0, both comp on/off), but the
  REGULATION component IS heritable (r≈0.29, replicated). Selection on aggregate fitness is selectionist,
  not Darwinian; the heritable structure lives specifically in regulation.
- D110: the developed state's context is NONLINEARLY decodable (random forest ≈0.60–0.69 vs 0.25 chance)
  where LINEAR/covariance decoders found chance. Prior "encoding at floor / context not decodable" results
  were DECODER-FORMAT ARTIFACTS — the information was present all along, in distributed/nonlinear form.
- Three consilient supports for the reframe (D109): the heritability dissociation (retrodicted, not
  designed for); deep-learning nets natively find distributed/nonlinear solutions (clean linear encoding
  is not what successful learners build); biology's clean linear encoders (topographic maps, tonotopy)
  are STRUCTURALLY SPECIFIED by afferent wiring, NOT self-organized from recurrent dynamics.

**What specifically was wrong in v1:** the DIFFICULTY ORDERING and the EMERGENCE framing. v1 assumed
encoding is the easy foundation and regulation is the hard emergent capstone built atop it. The evidence
inverts this: the substrate represents context in distributed/nonlinear form FROM THE START (regulation is
NATIVE), while clean linear encoding is the HARD, ordered special case that recurrent dynamics do not
spontaneously produce (it requires training, as in deep nets, or structural specification, as in bio
maps). So regulation does not EMERGE atop a pre-built encoding level — it is present natively; encoding-as-
we-were-measuring-it was never the foundation the ladder assumed.

**H-Cv2 (PROVISIONAL — advanced 2026-07-22 on the D108–D110 evidence; NOT yet validated).**
> The modulating (regulatory) level is NATIVE to the substrate — distributed, nonlinear, fluctuating
> dynamics carry context-dependent structure from the outset (nonlinear-decodable well above chance in an
> untrained random network). Therefore the second descent corresponds NOT to the EMERGENCE of a modulating
> level but to its REFINEMENT: the sharpening of natively-distributed regulatory structure into a more
> usable, more separable, more reliably-transmitted (heritable) form as P increases and under selection.
> The double-descent second descent is a refinement curve of a native competence, not the appearance of a
> new one. Measured through a NONLINEAR regulation readout (a linear readout structurally mismeasures it).

**What H-Cv2 predicts (testable, and what would distinguish it from H-C v1):**
- Under a nonlinear regulation readout, error-vs-P should show structure that the linear readout hid
  (distinguishes v2 from v1: v1 predicts nothing special about readout nonlinearity).
- Nonlinear-decodability of context should be ABOVE CHANCE even at LOW P / no selection (native), and
  should CLIMB with P/selection (refinement). v1 predicts it should be near-floor until the modulating
  level emerges at high P.
- Regulation should be more heritable / more selectable than aggregate fitness or encoding (v1 predicts
  regulation is the hard, late, emergent thing — the opposite).
- The linear-vs-nonlinear decodability GAP as a function of P is a discriminating signature (does
  refinement make the representation more linearly accessible, or does it stay distributed?).

**Status: H-C v1 SUPERSEDED (retained, NOT refuted); H-Cv2 PROVISIONAL.** v1 and v2 are NOT cleanly
mutually exclusive — the shift is specifically about the difficulty ordering and emergence-vs-refinement,
not a wholesale replacement. A hybrid remains possible (native-but-crude regulation → refined), which
would be a milder revision of v1 rather than the full inversion. H-Cv2 is advanced on strong but
UNVALIDATED evidence; it is GATED on two confirmatory tests before promotion to SUPPORTED:
  1. The REVERSAL TEST — does encoding-selection evolve WORSE (lower heritability, less climbing) than
     regulation-selection? (v2 predicts yes; v1 predicts no / opposite.)
  2. The REGULATION RANGE-ARTIFACT CONTROL — is regulation's higher heritability a depth fact, or an
     artifact of regulation varying less (smaller SD) than fitness, leaving less range for mutation to
     disrupt? Must be ruled out.
Until both clear, H-C v1 remains LIVE as the alternative the tests could rescue.

## H-D — the spiking test
**v1 (PRE-REGISTERED).** No fluctuation-driven dynamical regime → no second descent. A modulating/gain
mechanism requires the fluctuation-driven regime, which only a spiking substrate can enter and test; an
internal on/off switch of that regime is the crux.
- **Status: PRE-REGISTERED, unrevised, possibly reinforced.** The reframe is BUILT on distributed
  fluctuating dynamics being the substrate's native computational mode; D110's nonlinear-decodability is
  evidence the fluctuation-driven regime carries the computation. Consistent with and supportive of H-D.

---

## CORRECTION (2026-07-22, D112) — affects H-Cv2's evidential basis, not its content

**What was found.** "Encoding" and "regulation" as implemented are the SAME measurement offset by a
constant: encoding = 1.0 − test_err, regulation = floor − test_err (floor = 1.014), so
regulation ≡ encoding + 0.014, perfectly correlated over the operating range. They are not separable
components.

**Consequence for the H-C → H-Cv2 revision.** The revision cited four supports. Support #1 (the D109
heritability dissociation) was stated as "regulation is heritable, aggregate fitness/encoding is not." That
comparison was never actually run: the probe compared HYBRID fitness against REGULATION, and since
regulation ≡ encoding + const their heritabilities are necessarily identical. **Restated correctly, the
D109 dissociation is: pure test-error-based PERFORMANCE (r≈0.29) vs HYBRID fitness (r≈0.03), implicating
`carrying` — the covariance-decay memory measure, the only genuinely distinct component — as the source of
non-heritability.**

Supports #2 (deep networks natively find distributed solutions), #3 (biology's clean linear encoders are
structurally specified rather than emergent) and #4 (D110: context nonlinearly but not linearly decodable)
are independent of this error and stand unchanged.

**Status of H-Cv2 after the correction: STILL PROVISIONAL, not refuted, but with one leg reinterpreted.**
Its "encoding is a hard ordered target while regulation is native" phrasing leaned on a component
distinction that does not exist in the implementation. The underlying claim — that the substrate natively
carries distributed context structure, and the second descent is REFINEMENT rather than EMERGENCE — rests
on supports #2–#4 and is unaffected. **But note H-Cv2 can no longer be tested by comparing the
enc/reg components**, because they are the same quantity; its discriminating predictions must be evaluated
on decodability, structural descriptors, and the fitness-vs-P curve instead.

**Related design decision (D112).** The enc/car/reg decomposition is COLLAPSED for selection purposes: the
D094 three-term fitness was itself an a priori engineering hypothesis about how the network ought to solve
the task (encoding → carrying → regulation atop it), which is the same imposition the reframe rejects.
Selection now uses a single performance scalar (floor − test_err); the components are retained as
post-hoc DIAGNOSTICS. This also means the discriminating tests for H-Cv2 vs H-C v1 shift toward "analyse
what the evolved networks actually built, and how it changed with P" rather than "which pre-defined
component climbed."

**SECOND CORRECTION (2026-07-23, D115) — the heritability leg is WITHDRAWN, not merely restated.**
D112 restated support #1 as "performance vs carrying." D115 goes further and withdraws it entirely: at
n=30 the SE of a correlation is 0.192, so D109's regulation heritability r=0.29 sits 1.5 SE from zero
(p≈0.13) and is **not significantly different from zero, nor from the fitness r=0.03 it was contrasted
with.** There was never a measured heritability dissociation. Compounding this, D115 showed fitness
reliability at n_assays=1 is ≈0.05 — so D109's measurements were taken on an essentially unreliable
signal in the first place.

**H-Cv2's remaining support: #2 (deep networks natively find distributed solutions), #3 (biology's clean
linear encoders are structurally specified rather than emergent), #4 (D110 nonlinear decodability — a
LARGE effect: RF 0.60–0.69 vs 0.25 chance, and the only one of the four that is statistically robust).**
H-Cv2 is therefore NOT refuted, but it now rests on one empirical result plus two arguments from the
literature. Its status remains PROVISIONAL, with a weaker evidential base than when it was advanced.

---

## Revision history (chronological)
- **2026-07-22** — H-C v1 → H-Cv2 (difficulty ordering inverted: regulation native, encoding the hard
  ordered case; second descent = refinement not emergence). Forced by DECISIONS D108–D110. H-Cv2
  PROVISIONAL, gated on the reversal test + range-artifact control. H-A measurement rebuilt (nonlinear
  readout) without revising the claim. Driving question, H-B, H-D unrevised.
- **2026-07-22 (correction, D112)** — encoding ≡ regulation + const discovered; H-Cv2 support #1 restated
  (dissociation is performance-vs-carrying, not regulation-vs-encoding). H-Cv2 remains PROVISIONAL on
  supports #2–#4. enc/car/reg decomposition collapsed for selection; components retained as diagnostics.
  H-Cv2's discriminating tests move to decodability / structural descriptors / the fitness-vs-P curve.
- **2026-07-23 (correction, D115)** — heritability leg of H-Cv2 WITHDRAWN: D109's r=0.29 was never
  significant at n=30 (SE=0.192, p≈0.13), and fitness reliability at n_assays=1 is ≈0.05, so the
  measurement was unreliable regardless. H-Cv2 now rests on D110 plus two literature arguments.
  Standing rule added: compute the SE before calling a correlation a finding.


  ## SELECTABILITY (precondition for H-A..H-D on the trial task) — advanced then REFUTED

**Context.** This is not one of the driving H-A..H-D; it is a PRECONDITION for testing any of them on
the D120 trial task. Frank's whole analogy assumes selection can act; if the trial_xor fitness carries
no selectable gradient, no error-vs-P curve can be measured and H-A..H-D are untestable on this task.
The 2026-07-24/25 reliability investigation advanced a working prediction about that precondition and
then refuted it. Recorded here per the pre-registration discipline so the advance→refute path is legible.

**S1 (PROVISIONAL — advanced 2026-07-24 on partial, later-discredited evidence).**
> The trial_xor fitness has no gen-0 gradient BY CONSTRUCTION (the XOR floor puts every random genome at
> chance), but it is "SELECTABLE ONCE MOVING": once a few generations of selection give the population
> genuine skill variance, the fitness estimate distinguishes genomes and selection accelerates
> (slow-start-then-climb). Evidence at advancement: an n=20 evolved population showed val_acc reliability
> ~0.53 vs ~0.22 for random.

**Evidence that REFUTED it (2026-07-25 overnight; DECISIONS D124; runs/reliability/ two n=30 logs):**
- **The advancing evidence was an artifact.** The n=20 ~0.53 did not survive n=30 with the full n_val
  sweep. It was in-sample affine-readout OVERFITTING at small n_val: signal appears at n_val=20 and
  VANISHES at n_val=40/80 (backwards for real signal — more trials should reveal more). At the honest
  n_val=80, evolved val_acc reliability is ~0.00 (developed) / ~0.20 (undeveloped) — i.e. NOT above
  random (~0.15). Same D115 lesson, re-learned: check that a number survives more power before calling it.
- **The 40-generation trajectory is FLAT.** best_test bounces ~0.88–1.00 with no trend; fit_mean sits at
  ~+0.012 from gen 0 to gen 39. Forty generations of selection produced no performance climb. This is
  the direct test, watched in real time rather than inferred — the D115 "selection on noise" failure.
- **Evolved ≈ random across all five bases and both dev conditions.** No amplification, because there was
  no climb to amplify. The refutation does not depend on the readout basis (NMSE, accuracy, margin@T all
  flat) nor on development (dev and dev-off both flat).

**S1 status: REFUTED (well-powered).** "Selectable once moving" is false for the trial_xor task at the
current operating point. Combined with the earlier delay sweep (0/50/100 ms all flat) and basis sweep
(all five flat), every LEVER THAT LEAVES P's MEANING INTACT — fitness basis, delay, more assays,
development on/off — has now been falsified as a route to a selectable gen-0-to-gen-40 gradient.

**One NON-NULL, logged as a lead not a finding.** Across the 40 generations the ONLY monotonic mover was
`mean_exc` (E/I composition), 0.80 → 0.64. Selection WAS gripping something heritable — cell-identity
composition — it simply was not task performance. This reconnects to the H-Cv2 theme (the heritable
structure selection can act on is not aggregate performance), now on the trial task rather than the
covariance task, and is a candidate thread if the study reframes around what selection CAN grip. It is a
single descriptive observation, not tested; SE not computed; do not treat as a finding.

**HONEST LIMITATION of the refutation (do not overclaim).** The overnight GA evolve phase ran at
`n_assays=2` (the reliability probe's cost-capped default), not the arm's `n_assays=4`. So the flat
trajectory specifically is at reduced assays. The reliability sweep argues 4 would not rescue it
(reliability stays low even at n_assays=8: evolved n_val=80 ~0.20 undeveloped), so the definitive
`n_assays=4` arm (scripts/trial_selection_run.py, 40 gens) was NOT run because the reliability evidence
predicts it would confirm the null at greater cost — which is the entire point of reliability-first. But
that one direct test remains formally unrun; the conclusion rests on the reliability sweep + the flat
n_assays=2 trajectory, which are strong but not the arm itself.

**BEARING ON H-A..H-D.** None are refuted — they are BLOCKED on this precondition. The error-vs-P_dev
curve (D104) cannot be measured while selection has no gradient to follow. The live options all change
what P means or what is being selected: the XOR chance-floor task structure (D120), the operating point
(gain/noise, D119 — the one lever never moved), or reframing selection onto the heritable structure that
DID move (composition/regulation, the H-Cv2 thread). Which lever to touch is deferred; this entry only
records that the tuning-level levers are exhausted.

### Revision history addition
- **2026-07-25** — SELECTABILITY prediction S1 (selectable-once-moving) advanced 2026-07-24 on n=20
  evidence, REFUTED same investigation at n=30: advancing evidence was small-n_val overfitting; 40-gen
  trajectory flat; evolved not above random on any basis or dev condition. `mean_exc` monotonic drift
  logged as an untested lead. H-A..H-D unrefuted but BLOCKED on selectability. (DECISIONS D124.)


## TESTABILITY NOTE (2026-07-25) — a flat error-vs-P curve is TWO-WAYS AMBIGUOUS; testing H-A requires a task that threads between the two failure modes

*Bears on the driving question ("does the network show the signature — a peak — AT ALL?") and H-A ("a peak exists"). This is NOT a new hypothesis and NOT a revision of H-A's claim — it is a constraint on what task/measurement can TEST H-A, forced by the 2026-07-25 selectability null (SELECTABILITY S1, REFUTED) and two independent outside-view task critiques. Full design rationale and task-fit criteria live in FRAMING.md; recorded here because it changes how a flat result must be READ.*

**The frame.** An error-vs-P (fitness-vs-P) curve returns FLAT for two OPPOSITE reasons, indistinguishable
from the curve alone:
- **TOO HARD → unselectable.** Random genomes at chance BY CONSTRUCTION (arbitrary binding, trial_xor):
  selection never moves; flat-at-chance for all P. The mode SELECTABILITY S1 refuted the current task into.
- **TOO SIMPLE → no interpolation peak.** Solved at trivially low P (2-cue fixed-delay maintenance at
  P ~ 50–100 on a 50-neuron reservoir): smooth first descent, peak (if any) below the operational P range.

**Consequence for H-A.** A flat curve DOES NOT refute H-A ("a peak exists") — it is ambiguous between
"no peak" and "peak exists but off-range (too simple)" and "task unselectable (too hard)." Testing H-A
therefore requires a task chosen to thread BETWEEN the two failure modes: a gen-0 gradient (rules out
too-hard) AND P_crit pushed into the operational synapse range ~[100,1500] (rules out too-simple). This is
a task-design precondition on the H-A test, not a change to the H-A prediction.

**The premise H-A/H-B must not smuggle in.** The ML literature and the outside advisors reason as if P_crit
EXISTS on the axis and only its LOCATION is in question. For this project that IS the driving question's
"at all?": whether the interpolation phenomenology transfers to EVOLUTIONARY search (not SGD — Frank is
explicit) with a DEVELOPMENTAL contraction between dialed-P and effective-P (D104's P_dev), which is
UNCONFIRMED. D104 showed the global-density sweeps flat but attributed it to varying the wrong P; whether
varying P_dev yields a peak AT ALL, under evolution+development, is prior and unobserved. Positioning a
peak (e.g. dimensioning a "DMTS Plus" so P_crit lands mid-range) is premature until a peak is observed on
some selectable task.

**Status.** Design constraint on the H-A test; H-A (v1) remains PRE-REGISTERED and unrevised as a claim.
Records that (i) a flat result is not a refutation of H-A, and (ii) the "does P_dev peak at all under
evolution+development" question (the driving question's "at all?", D104-open) is logically prior to any
task-dimensioning aimed at placing a peak.

### Revision history addition
- **2026-07-25** — TESTABILITY NOTE added (bears on driving question + H-A, revises neither): flat
  error-vs-P is two-ways ambiguous — TOO HARD (no gen-0 gradient, unselectable; SELECTABILITY S1) vs
  TOO SIMPLE (P_crit below the operational range, no interpolation peak). Testing H-A requires a task that
  threads between them. The premise that P_crit EXISTS on-axis (assumed by the ML analogy and both outside
  views) is the driving question's own "at all?" and is UNCONFIRMED for evolution+development (D104-open);
  it must not be assumed while dimensioning a task to position a peak. Full criteria + candidate task menu
  in FRAMING.md. Prompted by the SELECTABILITY S1 refutation and two outside-view task critiques.

**S1a (the readout-artifact alternative) — ADVANCED AND REJECTED, 2026-07-25.** The S1 refutation left one
substantive escape hatch, and it is worth recording that it was tested rather than argued away.

> **S1a (advanced as a challenge to the refutation).** The trial_xor null may be an artifact of MEASUREMENT,
> not a fact about the substrate: every number behind S1's refutation came from ONE arbitrary output cell
> (`R[:,0]`, D095). If the network computes the binding somewhere the fitness never reads, then "unselectable"
> describes the readout, and an all-neuron-aggregate fitness restores a selectable gradient.

**Why the obvious test would NOT have settled it (PJM).** Re-analysing the evolved population is
structurally incapable of answering it: that population was selected UNDER single-neuron pressure, so
distributed capability had no path to express there. Absence of distributed representation under
single-neuron selection says almost nothing about whether it would emerge under distributed selection —
you cannot observe the fruit of a pressure never applied. What survives the objection is the RANDOM
population, which has no selection history and is therefore an assumption-free gen-0 measurement.

**Evidence that REJECTED S1a (DECISIONS D125; runs/allneuron/, n=30, draws=8, n_val=80).** Scoring all 50
neurons independently, each with its own D095-weak readout: pooled over 1,500 (genome, neuron) pairs, every
per-neuron score lies within 2 noise-sd of the median (val_acc median 0.530, max 0.589, threshold 0.606;
chance 0.500). The per-genome count of neurons above that threshold is zero for essentially every genome in
every condition — no between-genome variation in how many neurons carry the task, because none do. And the
aggregate behaved diagnostically: averaging 50 neurons cut noise by ~6× (≈√50, as independent averaging
predicts) while `signal_sd` fell to 0.0000 — the signature of averaging pure noise. A distributed
representation would have survived that averaging and reliability would have risen.

**S1a status: REJECTED on the gen-0 question.** There is no toehold at ANY neuron in an unselected
population. This does not prove all-neuron SELECTION would remain flat over 40 generations — PJM's
objection stands and no measurement can retire it — but the all-neuron arm would begin from exactly that
population, so it starts from the same zero gradient single-neuron selection did. The all-neuron-aggregate
arm is ruled out as the next move.

**Consequence for S1.** The refutation hardens: the null is not an artifact of where the fitness looked.
The substrate does not perform the arbitrary binding anywhere. This converts the S1 result from a
statement about a measurement into a statement about the TASK — `trial_xor`'s target is arbitrary by
construction, hence orthogonal to every dynamics-native property a generic E/I reservoir produces, and
unsupervised development is target-blind. It therefore lands squarely on the TESTABILITY NOTE's task-fit
criterion 1 (dynamics-native reward, not an arbitrary lookup table) and narrows the live fork recorded
under "BEARING ON H-A..H-D": of the options listed there, the readout was not the problem, so the fork is
now between the task's chance-floor STRUCTURE (D120) and the operating point (D119) — with the DMTS-family
menu in FRAMING as the pre-registered candidate set for the former. Which lever is taken remains a
DECISIONS-level design turn; this entry records only that one branch is closed by evidence.

### Revision history addition
- **2026-07-25** — SELECTABILITY S1a (the readout-artifact alternative to the S1 refutation) advanced and
  REJECTED the same day: all-neuron scoring at n=30 found no gen-0 signal at ANY of 50 neurons in an
  unselected population (every per-neuron score within 2 noise-sd of the median; mean-over-neurons
  averaged to zero signal while noise fell ~√50). The all-neuron-aggregate arm is ruled out; the S1
  refutation is not a readout artifact and is now a statement about the task rather than the measurement.
  (DECISIONS D125.)

**S1a (the readout-artifact alternative) — ADVANCED AND REJECTED, 2026-07-25.** The S1 refutation left one
substantive escape hatch, and it is worth recording that it was tested rather than argued away.

> **S1a (advanced as a challenge to the refutation).** The trial_xor null may be an artifact of MEASUREMENT,
> not a fact about the substrate: every number behind S1's refutation came from ONE arbitrary output cell
> (`R[:,0]`, D095). If the network computes the binding somewhere the fitness never reads, then "unselectable"
> describes the readout, and an all-neuron-aggregate fitness restores a selectable gradient.

**Why the obvious test would NOT have settled it (PJM).** Re-analysing the evolved population is
structurally incapable of answering it: that population was selected UNDER single-neuron pressure, so
distributed capability had no path to express there. Absence of distributed representation under
single-neuron selection says almost nothing about whether it would emerge under distributed selection —
you cannot observe the fruit of a pressure never applied. What survives the objection is the RANDOM
population, which has no selection history and is therefore an assumption-free gen-0 measurement.

**Evidence that REJECTED S1a (DECISIONS D125; runs/allneuron/, n=30, draws=8, n_val=80).** Scoring all 50
neurons independently, each with its own D095-weak readout: pooled over 1,500 (genome, neuron) pairs, every
per-neuron score lies within 2 noise-sd of the median (val_acc median 0.530, max 0.589, threshold 0.606;
chance 0.500). The per-genome count of neurons above that threshold is zero for essentially every genome in
every condition — no between-genome variation in how many neurons carry the task, because none do. And the
aggregate behaved diagnostically: averaging 50 neurons cut noise by ~6× (≈√50, as independent averaging
predicts) while `signal_sd` fell to 0.0000 — the signature of averaging pure noise. A distributed
representation would have survived that averaging and reliability would have risen.

**S1a status: REJECTED on the gen-0 question.** There is no toehold at ANY neuron in an unselected
population. This does not prove all-neuron SELECTION would remain flat over 40 generations — PJM's
objection stands and no measurement can retire it — but the all-neuron arm would begin from exactly that
population, so it starts from the same zero gradient single-neuron selection did. The all-neuron-aggregate
arm is ruled out as the next move.

**Consequence for S1.** The refutation hardens: the null is not an artifact of where the fitness looked.
The substrate does not perform the arbitrary binding anywhere. This converts the S1 result from a
statement about a measurement into a statement about the TASK — `trial_xor`'s target is arbitrary by
construction, hence orthogonal to every dynamics-native property a generic E/I reservoir produces, and
unsupervised development is target-blind. It therefore lands squarely on the TESTABILITY NOTE's task-fit
criterion 1 (dynamics-native reward, not an arbitrary lookup table) and narrows the live fork recorded
under "BEARING ON H-A..H-D": of the options listed there, the readout was not the problem, so the fork is
now between the task's chance-floor STRUCTURE (D120) and the operating point (D119) — with the DMTS-family
menu in FRAMING as the pre-registered candidate set for the former. Which lever is taken remains a
DECISIONS-level design turn; this entry records only that one branch is closed by evidence.

### Revision history addition
- **2026-07-25** — SELECTABILITY S1a (the readout-artifact alternative to the S1 refutation) advanced and
  REJECTED the same day: all-neuron scoring at n=30 found no gen-0 signal at ANY of 50 neurons in an
  unselected population (every per-neuron score within 2 noise-sd of the median; mean-over-neurons
  averaged to zero signal while noise fell ~√50). The all-neuron-aggregate arm is ruled out; the S1
  refutation is not a readout artifact and is now a statement about the task rather than the measurement.
  (DECISIONS D125.)

