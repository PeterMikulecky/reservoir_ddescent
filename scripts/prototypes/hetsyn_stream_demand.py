"""hetsyn_stream_demand.py - does the STRUCTURED ACCUMULATE task create a real demand for tau COUNT?

THE TASK.  target = sum(all segments) + lam * (final segment), evidence arriving THROUGHOUT the trial.

WHY IT SHOULD WORK WHERE DMTS DID NOT (D142). In DMTS the delay is DEAD TIME, so a timescale only has
to SURVIVE it -- one long tau does that and extra taus are redundant, which is why P=1 won. Here
information arrives continuously, and matching `alpha*sum(x) + beta*x_last` requires a weighting that is
simultaneously FLAT across the trial (for the sum) and PEAKED at the end (for recency). A single
exponential exp(-(T-t_k)/tau) cannot be both; two can approximate it. **The demand is on tau COUNT and
it is forced by geometry, not argued.**

ANALYTIC PRE-CHECK (ideal observer, no spikes, 4000 trials) -- run BEFORE any simulation:

    lam |  best 1 tau | best 2 tau |  gap
      0 |    0.9983   |   1.0000   | +0.002
      2 |    0.9350   |   0.9994   | +0.064
      4 |    0.9188   |   0.9996   | +0.081   <- peak
      8 |    0.9680   |   0.9998   | +0.032
    100 |    0.9997   |   1.0000   | +0.000

An inverted U: no advantage at either extreme (pure accumulation / pure recency), a clear peak around
lam ~ 4. **This is the check that D126, D141 and the variable-delay design never had** -- three task
designs adopted on mechanistic arguments, all of which failed on contact.

WHAT THIS SCRIPT ADDS. The SIMULATED version, where Poisson noise, the 30 ms tau_r filter and
thresholding will compress the gap. Available headroom is only ~0.08, so seeds matter.

PRE-REGISTERED READ:
  P=2 beats P=1 at intermediate lam by > 2 pooled sd, with the gap SHRINKING at lam=0 and lam large
      -> the demand survives spiking. The task is viable and the P axis has its first derived demand.
  no gap at any lam -> the noise floor swamps an 0.08 effect. Known BEFORE building a sweep on it.
  gap present but FLAT in lam -> something other than the intended mechanism is producing it; the
      inverted-U shape is the signature, not the gap alone.

Run:  python scripts/prototypes/hetsyn_stream_demand.py --workers 6
"""
from __future__ import annotations
import argparse, itertools, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hetsyn_core import run_stream, decode_reg

# 5 values, not 6: P=2 pairs drop from 15 to 10 and the run by a third. The grid spans 20-1600 ms and
# we are looking for a SHAPE across lam, not an optimum, so one fewer interior point costs little.
TAU_GRID = [20., 60., 200., 700., 1600.]


def _job(args):
    """TOP-LEVEL and picklable -- Windows spawn cannot ship a closure (D007)."""
    P, taus, lam, seed = args
    X, y = run_stream(P, list(taus), lam, seed)
    return P, taus, lam, seed, decode_reg(X, y)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lams", type=float, nargs="+", default=[0.0, 4.0, 100.0])
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    jobs = []
    for lam in a.lams:
        for t in TAU_GRID:                                   # P=1: one tau, swept
            for s in range(a.seeds):
                jobs.append((1, (t,), lam, s))
        for t1, t2 in itertools.combinations(TAU_GRID, 2):   # P=2: tau PAIRS, swept
            for s in range(a.seeds):
                jobs.append((2, (t2, t1), lam, s))

    print("lams=%s  seeds=%d  tau grid=%s  jobs=%d  workers=%d"
          % (a.lams, a.seeds, [int(t) for t in TAU_GRID], len(jobs), a.workers))
    print("Both P=1 and P=2 are swept over their OWN taus -- each compared at its best (D142's lesson).")
    print("Ideal-observer gap peaks at lam~4 (+0.081) and vanishes at lam=0 and lam=100.\n")
    t0 = time.time()
    if a.workers > 1:
        import multiprocessing as mp
        # maxtasksperchild recycles workers periodically. Brian2's code-generation cache grows within a
        # process, and the FIRST version of this script (which rebuilt the network every trial) showed
        # batches of 10 jobs going 668 s -> 1815 s across a run. The rebuild is fixed, but recycling is
        # cheap insurance against any residual growth.
        with mp.get_context("spawn").Pool(a.workers, maxtasksperchild=4) as pool:
            res = []
            for k, r in enumerate(pool.imap_unordered(_job, jobs), 1):
                res.append(r)
                if k % 10 == 0 or k == len(jobs):
                    print("   %d/%d [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)
    else:
        res = []
        for k, j in enumerate(jobs, 1):
            res.append(_job(j))
            print("   %d/%d [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)

    print("\n  lam  | P=1 best (tau)        | P=2 best (taus)            |  gap   | pooled sd | n sd")
    print("  -----+-----------------------+----------------------------+--------+-----------+------")
    summary = []
    for lam in a.lams:
        best = {}
        for P in (1, 2):
            rows = {}
            for Pp, taus, lm, seed, acc in res:
                if Pp == P and lm == lam:
                    rows.setdefault(taus, []).append(acc)
            if not rows:
                continue
            taus, accs = max(rows.items(), key=lambda kv: np.mean(kv[1]))
            best[P] = (float(np.mean(accs)),
                       float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0, taus)
        if 1 in best and 2 in best:
            gap = best[2][0] - best[1][0]
            pooled = np.sqrt((best[1][1] ** 2 + best[2][1] ** 2) / 2) + 1e-9
            summary.append((lam, gap, gap / pooled))
            print("  %-5g| %.3f (%4d)          | %.3f %-20s | %+.3f |   %.3f   | %4.1f"
                  % (lam, best[1][0], int(best[1][2][0]), best[2][0],
                     str(tuple(int(t) for t in best[2][2])), gap, pooled, gap / pooled))

    print("\nREAD:")
    if not summary:
        print("  no complete lam rows.")
        return
    peak = max(summary, key=lambda s: s[1])
    ends = [s for s in summary if s[0] == min(a.lams) or s[0] == max(a.lams)]
    print("  largest gap %+.3f at lam=%g (%.1f pooled sd)" % (peak[1], peak[0], peak[2]))
    if peak[2] > 2.0 and peak[1] > 0 and all(e[1] < peak[1] for e in ends):
        print("  THE DEMAND SURVIVES SPIKING, AND IT HAS THE INVERTED-U SHAPE: P=2 beats P=1 at")
        print("  intermediate lam and the advantage shrinks at both extremes. That is the SIGNATURE of")
        print("  the intended mechanism, not just a gap. The task is viable and lam positions P_crit.")
    elif peak[2] > 2.0:
        print("  A gap exists but it is NOT shaped like the prediction (it does not shrink at the")
        print("  extremes). Something other than the intended mechanism is producing it -- diagnose")
        print("  before building on it.")
    else:
        print("  NO GAP survives spiking. An 0.08 ideal-observer advantage is below this substrate's")
        print("  noise floor at these seeds. Known BEFORE a sweep was built on it -- raise seeds or")
        print("  trials to confirm, then abandon or redesign.")


if __name__ == "__main__":
    main()
