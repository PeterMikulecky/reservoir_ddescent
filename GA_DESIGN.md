# E9 — Evolving motif-encoded reservoirs (flagship design)

Per D021. The linear readout is the scoring mechanism; a genetic algorithm supplies the
selection, heredity, and lineage that the reservoir alone lacks. This document is the
concrete design: genome, fitness, the below/above-threshold contrast, measurements,
controls, and the open questions to settle before building.

## 0. Why this is the flagship

Everything else we planned re-derives an established mechanism link (REFERENCES.md
Positioning). **The literature we surveyed has no selection.** Frank's claim is
evolutionary, and his mapping becomes *literal* here rather than metaphorical:

| Frank | E9 |
|---|---|
| Regulatory architecture | Reservoir connectivity, built from a genome |
| Genome / heritable parameters | Motif-signature genome (below) |
| Selective history | The set of environments encountered so far |
| Selection | GA selection on fitness over that history |
| Novel environments | Held-out environments, never selected on |
| Fitness landscape / training-error surface | Fitness over encountered environments |
| Regulatory dimensionality | PR of reservoir activity (D002/D016) |

Nothing in this table is doing unearned analogical work (contrast D003, where a learning
optimizer stood in for selection — the reason the epoch-wise story stayed exploratory).

## 1. Genome

**v1 (build this first).** Four real-valued genes, all cheap to implement, no SONET
dependency:

| Gene | Range | Meaning | Why |
|---|---|---|---|
| `p` | [0.005, 0.6] | connection density | Frank's "more parameters" axis; the synapse count |
| `w0` | [0.2, 4.0] | per-synapse coupling (D014) | must be evolvable — it is the operative gain knob |
| `recip` | [0, 1] | reciprocity bias: P(connection is made bidirectional) | Recanatesi: reciprocal/trace motifs are the **only** motif class that *raises* dimensionality; chains/convergent/divergent lower it |
| `ei` | [0.5, 1.0] | fraction excitatory (Dale's law) | the E/I literature's PR lever; `ei_split` already exists in `connectivity.py` but is unused |

Reciprocity is the deliberate v1 motif knob: it is the dimension-*raising* motif per
Recanatesi, and it is trivial to implement (symmetrize a sampled fraction of edges). Full
SONET (5 α-parameters: recip, conv, div, chain + p) is the **v2** genome once v1 works —
it buys the full motif signature at the cost of implementing the Zhao/Nykamp generator.

Genes are real-valued; mutation = Gaussian perturbation with per-gene σ, clipped to range.
Recombination = per-gene uniform crossover. Both are deliberately boring — the science is
in the fitness/threshold contrast, not the GA machinery.

**Log the genome→phenotype map every generation.** `p` and `recip` jointly determine synapse
count; `w0`, `p`, `ei` jointly determine PR. That many-to-one map is the D019 instrument, not
a nuisance.

## 2. Genotype → phenotype → fitness

```
genome (p, w0, recip, ei)
   -> W_rec           (connectivity.make_recurrent_weights, w0 mode + recip + ei)
   -> reservoir       (LIFReservoir, fixed operating point from T0)
   -> X_train         states over encountered environments
   -> readout         min-norm least squares  (the "biological" unregularized regime, D-E4)
   -> fitness         performance over encountered environments − metabolic cost
```

**Fitness.**

```
fitness = −NMSE(encountered environments) − c_syn · synapse_count
```

The **metabolic cost** term `c_syn` is not decoration — it is load-bearing three ways:
1. Without it, if more wiring ever helps, `p` simply rails to its maximum and the run is
   uninformative.
2. It is biologically real (synapses are expensive).
3. It directly operationalizes Frank's claim that *biology does not penalize complexity the
   way classical statistics does*. Sweeping `c_syn` — including `c_syn = 0` — turns that
   claim into a manipulable variable rather than an assumption. **`c_syn` sweep is a
   first-class experimental axis, not a nuisance parameter.**

**Test (never selected on):** NMSE on held-out novel environments, including
novel-direction environments from the anisotropic generator (`tasks.anisotropic_regression`
already builds these).

## 3. The central contrast: below vs. above the interpolation threshold

The readout has N features (reservoir neurons) and n training samples (environments
encountered). The interpolation threshold sits near N ≈ n.

- **Below threshold** (n ≫ N — rich selective history): training error is nonzero and varies
  across genomes. Fitness is informative. Classical selection.
- **Above threshold** (n ≪ N — sparse selective history): **every genome interpolates;
  training error is ~0 for all; the fitness landscape is flat** (modulo the cost term).
  Selection cannot distinguish solutions. The population drifts on a **neutral network**.

This is not a bug to engineer around. It is Frank's own reframing made mechanical: *"the
relevant factor is not a position on a fitness surface. It is how the dimensionality of the
regulatory architecture alters the geometry of evolutionary trajectories within the fitness
landscape."* Above threshold, what determines generalization is **which region of the
neutral network the dynamics find** — driven by mutation bias and the structure of the
genotype→phenotype map, not by the fitness gradient.

**Manipulate the contrast by varying n** (the number of environments in the selective
history) at fixed N. This is biologically legible: lineages with rich vs. sparse
environmental history.

## 4. Hypotheses

- **G1 (drift finds generality).** Above the interpolation threshold, where selection on
  training performance is blind, generalization to novel environments *still* improves over
  generations. *This is Frank's central mechanism, and the sharpest thing E9 can show.*
- **G2 (dimensionality mediates).** Any improvement in generalization is mediated by PR
  (bootstrap mediation, as in `analysis.mediation_density_pr`, with evolutionary time as the
  driver).
- **G3 (screening-off; = D019).** Across the evolved population's natural scatter,
  **PR screens off structure**: conditional on PR, genome/structure adds no predictive power
  for generalization. Supports Frank's claim H. Failure (structure predicts beyond PR) is an
  equally publishable challenge to it.
- **G4 (complexity cost).** As `c_syn → 0`, evolved `p` and synapse count rise and the
  population experiences the full double-descent curve; as `c_syn` grows, complexity is
  penalized and the interpolation spike is smoothed — the evolutionary analogue of
  ridge-vs-min-norm (E4). Tests Frank's "biology doesn't penalize complexity" claim directly.
- **G5 (direction of the wiring→dimension effect).** Evolved genomes should sit near the
  Litwin-Kumar dimension optimum in in-degree (K = p·N ≈ 9 at N = 1000), *if* PR is what
  selection is effectively chasing. A strong, cheap, falsifiable point prediction borrowed
  from the literature.

## 5. Measurements (per generation)

Population-level: mean/best/variance of fitness, training NMSE, **novel-environment NMSE**,
PR, effective rank, synapse count, and each gene. Plus genetic diversity, and the
**PR–generalization correlation across the population** (the live G3 signal).

End-of-run: the full evolved population as the D019 screening-off library — iso-PR /
iso-structure pairs located post hoc.

## 6. Controls (each one kills a specific alternative explanation)

| Control | Kills |
|---|---|
| **No selection** (random parents each generation) | "PR rose by mutation/GP-map bias alone, not selection." *Essential* — above threshold this is the null, and it may be the actual mechanism. |
| **Shuffled fitness** | selection-is-doing-nothing |
| **Frozen genome** (evolve nothing, resample) | drift-free baseline |
| **Below-threshold arm** | isolates the flat-landscape claim |
| **`c_syn = 0` vs. `c_syn > 0`** | G4 |

The no-selection control deserves emphasis: above the interpolation threshold, fitness is
flat *by construction*, so "evolution" is drift plus mutation bias. If PR rises identically
without selection, the honest finding is that the **genotype→phenotype map**, not selection,
biases toward high dimensionality — which is a real result (developmental/variational bias,
"arrival of the fittest") but a *different* claim from Frank's, and must not be reported as
his.

## 7. Compute budget

Genome is 4 numbers; cost is dominated by reservoir simulation + readout fit per individual.
At N = 300, ~2–5 s per evaluation. Population 50 × 100 generations = 5,000 evaluations ≈
3–7 h serial, **≈ 1 h on 6 workers**. Each (threshold arm × `c_syn` level × control × seed)
multiplies that — so budget deliberately, and prototype at population 20 × 30 generations.

Parallelism: evaluate individuals within a generation via the existing spawn-safe pool
(`fixed_n._run_one_cell` pattern). One GA run = one provenance run (D007); generation-wise
records go to `data/generations.parquet`, the final population to `data/population.parquet`.

## 8. Open design questions (settle before building)

1. **Does the flat landscape actually go flat?** Verify empirically that above threshold,
   training NMSE ≈ 0 across the genome range. If the min-norm readout leaves residual
   variation, selection isn't blind and the contrast weakens. **Check this first — it is the
   load-bearing assumption of the whole design.**
2. **Operating point.** T0 must be re-run in the `w0` parameterization to fix bias/input_gain
   before E9. E9 inherits that operating point; `w0` then evolves around it.
3. **Environment model.** What is "an environment"? v1: a draw from the anisotropic
   generator, fitness = NMSE across encountered draws. Open: stationary set vs. environments
   *accumulating* over generations (the latter is more evolutionarily honest and makes n grow
   with lineage age — which would make the threshold crossing itself an evolutionary event,
   an attractive but more complex design).
4. **Is `w0` evolvable a confound?** `w0` moves PR strongly and directly. If evolution just
   tunes `w0`, the motif story is bypassed. Consider a fixed-`w0` arm to force structural
   routes to PR.
5. **N.** 300 for tractability; the D020 scaling study checks whether conclusions survive to
   1000.

## 9. Build order

1. Re-run T0 in `w0` parameterization → operating point.
2. **Flat-landscape check** (open question 1). If it fails, redesign before building the GA.
3. `ddescent/evolve.py`: genome, mutation, recombination, selection; `connectivity.py` gains
   `recip` and activates `ei_split`.
4. `scripts/run_E9_evolve.py`: provenanced, parallel, generation-wise logging.
5. Prototype (pop 20 × 30 gens, one arm) → sanity, then the full design.

## 10. What E9 can and cannot claim

**Can:** that selection and drift over heritable regulatory structure do (or do not) produce
generalizing solutions; that dimensionality does (or does not) mediate it; that
dimensionality does (or does not) screen off structure.

**Cannot:** anything about *real* evolutionary history. This is a model of a population of
reservoirs, not of lineages of organisms. The comparative claim (Frank's prokaryote →
eukaryote → multicellular trend) is not testable here — that is E7's job (D020), and even
there the reservoir's role is a calibrated reference, not evidence about the tree of life.
State this limitation in the writeup rather than letting a reader infer more.
