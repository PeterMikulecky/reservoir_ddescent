"""hetsyn_component_scaling.py - does P_crit track the NUMBER OF TARGET COMPONENTS, in spiking?

THE PREDICTION, derived analytically before any simulation (ideal observer, 4000 trials):

    target         | P=1   | P=2   | P=3   | 2-1    | 3-2
    1 component    | 0.998 | 1.000 | 1.000 | +0.002 | +0.000
    2 components   | 0.919 | 1.000 | 1.000 | +0.081 | +0.000
    3 components   | 0.874 | 0.884 | 0.983 | +0.011 | +0.098

**The advantage appears exactly at P = m and vanishes beyond it.** That is a DIAGONAL, and it is the
signature to look for -- a gap alone could come from anything, but a gap that moves with m cannot.

WHY THIS MATTERS. `P_crit = m` makes the interpolation threshold POSITIONABLE: add a target component
and the threshold moves. That was the property D141's `P ~ m + 1` claimed for DELAY count and failed to
deliver (D142: swept properly, P=1 beat P=3 beat P=2). The difference is that this relation was checked
analytically first, and would have died for the cost of twenty lines if the diagonal had not appeared.

WHAT THE SIMULATION ADDS. Spiking noise, the 30 ms tau_r filter and thresholding compress the effect:
the 2-component gap fell from +0.081 (ideal) to +0.055 (spiking, 2.7 pooled sd) in the demand test. The
question is whether the DIAGONAL survives that compression, not whether the numbers match.

PRE-REGISTERED READ:
  gap peaks at P = m for every m, i.e. a diagonal -> P_crit tracks component count in spiking. The task
      family is viable and P_crit is positionable. Proceed to the sweep design.
  gaps present but NOT diagonal (e.g. P=2 always best) -> something other than component-matching is
      producing them. Diagnose before building.
  no gaps survive -> the ~0.05-0.10 ideal-observer effects are below this substrate's noise floor.
      Known BEFORE a sweep was built on it.

Run:  python scripts/prototypes/hetsyn_component_scaling.py --workers 6
"""
from __future__ import annotations
import argparse, itertools, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# hetsyn_core pins BLAS threads (before numpy) and provides run_stream / decode_reg / save_results.
from hetsyn_core import run_stream, decode_reg, save_results

TAU_GRID = [20., 60., 200., 700., 1600.]


def _job(args):
    """TOP-LEVEL and picklable -- Windows spawn cannot ship a closure (D007)."""
    n_comp, P, taus, seed = args
    X, y = run_stream(P, list(taus), 4.0, seed, n_comp=n_comp)
    return n_comp, P, taus, seed, decode_reg(X, y)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--comps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--ps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    jobs = []
    for m in a.comps:
        for P in a.ps:
            for taus in itertools.combinations(TAU_GRID, P):
                for s in range(a.seeds):
                    jobs.append((m, P, taus, s))

    print("components=%s  P=%s  seeds=%d  tau grid=%s" % (a.comps, a.ps, a.seeds,
                                                          [int(t) for t in TAU_GRID]))
    print("jobs=%d  workers=%d   (BLAS threads pinned to 1 in hetsyn_core)" % (len(jobs), a.workers))
    print("Every P swept over its OWN taus -- each compared at its best (D142's lesson).")
    print("Looking for a DIAGONAL: gap peaking at P = m.\n")
    t0 = time.time()
    if a.workers > 1:
        import multiprocessing as mp
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

    save_results("component_scaling", res,
                 meta=dict(comps=a.comps, ps=a.ps, seeds=a.seeds, tau_grid=TAU_GRID))

    best = {}
    print("\n   m  |  P  | best taus            | mean  |  sd   | gap vs P-1 | n sd")
    print("  ----+-----+----------------------+-------+-------+------------+------")
    for m in a.comps:
        prev = None
        for P in a.ps:
            rows = {}
            for mm, Pp, taus, seed, acc in res:
                if mm == m and Pp == P:
                    rows.setdefault(taus, []).append(acc)
            if not rows:
                continue
            taus, accs = max(rows.items(), key=lambda kv: np.mean(kv[1]))
            mu = float(np.mean(accs))
            sd = float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0
            best[(m, P)] = (mu, sd, taus)
            if prev is None:
                gap_s, nsd_s = "     --    ", "  -- "
            else:
                gap = mu - prev[0]
                pooled = np.sqrt((sd ** 2 + prev[1] ** 2) / 2) + 1e-9
                gap_s, nsd_s = "%+.3f     " % gap, "%4.1f" % (gap / pooled)
            print("   %d  |  %d  | %-20s | %.3f | %.3f | %s | %s"
                  % (m, P, str(tuple(int(t) for t in taus)), mu, sd, gap_s, nsd_s))
            prev = (mu, sd)
        print("  ----+-----+----------------------+-------+-------+------------+------")

    print("\nREAD:")
    diag_ok = []
    for m in a.comps:
        gaps = {}
        for P in a.ps:
            if P == min(a.ps) or (m, P) not in best or (m, P - 1) not in best:
                continue
            gaps[P] = best[(m, P)][0] - best[(m, P - 1)][0]
        if not gaps:
            continue
        peak = max(gaps, key=lambda k: gaps[k])
        hit = (peak == m)
        diag_ok.append(hit)
        print("   m=%d: largest gain at P=%d (%+.3f)%s"
              % (m, peak, gaps[peak], "   <- matches P=m" if hit else "   <- does NOT match P=m"))
    if diag_ok and all(diag_ok):
        print("\n  THE DIAGONAL SURVIVES SPIKING. P_crit tracks the number of target components, so the")
        print("  threshold is POSITIONABLE by task construction. The task family is viable; design the")
        print("  sweep around m.")
    elif any(g for g in diag_ok):
        print("\n  PARTIAL diagonal. Some m match and some do not -- read the per-row gaps before")
        print("  concluding; a single mismatched row may be power rather than mechanism.")
    else:
        print("\n  NO DIAGONAL. The gaps are not tracking component count, so something other than")
        print("  component-matching produces them. Diagnose before building a sweep on this task.")


if __name__ == "__main__":
    main()
