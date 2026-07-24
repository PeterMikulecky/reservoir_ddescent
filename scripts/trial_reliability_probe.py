"""TRIAL-TASK FITNESS RELIABILITY (proper). Is the trial_xor fitness a SELECTABLE signal, or noise --
and if noise, WHICH kind, and which lever fixes it cheapest?

Built for the cue->delay->probe XOR task (D120). The covariance-era fitness_reliability_probe.py is
RETIRED with its task; this is not an alias of it. It keeps that probe's one genuinely task-independent
idea -- separate true between-genome variance from measurement variance by how the estimate sharpens as
you average more -- and drops everything covariance-specific.

FOUR DECISIONS (PJM), each load-bearing:

1. TWO POPULATIONS, reported side by side.
   * RANDOM        -- unselected genomes. On a chance-by-construction task these cluster near the XOR
                      floor, so low reliability here can mean "no true variance yet" (a gen-0 GRADIENT
                      fact about the task) rather than "too noisy" -- a distinction random-only cannot
                      make.
   * LIGHTLY-EVOLVED -- a few generations of selection first, so genomes actually DIFFER in the ability
                      the task rewards (cue-holding, binding). Reliability HERE answers the question
                      that matters for selection: once genomes differ in skill, can the fitness
                      estimate TELL THEM APART? High on evolved but near-zero on random -> the arm has
                      no gen-0 gradient but IS selectable once moving (argues for a curriculum/seed,
                      not more assays).

2. BOTH BASES, side by side.
   * trial_score = 1 - val_err  -- the fitness selection actually optimises (NMSE-based, continuous).
   * val_acc                    -- the task's native meaning (binary, chance = 0.5). Different noise
                                   floor; reported so you can see whether the continuous fitness is
                                   noisier than the thing you care about.

3. TWO LEVERS SWEPT, because near the chance floor they trade off differently in COST.
   * n_assays -- average a independent noise draws over the full val set. Cost = a val-behaves (a x
                 per-behave overhead).
   * n_val    -- score over more trials per split. Cost = 1 behave with v trials (overhead paid once).
   Both cut measurement noise ~ 1/sqrt(total trials); n_val amortises the per-behave overhead, so if
   the two give equal reliability per trial, n_val is cheaper per unit reliability. The probe reports
   the noise under each so you can pick.

4. BOTH DECOMPOSITIONS, cross-checked.
   * ICC        -- from replication: noise_var = mean within-genome variance; signal_var =
                   var(genome means) - noise_var/draws; reliability(a) = signal/(signal + noise/a).
   * REGRESSION -- fit V_obs(a) = V_true + V_noise/a across the n_assays grid (uses the whole sweep;
                   better determined). Agreement is the confidence check; disagreement flags too-few
                   genomes or non-Gaussian noise.

EFFICIENCY. Each genome is DEVELOPED ONCE and behaved `draws` times on the val stream; every
(population x basis x n_assays x n_val) cell is then computed from the STORED readouts with no further
simulation. n_val is a subset of the stored val trials; n_assays is a subset of the stored draws.

Usage:
  python trial_reliability_probe.py [--n 30] [--draws 8] [--nval 20 40 80] [--assays 1 2 4 8]
                                    [--evolve-gens 5] [--dev-ms 16000] [--delay 1]
  --n>=30 per the standing statistical rule; drop it for a quick look. Cost scales as
  n x draws x max(nval) behaves x 2 populations -- a real (pre-arm, one-time) measurement.
"""
import sys, argparse, pathlib, zlib
_here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parent))
import numpy as np, warnings
warnings.filterwarnings("ignore")

from ddescent import study_config as SC
from ddescent.evonet import EvoNet, random_genome
from ddescent.evolve import _affine_nmse, run_evolution
from ddescent.trial_eval import trial_evaluate


# --- scoring: replicate trial_eval._score_split on the FIRST v trials of a stored readout ----------
def score_subset(R, Y, v):
    """(trial_score, accuracy) from readout R (n_val x d) and targets Y (n_val x 1) on first v trials.
    Uses the SAME in-sample per-output affine readout as _score_split (D095), so numbers match the arm."""
    Rv, Yv = R[:v], Y[:v]
    err = float(_affine_nmse(Yv, Rv))
    acc_cols = []
    for j in range(Yv.shape[1]):
        A = np.vstack([Rv[:, j], np.ones(len(Rv))]).T
        coef, *_ = np.linalg.lstsq(A, Yv[:, j], rcond=None)
        acc_cols.append(np.sign(A @ coef + 1e-12) == np.sign(Yv[:, j]))
    return 1.0 - err, float(np.mean(acc_cols))


# --- collect: develop each genome once, store `draws` independent val readouts ----------------------
def collect(genomes, task, net_cfg, cfg, draws, base_seed):
    rows = task.response_rows("val")
    Y = task.Y_val
    stored = []
    for gi, g in enumerate(genomes):
        net = EvoNet(g, net_cfg)
        gseed = (zlib.crc32(g.mag.tobytes()) ^ (cfg.seed & 0xFFFFFFFF)) & 0x7FFFFFFF
        if cfg.dev_ms and cfg.dev_ms > 0:
            net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms, warmup_ms=SC.WARMUP_MS,
                        n_checkpoints=4, seed=gseed)
        d = [net.behave(task.E_val, noise_seed=(base_seed + 131 * gi + 7 * k + 1) & 0x7FFFFFFF)["rates"][rows]
             for k in range(draws)]
        stored.append(np.stack(d))                 # (draws, n_val, d)
        print("    genome %2d done" % gi, flush=True)
    return stored, Y


# --- decomposition at one (n_val, basis): ICC + regression across the n_assays grid -----------------
def decompose(stored, Y, v, basis, assays):
    M = len(stored); K = stored[0].shape[0]
    S = np.zeros((M, K))
    for gi in range(M):
        for k in range(K):
            ts, acc = score_subset(stored[gi][k], Y, v)
            S[gi, k] = ts if basis == "trial_score" else acc

    noise_var = float(np.mean(S.var(axis=1, ddof=1)))                 # within-genome measurement var
    between   = float(S.mean(axis=1).var(ddof=1))                    # var of K-averaged genome means
    Vt_icc    = max(0.0, between - noise_var / K)                    # ICC signal variance

    aa = np.array([a for a in assays if a <= K], float)
    Vobs = np.array([S[:, :int(a)].mean(axis=1).var(ddof=1) for a in aa])
    A = np.vstack([np.ones_like(aa), 1.0 / aa]).T
    (Vt_reg, Vn_reg), *_ = np.linalg.lstsq(A, Vobs, rcond=None)
    Vt_reg = max(float(Vt_reg), 0.0); Vn_reg = float(Vn_reg)

    def _clip01(x):
        return float(min(1.0, max(0.0, x))) if x == x else x     # keep nan as nan
    rel = {}
    for a in assays:
        icc_a = (Vt_icc / (Vt_icc + noise_var / a)) if (Vt_icc + noise_var / a) > 1e-18 else float("nan")
        # regression reliability is only meaningful if the fit is physical (noise falls with a, i.e.
        # V_noise > 0). A degenerate fit (too few assay points / genomes) -> report nan, not nonsense.
        if Vn_reg > 1e-18 and (Vt_reg + Vn_reg / a) > 1e-18:
            reg_a = Vt_reg / (Vt_reg + Vn_reg / a)
        else:
            reg_a = float("nan")
        rel[int(a)] = (_clip01(icc_a), _clip01(reg_a))
    return dict(noise_var=noise_var, signal_var_icc=Vt_icc, signal_var_reg=Vt_reg, noise_var_reg=Vn_reg,
                rel=rel, fitness_mean=float(S.mean()))


def make_population(kind, task, net_cfg, cfg, n, evolve_gens, seed0=2000):
    randoms = [random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed0 + i)
               for i in range(n)]
    if kind == "random":
        return randoms
    # lightly-evolved: a few generations of real selection, then take the final population
    ecfg = SC.make_trial_evolve_cfg(pop_size=n, n_generations=evolve_gens,
                                    dev_ms=cfg.dev_ms, n_assays=max(1, min(2, cfg.n_assays)))
    print("  evolving population for %d generations (this is the expensive part) ..." % evolve_gens, flush=True)
    _, pop = run_evolution(task, net_cfg, ecfg,
                           eval_fn=lambda g: trial_evaluate(g, task, net_cfg, ecfg),
                           report_fn=lambda g: trial_evaluate(g, task, net_cfg, ecfg, report=True),
                           worker_scorer="trial", n_workers=1, verbose=False)
    return pop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--draws", type=int, default=8)
    ap.add_argument("--nval", type=int, nargs="+", default=[20, 40, 80])
    ap.add_argument("--assays", type=int, nargs="+", default=[1, 2, 4, 8])
    ap.add_argument("--evolve-gens", type=int, default=5)
    ap.add_argument("--dev-ms", type=float, default=None)
    ap.add_argument("--delay", type=int, default=None)
    ap.add_argument("--populations", nargs="+", default=["random", "evolved"],
                    choices=["random", "evolved"])
    args = ap.parse_args()

    nval_max = max(args.nval)
    task = SC.make_trial_task(delay_segments=(SC.TRIAL["delay_segments"] if args.delay is None else args.delay),
                              n_val=nval_max)
    net_cfg = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg()
    if args.dev_ms is not None:
        cfg.dev_ms = args.dev_ms
    assays = [a for a in args.assays if a <= args.draws]

    print("TRIAL-TASK FITNESS RELIABILITY (proper)")
    print("n=%d genomes, draws=%d, n_val sweep=%s (built %d), n_assays sweep=%s, dev_ms=%s, delay=%d"
          % (args.n, args.draws, args.nval, nval_max, assays,
             int(cfg.dev_ms) if cfg.dev_ms else 0, task.meta["delay_segments"]))
    if args.n < 30:
        print("  (n < 30: below the standing statistical rule; treat correlations/variances as indicative)")

    for pop_kind in args.populations:
        print("\n" + "=" * 84)
        print("POPULATION: %s" % pop_kind.upper())
        print("=" * 84)
        genomes = make_population(pop_kind, task, net_cfg, cfg, args.n, args.evolve_gens)
        print("  developing + sampling %d genomes x %d draws ..." % (len(genomes), args.draws), flush=True)
        stored, Y = collect(genomes, task, net_cfg, cfg, args.draws, base_seed=5000)

        for basis in ("trial_score", "val_acc"):
            print("\n  --- basis: %s ---" % basis)
            print("   n_val | signal_sd | noise_sd(1 draw) | reliability by n_assays (ICC / regression)")
            print("   ------+-----------+------------------+" + "-" * 44)
            noise_by_v = {}
            for v in args.nval:
                d = decompose(stored, Y, v, basis, assays)
                noise_by_v[v] = d["noise_var"]
                relstr = "  ".join("a%d:%.2f/%.2f" % (a, d["rel"][a][0], d["rel"][a][1]) for a in assays)
                print("    %3d  |  %.4f   |     %.4f       | %s"
                      % (v, d["signal_var_icc"] ** 0.5, d["noise_var"] ** 0.5, relstr))
            # lever comparison: does noise fall ~ 1/n_val (i.e. n_val interchangeable with n_assays)?
            vs = np.array(sorted(noise_by_v)); nv = np.array([noise_by_v[x] for x in vs])
            if len(vs) >= 2 and nv[-1] > 0:
                prod = nv * vs                                   # noise_var * n_val ; ~constant if ~1/n_val
                ratio = float(prod[0] / (prod[-1] + 1e-18))
                verdict = ("~constant -> more trials cut noise like more assays (cheaper: overhead paid once)"
                           if 0.5 < ratio < 2 else "NOT ~1/n_val -> n_val and n_assays are not interchangeable here")
                print("   n_val scaling: noise_var*n_val ratio across sweep = %.2f  (%s)" % (ratio, verdict))

    print("\nREAD:")
    print("  * RANDOM low + EVOLVED high  -> no gen-0 gradient but selectable once moving: use a")
    print("    curriculum/seed (D120 ramp), not more assays.")
    print("  * BOTH low, signal_sd tiny   -> little true variance anywhere: change the landscape.")
    print("  * reliability CLIMBS with n_assays and ICC~regression -> noise-limited; pick the n_assays")
    print("    (or n_val, if its scaling is ~constant above) where reliability first clears ~0.3-0.4.")
    print("  * ICC and regression DISAGREE -> too few genomes or non-Gaussian noise; raise --n.")


if __name__ == "__main__":
    main()
