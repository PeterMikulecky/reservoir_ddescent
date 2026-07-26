"""block_architecture_probe.py - is there ANY block architecture where recurrence matters? (post-check)

WHY THIS EXISTS. `block_genome_check` found the clustered genome produces no carry past tau_slow, and
worse, ABLATED BEATS INTACT at both delays (0.999 vs 0.931 at 50 ms). Recurrence is not merely absent --
it is actively degrading the cue, behaving as noise relative to the trace. Before changing the genome
again, find out whether the target is even in the space: **can ANY hand-set block architecture make
recurrence matter?** If not, the encoding was never the constraint (E1 refuted, D131 step 4 stop) and
the problem is the neuron model.

THREE CHANGES FROM THE FIRST CHECK, each with a reason:

  1. DEDICATED INHIBITORY BLOCK. `clustered_block_genes` assigned E/I per neuron at ei_split independent
     of block, so every cluster contained its own inhibitory neurons, locally cancelling the excitation
     that would sustain it. The D092 ceiling is "2 clusters + inhib pool" -- a SHARED inhibitory
     population giving global feedback (Wang/Compte). Local inhibition inside each cluster is close to
     the opposite arrangement. Here one block is designated inhibitory and the rest excitatory.

  2. WITHIN-BLOCK STRENGTH IS SWEPT. Whether a cluster sustains itself depends on recurrent loop gain,
     which nobody has measured in this substrate. A single hand-picked `within=4.0` tests one point on
     an unknown curve. Swept from clearly-subcritical to clearly-runaway, with firing rates reported so
     the runaway end is identifiable rather than inferred.

  3. THE RELATION IS MEASURED, NOT JUST CUE CARRY. This is the reframe that matters most. The task runs
     at delay=1, where leak already holds the cue at 1.000 -- long-delay memory is not what the study
     needs. What it needs is that RECURRENT SYNAPSES MATTER FOR THE TASK, because P counts them, and
     D128 established the task's discriminating quantity is the match/non-match conjunction. So the
     decisive column is relation decodability at the probe stage, intact minus ablated. The first check
     never measured it.

READ (pre-registered):
  some strength where intact >> ablated on RELATION  -> recurrence can matter. That architecture and
      that loop gain define the regime; make the genome able to express it and proceed.
  intact >> ablated on CUE CARRY only                -> recurrence supplies memory but not computation.
      Useful for the delay axis (D126 rung 1), not for the task as it stands.
  intact <= ablated everywhere, at every strength    -> E1 REFUTED. Recurrence cannot matter in this
      substrate under any block architecture, so no encoding fix will help. STOP and return to the
      neuron model (D131 step 4 stop condition).
  runaway before any benefit appears                 -> the useful regime is empty: the loop is either
      too weak to contribute or unstable. Also a substrate finding, and a sharper one.

Run:  python scripts/block_architecture_probe.py [--strengths ...] [--genomes 3]
"""
from __future__ import annotations
import argparse
import warnings
from dataclasses import replace

import numpy as np

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet
from ddescent.block_genome import BlockGenes, make_xi, to_genome

from delay_persistence_probe import decode, decode_null, _expand, stage_rows

DEFAULT_STRENGTHS = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]


def ei_block_genes(nc, K_exc: int, within: float, between: float = 0.5,
                   inh_to_exc: float = 1.0, exc_to_inh: float = 1.0,
                   inh_frac: float = 0.2, seed: int = 0) -> BlockGenes:
    """K_exc excitatory blocks plus ONE shared inhibitory block (the ceiling's architecture).

    Block K_exc is the inhibitory pool: every neuron in it is inhibitory, every neuron elsewhere is
    excitatory. That is expressible in one gene per block if sign is a BLOCK property -- which the
    current per-neuron sign genes (D038) cannot do without ~25 coordinated mutations. Recorded because
    it is E1 recurring one level up: the vocabulary cannot say "this type is inhibitory."
    """
    rng = np.random.default_rng(seed)
    K = K_exc + 1
    n_inh = max(1, int(round(inh_frac * nc.N)))
    assign = np.empty(nc.N, dtype=int)
    assign[:n_inh] = K_exc                                     # the inhibitory pool
    rest = np.tile(np.arange(K_exc), int(np.ceil((nc.N - n_inh) / K_exc)))[: nc.N - n_inh]
    assign[n_inh:] = rest
    rng.shuffle(assign)
    B = np.full((K, K), between, dtype=float)
    for i in range(K_exc):
        B[i, i] = within                                       # strong WITHIN excitatory cluster
    B[K_exc, :K_exc] = exc_to_inh                              # exc -> shared inhibition
    B[:K_exc, K_exc] = inh_to_exc                              # shared inhibition -> exc
    B[K_exc, K_exc] = between
    signs = np.where(assign == K_exc, -1.0, 1.0)               # sign is a BLOCK property here
    return BlockGenes(assign=assign, B=B, signs=signs)


def measure(nc, density, xi, genes, task, rel, cue, n_seeds, ablate: bool):
    probe = stage_rows(task, "test", "probe")
    delay = stage_rows(task, "test", "delay")
    out = {k: [] for k in ("rate", "cue", "lin", "quad", "lin_null", "quad_null", "silent")}
    for s in range(n_seeds):
        g = to_genome(genes, xi, density)
        if ablate:
            g = replace(g, mag=np.zeros_like(g.mag))
        B = EvoNet(g, nc).behave(task.E_test, noise_seed=2 + s)
        Xp, Xd = B["state"][probe], B["state"][delay]
        out["rate"].append(float(Xp.mean()))
        out["silent"].append(float(np.mean(Xp.std(0) < 1e-6)))
        out["cue"].append(decode(Xd, cue))
        out["lin"].append(decode(Xp, rel))
        out["lin_null"].append(decode_null(Xp, rel, n_rep=25)[1])
        Zq = _expand(Xp, "quad", seed=s, k_override=10)
        out["quad"].append(decode(Zq, rel))
        out["quad_null"].append(decode_null(Zq, rel, n_rep=25)[1])
    return {k: float(np.mean(v)) for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strengths", type=float, nargs="+", default=DEFAULT_STRENGTHS)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--k-exc", type=int, default=4)
    ap.add_argument("--genomes", type=int, default=3)
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--delay", type=int, default=1)
    ap.add_argument("--xi-seed", type=int, default=7)
    a = ap.parse_args()

    warnings.filterwarnings("ignore")
    with tee("block_architecture_probe", log_dir="runs/block_genome",
             header="is there ANY block architecture where recurrence matters?"):
        nc = SC.make_net_cfg(N=a.n)
        xi = make_xi(nc.N, seed=a.xi_seed)
        task = SC.make_trial_task(n_trials=a.trials, n_val=a.trials, n_test=a.trials,
                                  delay_segments=a.delay)
        rel = (task.cue_test == task.probe_test).astype(int)
        cue = task.cue_test
        print("N=%d  K_exc=%d + 1 inhibitory block  density=%.2f  delay=%d (%d ms)  nmda_frac=%.2f"
              % (nc.N, a.k_exc, a.density, a.delay, a.delay * 50, nc.nmda_frac))
        print("Sweeping WITHIN-cluster excitatory strength. Sign is a BLOCK property here, so the")
        print("inhibitory pool is SHARED (the D092 ceiling architecture) rather than split across")
        print("clusters as in the first check -- where local inhibition cancelled each cluster.\n")

        rows = []
        for w in a.strengths:
            genes = ei_block_genes(nc, a.k_exc, within=w, seed=1)
            i = measure(nc, a.density, xi, genes, task, rel, cue, a.genomes, ablate=False)
            b = measure(nc, a.density, xi, genes, task, rel, cue, a.genomes, ablate=True)
            rows.append((w, i, b))
            print("   within=%-5g done  (rate %.3f, silent %.0f%%)" % (w, i["rate"], 100 * i["silent"]),
                  flush=True)

        print("\n  within | rate  | silent | CUE: intact/abl (d)      | RELATION quad: intact/abl (d)")
        print("  -------+-------+--------+--------------------------+------------------------------")
        for w, i, b in rows:
            print("  %-6g | %.3f | %5.0f%% | %.3f / %.3f  (%+.3f) | %.3f / %.3f  (%+.3f)%s"
                  % (w, i["rate"], 100 * i["silent"], i["cue"], b["cue"], i["cue"] - b["cue"],
                     i["quad"], b["quad"], i["quad"] - b["quad"],
                     "  *" if (i["quad"] - b["quad"]) > 0.05 and i["quad"] > i["quad_null"] else ""))
        print("  (* = intact exceeds ablated on the RELATION by >0.05 AND clears its own null)")

        dq = [(w, i["quad"] - b["quad"], i["quad"] > i["quad_null"]) for w, i, b in rows]
        dc = [(w, i["cue"] - b["cue"]) for w, i, b in rows]
        best_q = max(dq, key=lambda t: t[1])
        best_c = max(dc, key=lambda t: t[1])
        runaway = [w for w, i, b in rows if i["rate"] > 3 * rows[0][1]["rate"] or i["silent"] > 0.2]
        print("\nREAD:")
        print("  best RELATION gain from recurrence: %+.3f at within=%g%s"
              % (best_q[1], best_q[0], " (clears null)" if best_q[2] else " (does NOT clear its null)"))
        print("  best CUE-CARRY gain from recurrence: %+.3f at within=%g" % (best_c[1], best_c[0]))
        if runaway:
            print("  unstable / saturating at within >= %g (rate blow-up or silent units)" % min(runaway))
        if best_q[1] > 0.05 and best_q[2]:
            print("  RECURRENCE CAN MATTER. That architecture and loop gain define the regime; make the")
            print("  genome able to express it (block-level sign genes) and proceed to D131 step 3.")
        elif best_c[1] > 0.05:
            print("  Recurrence supplies MEMORY but not computation. Useful for the delay axis (D126")
            print("  rung 1), not for the task as it stands.")
        else:
            print("  NO ARCHITECTURE AND NO LOOP GAIN MAKES RECURRENCE MATTER. E1 is REFUTED: the")
            print("  encoding was never the constraint, because the target is not in the space at all.")
            print("  STOP (D131 step 4). Return to the neuron model and the substrate's capacity for")
            print("  persistent activity -- with one fewer explanation available.")


if __name__ == "__main__":
    main()
