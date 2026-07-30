"""hetsyn_tau_sweep.py - what can TWO memory timescales actually achieve under variable delay?

WHY. The D141 amendment found P=3 (taus 800, 250, 5) recovering to 0.690 where P=2 sits at chance
(0.509) under delays [200, 800] -- first support for `P ~ m + 1`, that P counts timescales in the MEMORY
pathway. But 0.690 is far short of the 0.963 P=2 reached at a SINGLE fixed delay, and **the taus were
picked by hand and never swept, so 0.690 is a LOWER BOUND on P=3, not its ceiling.** Quoting a
hand-picked value as a ceiling is exactly the error the D139 amendment was written to catch (where P=1's
"0.583" became 0.850 once its tau was swept).

WHAT THIS DOES. Sweeps the two MEMORY time constants at P=3 over a grid, replicates across seeds, and
reports P=1 and P=2 baselines with THEIR taus swept too -- so every condition is compared at its own
best, not at one arbitrary point.

WARNING - A BUG IN THE FIRST VERSION INVALIDATED AN ENTIRE 80-JOB RUN. The cue synapses were stored in
a LIST and passed to `b2.run()`, which uses magic collection: it scans the calling frame's VARIABLES, so
a Synapses object held only inside a list is invisible to it. Every trial therefore ran with probe input
and NO CUE INPUT AT ALL, silently, while printing plausible progress. Brian2 does warn
("getting deleted, but was never included in a network") but only at GARBAGE COLLECTION -- after the
results are computed, and after the window a short smoke test would inspect. Now fixed with an explicit
`b2.Network(*objs)` plus an assertion on the synapse count, which fails at construction rather than
after the run. Verified against `hetsyn_probe_aligned.py` (which escaped the bug by stashing synapses in
`globals()`, which collection DOES scan): P=1 0.495, P=2 0.509, P=3 0.690, reproduced exactly.

RUN LOCALLY (PJM's machine, --workers 6). This is the first result in the project that genuinely
benefits from parallelism; the sandbox is for smoke tests.

PRE-REGISTERED READ:
  P=3 best >> P=2 best, and P=3 best approaches the single-delay ceiling (~0.96)
      -> two memory timescales DO span two delays. `P ~ m + 1` holds, P_crit is placeable, and the
         sweep design is sound.
  P=3 best >> P=2 best but plateaus well below the ceiling (~0.7-0.8)
      -> two timescales help but do not span. Either more timescales per delay are needed, or the
         readout is the limit. Measure before designing around it.
  P=3 best ~ P=2 best once BOTH are swept
      -> the D141 amendment's 0.690 was a tau artifact and `P ~ m + 1` is NOT supported. That would be a
         serious problem for the sweep design, since P_crit-placeability is the property it rests on.

Run:  python scripts/prototypes/hetsyn_tau_sweep.py --workers 6
"""
from __future__ import annotations
import argparse, itertools, time
import numpy as np

# THE BLOCK-RUNNER AND DECODER LIVE IN ONE PLACE. Two prototypes with apparently-identical synapse
# construction diverged invisibly once already -- one used globals() (which Brian2's magic collection
# scans) and worked, this one used a list (which it does not) and silently ran an entire 80-job run
# with NO CUE INPUT. Importing rather than reimplementing is the fix for that class of divergence.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hetsyn_core import run_block, decode


def _job(args):
    """TOP-LEVEL and picklable -- Windows spawn cannot ship a closure (D007)."""
    P, taus, delays, seed = args
    X, y = run_block(P, list(taus), list(delays), seed)
    return P, taus, seed, decode(X, y)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--delays", type=int, nargs="+", default=[200, 800])
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--fast-tau", type=float, default=5.0)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    mem_grid = [100., 200., 400., 800., 1600.]
    jobs = []
    # P=1: one tau, doing BOTH memory and probe. Swept.
    for t1 in mem_grid:
        for s in range(a.seeds):
            jobs.append((1, (t1,), tuple(a.delays), s))
    # P=2: ONE memory tau + the fast probe channel. Swept.
    for t1 in mem_grid:
        for s in range(a.seeds):
            jobs.append((2, (t1, a.fast_tau), tuple(a.delays), s))
    # P=3: TWO memory taus + the fast probe channel. Swept over ordered pairs.
    for t1, t2 in itertools.combinations(mem_grid, 2):
        for s in range(a.seeds):
            jobs.append((3, (t2, t1, a.fast_tau), tuple(a.delays), s))

    print("delays=%s  seeds=%d  fast_tau=%.0f  jobs=%d  workers=%d"
          % (a.delays, a.seeds, a.fast_tau, len(jobs), a.workers))
    print("Every condition is swept over its OWN taus, so each is compared at its BEST (D139 amendment).\n")
    t0 = time.time()
    if a.workers > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(a.workers) as pool:
            res = []
            for k, r in enumerate(pool.imap_unordered(_job, jobs), 1):
                res.append(r)
                if k % 5 == 0 or k == len(jobs):
                    print("   %d/%d [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)
    else:
        res = []
        for k, j in enumerate(jobs, 1):
            res.append(_job(j))
            print("   %d/%d [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)

    print("\n  P | taus                     | mean  |  sd   | per-seed")
    print("  --+--------------------------+-------+-------+---------")
    best = {}
    for P in (1, 2, 3):
        rows = {}
        for Pp, taus, seed, acc in res:
            if Pp == P:
                rows.setdefault(taus, []).append(acc)
        for taus, accs in sorted(rows.items(), key=lambda kv: -np.mean(kv[1])):
            m, sd = float(np.mean(accs)), float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0
            if P not in best:
                best[P] = (m, sd, taus)
            print("  %d | %-24s | %.3f | %.3f | %s"
                  % (P, str(tuple(int(t) for t in taus)), m, sd,
                     " ".join("%.2f" % v for v in accs)))
        print("  --+--------------------------+-------+-------+---------")

    print("\nREAD (chance 0.500; P=2 at a SINGLE fixed delay reached 0.963):")
    for P in (1, 2, 3):
        if P in best:
            m, sd, taus = best[P]
            print("  P=%d best: %.3f (sd %.3f) at taus=%s" % (P, m, sd, tuple(int(t) for t in taus)))
    if 3 in best and 2 in best:
        gap = best[3][0] - best[2][0]
        pooled = np.sqrt((best[3][1] ** 2 + best[2][1] ** 2) / 2) + 1e-9
        print("\n  P=3 minus P=2 (both at their best): %+.3f, %.1f pooled sd" % (gap, gap / pooled))
        if gap > 2 * pooled and best[3][0] > 0.85:
            print("  TWO MEMORY TIMESCALES SPAN TWO DELAYS. `P ~ m + 1` holds and P_crit is placeable.")
        elif gap > 2 * pooled:
            print("  P=3 beats P=2 but plateaus below the single-delay ceiling. Two timescales HELP but")
            print("  do not fully span -- measure whether more per delay, or the readout, is the limit.")
        else:
            print("  P=3 ~ P=2 once BOTH are swept. The amendment's 0.690 was a tau artifact and")
            print("  `P ~ m + 1` is NOT supported -- a serious problem for the sweep design, whose")
            print("  P_crit-placeability rests on it.")


if __name__ == "__main__":
    main()
