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

    # --- fitness (D094 three-term) ------------------------------------------------------
    c_syn: float = 0.0                  # metabolic cost per synapse. 0 = FRANK'S ASSUMED REGIME
    w_e: float = 1.0                    # weight on encoding (first descent)
    w_c: float = 1.0                    # weight on carrying (short-term memory)
    w_r: float = 2.0                    # weight on carrying*regulation bonus (second descent)
    w0: float = 0.6
    ei_split: float = 0.8

    # --- development inner loop (D083/D087) --------------------------------------------
    dev_ms: float = 1500.0              # development duration per eval; 0 disables (birth scoring)
    dev_eta: float = 1e-3               # Vogels plasticity learning rate

    # --- noise-robust evaluation (D085c / determinism) --------------------------------
    n_assays: int = 3                   # noise realizations per genome, averaged. >1 so a single
                                        # lucky/unlucky noise draw isn't mistaken for signal.

    _gen: int = 0                       # internal: current generation (folded into per-assay seeds
                                        # so unchanged elites get fresh noise each gen). Set by the loop.

    seed: int = 0


def _fitness(comp: dict, n_params: int, cfg: EvolveConfig) -> float:
    """D094 three-term fitness on the DEVELOPED phenotype:
        w_e*encoding + w_c*carrying + w_r*(carrying*regulation)  -  c_syn*|W|
    - encoding   = memoryless-achievable task performance (first descent).
    - carrying   = short-term memory: context-distinguishability of state (credited alone).
    - carrying*regulation = working memory BONUS (second descent): regulation is contingent on
      holding context (multiplicative), so it is only accessible on top of carrying (D094).
    c_syn is the metabolic complexity penalty: 0 = Frank's assumed regime (D054); >0 regularized.
    All components are read through the CAPACITY-CONSTRAINED designated-slice readout (D095)."""
    base = (cfg.w_e * comp["encoding"]
            + cfg.w_c * comp["carrying"]
            + cfg.w_r * (comp["carrying"] * comp["regulation"]))
    return base - cfg.c_syn * n_params


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


def _affine_nmse(Y, R):
    """D095 capacity-constrained readout: per-output AFFINE map (gain+offset per output neuron).
    NOT a mixing matrix -- d scalars, cannot mix neurons, cannot adapt to individual networks
    beyond scale/offset. This is the population-constant, non-cheating readout (D095): all real
    task performance must come from the network's dynamics routing signal to the output slice."""
    out = np.empty_like(Y)
    for j in range(Y.shape[1]):
        A = np.vstack([R[:, j], np.ones(len(R))]).T
        coef, *_ = np.linalg.lstsq(A, Y[:, j], rcond=None)
        out[:, j] = A @ coef
    return float(np.mean((Y - out) ** 2) / (np.var(Y) + 1e-12))


def _carry_covdecay(net, task, net_cfg, noise_seed=None, n_cue=8, delays=(50.0, 300.0, 800.0)):
    """Carrying = intrinsic persistence of the stimulus COVARIANCE structure (D098), scored by the
    DECAY TIME of that persistence (D098b): recurrence extends the LIFETIME of the covariance
    similarity, not its magnitude, so the discriminating statistic is AREA under the
    similarity-vs-delay curve -- NOT similarity at a single delay (where passive current-echo and
    active recurrent maintenance look identical -- the confound that sank 3 prior measures).

    Non-relational, whole-network, overlapping inputs, NO cue/label (D098): drive with a task-
    stimulus run -> for each silent-delay length, read the persisting state in a short window at the
    END of the delay -> covariance-alignment of that state with the stimulus top-subspace, MINUS a
    shuffled-stimulus baseline (removes fixed-point confounds) -> carry = area under the
    (delay -> similarity) curve. Passive echo -> fast decay -> small area; active maintenance ->
    slow decay -> large area.

    delays: GA uses a REDUCED 3-point set for cost (D098b); characterization can pass a finer sweep.
    """
    c = net_cfg
    if noise_seed is not None:
        import brian2 as b2
        b2.seed(noise_seed)
    rng = np.random.default_rng(0 if noise_seed is None else noise_seed)
    if len(task.E_train) < n_cue:
        return 0.0
    stim = task.E_train[rng.choice(len(task.E_train), n_cue, replace=False)]
    dp = np.zeros((n_cue, c.N)); dp[:, :c.n_in] = stim
    _evals, evec = np.linalg.eigh(np.cov(dp.T) + 1e-9 * np.eye(c.N))
    top = evec[:, -min(5, c.n_in):]                        # top stimulus-covariance directions
    stim_shuf = stim.copy()
    for j in range(stim.shape[1]):
        rng.shuffle(stim_shuf[:, j])                        # destroys covariance, keeps marginals

    def _persist_window(cue, delay_ms):
        import brian2 as b2
        from brian2 import ms
        n = cue.shape[0]; cue_ms = n * c.present_ms; tot = cue_ms + delay_ms
        n_steps = int(round(tot / c.present_ms)); drive = np.zeros((n_steps, c.N))
        for k in range(n): drive[k, :c.n_in] = c.input_gain * cue[k]
        ta = b2.TimedArray(drive, dt=c.present_ms * ms)
        net.net.restore("init"); net.G.namespace["ta"] = ta
        mon = b2.StateMonitor(net.G, "r", record=True, dt=c.sample_ms * ms, name="mon_carry")
        net.net.add(mon); net.net.run(tot * ms)
        r = np.asarray(mon.r); t = np.asarray(mon.t / ms); net.net.remove(mon)
        if len(t): t = t - t[0]
        return r[:, t > (cue_ms + delay_ms - 50)]          # short window at the END of the delay

    def _align(Pm):
        if Pm.shape[1] < 3:
            return 0.0
        pcov = np.cov(Pm)
        return float(np.trace(top.T @ pcov @ top) / (np.trace(pcov) + 1e-9))

    curve = []
    for dly in delays:
        a_real = _align(_persist_window(stim, dly))
        a_shuf = _align(_persist_window(stim_shuf, dly))
        curve.append(max(0.0, a_real - a_shuf))
    if len(delays) < 2:
        return float(curve[0])
    return float(np.trapezoid(curve, delays) / (delays[-1] - delays[0]))


def evaluate(genome: Genome, task, net_cfg: EvoNetConfig, cfg: "EvolveConfig | None" = None) -> dict:
    """DEVELOP then score the DEVELOPED phenotype (D083), averaged over K NOISE ASSAYS for
    noise-robustness (D085c): a single lucky/unlucky noise draw must not be mistaken for signal.
    Returns the three D094 components read through the capacity-constrained designated-slice
    readout (D095), each MEANED over K assays (with per-assay SD reported for diagnostics).

    Determinism: each assay uses a reproducible noise seed derived from (cfg.seed, genome hash,
    assay index), so the whole run replays identically while each assay sees an INDEPENDENT noise
    realization -- exactly what distributional evaluation needs.
    """
    net = EvoNet(genome, net_cfg)

    floor = task.headroom()["memoryless_floor"]
    n_assays = 1 if cfg is None else max(1, cfg.n_assays)
    base_seed = 0 if cfg is None else cfg.seed
    # STABLE genome-derived seed (Python's hash() is per-process randomized -> nondeterministic;
    # use a content hash of the weight bytes instead so runs replay identically).
    import zlib
    gseed = (zlib.crc32(genome.mag.tobytes()) ^ (base_seed & 0xFFFFFFFF)) & 0x7FFFFFFF

    # --- development (D083): mature the phenotype before scoring, DETERMINISTICALLY -----------
    if cfg is None or cfg.dev_ms > 0:
        eta = 1e-3 if cfg is None else cfg.dev_eta
        dev_ms = 1500.0 if cfg is None else cfg.dev_ms
        net.develop(task.E_train, eta=eta, dev_ms=dev_ms, warmup_ms=200.0, n_checkpoints=4,
                    seed=gseed)

    enc, car, reg, etr, ete = [], [], [], [], []
    # generation component in the seed (fix b): with n_assays=1, an unchanged ELITE must NOT see the
    # identical noise draw every generation (frozen noise -- the determinism-audit failure mode). The
    # generation is folded in so elites get FRESH noise each gen while the whole run stays reproducible.
    gen_off = 0 if cfg is None else (getattr(cfg, "_gen", 0) * 100003)
    for a in range(n_assays):
        s_tr = (gseed + gen_off + 4 * a + 1) & 0x7FFFFFFF
        s_te = (gseed + gen_off + 4 * a + 2) & 0x7FFFFFFF
        s_ca = (gseed + gen_off + 4 * a + 3) & 0x7FFFFFFF
        B_tr = net.behave(task.E_train, noise_seed=s_tr)
        B_te = net.behave(task.E_test, noise_seed=s_te)
        e_tr = _affine_nmse(task.Y_train, B_tr["rates"])
        e_te = _affine_nmse(task.Y_test, B_te["rates"])
        etr.append(e_tr); ete.append(e_te)
        enc.append(max(0.0, 1.0 - e_te))
        reg.append(max(0.0, floor - e_te))
        car.append(_carry_covdecay(net, task, net_cfg, noise_seed=s_ca))

    return dict(train_err=float(np.mean(etr)), test_err=float(np.mean(ete)),
                n_params=genome.n_params(), exc_frac=genome.exc_fraction(),
                encoding=float(np.mean(enc)), carrying=float(np.mean(car)),
                regulation=float(np.mean(reg)),
                # per-assay SDs: diagnostics for whether a component is stable signal or noise
                encoding_sd=float(np.std(enc)), carrying_sd=float(np.std(car)),
                regulation_sd=float(np.std(reg)), n_assays=n_assays)


_WORKER = {}


def _init_worker(task, net_cfg, cfg=None):
    """Set the task/net_cfg/cfg ONCE per worker (D064).

    Without this, `pool.map` re-pickles the task (E/Y arrays + W_ctx) and net_cfg for **every
    individual, every generation** — real overhead that ate most of the parallel speedup.
    """
    _WORKER["task"] = task
    _WORKER["net_cfg"] = net_cfg
    _WORKER["cfg"] = cfg


def _eval_payload(item):
    """TOP-LEVEL, picklable — Windows spawn (D007). Receives (genome, gen); task/cfg from worker."""
    genome, gen = item
    cfg = _WORKER.get("cfg")
    if cfg is not None:
        cfg._gen = gen
    r = evaluate(genome, _WORKER["task"], _WORKER["net_cfg"], cfg)
    r.pop("state", None); r.pop("state_var", None)   # do not ship big arrays back
    return r


def run_evolution(task, net_cfg: EvoNetConfig, cfg: EvolveConfig,
                  eval_fn=None, n_workers: int = 1, verbose: bool = True) -> tuple:
    """Evolve W. Returns (history_rows, final_population).

    Records BOTH best-individual and population-mean training error (D059): interpolation
    (Gate B0) asks whether **any** genome can fit exactly; R&N's Occam factor is a
    **class-level** effect.
    """
    rng = np.random.default_rng(cfg.seed)
    # BUG FIX (D065): decide about the pool BEFORE overwriting eval_fn.
    # The old order set `eval_fn` to a lambda first, then tested `eval_fn is None` — which was
    # therefore ALWAYS FALSE, so the pool was NEVER created and every run was silently SERIAL
    # (one process, ~1 core). Caught by PJM watching Task Manager: "only 1 Python process at 12%".
    use_pool = (n_workers > 1) and (eval_fn is None)
    eval_fn = eval_fn or (lambda g: evaluate(g, task, net_cfg, cfg))

    pop = [random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split,
                         seed=cfg.seed + i) for i in range(cfg.pop_size)]
    history = []
    pool = None
    if use_pool:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(n_workers, initializer=_init_worker,
                                            initargs=(task, net_cfg, cfg))
    try:
      for gen in range(cfg.n_generations):
          cfg._gen = gen                          # fold generation into per-assay seeds (fix b)
          if pool is not None:
            res = pool.map(_eval_payload, [(g, gen) for g in pop])  # ship genome + gen
          else:
            res = [eval_fn(g) for g in pop]
          errs = np.array([r["train_err"] for r in res])
          tests = np.array([r["test_err"] for r in res])
          nps = np.array([r["n_params"] for r in res])
          fits = np.array([_fitness(r, r["n_params"], cfg) for r in res])

          order = np.argsort(-fits)
          history.append(dict(
            gen=gen,
            # best individual — the right convention for Gate B0 (can ANY genome interpolate?)
            best_train=float(errs[order[0]]), best_test=float(tests[order[0]]),
            best_params=int(nps[order[0]]),
            # population mean — the right convention for R&N's class-level Occam factor
            mean_train=float(errs.mean()), mean_test=float(tests.mean()),
            mean_params=float(nps.mean()), std_params=float(nps.std()),
            mean_exc_frac=float(np.mean([r["exc_frac"] for r in res])),
            fit_mean=float(fits.mean()), fit_std=float(fits.std()),
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
