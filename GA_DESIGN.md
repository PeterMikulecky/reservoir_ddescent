# E9 — Evolving reservoir capacity and structure (flagship design, rev. C)

Per D021, revised by D022/D023. A genetic algorithm supplies the selection, heredity, and
lineage the reservoir lacks; the linear readout is the scoring mechanism. **Rev. C makes
readout capacity `M` heritable — which is what makes Frank's central claim testable at all.**

## 0. The core idea

The double-descent x-axis is the number of **learned** parameters. In this model the learned
parameters are the readout weights — there are **M** of them. The recurrent weights are
*structure*: fixed per genome, not learned. So **M is Frank's Figure 1 x-axis.**

If the experimenter fixes M (as in rev. A/B), "does evolution find overparameterization?" is
unaskable — we chose the answer. Rev. C puts M in the genome and lets selection choose.

## 1. The prediction that makes this worth running

The interpolation threshold sits at **M ≈ n** (n = number of environments in the selective
history). Two measured facts (flat-landscape check, 2026-07-14, N=300):

- **Below threshold (M < n):** training error is nonzero and falls as M grows. Verified:
  error varied ~6× across genomes (0.05–0.43) at n=400 > N=300. → selection pushes **M up**.
- **Above threshold (M > n):** training error is *exactly* zero for every genome (~1e-29,
  even at PR = 2.5 — rank is full at min(n,M) regardless of PR). Extra features buy nothing.
  With any metabolic cost, `fitness = −c_syn·cost(M)` → selection pushes **M down**.

Those forces meet at **M ≈ n — the test-error peak.**

> **G1 (the sharp one).** Selection on past environments, with *any* metabolic cost on
> parameters, parks a lineage at the interpolation threshold: the **worst-generalizing
> configuration available**. This is a direct challenge to Frank.

> **G2 (the twist that rescues him).** At `c_syn = 0`, fitness is flat for all M ≥ n but
> still penalizing below n — a **neutral plateau with a reflecting boundary**. Drift cannot
> go below n, so M random-walks *upward* into the overparameterized regime and generalization
> improves via the second descent. **Frank's aside that "biology tends not to penalize
> complexity as strongly" turns out to be the precise condition his thesis requires.**

So `c_syn` is not a nuisance parameter — it is **the central swept axis**, and the
evolutionary form of E4's ridge-vs-min-norm contrast.

## 2. Genome

Five genes, real-valued. Mutation = Gaussian perturbation (per-gene σ, clipped);
recombination = per-gene uniform crossover. GA machinery deliberately boring.

| Gene | Range | Meaning |
|---|---|---|
| `M` | [2, N] | **readout capacity — the learned-parameter count; Frank's x-axis** |
| `p` | [0.005, 0.6] | recurrent density (synapse count) |
| `w0` | [0.2, 4.0] | per-synapse coupling (D014; operative range ~0.5–3.0) |
| `recip` | [0, 1] | reciprocity bias — the one motif class that *raises* PR (Recanatesi) |
| `ei` | [0.5, 1.0] | fraction excitatory (Dale's law; `ei_split` exists but is unused) |

`M` selects **which** neurons the readout taps. v1: a deterministic seeded subset of size M
(so M is inherited as a count, and the identity is a fixed function of the genome). v2 option:
an evolvable mask, if identity turns out to matter.

**This separates two readings of Frank's "parameterization" that he does not distinguish:**
`M` = learned-parameter count; `p`/`w0`/`recip` = regulatory structure. E9 can ask which one
behaves the way he claims. (Sharpens D016.)

## 3. Fitness

```
fitness = −NMSE(n encountered environments) − c_syn · cost
cost    = M                (learned parameters)   [v1]
        | M + λ·synapses   (parameters + wiring)  [v2 — separates the two costs]
```

Test (never selected on): NMSE on held-out novel environments, incl. novel-direction draws
from `tasks.anisotropic_regression`.

`c_syn` sweep: **0** (Frank's regime), small, moderate. G1 predicts M → n for c_syn > 0;
G2 predicts M drifts ≫ n at c_syn = 0.

## 4. Scale

- **N = 1000** (reservoir pool). Benchmarked: cost scales sublinearly in N (the `w0` mode
  skips the O(N³) eigenvalue call), ~4 s/individual → **pop 50 × 100 gens ≈ 1–2 h on 6
  workers**. Matches the group's original brainstorm and both Litwin-Kumar (2017) and
  Recanatesi (2019) — direct comparability.
- **n = 50–100** environments, so M ∈ [2, 1000] straddles the threshold with headroom on
  both sides. **N ≫ n is the binding design constraint.**
- Prototype at N=300, pop 20 × 30 gens.

## 5. Measurements (per generation)

Genes (esp. **M**), fitness, training NMSE, **novel-environment NMSE**, PR, effective rank,
synapse count, diversity, and the population-wide PR–generalization correlation.
Key series: **M vs. n over generations** (G1/G2), and novel error vs. M (the double-descent
curve, traced by evolution rather than by sweep).

End-of-run: the evolved population is the D019 screening-off library — natural scatter over
structure and PR, for the conditional-independence test.

## 6. Controls

| Control | Kills |
|---|---|
| **No selection** (random parents) | "M/PR moved by mutation bias alone." Essential — at c_syn=0 this is nearly the null, and may be the real mechanism (variational bias ≠ Frank's claim). |
| Shuffled fitness | selection-does-nothing |
| `c_syn` = 0 vs >0 | G1 vs G2 — the central contrast |
| Fixed-`M` arm | isolates structure's contribution from capacity's |
| Fixed-`w0` arm | prevents w0 from trivially bypassing the structural route to PR |

## 7. Hypotheses

- **G1** — with c_syn > 0, evolved M converges to ≈ n; novel-environment error is *maximal*
  there. Selection finds the worst-generalizing capacity.
- **G2** — with c_syn = 0, M drifts ≫ n; novel error falls via the second descent.
- **G3 (= D019)** — across the evolved population, **PR screens off structure**: given PR,
  genome structure adds nothing for generalization. Frank's claim H. Failure is equally
  publishable.
- **G4** — dimensionality mediates any generalization gain (bootstrap mediation, evolutionary
  time as driver).
- **G5** — evolved in-degree (p·N) sits near the Litwin-Kumar dimension optimum (K ≈ 9 at
  N = 1000) if PR is what selection effectively chases. Cheap, falsifiable, borrowed.

## 8. Settled / open

**Settled by the flat-landscape check (2026-07-14):**
- Landscape *is* exactly flat above threshold (1e-29 for all genomes). ✓
- Below threshold fitness is informative and favors high PR. ✓
- **PR does not relocate the threshold** — rank is full at min(n,M) regardless of PR.
  Independent confirmation of D018 (H5 retired), from our own data.

**Open:**
1. **Operating point.** T0 must be re-run in the `w0` parameterization; E9 inherits
   bias/input_gain, and `w0` evolves around it. **This is the immediate next step.**
2. **Does M's identity matter, or only its count?** v1 assumes count. Check with a
   fixed-count/varying-identity probe before committing.
3. **Environment model.** v1: fixed set of n draws. Option: environments *accumulate* over
   generations (rev. B's idea) — makes the threshold crossing an evolutionary event. Could be
   layered on top of C later.
4. **Cost functional.** Is cost ∝ M, or ∝ synapses, or both? v2 separates them; v1 uses M.

## 9. Build order

1. **T0 re-run in `w0` parameterization** → operating point. ← next
2. `connectivity.py`: add `recip`, activate `ei_split`.
3. `ddescent/evolve.py`: genome (incl. M), mutation, recombination, selection, M-subset readout.
4. `scripts/run_E9_evolve.py`: provenanced, spawn-parallel, generation-wise logging.
5. Prototype (N=300, pop 20 × 30, one c_syn) → then production (N=1000, c_syn sweep).

## 10. What E9 can and cannot claim

**Can:** whether selection over heritable capacity and structure finds — or avoids —
overparameterization; whether generalization follows; whether dimensionality mediates and
screens off structure; and what `c_syn` regime Frank's thesis requires.

**Cannot:** anything about real evolutionary history. This is a population of reservoirs, not
lineages of organisms. Frank's comparative claim (prokaryote → eukaryote → multicellular) is
not testable here — that is E7's job (D020), where the reservoir is a calibrated reference,
not evidence about the tree of life. State this in the writeup; don't let a reader infer more.
