"""TRIAL-TASK FITNESS RELIABILITY - is selection on the cue->delay->probe XOR task measuring signal,
or noise? Re-baselines n_assays for the NEW task (D119: "D115's n_assays=4 was measured at the OLD
operating point" -- the trial task has a different, smaller fitness spread, so its reliability is
unknown).

WHY THIS EXISTS. D115 found fitness reliability ~0.05 at n_assays=1 on the covariance task -- selection
on approximately pure noise -- and lifted it with n_assays=4. Reliability is the BINDING constraint
(D119): without a reproducible fitness signal, selection cannot work and a 40-generation arm just
reproduces the D115 failure. The trial-task fitness (trial_score = 1 - val_err) is bounded differently
and, on unselected genomes, has a small spread, so n_assays=4 may or may not clear the floor here.

WHAT IT MEASURES (across a population of unselected genomes):
  * RELIABILITY (primary)    -- a variance decomposition. Single-draw fitness variance splits into
                                SIGNAL (true between-genome differences) and NOISE (within-genome
                                measurement scatter across noise draws). reliability at n_assays=k =
                                signal / (signal + noise/k) -- the fraction of the fitness a k-draw
                                estimate carries that is real. Well-defined at k=1, and it exposes the
                                signal/noise split directly (the interpretation note below turns on it).
  * r(val, test)             -- correlate the val-based fitness (what SELECTION sees) with the
                                test-based fitness (held-out) across genomes. D119's reported metric,
                                kept as a cross-check; it also folds in generalisation. (Needs enough
                                genomes to be stable -- use >=12; a handful of genomes makes it noise.)

Each genome is DEVELOPED ONCE (with the arm's real dev_eta/dev_ms) and then scored over many
independent noise draws, so sweeping n_assays is cheap -- no redevelopment per assay level.

CRITICAL INTERPRETATION. Low reliability has TWO causes and they need different responses:
  (a) too much MEASUREMENT NOISE  -> more assays fix it (signal_sd >> per-draw noise once averaged);
  (b) no TRUE fitness VARIANCE among unselected genomes (all ~chance on the XOR, since binding is
      selection-only) -> more assays DON'T help; the arm may simply have nothing to grip at gen 0.
The probe reports between-genome signal SD vs within-genome noise SD so you can tell which you have.
If (b), that is a statement about the TASK's gen-0 gradient, not a fixable measurement problem.

Usage:  python trial_reliability_probe.py [--genomes 8] [--draws 16] [--dev-ms 16000] [--delay 1]
"""
import sys, argparse, pathlib, zlib
_here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parent))
import numpy as np

from ddescent import study_config as SC
from ddescent.evonet import EvoNet, random_genome
from ddescent.trial_eval import _score_split


def _pearson(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")            # no variance to correlate (see interpretation note)
    return float(np.corrcoef(a, b)[0, 1])


def develop_and_sample(g, task, net_cfg, cfg, n_draws, base_seed):
    """Develop ONE genome once (as the arm would), then draw n_draws independent val/test fitnesses."""
    net = EvoNet(g, net_cfg)
    gseed = (zlib.crc32(g.mag.tobytes()) ^ (cfg.seed & 0xFFFFFFFF)) & 0x7FFFFFFF
    if cfg.dev_ms and cfg.dev_ms > 0:
        net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms, warmup_ms=SC.WARMUP_MS,
                    n_checkpoints=4, seed=gseed)
    vals, tests = [], []
    for i in range(n_draws):
        ev, _ = _score_split(net, task, "val",  (base_seed + 7 * i + 1) & 0x7FFFFFFF)
        et, _ = _score_split(net, task, "test", (base_seed + 7 * i + 2) & 0x7FFFFFFF)
        vals.append(1.0 - ev)          # trial_score = 1 - val_err (the fitness basis)
        tests.append(1.0 - et)
    return np.array(vals), np.array(tests)


def run(genomes=12, draws=8, dev_ms=None, delay=None, assays_grid=(1, 2, 4, 8), verbose=True):
    task = SC.make_trial_task(delay_segments=(SC.TRIAL["delay_segments"] if delay is None else delay))
    net_cfg = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg()
    if dev_ms is not None:
        cfg.dev_ms = dev_ms
    assays_grid = tuple(k for k in assays_grid if k <= draws)

    V = np.zeros((genomes, draws)); T = np.zeros((genomes, draws))
    for m in range(genomes):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=2000 + m)
        v, t = develop_and_sample(g, task, net_cfg, cfg, draws, base_seed=1000 + 101 * m)
        V[m] = v; T[m] = t
        if verbose:
            print("  genome %2d: fitness %.4f +/- %.4f (per-draw)" % (m, v.mean(), v.std()), flush=True)

    # --- one-way random-effects variance decomposition (the reliability core) --------------------
    # Single-draw fitness variance = SIGNAL (true between-genome) + NOISE (within-genome measurement).
    # Estimate each; reliability at n_assays=k is the fraction of variance that is signal once k draws
    # are averaged (noise falls as noise_var/k, signal does not). This is well-defined at k=1, unlike
    # a correlation over few genomes, and it cleanly separates the two causes of low reliability.
    noise_var = float(np.mean(V.var(axis=1, ddof=1)))            # mean within-genome variance
    between   = float(V.mean(axis=1).var(ddof=1))               # variance of per-genome mean estimates
    signal_var = max(0.0, between - noise_var / draws)          # unbiased true between-genome variance

    rows = []
    for k in assays_grid:
        denom = signal_var + noise_var / k
        reliability = (signal_var / denom) if denom > 1e-18 else float("nan")
        val_k = V[:, :k].mean(1); test_k = T[:, :k].mean(1)     # D119 cross-check at this n_assays
        rows.append(dict(n_assays=k, reliability=reliability, r_val_test=_pearson(val_k, test_k)))
    return dict(rows=rows, signal_sd=signal_var ** 0.5, noise_sd=noise_var ** 0.5,
                fitness_mean=float(V.mean()), n_genomes=genomes, draws=draws)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genomes", type=int, default=8)
    ap.add_argument("--draws", type=int, default=16, help="independent noise draws per genome (>= 2*max n_assays)")
    ap.add_argument("--dev-ms", type=float, default=None, help="override dev_ms (default = trial config)")
    ap.add_argument("--delay", type=int, default=None)
    args = ap.parse_args()
    import warnings; warnings.filterwarnings("ignore")

    print("TRIAL-TASK FITNESS RELIABILITY  (%d genomes, %d draws each, dev_ms=%s)"
          % (args.genomes, args.draws, args.dev_ms if args.dev_ms is not None else int(SC.trial_dev_ms())))
    print("developing genomes and sampling the noise ...")
    out = run(genomes=args.genomes, draws=args.draws, dev_ms=args.dev_ms, delay=args.delay)

    print("\n fitness mean=%.4f | SIGNAL sd (true between-genome)=%.4f | NOISE sd (per-draw)=%.4f"
          % (out["fitness_mean"], out["signal_sd"], out["noise_sd"]))
    snr = out["signal_sd"] / out["noise_sd"] if out["noise_sd"] > 1e-12 else float("inf")
    print(" single-draw signal/noise ratio = %.2f" % snr)
    print("\n n_assays | reliability | r(val,test)")
    print(" ---------+-------------+------------")
    for r in out["rows"]:
        print("    %2d    |    %5.3f    |   %+6.3f" % (r["n_assays"], r["reliability"], r["r_val_test"]))
    print("\n reliability = fraction of fitness variance that is TRUE signal after averaging n_assays")
    print(" draws (0=pure noise, 1=perfect). r(val,test) is D119's cross-check (COVARIANCE ref: 0.465")
    print(" PASS / 0.066 FAIL -- a different task, so read the trend, not the absolute threshold).")
    print("\n INTERPRETATION:")
    print("  - reliability RISES toward 1 with n_assays  -> noise-limited; n_assays is the right lever.")
    print("  - reliability stays LOW and SIGNAL sd tiny   -> little true variance among unselected")
    print("    genomes (XOR binding is selection-only): a gen-0 GRADIENT problem, not a noise problem;")
    print("    more assays won't help and the arm may not climb from random init at this difficulty.")
    print("  Rule of thumb: n_assays where reliability first clears ~0.3-0.4 is the cheapest usable set.")


if __name__ == "__main__":
    main()
