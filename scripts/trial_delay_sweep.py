"""DELAY SWEEP for the trial task: does a gen-0 fitness gradient appear as the delay shrinks toward a
pure binding task (0 ms), and does accuracy see it where NMSE does not?

Motivation: the n=30 reliability read at delay=1 (50 ms) found trial_score (NMSE) flat on BOTH
populations and only accuracy carrying marginal signal (evolved only). The delay is the framework-SAFE
task knob (unlike a curriculum: pick ONE rung and sweep P under it). present_ms=50, so 0-50 ms is
exactly two rungs -- delay_segments 0 (no maintenance, pure cue x probe binding) and 1 (one 50 ms
silent gap). This measures reliability at each, for both bases, so you can choose the fixed operating
rung on evidence.

Reuses the reliability probe's honest machinery (develop once, sample draws, ICC decomposition). Reports
the ICC reliability (the conservative estimate; the V_obs regression over-reads near the floor). RANDOM
population by default because THAT is the gen-0 launch question; add --populations evolved for the
"selectable once moving" read (expensive: adds a short GA per delay).

Usage:
  python trial_delay_sweep.py [--n 20] [--draws 6] [--nval 40] [--assays 1 2 4 8]
                              [--delays 0 1] [--dev-ms 16000] [--populations random [evolved]]
  Full dev_ms by default (development is what surfaces signal; do not shorten it for a "quick" look
  unless you accept a suppressed-signal read). --dev-ms 8000 = one pass, ~2x faster, indicative.
"""
import sys, argparse, pathlib
_here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parent)); sys.path.insert(0, str(_here))
import numpy as np, warnings
warnings.filterwarnings("ignore")

from ddescent import study_config as SC
from ddescent.runlog import tee
from trial_reliability_probe import make_population, collect, decompose


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--draws", type=int, default=6)
    ap.add_argument("--nval", type=int, default=40)
    ap.add_argument("--assays", type=int, nargs="+", default=[1, 2, 4, 8])
    ap.add_argument("--delays", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--evolve-gens", type=int, default=5)
    ap.add_argument("--dev-ms", type=float, default=None)
    ap.add_argument("--populations", nargs="+", default=["random"], choices=["random", "evolved"])
    args = ap.parse_args()
    assays = [a for a in args.assays if a <= args.draws]

    with tee("trial_delay_sweep", log_dir="runs/delay_sweep",
             header=f"delay sweep {args.delays} segments (x{SC.NET['present_ms']}ms); n={args.n} "
                    f"draws={args.draws} n_val={args.nval}"):
        net_cfg = SC.make_net_cfg()
        print("DELAY SWEEP  (reliability = ICC, the conservative estimate; a real gen-0 gradient needs")
        print("signal_sd above the noise floor AND reliability climbing with n_assays)")
        print("n=%d draws=%d n_val=%d assays=%s dev_ms=%s" %
              (args.n, args.draws, args.nval, assays,
               int(args.dev_ms) if args.dev_ms else int(SC.trial_dev_ms())))

        for pop_kind in args.populations:
            print("\n" + "=" * 90)
            print("POPULATION: %s" % pop_kind.upper())
            print("=" * 90)
            print(" delay | basis        | signal_sd | noise_sd | reliability(ICC) " +
                  "  ".join("a%d" % a for a in assays))
            print(" ------+--------------+-----------+----------+" + "-" * 40)
            for d in args.delays:
                task = SC.make_trial_task(delay_segments=d, n_val=args.nval)
                cfg = SC.make_trial_evolve_cfg()
                if args.dev_ms is not None:
                    cfg.dev_ms = args.dev_ms
                genomes = make_population(pop_kind, task, net_cfg, cfg, args.n, args.evolve_gens)
                stored, Y = collect(genomes, task, net_cfg, cfg, args.draws, base_seed=6000 + 1000 * d)
                for basis in ("trial_score", "val_acc"):
                    r = decompose(stored, Y, args.nval, basis, assays)
                    rels = "  ".join("%.2f" % r["rel"][a][0] for a in assays)   # ICC column
                    print("  %2dms | %-12s |  %.4f   |  %.4f  | %s"
                          % (d * SC.NET["present_ms"], basis,
                             r["signal_var_icc"] ** 0.5, r["noise_var"] ** 0.5, rels))
            print()

        print("READ:")
        print("  * signal_sd rises and reliability clears ~0.3-0.4 at 0 ms but not 50 ms  -> the delay")
        print("    (maintenance) is what flattens the gradient; run the study at delay=0 (a clean fixed")
        print("    rung: pure binding, no memory) rather than a curriculum.")
        print("  * accuracy shows a gradient where NMSE does not, at either delay  -> the fix is the")
        print("    fitness BASIS (select on accuracy), independent of the delay -- touches nothing P")
        print("    depends on.")
        print("  * both bases flat at both delays  -> the block is binding itself, not maintenance;")
        print("    delay is not the lever and the operating point / task structure is next.")


if __name__ == "__main__":
    main()
