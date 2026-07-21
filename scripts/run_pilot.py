"""PILOT run of the complete step-3 apparatus (D096-D098b). Structured as a grid of independent
(P, seed) CELLS -- embarrassingly parallel and VM-ready (each cell is its own GA run, separately
provenanced). Default n_workers=6 (leave 2 cores free on an 8-core laptop, PJM).

THE PILOT'S QUESTION (not the double-descent curve -- that's the full run). Does the apparatus BEHAVE
over a real number of generations?
  1. Does FITNESS CLIMB under selection (vs the flat Gate A on birth fitness, D082)?
  2. Do the COMPONENTS (encoding, carrying, regulation) PERSIST and COMPOUND over generations, or
     dissolve (the noise test PJM named -- gen-0 signal was expected-flat; real signal must compound)?
  3. Any blowups / NaNs / degenerate collapse over 50 generations?
  4. Does carrying (now the validated covariance-decay measure, D098b) actually rise, so the
     carrying*regulation second-descent term can switch on (the D096 concern)?

Pilot grid (small, ~1.1 hr on 6 cores at 4s/eval): densities x 1 seed, 50 generations, pop 30.
If encouraging -> design the full run (more P, more seeds, more gens, c_syn sweep).

Run from repo root:  python scripts/run_pilot.py            (uses 6 workers)
                     python scripts/run_pilot.py --workers 4  (override)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np
from ddescent import provenance as P
from ddescent import tasks as T
from ddescent.evonet import EvoNetConfig
from ddescent.evolve import EvolveConfig, run_evolution

# --- pilot grid (deliberately small; this is a shakedown, not the experiment) ---------------
DENSITIES = [0.2, 0.4, 0.6, 0.8]     # the P axis (nominal density -> synapse count)
SEEDS = [0]                          # 1 seed for the pilot
POP = 30
GENS = 50
DEV_MS = 800.0
N_ASSAYS = 1                         # 1 during evolution (selection averages over gens); fresh noise/gen


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    ap.add_argument("--gens", type=int, default=GENS)
    ap.add_argument("--pop", type=int, default=POP)
    args = ap.parse_args()

    task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                       context_dwell=10, seed=0)
    floor = task.headroom()["memoryless_floor"]; ceil = task.headroom()["oracle_ceiling"]

    run = P.new_run("E9", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(experiment="pilot", densities=DENSITIES, seeds=SEEDS,
                                pop=args.pop, gens=args.gens, dev_ms=DEV_MS, n_assays=N_ASSAYS,
                                workers=args.workers, floor=floor, ceiling=ceil),
                    tag="step3-pilot",
                    notes="Pilot of the full develop+3-term-fitness+selection apparatus (D096-D098b). "
                          "Q: does fitness climb + components compound over 50 gens? shakedown, not "
                          "the double-descent curve.")
    print(f"run: {run.run_id}")
    print(f"STEP-3 PILOT | grid {len(DENSITIES)}P x {len(SEEDS)}seed | pop {args.pop} x {args.gens} gens "
          f"| {args.workers} workers")
    print(f"task floor={floor:.3f} ceiling={ceil:.3f}\n")

    all_rows = []
    for dens in DENSITIES:
        for seed in SEEDS:
            netcfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                                  present_ms=50, tau_slow=100.0, nmda_frac=0.5)
            cfg = EvolveConfig(pop_size=args.pop, n_generations=args.gens, elite=2, density=dens,
                               dev_ms=DEV_MS, n_assays=N_ASSAYS, seed=seed, c_syn=0.0)
            print(f"--- cell density={dens} seed={seed} ---")
            hist, _ = run_evolution(task, netcfg, cfg, n_workers=args.workers, verbose=False)
            for h in hist:
                h["density"] = dens; h["seed"] = seed
                all_rows.append(h)
            h0, hf = hist[0], hist[-1]
            print(f"  fit: {h0['fit_mean']:.4f} -> {hf['fit_mean']:.4f} (best_test {h0['best_test']:.3f} "
                  f"-> {hf['best_test']:.3f})")
            print(f"  enc: {h0['enc_mean']:.4f}->{hf['enc_mean']:.4f}  "
                  f"car: {h0['car_mean']:.4f}->{hf['car_mean']:.4f}  "
                  f"reg: {h0['reg_mean']:.4f}->{hf['reg_mean']:.4f}")

    import pandas as pd
    df = pd.DataFrame(all_rows)
    df.to_parquet(run.table_path("pilot_history"))

    # --- pilot verdict: did the apparatus behave? -------------------------------------------
    print("\n=== PILOT VERDICT ===")
    climbed, compounded, clean = [], [], True
    for dens in DENSITIES:
        d = df[df.density == dens].sort_values("gen")
        fit_climb = d["fit_mean"].iloc[-1] - d["fit_mean"].iloc[0]
        car_rise = d["car_mean"].iloc[-1] - d["car_mean"].iloc[0]
        reg_rise = d["reg_mean"].iloc[-1] - d["reg_mean"].iloc[0]
        nan_any = d[["fit_mean", "enc_mean", "car_mean", "reg_mean"]].isna().any().any()
        climbed.append(fit_climb > 0); compounded.append(car_rise > 0 or reg_rise > 0)
        clean = clean and not nan_any
        print(f"  P={dens}: fit {'+' if fit_climb>0 else ''}{fit_climb:.4f} | "
              f"car {'+' if car_rise>0 else ''}{car_rise:.4f} | reg {'+' if reg_rise>0 else ''}{reg_rise:.4f}"
              f"{' | NaN!' if nan_any else ''}")
    print(f"\nfitness climbed in {sum(climbed)}/{len(DENSITIES)} cells")
    print(f"a capability (car or reg) compounded in {sum(compounded)}/{len(DENSITIES)} cells")
    print(f"no NaN/degenerate: {clean}")
    ok = sum(climbed) >= len(DENSITIES) // 2 and clean
    print(f"\n=> apparatus {'BEHAVES -- design the full run' if ok else 'has issues -- inspect before full run'}")

    run.finalize(status="complete", n_conditions=len(df),
                 notebook_note=f"Step-3 pilot: fitness climbed {sum(climbed)}/{len(DENSITIES)} cells, "
                               f"capability compounded {sum(compounded)}/{len(DENSITIES)}, clean={clean}. "
                               f"{'apparatus behaves' if ok else 'needs inspection'}.")


if __name__ == "__main__":
    main()
