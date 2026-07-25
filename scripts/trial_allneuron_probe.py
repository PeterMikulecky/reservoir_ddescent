"""ALL-NEURON diagnostic (go/no-go for the all-neuron-aggregate selection arm).

The overnight null (DECISIONS D124) was measured through ONE arbitrary output neuron (R[:,0], D095).
This asks a narrower question the reliability probe could not: scoring EVERY neuron (each with its own
D095-weak affine readout), is there gen-0 between-genome signal that neuron-0 missed?

IT SETTLES NEITHER ARM -- it is a DECISION GATE (PJM's framing): the readouts were not persisted and,
more importantly, the evolved population was selected UNDER single-neuron pressure, so distributed
capability had no path to EXPRESS here. A null here does NOT prove all-neuron selection would stay flat;
a positive says the all-neuron arm has a gen-0 toehold worth an overnight. Read it as go/no-go only.

Reports, per population x dev-condition x basis:
  * single  (neuron 0)         -- reproduces the overnight baseline.
  * mean    (mean over 50)     -- the honest aggregate (a candidate fitness); robust to the N-lottery.
  * best    (max over 50)      -- the luckiest neuron; RISES with in-degree by chance, so read with care.
  For each: between-network signal_sd + ICC reliability (does the aggregate distinguish genomes?).
And two DISTRIBUTIONS (PJM):
  * ACROSS NEURONS (within/pooled): percentiles of per-neuron score -- are most neurons at chance with a
    thin tail (concentrated), or is signal spread across many (distributed)?
  * AMONG NETWORKS: per-genome count of neurons above a chance+2*noise threshold -- does the NUMBER of
    task-carrying neurons vary between genomes (something selection could grip) or is it uniform?

Usage:
  python trial_allneuron_probe.py [--n 30] [--draws 8] [--nval 80] [--populations random [evolved]]
                                  [--dev-conditions developed undeveloped] [--workers 6]
                                  [--evolved-ckpt runs/reliability/evolved_pop.pkl]
  Loading --evolved-ckpt reuses the overnight's evolved genomes (no re-evolve). Undeveloped random is
  cheap (no development); developed adds ~1-1.5 min/genome.
"""
import sys, argparse, pathlib, zlib
_here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parent)); sys.path.insert(0, str(_here))
import numpy as np, warnings
warnings.filterwarnings("ignore")

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet
from trial_reliability_probe import make_population


def score_one(col, y):
    """(trial_score, val_acc) for ONE neuron's rate column (n_val,) vs target y (n_val,), in-sample
    affine (matches the D095 readout, applied per neuron)."""
    A = np.vstack([col, np.ones(len(col))]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ coef
    nmse = float(np.mean((y - yhat) ** 2) / (np.var(y) + 1e-12))
    acc = float(np.mean(np.sign(yhat + 1e-12) == np.sign(y)))
    return 1.0 - nmse, acc


def collect_allneuron(genomes, task, net_cfg, cfg, draws, develop, base_seed):
    """Per genome: develop (or not), then `draws` behaves capturing ALL-N state at the val read rows.
    Returns S[basis] arrays of shape (G, draws, n_val, N)."""
    rows = task.response_rows("val"); y = task.Y_val[:, 0]
    N = net_cfg.N
    out = []
    for gi, g in enumerate(genomes):
        net = EvoNet(g, net_cfg)
        if develop and cfg.dev_ms and cfg.dev_ms > 0:
            gseed = (zlib.crc32(g.mag.tobytes()) ^ (cfg.seed & 0xFFFFFFFF)) & 0x7FFFFFFF
            net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms, warmup_ms=SC.WARMUP_MS,
                        n_checkpoints=4, seed=gseed)
        draws_states = [net.behave(task.E_val, noise_seed=(base_seed + 131 * gi + 7 * k + 1) & 0x7FFFFFFF)["state"][rows]
                        for k in range(draws)]
        out.append(np.stack(draws_states))     # (draws, n_val, N)
        print("    genome %2d done" % gi, flush=True)
    return out, y, N


def analyze(states, y, N, basis):
    """states: list of (draws, n_val, N). Returns per-(genome,neuron) mean score & noise, then the
    single/mean/best aggregates and distributions."""
    G = len(states); K = states[0].shape[0]
    bi = 0 if basis == "trial_score" else 1
    # per (genome, neuron, draw) score
    s = np.zeros((G, N, K))
    for gi in range(G):
        for k in range(K):
            St = states[gi][k]                                  # (n_val, N)
            for j in range(N):
                s[gi, j, k] = score_one(St[:, j], y)[bi]
    mean_gj = s.mean(axis=2)                                    # (G, N) draw-averaged per-neuron score
    noise_gj = s.var(axis=2, ddof=1)                           # per-neuron measurement variance

    def icc(agg_gk):                                            # agg_gk: (G, K) per-draw aggregate
        nv = float(np.mean(agg_gk.var(axis=1, ddof=1)))
        between = float(agg_gk.mean(axis=1).var(ddof=1))
        sig = max(0.0, between - nv / K)
        return sig ** 0.5, nv ** 0.5, (sig / (sig + nv / K) if sig + nv / K > 1e-18 else float("nan"))

    single = icc(s[:, 0, :])                                    # neuron 0 per-draw
    mean_agg = icc(s.mean(axis=1))                             # mean over neurons, per draw
    jbest = mean_gj.argmax(axis=1)                            # best neuron per genome (by draw-mean)
    best_agg = icc(np.stack([s[gi, jbest[gi], :] for gi in range(G)]))

    # distributions
    pooled = mean_gj.reshape(-1)                                # all per-neuron scores
    pct = np.percentile(pooled, [50, 90, 99, 100])
    thr = np.median(pooled) + 2.0 * np.sqrt(np.mean(noise_gj))  # chance + 2*typical per-neuron noise
    n_above = (mean_gj > thr).sum(axis=1)                      # per genome: #neurons above threshold
    return dict(single=single, mean=mean_agg, best=best_agg,
                pooled_pct=pct, thr=thr, n_above=n_above, mean_gj=mean_gj)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--draws", type=int, default=8)
    ap.add_argument("--nval", type=int, default=80)
    ap.add_argument("--populations", nargs="+", default=["random"], choices=["random", "evolved"])
    ap.add_argument("--dev-conditions", nargs="+", default=["undeveloped"],
                    choices=["developed", "undeveloped"])
    ap.add_argument("--evolve-gens", type=int, default=40)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--evolved-ckpt", default=None)
    args = ap.parse_args()

    task = SC.make_trial_task(n_val=args.nval)
    net_cfg = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg()
    hdr = ("allneuron: n=%d draws=%d nval=%d pops=%s dev=%s N=%d"
           % (args.n, args.draws, args.nval, ",".join(args.populations),
              ",".join(args.dev_conditions), net_cfg.N))
    with tee("trial_allneuron_probe", log_dir="runs/allneuron", header=hdr):
        print("ALL-NEURON go/no-go (settles NEITHER arm; decides which overnight to spend)")
        print(hdr)
        for pop_kind in args.populations:
            genomes = make_population(pop_kind, task, net_cfg, cfg, args.n, args.evolve_gens,
                                      workers=args.workers, ckpt=args.evolved_ckpt)
            for dev in args.dev_conditions:
                print("\n" + "=" * 88)
                print("POPULATION: %s   |   %s" % (pop_kind.upper(), dev.upper()))
                print("=" * 88)
                states, y, N = collect_allneuron(genomes, task, net_cfg, cfg, args.draws,
                                                 develop=(dev == "developed"), base_seed=7000)
                for basis in ("trial_score", "val_acc"):
                    r = analyze(states, y, N, basis)
                    print("\n  --- basis: %s ---" % basis)
                    for label, agg in [("single(n0)", r["single"]), ("mean(all)", r["mean"]),
                                       ("best(all)", r["best"])]:
                        print("    %-11s signal_sd=%.4f  noise_sd=%.4f  reliability=%.3f"
                              % (label, agg[0], agg[1], agg[2]))
                    p = r["pooled_pct"]
                    print("    across-neuron score distribution (median/90th/99th/max): %.3f / %.3f / %.3f / %.3f"
                          % (p[0], p[1], p[2], p[3]))
                    na = r["n_above"]
                    print("    #neurons above chance+2sd (thr=%.3f) per genome: median=%.0f max=%.0f "
                          "spread(sd)=%.2f  <- among-network variation in HOW MANY carry the task"
                          % (r["thr"], np.median(na), na.max(), na.std()))
        print("\nGO/NO-GO READ:")
        print("  * mean(all) signal_sd >> single(n0), reliability clears ~0.3-0.4  -> all-neuron arm has")
        print("    a gen-0 toehold single-neuron missed; worth an overnight.")
        print("  * mean(all) ~ single(n0), both flat, #-above-chance uniform across genomes -> no toehold;")
        print("    RL-in-development (which can manufacture a gradient the unsupervised floor cannot) is")
        print("    the better structural lever.")
        print("  * best(all) high but mean(all) flat -> lucky-neuron lottery (rises with in-degree at")
        print("    fixed N); NOT a selectable signal on its own -- do not be fooled by best alone.")


if __name__ == "__main__":
    main()
