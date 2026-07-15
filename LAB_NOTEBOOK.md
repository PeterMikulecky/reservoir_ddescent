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

## 2026-07-14 — Reframe: the flagship becomes an evolutionary model (E9)
Four critiques from PJM, each landing, reshaped the project.

**Interpretation test retired (D018).** Checked the RMT literature: the interpolation peak
occurs where normalized effective degrees of freedom η_κ → 1 (Bach 2023; Hastie et al.).
So "effective dimensionality, not nominal count, sets the threshold" is *already
established*, and the literature supplies the principled metric (edof) — a different
functional of the spectrum than PR. PJM's critique ("we'd need to show other candidates
*aren't* the axis") forced the check. H5 demoted to a diagnostic.

**Dissociation reframed (D019).** PJM caught that varying motifs *in order to* move PR
couples them by construction — collinear predictors, same error class as the D014
normalization bug. Correct design exploits the many-to-one structure→PR map (Recanatesi:
PR varies widely at fixed density): build natural scatter, then test whether **PR screens
off structure** for generalization. That *is* Frank's claim H.

**E7 scoped (D020).** A reference point for messier systems must characterize its own
scaling — what's invariant, what's substrate-specific.

**Flagship = GA over motif-encoded reservoirs (D021, PJM's proposal).** The entire surveyed
literature lacks **selection**. A GA supplies heredity, lineage, population, and makes
Frank's mapping literal (selective history = training data; novel environments = test data)
rather than metaphorical. Genome v1 = (p, w0, recip, ei); readout = scoring mechanism;
metabolic cost on synapses makes "biology doesn't penalize complexity" a manipulable axis.

**The structural insight.** Above the interpolation threshold every individual interpolates,
so the fitness landscape is **flat — a neutral network**. Not a bug: it lands the population
exactly in the regime Frank's Gavrilets/neutral-space reframing is about. Central contrast
becomes below vs. above threshold, manipulated via size of selective history. The GA also
generates the D019 screening-off library as a byproduct.

**Where the project now stands.** It was "does dimensionality drive generalization"
(answered, by others, 2017). It is now: **does selection over heritable regulatory structure
produce general solutions, and does dimensionality mediate it?** The established literature
becomes the calibrated instrument — PJM's original instinct — rather than the result.

*Next:* (1) re-run T0 in the w0 parameterization; (2) **flat-landscape check** — verify
training NMSE ≈ 0 across the genome range above threshold, the load-bearing assumption of
E9; (3) build `evolve.py`. See GA_DESIGN.md.

<!-- Future run stubs will be auto-appended below this line. -->

## 2026-07-15 04:13 — `T0-tune_operating_point__20260715-033028__exp__gcae6f45__fine-w0-n1000`  <!-- auto -->
- type `exp` · stage `T0` · git `gcae6f45` (T0 rev2: sweep w0 not spectral_radius (D014); score substrates over genome space; full metric battery) · status **complete**
- result: 20/20 healthy; best bias=0.4 gain=0.1; PR 7.9-53.5 (rel 200%); peak PR 57.1
- _interpretation:_ 

## 2026-07-15 05:02 — `T0-tune_operating_point__20260715-050108__exp__ge927bdb__readout-check-n1000`  <!-- auto -->
- type `exp` · stage `T0` · git `ge927bdb` (D027: three-way readout check passes - averaging confound cleared) · status **complete**
- result: readout check @ bias=0.4 gain=0.1: inst/mean span ratio 0.96, direction agree=True
- _interpretation:_ 

## 2026-07-15 06:41 — `T0-tune_operating_point__20260715-053812__exp__gefee6c4__feature-n1000`  <!-- auto -->
- type `exp` · stage `T0` · git `gefee6c4` (feature check: sweep seeds internally, separate net/task seeds, pooled mixed model) · status **complete**
- result: FIRST generalization measurement. median novel NMSE: mean=5.681, inst=22.496, var=13.661; best=mean
- _interpretation:_ 

## 2026-07-15 06:54 — `AN-analysis__20260715-065428__exp__g2798ab0__feature-check-models`  <!-- auto -->
- type `exp` · stage `AN` · git `g2798ab0` (lab nb update) · status **complete**
- result: M1/M2/M3 x {test,novel} on T0-tune_operating_point__20260715-053812__exp__gefee6c4__feature-n1000; M2 beta_pr (test): mean=+0.19, inst=-0.50, var=-246.84
- _interpretation:_ 
