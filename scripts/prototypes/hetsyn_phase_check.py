"""hetsyn_phase_check.py - is the D142 table confounded by COMMENSURATE delay/tau lattices? (PJM)

THE CONCERN. D142's delays [200, 400, 800] and tau grid [100, 200, 400, 800, 1600] are all powers of two
apart, so the two lattices are commensurate. Two mechanisms could exploit that:
  * ALIASING -- exp(-D/tau) takes values related by a common ratio, and a readout could latch onto that
    structure rather than onto genuine timescale coverage.
  * ENTRAINMENT -- tau_m = 20 ms with 40 Hz input gives a natural periodicity, so delays related by
    factors of two leave the network in comparable PHASE, and match/non-match could be read partly from
    phase rather than from trace amplitude.

TWO TESTS, CHEAPEST FIRST.

  A) PHASE SENSITIVITY (2 conditions, no redesign). If the readout exploits entrainment, performance
     should change noticeably for a SMALL delay perturbation -- 400 vs 420 ms. If it is pure trace
     amplitude, exp(-420/tau) vs exp(-400/tau) differs by ~1-5% and performance should barely move.
     **This distinguishes the mechanisms before committing to a redesign.**

  B) INCOMMENSURATE LATTICE. Delays [230, 370, 610] (pairwise ratios not small integers, similar span to
     [200, 800]) with a tau grid off the powers-of-two lattice. If D142's ordering (P=1 > P=3 > P=2)
     survives, the finding stands. If it changes, the whole table is a lattice artifact.

PRE-REGISTERED READ for (A):
  |delta| < ~0.03 across 400 vs 420 -> amplitude-driven; entrainment is NOT the mechanism and (B) is a
      formality worth running once.
  |delta| > ~0.08 -> phase matters, D142's table is suspect, and (B) is mandatory before any conclusion.

Run:  python scripts/prototypes/hetsyn_phase_check.py --workers 6
"""
from __future__ import annotations
import argparse, itertools, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hetsyn_core import run_block, decode


def _job(args):
    """TOP-LEVEL and picklable -- Windows spawn cannot ship a closure (D007)."""
    tag, P, taus, delays, seed = args
    X, y = run_block(P, list(taus), list(delays), seed)
    return tag, P, taus, seed, decode(X, y)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--skip-b", action="store_true", help="run only the cheap phase-sensitivity test")
    a = ap.parse_args()

    jobs = []
    # (A) PHASE SENSITIVITY: single fixed delay, perturbed by 5%. Uses the taus that won in D142.
    for d in (400, 420):
        for P, taus in ((1, (1600.,)), (3, (1600., 200., 5.))):
            for s in range(a.seeds):
                jobs.append(("A", P, taus, (d,), s))
    # (B) INCOMMENSURATE lattice: delays and taus both off powers of two.
    if not a.skip_b:
        inc_delays = (230, 370, 610)
        inc_taus1 = [(t,) for t in (130., 290., 530., 970., 1810.)]
        inc_taus2 = [(t, 7.) for t in (130., 290., 530., 970., 1810.)]
        inc_taus3 = [(t2, t1, 7.) for t1, t2 in itertools.combinations((130., 290., 530., 970., 1810.), 2)]
        for P, grid in ((1, inc_taus1), (2, inc_taus2), (3, inc_taus3)):
            for taus in grid:
                for s in range(a.seeds):
                    jobs.append(("B", P, taus, inc_delays, s))

    print("jobs=%d  seeds=%d  workers=%d" % (len(jobs), a.seeds, a.workers))
    print("(A) 400 vs 420 ms, single delay -- phase sensitivity.")
    if not a.skip_b:
        print("(B) delays (230, 370, 610), taus off the powers-of-two lattice -- incommensurate check.\n")
    t0 = time.time()
    if a.workers > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(a.workers) as pool:
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

    print("\n(A) PHASE SENSITIVITY -- a 5%% delay change (400 -> 420 ms)")
    print("  P | taus                | 400 ms | 420 ms | delta")
    print("  --+---------------------+--------+--------+-------")
    deltas = []
    for P, taus in ((1, (1600.,)), (3, (1600., 200., 5.))):
        v = {}
        for d in (400, 420):
            accs = [r[4] for r in res if r[0] == "A" and r[1] == P and r[2] == taus and r[3] == (d,)]
            v[d] = float(np.mean(accs)) if accs else float("nan")
        dl = v[420] - v[400]
        deltas.append(abs(dl))
        print("  %d | %-19s | %.3f  | %.3f  | %+.3f" % (P, str(tuple(int(t) for t in taus)),
                                                        v[400], v[420], dl))
    md = max(deltas) if deltas else float("nan")
    print("\n  largest |delta| = %.3f" % md)
    if md < 0.03:
        print("  AMPLITUDE-DRIVEN. A 5%% delay change barely moves performance, so entrainment/phase is")
        print("  not the mechanism and D142's table is not a phase artifact.")
    elif md > 0.08:
        print("  PHASE MATTERS. D142's table is suspect and the incommensurate check is mandatory.")
    else:
        print("  Ambiguous at this power. Add seeds before concluding.")

    if not a.skip_b:
        print("\n(B) INCOMMENSURATE LATTICE -- delays (230, 370, 610), taus off powers of two")
        print("  P | best taus            | mean  |  sd")
        print("  --+----------------------+-------+------")
        best = {}
        for P in (1, 2, 3):
            rows = {}
            for tag, Pp, taus, seed, acc in res:
                if tag == "B" and Pp == P:
                    rows.setdefault(taus, []).append(acc)
            if not rows:
                continue
            taus, accs = max(rows.items(), key=lambda kv: np.mean(kv[1]))
            m = float(np.mean(accs))
            sd = float(np.std(accs, ddof=1)) if len(accs) > 1 else 0.0
            best[P] = m
            print("  %d | %-20s | %.3f | %.3f" % (P, str(tuple(int(t) for t in taus)), m, sd))
        if len(best) == 3:
            order = sorted(best, key=lambda k: -best[k])
            print("\n  ordering: P=%d > P=%d > P=%d" % tuple(order))
            print("  D142 (commensurate) gave P=1 > P=3 > P=2.")
            print("  SAME ordering -> D142 stands. DIFFERENT -> D142's table is a lattice artifact.")


if __name__ == "__main__":
    main()
