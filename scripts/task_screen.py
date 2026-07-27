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
def _held_out_r(X, y, alphas=(1e-1, 1e0, 1e1, 1e2, 1e3, 1e4)):
    """Pearson r of a HELD-OUT ridge fit, with the penalty CHOSEN BY AN INTERNAL SPLIT.

    A FIXED penalty does not work here, and a real end-to-end run showed why: at 50 fit samples with
    100 features, ridge=1.0 left the 100-neuron pooled readout scoring 0.127 while a 10-neuron SUBSET
    of its own features scored 0.433. A readout beaten by a subset of itself is not an upper bound, and
    the verdict logic then reported "the state does not contain the target" when the input neurons
    plainly carried it.

    So the penalty is selected on an inner split of the FIT half only -- the test half is never touched
    during selection, so this stays a held-out score. Wide grid, because the right penalty differs by
    orders of magnitude between a 10-feature and a 100-feature readout.
    """
    X = np.asarray(X, float)
    n = len(y)
    fit, test = np.arange(n) < n // 2, np.arange(n) >= n // 2
    mu, sd = X[fit].mean(0), X[fit].std(0) + 1e-9
    Xz = (X - mu) / sd
    Xf, yf = Xz[fit], y[fit] - y[fit].mean()
    n_inner = max(2, len(yf) // 2)
    Xi, yi, Xv, yv = Xf[:n_inner], yf[:n_inner], Xf[n_inner:], yf[n_inner:]
    best_a, best_s = alphas[0], -np.inf
    for a in alphas:
        c = np.linalg.solve(Xi.T @ Xi + a * np.eye(Xi.shape[1]), Xi.T @ yi)
        pv = Xv @ c
        sc = -np.inf if pv.std() < 1e-12 or yv.std() < 1e-12 else float(np.corrcoef(pv, yv)[0, 1])
        if sc > best_s:
            best_a, best_s = a, sc
    coef = np.linalg.solve(Xf.T @ Xf + best_a * np.eye(Xf.shape[1]), Xf.T @ yf)
    pred = Xz[test] @ coef
    if pred.std() < 1e-12 or y[test].std() < 1e-12:
        return 0.0
    return float(np.corrcoef(pred, y[test])[0, 1])


def r_null(n_test, n_rep=400, seed=0):
    """The MEASURED chance level for |r| at this sample size. NOT zero.

    A correlation on n held-out trials has |r| ~ 1/sqrt(n) under the null, so at n=100 the floor is
    ~0.10 -- and the first version of this screen reported mean |r| of 0.069-0.077 as if it were
    performance, then computed a RELIABILITY on it and called 0.579 selectable. That is
    between-genome variance in NOISE. D130's own standing rule says a variance or difference test is
    meaningful only when at least one arm clears its own null; this function makes that enforceable.
    """
    rng = np.random.default_rng(seed)
    return float(np.percentile([abs(np.corrcoef(rng.standard_normal(n_test),
                                                rng.standard_normal(n_test))[0, 1])
                                for _ in range(n_rep)], 95))


def score_all(net, E, y, read_rows, out_index, n_in, noise_seed):
    """Every readout, from ONE simulation. Adding readouts costs no extra behave() calls.

    THREE READOUTS, answering different questions:
      single  - the D095-weak two-parameter affine on the designated neuron. THE FITNESS. If this is at
                chance while the others are not, the readout is the bottleneck and no task will ever be
                selectable -- which would explain every null in the project.
      pooled  - linear over all N neurons. Diagnostic UPPER BOUND: is the information in the state at
                all? Negatives transfer down to `single`; positives do not.
      inputs  - linear over the n_in driven neurons only. What is available WITHOUT any recurrent
                processing, so pooled-minus-inputs is what the network's dynamics actually add.
    """
    B = net.behave(E, noise_seed=noise_seed)
    S = B["state"][read_rows]
    return dict(single=_held_out_r(S[:, [out_index]], y),
                pooled=_held_out_r(S, y),
                inputs=_held_out_r(S[:, :n_in], y))


# ==================================================================================================
# PARALLELISM -- one GENOME per work unit (D007 spawn-safe, D064 init-once-per-worker)
# ==================================================================================================
# The screen is embarrassingly parallel across genomes: each genome's draws and its ablation are
# independent of every other genome's. Work units are whole genomes rather than individual draws, so
# each worker builds its Brian2 network once and reuses it -- the same reason the serial version hoisted
# EvoNet out of the draw loop.
_CTX = {}


def _init_screen_worker(ctx):
    """Set the per-worker constants ONCE (D064). The task is REGENERATED from its seed rather than
    shipped, so nothing large crosses the spawn boundary and every worker builds identical stimuli."""
    _CTX.update(ctx)
    _CTX["nc"] = SC.make_net_cfg(N=ctx["N"])
    _CTX["cfg"] = SC.make_trial_evolve_cfg()
    E, y, read_rows, meta = TASKS[ctx["task_name"]](ctx["n_trials"], _CTX["nc"].n_in, seed=ctx["seed"])
    _CTX.update(E=E, y=y, read_rows=read_rows, meta=meta)


def _screen_genome(gi):
    """TOP-LEVEL and picklable -- Windows spawn cannot ship a closure or lambda (D007)."""
    nc, cfg = _CTX["nc"], _CTX["cfg"]
    E, y, read_rows = _CTX["E"], _CTX["y"], _CTX["read_rows"]
    out_index = nc.N - nc.d
    g = random_genome(nc, _CTX["density"], w0=SC.w0_for_density(_CTX["density"]),
                      ei_split=cfg.ei_split, seed=_CTX["seed"] + gi)
    net = EvoNet(g, nc)                          # built ONCE per genome, reused across noise draws
    draws = [score_all(net, E, y, read_rows, out_index, nc.n_in, noise_seed=100 + d)
             for d in range(_CTX["n_draws"])]
    # ABLATION IS SCORED ON THE POOLED READOUT ONLY, and this is not a detail: with mag=0 the
    # designated neuron has NO inputs at all (external drive reaches only neurons 0..n_in-1), so a
    # single-neuron ablation score is structurally pure noise and would measure "is intact above
    # chance", not "does recurrence matter". The pooled readout still sees the driven neurons.
    net_abl = EvoNet(replace(g, mag=np.zeros_like(g.mag)), nc)
    abl = score_all(net_abl, E, y, read_rows, out_index, nc.n_in, noise_seed=100)
    return ({k: [abs(d[k]) for d in draws] for k in ("single", "pooled", "inputs")},
            {k: abs(abl[k]) for k in ("single", "pooled", "inputs")})


def screen_one(task_name, N, n_genomes, n_draws, n_trials, density, seed=1, n_workers=1):
    ctx = dict(task_name=task_name, N=N, n_draws=n_draws, n_trials=n_trials,
               density=density, seed=seed)
    keys = ("single", "pooled", "inputs")

    if n_workers > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(n_workers, initializer=_init_screen_worker,
                                          initargs=(ctx,)) as pool:
            results = []
            for done, res in enumerate(pool.imap(_screen_genome, range(n_genomes)), 1):
                results.append(res)
                print("      genome %d/%d done" % (done, n_genomes), flush=True)
    else:
        _init_screen_worker(ctx)
        results = []
        for gi in range(n_genomes):
            results.append(_screen_genome(gi))
            print("      genome %d/%d done" % (gi + 1, n_genomes), flush=True)

    per = {k: [r[0][k] for r in results] for k in keys}
    abl = {k: [r[1][k] for r in results] for k in keys}

    nc = SC.make_net_cfg(N=N)
    _, _, _, meta = TASKS[task_name](n_trials, nc.n_in, seed=seed)
    out = dict(N=N, n_test=n_trials - n_trials // 2,
               **{k: v for k, v in meta.items() if k not in ("task", "N")})
    out["task"] = task_name
    out["chance"] = r_null(out["n_test"])
    for k in keys:
        M = np.array(per[k])
        gm = M.mean(1)
        sig = float(np.std(gm, ddof=1))
        noi = float(np.mean(np.std(M, axis=1, ddof=1)))
        out[k] = float(gm.mean())
        out[k + "_best"] = float(gm.max())
        out[k + "_rel"] = float(sig ** 2 / (sig ** 2 + noi ** 2 + 1e-12))
        out[k + "_abl"] = float(np.mean(abl[k]))
    out["d_ablate"] = out["pooled"] - out["pooled_abl"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tasks", nargs="+", default=["accumulate", "delayed", "dmts"])
    ap.add_argument("--ns", type=int, nargs="+", default=[100])
    ap.add_argument("--genomes", type=int, default=10)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--trials", type=int, default=600,
                    help="n/2 are used to fit. With N features the pooled readout needs "
                         "n_fit >> N; 200 trials gave 100 fit samples for 100 features.")
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--workers", type=int, default=1,
                    help="processes; one GENOME per work unit. Up to 6 available.")
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("task_screen", log_dir="runs/task_screen",
             header="which task is SELECTABLE at gen 0 AND requires recurrence? (D132)"):
        print("tasks=%s  N=%s  genomes=%d  draws=%d  trials=%d  density=%.2f"
              % (a.tasks, a.ns, a.genomes, a.draws, a.trials, a.density))
        print("workers=%d%s" % (a.workers, "  (SERIAL -- pass --workers 6 to parallelise)"
                                 if a.workers <= 1 else "  (one genome per work unit)"))
        print("Random UNDEVELOPED genomes. No GA, no development. dmts is the known-NEGATIVE control.\n")
        rows, t0 = [], time.time()
        for N in a.ns:
            for t in a.tasks:
                print("   %s at N=%d:" % (t, N), flush=True)
                rows.append(screen_one(t, N, a.genomes, a.draws, a.trials, a.density,
                                       n_workers=a.workers))
                print("     done [%.0fs elapsed]" % (time.time() - t0), flush=True)

        ch = rows[0]["chance"]
        print("\n  CHANCE LEVEL for |r| at n_test=%d is %.3f (95th pct of the null). NOT zero."
              % (rows[0]["n_test"], ch))
        print("\n  task        N   | single | pooled | inputs | pooled-inputs | pooled_abl | d_abl")
        print("  ----------------+--------+--------+--------+---------------+------------+------")
        for r in rows:
            print("  %-11s %3d | %.3f%s | %.3f%s | %.3f%s |     %+.3f     |   %.3f    | %+.3f"
                  % (r["task"], r["N"],
                     r["single"], "*" if r["single"] > ch else " ",
                     r["pooled"], "*" if r["pooled"] > ch else " ",
                     r["inputs"], "*" if r["inputs"] > ch else " ",
                     r["pooled"] - r["inputs"], r["pooled_abl"], r["d_ablate"]))
        print("  (* = clears the chance level. pooled-inputs = what RECURRENT PROCESSING adds.)")

        print("\n  task        N   | above chance? | selectable | needs recurrence | VERDICT")
        print("  ----------------+---------------+------------+------------------+--------")
        for r in rows:
            live = max(r["pooled"], r["inputs"], r["single"]) > ch
            sel = live and r["single"] > ch and r["single_rel"] > 0.30
            rec = live and r["d_ablate"] > 0.05
            print("  %-11s %3d |     %-5s     |    %-5s   |      %-5s       | %s"
                  % (r["task"], r["N"], live, sel, rec, "PASS" if (sel and rec) else "fail"))
        print("  (selectable and needs-recurrence are only evaluated where SOME readout clears chance --")
        print("   D130's rule: a variance or difference test means nothing when both arms are noise.)")

        live = [r for r in rows if max(r["pooled"], r["inputs"], r["single"]) > ch]
        readout_gap = [r for r in rows
                       if max(r["pooled"], r["inputs"]) > ch and r["single"] <= ch]
        print("\nREAD:")
        if not live:
            print("  NO TASK IS ABOVE CHANCE ON ANY READOUT (single, pooled, or inputs). The state does not")
            print("  contain the target at all, for any candidate. That is a SUBSTRATE result, not a")
            print("  task-choice result, and no readout or encoding fix addresses it. Vary N before")
            print("  concluding: only N=100 has been tested.")
        elif readout_gap:
            print("  A STRONG readout clears chance where the D095-weak SINGLE readout does not, for: %s"
                  % ", ".join(r["task"] for r in readout_gap))
            print("  The information IS in the state and the D095-weak readout cannot reach it. That")
            print("  is a READOUT finding, and it would explain every null in this project -- loc_single")
            print("  and loc_best have sat at their noise floors in every sweep. The fitness readout,")
            print("  not the task, would then be what needs redesigning (D127's all-neuron arm).")
        else:
            print("  Tasks above chance on pooled: %s" % ", ".join(r["task"] for r in live))
            print("  Read the pooled-inputs column: that is what recurrent processing ADDS over the")
            print("  driven neurons alone. If it is ~0, the network is a feedforward relay (D129/D130).")


if __name__ == "__main__":
    main()
