"""trial_operating_point_sweep.py - can the OPERATING POINT move what P could not? (D119, D128 follow-up)

THE QUESTION. The density sweep found every representational quantity invariant to a 45x change in P:
PR_state 5.5-8.0 with no trend, the relation present at second order everywhere (quad ~0.75) and
readable by no capacity-bounded readout anywhere (loc_best 0.549-0.561, at its noise floor). If
effective dimensionality is set by the OPERATING REGIME rather than by parameter count, that flatness
is what the w0_for_density control guarantees rather than a discovery -- and the regime, not P, is the
lever. D119 has listed the operating point as live since it was written and it has never been moved.
`input_gain = 10.0` carries the annotation "the useful regime; NOT the PR-optimal one" (D030/D033).

WHAT THIS ANSWERS, all at fixed density (so P is held constant and only the regime varies):
  1. Is PR_state MOVABLE AT ALL? Flat across P AND across regime would mean it is pinned by something
     structural. Moving with regime would mean effective dimensionality is a property of the operating
     point, which is a substantive claim about where a second descent could come from in this system.
  2. Does any regime produce the SECOND-ORDER -> WEAKLY-READABLE conversion? That is the D128 gap.
  3. Does loc_best ever LEAVE ITS NOISE FLOOR? If not, there is no gradient for a GA at any regime,
     and that is a real negative about this substrate rather than a gap in our probing.

WARNING - PR_state HAS NEVER HAD A NULL, AND THAT WAS A GAP. It was reported as 5.5-8.0 with no baseline.
This script measures one: shuffle each neuron's values across trials independently, which destroys
cross-neuron correlation while preserving every unit's marginal distribution. PR of that shuffle is
"no correlation structure" for these exact data. Only PR relative to its null is interpretable -- the
same rule D127 imposed on PR_task and the same one every decoder here already follows.

SATURATION. D128's candidate mechanism is that at high input_gain the input neurons saturate, so
doubled drive gives the same rate as single drive and the amplitude channel closes at entry. The direct
signature is neurons that DO NOT VARY with the stimulus. `frac_lowvar` counts units whose across-trial
sd is under 1% of the population median -- saturated and silent units both land there, and both mean
the same thing: that unit carries no stimulus information.

PRE-REGISTERED READ (fixed before running):
  PR rises above its null as gain falls        -> effective dimensionality is regime-set. The operating
                                                  point is the lever P was not, and a P sweep should be
                                                  re-run at the PR-favourable regime before conclusions.
  loc_best leaves its noise floor at some gain -> a weak readout can see the relation there; that regime
                                                  is where a GA becomes possible.
  frac_lowvar high at gain=10, falling as gain -> saturation confirmed as the closing mechanism.
    drops, with quad/loc_best improving
  everything flat across the whole gain range  -> the substrate's representation is invariant to both P
                                                  and regime. That is a real, reportable negative and
                                                  the point to stop probing.

Run:  python scripts/trial_operating_point_sweep.py [--gains ...] [--genomes N] [--density D]
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

from delay_persistence_probe import decode, decode_null, _expand, stage_rows

DEFAULT_GAINS = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0]


def pr_with_null(X, n_rep: int = 20, seed: int = 0):
    """Participation ratio and its no-cross-structure null.

    The null shuffles each neuron's values across trials INDEPENDENTLY: every unit keeps its own
    marginal distribution, but all cross-neuron correlation is destroyed. PR of that shuffle is what
    "no shared structure" reads for these data. PR alone is uninterpretable -- 7 of 50 means nothing
    until you know what 50 uncorrelated units of the same marginals would give.
    """
    X = np.asarray(X, float)
    rng = np.random.default_rng(seed)
    obs = float(participation_ratio(X))
    nul = []
    for _ in range(n_rep):
        Xs = np.column_stack([X[rng.permutation(X.shape[0]), j] for j in range(X.shape[1])])
        nul.append(float(participation_ratio(Xs)))
    return obs, float(np.mean(nul))


def loc_best_null(X, y, out_index: int, n_rep: int = 6, seed: int = 0) -> float:
    """The noise floor of loc_best: best-of-N per-neuron score under SHUFFLED targets.

    Necessary because max-over-N is upward biased by selection -- with 50 units, the luckiest one
    always looks good. Only loc_best ABOVE this is evidence that a unit carries anything.
    """
    rng = np.random.default_rng(seed)
    return float(np.mean([localization_report(X, y[rng.permutation(len(y))], out_index=out_index,
                                              n_null=2, seed=seed + r)["loc_best"]
                          for r in range(n_rep)]))


def sweep(gains, density, n_genomes=4, n_trials=400, seed=1, stage="probe"):
    cfg = SC.make_trial_evolve_cfg()
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials)
    rel = (task.cue_test == task.probe_test).astype(int)
    y = rel * 2.0 - 1.0
    w0 = SC.w0_for_density(density)
    rows_idx = None
    out, t0 = [], time.time()
    for gi, gain in enumerate(gains):
        nc = SC.make_net_cfg(input_gain=float(gain))
        if rows_idx is None:
            rows_idx = stage_rows(task, "test", stage)
        acc = {k: [] for k in ("pr", "pr_null", "rate", "frac_lowvar",
                               "lin", "lin_null", "quad", "quad_null",
                               "loc_best", "loc_best_null", "loc_n_above", "loc_mean")}
        for g_i in range(n_genomes):
            g = random_genome(nc, density, w0=w0, ei_split=cfg.ei_split, seed=seed + 100 * gi + g_i)
            B = EvoNet(g, nc).behave(task.E_test, noise_seed=2 + g_i)
            X = B["state"][rows_idx]
            sd = X.std(0)
            acc["rate"].append(float(X.mean()))
            acc["frac_lowvar"].append(float(np.mean(sd < 0.01 * (np.median(sd) + 1e-12))))
            p, pn = pr_with_null(X, seed=g_i)
            acc["pr"].append(p); acc["pr_null"].append(pn)
            acc["lin"].append(decode(X, rel)); acc["lin_null"].append(decode_null(X, rel, n_rep=30)[1])
            Zq = _expand(X, "quad", seed=g_i)
            acc["quad"].append(decode(Zq, rel)); acc["quad_null"].append(decode_null(Zq, rel, n_rep=30)[1])
            L = localization_report(X, y, out_index=nc.N - nc.d, seed=g_i)
            acc["loc_best"].append(float(L["loc_best"])); acc["loc_mean"].append(float(L["loc_mean"]))
            acc["loc_n_above"].append(float(L["loc_n_above"]))
            acc["loc_best_null"].append(loc_best_null(X, y, nc.N - nc.d, seed=g_i))
        row = dict(gain=gain)
        for k in acc:
            row[k] = float(np.mean(acc[k]))
            row[k + "_sd"] = float(np.std(acc[k], ddof=1)) if n_genomes > 1 else 0.0
        out.append(row)
        el = time.time() - t0
        print("   gain=%-5g done   [%.0fs elapsed, ~%.0fs left]"
              % (gain, el, el / (gi + 1) * (len(gains) - gi - 1)), flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gains", type=float, nargs="+", default=DEFAULT_GAINS)
    ap.add_argument("--density", type=float, default=None)
    ap.add_argument("--genomes", type=int, default=4)
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    dens = a.density if a.density is not None else SC.make_trial_evolve_cfg().density

    warnings.filterwarnings("ignore")
    with tee("trial_operating_point_sweep", log_dir="runs/operating_point",
             header="operating point (input_gain) at FIXED density -- random undeveloped genomes"):
        print("density=%.3f (P=%d, FIXED)  genomes=%d  trials=%d  gains=%s"
              % (dens, round(dens * 50 * 49), a.genomes, a.trials, a.gains))
        print("Only the regime varies. P is constant, so nothing here is a P effect.\n")
        rows = sweep(a.gains, dens, a.genomes, a.trials, a.seed)

        print("\n  SUBSTRATE STATE")
        print("  gain  | mean rate | frac_lowvar |  PR (null)  PR/null")
        print("  ------+-----------+-------------+--------------------")
        for r in rows:
            print("  %-5g | %9.4f | %11.3f | %5.2f (%5.2f)  %.2f"
                  % (r["gain"], r["rate"], r["frac_lowvar"], r["pr"], r["pr_null"],
                     r["pr"] / (r["pr_null"] + 1e-12)))
        print("  (frac_lowvar = units not varying with stimulus: saturated or silent, both uninformative)")

        print("\n  RELATION ACCESSIBILITY")
        print("  gain  | loc_best (null)  | loc_mean | n_above |  linear (null)  |  quad (null)")
        print("  ------+------------------+----------+---------+-----------------+---------------")
        for r in rows:
            print("  %-5g | %.3f (%.3f)%s | %.3f    |  %4.1f   | %.3f (%.3f)%s | %.3f (%.3f)%s"
                  % (r["gain"], r["loc_best"], r["loc_best_null"],
                     "*" if r["loc_best"] > r["loc_best_null"] else " ",
                     r["loc_mean"], r["loc_n_above"],
                     r["lin"], r["lin_null"], "*" if r["lin"] > r["lin_null"] else " ",
                     r["quad"], r["quad_null"], "*" if r["quad"] > r["quad_null"] else " "))
        print("  (* = clears its own null. loc_best is the one that decides whether a GA has a gradient.)")

        pr_ratio = [r["pr"] / (r["pr_null"] + 1e-12) for r in rows]
        lb_ok = [r for r in rows if r["loc_best"] > r["loc_best_null"]]
        print("\nREAD:")
        print("  PR/null ranges %.2f to %.2f across the gain range." % (min(pr_ratio), max(pr_ratio)))
        if max(pr_ratio) - min(pr_ratio) > 0.15:
            print("  PR IS MOVABLE by the regime. Effective dimensionality is a property of the operating")
            print("  point, not of P -- and the density sweep should be re-run at the favourable regime")
            print("  before any conclusion about P is drawn.")
        else:
            print("  PR is INVARIANT to the regime as well as to P. Combined with the density sweep that")
            print("  is a substantive negative: this substrate's effective dimensionality is pinned.")
        if lb_ok:
            print("  loc_best LEAVES its noise floor at gain=%s: a capacity-bounded readout can see the"
                  % ", ".join(str(r["gain"]) for r in lb_ok))
            print("  relation there, and that regime is where a GA becomes possible.")
        else:
            print("  loc_best NEVER leaves its noise floor at any gain: no weak readout sees the relation")
            print("  in any regime tested, so there is no gradient for a GA to climb. That is a real")
            print("  negative about the substrate, not a gap in probing.")
        print("\n  Fixed density, random undeveloped genomes, no selection and no development.")


if __name__ == "__main__":
    main()
