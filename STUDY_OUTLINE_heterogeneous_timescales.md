# STUDY OUTLINE — Evolving heterogeneous synaptic timescales, with P = the number of independently tunable time constants

**Status: OUTLINE for argument, not a decision.** Nothing here is memorialised. Written 2026-07-29 after
the literature search (Perez-Nieves et al. 2021; HetSyn 2025; Beiran & Ostojic 2019; Deco et al. 2013)
and the substrate-first turn. Several parts should probably be rejected; §7 lists the ones I am least
sure of.

---

## 1. Why this is a different study, not another repair

Everything from D124 to D138 was a repair to a design fixed months ago: N=100, one shared `tau_slow`,
`P = |W|`, a weak readout, a task chosen before the substrate was characterised. Fifteen entries of
repairs produced a precise account of what the substrate does NOT do.

The literature supplies the missing mechanism, and it is not one we had considered:

> **In HetSyn, temporal integration moves from the membrane to the SYNAPSE. Each synapse has its own
> decay constant, so different inputs to the SAME neuron have different memory spans.** A long-tau
> synapse carries "then", a short-tau synapse carries "now", and the neuron detects their coincidence.

That is exactly the conjunction D128 found our substrate could not compute — and it explains WHY it
could not: **one `tau_slow` shared by every synapse means no neuron can compare across time.** It also
explains why HetSyn outperforms neuron-level heterogeneity: a per-neuron tau applies uniformly to all
inputs and cannot differentiate them.

**This retires the D132 conclusion that relational tasks are beyond this substrate.** HetSyn reports
100% on delayed match-to-sample at an 800 ms delay, still effective at FIVE neurons, and 100% at 2500 ms.
DMTS was retired for a reason that does not survive per-synapse time constants.

---

## 2. The gap

| what exists | what does not |
|---|---|
| Heterogeneity helps, strongly, on temporally structured tasks (Perez-Nieves) | Nobody has EVOLVED time constants. Perez-Nieves explicitly flags this: their result is consistent with lifetime learning **or an evolutionary process**, and they test only the first |
| Homogeneous vs heterogeneous, plus one "intermediate" (5% slow) condition | Nobody has swept the NUMBER of independently tunable time constants as a continuous axis |
| HetSyn's masking experiment: 80% of synaptic taus frozen still gives 100% accuracy | Three or four points, accuracy only. No generalization gap, no search for non-monotonicity |
| Learned tau distributions are log-normal/gamma, matching biology | No error-vs-parameter-count curve of any kind |

**HetSyn's masking experiment is a crude version of the sweep this study proposes**, and its result is
already informative: P_crit for their DMTS lies below 20% of synapses.

---

## 3. P, defined for this architecture

> **P = the number of independently tunable time constants.**

Synapses are partitioned into P groups; all synapses in a group share one tau. P=1 is homogeneous
(vanilla LIF); P=|W| is fully heterogeneous (HetSynLIF). HetSyn's Propositions 1–3 prove the model
reduces to vanilla LIF, to ALIF, and to neuron-level heterogeneity under exactly these parameter
sharings, so **the axis is a nested hierarchy of established models, not an invention.**

Why this P and not `|W|`:
- **It counts parameters that demonstrably move function.** D130/D135/D136 established that recurrent
  synapses in our current substrate do not participate; a flat error-vs-P curve is the CORRECT result
  for a parameter count over inert components. That may be all the flatness ever was.
- **It is literally the number of degrees of freedom in the regulatory level.** A time constant computes
  nothing; it governs how another quantity evolves. FRAMING defines regulation as a level that modulates
  another level, and P-as-timescale-count measures that directly where P-as-synapse-count does not.
- **The variance screen supports it.** Intrinsic parameters ranked above recurrent weights for heritable
  variance in fitness (signs 0.72, v_thresh 0.71, bias 0.67, recurrent 0.58, input_cols 0.48 at 4 draws).

⚠ **A tension to resolve, not assume away.** Perez-Nieves tested heterogeneity of firing threshold and
reset potential and found NO appreciable difference, because in their model those are nearly equivalent
to rescaling the membrane potential. Our screen ranked `v_thresh` second. Ours has a fixed `bias` below
threshold so distance-to-threshold genuinely varies — but the discrepancy needs measuring.

---

## 4. The task, and why P_crit can be POSITIONED

Adopt HetSyn's DMTS, which is demonstrated solvable, with our nested split (D131):
- **Separate input channels per cue category** plus dedicated noise channels — the cue-selective routing
  whose absence made our D132 architecture probe uninformative.
- K cue categories -> K² ordered pairs; **train on a subset, test on held-out PAIRS** (generalization to
  new structure) and on held-out trials of seen pairs (generalization to new noise). Three error
  measures, as D131 specifies.
- Delay length is a difficulty knob with a known working range (HetSyn: 800–2500 ms).

**The critical property: the number of task-relevant timescales is under our control.** A task requiring
*k* distinct timescales should interpolate near P ≈ *k*. That means **P_crit can be placed inside the
swept range rather than hoped for** — which is FRAMING's two-failure-mode problem (flat curve = "too
hard" or "too simple") solved by construction rather than by argument. No previous task in this project
had that property.

---

## 5. Substrate, development, selection

**Substrate.** HetSynLIF: membrane potential is the sum of synaptic currents minus a reset current, each
synapse carrying its own decay. N ≈ 100 (Perez-Nieves used 128 and chose small deliberately — with more
neurons, homogeneous performance approaches ceiling and architectural effects vanish). Fixed and NOT
evolvable: E/I identity, tau_m, the input projection scaffold. Evolvable: synaptic weights, the P group
time constants, per-neuron bias.
- **tau range:** biological synaptic taus are log-normal and long-tailed past 500 ms (Allen Institute:
  194 human, 1213 mouse pairs), so the usable range is far wider than our current 100 ms. Perez-Nieves
  bound membrane tau at 100 ms because ~99.5% of recorded membrane constants fall below it — that bound
  applies to MEMBRANE, not synaptic, constants.

**Development = noise-driven working-point tuning (Deco).** The stimulus is WEAK, SLOW noise — an
Ornstein-Uhlenbeck background, and they cut noise amplitude 14x from their earlier model because strong
noise degrades the structure-function fit. Target: the network's own critical point, measured as the
autocorrelation time of spontaneous activity (critical slowing).
- **Why this does not contaminate P:** an unstructured-noise stimulus with a dynamical target has NO
  access to the task, so development cannot encode task-specific information and cannot inflate
  task-relevant capacity. Structural, not approximate — and it holds only while the stimulus stays
  task-blind.
- **Deco predicts development makes P MORE legible, not less.** Covariance is set by the Jacobian's
  eigendecomposition, fixed by connectivity at the working point; at criticality structure is maximally
  expressed. That inverts the H-E "development washes out variance" concern and is pre-registerable.

**Selection.** D134's all-neuron fitness as amended: N independent held-out two-parameter affine reads,
aggregated as the MEAN PREDICTION (not mean of scores — 0.517 vs 0.114, below chance).
- ⚠ **Do NOT adopt HetSyn's firing-rate regulariser** (they penalise deviation from 10 Hz at weight
  0.01). That is an auxiliary objective, and D134 forbids them: selection then optimises firing rate and
  the P-curve stops being a curve of task performance. If a rate constraint proves necessary, impose it
  as a **viability filter** — networks outside a band are excluded, not scored — which keeps the fitness
  single-objective.

---

## 6. What would count as a result

- **Non-monotone test error vs P, with the peak surviving D126's criterion** (exceeds neighbours by >2 SE
  AND appears in a majority of individual seed curves) -> double descent on a timescale axis. Novel: no
  error-vs-parameter-count curve exists anywhere in this literature.
- **The correlate to look for**, and it is specific rather than generic: past P_crit, does the evolved
  tau DISTRIBUTION change character — from a few tuned values to the log-normal/long-tailed shape both
  Perez-Nieves and HetSyn recover, and which matches biology? **That would be encoding saturation shown
  as a change in the form of the regulatory level, not merely in its size.**
- **Monotone decreasing** -> heterogeneity helps without an interpolation peak. Still a result: the
  first evolved (not gradient-trained) demonstration, and a direct test of Perez-Nieves' untested
  evolutionary alternative.
- **Flat** -> P defined this way also fails to move error, which after `|W|` would be a strong statement
  that this substrate does not exhibit parameter-count effects at all.

---

## 7. What I am least sure about

- **Whether evolution can find what surrogate gradients find.** Every result cited used BPTT or FORCE.
  HetSyn's DMTS took 1000 iterations with batch 32; Perez-Nieves used ~2 GPU-years overall. A GA on a
  noisy fitness may need far more generations than we can afford, and D137's gate says our gradient is
  real but modest.
- **Whether P as group count is the right granularity.** Partitioning synapses into P groups is one
  choice; per-neuron grouping (HetNeuLIF) is another and is a strictly smaller axis. They may give
  different curves, and that difference may itself be the interesting thing.
- **Implementation cost.** Per-synapse decay constants mean |W| extra state variables in Brian2. At
  N=100, density 0.3, that is 3000 — feasible, but it is a substantial rewrite of `evonet`, not a
  parameter change.
- **Whether the tau distribution correlate is real or decorative.** "The distribution changes shape past
  P_crit" is an attractive story and I have no evidence for it. It should be pre-registered as a
  prediction that can fail, not offered as an interpretation after the fact.
- **We have been here before.** D126 and D131 were also well-argued designs that failed for reasons
  invisible at design time. The mitigation is §8.

---

## 8. Build order — cheap checks that can each end the line

1. **Does per-synapse tau solve the D128 conjunction?** Hand-build a small HetSynLIF network with two
   synapse populations (long tau, short tau) onto shared postsynaptic neurons; test whether match/
   non-match becomes linearly decodable where D128 measured it at chance. **This is the whole premise in
   one cheap test.** If it fails, stop.
2. **Known-positive:** reproduce HetSyn's DMTS result at small N with hand-set time constants. If the
   published result does not reproduce in our implementation, fix that before anything else.
3. **Gen-0 prior check:** random genomes at each P must be AT CHANCE (the D131 E2 condition).
4. **Reliability at each P** (D115): fitness must clear the bar before any arm is run.
5. **Mutational smoothness** of the tau genes; log-scale mutation, since tau spans orders of magnitude.
6. Only then the P sweep, with D127's localization instrumentation attached.

Steps 1–5 are cheap and each can end the line. Step 1 in particular tests the single claim the whole
study rests on, and it is the one that should be run first.
