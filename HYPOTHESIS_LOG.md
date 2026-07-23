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

## Revision history (chronological)
- **2026-07-22** — H-C v1 → H-Cv2 (difficulty ordering inverted: regulation native, encoding the hard
  ordered case; second descent = refinement not emergence). Forced by DECISIONS D108–D110. H-Cv2
  PROVISIONAL, gated on the reversal test + range-artifact control. H-A measurement rebuilt (nonlinear
  readout) without revising the claim. Driving question, H-B, H-D unrevised.
