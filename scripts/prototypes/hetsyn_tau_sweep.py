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
import argparse, itertools, time, warnings
import numpy as np

warnings.filterwarnings("ignore")
import brian2 as b2
from brian2 import ms
b2.prefs.codegen.target = "numpy"
b2.BrianLogger.suppress_name("resolution_conflict")

CUE, PROBE, RATE = 100, 100, 40.0


def run_block(P, taus, delays, seed, w=0.3, N=30, per_cat=15, nch=8, n_trials=144):
    """One (P, taus, seed) cell. Probe-aligned readout; cue synapses spread over the MEMORY groups."""
    rng = np.random.default_rng(seed)
    K = 2
    cue = rng.integers(0, K, n_trials)
    probe = rng.integers(0, K, n_trials)
    dsel = rng.integers(0, len(delays), n_trials)
    rel = (cue == probe).astype(int)
    out = np.zeros((n_trials, N))
    cur = " + ".join("I%d" % k for k in range(P))
    eqs = "\n".join(
        ["dv/dt = (-v + %s)/tau_m : 1 (unless refractory)" % cur]
        + ["dI%d/dt = -I%d/tau%d : 1" % (k, k, k) for k in range(P)]
        + ["dr/dt = -r/tau_r : 1"])
    ns = dict(tau_m=20 * ms, tau_r=30 * ms)
    for k, t_ in enumerate(taus):
        ns["tau%d" % k] = t_ * ms
    T_MAX = CUE + max(delays) + PROBE
    for t in range(n_trials):
        D = delays[dsel[t]]
        probe_on = CUE + D
        b2.start_scope()
        G = b2.NeuronGroup(N, eqs, threshold="v>1", reset="v=0; r+=1", refractory=2 * ms,
                           method="euler", namespace=ns)
        def sp(t0, t1):
            ii, tt = [], []
            for ch in range(nch):
                m = max(1, int(RATE * (t1 - t0) / 1000))
                tt += list(rng.uniform(t0, t1, size=m)); ii += [ch] * m
            ii = np.array(ii); tt = np.round(np.array(tt), 1)
            _, k = np.unique(np.stack([ii, tt]), axis=1, return_index=True)
            ii, tt = ii[k], tt[k]
            o = np.argsort(tt)
            return ii[o], tt[o]
        ci, ct = sp(1.0, CUE)
        pi, pt = sp(probe_on, probe_on + PROBE - 1.0)
        CU = b2.SpikeGeneratorGroup(nch, ci, ct * ms)
        PR = b2.SpikeGeneratorGroup(nch, pi, pt * ms)
        ctg = np.arange(cue[t] * per_cat, (cue[t] + 1) * per_cat)
        ptg = np.arange(probe[t] * per_cat, (probe[t] + 1) * per_cat)
        keep = []
        mem = list(range(max(1, P - 1)))          # all groups but the last are MEMORY groups
        for gi, grp in enumerate(mem):
            sub = ctg[gi::len(mem)]
            if len(sub) == 0:
                continue
            S = b2.Synapses(CU, G, on_pre="I%d += w" % grp, namespace=dict(w=w))
            S.connect(i=np.repeat(np.arange(nch), len(sub)), j=np.tile(sub, nch))
            keep.append(S)
        fast = P - 1 if P > 1 else 0              # the last group is the PROBE's fast channel
        Sp = b2.Synapses(PR, G, on_pre="I%d += w" % fast, namespace=dict(w=w))
        Sp.connect(i=np.repeat(np.arange(nch), len(ptg)), j=np.tile(ptg, nch))
        keep.append(Sp)
        M = b2.StateMonitor(G, "r", record=True, dt=5 * ms)
        b2.run(T_MAX * ms)
        i1 = int((probe_on + PROBE) / 5.0)        # PROBE-ALIGNED: 60 ms after probe offset
        out[t] = M.r[:, max(0, i1 - 12):i1].mean(1)
    return out, rel


def decode(X, y, n_part=3):
    n = len(y); acc = []
    for s in range(n_part):
        idx = np.random.default_rng(s).permutation(n)
        f, e = idx[:n // 2], idx[n // 2:]
        Z = (X - X[f].mean(0)) / (X[f].std(0) + 1e-9)
        A = np.hstack([Z[f], np.ones((len(f), 1))])
        c, *_ = np.linalg.lstsq(A, y[f] * 2.0 - 1, rcond=None)
        acc.append(np.mean(((np.hstack([Z[e], np.ones((len(e), 1))]) @ c) > 0) == (y[e] > 0)))
    return float(np.mean(acc))


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
