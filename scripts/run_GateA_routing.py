#!/usr/bin/env python3
"""GATE A (D080/D081) — does selection route E to the output neurons?

Pre-registered: metric = champion E|rates (NMSE reconstructing E from output rates) on a fixed
200-env probe. PASS = falls from ~0.99 to < 0.80 by the final generation. See D080/D081.

Run from repo root:  python run_GateA_routing.py
~2.2 h (D079). Prints progress with ETA; logs to runs/E9_evolve/.../logs/run.log.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from ddescent import provenance as P
from ddescent import tasks as T
from ddescent.evonet import EvoNetConfig
from ddescent.evolve import EvolveConfig, run_evolution

# ---- pre-registered config (D080/D081) --------------------------------------------------
N, POP, D, N_ENV, DENS, GENS = 50, 30, 3, 50, 0.5, 4900
PROBE_ENV = 200          # D081: over-determined decode (200 >> 50 state dims)
SEED = 0

def main():
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("--gens", type=int, default=GENS, help="override depth (default 4900)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    task = T.hierarchical_environments(K=10, d=D, r1=3, n_contexts=4, n_train=N_ENV,
                                       n_test=N_ENV, context_dwell=10, seed=args.seed)
    # independent probe (different seed) so routing is measured on held-out stimuli
    probe = T.hierarchical_environments(K=10, d=D, r1=3, n_contexts=4, n_train=PROBE_ENV,
                                        n_test=PROBE_ENV, context_dwell=10, seed=args.seed + 12345)
    net = EvoNetConfig(N=N, n_in=10, d=D, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                       present_ms=50, readout_window_ms=20, nmda_frac=0.5)
    cfg = EvolveConfig(pop_size=POP, n_generations=args.gens, density=DENS, seed=args.seed,
                       selection="replicator", test_every=20, track_routing=True,
                       _routing_probe={"E_train": probe.E_train, "E_test": probe.E_test})

    run = P.new_run("E9", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(gate="A", N=N, pop=POP, d=D, n_env=N_ENV, density=DENS,
                                gens=args.gens, probe_env=PROBE_ENV, nmda_frac=0.5),
                    tag="gateA-routing", seeds=[args.seed],
                    notes="Gate A (D080/D081): does selection route E to the output neurons?")
    print(f"run: {run.run_id}")
    run.start_log()

    hr = task.headroom()   # D057 required pre-run check
    print(f"task: memoryless_floor={hr['memoryless_floor']:.3f} oracle={hr['oracle_ceiling']:.3f}")
    print(f"Gate A pass (D081): champion E|rates 0.99 -> < 0.80 by gen {args.gens}\n")

    hist, pop = run_evolution(task, net, cfg, verbose=True, batched=True)
    df = pd.DataFrame(hist)
    df.to_parquet(run.table_path("gateA"))

    routing = df[df.e_from_rates.notna()][["gen", "e_from_rates", "e_from_state", "best_train"]]
    r0 = float(routing.e_from_rates.iloc[0]); rN = float(routing.e_from_rates.iloc[-1])
    sN = float(routing.e_from_state.iloc[-1])
    print("\n=== GATE A ROUTING TRAJECTORY (champion E|rates on the 200-env probe) ===")
    print(f"{'gen':>6} {'E|rates':>9} {'E|state':>9} {'best_train':>11}")
    for _, r in routing.iterrows():
        print(f"{int(r.gen):>6} {r.e_from_rates:>9.3f} {r.e_from_state:>9.3f} {r.best_train:>11.3f}")

    fell = r0 - rN
    print(f"\n=== VERDICT (D081) ===")
    print(f"  E|rates: {r0:.3f} (gen 0) -> {rN:.3f} (gen {int(routing.gen.iloc[-1])})   fell {fell:+.3f}")
    print(f"  E|state ceiling at end: {sN:.3f}")
    if rN < 0.80 and fell >= 0.05:
        verdict = "PASS -- selection ROUTES E to the output neurons. Gate B is meaningful."
    elif rN <= 0.93 and fell >= 0.05:
        verdict = "AMBIGUOUS -- weak routing. Report, do not over-read."
    else:
        verdict = "FAIL -- routing not established. Investigate BEFORE Gate B (D080 fail-map)."
    print(f"  => {verdict}")

    best_train_final = float(df.best_train.iloc[-1])
    print(f"\n  secondary (D080): champion train {best_train_final:.3f} vs memoryless floor "
          f"{hr['memoryless_floor']:.3f} -- beating it needs CONTEXT (level-2, blocked D076); "
          f"{'BELOW floor (unexpected!)' if best_train_final < hr['memoryless_floor'] else 'above floor (expected)'}")

    run.finalize(status="complete", n_conditions=1,
                 notebook_note=(f"Gate A: E|rates {r0:.3f}->{rN:.3f} (fell {fell:+.3f}); "
                                f"{'PASS' if (rN<0.80 and fell>=0.05) else 'AMBIG' if (rN<=0.93 and fell>=0.05) else 'FAIL'}"))

if __name__ == "__main__":
    main()
