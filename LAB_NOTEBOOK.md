# Lab notebook

Running record of what we did, found, and decided. Two kinds of entry:

- **Auto stubs** (`<!-- auto -->`) — appended automatically by `provenance.py` when a
  run finalizes: run ID, git commit + message, config, headline result, and a blank
  `_interpretation:_` line. *Fill that line in* — the facts are automatic, the meaning
  is not.
- **Prose entries** — hand-written notes: what a session concluded, what we decided,
  why. These carry the reasoning that stubs can't.

Newest entries at the bottom. Decisions referenced as `Dxxx` live in `DECISIONS.md`.

---

## 2026-07-13/14 — Project scaffold and environment
Built the reservoir engine (Brian2 LIF, numpy codegen — D001), the experiment/analysis
package, and the provenance system (run IDs, manifests, confirmatory firewall — D004).
Set up the working environment: local repo on `C:\dev\` + private GitHub (D008), run
data off the local drive via `DDESCENT_RUNS_ROOT` with cloud folders as archive-only
(D009), cmd terminal (D011). Smoke test passed and reproduced sandbox numbers exactly
(`pr_mean 9.212`) — seeded reproducibility confirmed.

## 2026-07-14 — T0 tuning: the static regime cannot support E1
Goal: find an operating point where PR is large **and responsive to connectivity** — the
independent variable E1 needs.

Coarse sweep (N=500, 48 operating points): activity spanned 0.11–0.90 with 44/48 in the
healthy band, peak PR ≈ 46 — so the dynamical regime is *fine*. But the best PR
responsiveness was `pr_range` ≈ 0.7 against `pr_mean` ≈ 37, i.e. **PR varies < 2% across
the full connectivity range.** Best candidates all sat at the lowest input gain (0.1),
with low-to-mid bias.

Follow-up: added `present_ms` as a swept axis to test reading the recurrent **transient**
instead of the settled fixed point. It helped in the predicted direction — responsiveness
roughly 2–3× better at `present_ms=20` vs `150` — but topped out around **3.7%**. Still
far too flat for E1.

**Interpretation.** With a static input read at (or near) the settled state, the reservoir
is essentially a random feature map of the input vector, so PR is anchored to the input
dimensionality (K=20) and recurrent connectivity is only a second-order perturbation. No
amount of bias/gain/timing tuning moves that anchor. Recurrence genuinely shapes effective
dimensionality only when the network integrates an input **history** — the temporal
regime, which is also the standard reservoir-computing setup and closer to Frank's picture
of regulatory circuits processing signals over context.

**Decision.** Pivot E1 to temporal inputs (D012), *provisionally* — gated on a temporal
PR-responsiveness check: confirm connectivity strongly moves PR with temporal inputs before
rebuilding E1. Flagged as a possible framing change (instantaneous map → memory/trajectory
system); H1–H5 to be re-examined in a design_doc revision.

**Value of the negative result.** Tuning did its job: it ruled out the static setup *before*
a flagship run that couldn't have worked.

*Next:* build a temporal task + a temporal PR-responsiveness diagnostic; run it as the
go/no-go for the pivot.

## 2026-07-14 — Literature search overturns the temporal pivot: the flat PR was our own artifact
Before building the temporal diagnostic, ran a targeted literature search on what controls
dynamics/dimensionality in spiking reservoirs. It immediately overturned the previous
session's conclusion.

**Key sources.** Recanatesi, Ocker, Buice & Shea-Brown (2019, PLOS Comp Biol),
*Dimensionality in recurrent spiking networks* — uses the **same participation-ratio**
measure, and sweeps connection probability *p* to show dimensionality is strongly
regulated by connectivity, **decreasing as p rises**, with the effect concentrated where
the spectral radius approaches 1. Also: dimensionality varies widely *at fixed p*
depending on how connections are arranged (motif structure), and most motif types
(chains, convergent, divergent) *lower* dimensionality, while reciprocal/trace motifs can
raise it. Supporting: Legenstein & Maass (2007) kernel-rank / generalization-rank
measures; Büsing et al. (2010) on connectivity dependence in binary vs analog reservoirs.

**The realization.** Recanatesi et al. vary p *without renormalizing gain*. We were
renormalizing — in **both** available modes (`spectral_radius` rescales to a fixed rho;
`gain` divides by √(p·N), pinning rho ≈ gain). So sweeping density while holding coupling
constant erased the density → dimensionality pathway by construction.

**Control test (the smoking gun).** At w0 = 0.05 — roughly what the spectral-radius
normalization produced — PR was *numerically identical* to a network with **no recurrent
synapses at all** (15.06 vs 14.97). The recurrence was effectively disabled. Only at
w0 ≈ 3.0 (60× larger) did PR move (15 → 7.6). The "edge of chaos at rho ≈ 1" heuristic is
a **rate-network** result; this spiking LIF model with reset/refractoriness needs far
stronger coupling, so the whole rho ∈ [0.5, 2.0] sweep sat in a dead zone.

**Result after the fix** (fixed per-synapse w0, no renormalization), PR spread across
density:

| regime | w0 = 0.05 (old scaling) | w0 = 1.5 | w0 = 3.0 |
|---|---|---|---|
| static  | 0% | 124% | 159% |
| temporal | — | 127% | — |

Direction matches Recanatesi et al.: **PR decreases with density.**

**Interpretation.** My previous mechanistic story — "static input anchors PR to input
dimensionality; only temporal recurrence can shape the representation" — was plausible and
**wrong**. Static works fine (better than temporal, in fact). The static/temporal axis was
never the binding constraint; effective coupling was. D012 (temporal pivot) is superseded
by D014. E1 stays static; no framing change; H1–H5 stand.

**Bonus for the science.** Frank's intuition is more wiring → more dimensionality. Both the
literature and our data show dimensionality *decreasing* with connectivity — sharpening H2
into a directional prediction with independent backing.

**Methodological lesson.** Two faults compounded and were both invisible to the tuning
sweep, which faithfully measured a real quantity in a regime where the independent variable
did nothing: (1) a normalization holding the mediating quantity constant, (2) a parameter
range where the manipulated component had no effect. Standing rules going forward: when
sweeping a structural variable, check that no normalization pins the mediator; and run a
**disconnected-network control** to confirm the component does anything at all before
interpreting a null.

*Next:* re-run the T0 tuning sweep in the w0 parameterization (sweep w0 × density × bias/
input_gain) to pick an operating point with high, responsive PR and healthy activity —
then E1 (static, as originally designed) is unblocked.

<!-- Future run stubs will be auto-appended below this line. -->
