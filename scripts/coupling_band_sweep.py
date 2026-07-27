"""coupling_band_sweep.py - is there a w0 band where the D095-weak fitness can READ the task? (D133)

THE QUESTION. D133 found the signal dies at the first synapse: driven neurons carry the target at ~0.44,
one hop out it is at chance, at every N from 8 to 100 and with or without autapses. The synaptic INPUT to
hop-1 neurons carries signal (0.16-0.24, above chance), so E/I cancellation is not the cause -- the
neuron's own transfer is, with corr(input, output) only 0.18-0.28. The structural suspect is visible in
the code: `drive[:, :n_in] = input_gain * E` amplifies external input 10x while recurrent input is plain
`W @ state` with no gain, so downstream neurons never see the boost the driven ones do.

A coarse w0 sweep at N=50/n=3 found an INTERIOR OPTIMUM: corr(in,out) rises 0.211 -> 0.346 by w0x4,
hop1 |r| crosses chance, and the DESIGNATED FITNESS CELL reaches 0.195 at w0x8 -- above chance for the
first time since D125. But past x8 strong recurrence swamps the external drive and the DRIVEN neurons
degrade (hop0 0.426 -> 0.075 by x32). The band is narrow and the study sits at x1, on the dead side.

WHAT THIS SWEEP ADDS, and why the coarse result cannot be trusted as it stands:
  * The study's actual configuration -- N=100, n_in=10 -- not the diagnostic's N=50/n_in=4.
  * Enough genomes to put an error bar on the designated score. The 0.195 was n=3 in ONE condition and
    D115's rule forbids promoting it until it survives more power.
  * RELIABILITY of the designated score, not just its mean: between-genome signal against within-genome
    noise across independent draws. A fitness that is above chance but unreliable is still unusable --
    that is D115/D124 exactly, and it is the failure this project keeps rediscovering.
  * Finer resolution across x2..x16, where the coarse sweep showed the optimum.

THE TWO CURVES THAT MUST OVERLAP. Raising w0 helps transmission and hurts the driven representation.
The band is where BOTH are alive at once. If they do not overlap with room to spare at the study's
configuration, no operating point makes this architecture work as designed.

PRE-REGISTERED READ:
  designated above chance AND reliability > 0.3, with hop0 still alive  -> the band exists. That w0 is
      the operating point, and D129/D130/D124 should be re-run there before any of them is trusted.
  designated above chance but reliability low                          -> selection still has nothing to
      grip; a mean above chance is not a gradient (D115).
  no w0 where designated and hop0 are both alive                       -> the architecture cannot deliver
      the stimulus to a designated readout at any coupling. That is structural, and the response is to
      change the readout (D127's all-neuron arm) or the input wiring, not the operating point.

Run:  python scripts/coupling_band_sweep.py [--mults 2 3 4 6 8 12 16] [--workers 6]
"""
from __future__ import annotations
import argparse
import time
import warnings

import numpy as np

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet, random_genome

from task_screen import make_accumulate, r_null, _held_out_r
from propagation_probe import hop_distance, per_neuron_r

_CTX = {}


def _init(ctx):
    """Per-worker setup ONCE (D064); the task is regenerated from its seed, not shipped (D007)."""
    _CTX.update(ctx)
    _CTX["nc"] = SC.make_net_cfg(N=ctx["N"], n_in=ctx["n_in"])
    _CTX["cfg"] = SC.make_trial_evolve_cfg()
    E, y, rows, _ = make_accumulate(ctx["n_trials"], _CTX["nc"].n_in, seed=ctx["seed"])
    _CTX.update(E=E, y=y, rows=rows)


def _one(job):
    """TOP-LEVEL and picklable -- Windows spawn cannot ship a closure (D007). One (mult, genome) unit."""
    mult, gi = job
    nc, cfg = _CTX["nc"], _CTX["cfg"]
    E, y, rows = _CTX["E"], _CTX["y"], _CTX["rows"]
    dens = _CTX["density"]
    g = random_genome(nc, dens, w0=SC.w0_for_density(dens) * mult,
                      ei_split=cfg.ei_split, seed=_CTX["seed"] + gi)
    net = EvoNet(g, nc)
    dist = hop_distance(g.mag, nc.n_in)
    out_index = nc.N - nc.d
    per_draw = []
    for d in range(_CTX["n_draws"]):
        S = net.behave(E, noise_seed=200 + d)["state"][rows]
        r = per_neuron_r(S, y)
        per_draw.append(dict(hop0=float(r[dist == 0].mean()),
                             hop1=float(r[dist == 1].mean()) if (dist == 1).any() else np.nan,
                             designated=float(r[out_index]),
                             # the D095 fitness as actually computed: a 2-param affine, held out
                             fitness=abs(_held_out_r(S[:, [out_index]], y)),
                             rate=float(S.mean())))
    return mult, per_draw


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mults", type=float, nargs="+", default=[1, 2, 3, 4, 6, 8, 12, 16])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--n-in", type=int, default=10)
    ap.add_argument("--genomes", type=int, default=8)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--trials", type=int, default=300)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("coupling_band_sweep", log_dir="runs/coupling_band",
             header="is there a w0 band where the D095-weak fitness can read the task? (D133)"):
        print("N=%d n_in=%d density=%.2f genomes=%d draws=%d trials=%d workers=%d"
              % (a.n, a.n_in, a.density, a.genomes, a.draws, a.trials, a.workers))
        print("w0 multipliers on w0_for_density(%.2f)=%.3f; 1.0 IS the study's current setting."
              % (a.density, SC.w0_for_density(a.density)))
        print("Task is `accumulate` -- the only candidate that cleared chance in the screen.\n")

        ctx = dict(N=a.n, n_in=a.n_in, density=a.density, n_draws=a.draws,
                   n_trials=a.trials, seed=a.seed)
        jobs = [(m, gi) for m in a.mults for gi in range(a.genomes)]
        t0 = time.time()
        if a.workers > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(a.workers, initializer=_init, initargs=(ctx,)) as pool:
                res = []
                for n_done, r in enumerate(pool.imap(_one, jobs), 1):
                    res.append(r)
                    print("   %d/%d done [%.0fs]" % (n_done, len(jobs), time.time() - t0), flush=True)
        else:
            _init(ctx)
            res = []
            for n_done, j in enumerate(jobs, 1):
                res.append(_one(j))
                print("   %d/%d done [%.0fs]" % (n_done, len(jobs), time.time() - t0), flush=True)

        ch = r_null(a.trials - a.trials // 2)
        print("\n  chance |r| = %.3f (per-neuron, n_test=%d)\n" % (ch, a.trials - a.trials // 2))
        print("  w0x  | hop0        | hop1        | designated  | FITNESS (sd) | reliability | rate")
        print("  -----+-------------+-------------+-------------+--------------+-------------+------")
        rows_out = []
        for m in a.mults:
            draws = [d for mm, d in res if mm == m]
            def col(k):
                return np.array([[dd[k] for dd in g] for g in draws])   # (genomes, draws)
            F = col("fitness")
            gm = F.mean(1)
            sig = float(np.std(gm, ddof=1))
            noi = float(np.mean(np.std(F, axis=1, ddof=1)))
            rel = sig ** 2 / (sig ** 2 + noi ** 2 + 1e-12)
            h0, h1, de = col("hop0").mean(), np.nanmean(col("hop1")), col("designated").mean()
            rows_out.append(dict(mult=m, hop0=h0, hop1=h1, designated=de,
                                 fitness=float(gm.mean()), fit_sd=float(gm.std(ddof=1)),
                                 rel=float(rel), rate=float(col("rate").mean())))
            def f(v):
                return "%.3f%s" % (v, "*" if v > ch else " ")
            print("  %-4g | %s      | %s      | %s      | %s (%.3f)|    %.3f    | %.3f"
                  % (m, f(h0), f(h1), f(de), f(float(gm.mean())), float(gm.std(ddof=1)),
                     rel, float(col("rate").mean())))
        print("  (* = above chance. FITNESS is the D095 2-param affine on the designated cell, held out.)")

        band = [r for r in rows_out
                if r["fitness"] > ch and r["rel"] > 0.30 and r["hop0"] > ch]
        above = [r for r in rows_out if r["fitness"] > ch and r["hop0"] > ch]
        print("\nREAD:")
        if band:
            b = max(band, key=lambda r: r["fitness"])
            print("  THE BAND EXISTS. At w0x%g the D095-weak fitness reads %.3f (chance %.3f) with"
                  % (b["mult"], b["fitness"], ch))
            print("  reliability %.3f, while the driven representation is still alive (hop0 %.3f)."
                  % (b["rel"], b["hop0"]))
            print("  That is the operating point. D124, D129 and D130 were all run at w0x1 and should be")
            print("  re-run here before any of them is trusted as a statement about this substrate.")
        elif above:
            b = max(above, key=lambda r: r["fitness"])
            print("  Fitness clears chance at w0x%g (%.3f) but reliability is only %.3f."
                  % (b["mult"], b["fitness"], b["rel"]))
            print("  A mean above chance is NOT a gradient: selection needs between-genome variance above")
            print("  measurement noise (D115/D124). More draws would tighten this; if it stays low, the")
            print("  designated-cell readout is unusable even in the band.")
        else:
            print("  NO w0 GIVES A READABLE FITNESS WITH THE DRIVEN REPRESENTATION INTACT. The two curves")
            print("  do not overlap: coupling strong enough to cross the synapse is strong enough to")
            print("  swamp the input. That is STRUCTURAL -- the response is to change the readout")
            print("  (D127's all-neuron arm) or the input wiring, not the operating point.")


if __name__ == "__main__":
    main()
