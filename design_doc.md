# Double descent in a LIF reservoir: pilot design

A pilot study probing Frank (2026), *Generalization as the great leap in evolvability*,
using a reservoir of N = 1000 leaky integrate-and-fire neurons with variable
connectivity and a linear readout. This document lays out (1) the larger experiment
set and how it maps to Frank's arguments, (3) the fixed-N dissociation hypotheses and
the measurements that address them, and (4) the analysis pipeline. Part (2), the
Brian2 engine, is the code in `ddescent/`.

## 0. How the reservoir maps onto Frank's argument

Frank's biological dictionary is: regulatory connections are parameters, selective
history is training data, selection is the optimizer, novel environments are test
data, and the fitness landscape is the training-error surface. The reservoir gives us
each term explicitly, but with one subtlety that is the whole reason this model is
worth building:

| Frank's term | Reservoir counterpart |
|---|---|
| Regulatory architecture | Recurrent LIF connectivity `W_rec` (fixed per organism) |
| Parameter count | Number of nonzero recurrent synapses |
| Phenotype / internal representation | Reservoir state `X` (filtered rates) |
| Tuned adaptive trait | Linear readout weights (the trained part) |
| Training environments | Input patterns `U_train` |
| Novel environments | `U_test` (within-class) and `U_novel` (out-of-distribution / novel direction) |
| Effective regulatory dimensionality | **Participation ratio (PR) of the state covariance** |

The subtlety: Frank's prose slides between three things — raw parameter count, wiring
connectivity, and *effective* dimensionality — as if they move together. In a
recurrent network they do not. Dense coupling can *collapse* effective dimensionality
through synchronization as easily as raise it. The reservoir lets us hold neuron count
fixed and dissociate these three quantities, which is what turns "more wiring →
generalization" from an assertion into a testable, mechanistic claim.

## 1. The experiment set

Nine experiment families. E1 is the flagship (this pilot); the rest are the natural
extensions the same engine supports, and each isolates one specific Frank claim.

**E0 — Readout double descent (validation).** Fix the reservoir; sweep the number of
readout features feeding a least-squares/ridge readout past the interpolation
threshold. Reproduces Frank's Figure 1 in the "trained trait" sense. *Purpose:*
validate the setup and provide the E1↔E0 bridge (H5). *Frank claim:* B (double
descent exists). Not the result — the baseline.

**E1 — Fixed-N dissociation (flagship).** Hold N = 1000; sweep connectivity (density,
spectral radius) across seeds to move PR at constant neuron count. Regress
generalization on synapse count, density, and PR separately. *Frank claim:* H
(dimensionality *per se*, not specific circuit features, is the primary cause of
generalizing capacity) — the load-bearing and least-tested assertion in the paper.
Hypotheses H1–H5 below.

**E2 — Variance geometry (Schaeffer et al.).** Give environments anisotropic
covariance; train on high-variance directions, test along weakly-sampled directions.
Measure how PR flattens the novel-direction error spike. *Frank claim:* C3 — his
sentence about past environments sampling one direction while a novel environment
along a weakly-sampled direction exposes concentrated error. The most literal
instantiation of his biology. (Implemented: `tasks.anisotropic_regression` already
builds the novel-direction test set.)

**E3 — Aliasing / noise (Transtrum et al.).** Sweep injected noise
(`ReservoirConfig.noise_sigma`, or target noise); measure interpolation-peak height
vs noise and vs PR. *Frank claim:* C2 — extra dimensions supply the slack to separate
signal from noise; the peak is noise-driven. Doubles as a check that the setup
reproduces the known label-noise amplification of double descent (Nakkiran et al.).

**E4 — Implicit bias / regularization (Wilson; Frank's "biology doesn't penalize
complexity").** Contrast min-norm interpolation (`alpha = 0`) with ridge (`alpha > 0`);
show ridge smooths the spike away, and that min-norm selects low-weight-norm, smooth
input→output maps. *Frank claim:* C1 and E — the "biological = unregularized" regime
experiences the full double descent.

**E5 — Temporal double descent (online).** Train the readout online (RLS/FORCE,
`readout.OnlineRLS`) and look for epoch-wise double descent over training time.
*Frank claim:* G — older circuits generalize better. **Caveat:** the "training time =
circuit age = evolutionary time" identity is a metaphor doing real work; decide as a
group how much weight to place on it before building around it.

**E6 — Snakeness task (essence vs outline).** Structured classes; test on novel
within-class exemplars (recognizes snakeness?) vs out-of-class inputs (asserts
structure it never saw?). *Frank claim:* A — the memorization/generalization
distinction his opening rattlesnake example dramatizes. This is a *task lens* overlaid
on E1–E5, not a separate sweep. (Implemented: `tasks.snakeness_classification`.)

**E7 — Comparative ladder (prokaryote → eukaryote → multicellular).** Re-frame E1 as a
graded series: reservoirs tiered by regulatory dimensionality, predicting monotone
generalization gain. *Frank claim:* F — the historical trend. This is also the
**bridge to the rest of your group**: PR is a portable axis. Whoever runs boolean
networks computes PR on their state spectra; the beehive/ant-colony people ask the
analogous question about collective-state dimensionality. The reservoir becomes the
clean reference phenomenology the messier model systems get compared against.

**E8 — Neutral-space selection (Gavrilets; Frank's landscape reframing).** Among
readout solutions that interpolate the training data equally well (a neutral manifold),
which does the learning dynamics find, and does that member generalize? *Frank claim:*
J and I — his shift from "position on a fitness surface" to "which solution within the
connected neutral region does learning select." Connects min-norm selection (E4) to
Gavrilets' neutral networks.

### How they relate

```
                 E0 validation (Fig 1 reproduction)
                        │  provides interpolation-threshold bridge (H5)
                        ▼
   ┌──────────────  E1  FIXED-N DISSOCIATION  ──────────────┐
   │            (PR as the master axis; claim H)             │
   │                                                         │
   ▼                    ▼                    ▼               ▼
  E2 variance         E3 aliasing         E4 implicit bias  E7 comparative
  geometry (C3)       / noise (C2)        + regularization  ladder (F) ──► other
   │                    │                  (C1, E) ──► E8     group models
   │                    │                   neutral-space (J,I)
   └──── each predicts a DIFFERENT signature of *how* extra PR helps ────┘

              E5 temporal double descent (G) — the online twin of E0/E1
              E6 snakeness task (A) — a task lens overlaid on all of the above
```

E2/E3/E4 are complementary because they predict three *distinct* signatures of the
same PR effect: E2 says extra dimensions **spread** novel-direction error into many
small mismatches; E3 says they **absorb** noise; E4 says they let learning **select**
the smooth interpolant. A strong pilot shows E1's PR effect and then attributes it
across E2–E4 rather than treating "dimensionality helps" as a black box.

## 3. Fixed-N dissociation: hypotheses and measurements

### Hypotheses

**H1 — dimensionality primacy.** In a model predicting generalization error from
{log synapse count, density, PR} (standardized), the PR coefficient is significant and
dominant; count and density lose predictive power once PR is included. *This is the
direct test of Frank's claim H.*

**H2 — connectivity is not dimensionality.** Density → generalization is
**non-monotonic** (inverted-U or worse), because dense recurrent coupling can collapse
PR via synchronization. Operationally: a significant quadratic density term, and/or an
interior peak in the density→PR curve. *If true, "more wiring" is a bad proxy for the
thing that actually matters — a boundary condition Frank's verbal argument glosses.*

**H3 — usable-dimension saturation.** Generalization improves with PR then **plateaus**
once PR exceeds the environment's intrinsic dimensionality (`env_intrinsic_dim`). A
saturating fit beats a linear one (AIC), and the knee sits near the environment
dimension. *This distinguishes naive "more dimensions always help" from "more* usable
*dimensions help until you cover the environment manifold."*

**H4 — mediation.** Any effect of density on generalization is **mediated by PR**: the
bootstrap indirect effect (density → PR → generalization) is significant and the direct
effect shrinks. *Formalizes "connectivity acts through effective dimensionality."*

**H5 — threshold scales with PR (E0 bridge).** The interpolation-threshold location in
the readout-feature sweep scales with reservoir PR, not nominal feature count. *Ties
E1's structural axis to E0's classic double-descent curve: the "number of parameters"
on Frank's x-axis is really* effective *dimensionality.*

Directional prediction if Frank is right: **H1 supported, H2 supported, H3 supported,
H4 supported.** The most informative *falsification* is H2 failing (density monotonic)
together with H1 showing count/density predict as well as PR — that would say raw
wiring, not effective dimensionality, is the operative variable, contradicting the
mechanism while preserving Frank's correlation.

### Measurements recorded per run

Structural (set): `N`, `density`, `spectral_radius_target`, `seed`, `synapse_count`,
`log_synapse_count`. Dynamical (measured): `spectral_radius_measured`, `pr`,
`effective_rank`, `env_intrinsic_dim`. Outcome: `train_err`, `test_err` (within-class),
`novel_err` (novel-direction / out-of-distribution), `gen_gap`, `weight_norm`. The
tidy table (one row per reservoir × seed) is the sole input to the analysis, so
simulation and inference are fully decoupled.

### The tuning prerequisite (read before running for real)

The demo sweep exposes the one thing that must be solved first: **PR has to actually
vary with connectivity.** In the untuned demo, strong input drive plus a fixed bias
saturates the network, so PR is pinned near the input's own dimensionality (~4–5)
regardless of density or spectral radius — and with no PR variance, H1/H4 are
untestable. Before the real sweep, tune the reservoir into a regime where recurrent
dynamics shape the representation:

- reduce `input_gain` / `bias` so the reservoir is not input-saturated and recurrent
  activity dominates the state;
- operate near the edge-of-chaos transition (sweep `bias` and measured spectral radius
  to find where PR is both large and *sensitive* to connectivity);
- widen the connectivity grid and confirm, as a manipulation check, that PR spans a
  broad range (e.g. ~5 to several hundred) across the grid.

A short pre-sweep that maps PR against (`bias`, `input_gain`, spectral radius) at fixed
N, choosing the operating point where PR is most responsive, is a required Step 0. This
is itself a small result: it locates the dynamical regime in which "regulatory
dimensionality" is a live variable at all.

## 4. Analytical / statistical pipeline

All in `ddescent/analysis.py`; each function consumes the results table.

**Design and repeated measures.** The sweep is a grid of connectivity conditions ×
random seeds, with fresh environment draws per seed. Seed (equivalently
environment-instance) is a random effect: it moves the error baseline substantially
(the demo's group variance dwarfs fixed effects), so models must account for it rather
than pool naively.

**Preprocessing.** Standardize the three predictors (z-scores) so coefficients are
comparable magnitudes. Keep `synapse_count` on a log scale (it spans orders of
magnitude across the density grid). Report a manipulation check first: the realized
range of PR, spectral radius, and synapse count, to confirm the dissociation actually
happened (see tuning prerequisite).

**H1 — standardized coefficients / mixed model.** `standardized_coefficients`: fit
`gen_err ~ log_synapses_z + density_z + pr_z` with a random intercept per seed
(`statsmodels` MixedLM). Support = dominant, significant PR coefficient with attenuated
count/density. Cross-check with `univariate_r2` (each predictor's marginal R²) and with
a commonality/variance-partition view (unique vs shared variance of PR vs
count/density).

**H2 — density nonlinearity.** `density_nonlinearity`: compare linear vs
quadratic-in-density fits by AIC, test the quadratic term, locate the turning point,
and separately fit PR ~ density to show whether PR peaks at interior density (the
synchronization-collapse mechanism). A GAM/segmented fit is the robustness upgrade.

**H3 — saturation.** `pr_saturation`: compare a linear PR fit to a saturating
(exponential-approach) fit by AIC; report the fitted plateau and the knee PR, and
compare the knee to `env_intrinsic_dim`. Prediction: saturating wins and the knee sits
near the environment dimension. Robustness: vary `n_high` in the task to move the
environment dimension and confirm the knee tracks it.

**H4 — mediation.** `mediation_density_pr`: bootstrap the indirect effect
(a: density→PR, b: PR→gen | density) with a percentile CI on a·b, and report the direct
effect c′. Support = CI excludes zero and c′ shrinks relative to the total effect. Use
≥ 2000 bootstrap resamples for the reported analysis (the demo uses 500 for speed).

**H5 — threshold vs PR (E0).** `peak_location_vs_pr`: from the E0 readout-feature sweep
(one reservoir per group, swept over readout width), locate each group's peak-error
feature count and the PR there; regress peak location on PR. Support = positive slope,
tight fit — the interpolation threshold tracks effective, not nominal, dimensionality.

**Multiplicity, effect sizes, and decision rules.** Five hypotheses → control the
family-wise error (Holm across H1–H5) and report effect sizes and CIs, not just
p-values (the qualitative pattern across H1–H4 matters more than any single test).
Pre-register the directional predictions and the operating-point selection rule (chosen
on the PR-responsiveness pre-sweep, not on the outcome) so the flagship analysis is
confirmatory. Power: seeds are cheap; scale the number of seeds per grid cell until the
H4 indirect-effect CI is informative in a pilot power check.

**Robustness battery (report as supplementary).** Re-run the H1 conclusion under:
alternative tasks (snakeness vs regression), noise on/off, alternative readout
regularization, alternative dimensionality measures (`effective_rank`, linear
dimensionality, nonlinear intrinsic-dimension estimators), and integration `dt`. The
headline claim is credible only if PR-dominance is invariant to these.

## Code map

```
ddescent/
  connectivity.py   ConnectivityConfig, make_recurrent_weights (spectral-radius / E-I), make_input_weights
  reservoir.py      ReservoirConfig, LIFReservoir (streaming run_static; run_temporal hook)
  tasks.py          anisotropic_regression (E2 novel-direction sets), snakeness_classification (E6)
  measures.py       participation_ratio, effective_rank, intrinsic_dim_of_inputs, nmse, generalization_gap
  readout.py        LinearReadout (ridge / min-norm), OnlineRLS (E5), evaluate_regression / _classification
  analysis.py       H1 standardized_coefficients, H2 density_nonlinearity, H3 pr_saturation,
                    H4 mediation_density_pr, H5 peak_location_vs_pr, run_all
  experiments/
    fixed_n.py      SweepConfig, run_sweep -> tidy results table
run_demo.py         small end-to-end demo -> results_demo.csv
```

Extension points already wired: `noise_sigma` (E3), `alpha` (E4), `run_temporal` +
`OnlineRLS` (E5), `snakeness_classification` (E6), tiered `SweepConfig` (E7), min-norm
readout weight-norm / neutral-manifold access (E8).
