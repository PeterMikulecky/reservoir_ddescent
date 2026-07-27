"""task_screen.py - which candidate task is FINDABLE by selection AND needs recurrence? (D132)

THE TWO THINGS THAT KILLED EVERYTHING SO FAR, tested directly and cheaply, on RANDOM UNDEVELOPED
genomes with no GA and no development:

  (a) SELECTABILITY. Is there between-genome variance in fitness at generation 0, above measurement
      noise? D124 spent a 40-generation arm discovering there was not. The D115 machinery answers it in
      minutes: score G genomes under K independent noise draws, decompose into signal_sd (between
      genomes) and noise_sd (within genome, across draws), reliability = signal^2/(signal^2+noise^2).
      Selection cannot act on a signal below its own measurement noise.

  (b) RECURRENCE-DEPENDENCE. Does ablating all recurrent connectivity destroy performance? D129 and
      D130 established that if recurrence contributes nothing, P -- which counts recurrent synapses --
      cannot matter, and the whole study is measuring a feedforward transform. A task where the ablated
      network scores as well as the intact one is unusable no matter how selectable it is.

A task PASSES only if it clears BOTH. DMTS is included as a known NEGATIVE control: it should fail (b)
and probably (a), which is what validates the screen.

WHY THESE CANDIDATE TASKS (D132). Both retired tasks demanded a CONJUNCTION -- a function of two things
presented at different times -- which is second-order in the rates, and this substrate has no native
second-order operation. The replacement criteria are: the discriminating quantity must be FIRST-ORDER
(a two-parameter affine can read it in principle), but must require something LEAK ALONE CANNOT DO, or
recurrence is irrelevant. Exactly one such capability is verified here: TEMPORAL INTEGRATION BEYOND
tau_slow. Ablated networks are at chance by 200 ms (D130); the validated ceiling holds to 600 ms.

  accumulate  - a noisy stimulus streams for the whole trial; the target is the TOTAL evidence.
                With trial length >> tau_slow, a leak-only network can only see the last ~100 ms, so
                its score is capped; a network that integrates recurrently can use all of it.
                (Wang 2002 slow reverberation as an integrator.)
  delayed     - present amplitude a in segment 0, then silence past tau_slow, then read.
                The target is a. Leak alone loses it; held activity does not.
                (Compte et al. 2000 graded memory.)
  dmts        - the retired task, as the known-negative control.

N IS A VARIABLE, NOT A CONSTANT. "This substrate cannot" and "this substrate at N=100 cannot" are
different claims and only the second has been tested. Litwin-Kumar's clustered networks use ~1600
excitatory neurons; ours use 80.

Run:  python scripts/task_screen.py [--tasks accumulate delayed dmts] [--ns 100] [--genomes 10]
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


# ==================================================================================================
# TASK GENERATORS - deliberately standalone, NOT added to trial_task.py
# ==================================================================================================
# None of these has survived a screen yet. Refactoring the task module for tasks that may not survive
# would repeat the D126 mistake of building infrastructure around an unvalidated choice.

def make_accumulate(n_trials, n_in, n_seg=8, seed=0):
    """INDEPENDENT evidence per segment; the target is the TOTAL. Only a true integrator can do it.

    The first version gave every segment the SAME hidden level plus noise, so a single segment nearly
    revealed the answer -- measured: a leak-only reader seeing only the last segment scored 0.809, so
    the gap recurrence would have to supply was just 0.19. Useless as a discriminator.

    Here each segment's evidence is an INDEPENDENT draw and the target is their sum. One segment then
    carries 1/n_seg of the variance (r ~ sqrt(1/8) = 0.35), while integrating all eight gives 1.0. The
    gap is the whole point: it is exactly what recurrence would have to supply, and it is what
    `d_ablate` measures. Still FIRST-ORDER -- total drive is a scalar an affine can read.
    """
    rng = np.random.default_rng(seed)
    direction = rng.standard_normal(n_in)
    direction /= np.linalg.norm(direction)
    per_seg = rng.standard_normal((n_trials, n_seg))            # INDEPENDENT per segment
    E = (per_seg[:, :, None] * direction[None, None, :]).reshape(n_trials * n_seg, n_in)
    y = per_seg.sum(1)
    read_rows = np.arange(n_trials) * n_seg + (n_seg - 1)
    return E, y, read_rows, dict(task="accumulate", n_seg=n_seg, ms=n_seg * 50)


def make_delayed(n_trials, n_in, n_seg=6, seed=0):
    """Present amplitude a in segment 0, then silence; read at the last segment. Target is a.

    With n_seg=6 the read is 250 ms after the stimulus, well past tau_slow=100 ms, so passive decay has
    lost it. First-order (the target is an amplitude) but unreachable without held activity.
    """
    rng = np.random.default_rng(seed)
    direction = rng.standard_normal(n_in)
    direction /= np.linalg.norm(direction)
    a = rng.standard_normal(n_trials)
    E = np.zeros((n_trials * n_seg, n_in))
    E[np.arange(n_trials) * n_seg] = a[:, None] * direction[None, :]
    read_rows = np.arange(n_trials) * n_seg + (n_seg - 1)
    return E, a, read_rows, dict(task="delayed", n_seg=n_seg, delay_ms=(n_seg - 1) * 50)


def make_dmts(n_trials, n_in, n_seg=4, seed=0):
    """The retired task, as the known-NEGATIVE control. Cue, delay, probe, read; target match/non-match."""
    rng = np.random.default_rng(seed)
    pats = rng.standard_normal((2, n_in))
    pats /= np.linalg.norm(pats, axis=1, keepdims=True)
    cue = rng.integers(0, 2, n_trials)
    is_match = rng.random(n_trials) < 0.5
    probe = np.where(is_match, cue, 1 - cue)
    E = np.zeros((n_trials * n_seg, n_in))
    E[np.arange(n_trials) * n_seg] = pats[cue]
    E[np.arange(n_trials) * n_seg + 2] = pats[probe]
    read_rows = np.arange(n_trials) * n_seg + 3
    return E, np.where(is_match, 1.0, -1.0), read_rows, dict(task="dmts", n_seg=n_seg)


TASKS = dict(accumulate=make_accumulate, delayed=make_delayed, dmts=make_dmts)


# ==================================================================================================
def score(net, E, y, read_rows, out_index, noise_seed):
    """D095-weak readout: a TWO-PARAMETER affine on ONE designated neuron, scored HELD-OUT.

    Held-out because in-sample affine fits do not sit at chance (D129: the per-neuron floor is ~0.56 at
    n=200, which is what broke the first PR definition). Fit on half the trials, score on the other.
    Returned as Pearson r between prediction and target -- bounded, and 0 is the true no-skill point.
    """
    B = net.behave(E, noise_seed=noise_seed)
    v = B["state"][read_rows][:, out_index]
    n = len(y)
    fit, test = np.arange(n) < n // 2, np.arange(n) >= n // 2
    A = np.vstack([v[fit], np.ones(fit.sum())]).T
    coef, *_ = np.linalg.lstsq(A, y[fit], rcond=None)
    pred = v[test] * coef[0] + coef[1]
    if pred.std() < 1e-12 or y[test].std() < 1e-12:
        return 0.0
    return float(np.corrcoef(pred, y[test])[0, 1])


def screen_one(task_name, N, n_genomes, n_draws, n_trials, density, seed=1):
    nc = SC.make_net_cfg(N=N)
    cfg = SC.make_trial_evolve_cfg()
    w0 = SC.w0_for_density(density)
    E, y, read_rows, meta = TASKS[task_name](n_trials, nc.n_in, seed=seed)
    out_index = nc.N - nc.d

    per_genome, ablated = [], []
    for gi in range(n_genomes):
        g = random_genome(nc, density, w0=w0, ei_split=cfg.ei_split, seed=seed + gi)
        net = EvoNet(g, nc)                      # built ONCE per genome, reused across noise draws
        per_genome.append([score(net, E, y, read_rows, out_index, noise_seed=100 + d)
                           for d in range(n_draws)])
        net_abl = EvoNet(replace(g, mag=np.zeros_like(g.mag)), nc)
        ablated.append(score(net_abl, E, y, read_rows, out_index, noise_seed=100))
        print("      genome %d done" % gi, flush=True)

    M = np.abs(np.array(per_genome))                      # |r|: sign is arbitrary for a random genome
    gm = M.mean(1)
    signal_sd = float(np.std(gm, ddof=1))                 # BETWEEN genomes: what selection could grip
    noise_sd = float(np.mean(np.std(M, axis=1, ddof=1)))  # WITHIN genome: measurement noise
    rel = signal_sd ** 2 / (signal_sd ** 2 + noise_sd ** 2 + 1e-12)
    abl = np.abs(np.array(ablated))
    return dict(task=task_name, N=N, mean=float(gm.mean()), best=float(gm.max()),
                signal_sd=signal_sd, noise_sd=noise_sd, reliability=float(rel),
                ablated=float(abl.mean()), d_ablate=float(gm.mean() - abl.mean()),
                # meta carries its own "task" key, which collides with the explicit argument above
                **{k: v for k, v in meta.items() if k not in ("task", "N")})


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tasks", nargs="+", default=["accumulate", "delayed", "dmts"])
    ap.add_argument("--ns", type=int, nargs="+", default=[100])
    ap.add_argument("--genomes", type=int, default=10)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--density", type=float, default=0.3)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("task_screen", log_dir="runs/task_screen",
             header="which task is SELECTABLE at gen 0 AND requires recurrence? (D132)"):
        print("tasks=%s  N=%s  genomes=%d  draws=%d  trials=%d  density=%.2f"
              % (a.tasks, a.ns, a.genomes, a.draws, a.trials, a.density))
        print("Random UNDEVELOPED genomes. No GA, no development. dmts is the known-NEGATIVE control.\n")
        rows, t0 = [], time.time()
        for N in a.ns:
            for t in a.tasks:
                print("   %s at N=%d:" % (t, N), flush=True)
                rows.append(screen_one(t, N, a.genomes, a.draws, a.trials, a.density))
                print("     done [%.0fs elapsed]" % (time.time() - t0), flush=True)

        print("\n  task        N   | mean |r| | best  | signal_sd | noise_sd | reliability | ablated | d_abl")
        print("  ----------------+----------+-------+-----------+----------+-------------+---------+------")
        for r in rows:
            print("  %-11s %3d | %8.3f | %.3f |  %.4f   |  %.4f  |    %.3f    |  %.3f  | %+.3f"
                  % (r["task"], r["N"], r["mean"], r["best"], r["signal_sd"], r["noise_sd"],
                     r["reliability"], r["ablated"], r["d_ablate"]))

        print("\n  PASS = selectable (reliability > 0.30) AND recurrence-dependent (d_ablate > 0.05)")
        print("  task        N   | selectable | needs recurrence | VERDICT")
        print("  ----------------+------------+------------------+--------")
        for r in rows:
            sel, rec = r["reliability"] > 0.30, r["d_ablate"] > 0.05
            print("  %-11s %3d |    %-5s   |      %-5s       | %s"
                  % (r["task"], r["N"], sel, rec, "PASS" if (sel and rec) else "fail"))

        winners = [r for r in rows if r["reliability"] > 0.30 and r["d_ablate"] > 0.05]
        dm = [r for r in rows if r["task"] == "dmts"]
        print("\nREAD:")
        if dm and (dm[0]["reliability"] > 0.30 and dm[0]["d_ablate"] > 0.05):
            print("  WARNING: the known-NEGATIVE control PASSED. The screen's thresholds are wrong, or")
            print("  something about this implementation differs from the retired task. Do not trust")
            print("  any other row until that is explained.")
        if winners:
            print("  PASSING: %s" % ", ".join("%s@N=%d" % (r["task"], r["N"]) for r in winners))
            print("  That task has gen-0 variance selection could grip AND breaks when recurrence is")
            print("  removed -- the two conditions every retired task failed. It is the candidate for")
            print("  the P_gene sweep; confirm with a reliability probe at full n before committing.")
        else:
            print("  NOTHING PASSES. Check the two columns separately -- a task that is selectable but")
            print("  not recurrence-dependent means P cannot matter (D129/D130 again); one that needs")
            print("  recurrence but is unselectable means selection has no gradient (D124 again).")
            print("  If N was varied and neither helped, that bounds the substrate rather than the task.")


if __name__ == "__main__":
    main()
