"""hetsyn_config_scan.py - find the (trial length, tau cap) configuration BY MEASURING (D145).

WHY EMPIRICALLY. An ideal-observer scan identified 320 ms / cap 125 as the configuration where the
diagonal survives AND every tau sits in the PNAS biological band. In spiking it collapsed: nothing
cleared 0.4 sd, every winning tau set sat at the grid edge, and m=2's seed sd rose fivefold to 0.104
(D145). The ideal observer cannot represent the two effects that killed it -- fewer spikes per segment
at shorter segment durations, and an effective integration window shortened by the tau_r=30 ms readout
filter and the threshold nonlinearity. **It is a reliable guide to whether a demand EXISTS and an
unreliable guide to whether the demand is MEASURABLE.**

So the (trial, cap) pair is found by measurement. Two anchors are known:
  800 ms, uncapped  -> diagonal HOLDS (D143), but winning taus reach 1600 ms, above the PNAS band
  320 ms, cap 125   -> diagonal GONE (D145)

WHAT THIS SCANS. Configurations between the anchors, at m=2 and m=3 only (m=1 cannot show a diagonal --
it has no P=0 to gain over, the error D143's verdict made). Longer segments are preferred over shorter
at equal trial length, since segment duration drives per-segment SNR.

METRIC. For each configuration, the DIAGONAL SCORE: the gain at P=m minus the largest off-diagonal gain,
in units of the pooled seed sd. Positive and large means the diagonal is present and resolvable; near
zero means noise, whatever the raw gains look like.

WARNING - PROVISIONAL BY CONSTRUCTION (PJM). Every result here uses hand-set taus from a fixed grid. A GA
searches continuously and will find combinations no grid expresses, so the configuration that best
supports a diagonal under GRID SEARCH need not be the one that best supports it under SELECTION. Treat
the winner as a starting point for D144's single-P GA test, not as settled.

Run:  python scripts/prototypes/hetsyn_config_scan.py --workers 6
"""
from __future__ import annotations
import argparse, itertools, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hetsyn_core import run_stream, decode_reg, save_results

# (label, n_seg, seg_ms, tau_cap). Segment duration is held at >= 60 ms wherever possible: D145's
# collapse came partly from 40 ms segments carrying ~40% as many spikes as 100 ms ones.
# Three configurations, not five: at ~80 s/job a five-config scan is 750 jobs (~3 h on 6 workers) and
# the informative question is a LADDER between the two known anchors, not a dense grid. Each step here
# relaxes exactly one thing relative to the failed 320 ms / cap 125 point.
CONFIGS = [
    ("800ms/8x100/cap500",  8, 100, 500.),   # longest trial, cap still below the D143 winner (1600)
    ("800ms/8x100/cap250",  8, 100, 250.),   # same trial, tighter cap -- where does it break?
    ("480ms/8x60/cap250",   8,  60, 250.),   # shorter trial at 60 ms segments (D145: 40 ms was too few
]                                            # spikes per segment); tests whether trial length or
                                             # segment duration was the binding constraint


def tau_grid(cap, n=5):
    return list(np.geomspace(20.0, cap, n))


def _job(args):
    """TOP-LEVEL and picklable -- Windows spawn cannot ship a closure (D007)."""
    cfg_i, m, P, taus, seed = args
    _, n_seg, seg_ms, _ = CONFIGS[cfg_i]
    X, y = run_stream(P, list(taus), 4.0, seed, n_comp=m, n_seg=n_seg, seg_ms=seg_ms)
    return cfg_i, m, P, taus, seed, decode_reg(X, y)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--configs", type=int, nargs="+", default=list(range(len(CONFIGS))))
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    jobs = []
    for ci in a.configs:
        cap = CONFIGS[ci][3]
        g = tau_grid(cap)
        for m in (2, 3):                       # m=1 cannot show a diagonal
            for P in (1, 2, 3):
                for taus in itertools.combinations(g, P):
                    for s in range(a.seeds):
                        jobs.append((ci, m, P, tuple(taus), s))

    print("configs: %s" % ", ".join(CONFIGS[i][0] for i in a.configs))
    print("m in (2,3); P in (1,2,3); seeds=%d; jobs=%d; workers=%d" % (a.seeds, len(jobs), a.workers))
    print("Anchors: 800ms uncapped holds the diagonal (D143); 320ms/cap125 does not (D145).\n")
    t0 = time.time()
    if a.workers > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(a.workers, maxtasksperchild=4) as pool:
            res = []
            for k, r in enumerate(pool.imap_unordered(_job, jobs), 1):
                res.append(r)
                if k % 20 == 0 or k == len(jobs):
                    print("   %d/%d [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)
    else:
        res = []
        for k, j in enumerate(jobs, 1):
            res.append(_job(j))
            if k % 20 == 0 or k == len(jobs):
                print("   %d/%d [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)

    save_results("config_scan", res,
                 meta=dict(configs=[CONFIGS[i] for i in a.configs], seeds=a.seeds))

    print("\n  config              | m | P=1   | P=2   | P=3   | gain@m | best off-diag | DIAGONAL SCORE")
    print("  --------------------+---+-------+-------+-------+--------+---------------+---------------")
    scores = {}
    for ci in a.configs:
        tot = []
        for m in (2, 3):
            best, sds = {}, {}
            for P in (1, 2, 3):
                rows = {}
                for c, mm, Pp, taus, seed, acc in res:
                    if c == ci and mm == m and Pp == P:
                        rows.setdefault(taus, []).append(acc)
                if not rows:
                    continue
                taus, accs = max(rows.items(), key=lambda kv: np.mean(kv[1]))
                best[P] = float(np.mean(accs))
                sds[P] = float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0
            if len(best) < 3:
                continue
            gains = {P: best[P] - best[P - 1] for P in (2, 3)}
            pooled = float(np.mean(list(sds.values()))) + 1e-9
            on = gains[m] if m in gains else float("nan")
            off = max(v for k, v in gains.items() if k != m)
            score = (on - off) / pooled
            tot.append(score)
            print("  %-20s| %d | %.3f | %.3f | %.3f | %+.3f | %+.3f        | %+.1f sd"
                  % (CONFIGS[ci][0], m, best[1], best[2], best[3], on, off, score))
        if tot:
            scores[ci] = float(np.mean(tot))
        print("  --------------------+---+-------+-------+-------+--------+---------------+---------------")

    print("\nREAD (diagonal score = [gain at P=m] minus [best off-diagonal gain], in pooled seed sd):")
    for ci, sc in sorted(scores.items(), key=lambda kv: -kv[1]):
        print("   %-20s  mean over m=2,3: %+.1f sd" % (CONFIGS[ci][0], sc))
    if scores:
        bi = max(scores, key=lambda k: scores[k])
        if scores[bi] > 1.0:
            print("\n  BEST: %s (%+.1f sd). Longest tau in its grid is %d ms."
                  % (CONFIGS[bi][0], scores[bi], int(CONFIGS[bi][3])))
            print("  Take this to D144's single-P GA test -- and expect it to move, since a GA searches")
            print("  continuously where this scan searches a 5-value grid.")
        else:
            print("\n  NO CONFIGURATION SHOWS A RESOLVABLE DIAGONAL at these seeds. Either the biological")
            print("  cap is incompatible with a measurable effect in this substrate -- in which case the")
            print("  choice is 800 ms uncapped with a stated caveat -- or more seeds are needed to")
            print("  resolve it. Raise --seeds before concluding.")


if __name__ == "__main__":
    main()
