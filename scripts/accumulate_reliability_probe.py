"""accumulate_reliability_probe.py - is the D134 fitness SELECTABLE? The D115 precondition, measured.

(Named to avoid `fitness_reliability_probe.py`, which is the committed D113/D114-era probe for the
retired covariance fitness. Different fitness, different task, different question.)

WHY THIS EXISTS. D136 asserted that "the precondition D115 requires is now met for the first time",
citing gen-0 = 0.517 with between-genome sd = 0.074. **That was never measured.** The 0.074 came from
six genomes at ONE noise draw each, so it conflates between-genome variance with measurement noise.
D115's machinery exists precisely to separate them and was not applied.

A partial sandbox run (n=2 genomes, 3 draws) put the real numbers far from the claim:

    all-neuron (D134 fitness) : mean 0.524  signal_sd 0.0104  noise_sd 0.0140  reliability 0.358
    driven-only               : mean 0.528  signal_sd 0.0018  noise_sd 0.0112  reliability 0.025

signal_sd is 0.010, not 0.074 -- the earlier figure was mostly measurement noise. And the driven cells
carry essentially NO between-genome signal, which makes sense: their score is passive leak and every
genome shares the same tau_slow. Whatever selectable variance exists comes from the ninety NON-driven
neurons -- from how much noise each genome contributes to the average. That is what D134's amendment
predicted, and it makes the gradient's DIRECTION the real question, not its existence.

n=2 is not a measurement. This runs it properly.

REPORTS, per readout: signal_sd (between-genome, what selection grips), noise_sd (within-genome across
independent draws), reliability = signal^2/(signal^2+noise^2). D124 declared a task unselectable at
~0.1-0.2. The ablated/passive-leak ceiling is 0.542 (D135) and intact must BEAT it for recurrence to be
contributing anything at all.

PRE-REGISTERED READ:
  reliability > 0.3 AND driven-only comparably high -> selection can grip integration quality itself.
      The strongest case for spending the arm.
  reliability > 0.3 but driven-only ~ 0 -> the gradient IS the noise-contribution term. Selection climbs
      by suppressing recurrent interference, walks to the ablated ceiling, and stops. The arm remains
      informative (that plateau is D136's pre-registered negative) but this is not promise.
  reliability < 0.2 -> D115 forbids the arm. Do not spend it.

Run:  python scripts/accumulate_reliability_probe.py --workers 6
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

_CTX = {}


def _init(ctx):
    """Per-worker setup ONCE (D064); task regenerated from seed, not shipped (D007)."""
    _CTX.update(ctx)
    E, y, rows, _ = make_accumulate(ctx["n_trials"], ctx["n_in"], seed=ctx["seed"])
    n = len(y)
    _CTX.update(E=E, y=y, rows=rows,
                fit=np.arange(n) < n // 2, te=np.arange(n) >= n // 2)


def _agg(S, cols):
    """D134 as amended: per-neuron HELD-OUT two-parameter affine, then the MEAN PREDICTION.

    Predictions, not scores -- the amendment measured 0.517 vs 0.114 (below chance). Aggregation
    weights are fixed at 1/N and never fitted, so D095's capacity bound is untouched.
    """
    fit, te, y = _CTX["fit"], _CTX["te"], _CTX["y"]
    P = np.empty((te.sum(), len(cols)))
    for k, j in enumerate(cols):
        A = np.vstack([S[fit, j], np.ones(fit.sum())]).T
        c, *_ = np.linalg.lstsq(A, y[fit], rcond=None)
        P[:, k] = S[te, j] * c[0] + c[1]
    p = P.mean(1)
    return 0.0 if p.std() < 1e-12 else float(abs(np.corrcoef(p, y[te])[0, 1]))


def _one(gi):
    """TOP-LEVEL and picklable (D007). One genome: every draw, plus its ablated control."""
    nc = SC.make_net_cfg(N=_CTX["N"], n_in=_CTX["n_in"])
    cfg = SC.make_trial_evolve_cfg()
    dens = _CTX["density"]
    g = random_genome(nc, dens, w0=SC.w0_for_density(dens) * _CTX["w0_mult"],
                      ei_split=cfg.ei_split, seed=_CTX["seed"] + gi)
    E, rows = _CTX["E"], _CTX["rows"]
    allc, drv = list(range(nc.N)), list(range(nc.n_in))
    net = EvoNet(g, nc)
    a, d = [], []
    for k in range(_CTX["n_draws"]):
        S = net.behave(E, noise_seed=300 + k)["state"][rows]
        a.append(_agg(S, allc))
        d.append(_agg(S, drv))
    Sa = EvoNet(replace(g, mag=np.zeros_like(g.mag)), nc).behave(E, noise_seed=300)["state"][rows]
    return dict(gi=gi, allneu=a, driven=d, ablated=_agg(Sa, allc))


def _decompose(X):
    """D115: split between-genome SIGNAL from within-genome NOISE. X is (genomes, draws)."""
    gm = X.mean(1)
    sig = float(np.std(gm, ddof=1))
    noi = float(np.mean(np.std(X, axis=1, ddof=1)))
    return float(gm.mean()), sig, noi, float(sig ** 2 / (sig ** 2 + noi ** 2 + 1e-12))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--genomes", type=int, default=10)
    ap.add_argument("--draws", type=int, default=4)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--n-in", type=int, default=10)
    ap.add_argument("--trials", type=int, default=300)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--w0-mult", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("accumulate_reliability_probe", log_dir="runs/fitness_reliability",
             header="is the D134 fitness selectable? D115 decomposition on accumulate"):
        print("N=%d n_in=%d density=%.2f w0x%g genomes=%d draws=%d trials=%d workers=%d"
              % (a.n, a.n_in, a.density, a.w0_mult, a.genomes, a.draws, a.trials, a.workers))
        print("D124 called a task UNSELECTABLE at reliability ~0.1-0.2. Passive-leak ceiling is 0.542.\n")

        ctx = dict(N=a.n, n_in=a.n_in, density=a.density, n_trials=a.trials,
                   n_draws=a.draws, seed=a.seed, w0_mult=a.w0_mult)
        t0 = time.time()
        if a.workers > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(a.workers, initializer=_init, initargs=(ctx,)) as pool:
                res = []
                for k, r in enumerate(pool.imap(_one, range(a.genomes)), 1):
                    res.append(r)
                    print("   %d/%d genomes done [%.0fs]" % (k, a.genomes, time.time() - t0), flush=True)
        else:
            _init(ctx)
            res = []
            for gi in range(a.genomes):
                res.append(_one(gi))
                print("   %d/%d genomes done [%.0fs]" % (gi + 1, a.genomes, time.time() - t0), flush=True)

        A = np.array([r["allneu"] for r in res])
        D = np.array([r["driven"] for r in res])
        abl = float(np.mean([r["ablated"] for r in res]))
        ch = r_null(a.trials - a.trials // 2)

        print("\n  chance %.3f | ABLATED (passive leak) %.3f | perfect integrator 1.000\n" % (ch, abl))
        print("  readout      | mean  | signal_sd | noise_sd | RELIABILITY")
        print("  -------------+-------+-----------+----------+------------")
        out = {}
        for lbl, X in (("all-neuron", A), ("driven-only", D)):
            m, sig, noi, rel = _decompose(X)
            out[lbl] = (m, sig, noi, rel)
            print("  %-12s | %.3f | %9.4f | %8.4f |   %.3f" % (lbl, m, sig, noi, rel))
        print("\n  per-genome all-neuron means: %s" % " ".join("%.3f" % v for v in A.mean(1)))

        m, sig, noi, rel = out["all-neuron"]
        _, dsig, _, drel = out["driven-only"]
        print("\nREAD:")
        print("  all-neuron reliability %.3f | driven-only reliability %.3f" % (rel, drel))
        if rel < 0.20:
            print("  BELOW THE D115 BAR. Selection cannot act on a signal under its own measurement")
            print("  noise -- the D124 situation at a new operating point. DO NOT spend the arm.")
        elif drel > 0.20:
            print("  SELECTABLE, AND THE SIGNAL IS IN THE DRIVEN CELLS' INTEGRATION QUALITY -- the")
            print("  strongest case for the arm: selection would grip what the task actually rewards.")
        else:
            print("  Selectable (%.3f) but driven-only carries almost none of it (%.3f), so the gradient"
                  % (rel, drel))
            print("  is the NOISE-CONTRIBUTION term: selection climbs by suppressing recurrent")
            print("  interference, walks toward the ablated ceiling %.3f, and stops. The arm remains" % abl)
            print("  informative -- that plateau is D136's pre-registered negative -- but this is not")
            print("  evidence that recurrence can be made to contribute.")
        print("\n  mean %.3f vs ablated %.3f: intact is %s the passive-leak ceiling."
              % (m, abl, "ABOVE" if m > abl else "BELOW"))


if __name__ == "__main__":
    main()
