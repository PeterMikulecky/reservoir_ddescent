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

# Threshold on the PAIRED |t| for calling a recurrence contribution real. Set from the MEASURED null,
# not from convention: with n=6 paired genomes the null |t| reaches 2.52 at p95 and 3.86 at p99
# (20k simulated draws), and this sweep tests 27 cells, whose expected maximum under the null is ~2.77.
# A threshold of 2.0 therefore sits BELOW the noise -- it would flag roughly one cell per run by chance,
# and the first pass duly called +0.047 on n=3 a contribution. 4.0 clears p99 at n=6, so a single
# flagged cell across the whole grid is informative.
T_THRESHOLD = 4.0

DEFAULT_SCALES = [1.0, 2.0, 4.0]
# Delay segments to test. tau_slow = 100 ms and present_ms = 50 ms, so delay=1 (50 ms) is WITHIN reach
# of passive single-neuron decay -- which is why the first pass found the ablated arm holding the cue at
# 1.000 and learned nothing from it. Recurrence can only be NEEDED past tau_slow, so the informative
# rungs are 4 (200 ms) and 8 (400 ms).
DEFAULT_DELAYS = [1, 4, 8]
QUAD_K = 10          # MATCHED across every condition, including the 10-neuron input slice


def _ablate(g):
    """Zero all recurrent connectivity, leaving neuron identities and intrinsic dynamics untouched."""
    return replace(g, mag=np.zeros_like(g.mag))


def sweep(scales, delays, density, n_genomes=6, n_trials=400, seed=1):
    """Intact vs ablated at each (delay, coupling). Genomes are PAIRED: the same seed builds the genome
    for both arms, so the intact-minus-ablated difference is per-genome and its sd is meaningful."""
    cfg = SC.make_trial_evolve_cfg()
    nc = SC.make_net_cfg()
    w0_base = SC.w0_for_density(density)
    out, t0 = [], time.time()
    keys = ("cue_delay", "quad", "quad_in", "lin", "loc_best", "loc_best_nullv",
            "pr_ratio", "rate", "frac_lowvar", "quad_null", "lin_null")
    for si, (delay, sc) in enumerate([(d, s_) for d in delays for s_ in scales]):
        task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials,
                                  delay_segments=delay)
        rel = (task.cue_test == task.probe_test).astype(int)
        y = rel * 2.0 - 1.0
        cue = task.cue_test
        probe_idx = stage_rows(task, "test", "probe")
        delay_idx = stage_rows(task, "test", "delay")
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
            row = dict(scale=sc, arm=arm, delay=delay, w0=round(w0_base * sc, 4), per_genome=acc)
            for k in acc:
                row[k] = float(np.mean(acc[k]))
                row[k + "_sd"] = float(np.std(acc[k], ddof=1)) if n_genomes > 1 else 0.0
            out.append(row)
            el = time.time() - t0
            done = 2 * si + (1 if arm == "ablated" else 0) + 1
            print("   delay=%d w0x%-5g %-8s done   [%.0fs elapsed, ~%.0fs left]"
                  % (delay, sc, arm, el, el / done * (2 * len(scales) * len(delays) - done)), flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scales", type=float, nargs="+", default=DEFAULT_SCALES)
    ap.add_argument("--delays", type=int, nargs="+", default=DEFAULT_DELAYS)
    ap.add_argument("--density", type=float, default=None)
    ap.add_argument("--genomes", type=int, default=6)
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
        print("All quad uses k=%d for EVERY condition, so comparisons are matched." % QUAD_K)
        print("delays=%s segments (%s ms); tau_slow=%.0f ms, so delay>=%d exceeds passive decay."
              % (a.delays, [d * 50 for d in a.delays], SC.make_net_cfg().tau_slow,
                 int(np.ceil(SC.make_net_cfg().tau_slow / 50)) + 1))
        print("Genomes are PAIRED across arms (same seed), so differences are per-genome.\n")
        rows = sweep(a.scales, a.delays, dens, a.genomes, a.trials, a.seed)

        by = {(r["delay"], r["scale"], r["arm"]): r for r in rows}

        def paired(delay, sc, key):
            """Per-genome intact-minus-ablated difference: mean, sd, and t. Genomes are paired by seed,
            so this is a paired difference and its sd reflects genome-to-genome variation in what
            recurrence CONTRIBUTES -- not variation in the metric itself."""
            i = np.array(by[(delay, sc, "intact")]["per_genome"][key], float)
            b = np.array(by[(delay, sc, "ablated")]["per_genome"][key], float)
            d = i - b
            sd = float(np.std(d, ddof=1)) if len(d) > 1 else 0.0
            t = float(d.mean() / (sd / np.sqrt(len(d)) + 1e-12)) if sd > 0 else 0.0
            return float(d.mean()), sd, t

        print("\n  INTACT vs ABLATED  (ablated = recurrent connectivity zeroed, tau_slow retained)")
        print("  delay  w0x   arm      | cue@delay |  quad  | quad_in | loc_best (floor) | PR/null | lowvar")
        print("  -------+-----+--------+-----------+--------+---------+------------------+---------+-------")
        for delay in a.delays:
            for sc in a.scales:
                for arm in ("intact", "ablated"):
                    r = by[(delay, sc, arm)]
                    mark = "*" if (r["loc_best"] - r["loc_best_nullv"]) > MARGIN_SD * max(r["loc_best_sd"], 1e-6) else " "
                    print("  %d(%3dms) %-4g %-8s|   %.3f   | %.3f  |  %.3f  | %.3f (%.3f)%s |  %5.2f  | %.3f"
                          % (delay, delay * 50, sc, arm, r["cue_delay"], r["quad"], r["quad_in"],
                             r["loc_best"], r["loc_best_nullv"], mark, r["pr_ratio"], r["frac_lowvar"]))

        print("\n  RECURRENCE CONTRIBUTION -- PAIRED per-genome difference, mean (sd) t")
        print("  A contribution counts only if |t| > %.1f, set from the MEASURED null: at n=6 the null" % T_THRESHOLD)
        print("  |t| reaches 3.86 at p99 and ~2.77 as the expected max over this grid's 27 cells. The")
        print("  first pass used a hardcoded 0.05 difference with no variance reference, and called")
        print("  +0.047 on n=3 a contribution; a threshold of 2.0 would also sit below the noise.")
        print("  delay  w0x  |     d cue@delay      |        d quad        |      d loc_best")
        print("  -------+----+----------------------+----------------------+---------------------")
        verdicts = []
        for delay in a.delays:
            for sc in a.scales:
                cells = []
                for key in ("cue_delay", "quad", "loc_best"):
                    m, sd, t = paired(delay, sc, key)
                    cells.append("%+.3f (%.3f) t=%+5.2f%s" % (m, sd, t, "*" if abs(t) > T_THRESHOLD else " "))
                    verdicts.append((delay, sc, key, m, t))
                print("  %d(%3dms) %-4g| %s | %s | %s" % (delay, delay * 50, sc, cells[0], cells[1], cells[2]))
        print("  (* = |t| exceeds the threshold, i.e. recurrence measurably contributes)")

        print("\nREAD:")
        sig = [v for v in verdicts if abs(v[4]) > T_THRESHOLD]
        pos = [v for v in sig if v[3] > 0]
        for delay in a.delays:
            abl = [by[(delay, sc, "ablated")]["cue_delay"] for sc in a.scales]
            print("  delay=%d (%3d ms): ABLATED holds the cue at %.3f-%.3f%s"
                  % (delay, delay * 50, min(abl), max(abl),
                     "  <- passive decay suffices; recurrence CANNOT be required here"
                     if min(abl) > 0.9 else "  <- passive decay FAILS; recurrence could be required"))
        if not pos:
            print("  NO condition shows a positive recurrence contribution at |t| > %.1f." % T_THRESHOLD)
            print("  Across %d delays (to %d ms, %.1fx tau_slow) and %d couplings, the recurrent network"
                  % (len(a.delays), max(a.delays) * 50, max(a.delays) * 50 / 100.0, len(a.scales)))
            print("  adds nothing to memory, expansion, or readability. Everything measured on this task")
            print("  is a FEEDFORWARD transform of the stimulus through per-neuron tau_slow dynamics.")
            print("  Consequence: P counts recurrent synapses, those synapses do nothing, so P cannot")
            print("  matter -- which explains D129's flat density sweep as a necessity, not a null.")
        else:
            print("  Positive contribution at: %s"
                  % ", ".join("delay=%d w0x%g (%s %+.3f)" % (d, s_, k, m) for d, s_, k, m, _ in pos))
            print("  Recurrence is load-bearing there; re-run the density sweep in that regime before")
            print("  concluding anything about P.")
        print("\n  Fixed density and input_gain; random undeveloped genomes; no selection, no development.")


if __name__ == "__main__":
    main()
