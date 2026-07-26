"""trial_coupling_sweep.py - does RECURRENCE contribute anything, at any coupling strength?

TWO QUESTIONS, ONE SWEEP.

(1) HAS RECURRENCE EVER CONTRIBUTED ANYTHING? D129 found `quad_input` (the 10 input neurons alone)
    reading 0.808-0.831 while full-state `quad` read 0.731-0.777, at EVERY density. If a feedforward
    read of the driven neurons matches or beats the whole network, the recurrent dynamics may have been
    inert throughout -- which would reframe the entire investigation. That comparison was unmatched
    (10 vs 14 PCA components, so 65 vs 119 features at n=400) and therefore only suggestive. Here every
    quad uses k_override=10, so all conditions get 65 features and the comparison is like-for-like.

(2) IS THE COUPLING STRENGTH WRONG? `w0` has ALWAYS been derived from density by `w0_for_density`, a
    rule built to control the drive confound (holding summed input variance constant as in-degree
    grows). Whether the coupling that rule produces places the network in any useful dynamical regime
    -- ordered, critical, chaotic -- has never been asked. This is a DIFFERENT parameter from
    `input_gain` (external drive, swept in D129) and is the one the reservoir literature says governs
    memory and expansion. Swept here as a MULTIPLIER on the standing w0_for_density value, so 1.0 is
    exactly the project's current setting and every other point is a stated departure from it.

THE DESIGN. At each coupling, two arms on the SAME genomes:
  intact   - the network as built.
  ablated  - genome.mag zeroed: NO recurrent connectivity, while every neuron keeps its intrinsic
             tau_slow dynamics. This isolates the contribution of CONNECTIVITY specifically, not of
             temporal dynamics generally. Non-input neurons receive nothing and fall silent, which is
             the point: it asks what the driven neurons alone could give.

The measurement of interest is the DIFFERENCE, intact minus ablated, on each quantity. A difference of
~0 at every coupling means recurrence contributes nothing and the network has been decorative.

WHAT IS MEASURED, at the probe stage unless noted:
  cue@delay   - cue decodability at the DELAY stage: does the network HOLD the cue? Ablated still has
                tau_slow, so a difference here is memory contributed by CONNECTIVITY.
  quad        - second-order decodability of match/non-match, k_override=10 (MATCHED).
  quad_in     - the same restricted to the n_in input neurons, also k=10.
  linear      - pooled linear decodability.
  loc_best    - best single neuron under a D095-weak affine, against its measured noise floor. The
                quantity that decides whether a GA has any gradient; it has never left that floor.
  PR / null   - effective dimensionality against its shuffled-neuron null (D129).
  rate, frac_lowvar - substrate state; frac_lowvar counts units not varying with the stimulus.

Everything is compared against its own shuffled-target null, and a metric counts as clearing only if it
exceeds that null by more than MARGIN_SD across-genome sds (D129: a bare `>` flagged 0.555 vs 0.554).

PRE-REGISTERED READ (fixed before running):
  intact ~ ablated on everything, at every coupling  -> recurrence contributes NOTHING. The whole study
      has been measuring a feedforward transform of the stimulus, and P (which counts recurrent
      synapses) cannot matter because those synapses do not matter. That is the strongest possible
      negative and it would reframe the project.
  intact > ablated on cue@delay only                 -> recurrence supplies MEMORY but not expansion.
  intact > ablated on quad and/or loc_best           -> recurrence supplies EXPANSION. The coupling at
      which the gap is largest is the regime worth working in, and P may matter there.
  loc_best leaves its floor at some coupling         -> first gradient available to a GA in this project.
  everything degrades at high coupling               -> the upper end is chaotic; that bounds the range.

Run:  python scripts/trial_coupling_sweep.py [--scales ...] [--genomes N] [--density D]
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
from ddescent.measures import participation_ratio
from ddescent.trial_eval import localization_report

from delay_persistence_probe import decode, decode_null, _expand, stage_rows
from trial_operating_point_sweep import pr_with_null, loc_best_null

# Defined here rather than imported, so this script does not depend on which revision of
# trial_operating_point_sweep is checked out. A metric counts as clearing only if it exceeds its null by
# more than this many across-genome sds (D129: a bare `>` flagged loc_best at 0.555 against a null of
# 0.554 -- a comparison of two noisy estimates is not a test).
MARGIN_SD = 2.0

DEFAULT_SCALES = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]
QUAD_K = 10          # MATCHED across every condition, including the 10-neuron input slice


def _ablate(g):
    """Zero all recurrent connectivity, leaving neuron identities and intrinsic dynamics untouched."""
    return replace(g, mag=np.zeros_like(g.mag))


def sweep(scales, density, n_genomes=3, n_trials=400, seed=1):
    cfg = SC.make_trial_evolve_cfg()
    nc = SC.make_net_cfg()
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials)
    rel = (task.cue_test == task.probe_test).astype(int)
    y = rel * 2.0 - 1.0
    cue = task.cue_test
    probe_idx = stage_rows(task, "test", "probe")
    delay_idx = stage_rows(task, "test", "delay")
    w0_base = SC.w0_for_density(density)
    out, t0 = [], time.time()
    keys = ("cue_delay", "quad", "quad_in", "lin", "loc_best", "loc_best_nullv",
            "pr_ratio", "rate", "frac_lowvar", "quad_null", "lin_null")
    for si, sc in enumerate(scales):
        for arm in ("intact", "ablated"):
            acc = {k: [] for k in keys}
            for gi in range(n_genomes):
                g = random_genome(nc, density, w0=w0_base * sc, ei_split=cfg.ei_split,
                                  seed=seed + 100 * si + gi)
                if arm == "ablated":
                    g = _ablate(g)
                B = EvoNet(g, nc).behave(task.E_test, noise_seed=2 + gi)
                Xp = B["state"][probe_idx]
                Xd = B["state"][delay_idx]
                sd = Xp.std(0)
                acc["rate"].append(float(Xp.mean()))
                acc["frac_lowvar"].append(float(np.mean(sd < 0.01 * (np.median(sd) + 1e-12))))
                acc["cue_delay"].append(decode(Xd, cue))
                Zq = _expand(Xp, "quad", seed=gi, k_override=QUAD_K)
                Zi = _expand(Xp[:, : nc.n_in], "quad", seed=gi, k_override=QUAD_K)
                acc["quad"].append(decode(Zq, rel))
                acc["quad_null"].append(decode_null(Zq, rel, n_rep=30)[1])
                acc["quad_in"].append(decode(Zi, rel))
                acc["lin"].append(decode(Xp, rel))
                acc["lin_null"].append(decode_null(Xp, rel, n_rep=30)[1])
                L = localization_report(Xp, y, out_index=nc.N - nc.d, seed=gi)
                acc["loc_best"].append(float(L["loc_best"]))
                acc["loc_best_nullv"].append(loc_best_null(Xp, y, nc.N - nc.d, seed=gi))
                p, pn = pr_with_null(Xp, seed=gi)
                acc["pr_ratio"].append(p / (pn + 1e-12))
            row = dict(scale=sc, arm=arm, w0=round(w0_base * sc, 4))
            for k in acc:
                row[k] = float(np.mean(acc[k]))
                row[k + "_sd"] = float(np.std(acc[k], ddof=1)) if n_genomes > 1 else 0.0
            out.append(row)
            el = time.time() - t0
            done = 2 * si + (1 if arm == "ablated" else 0) + 1
            print("   w0x%-5g %-8s done   [%.0fs elapsed, ~%.0fs left]"
                  % (sc, arm, el, el / done * (2 * len(scales) - done)), flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scales", type=float, nargs="+", default=DEFAULT_SCALES)
    ap.add_argument("--density", type=float, default=None)
    ap.add_argument("--genomes", type=int, default=3)
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    dens = a.density if a.density is not None else SC.make_trial_evolve_cfg().density

    warnings.filterwarnings("ignore")
    with tee("trial_coupling_sweep", log_dir="runs/coupling",
             header="recurrent coupling strength x {intact, ablated} -- does recurrence contribute?"):
        print("density=%.3f (P=%d)  input_gain=%.1f (FIXED)  genomes=%d  trials=%d"
              % (dens, round(dens * 50 * 49), SC.make_net_cfg().input_gain, a.genomes, a.trials))
        print("w0 multipliers on w0_for_density(%.3f)=%.4f; 1.0 IS the project's current setting."
              % (dens, SC.w0_for_density(dens)))
        print("All quad uses k=%d for EVERY condition, so comparisons are matched.\n" % QUAD_K)
        rows = sweep(a.scales, dens, a.genomes, a.trials, a.seed)

        by = {(r["scale"], r["arm"]): r for r in rows}
        print("\n  INTACT vs ABLATED  (ablated = recurrent connectivity zeroed, tau_slow retained)")
        print("  w0x   arm      | cue@delay |  quad  | quad_in | linear | loc_best (floor) |  PR/null | lowvar")
        print("  ------+--------+-----------+--------+---------+--------+------------------+----------+-------")
        for sc in a.scales:
            for arm in ("intact", "ablated"):
                r = by[(sc, arm)]
                mark = "*" if (r["loc_best"] - r["loc_best_nullv"]) > MARGIN_SD * max(r["loc_best_sd"], 1e-6) else " "
                print("  %-5g %-8s|   %.3f   | %.3f  |  %.3f  | %.3f  | %.3f (%.3f)%s |  %5.2f   | %.3f"
                      % (sc, arm, r["cue_delay"], r["quad"], r["quad_in"], r["lin"],
                         r["loc_best"], r["loc_best_nullv"], mark, r["pr_ratio"], r["frac_lowvar"]))

        print("\n  RECURRENCE CONTRIBUTION  (intact minus ablated; ~0 means connectivity adds nothing)")
        print("  w0x   | d cue@delay | d quad  | d linear | d loc_best |  d PR/null")
        print("  ------+-------------+---------+----------+------------+-----------")
        for sc in a.scales:
            i, b = by[(sc, "intact")], by[(sc, "ablated")]
            print("  %-5g |   %+.3f    | %+.3f  |  %+.3f   |   %+.3f    |   %+.2f"
                  % (sc, i["cue_delay"] - b["cue_delay"], i["quad"] - b["quad"],
                     i["lin"] - b["lin"], i["loc_best"] - b["loc_best"],
                     i["pr_ratio"] - b["pr_ratio"]))

        dq = [by[(s, "intact")]["quad"] - by[(s, "ablated")]["quad"] for s in a.scales]
        dm = [by[(s, "intact")]["cue_delay"] - by[(s, "ablated")]["cue_delay"] for s in a.scales]
        lb = [r for r in rows
              if (r["loc_best"] - r["loc_best_nullv"]) > MARGIN_SD * max(r["loc_best_sd"], 1e-6)]
        print("\nREAD:")
        print("  Largest recurrence contribution: quad %+.3f, memory %+.3f." % (max(dq), max(dm)))
        if max(abs(min(dq)), max(dq)) < 0.05 and max(abs(min(dm)), max(dm)) < 0.05:
            print("  RECURRENCE CONTRIBUTES NOTHING at any coupling tested. The network is a feedforward")
            print("  transform of the stimulus, and P -- which counts recurrent synapses -- cannot matter")
            print("  because those synapses do not. This would reframe the project.")
        else:
            print("  Recurrence DOES contribute. The coupling with the largest gap is the regime worth")
            print("  working in, and a P sweep should be re-run there before P is judged inert.")
        if lb:
            print("  loc_best leaves its floor at: %s -- first GA gradient seen in this project."
                  % ", ".join("w0x%g/%s" % (r["scale"], r["arm"]) for r in lb))
        else:
            print("  loc_best never leaves its floor at any coupling, in either arm.")
        print("\n  Fixed density and input_gain; random undeveloped genomes; no selection, no development.")


if __name__ == "__main__":
    main()
