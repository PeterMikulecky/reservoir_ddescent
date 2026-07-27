"""propagation_probe.py - where does the signal die? (post-screen; literature-motivated)

THE FINDING THAT PROMPTED THIS. The task screen at N=100 on `accumulate`: the ten DRIVEN neurons carry
the target at |r| = 0.475 (chance 0.115), a pooled readout over all 100 gets 0.356, and the D095-weak
readout on the designated output neuron gets 0.054 -- BELOW chance. Adding the ninety non-driven neurons
makes a pooled readout WORSE than the ten driven ones alone. The architecture is input neurons ->
recurrent network -> designated output neurons, and it appears to fail at the first hop: the fitness
reads cells that have no access to what the network was given.

WHAT THIS MEASURES. Per-neuron |r| with the target, grouped by SYNAPTIC DISTANCE from the driven
neurons: hop 0 (driven), hop 1 (direct postsynaptic targets), hop 2, and beyond. If |r| falls to chance
at hop 1, that is a TRANSMISSION result -- not about the task, the readout, or the encoding -- and it
would explain every null this project has recorded, since the fitness has always read a neuron several
hops from the input.

TWO LITERATURE-MOTIVATED VARIABLES, both from refs supplied 2026-07-27:

  N. Yaqoob & Wrobel evolve SNNs that solve temporal pattern recognition with THREE OR FOUR INTERNEURONS
  plus one output neuron -- total 4-5 cells, with a single output neuron as the fitness readout, which
  is exactly our D095 arrangement. It works for them. The difference is scale: in a 5-neuron network
  every cell is effectively adjacent to the input, whereas at N=100 with 30 inputs each, signal from ten
  driven neurons is diluted across ninety. Our N may be too large for the signal to REACH a designated
  readout, and separately too large for evolution to SEARCH (their genomes are tiny and encode topology).
  So N is swept DOWN, not up -- the opposite of the direction assumed after D129.

  AUTAPSES. Self-connections are excluded project-wide -- `np.fill_diagonal(..., False)` in evonet,
  evolve, connectivity, and block_genome. But Seung et al. (2000) show an autapse is the minimal
  short-term analog memory (tuned synaptic feedback), and Yaqoob & Wrobel's follow-ups make
  self-excitation central: "Autapses enable temporal pattern recognition in spiking neural networks",
  "The Importance of Self-excitation in Spiking Neural Networks Evolved to Recognize Temporal Patterns".
  D130 found this substrate's ONLY memory is passive single-neuron leak. An autapse is precisely the
  mechanism that would make that time constant tunable per neuron -- and we removed it by construction.

READ (pre-registered):
  |r| at chance from hop 1 onward, at every N -> TRANSMISSION failure. The fitness cannot see the input
      at any scale, and no task, readout, or encoding change addresses it.
  |r| survives at small N but not large -> a SCALE result. Small networks are the regime this substrate
      supports, matching the evolved-SNN literature, and the study should move there.
  autapses raise hop-1+ |r| or the delayed-task score -> self-excitation supplies the memory the
      recurrent network does not, and excluding it was a substantive modelling choice, not a detail.

Run:  python scripts/propagation_probe.py [--ns 10 25 50 100] [--autapses both] [--workers 6]
"""
from __future__ import annotations
import argparse
import warnings

import numpy as np

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet, random_genome

from task_screen import make_accumulate, r_null


def hop_distance(mag, n_in):
    """Synaptic distance of every neuron from the DRIVEN set, by breadth-first search on mag != 0.

    mag[i, j] != 0 means j (pre) -> i (post), so a neuron is reachable in one more hop than any of its
    presynaptic partners. Unreached neurons get -1 and are reported separately: they are structurally
    incapable of carrying stimulus information at all, which is worth knowing on its own.
    """
    N = mag.shape[0]
    dist = np.full(N, -1)
    dist[:n_in] = 0
    frontier = list(range(n_in))
    d = 0
    while frontier:
        d += 1
        nxt = []
        for j in frontier:
            for i in np.where(mag[:, j] != 0)[0]:
                if dist[i] < 0:
                    dist[i] = d
                    nxt.append(int(i))
        frontier = nxt
    return dist


def per_neuron_r(S, y):
    """|Pearson r| between each neuron's activity and the target. One number per neuron, no fitting."""
    Sz = (S - S.mean(0)) / (S.std(0) + 1e-12)
    yz = (y - y.mean()) / (y.std() + 1e-12)
    return np.abs(Sz.T @ yz / len(y))


def probe_one(N, autapses, n_genomes, n_trials, density, seed=1, n_in=None):
    nc = SC.make_net_cfg(N=N) if n_in is None else SC.make_net_cfg(N=N, n_in=n_in)
    cfg = SC.make_trial_evolve_cfg()
    E, y, read_rows, _ = make_accumulate(n_trials, nc.n_in, seed=seed)
    rows = []
    for gi in range(n_genomes):
        g = random_genome(nc, density, w0=SC.w0_for_density(density),
                          ei_split=cfg.ei_split, seed=seed + gi)
        if autapses:
            # restore self-connections at the same magnitude scale as the rest of the genome
            rng = np.random.default_rng(seed + gi)
            diag = np.abs(rng.standard_normal(nc.N)) * float(np.abs(g.mag[g.mag != 0]).mean())
            mag = g.mag.copy()
            np.fill_diagonal(mag, diag)
            from dataclasses import replace
            g = replace(g, mag=mag)
        B = EvoNet(g, nc).behave(E, noise_seed=100)
        S = B["state"][read_rows]
        r = per_neuron_r(S, y)
        dist = hop_distance(g.mag, nc.n_in)
        rows.append((r, dist))
        print("      N=%d autapses=%s genome %d done" % (N, autapses, gi), flush=True)
    R = np.concatenate([r for r, _ in rows])
    D = np.concatenate([d for _, d in rows])
    # WARNING: if the designated readout cell is itself a DRIVEN neuron, it reads the stimulus
    # directly and the network is bypassed entirely. At N=10 with the config's n_in=10 that is the
    # whole network, and the designated cell duly "cleared" at 0.280 in a smoke run -- which says
    # nothing about transmission. Flagged so the row cannot be misread.
    out = dict(N=N, autapses=autapses, chance=r_null(len(y)), n_in=nc.n_in,
               designated_is_driven=bool((nc.N - nc.d) < nc.n_in))
    for h in (0, 1, 2, 3):
        m = D == h
        out["hop%d" % h] = float(R[m].mean()) if m.any() else float("nan")
        out["hop%d_n" % h] = int(m.sum())
    m = D > 3
    out["hop4plus"] = float(R[m].mean()) if m.any() else float("nan")
    out["unreached"] = int((D < 0).sum())
    out["designated"] = float(np.mean([r[nc.N - nc.d] for r, _ in rows]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ns", type=int, nargs="+", default=[8, 12, 20, 50, 100])
    ap.add_argument("--autapses", choices=["off", "on", "both"], default="both")
    ap.add_argument("--genomes", type=int, default=4)
    ap.add_argument("--trials", type=int, default=300)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--n-in", type=int, default=4,
                    help="driven neurons. The config default of 10 leaves NO interneurons at N<=10, "
                         "making small-N rows uninformative. Yaqoob & Wrobel's networks are 3-4 "
                         "interneurons plus one output, so a small n_in is the analogous setting.")
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("propagation_probe", log_dir="runs/propagation",
             header="where does the signal die? hop distance x N x autapses"):
        modes = [False, True] if a.autapses == "both" else [a.autapses == "on"]
        print("N=%s  autapses=%s  genomes=%d  trials=%d  density=%.2f"
              % (a.ns, modes, a.genomes, a.trials, a.density))
        print("Task is `accumulate` -- the only candidate that cleared chance in the screen.")
        print("Per-neuron |r| with the target, grouped by SYNAPTIC HOPS from the driven neurons.\n")
        rows = []
        for N in a.ns:
            for au in modes:
                rows.append(probe_one(N, au, a.genomes, a.trials, a.density, n_in=a.n_in))

        ch = rows[0]["chance"]
        print("\n  chance |r| for a single neuron at n=%d is %.3f\n" % (a.trials, ch))
        print("   N   autapse | hop0 (driven) | hop1  | hop2  | hop3  | 4+    | unreached | designated")
        print("  -----+--------+---------------+-------+-------+-------+-------+-----------+-----------")
        for r in rows:
            def f(k):
                v = r.get(k, float("nan"))
                return "  -  " if np.isnan(v) else ("%.3f%s" % (v, "*" if v > ch else " "))
            print("  %4d   %-6s |     %s     | %s | %s | %s | %s |    %4d   |   %s%s"
                  % (r["N"], "ON" if r["autapses"] else "off", f("hop0"), f("hop1"),
                     f("hop2"), f("hop3"), f("hop4plus"), r["unreached"],
                     "%.3f%s" % (r["designated"], "*" if r["designated"] > ch else " "),
                     "  <- DRIVEN cell: bypasses the network" if r["designated_is_driven"] else ""))
        print("  (* = above the single-neuron chance level. 'designated' is the D095 fitness cell.)")

        print("\nREAD:")
        for r in rows:
            if np.isnan(r["hop1"]):
                print("   N=%-4d autapse=%-3s : NO hop-1 neurons exist (n_in=%d covers the network) --"
                      % (r["N"], "ON" if r["autapses"] else "off", r["n_in"]))
                print("        uninformative about transmission; lower --n-in to create interneurons.")
                continue
            drop = r["hop0"] - r["hop1"]
            print("   N=%-4d autapse=%-3s : hop0 %.3f -> hop1 %.3f (drop %.3f)%s"
                  % (r["N"], "ON" if r["autapses"] else "off", r["hop0"], r["hop1"], drop,
                     "   <- signal survives one hop" if r["hop1"] > ch else "   <- DIES at one hop"))
        alive = [r for r in rows if not np.isnan(r["hop1"]) and r["hop1"] > ch]
        if not alive:
            print("\n  THE SIGNAL DIES AT THE FIRST HOP AT EVERY N AND IN BOTH AUTAPSE CONDITIONS.")
            print("  The fitness reads neurons that cannot access the stimulus. That is a TRANSMISSION")
            print("  result: no task, readout, or encoding change addresses it, and it would explain")
            print("  every null this project has recorded.")
        else:
            print("\n  Signal survives one hop at: %s"
                  % ", ".join("N=%d/autapse=%s" % (r["N"], "ON" if r["autapses"] else "off")
                              for r in alive))
            print("  Those are the configurations where a downstream fitness readout could work at all.")


if __name__ == "__main__":
    main()
