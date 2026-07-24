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
    # --- selection basis (D111) ------------------------------------------------------------------
    fitness_mode: str = "hybrid"        # 'hybrid'            = D094 three-term (encoding+carrying+bonus)
                                        # 'regulation_only'   = RAW regulation alone. This is literally the
                                        #   component D109 measured as HERITABLE (r~0.29) while aggregate
                                        #   fitness was not (r~0). Direct test of the D109 hypothesis that
                                        #   the hybrid DILUTES a transmissible signal with a
                                        #   non-transmissible one.
                                        # 'regulation_gated'  = carrying*regulation (the D094 bonus term).
                                        #   Keeps D094's logic that regulation is only meaningful ON TOP OF
                                        #   holding context, which guards against DEGENERATE solutions that
                                        #   score raw regulation without actually carrying context.
                                        # Which is right is OPEN -> measure both ways and compare (D104).
                                        # NOTE: readout is unchanged (LINEAR) in all modes -- D111's P-axis
                                        # criterion. This switch changes WHAT we select on, not HOW we read.
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
    All components are read through the CAPACITY-CONSTRAINED designated-slice readout (D095).

    D111: `fitness_mode` selects WHAT we select on. The readout stays LINEAR in every mode (the
    P-axis criterion: readout parameters are uncounted P, so the readout must not gain capacity).
    """
    mode = getattr(cfg, "fitness_mode", "hybrid")
    if mode == "regulation_only":
        base = comp["regulation"]                                   # the D109-heritable component
    elif mode == "regulation_gated":
        base = comp["carrying"] * comp["regulation"]                # D094 bonus term, carrying-gated
    elif mode == "hybrid":
        base = (cfg.w_e * comp["encoding"]
                + cfg.w_c * comp["carrying"]
                + cfg.w_r * (comp["carrying"] * comp["regulation"]))
    elif mode == "trial_xor":
        # Cue->delay->probe XOR task (D120). `trial_score` = 1.0 - val_err, so 0.0 is exactly
        # "no better than predicting the mean" -- a zero point that is EXACT rather than estimated,
        # because the XOR target puts every cue-blind and probe-blind strategy at chance by
        # construction. No clip: clipping at zero once flattened fitness to a constant and left
        # selection with nothing to act on (audit F2).
        base = comp["trial_score"] if "trial_score" in comp else (1.0 - comp["val_err"])
    else:
        raise ValueError(f"unknown fitness_mode {mode!r}")
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



# --- D113 three-way-split helpers + mechanical guard ----------------------------------------
def _val_E(task):
    """Stimuli for the SELECTION split. Falls back to test only for legacy tasks (warns)."""
    return task.E_test if getattr(task, "E_val", None) is None else task.E_val


def _val_Y(task):
    return task.Y_test if getattr(task, "Y_val", None) is None else task.Y_val


def assert_no_test_leakage(task) -> None:
    """D113 MECHANICAL GUARD. Fail loudly if the task lacks a validation split, because then every
    fitness component silently falls back to TEST error and selection optimises the reported
    generalisation quantity. Call this at the top of any run that will be reported."""
    if getattr(task, "E_val", None) is None:
        raise RuntimeError(
            "D113: task has NO validation split -- fitness would be computed from TEST error, "
            "leaking the reporting split into selection. Rebuild the task with n_val set."
        )




def covariance_powerlaw_exponent(state, rank_lo=3, rank_hi=None) -> float:
    """EFFECTIVE criticality statistic (audit E4). Raw rho(W) overstates gain in a spiking network,
    because threshold, refractoriness and saturation clamp the loop gain — so rho(W) is not the
    quantity that matters. This measures the OBSERVABLE that Stringer et al. 2026 use instead: the
    power-law decay exponent of the state covariance eigenspectrum.

    Their reference points, which make our number directly comparable to published data:
      ~0.67  critically normalised SYMMETRIC random dynamics (their analytic 2/3)
      ~1.25  NON-symmetric random dynamics
      0.7-0.85 observed in mouse cortex and brainwide recordings
    A much LARGER exponent means variance is concentrated in few modes (low effective dimensionality,
    incomplete normalisation); their CA1 exception sat at 0.4-0.5.

    Fitted by weighted least squares in log-log space over an intermediate rank band, following their
    method (weights = 1/log(rank), avoiding rank 1 and the noise-dominated tail).
    """
    X = np.asarray(state, dtype=float)
    X = X - X.mean(0)
    if X.shape[0] < 4 or X.shape[1] < 8:
        return float("nan")
    ev = np.linalg.svd(X, compute_uv=False) ** 2
    ev = ev[ev > 0]
    if rank_hi is None:
        rank_hi = max(rank_lo + 3, len(ev) // 2)
    rank_hi = min(rank_hi, len(ev))
    if rank_hi - rank_lo < 3:
        return float("nan")
    # GUARD: if the state's true rank collapses below the fit window, the eigenvalues being fitted are
    # numerical noise and the slope explodes. A local calibration produced alpha = 19.9 and 51.7 at
    # low noise + high gain for exactly this reason — those were broken measurements, not findings.
    # Require the fit band to carry real variance relative to the leading mode.
    if ev[rank_lo - 1] < 1e-9 * ev[0]:
        return float("nan")
    r = np.arange(rank_lo, rank_hi + 1, dtype=float)
    y = ev[rank_lo - 1:rank_hi]
    if np.min(y) < 1e-12 * ev[0]:
        keep = y > 1e-12 * ev[0]
        if keep.sum() < 4:
            return float("nan")
        r, y = r[keep], y[keep]
    w = 1.0 / np.log(r + 1.0)
    A = np.vstack([np.log(r), np.ones_like(r)]).T
    Aw, yw = A * w[:, None], np.log(y) * w
    coef, *_ = np.linalg.lstsq(Aw, yw, rcond=None)
    return float(-coef[0])          # exponent alpha in lambda_n ~ n^-alpha


def context_destroyed_score(net, task, split: str = "test", noise_seed: int = 0,
                            rng_seed: int = 12345) -> float:
    """D116 MATCHED FLOOR. Score the SAME network on the SAME stimuli with the temporal CONTEXT
    STRUCTURE DESTROYED (sample order shuffled, so consecutive stimuli come from different contexts
    and nothing can be accumulated across the dwell period).

    Why this replaces `headroom()['memoryless_floor']` as the reference for "no context inference":
    the old floor was a ridge on the RAW 10-dim stimulus, so it conflated MEMORYLESSNESS with
    REPRESENTATIONAL CAPACITY -- a static random 50-dim tanh expansion of the same input beats it
    (0.942 vs 1.020), with no network, no dynamics and no context. Beating that floor therefore
    demonstrated nonlinear expansion, not context inference.

    This control holds capacity FIXED (identical network, identical readout, identical stimuli) and
    removes ONLY the usable context structure. The gap
        context_destroyed_score - actual_score
    is the contribution attributable to context inference.
    """
    E_s, Y_s, _ = task._split(split)
    rng = np.random.default_rng(rng_seed)
    perm = rng.permutation(len(E_s))
    B = net.behave(E_s[perm], noise_seed=noise_seed)
    return float(_affine_nmse(Y_s[perm], B["rates"]))


def evaluate(genome: Genome, task, net_cfg: EvoNetConfig, cfg: "EvolveConfig | None" = None, report: bool = False) -> dict:
    """DEVELOP then score the DEVELOPED phenotype (D083), averaged over K NOISE ASSAYS for
    noise-robustness (D085c): a single lucky/unlucky noise draw must not be mistaken for signal.
    Returns the three D094 components read through the capacity-constrained designated-slice
    readout (D095), each MEANED over K assays (with per-assay SD reported for diagnostics).

    Determinism: each assay uses a reproducible noise seed derived from (cfg.seed, genome hash,
    assay index), so the whole run replays identically while each assay sees an INDEPENDENT noise
    realization -- exactly what distributional evaluation needs.
    """
    net = EvoNet(genome, net_cfg)

    # D113: the fitness-facing floor MUST come from the VALIDATION split, never test.
    floor = task.headroom(split="val")["memoryless_floor"]
    n_assays = 1 if cfg is None else max(1, cfg.n_assays)
    base_seed = 0 if cfg is None else cfg.seed
    # STABLE genome-derived seed (Python's hash() is per-process randomized -> nondeterministic;
    # use a content hash of the weight bytes instead so runs replay identically).
    import zlib
    gseed = (zlib.crc32(genome.mag.tobytes()) ^ (base_seed & 0xFFFFFFFF)) & 0x7FFFFFFF

    # --- development (D083): mature the phenotype before scoring, DETERMINISTICALLY -----------
    dev_converged = True; dev_aborted = False
    if cfg is None or cfg.dev_ms > 0:
        eta = 1e-3 if cfg is None else cfg.dev_eta
        dev_ms = 1500.0 if cfg is None else cfg.dev_ms
        dev_res = net.develop(task.E_train, eta=eta, dev_ms=dev_ms, warmup_ms=200.0,
                              n_checkpoints=4, seed=gseed)
        # D101 diagnostic #4/#6: did development settle within dev_ms (is dev_ms long enough)?
        # and did the NaN tripwire fire (numerical health)?
        dev_converged = bool(dev_res.get("converged", True))
        dev_aborted = (dev_res.get("reason", "ok") != "ok" and "NaN" in dev_res.get("reason", ""))

    enc, car, reg, etr, eva, ete = [], [], [], [], [], []
    cdest, cgain, alpha = [], [], []            # matched control + criticality (report only)
    # generation component in the seed (fix b): with n_assays=1, an unchanged ELITE must NOT see the
    # identical noise draw every generation (frozen noise -- the determinism-audit failure mode). The
    # generation is folded in so elites get FRESH noise each gen while the whole run stays reproducible.
    gen_off = 0 if cfg is None else (getattr(cfg, "_gen", 0) * 100003)
    for a in range(n_assays):
        s_tr = (gseed + gen_off + 4 * a + 1) & 0x7FFFFFFF
        s_te = (gseed + gen_off + 4 * a + 2) & 0x7FFFFFFF
        s_ca = (gseed + gen_off + 4 * a + 3) & 0x7FFFFFFF
        # D115 COST: development sits outside this loop, so replication repeats only behave().
        # Only the VALIDATION behave feeds selection (D113); train/test are pure REPORTING and were
        # being recomputed for every genome every generation (~2/3 of all evaluation cost). They are
        # now computed ONLY when report=True, which makes raising n_assays affordable.
        B_va = net.behave(_val_E(task), noise_seed=s_te)
        e_va = _affine_nmse(_val_Y(task), B_va["rates"])      # D113: SELECTION error
        eva.append(e_va)
        if report:
            B_tr = net.behave(task.E_train, noise_seed=s_tr)
            B_te = net.behave(task.E_test, noise_seed=s_te)
            etr.append(_affine_nmse(task.Y_train, B_tr["rates"]))
            e_te_a = _affine_nmse(task.Y_test, B_te["rates"])       # D113: REPORTING only
            ete.append(e_te_a)
            # D116/audit B1: the "memoryless floor" is capacity-confounded — a STATIC context-free
            # random expansion matches it — so it cannot license any claim about context inference.
            # The valid reference is the MATCHED control: the same network on the same stimuli with
            # the temporal context structure destroyed. Report the gap; it IS the context-use measure.
            cdest.append(context_destroyed_score(net, task, split="test", noise_seed=s_te))
            cgain.append(cdest[-1] - e_te_a)
            # audit E4: effective criticality, comparable to Stringer et al. (cortex 0.7-0.85).
            alpha.append(covariance_powerlaw_exponent(B_te["state"]))
        # --- every fitness component derives from VALIDATION error (D113) ---------------------
        # NO CLIP AT ZERO. `max(0, floor - e)` silently destroys ALL selection signal whenever the
        # population sits above the floor: with d=10 no random genome beat the val floor, so every
        # genome scored exactly 0.0 and selection had nothing to act on (audit F2/B2, 2026-07-24).
        # `floor` is a constant and cancels in the replicator softmax, so these are simply
        # sign-flipped error. Kept as offsets for continuity of reported scale.
        enc.append(1.0 - e_va)
        reg.append(floor - e_va)
        car.append(_carry_covdecay(net, task, net_cfg, noise_seed=s_ca))  # uses E_train only: no test contact

    _nan = float("nan")
    return dict(context_destroyed_err=float(np.mean(cdest)) if cdest else _nan,
                context_gain=float(np.mean(cgain)) if cgain else _nan,
                cov_powerlaw_alpha=float(np.nanmean(alpha)) if alpha else _nan,
                train_err=float(np.mean(etr)) if etr else _nan,
                val_err=float(np.mean(eva)),
                test_err=float(np.mean(ete)) if ete else _nan,
                n_params=genome.n_params(), exc_frac=genome.exc_fraction(),
                encoding=float(np.mean(enc)), carrying=float(np.mean(car)),
                regulation=float(np.mean(reg)),
                # per-assay SDs: diagnostics for whether a component is stable signal or noise
                encoding_sd=float(np.std(enc)), carrying_sd=float(np.std(car)),
                regulation_sd=float(np.std(reg)), n_assays=n_assays,
                dev_converged=dev_converged, dev_aborted=dev_aborted)


_WORKER = {}


def _init_worker(task, net_cfg, cfg=None, scorer="covariance"):
    """Set the task/net_cfg/cfg ONCE per worker (D064).

    Without this, `pool.map` re-pickles the task (E/Y arrays + W_ctx) and net_cfg for **every
    individual, every generation** — real overhead that ate most of the parallel speedup.

    `scorer` selects which evaluator the worker runs: "covariance" -> evaluate (the original path),
    "trial" -> trial_evaluate. It is a picklable string, unlike an eval_fn lambda, which is why the
    pool path dispatches on it rather than on the caller's eval_fn.
    """
    _WORKER["task"] = task
    _WORKER["net_cfg"] = net_cfg
    _WORKER["cfg"] = cfg
    _WORKER["scorer"] = scorer


def _eval_payload(item):
    """TOP-LEVEL, picklable — Windows spawn (D007). Receives (genome, gen); task/cfg from worker."""
    genome, gen = item
    cfg = _WORKER.get("cfg")
    if cfg is not None:
        cfg._gen = gen
    if _WORKER.get("scorer") == "trial":
        from .trial_eval import trial_evaluate
        r = trial_evaluate(genome, _WORKER["task"], _WORKER["net_cfg"], cfg)
    else:
        r = evaluate(genome, _WORKER["task"], _WORKER["net_cfg"], cfg)
    r.pop("state", None); r.pop("state_var", None)   # do not ship big arrays back
    return r


def run_evolution(task, net_cfg: EvoNetConfig, cfg: EvolveConfig,
                  eval_fn=None, report_fn=None, n_workers: int = 1, verbose: bool = True,
                  worker_scorer: str = "covariance") -> tuple:
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
    # Pool whenever parallel. The pool CANNOT ship a lambda across a spawn boundary, so it runs a
    # picklable top-level worker (`_eval_payload`) whose evaluator is selected by `worker_scorer`
    # ("covariance" -> evaluate, "trial" -> trial_evaluate); the SERIAL path uses `eval_fn`. A caller
    # wanting a PARALLEL trial arm passes worker_scorer="trial" (plus the matching eval_fn/report_fn
    # for the serial fallback and the per-gen report). The guard preserves the original behaviour for
    # any caller that passed a custom serial eval_fn without opting into a pooled scorer.
    use_pool = (n_workers > 1) and (eval_fn is None or worker_scorer != "covariance")
    eval_fn = eval_fn or (lambda g: evaluate(g, task, net_cfg, cfg))
    # The per-generation best-genome REPORT must use the SAME scorer family as the population, not a
    # hardcoded covariance evaluate(). Defaults preserve the covariance path EXACTLY; a trial arm
    # passes report_fn=lambda g: trial_evaluate(g, task, net_cfg, cfg, report=True) alongside its
    # eval_fn. (Was a hardcoded evaluate(report=True) below, which errors on a TrialTask — it has no
    # covariance interface. trial_evaluate(report=True) supplies the same train_err/test_err keys.)
    report_fn = report_fn or (lambda g: evaluate(g, task, net_cfg, cfg, report=True))

    pop = [random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split,
                         seed=cfg.seed + i) for i in range(cfg.pop_size)]
    history = []
    pool = None
    if use_pool:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(n_workers, initializer=_init_worker,
                                            initargs=(task, net_cfg, cfg, worker_scorer))
    try:
      for gen in range(cfg.n_generations):
          cfg._gen = gen                          # fold generation into per-assay seeds (fix b)
          if pool is not None:
            res = pool.map(_eval_payload, [(g, gen) for g in pop])  # ship genome + gen
          else:
            res = [eval_fn(g) for g in pop]
          nps = np.array([r["n_params"] for r in res])
          fits = np.array([_fitness(r, r["n_params"], cfg) for r in res])

          order = np.argsort(-fits)
          # D115: train/test errors are REPORTING only and are no longer computed for the whole
          # population (that was ~2/3 of all evaluation cost). Re-evaluate ONLY the current best
          # genome with report=True — one extra evaluation per generation instead of pop_size x 2
          # extra behaves per assay, which is what makes a useful n_assays affordable.
          rep = report_fn(pop[order[0]])
          errs = np.full(len(res), np.nan); tests = np.full(len(res), np.nan)
          errs[order[0]] = rep["train_err"]; tests[order[0]] = rep["test_err"]
          history.append(dict(
            gen=gen,
            # best individual — the right convention for Gate B0 (can ANY genome interpolate?)
            best_train=float(errs[order[0]]), best_test=float(tests[order[0]]),
            best_params=int(nps[order[0]]),
            # population mean — the right convention for R&N's class-level Occam factor
            # D115: population-wide train/test no longer computed (reporting-only); NaN by design.
            mean_train=float("nan"), mean_test=float("nan"),
            mean_params=float(nps.mean()), std_params=float(nps.std()),
            mean_exc_frac=float(np.mean([r["exc_frac"] for r in res])),
            fit_mean=float(fits.mean()), fit_std=float(fits.std()),
            # D094 component means -- the pilot watches whether these PERSIST and COMPOUND under
            # selection (the real test that development+selection builds capability, not gen-0 noise).
            enc_mean=float(np.mean([r["encoding"] for r in res])),
            car_mean=float(np.mean([r["carrying"] for r in res])),
            reg_mean=float(np.mean([r["regulation"] for r in res])),
            enc_best=float(res[order[0]]["encoding"]),
            car_best=float(res[order[0]]["carrying"]),
            reg_best=float(res[order[0]]["regulation"]),
            # D101 diagnostics: dev convergence fraction (#4, is dev_ms long enough) + abort count (#6)
            dev_conv_frac=float(np.mean([r.get("dev_converged", True) for r in res])),
            dev_abort_n=int(np.sum([r.get("dev_aborted", False) for r in res])),
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
