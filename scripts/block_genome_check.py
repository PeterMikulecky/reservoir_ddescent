"""block_genome_check.py - D131 build steps 1, 2 and 4. The decisive test of the redesign.

THREE QUESTIONS, IN THE ORDER THAT MATTERS:

  STEP 1 (invariants). P_syn is EXACTLY N*k at every K, no dead units, Dale's law holds, and RANDOM
  block genomes are NOT clustered. The last is the E2 falsification surface: a structured prior that is
  already clustered would be a seeded genome under another name.

  STEP 2 (known positive). Does a HAND-SET clustered genome hold the cue at a delay PAST tau_slow,
  where D130 showed the direct-encoded network holds nothing? This is the ceiling's topology expressed
  in the new vocabulary. If it fails, the implementation is wrong and nothing after it matters.
  WARNING - QUARANTINE (D092): the clustered genome is an instrument check ONLY. Never a seed, template,
  initial population, or comparison for evolved networks.

  STEP 4 (ablation, repeated). Intact vs ablated (`mag` zeroed, tau_slow retained) on the SAME genomes.
  D130 found the difference to be zero at every coupling and delay under the direct encoding, which is
  what made P meaningless. **If recurrence STILL contributes nothing here, E1 is refuted and the whole
  redesign has failed** -- stop rather than proceeding to a sweep.

WHY DELAY=4 (200 ms). tau_slow = 100 ms, so 50 ms is within passive single-neuron decay and cannot
discriminate: D130's ablated arm held the cue at 1.000 there and the comparison was uninformative. Past
tau_slow, leak alone fails, so anything that survives is contributed by CONNECTIVITY. Delay 1 is run
alongside purely as a positive control that the measurement works at all.

READ (pre-registered):
  clustered >> random at delay=4, and intact >> ablated  -> the encoding supplies what was missing.
    Proceed to step 3 (gen-0 prior at chance) then step 5 (mutational smoothness).
  clustered ~ random at delay=4                          -> the block genome does not produce carry.
    Implementation bug, or clusters are insufficient at this N. Fix before anything else.
  intact ~ ablated even for the clustered genome         -> E1 REFUTED. Recurrence contributes nothing
    even when the genome CAN express clustering, so the encoding was never the constraint. The problem
    is the neuron model or the substrate's capacity for persistent activity. STOP.

Run:  python scripts/block_genome_check.py [--n 100] [--delays 1 4] [--genomes 4]
"""
from __future__ import annotations
import argparse
import warnings
from dataclasses import replace

import numpy as np

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet
from ddescent.block_genome import (make_xi, to_genome, random_block_genes, clustered_block_genes)
from ddescent.trial_task import seg_layout

from delay_persistence_probe import decode, decode_null, stage_rows


def invariants(nc, density, xi, Ks=(2, 4, 8, 12, 20, 30)) -> bool:
    k = max(1, min(int(round(density * (nc.N - 1))), nc.N - 1))
    print("\n== STEP 1  INVARIANTS ==")
    print("   k=%d inputs per neuron -> P_syn must be N*k = %d at every K" % (k, nc.N * k))
    print("    K  | P_gene | P_syn | fixed | in-deg | dead | dale | cluster ratio (random)")
    ok = True
    for K in Ks:
        g = random_block_genes(nc, K, seed=K)
        gen = to_genome(g, xi, density)
        ind = (gen.mag != 0).sum(1)
        ps = int((gen.mag != 0).sum())
        a = g.assign
        same = a[:, None] == a[None, :]
        np.fill_diagonal(same, False)
        pres = gen.mag != 0
        ratio = pres[same].mean() / max(pres[~same].mean(), 1e-9)
        good = (ps == nc.N * k) and ind.min() > 0 and gen.dale_violations() == 0 and ratio < 1.6
        ok &= good
        print("    %2d | %6d | %5d | %-5s | %2d-%2d  |  %d   |  %d   | %.2f %s"
              % (K, g.p_gene(), ps, ps == nc.N * k, ind.min(), ind.max(),
                 int((ind == 0).sum()), gen.dale_violations(), ratio,
                 "" if good else "  <- FAIL"))
    print("   cluster ratio for RANDOM genomes must stay near 1 (E2: a clustered prior is a seeded")
    print("   genome under another name). The hand-set clustered genome should read >> 1.")
    return ok


def carry(nc, cfg, density, xi, delay, n_genomes, n_trials, seed=1):
    """Cue decodability at the DELAY stage, clustered vs random, intact vs ablated."""
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials,
                              delay_segments=delay)
    cue = task.cue_test
    rows = stage_rows(task, "test", "delay")
    out = {}
    for kind in ("clustered", "random"):
        for arm in ("intact", "ablated"):
            acc, nul = [], []
            for gi in range(n_genomes):
                genes = (clustered_block_genes(nc, 4, seed=seed + gi) if kind == "clustered"
                         else random_block_genes(nc, 4, seed=seed + gi))
                g = to_genome(genes, xi, density)
                if arm == "ablated":
                    g = replace(g, mag=np.zeros_like(g.mag))
                B = EvoNet(g, nc).behave(task.E_test, noise_seed=2 + gi)
                X = B["state"][rows]
                acc.append(decode(X, cue))
                nul.append(decode_null(X, cue, n_rep=30)[1])
            out[(kind, arm)] = (float(np.mean(acc)),
                                float(np.std(acc, ddof=1)) if n_genomes > 1 else 0.0,
                                float(np.mean(nul)))
            print("     %s/%s delay=%d done" % (kind, arm, delay), flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--delays", type=int, nargs="+", default=[1, 4])
    ap.add_argument("--genomes", type=int, default=4)
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--xi-seed", type=int, default=7)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("block_genome_check", log_dir="runs/block_genome",
             header="D131 steps 1/2/4 -- invariants, known positive, ablation repeated"):
        nc = SC.make_net_cfg(N=a.n)
        cfg = SC.make_trial_evolve_cfg()
        xi = make_xi(nc.N, seed=a.xi_seed)
        print("N=%d density=%.2f xi_seed=%d genomes=%d trials=%d tau_slow=%.0f ms"
              % (nc.N, a.density, a.xi_seed, a.genomes, a.trials, nc.tau_slow))

        ok = invariants(nc, a.density, xi)
        if not ok:
            print("\n   INVARIANTS FAILED -- stop here; nothing downstream is meaningful.")
            return

        print("\n== STEPS 2 and 4  CARRY: does connectivity hold the cue past tau_slow? ==")
        res = {}
        for d in a.delays:
            print("   delay=%d (%d ms)%s:" % (d, d * 50,
                  "  <- within passive decay, control only" if d * 50 <= nc.tau_slow
                  else "  <- PAST tau_slow, this is the test"))
            res[d] = carry(nc, cfg, a.density, xi, d, a.genomes, a.trials)

        print("\n  cue decodability at the DELAY stage, mean (sd) vs null")
        print("  delay      | genome    | intact          | ablated         | intact - ablated")
        print("  -----------+-----------+-----------------+-----------------+-----------------")
        for d in a.delays:
            for kind in ("clustered", "random"):
                i_m, i_s, i_n = res[d][(kind, "intact")]
                b_m, b_s, b_n = res[d][(kind, "ablated")]
                print("  %d (%3dms) | %-9s | %.3f (%.3f) %s | %.3f (%.3f) %s |     %+.3f"
                      % (d, d * 50, kind, i_m, i_s, "*" if i_m > i_n else " ",
                         b_m, b_s, "*" if b_m > b_n else " ", i_m - b_m))
        print("  (* = clears its own shuffled-label null)")

        print("\nREAD:")
        test_d = [d for d in a.delays if d * 50 > nc.tau_slow]
        if not test_d:
            print("  No delay past tau_slow was run -- the informative comparison is missing.")
            return
        d = test_d[0]
        c_i = res[d][("clustered", "intact")][0]
        c_a = res[d][("clustered", "ablated")][0]
        r_i = res[d][("random", "intact")][0]
        nullv = res[d][("clustered", "intact")][2]
        print("  At delay=%d (%d ms, past tau_slow):" % (d, d * 50))
        print("    clustered intact %.3f | clustered ablated %.3f | random intact %.3f | null %.3f"
              % (c_i, c_a, r_i, nullv))
        if c_i > nullv and (c_i - c_a) > 0.05 and (c_i - r_i) > 0.05:
            print("  THE ENCODING SUPPLIES WHAT WAS MISSING. Clustered connectivity holds the cue where")
            print("  leak alone cannot, and ablating it removes the effect. Proceed to step 3 (gen-0")
            print("  prior must be AT CHANCE) and step 5 (mutational smoothness vs fitness).")
        elif c_i <= nullv or (c_i - r_i) <= 0.05:
            print("  CLUSTERED IS NOT BETTER THAN RANDOM. The block genome does not produce carry --")
            print("  implementation bug, or clusters are insufficient at this N. Fix before anything else.")
        else:
            print("  INTACT ~ ABLATED EVEN WHEN CLUSTERED. E1 IS REFUTED: recurrence contributes nothing")
            print("  even when the genome CAN express clustering, so the encoding was never the")
            print("  constraint. The problem is the neuron model or the substrate's capacity for")
            print("  persistent activity. STOP -- do not proceed to a sweep.")


if __name__ == "__main__":
    main()
