"""parameter_variance_screen.py - WHICH PARAMETERS SHOULD P COUNT? Measured, not inherited.

THE QUESTION, AND WHY IT PRECEDES EVERYTHING ELSE. `P = |W|` counts recurrent synapses. Everything
since D130 says those synapses do not participate: ablating them changes nothing or IMPROVES the score
(D135: 0.542 ablated vs 0.436-0.530 intact), and no operating point in a swept space of input_gain
0.5-50, coupling 0.25-8x, density 0.02-0.9, N 8-400, autapses, nmda_frac 0.5-0.98 and four block
architectures changes that. **A flat error-vs-P curve is the CORRECT result for a parameter count over
components that do not affect the measured function.** The flatness may never have been a finding about
double descent at all.

So before choosing another task or another operating point, measure which parameter CLASSES actually
generate heritable variance in function. That is what P should count, and it has never been measured --
D095 fixed the readout and D014 fixed P = |W| by inheritance from the covariance era, neither against
data.

THE DESIGN. Hold one base genome. For each class, build G variants differing ONLY in that class, and
measure the between-variant sd of the fitness. A class that produces no between-variant variance cannot
be selected on, whatever its cardinality -- and a class that does is a candidate for P regardless of
whether it is synaptic.

  input_cols   - the projection FROM the driven neurons (columns < n_in of the weight matrix).
                 D133/D134 say the driven cells carry essentially all the task signal (0.475 vs 0.054
                 for the designated cell), so this is the leading candidate.
  recurrent    - every other column. This is what `P = |W|` currently counts.
  signs        - E/I identity per neuron (D038).
  bias         - the constant drive. The f-I gain measurement (df/dI = 6.60 Hz per unit current) says
                 this is leverage-rich, and the neuroevolution scaffolding literature makes per-neuron
                 I_bias mutable for exactly this reason.
  v_thresh     - firing threshold.
  tau_m        - membrane time constant.

WARNING - WHAT THIS SCREEN CANNOT DO. `bias`, `v_thresh` and `tau_m` are GLOBAL scalars in `EvoNetConfig`, so
they are perturbed globally, which is a PROXY for what per-neuron variation would do. If a global
perturbation does not move function, per-neuron variation almost certainly will not either -- but the
converse does not follow, and a positive here means "worth making per-neuron", not "already is".
Magnitudes across classes are matched only in the loose sense of a comparable relative perturbation, so
**read this as which classes produce variance AT ALL, not as a precise ranking.**

READ (pre-registered):
  only `recurrent` produces variance -> the current P is right and the flat curves are real.
  `input_cols` or an intrinsic class dominates -> P should count those, and every error-vs-P curve
      measured so far was swept over the wrong parameters. That reframes D129 onward.
  NO class produces variance above the noise floor -> the substrate cannot be selected on at all in this
      configuration, which is the strongest form of the negative result and the end of the line.

Run:  python scripts/parameter_variance_screen.py [--variants 8] [--workers 6]
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

CLASSES = ("input_cols", "recurrent", "signs", "bias", "v_thresh", "tau_m")
_CTX = {}


def _init(ctx):
    _CTX.update(ctx)
    E, y, rows, _ = make_accumulate(ctx["n_trials"], ctx["n_in"], seed=ctx["seed"])
    n = len(y)
    _CTX.update(E=E, y=y, rows=rows,
                fit=np.arange(n) < n // 2, te=np.arange(n) >= n // 2)


def _agg(S, cols):
    """D134 (amended): per-neuron HELD-OUT two-parameter affine, then the MEAN PREDICTION."""
    fit, te, y = _CTX["fit"], _CTX["te"], _CTX["y"]
    P = np.empty((te.sum(), len(cols)))
    for k, j in enumerate(cols):
        A = np.vstack([S[fit, j], np.ones(fit.sum())]).T
        c, *_ = np.linalg.lstsq(A, y[fit], rcond=None)
        P[:, k] = S[te, j] * c[0] + c[1]
    p = P.mean(1)
    return 0.0 if p.std() < 1e-12 else float(abs(np.corrcoef(p, y[te])[0, 1]))


def _variant(job):
    """TOP-LEVEL and picklable (D007). One (class, variant) cell: perturb ONE class, score it."""
    cls, vi = job
    dens, sig = _CTX["density"], _CTX["sigma"]
    base_nc = SC.make_net_cfg(N=_CTX["N"], n_in=_CTX["n_in"])
    rng = np.random.default_rng(9000 + vi)
    over = {}
    # the BASE genome is identical for every variant; only the named class is redrawn
    g = random_genome(base_nc, dens, w0=SC.w0_for_density(dens),
                      ei_split=0.8, seed=_CTX["seed"])
    mag = g.mag.copy()
    signs = g.signs.copy()
    n_in = base_nc.n_in
    if cls == "input_cols":
        m = rng.lognormal(0.0, sig, size=mag[:, :n_in].shape)
        mag[:, :n_in] = mag[:, :n_in] * m
    elif cls == "recurrent":
        m = rng.lognormal(0.0, sig, size=mag[:, n_in:].shape)
        mag[:, n_in:] = mag[:, n_in:] * m
    elif cls == "signs":
        flip = rng.random(signs.size) < 0.10
        signs = signs * np.where(flip, -1.0, 1.0)
    elif cls == "bias":
        over["bias"] = float(base_nc.bias * rng.lognormal(0.0, sig))
    elif cls == "v_thresh":
        over["v_thresh"] = float(base_nc.v_thresh * rng.lognormal(0.0, sig))
    elif cls == "tau_m":
        over["tau_m"] = float(base_nc.tau_m * rng.lognormal(0.0, sig))
    nc = SC.make_net_cfg(N=_CTX["N"], n_in=_CTX["n_in"], **over)
    gg = replace(g, mag=mag, signs=signs)
    S = EvoNet(gg, nc).behave(_CTX["E"], noise_seed=100)["state"][_CTX["rows"]]
    return cls, vi, _agg(S, list(range(nc.N))), _agg(S, list(range(n_in))), float(S.mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--variants", type=int, default=8)
    ap.add_argument("--sigma", type=float, default=0.30,
                    help="lognormal sd of the perturbation, applied identically to every class")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--n-in", type=int, default=10)
    ap.add_argument("--trials", type=int, default=300)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("parameter_variance_screen", log_dir="runs/param_variance",
             header="which parameter classes generate heritable variance in function?"):
        print("N=%d n_in=%d density=%.2f variants=%d sigma=%.2f trials=%d workers=%d"
              % (a.n, a.n_in, a.density, a.variants, a.sigma, a.trials, a.workers))
        print("ONE base genome; each variant redraws exactly ONE parameter class.\n")
        ctx = dict(N=a.n, n_in=a.n_in, density=a.density, n_trials=a.trials,
                   seed=a.seed, sigma=a.sigma)
        jobs = [(c, v) for c in CLASSES for v in range(a.variants)]
        t0 = time.time()
        if a.workers > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(a.workers, initializer=_init, initargs=(ctx,)) as pool:
                res = []
                for k, r in enumerate(pool.imap(_variant, jobs), 1):
                    res.append(r)
                    print("   %d/%d done [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)
        else:
            _init(ctx)
            res = []
            for k, j in enumerate(jobs, 1):
                res.append(_variant(j))
                print("   %d/%d done [%.0fs]" % (k, len(jobs), time.time() - t0), flush=True)

        # the NOISE FLOOR: same genome, same everything, only the noise seed differs.
        _init(ctx)
        nc = SC.make_net_cfg(N=a.n, n_in=a.n_in)
        g = random_genome(nc, a.density, w0=SC.w0_for_density(a.density), ei_split=0.8, seed=a.seed)
        net = EvoNet(g, nc)
        floor = [_agg(net.behave(_CTX["E"], noise_seed=500 + k)["state"][_CTX["rows"]],
                      list(range(nc.N))) for k in range(4)]
        f_sd = float(np.std(floor, ddof=1))

        f_mean = float(np.mean(floor))
        ch = r_null(a.trials - a.trials // 2)
        print("\n  MEASUREMENT NOISE FLOOR (same genome, noise seed only): mean %.3f, sd = %.4f"
              % (f_mean, f_sd))
        print("  chance |r| at n_test=%d is %.3f" % (a.trials - a.trials // 2, ch))
        # UNDERPOWERED GUARD. A smoke run at 120 trials produced floor sd 0.17 against a fitness mean
        # of 0.05-0.17 -- below chance -- and the verdict logic duly printed "NO CLASS clears the noise
        # floor", which was a statement about the trial count, not the substrate. Same failure mode as
        # the first task_screen and the first coupling probe: a rule firing on data too weak to carry it.
        underpowered = (f_mean < ch) or (f_sd > 0.25 * max(f_mean, 1e-9))
        if underpowered:
            print("\n  *** UNDERPOWERED: baseline fitness %.3f vs chance %.3f, noise sd %.4f."
                  % (f_mean, f_sd if False else f_mean, f_sd))
            print("  *** No verdict is reported. Raise --trials (300+ is where fitness reads ~0.52)")
            print("  *** and/or --variants. Every number below is descriptive only.")
        print("\n  class        | fitness mean |  sd     | sd / noise floor | driven-only sd | rate")
        print("  -------------+--------------+---------+------------------+----------------+------")
        out = []
        for c in CLASSES:
            v = [r for r in res if r[0] == c]
            f = np.array([x[2] for x in v]); d = np.array([x[3] for x in v])
            sd = float(f.std(ddof=1)); ratio = sd / (f_sd + 1e-12)
            out.append((c, float(f.mean()), sd, ratio))
            print("  %-12s |    %.3f     | %.4f  |      %5.2f       |     %.4f     | %.3f"
                  % (c, f.mean(), sd, ratio, d.std(ddof=1), np.mean([x[4] for x in v])))
        print("  (sd / noise floor > ~2 means the class produces variance selection could act on.)")

        live = [o for o in out if o[3] > 2.0]
        rec = [o for o in out if o[0] == "recurrent"][0]
        print("\nREAD:")
        if underpowered:
            print("  WITHHELD -- the run is underpowered (see above). The class sds below the noise")
            print("  floor mean nothing at this trial count.")
        elif not live:
            print("  NO CLASS clears the noise floor. Nothing in this substrate can be selected on in")
            print("  this configuration -- the strongest form of the negative result, and the end of")
            print("  the operating-point line.")
        else:
            print("  Classes above the noise floor: %s"
                  % ", ".join("%s (%.1fx)" % (o[0], o[3]) for o in sorted(live, key=lambda x: -x[3])))
            if rec[3] <= 2.0:
                print("  ** `recurrent` does NOT clear it (%.1fx) -- yet P = |W| counts exactly those." % rec[3])
                print("  Every error-vs-P curve measured so far was swept over parameters that do not")
                print("  move function. P should be redefined over the classes that do.")
            else:
                print("  `recurrent` clears at %.1fx, so the current P is defensible." % rec[3])
        print("\n  Perturbation is lognormal(sigma=%.2f) applied identically to every class; read this" % a.sigma)
        print("  as WHICH CLASSES PRODUCE VARIANCE, not as a precise ranking between them.")


if __name__ == "__main__":
    main()
