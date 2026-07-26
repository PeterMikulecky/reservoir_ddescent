"""trial_representation_sweep.py - representational quality vs P, WITHOUT selection (D128 follow-up).

THE QUESTION. D128 found that the match/non-match conjunction IS formed during the probe segment
(quad 0.783 vs null 0.539) but is available only to a SECOND-ORDER readout: linear decode at the same
stage is 0.479, chance. Under the reservoir premise the network's nonlinear expansion is what makes a
task variable linearly accessible to a weak reader. So "the relation is quadratic here" is not a defect
-- it is a MEASUREMENT of how much expansion this substrate performs at this operating point.

That quantity should change with P. Low P -> low effective dimensionality -> a conjunction that stays
second-order. Higher P -> richer dynamics -> at some point the conjunction becomes linearly separable.
If that transition exists, it is a NEW FUNCTIONAL LEVEL appearing on the P axis: exactly the encoding-
saturation mechanism the study proposes, and exactly what a second descent is supposed to signal.

WHY THIS NEEDS NO GA. Every quantity here is measured on RANDOM, UNDEVELOPED genomes. That removes a
circularity the project had walked into -- selection cannot be used to discover the P at which a task
first becomes selectable -- and it costs minutes per point instead of hours. It also answers, before any
sweep is funded, whether a selectable regime exists at all and where it starts.

WHAT IS MEASURED, at the PROBE stage (D128: where the conjunction lives; the READ segment is too late):
  PR          - participation ratio of the state (measures.participation_ratio): effective
                dimensionality of the representation. D075 measured PR_mean ~ 7 of 50 at the reference
                density. This is the D075-sense PR (activity covariance), NOT D127's PR over per-neuron
                task scores; they answer different questions and must not be conflated.
  linear      - decodability of match/non-match by a POOLED LINEAR readout. The headline: this is the
                order of readout D095's fitness is restricted to.
  quad        - decodability under PCA -> all pairwise products (full second order). D128's instrument,
                validated to clear two positive controls and stay at null on a negative control.
  quad_input  - the same, restricted to the n_in input neurons. Absent there means saturation closes the
                amplitude channel at ENTRY, before recurrence; present there but absent in the full
                state means the recurrent network discards it.
  Every one of these is reported against its own shuffled-target null. Never compare to 0.5.

DENSITY CONFOUND, ALREADY SOLVED BY THE PROJECT. Holding per-synapse magnitude fixed while sweeping
density makes TOTAL synaptic drive scale with P, which would confound representational change with a
simple drive increase. This sweep therefore uses SC.w0_for_density(d) at every point, the standing
w0 ~ 1/sqrt(density*N) discipline. Sweeping without it measures drive, not P.

PRE-REGISTERED READ (fixed before running):
  linear RISES with P and clears its null       -> the transition exists; that density is where the task
                                                   becomes selectable, and a GA arm below it is futile.
  linear FLAT at null while quad clears         -> the conjunction forms at every P but the reservoir
                                                   conversion to linear accessibility never happens.
                                                   That is a finding about the substrate, not the task.
  quad ALSO falls at low P                      -> forming the conjunction itself requires P.
  PR tracks linear                              -> effective dimensionality is the mechanism, and D127's
                                                   choice of a PR-family endpoint is vindicated.

Run:  python scripts/trial_representation_sweep.py [--densities ...] [--genomes N] [--trials N]
"""
from __future__ import annotations
import argparse
import time
import warnings

import numpy as np

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet, random_genome
from ddescent.measures import participation_ratio

# Single source of truth for the VALIDATED decoders (D128). Importing rather than copying so the
# instrument that produced D128 is byte-identical to the one used here.
from delay_persistence_probe import decode, decode_null, _expand, stage_rows

DEFAULT_DENSITIES = [0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.70, 0.90]


def sweep(densities, n_genomes: int = 4, n_trials: int = 400, seed: int = 1,
          stage: str = "probe") -> list[dict]:
    cfg = SC.make_trial_evolve_cfg()
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials)
    rel = (task.cue_test == task.probe_test).astype(int)
    rows_idx = None
    out, t_start = [], time.time()
    for di, dens in enumerate(densities):
        nc = SC.make_net_cfg()
        w0 = SC.w0_for_density(dens)          # D-standing: hold input fluctuations constant vs P
        if rows_idx is None:
            rows_idx = stage_rows(task, "test", stage)
        acc = {k: [] for k in ("pr", "lin", "quad", "quad_in")}
        nul = {k: [] for k in ("lin", "quad", "quad_in")}
        for g_i in range(n_genomes):
            g = random_genome(nc, dens, w0=w0, ei_split=cfg.ei_split, seed=seed + 1000 * di + g_i)
            B = EvoNet(g, nc).behave(task.E_test, noise_seed=2 + g_i)
            X = B["state"][rows_idx]                       # (n_trials, N) at the probe stage
            Xin = X[:, : nc.n_in]                          # input neurons only
            acc["pr"].append(participation_ratio(X))
            Zl, Zq, Zi = X, _expand(X, "quad", seed=g_i), _expand(Xin, "quad", seed=g_i)
            for key, Z in (("lin", Zl), ("quad", Zq), ("quad_in", Zi)):
                acc[key].append(decode(Z, rel))
                nul[key].append(decode_null(Z, rel, n_rep=30)[1])
        row = dict(density=dens, P=int(round(dens * nc.N * (nc.N - 1))), w0=round(w0, 4))
        for k in acc:
            row[k] = float(np.mean(acc[k]))
            row[k + "_sd"] = float(np.std(acc[k], ddof=1)) if n_genomes > 1 else 0.0
        for k in nul:
            row[k + "_null"] = float(np.mean(nul[k]))
            row[k + "_clears"] = bool(row[k] > row[k + "_null"])
        out.append(row)
        el = time.time() - t_start
        eta = el / (di + 1) * (len(densities) - di - 1)
        print("   density=%.2f  P=%4d  done   [%.0fs elapsed, ~%.0fs left]"
              % (dens, row["P"], el, eta), flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--densities", type=float, nargs="+", default=DEFAULT_DENSITIES)
    ap.add_argument("--genomes", type=int, default=4)
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--stage", type=str, default="probe")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("trial_representation_sweep", log_dir="runs/representation",
             header="representational quality vs P on RANDOM UNDEVELOPED genomes (D128 follow-up)"):
        print("stage=%s  genomes=%d  trials=%d  densities=%s"
              % (a.stage, a.genomes, a.trials, a.densities))
        print("w0 rescaled per density (w0 ~ 1/sqrt(density*N)) so P is not confounded with drive.\n")
        rows = sweep(a.densities, a.genomes, a.trials, a.seed, a.stage)

        print("\n  P     dens |   PR   |  linear (null)  |   quad (null)   | quad_in (null)")
        print("  ------------+--------+-----------------+-----------------+---------------")
        for r in rows:
            print("  %4d  %.2f | %6.2f | %.3f (%.3f) %s | %.3f (%.3f) %s | %.3f (%.3f) %s"
                  % (r["P"], r["density"], r["pr"],
                     r["lin"], r["lin_null"], "*" if r["lin_clears"] else " ",
                     r["quad"], r["quad_null"], "*" if r["quad_clears"] else " ",
                     r["quad_in"], r["quad_in_null"], "*" if r["quad_in_clears"] else " "))
        print("  (* = clears its own null)")

        lin_ok = [r for r in rows if r["lin_clears"]]
        print("\nREAD:")
        if lin_ok:
            print("  LINEAR clears from P=%d (density %.2f) upward -- a transition exists. That P is where"
                  % (lin_ok[0]["P"], lin_ok[0]["density"]))
            print("  the task becomes readable by a D095-weak fitness; a GA arm below it cannot work.")
        else:
            print("  LINEAR never clears at any P tested. If quad does, the conjunction forms but the")
            print("  reservoir conversion to linear accessibility does not happen -- a substrate finding.")
        print("  Compare PR against the linear column: if they track, effective dimensionality is the")
        print("  mechanism and D127's PR-family endpoint is measuring the right thing.")
        print("\n  UNDEVELOPED, RANDOM genomes throughout: no selection, no development, no fitness.")


if __name__ == "__main__":
    main()
