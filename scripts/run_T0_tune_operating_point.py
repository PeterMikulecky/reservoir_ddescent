#!/usr/bin/env python3
r"""
T0 - tune_operating_point : the mandatory Step 0.

Maps the reservoir's dynamical regime across operating-point hyperparameters
(bias, input_gain, spectral_radius) at fixed N, and finds the operating point where
participation ratio (PR) is both LARGE and RESPONSIVE to connectivity -- the only
regime in which the E1 fixed-N dissociation has a live independent variable.

For every (operating point x connectivity) cell it records not just PR but the
diagnostics needed to understand WHY a regime succeeds or fails:
  * pr        : effective dimensionality of the reservoir state
  * activity  : fraction of (pattern, neuron) rate-features that are active
                -> near 0 = silent network ; near 1 = SATURATED ; mid = healthy
  * rate      : mean filtered firing feature
Per operating point it then aggregates across the connectivity grid:
  pr_mean, pr_max, pr_range (= max-min), pr_cv (= std/mean), activity_mean, rate_mean.

Ranking is transparent: keep operating points in a HEALTHY activity band, then rank
by PR responsiveness (pr_range) with peak PR (pr_max) as tie-break. The winner is a
SUGGESTION -- the full landscape is saved for you to inspect before committing.

Run type is 'exp' (exploratory): this is where the operating point is chosen, before
any pre-registered E1 run.

Usage (Windows cmd, venv active):
  python scripts\run_T0_tune_operating_point.py --preset coarse   # cheap, N=500 (start here)
  python scripts\run_T0_tune_operating_point.py --preset fine     # full, N=1000
  python scripts\run_T0_tune_operating_point.py --preset smoke    # tiny wiring test
  # zoom into a promising region after coarse (comma-separated grids):
  python scripts\run_T0_tune_operating_point.py --N 1000 --biases 0.3,0.4,0.5 --gains 0.2,0.3 --radii 0.9,1.1,1.3 --densities 0.05,0.2,0.6
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse
import numpy as np
import pandas as pd

from ddescent import provenance as P
from ddescent.connectivity import ConnectivityConfig, make_recurrent_weights, make_input_weights
from ddescent.reservoir import ReservoirConfig, LIFReservoir
from ddescent.measures import participation_ratio, effective_rank

# activity band considered a healthy dynamical regime (not silent, not saturated)
HEALTHY_LO, HEALTHY_HI = 0.05, 0.90
U_SEED = 12345           # probe inputs are IDENTICAL across all cells for comparability


def _probe_cell(payload: dict) -> dict:
    """One (operating point x density) cell. TOP-LEVEL/picklable for Windows spawn."""
    p = payload
    U = np.random.default_rng(U_SEED).standard_normal((p["n_probe"], p["K"]))
    W = make_recurrent_weights(ConnectivityConfig(
        N=p["N"], density=p["density"], spectral_radius=p["sr"], seed=p["seed"]))
    Win = make_input_weights(p["N"], p["K"], seed=p["seed"] + 1)
    res = LIFReservoir(W, Win, ReservoirConfig(
        N=p["N"], bias=p["bias"], input_gain=p["ig"], seed=p["seed"] + 2, **p["res_kw"]))
    X = res.run_static(U)
    eps = 1e-6
    return dict(bias=p["bias"], input_gain=p["ig"], spectral_radius=p["sr"],
                density=p["density"], present_ms=p["res_kw"].get("present_ms", 150.0),
                pr=participation_ratio(X), effective_rank=effective_rank(X),
                activity=float((X > eps).mean()), rate=float(X.mean()))


def run_cells(grid: dict, N, K, n_probe, seed, res_kw, n_workers, verbose=True) -> pd.DataFrame:
    import itertools
    present_list = grid.get("present_ms_list") or [res_kw.get("present_ms", 150.0)]
    cells = list(itertools.product(grid["biases"], grid["gains"],
                                   grid["radii"], grid["densities"], present_list))

    def _cell_res_kw(pm):
        # derive readout window / sampling so short (transient) reads still work
        rk = dict(res_kw)
        rk["present_ms"] = pm
        rk["readout_window_ms"] = min(rk.get("readout_window_ms", 60.0), 0.6 * pm)
        rk["sample_ms"] = max(2.0, pm / 10.0)
        return rk

    payloads = [dict(bias=b, ig=g, sr=r, density=d, N=N, K=K, n_probe=n_probe,
                     seed=seed, res_kw=_cell_res_kw(pm))
                for (b, g, r, d, pm) in cells]
    rows = []
    if n_workers <= 1:
        for i, pl in enumerate(payloads):
            rows.append(_probe_cell(pl))
            if verbose and (i % 10 == 0 or i == len(payloads) - 1):
                print(f"  [{i+1}/{len(payloads)}] cells done")
    else:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=n_workers) as pool:
            for i, row in enumerate(pool.imap_unordered(_probe_cell, payloads)):
                rows.append(row)
                if verbose and (i % 10 == 0 or i == len(payloads) - 1):
                    print(f"  [{i+1}/{len(payloads)}] cells done")
    return pd.DataFrame(rows)


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    keys = ["bias", "input_gain", "spectral_radius", "present_ms"]
    g = (df.groupby(keys)
           .agg(pr_mean=("pr", "mean"), pr_max=("pr", "max"), pr_min=("pr", "min"),
                pr_std=("pr", "std"), activity_mean=("activity", "mean"),
                rate_mean=("rate", "mean"))
           .reset_index())
    g["pr_range"] = g["pr_max"] - g["pr_min"]
    g["pr_cv"] = g["pr_std"] / g["pr_mean"].replace(0, np.nan)
    g["healthy"] = (g["activity_mean"] >= HEALTHY_LO) & (g["activity_mean"] <= HEALTHY_HI)
    return g


def rank(agg: pd.DataFrame) -> pd.DataFrame:
    healthy = agg[agg["healthy"]]
    pool = healthy if len(healthy) else agg
    return pool.sort_values(["pr_range", "pr_max"], ascending=False).reset_index(drop=True)


PRESETS = {
    "smoke": dict(grid=dict(biases=(0.4, 0.7), gains=(0.3,), radii=(0.9, 1.5),
                            densities=(0.05, 0.4)),
                  N=120, K=8, n_probe=30, res_kw=dict(present_ms=100, readout_window_ms=40),
                  run_type="smoke", tag="wiring"),
    "coarse": dict(grid=dict(biases=(0.2, 0.4, 0.6, 0.8), gains=(0.1, 0.3, 0.6),
                             radii=(0.7, 1.0, 1.3, 1.6), densities=(0.05, 0.2, 0.6)),
                   N=500, K=20, n_probe=120, res_kw=dict(),
                   run_type="exp", tag="coarse-scan"),
    "fine": dict(grid=dict(biases=(0.3, 0.5, 0.7, 0.9), gains=(0.2, 0.4, 0.8),
                           radii=(0.6, 0.9, 1.1, 1.4, 1.8), densities=(0.02, 0.1, 0.4, 0.8)),
                 N=1000, K=20, n_probe=200, res_kw=dict(),
                 run_type="exp", tag="fine-scan"),
}


def _floats(s):
    return tuple(float(x) for x in s.split(",")) if s else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS), default="coarse")
    ap.add_argument("--smoke", action="store_true", help="alias for --preset smoke")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--N", type=int, default=None, help="override N")
    ap.add_argument("--n-probe", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    # optional grid overrides (comma-separated) for zooming into a region
    ap.add_argument("--biases", type=_floats, default=None)
    ap.add_argument("--gains", type=_floats, default=None)
    ap.add_argument("--radii", type=_floats, default=None)
    ap.add_argument("--densities", type=_floats, default=None)
    ap.add_argument("--present-ms", type=_floats, default=None,
                    help="sweep readout timing: short values read the recurrent "
                         "TRANSIENT (restores PR responsiveness); e.g. 20,40,80,150")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    preset = PRESETS["smoke" if args.smoke else args.preset]
    grid = dict(preset["grid"])
    for name, val in [("biases", args.biases), ("gains", args.gains),
                      ("radii", args.radii), ("densities", args.densities)]:
        if val is not None:
            grid[name] = val
    if args.present_ms is not None:
        grid["present_ms_list"] = args.present_ms
    N = args.N or preset["N"]
    n_probe = args.n_probe or preset["n_probe"]
    workers = 1 if (args.smoke or args.preset == "smoke") else args.workers

    cfg = dict(grid=grid, N=N, K=preset["K"], n_probe=n_probe, seed=args.seed,
               res_kw=preset["res_kw"], workers=workers, preset=args.preset)
    n_present = len(grid.get("present_ms_list") or [1])
    n_cells = (len(grid["biases"]) * len(grid["gains"]) *
               len(grid["radii"]) * len(grid["densities"]) * n_present)

    run = P.new_run("T0", preset["run_type"], project_root=args.project_root,
                    runs_root=args.runs_root, config=cfg, tag=args.tag or preset["tag"],
                    seeds=[args.seed],
                    notes="operating-point landscape: PR + activity diagnostics")
    print(f"run: {run.run_id}")
    print(f"grid: {n_cells} cells (N={N}, n_probe={n_probe}, workers={workers})")
    try:
        df = run_cells(grid, N, preset["K"], n_probe, args.seed,
                       preset["res_kw"], workers)
        df.to_parquet(run.table_path("cells"))
        agg = aggregate(df)
        agg.to_parquet(run.data / "operating_points.parquet")
        ranked = rank(agg)
        ranked.to_parquet(run.data / "operating_points_ranked.parquet")

        # diagnostics the human needs to see immediately
        print(f"\nactivity across grid: min={agg.activity_mean.min():.2f} "
              f"max={agg.activity_mean.max():.2f}  (healthy band {HEALTHY_LO}-{HEALTHY_HI})")
        n_healthy = int(agg.healthy.sum())
        print(f"healthy operating points: {n_healthy}/{len(agg)}")
        if n_healthy == 0:
            if agg.activity_mean.median() > HEALTHY_HI:
                print("  !! network is SATURATED almost everywhere -> lower bias / input_gain,")
                print("     or shorten present_ms to read the transient instead of the fixed point.")
            else:
                print("  !! network is mostly SILENT -> raise bias / input_gain.")
        print(f"PR responsiveness (pr_range) best: {ranked.pr_range.iloc[0]:.1f}; "
              f"peak PR seen: {agg.pr_max.max():.1f}")
        # the failure mode most likely to sink E1: healthy regime, but PR barely
        # moves with connectivity. Flag it explicitly, since its fix differs from
        # the saturation fix.
        if n_healthy:
            rel = ranked["pr_range"].iloc[0] / max(ranked["pr_mean"].iloc[0], 1e-9)
            if rel < 0.10:
                print(f"  !! best PR varies only {100*rel:.1f}% across connectivity -- "
                      f"too flat for E1.")
                print("     Connectivity isn't shaping effective dimensionality here. Next "
                      "levers: shorten present_ms to read")
                print("     the recurrent TRANSIENT rather than the settled fixed point, or "
                      "move to temporal inputs.")
        print("\ntop candidate operating points:")
        show = ["bias", "input_gain", "spectral_radius", "present_ms", "pr_mean",
                "pr_max", "pr_range", "activity_mean", "healthy"]
        print(ranked[show].head(8).round(3).to_string(index=False))

        best = ranked.iloc[0]
        chosen = dict(bias=float(best.bias), input_gain=float(best.input_gain),
                      spectral_radius=float(best.spectral_radius),
                      present_ms=float(best.present_ms),
                      pr_mean=float(best.pr_mean), pr_max=float(best.pr_max),
                      pr_range=float(best.pr_range), activity_mean=float(best.activity_mean),
                      healthy=bool(best.healthy))
        (run.analysis / "chosen_operating_point.json").write_text(pd.Series(chosen).to_json(indent=2))
        note = (f"{n_healthy}/{len(agg)} healthy; best pr_range={best.pr_range:.2f} "
                f"(pr_mean={best.pr_mean:.1f}); peak PR={agg.pr_max.max():.1f}; "
                f"chosen bias={best.bias} gain={best.input_gain} sr={best.spectral_radius} "
                f"present_ms={best.present_ms}")
        run.finalize(status="complete", n_conditions=len(df), chosen_operating_point=chosen,
                     notebook_note=note)
        print(f"\nsuggested operating point written to chosen_operating_point.json")
        print("  (inspect operating_points.parquet before committing to it)")
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
