"""nmda_coupling_sweep.py - the last untested variable: does SLOW current let recurrence integrate?

THE QUESTION. D135 found that ablating recurrence IMPROVES driven-neuron integration (0.542 vs
0.436-0.530 intact), monotonically across a 16x coupling range, and that the fitness is measuring passive
leak exactly: tau_slow = 100 ms covers ~2 of 8 x 50 ms segments, and sqrt(2/8) = 0.500 against an
observed 0.542. Together with D133 (signal does not cross the first synapse) that closes every route by
which P could matter -- UNLESS the one variable never moved is the one that matters.

`nmda_frac` is 0.5 in the trial config. The VALIDATED engineered ceiling requires ~0.7 and attributes its
sustained attractor to SLOW REVERBERATION. The parameter enters as a CHARGE SPLIT (D075):

    w_slow = f * w * (tau_syn / tau_slow)      w_fast = (1 - f) * w      total charge constant in f

so raising f does not add drive -- it redistributes the same charge into a channel that lasts 20x longer.
That is precisely what an integrator needs and what the fast channel cannot supply.

WHY THIS IS A 2D SWEEP AND NOT A LINE. The Wang (2002) mechanism needs BOTH slow current AND enough
recurrent gain to reverberate. Slow synapses with no loop gain decay; loop gain with only fast synapses
produces the runaway D130 and D132 both found. Neither knob alone is the hypothesis; their conjunction
is. So `nmda_frac` x w0, with the ablated network as the bar.

THE BAR IS 0.542, NOT CHANCE. That is what the DRIVEN neurons score with recurrence entirely removed
(D135) -- pure passive leak. Recurrence has to BEAT it, not merely clear chance. Every intact condition
measured so far has scored BELOW it. Reported as `d_ablate`; a positive number is the first evidence in
this project that recurrent synapses contribute anything to task performance.

PRE-REGISTERED READ:
  d_ablate > 0 at some (f, w0), replicating across genomes -> recurrence integrates. P has a mechanism,
      that cell is the operating point, and the GA arm becomes worth running there. D129/D130/D133/D135
      were all measured at f=0.5 and would need re-running.
  d_ablate <= 0 everywhere -> slow current does not rescue it either. Every knob this architecture
      exposes has now been swept, and the conclusion is structural rather than a tuning failure. The
      response is a different architecture or a different claim -- not another parameter.
  rate blow-up or silent units at high f x high w0 -> the usable region is bounded above; report where.

Run:  python scripts/nmda_coupling_sweep.py --workers 6
"""
from __future__ import annotations
import argparse
import time
import warnings
from dataclasses import replace

import numpy as np

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet, random_genome

from task_screen import make_accumulate, r_null

# A cell counts as showing a real contribution only if the PAIRED per-genome difference (intact minus
# ablated, SAME genome) clears this |t|. Set from D130's measured null: at n=6 paired samples the null
# |t| reaches 3.86 at p99, and a grid of this size has an expected maximum near 2.8 under the null. A
# bare "difference > 2 sd" rule is not a test -- a 2-genome smoke run of this very script duly reported
# "RECURRENCE INTEGRATES" on d_ablate = +0.022 with an sd estimated from two points.
T_THRESHOLD = 4.0
MIN_GENOMES = 6

_CTX = {}


def _init(ctx):
    """Per-worker setup ONCE (D064); task regenerated from seed, not shipped (D007)."""
    _CTX.update(ctx)
    E, y, rows, meta = make_accumulate(ctx["n_trials"], ctx["n_in"], seed=ctx["seed"])
    n = len(y)
    _CTX.update(E=E, y=y, rows=rows, n_seg=meta["n_seg"],
                fit=np.arange(n) < n // 2, te=np.arange(n) >= n // 2)


def _agg_pred(S, cols):
    """D134 (as amended): per-neuron HELD-OUT two-parameter affine, then the MEAN PREDICTION.

    Mean of PREDICTIONS, not of scores -- the amendment measured 0.517 vs 0.114 (below chance) for the
    two readings. Aggregation weights are fixed at 1/N and never fitted, so D095's capacity bound holds:
    no free parameter combines neurons.
    """
    fit, te, y = _CTX["fit"], _CTX["te"], _CTX["y"]
    P = np.empty((te.sum(), len(cols)))
    for k, j in enumerate(cols):
        A = np.vstack([S[fit, j], np.ones(fit.sum())]).T
        c, *_ = np.linalg.lstsq(A, y[fit], rcond=None)
        P[:, k] = S[te, j] * c[0] + c[1]
    p = P.mean(1)
    return 0.0 if p.std() < 1e-12 else float(abs(np.corrcoef(p, y[te])[0, 1]))


def _one(job):
    """TOP-LEVEL and picklable (D007). One (nmda_frac, w0 multiplier, genome) cell."""
    f, mult, gi = job
    nc = SC.make_net_cfg(N=_CTX["N"], n_in=_CTX["n_in"], nmda_frac=f)
    cfg = SC.make_trial_evolve_cfg()
    dens = _CTX["density"]
    g = random_genome(nc, dens, w0=SC.w0_for_density(dens) * mult,
                      ei_split=cfg.ei_split, seed=_CTX["seed"] + gi)
    E, rows = _CTX["E"], _CTX["rows"]
    drv, allc = list(range(nc.n_in)), list(range(nc.N))
    S = EvoNet(g, nc).behave(E, noise_seed=100)["state"][rows]
    Sa = EvoNet(replace(g, mag=np.zeros_like(g.mag)), nc).behave(E, noise_seed=100)["state"][rows]
    return dict(f=f, mult=mult, gi=gi,
                driven=_agg_pred(S, drv), allneu=_agg_pred(S, allc),
                ablated=_agg_pred(Sa, drv),
                rate=float(S.mean()), silent=float(np.mean(S.std(0) < 1e-6)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fracs", type=float, nargs="+", default=[0.5, 0.7, 0.9, 0.98])
    ap.add_argument("--mults", type=float, nargs="+", default=[1, 2, 4, 8])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--n-in", type=int, default=10)
    ap.add_argument("--genomes", type=int, default=4)
    ap.add_argument("--trials", type=int, default=300)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("nmda_coupling_sweep", log_dir="runs/nmda",
             header="does SLOW current let recurrence integrate? nmda_frac x coupling"):
        print("N=%d n_in=%d density=%.2f genomes=%d trials=%d workers=%d"
              % (a.n, a.n_in, a.density, a.genomes, a.trials, a.workers))
        print("nmda_frac %s (config is 0.5; the validated ceiling needs ~0.7)" % a.fracs)
        print("w0 multipliers %s on w0_for_density(%.2f)=%.3f" % (a.mults, a.density,
                                                                 SC.w0_for_density(a.density)))
        print("Charge-split (D075): raising f moves charge into the slow channel, it does NOT add drive.")
        print("THE BAR IS THE ABLATED SCORE, not chance -- recurrence must BEAT passive leak.\n")

        ctx = dict(N=a.n, n_in=a.n_in, density=a.density, n_trials=a.trials, seed=a.seed)
        jobs = [(f, m, gi) for f in a.fracs for m in a.mults for gi in range(a.genomes)]
        t0 = time.time()
        if a.workers > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(a.workers, initializer=_init, initargs=(ctx,)) as pool:
                res = []
                for k, r in enumerate(pool.imap(_one, jobs), 1):
                    res.append(r)
                    print("   %d/%d done [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)
        else:
            _init(ctx)
            res = []
            for k, j in enumerate(jobs, 1):
                res.append(_one(j))
                print("   %d/%d done [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)

        ch = r_null(a.trials - a.trials // 2)
        abl = float(np.mean([r["ablated"] for r in res]))
        print("\n  chance %.3f | ABLATED (passive leak, the BAR) %.3f | perfect integrator 1.000\n"
              % (ch, abl))
        print("  nmda | w0x | driven | all-100 | d_ablate (sd)  t   | rate  | silent")
        print("  -----+-----+--------+---------+--------------------+-------+-------")
        best = None
        for f in a.fracs:
            for m in a.mults:
                cell = [r for r in res if r["f"] == f and r["mult"] == m]
                # PAIRED: intact and ablated share a genome, so the difference is per-genome and its
                # sd measures variation in what RECURRENCE CONTRIBUTES, not variation in the metric.
                diff = np.array([c["driven"] - c["ablated"] for c in cell])
                d = float(np.mean([c["driven"] for c in cell]))
                dsd = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0
                t = float(diff.mean() / (dsd / np.sqrt(len(diff)) + 1e-12)) if dsd > 0 else 0.0
                sig = abs(t) > T_THRESHOLD and diff.mean() > 0 and len(diff) >= MIN_GENOMES
                if best is None or diff.mean() > best[0]:
                    best = (float(diff.mean()), f, m, d, dsd, t)
                print("  %-4g | %-3g | %.3f  |  %.3f  | %+.3f (%.3f) %+5.2f%s |  %.3f | %.3f"
                      % (f, m, d, float(np.mean([c["allneu"] for c in cell])),
                         diff.mean(), dsd, t, "*" if sig else " ",
                         float(np.mean([c["rate"] for c in cell])),
                         float(np.mean([c["silent"] for c in cell]))))
        print("  (* = PAIRED per-genome difference clears |t| > %.1f with n >= %d genomes.)"
              % (T_THRESHOLD, MIN_GENOMES))
        if a.genomes < MIN_GENOMES:
            print("  WARNING: --genomes %d is below %d. No cell can be called significant; the sd of a"
                  % (a.genomes, MIN_GENOMES))
            print("  paired difference is not estimable from so few points, and this script's own smoke")
            print("  run at n=2 produced a false positive. Treat every number below as descriptive.")

        da, f, m, d, dsd, t = best
        print("\nREAD:")
        print("  best d_ablate = %+.3f at nmda_frac=%g, w0x%g (driven %.3f, paired sd %.3f, t=%+.2f)"
              % (da, f, m, d, dsd, t))
        if abs(t) > T_THRESHOLD and da > 0 and a.genomes >= MIN_GENOMES:
            print("  RECURRENCE INTEGRATES. This is the first condition in the project where recurrent")
            print("  synapses contribute to task performance. That cell is the operating point, and")
            print("  D129/D130/D133/D135 -- all measured at nmda_frac=0.5 -- need re-running there")
            print("  before any is trusted. Then the GA arm.")
        else:
            print("  SLOW CURRENT DOES NOT RESCUE IT. Every knob this architecture exposes has now been")
            print("  swept: input_gain, coupling, density, N, autapses, block architecture, task class,")
            print("  readout, and nmda_frac. None produces a condition where recurrent synapses help.")
            print("  The conclusion is STRUCTURAL, not a tuning failure -- the response is a different")
            print("  architecture or a different claim, NOT another parameter.")


if __name__ == "__main__":
    main()
