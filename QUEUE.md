# Queue

Single source of truth for what's next. Updated 2026-07-15 (end of session).
Rule: **nothing here is a claim** — claims live in DECISIONS.md, narrative in LAB_NOTEBOOK.md.

## Where the project stands

The flagship is **E9**: evolve motif-encoded reservoirs with a GA; readout = scoring
mechanism; the genome carries readout capacity `M`, so evolution — not the experimenter —
chooses where it sits relative to the interpolation threshold (D021/D023).

**2026-07-16 (D030): the reservoir was never checked against a raw-input baseline, and at
T0's operating point it LOSES — 0.880 vs 0.216, four times worse than no reservoir.** T0
optimized PR responsiveness, which is in *opposition* to encoding the input. The operating
point is invalid, and D028 (the "PR_var supports Frank" finding) was measured there and is now
in doubt. Fixed: `ddescent/baseline.py` + T0 rev3 gates on skill > 1 before ranking by PR.

**Biggest open risk:** the useful regime (gain~10) may have no live PR axis (6% responsiveness,
saturated activity in smoke). If that holds at N=1000, **E9's premise fails** and the model
needs rethinking.

**D029 (task fix) is DONE** — novel is now novel-but-related (displaced along a *sampled* axis),
with graded `novel_levels` giving a generalization *curve*. It was correct and still needed; it
just wasn't the binding problem.

---

## Critical path (do in this order)

### 0. RE-TUNE T0 WITH THE BASELINE GATE  ← START HERE  (D030)
`python scripts\run_T0_tune_operating_point.py --preset coarse`   then `--preset fine`
T0 rev3 runs a real task per condition and gates on **skill > 1** (beats a linear readout on
the raw input) before ranking by PR. The old operating point (bias 0.4, **gain 0.1**) is
**invalid**: there the reservoir scored 0.880 vs a 0.216 baseline — 4x worse than no reservoir.
*Watch for:* the smoke run picks gain=10 (skill 1.24) but PR responsiveness collapses to 6%
and activity saturates. **If the useful regime has no live PR axis at N=1000, E9's premise is
in trouble** — that is the thing to find out, and it is now the project's biggest open risk.
*If nothing beats baseline:* widen gains further (30, 100) before trusting any PR result.

### 0b. Re-examine D028 at a VALID operating point
D028's "PR_var predicts generalization / screens off structure" was measured at gain 0.1 where
nothing generalizes. Re-run the feature check once a useful operating point exists:
`python scripts\run_T0_feature_check.py --preset fine --seeds 10` then `python scripts\analyze_AN_feature_check.py`

### 1. Fix the novel-environment generator  (D029)  [DONE — verify]
`tasks.anisotropic_regression` draws novel inputs along the **lowest-variance axes** — the
ones training barely sampled. Every novel NMSE in the N=1000 run exceeded 1: nothing beat
predicting the mean. That is orthogonal extrapolation, not Frank's "new instances of a
learned class."
*Fix:* novel = **novel-but-related** — fresh draws from the same structured class, or
moderate shifts along *sampled* directions. `tasks.snakeness_classification` already sketches
the class-structure idea; may be the better base.
*Gates:* H1 verdict · D028 finalization · E9's fitness definition.

### 2. Re-run the feature check on the fixed task
`python scripts\run_T0_feature_check.py --preset fine --seeds 10`
then `python scripts\analyze_AN_feature_check.py`
*Watch:* does `X_var`'s screening-off (M2: pr significant, w0/density not) survive a task that
measures real generalization?

### 3. Finalize the fitness feature (closes D028)
`X_var`, or `X_mean`+`X_var` concatenated. **Do not default to `X_mean`** — on current
evidence that would make Frank's mechanism invisible to E9 by construction.

### 4. Commit the operating point
- **Gain cliff:** the T0 argmax sits on the grid boundary (every top point had the *lowest*
  `input_gain`=0.1). Cliff or headroom?
  `python scripts\run_T0_tune_operating_point.py --preset fine --biases 0.3,0.4,0.5 --gains 0.03,0.05,0.1,0.15 --tag gain-cliff`
- **Seed replication:** T0 has **none** — it takes the argmax of a noisy quantity from a
  single draw (winner's curse). The top three `pr_rel` values differed by 0.8%. Add seed
  aggregation + variability reporting, as `run_T0_feature_check.py` now does.
- Provisional pick meanwhile: **bias 0.4, input_gain 0.1** — chosen for activity margin
  (0.603) among statistically-tied leaders, not for winning by 0.8%. The robust finding is
  *"gain=0.1 matters; bias is free in 0.2–0.5."*

### 5. Build E9
1. `connectivity.py`: add `recip` (reciprocity bias — the one motif class that *raises* PR,
   per Recanatesi); activate `ei_split` (exists, unused).
2. `ddescent/evolve.py`: genome `(M, p, w0, recip, ei)`, mutation, recombination, selection,
   M-subset readout.
3. `scripts/run_E9_evolve.py`: provenanced, spawn-parallel, generation-wise logging.
4. Prototype: N=300, pop 20 × 30 gens, one `c_syn`.
5. Production: N=1000, **`c_syn` sweep** (G1 vs G2 — the central contrast).
See `GA_DESIGN.md`.

---

## Free / cheap (grab when convenient)

- **Q1 in-distribution medians.** The feature check prints medians for `novel` only, so we
  **still don't know which channel generalizes best in-distribution** — the comparison that
  matters. Two-line change to the print block, no re-run.
- **Robust re-fit of the `var` models.** Several fits flagged DID NOT CONVERGE (D028 caveat
  1). M2/M3 agree, but confirm with a robust/bootstrap fit.
- **Terminology: "cells" → "conditions".** The scripts print "cells" while the manifest stores
  `n_conditions`. In a computational-neuroscience project "cell" colliding with "neuron" is a
  bad word choice — mine. Rename before it reaches a paper draft.

## Deferred (real, not forgotten)

- **Crossed net × task design.** `net_seed` and `task_seed` are **aliased** (`task_seed =
  net_seed + 500`), so network variance and environment variance cannot be separated. Needs a
  crossed design — a *new experiment*, not a re-analysis. Do after the task fix (which changes
  what a "task draw" means).
- **Protocol T (temporal).** Specced in `PROTOCOLS.md`, never built. ~10% of Protocol S's
  cost. Characterization only — fitness stays Protocol S (D026).
- **Systematic related-work review (D017).** A first targeted search showed most planned
  mechanism links are already established (REFERENCES.md "Positioning"). The full review has
  not been done. Priority reads: Clark/Abbott/Litwin-Kumar 2023; Cayco-Gajic 2017;
  Litwin-Kumar 2017 in full; Dambre 2012; the E/I-ratio PR paper.
- **E7 scaling/invariants study (D020)** — the group-facing deliverable.
- **Two GA arms (S-fitness vs T-fitness)** — a real experiment about whether environmental
  structure shapes evolvability. Doubles the budget; second flagship. Worth wanting.
- **H2 needs restating.** The N=1000 readout check showed density → PR is **not** a main
  effect but a **w0 × density interaction**: monotonic fall at w0≤1.0, but **U-shaped at
  w0=3.0** (15.4 → 8.8 → 17.0 → 23.1). Note this is a **U**, where Litwin-Kumar found an
  **inverted-U** — different quantity (recurrent density vs feedforward in-degree), so neither
  contradiction nor confirmation.

## Standing rules (earned the hard way)

- **Log-transform heavy-tailed error outcomes.** Raw NMSE spanned 5 orders of magnitude and
  the un-transformed models were garbage (D028 method note).
- **Treat convergence warnings as results**, not noise.
- **Commit before `reg` runs** — the firewall enforces it. A finished run dirties
  `LAB_NOTEBOOK.md` via the auto-stub, so commit the notebook (with your interpretation line
  filled in) before the next confirmatory run.
- **When sweeping a structural variable**, check no normalization pins the mediator, and run a
  **disconnected-network control** to confirm the component does anything at all before
  interpreting a null (D014).
- **PR stays the pre-specified confirmatory measure** (D002/D016); the rest of the battery is
  exploratory (D025). Collect broadly, commit narrowly.
