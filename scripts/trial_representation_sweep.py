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

WHY THIS NEEDS NO GA -- AND WHAT IT THEREFORE CANNOT SAY (PJM correction, 2026-07-25). Every quantity
here is measured on RANDOM, UNDEVELOPED genomes, which removes a circularity (selection cannot be used
to discover the P at which a task first becomes selectable) and costs minutes rather than hours.

But random genomes measure whether the conversion from second-order structure to linearly-readable rate
happens BY DEFAULT -- NOT whether selection could find it. Producing that conversion is precisely what
selection would be doing, so "the mean random genome does not clear at this P" does NOT license "a GA
arm at this P must fail." That is the D125 objection running in reverse: absence in an UNSELECTED
population cannot prove absence under selection.

Consequently this sweep reports the ACROSS-GENOME SPREAD and the BEST genome, not only the mean.
Selection grips variance. The mean is the wrong summary for a selectability question, and only the
cell "at null with negligible spread" is evidence that selection has nothing to climb.

Note also that D095 requires BOUNDED READOUT CAPACITY, not linearity. A weak second-order readout is
conceivable and is not ruled out by anything here -- though a per-neuron quadratic would not suffice,
since the relation is sum_i proj_i^2 and needs cross terms ACROSS neurons that x^2 on one unit cannot
supply.

THE READOUTS ARE A DESIGN AXIS, NOT A FIXED LINEAR GIVEN (PJM correction, 2026-07-25). D095's weak
affine constrains READOUT CAPACITY so the reader cannot absorb the work; it is not an endorsement of the
reservoir premise, and this project has deliberately developed alternatives to it -- most notably the
ALL-NEURON readout (D125/D127): N independent weak affine reads, aggregated by their SCORES. That is not
a pooled decoder in disguise; it is a summary of PER-NEURON decodability, and it answers the question
that matters here -- did any individual neuron end up carrying the relation?

So the sweep reports the project's ACTUAL readouts (single-neuron, all-neuron) alongside two diagnostic
UPPER BOUNDS (pooled linear, quad). The pooled linear decoder is the RC-style readout this project has
moved away from; it is retained ONLY because a negative from a stronger reader is a valid negative for a
weaker one. It is not the criterion for anything.

WHAT IS MEASURED, at the PROBE stage (D128: where the conjunction lives; the READ segment is too late):
  loc_single  - D095 weak affine on the DESIGNATED output neuron (index N-d). The current fitness.
  loc_mean    - mean over N independent weak affine reads (D127 all-neuron readout).
  loc_best    - best single neuron. Rises with in-degree at fixed N (D125), so read it with the mean.
  loc_n_above - how many neurons clear a null-calibrated threshold: the conversion counted per neuron.
  loc_pr      - D127's PR over per-neuron TASK SCORES: effective number of neurons carrying the
                relation, against its scrambled-target null. NOT the same as PR below.
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
  linear (MEAN) rises with P and clears         -> the conversion happens BY DEFAULT from that P up.
  linear SPREAD across genomes is large, or       -> selection has purchase even where the mean is at
    the best genome clears while the mean            null: it grips VARIANCE, not means. This, not the
    does not                                         mean, is the gen-0 selectability signal.
  linear at null with NEGLIGIBLE spread          -> nothing for selection to climb at that P. This is
                                                    the only cell that licenses "a GA arm here fails."
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
from ddescent.trial_eval import localization_report

# Single source of truth for the VALIDATED decoders (D128). Importing rather than copying so the
# instrument that produced D128 is byte-identical to the one used here.
from delay_persistence_probe import decode, decode_null, _expand, stage_rows

def _affine_score(v, y) -> float:
    """Accuracy of a TWO-PARAMETER affine (scale + offset) on a single scalar per trial.

    Exactly D095's capacity -- one gain, one offset, no mixing. What differs from D095 is not how much
    the readout may fit but WHAT SCALAR it is handed.
    """
    v = np.asarray(v, float)
    A = np.vstack([(v - v.mean()) / (v.std() + 1e-12), np.ones(len(v))]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return float(np.mean(np.sign(A @ coef + 1e-12) == np.sign(y)))


def relational_scalars(Xd, Xt) -> dict:
    """SELF-REFERENTIAL relational scalars: each trial's TEST state compared to its OWN DELAY state.

    Motivation (PJM). The discriminating quantity in DMTS is second-order across neurons
    (sum_i proj_i^2), which no per-neuron affine can express -- x^2 on one unit has no cross terms. But
    a DISTANCE has cross terms and costs no fitted parameters: the reference is the network's own prior
    activity, not a fitted mean or covariance. So this is second-order at D095 capacity.

The normalised scalars (cos, corr) are the principled ones: match keeps the test state ALIGNED with
    the delay state (cos -> 1) while non-match rotates it away (cos -> a/sqrt(a^2+b^2)).

    `eucl` and `tnorm` are included as amplitude-channel contrasts. To first order they should not
    discriminate -- match adds b along the cue direction, non-match along an orthogonal one, and
    ||b p_i|| == ||b p_j||. But because the trace DECAYS between delay and test, a match partially
    cancels: ||(b - ka) p_i|| vs ||-ka p_i + b p_j||, which differ. On synthetic states eucl reaches
    0.555 (marginal) and tnorm 0.662, so the amplitude channel does carry some of it. That matters
    because saturation at high input_gain is exactly what would close that channel -- if tnorm falls
    away in the real network while cos survives, the discrimination is geometric rather than amplitude.

    Passes omit_cue BY CONSTRUCTION: with no cue the delay state is baseline on every trial, so its
    alignment with the test state carries no relation information.
    """
    Xd = np.asarray(Xd, float); Xt = np.asarray(Xt, float)
    dn = np.linalg.norm(Xd, axis=1) + 1e-12
    tn = np.linalg.norm(Xt, axis=1) + 1e-12
    dot = np.sum(Xd * Xt, axis=1)
    Zd = Xd - Xd.mean(1, keepdims=True); Zt = Xt - Xt.mean(1, keepdims=True)
    corr = np.sum(Zd * Zt, axis=1) / ((np.linalg.norm(Zd, axis=1) + 1e-12) * (np.linalg.norm(Zt, axis=1) + 1e-12))
    return dict(cos=dot / (dn * tn), corr=corr,
                eucl=np.linalg.norm(Xt - Xd, axis=1), tnorm=tn)


def rsa_separation(X, labels, n_null: int = 60, seed: int = 0):
    """RSA with NO fitted parameters at all: does the trial-by-trial state geometry cluster by label?

    Builds the representational dissimilarity matrix (correlation distance between trial state
    vectors) and reports (between-class mean - within-class mean) / overall mean. Nothing is fitted,
    so this cannot carry its own interpolation threshold into a P sweep -- which is why it belongs in
    the DIAGNOSTIC layer and is safe there. Returned with a label-shuffled null.
    """
    X = np.asarray(X, float)
    Z = (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)
    C = (Z @ Z.T) / X.shape[1]
    D = 1.0 - C
    lab = np.asarray(labels).ravel()
    iu = np.triu_indices(len(lab), k=1)
    same = (lab[iu[0]] == lab[iu[1]])
    d = D[iu]
    def sep(mask):
        return float((d[~mask].mean() - d[mask].mean()) / (d.mean() + 1e-12))
    obs = sep(same)
    rng = np.random.default_rng(seed)
    nul = [sep(lab[rng.permutation(len(lab))][iu[0]] == lab[rng.permutation(len(lab))][iu[1]])
           for _ in range(n_null)]
    return obs, float(np.percentile(nul, 95))


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
            delay_idx = stage_rows(task, "test", "delay")
        acc = {k: [] for k in ("pr", "lin", "quad", "quad_in",
                               "loc_single", "loc_mean", "loc_best", "loc_n_above",
                               "loc_pr", "loc_pr_excess",
                               "cos", "corr", "eucl", "tnorm", "rsa", "rsa_null")}
        nul = {k: [] for k in ("lin", "quad", "quad_in")}
        for g_i in range(n_genomes):
            g = random_genome(nc, dens, w0=w0, ei_split=cfg.ei_split, seed=seed + 1000 * di + g_i)
            B = EvoNet(g, nc).behave(task.E_test, noise_seed=2 + g_i)
            X = B["state"][rows_idx]                       # (n_trials, N) at the probe stage
            Xin = X[:, : nc.n_in]                          # input neurons only
            acc["pr"].append(participation_ratio(X))
            # D127 all-neuron readout, applied to the RELATION (targets must be +-1 for sign scoring)
            L = localization_report(X, rel * 2.0 - 1.0, out_index=nc.N - nc.d, seed=g_i)
            for k in ("loc_single", "loc_mean", "loc_best", "loc_n_above", "loc_pr"):
                acc[k].append(float(L[k]))
            acc["loc_pr_excess"].append(float(L["loc_pr"] - L["loc_pr_null"]))
            Zl, Zq, Zi = X, _expand(X, "quad", seed=g_i), _expand(Xin, "quad", seed=g_i)
            for key, Z in (("lin", Zl), ("quad", Zq), ("quad_in", Zi)):
                acc[key].append(decode(Z, rel))
                nul[key].append(decode_null(Z, rel, n_rep=30)[1])
            # SELF-REFERENTIAL relational scalars at D095 capacity, and parameter-free RSA
            Xd = B["state"][delay_idx]
            yy = rel * 2.0 - 1.0
            for k, v in relational_scalars(Xd, X).items():
                acc[k].append(_affine_score(v, yy))
            r_obs, r_null = rsa_separation(X, rel, seed=g_i)
            acc["rsa"].append(r_obs); acc["rsa_null"].append(r_null)
        row = dict(density=dens, P=int(round(dens * nc.N * (nc.N - 1))), w0=round(w0, 4))
        for k in acc:
            row[k] = float(np.mean(acc[k]))
            row[k + "_sd"] = float(np.std(acc[k], ddof=1)) if n_genomes > 1 else 0.0
            row[k + "_max"] = float(np.max(acc[k]))          # selection grips the tail, not the mean
        for k in nul:
            row[k + "_null"] = float(np.mean(nul[k]))
            row[k + "_clears"] = bool(row[k] > row[k + "_null"])
            row[k + "_any_clears"] = bool(row[k + "_max"] > row[k + "_null"])
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

        print("\n  THE PROJECT'S READOUTS (weak, capacity-bounded -- these are what selection could use)")
        print("  P     dens | single | all-neuron mean | best  | n_above | PR_task (excess)")
        print("  -----------+--------+-----------------+-------+---------+-----------------")
        for r in rows:
            print("  %4d  %.2f | %.3f  |      %.3f      | %.3f |  %4.1f   | %5.2f (%+.2f)"
                  % (r["P"], r["density"], r["loc_single"], r["loc_mean"], r["loc_best"],
                     r["loc_n_above"], r["loc_pr"], r["loc_pr_excess"]))

        print("\n  CANDIDATE WEAK READOUTS -- second-order but D095 capacity (2 params on one scalar)")
        print("  P     dens |  cos  | corr  | eucl  | tnorm |  RSA sep (null)   [RSA fits nothing]")
        print("  -----------+-------+-------+-------+-------+--------------------")
        for r in rows:
            print("  %4d  %.2f | %.3f | %.3f | %.3f | %.3f | %+.4f (%.4f)%s"
                  % (r["P"], r["density"], r["cos"], r["corr"], r["eucl"], r["tnorm"],
                     r["rsa"], r["rsa_null"], "*" if r["rsa"] > r["rsa_null"] else " "))
        print("  (cos/corr are GEOMETRIC; tnorm is the AMPLITUDE channel that saturation would close.)")

        print("\n  DIAGNOSTIC UPPER BOUNDS (stronger than any allowed fitness; negatives transfer down,")
        print("  positives do NOT. The pooled linear decoder is the RC-style readout, kept for contrast.)")
        print("  P     dens |   PR_state | pooled linear: mean (sd) max  null | quad  null | quad_in null")
        print("  -----------+------------+-----------------------------------+------------+-------------")
        for r in rows:
            print("  %4d  %.2f |   %6.2f   | %.3f (%.3f) %.3f%s %.3f | %.3f%s %.3f | %.3f%s %.3f"
                  % (r["P"], r["density"], r["pr"],
                     r["lin"], r["lin_sd"], r["lin_max"],
                     "*" if r["lin_any_clears"] else " ", r["lin_null"],
                     r["quad"], "*" if r["quad_clears"] else " ", r["quad_null"],
                     r["quad_in"], "*" if r["quad_in_clears"] else " ", r["quad_in_null"]))
        print("  (* = clears its null; on linear max, at least ONE genome clears)")

        lin_any_ok = [r for r in rows if r["lin_any_clears"]]
        quad_ok = [r for r in rows if r["quad_clears"]]
        best_rise = rows[-1]["loc_best"] - rows[0]["loc_best"]
        nab = max(r["loc_n_above"] for r in rows)
        print("\nREAD:")
        print("  The headline is the FIRST table. loc_best and loc_n_above answer the conversion")
        print("  question per neuron: did ANY unit come to carry the relation, and how many?")
        if nab > 0:
            print("  n_above reaches %.1f -- some neuron(s) DO carry it; the conversion happens, and how" % nab)
            print("  that count moves with P is the encoding-saturation curve in its most direct form.")
        else:
            print("  n_above is 0 at every P: no individual neuron carries the relation anywhere in range.")
            print("  Neither weak readout can see it, and that is a statement about the SUBSTRATE.")
        print("  loc_best change across the range: %+.3f (rising = the conversion strengthens with P)."
              % best_rise)
        if quad_ok and not lin_any_ok:
            print("  quad clears where pooled linear never does: the structure is present and explicit")
            print("  only at second order across the whole range tested.")
        best_scalar = max(("cos", "corr", "eucl", "tnorm"), key=lambda k: max(r[k] for r in rows))
        print("  Best self-referential scalar across the sweep: %s (max %.3f). If cos/corr hold up"
              % (best_scalar, max(r[best_scalar] for r in rows)))
        print("  where tnorm does not, the discrimination is GEOMETRIC, not amplitude -- which would")
        print("  mean saturation is not the limiting factor. Any scalar that looks usable must still")
        print("  pass the D120 controls (omit_cue and scramble at chance) before it can be a fitness.")
        print("  NOTE: a weak readout failing does NOT mean a GA arm must fail -- selection grips")
        print("  variance and would be BUILDING the conversion. Read the sd and max columns.")
        print("  Compare PR_state against PR_task: if they track, effective dimensionality is the")
        print("  mechanism, and D127's PR-family endpoint is measuring the right thing.")
        print("\n  UNDEVELOPED, RANDOM genomes throughout: no selection, no development, no fitness.")


if __name__ == "__main__":
    main()
