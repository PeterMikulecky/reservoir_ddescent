"""
The GA. **W is the genome; selection is the optimizer.**

Four design decisions here each silently determine an outcome, so each is an ARM, not a
default (D060).

────────────────────────────────────────────────────────────────────────────────────────
1. SELECTION SCHEME — decides whether R&N's Occam factor EXISTS AT ALL.
   R&N's mechanism is a **replicator-dynamics** effect: complex classes attain the highest
   per-timestep fitness but collapse onto a *different* best member each generation, so their
   **class growth rate** suffers ("overfitness"). That requires **fitness-proportional**
   selection over a distribution of types.
   **Tournament selection is RANK-based — it has no Occam factor.** Choosing it would DELETE
   one of the two mechanisms we are adjudicating, and we would never see it.
   *And note:* **Friedlander used tournament; R&N used replicator.** The two prior works we sit
   between differ on exactly this — which may partly explain why they reached opposite answers.
   ⇒ selection scheme is a **dial in the D052 graded series**.

2. DENSITY: FIXED vs EVOLVABLE — splits the study in two.
   The Occam factor is **between-class competition**. With density fixed, every individual has
   the same |W| — **one complexity class, no competition, the Occam factor cannot operate.**
     * `fixed`     : |W| fixed per arm, swept across arms → **does the curve have a peak and a
                     second descent?** (Gate B — Frank's curve.)
     * `evolvable` : structural add/remove mutations → **where does evolution LAND on that
                     curve?** (R&N's question — the money experiment.)

3. CROSSOVER is OFF by default. Two networks can compute the same function with **permuted
   neurons** (the competing-conventions problem); swapping rows/columns destroys both. NEAT
   solves this with historical markings; we have direct encoding. **Mutation-only (an
   evolution-strategy) is the safe default.** A dial, revisitable.

4. THE RISK WE CANNOT DESIGN AWAY: can a GA optimise thousands of parameters with a population
   of ~50? **Gate B0 IS that test** (does training error reach ~0?), which is why it runs before
   everything. Population size, generations and mutation σ are **load-bearing**, not tuning.
────────────────────────────────────────────────────────────────────────────────────────

Genome = Arm 1 of D059: `mag` + `signs` only. `noise_sigma` is NEVER a gene — it is H-D's
treatment variable (if evolution controlled it, the population would choose its own arm).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from .evonet import EvoNetConfig, EvoNet, Genome, random_genome, mutate


@dataclass
class EvolveConfig:
    # --- population -------------------------------------------------------------------
    pop_size: int = 50
    n_generations: int = 200
    elite: int = 2                      # copied unchanged each generation

    # --- test-error capture cadence (D077) ---------------------------------------------
    # Selection never reads test error; it is REPORTING only. Three tiers:
    #   * champion (best individual) test error: EVERY generation  -> the epoch-wise DD
    #     trajectory (a champion-RELAY, not a fixed-model curve; and generation-axis, NOT the
    #     P-axis the study's headline DD lives on -- see D077).
    #   * whole-population test (mean + spread): every `test_every` gens, AND the final gen
    #     -> D059's class-level Occam signal, at 1/test_every the cost.
    # test_every=0 disables the periodic population sweep (champion + final only).
    test_every: int = 20

    # --- ARM 1: selection scheme (D060) ------------------------------------------------
    selection: str = "replicator"       # 'replicator' (Occam factor lives) | 'tournament'
    tournament_k: int = 3
    fitness_beta: float = 1.0           # replicator softmax sharpness on fitness

    # --- ARM 2: density mode -----------------------------------------------------------
    density_mode: str = "fixed"         # 'fixed' (sweep |W| across arms) | 'evolvable'
    density: float = 0.3                # used when fixed; initial value when evolvable
    struct_add_p: float = 0.002         # per-absent-synapse add rate   (evolvable only)
    struct_del_p: float = 0.002         # per-present-synapse delete rate (evolvable only)

    # --- mutation (D043: PRODUCT rule) --------------------------------------------------
    mag_sigma: float = 0.2
    sign_flip_p: float = 0.005
    mutation_rule: str = "product"      # 'product' | 'sum'  (sum is a D052 contrast arm)
    crossover: bool = False             # OFF: competing conventions

    # --- fitness ------------------------------------------------------------------------
    c_syn: float = 0.0                  # metabolic cost per synapse. 0 = FRANK'S ASSUMED REGIME
    w0: float = 0.6
    ei_split: float = 0.8

    seed: int = 0


def _fitness(err: float, n_params: int, cfg: EvolveConfig) -> float:
    """-error - c_syn*|W|.  c_syn=0 is Frank's assumed regime (D054): biology does not
    penalize complexity. c_syn>0 is the regularized one. **This sweep asks whether Frank's
    assumed regime is even reachable.**"""
    return -err - cfg.c_syn * n_params


def _select(fits: np.ndarray, n: int, cfg: EvolveConfig, rng) -> np.ndarray:
    """Return parent indices.

    'replicator' — fitness-proportional (softmax). **Reproduces R&N's dynamics, so the Occam
        factor can operate:** a class whose best member changes every generation grows slower
        than its peak fitness suggests.
    'tournament' — rank-based, k-way. **No Occam factor.** Friedlander's scheme.
    """
    if cfg.selection == "replicator":
        z = cfg.fitness_beta * (fits - fits.max())
        p = np.exp(z); p /= p.sum()
        return rng.choice(len(fits), size=n, replace=True, p=p)
    elif cfg.selection == "tournament":
        idx = rng.integers(0, len(fits), size=(n, cfg.tournament_k))
        return idx[np.arange(n), np.argmax(fits[idx], axis=1)]
    raise ValueError(f"unknown selection {cfg.selection!r}")


def _structural_mutate(g: Genome, cfg: EvolveConfig, rng) -> Genome:
    """Add/remove synapses — only in `density_mode='evolvable'`.

    This is what makes |W| a HERITABLE quantity, hence what creates the **complexity classes**
    the Occam factor competes between. Without it there is one class and R&N's mechanism is
    silent by construction.
    """
    mag = g.mag.copy()
    present = mag != 0
    absent = ~present
    np.fill_diagonal(absent, False)

    add = absent & (rng.random(mag.shape) < cfg.struct_add_p)
    if add.any():
        mag[add] = np.abs(rng.normal(0, cfg.w0, int(add.sum())))
    dele = present & (rng.random(mag.shape) < cfg.struct_del_p)
    mag[dele] = 0.0
    return Genome(signs=g.signs.copy(), mag=mag)


def _nmse_affine(Y, R):
    """Align the network's arbitrary rate units to the demanded profile via a per-output affine
    map, then NMSE. NOT a trained readout — d scalars (gain+offset per output neuron), not a
    mixing matrix; it cannot mix neurons (D036)."""
    out = np.empty_like(Y)
    for j in range(Y.shape[1]):
        A = np.vstack([R[:, j], np.ones(len(R))]).T
        coef, *_ = np.linalg.lstsq(A, Y[:, j], rcond=None)
        out[:, j] = A @ coef
    return float(np.mean((Y - out) ** 2) / (np.var(Y) + 1e-12))


def evaluate(genome: Genome, task, net_cfg: EvoNetConfig, with_test: bool = True) -> dict:
    """Behaviour → phenotype → error. Fitness reads OUTPUT RATES (D036).

    **`with_test` (D077).** Selection (`_fitness`) reads ONLY `train_err`, so test is never needed
    to evolve — only to REPORT. A full test `behave()` is a second simulation per genome, and at
    30 genomes × every generation that was ~half the GA's runtime, thrown away: the population-mean
    test trajectory it produced is read by NO hypothesis (BRIDGE Level 5: the study's double
    descent is error-vs-P ACROSS ARMS at convergence, not a per-generation curve within one arm).
    With `with_test=False` we skip the test `behave()` entirely. The caller (run_evolution) then
    computes test only where it is actually used: the champion every generation (the epoch-wise
    trajectory — kept dense, one extra behave/gen) and the whole population every `test_every`
    generations + the final generation (D059's class-level Occam signal). `test_err` is np.nan
    when skipped, which pandas carries cleanly.
    """
    net = EvoNet(genome, net_cfg)
    B_tr = net.behave(task.E_train)
    err_tr = _nmse_affine(task.Y_train, B_tr["rates"])
    err_te = _nmse_affine(task.Y_test, net.behave(task.E_test)["rates"]) if with_test else float("nan")
    return dict(train_err=err_tr, test_err=err_te, n_params=genome.n_params(),
                exc_frac=genome.exc_fraction(), state=B_tr["state"], state_var=B_tr["state_var"])


_WORKER = {}


def _init_worker(task, net_cfg):
    """Set the task/net_cfg ONCE per worker (D064).

    Without this, `pool.map` re-pickles the task (E/Y arrays + W_ctx) and net_cfg for **every
    individual, every generation** — real overhead that ate most of the parallel speedup.
    """
    _WORKER["task"] = task
    _WORKER["net_cfg"] = net_cfg


def _eval_payload(genome):
    """TOP-LEVEL, picklable — Windows spawn (D007). One individual; task comes from the worker.

    D077: TRAIN-ONLY. Population evaluation never needs test (fitness reads train), so the worker
    skips the test `behave()`. Test is computed back in run_evolution for the champion + periodic
    population sweeps only."""
    r = evaluate(genome, _WORKER["task"], _WORKER["net_cfg"], with_test=False)
    r.pop("state", None); r.pop("state_var", None)   # do not ship big arrays back
    return r


def run_evolution(task, net_cfg: EvoNetConfig, cfg: EvolveConfig,
                  eval_fn=None, n_workers: int = 1, verbose: bool = True) -> tuple:
    """Evolve W. Returns (history_rows, final_population).

    Records BOTH best-individual and population-mean training error (D059): interpolation
    (Gate B0) asks whether **any** genome can fit exactly; R&N's Occam factor is a
    **class-level** effect.
    """
def _errs_from_behave(B_list, task, which):
    """NMSE per genome from a list of behave outputs (batched or single). which: 'train'|'test'."""
    Y = task.Y_train if which == "train" else task.Y_test
    return np.array([_nmse_affine(Y, B["rates"]) for B in B_list])


def run_evolution(task, net_cfg: EvoNetConfig, cfg: EvolveConfig,
                  eval_fn=None, n_workers: int = 1, verbose: bool = True,
                  batched: bool = True) -> tuple:
    """Evolve W. Returns (history_rows, final_population).

    Records BOTH best-individual and population-mean training error (D059): interpolation
    (Gate B0) asks whether **any** genome can fit exactly; R&N's Occam factor is a
    **class-level** effect.

    **`batched=True` (D078, default).** The whole population runs as ONE block-diagonal network
    per generation (`evonet.behave_batch`) — the ~15× measured speedup. The per-genome pool path
    (`n_workers>1`) is retained for `batched=False` / `eval_fn` overrides but is now the SLOW
    path: batching makes multiprocessing redundant (step 4). Train/selection are identical to the
    single-genome path — verified bit-for-bit at noise=0 by `verify_batch_equivalence` (D078).
    """
    from .evonet import behave_batch
    rng = np.random.default_rng(cfg.seed)
    use_pool = (not batched) and (n_workers > 1) and (eval_fn is None)
    eval_fn = eval_fn or (lambda g: evaluate(g, task, net_cfg, with_test=False))

    pop = [random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split,
                         seed=cfg.seed + i) for i in range(cfg.pop_size)]
    history = []
    pool = None
    if use_pool:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(n_workers, initializer=_init_worker,
                                            initargs=(task, net_cfg))
    try:
      for gen in range(cfg.n_generations):
          # ---- TRAIN: whole population (fitness reads train) -----------------------------
          if batched:
            B_tr = behave_batch(pop, net_cfg, task.E_train)          # one run, all genomes
            errs = _errs_from_behave(B_tr, task, "train")
            nps = np.array([g.n_params() for g in pop])
            excf = np.array([g.exc_fraction() for g in pop])
          elif pool is not None:
            res = pool.map(_eval_payload, pop)
            errs = np.array([r["train_err"] for r in res])
            nps = np.array([r["n_params"] for r in res])
            excf = np.array([r["exc_frac"] for r in res])
          else:
            res = [eval_fn(g) for g in pop]
            errs = np.array([r["train_err"] for r in res])
            nps = np.array([r["n_params"] for r in res])
            excf = np.array([r["exc_frac"] for r in res])
          fits = np.array([_fitness(e, p, cfg) for e, p in zip(errs, nps)])
          order = np.argsort(-fits)

          # ---- D077: selective TEST evaluation (batched too) -----------------------------
          is_final = (gen == cfg.n_generations - 1)
          do_pop_test = is_final or (cfg.test_every > 0 and gen % cfg.test_every == 0)
          if do_pop_test:
            # whole population — D059's class-level Occam signal + the final-gen P-point that
            # enters the cross-arm double-descent curve (the STUDY's headline DD, BRIDGE L5).
            if batched:
                B_te = behave_batch(pop, net_cfg, task.E_test)
                tests = _errs_from_behave(B_te, task, "test")
            else:
                tests = np.array([evaluate(pop[i], task, net_cfg, with_test=True)["test_err"]
                                  for i in range(len(pop))])
            best_test = float(tests[order[0]]); mean_test = float(np.nanmean(tests))
            std_test = float(np.nanstd(tests))
          else:
            # champion only — the epoch-wise DD trajectory, kept dense (one extra behave/gen).
            champ = pop[order[0]]
            if batched:
                best_test = float(_errs_from_behave(behave_batch([champ], net_cfg, task.E_test),
                                                    task, "test")[0])
            else:
                best_test = evaluate(champ, task, net_cfg, with_test=True)["test_err"]
            mean_test = float("nan"); std_test = float("nan")

          history.append(dict(
            gen=gen,
            # best individual — Gate B0's convention (can ANY genome interpolate?) + epoch-wise DD
            best_train=float(errs[order[0]]), best_test=best_test,
            best_params=int(nps[order[0]]),
            # population mean — R&N's class-level Occam factor; test is NaN on non-sweep gens
            mean_train=float(errs.mean()), mean_test=mean_test, std_test=std_test,
            mean_params=float(nps.mean()), std_params=float(nps.std()),
            mean_exc_frac=float(excf.mean()),
            fit_mean=float(fits.mean()), fit_std=float(fits.std()),
            pop_test=bool(do_pop_test),      # provenance: was mean_test a real sweep or NaN?
          ))
          if verbose and (gen % 20 == 0 or gen == cfg.n_generations - 1):
            h = history[-1]
            print(f"  gen {gen:>4}: best_train={h['best_train']:.3f} best_test={h['best_test']:.3f} "
                  f"|W|={h['mean_params']:.0f}±{h['std_params']:.0f} exc={h['mean_exc_frac']:.2f}")

          if gen == cfg.n_generations - 1:
            break
          new = [pop[i] for i in order[:cfg.elite]]                  # elitism
          parents = _select(fits, cfg.pop_size - cfg.elite, cfg, rng)
          for pi in parents:
            child = mutate(pop[pi], mag_sigma=cfg.mag_sigma, sign_flip_p=cfg.sign_flip_p,
                           rule=cfg.mutation_rule, rng=rng)
            if cfg.density_mode == "evolvable":
                child = _structural_mutate(child, cfg, rng)
            new.append(child)
          pop = new
    finally:
        if pool is not None:
            pool.close(); pool.join()
    return history, pop
