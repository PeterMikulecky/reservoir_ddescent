#!/usr/bin/env python3
r"""
T0 - tune_operating_point : fix the reservoir operating point for E9.

REV 2 (D014/D023/D025): sweeps **w0** (fixed per-synapse coupling), NOT spectral_radius.
D014 established that spectral radius is inert in this spiking LIF model -- the entire
rho in [0.5, 2.0] range is a dead zone where recurrence has no measurable effect on PR.
The operative coupling knob is w0 (~0.5-3.0).

WHAT THIS SCRIPT DECIDES.  In E9 rev. C the genome is (M, p, w0, recip, ei) -- so w0 and
p are EVOLVABLE and must NOT be fixed here. What must be fixed is the *substrate*:
**bias and input_gain**. So the sweep is

    (bias x input_gain)   <- the operating point we are choosing
        x (w0 x density)  <- the genome subspace evolution will explore

and each (bias, input_gain) is scored by how the reservoir behaves *across the genome
space* it will have to support:
  * pr_range / pr_rel   -- does PR actually MOVE as the genome varies? (E9 needs a live
                           dimensionality axis; a flat substrate makes the GA pointless)
  * pr_max              -- is there usable dimensionality at all?
  * activity_mean       -- is the network healthy (not silent, not saturated)?

Ranking: keep operating points in a healthy activity band, then rank by PR responsiveness
(pr_rel) with peak PR as tie-break. The winner is a SUGGESTION; the full landscape is
saved for inspection.

Full metric battery (D025) is recorded per cell, including the **spectrum** -- so any
spectral metric (edof, spectral entropy, ...) is recoverable post hoc without re-running.

Usage (Windows cmd, venv active):
  python scripts\run_T0_tune_operating_point.py --preset smoke    # wiring test
  python scripts\run_T0_tune_operating_point.py --preset coarse   # N=300, start here
  python scripts\run_T0_tune_operating_point.py --preset fine     # N=1000, production
  python scripts\run_T0_tune_operating_point.py --preset fine --biases 0.3,0.4,0.5 --gains 0.2,0.3
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse, itertools
import numpy as np
import pandas as pd

from ddescent import provenance as P
from ddescent.connectivity import ConnectivityConfig, make_recurrent_weights, make_input_weights
from ddescent.reservoir import ReservoirConfig, LIFReservoir
from ddescent import metrics as MET
from ddescent import baseline as BASE
from ddescent import tasks as TASKS

HEALTHY_LO, HEALTHY_HI = 0.05, 0.90     # activity band: not silent, not saturated
U_SEED = 12345                          # identical probe inputs across every condition


def _probe_cell(pl: dict) -> dict:
    """One (bias, input_gain, w0, density) condition. TOP-LEVEL/picklable for Windows spawn.

    REV 3 (D030): now runs an actual TASK and scores the reservoir against a RAW-INPUT
    baseline. PR alone is not a fitness signal -- at the operating point the PR-only
    objective selected (gain 0.1), the reservoir was 4x WORSE than no reservoir at all.
    """
    W = make_recurrent_weights(ConnectivityConfig(
        N=pl["N"], density=pl["density"], w0=pl["w0"],
        spectral_radius=None, seed=pl["seed"]))          # w0 mode (D014)
    Win = make_input_weights(pl["N"], pl["K"], seed=pl["seed"] + 1)
    res = LIFReservoir(W, Win, ReservoirConfig(
        N=pl["N"], bias=pl["bias"], input_gain=pl["ig"], seed=pl["seed"] + 2, **pl["res_kw"]))

    task = TASKS.anisotropic_regression(K=pl["K"], n_train=pl["n_probe"],
                                        n_test=pl["n_probe"], seed=pl["seed"] + 500)
    S_tr = res.run_stationary(task.U_train, sample_ms=pl.get("sample_ms", 6.0))
    S_te = res.run_stationary(task.U_test, sample_ms=pl.get("sample_ms", 6.0))

    bat = MET.full_battery(S_tr["X_mean"], W)             # D025: includes the spectrum
    spec = bat.pop("spectrum")
    scored = BASE.evaluate_features(S_tr, S_te, task)     # D030: the gate
    pr_var = MET.pr_from_spectrum(MET.spectrum(S_tr["X_var"]))

    row = dict(bias=pl["bias"], input_gain=pl["ig"], w0=pl["w0"], density=pl["density"],
               N=pl["N"], pr_var=pr_var, **bat, **scored)
    row["spectrum"] = spec.tolist()
    return row


def run_cells(grid, N, K, n_probe, seed, res_kw, n_workers, sample_ms=6.0, verbose=True) -> pd.DataFrame:
    cells = list(itertools.product(grid["biases"], grid["gains"],
                                   grid["w0s"], grid["densities"]))
    payloads = [dict(bias=b, ig=g, w0=w, density=d, N=N, K=K, n_probe=n_probe,
                     seed=seed, res_kw=res_kw, sample_ms=sample_ms) for (b, g, w, d) in cells]
    rows = []
    if n_workers <= 1:
        for i, pl in enumerate(payloads):
            rows.append(_probe_cell(pl))
            if verbose and (i % 10 == 0 or i == len(payloads) - 1):
                print(f"  [{i+1}/{len(payloads)}] cells")
    else:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(processes=n_workers) as pool:
            for i, row in enumerate(pool.imap_unordered(_probe_cell, payloads)):
                rows.append(row)
                if verbose and (i % 10 == 0 or i == len(payloads) - 1):
                    print(f"  [{i+1}/{len(payloads)}] cells")
    return pd.DataFrame(rows)


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Score each (bias, input_gain) by its behaviour ACROSS the (w0 x density) genome space."""
    g = (df.groupby(["bias", "input_gain"])
           .agg(pr_mean=("pr", "mean"), pr_max=("pr", "max"), pr_min=("pr", "min"),
                pr_var_mean=("pr_var", "mean"),
                skill_med=("best_skill", "median"), skill_max=("best_skill", "max"),
                frac_beating=("beats_baseline", "mean"),
                activity_mean=("active_frac", "mean"),
                silent_frac=("silent_frac", "mean"), rate_cv=("rate_cv", "mean"))
           .reset_index())
    g["pr_range"] = g["pr_max"] - g["pr_min"]
    g["pr_rel"] = g["pr_range"] / g["pr_mean"].replace(0, np.nan)   # relative responsiveness
    g["healthy"] = (g["activity_mean"] >= HEALTHY_LO) & (g["activity_mean"] <= HEALTHY_HI)
    # D030: skill is a GATE. An operating point where the reservoir loses to a linear
    # readout on the raw input is disqualified no matter how responsive its PR looks.
    g["useful"] = g["skill_med"] > 1.0
    return g


def rank(agg: pd.DataFrame) -> pd.DataFrame:
    """Gate on usefulness AND health first; only THEN rank by PR responsiveness.

    Ordering matters (D030). The previous version ranked on pr_rel alone and selected an
    operating point where the reservoir was 4x worse than no reservoir. Dimensionality is
    only interesting in a regime that computes.
    """
    pool = agg[agg["useful"] & agg["healthy"]]
    if not len(pool):
        pool = agg[agg["useful"]]
    if not len(pool):
        pool = agg          # nothing beats baseline; caller must warn loudly
    return pool.sort_values(["skill_med", "pr_rel"], ascending=False).reset_index(drop=True)


PRESETS = {
    "smoke":  dict(grid=dict(biases=(0.4,), gains=(1.0, 10.0), w0s=(0.5, 2.0),
                             densities=(0.05, 0.3)),
                   N=120, K=8, n_probe=40, sample_ms=8.0,
                   res_kw=dict(present_ms=100, readout_window_ms=40),
                   run_type="smoke", tag="wiring"),
    # D030: gain grids now span the range where the reservoir can actually BEAT the
    # raw-input baseline. The old grids topped out at 0.6; the reservoir first beat
    # baseline at gain=10. We were searching entirely inside the useless regime.
    "coarse": dict(grid=dict(biases=(0.2, 0.4, 0.6), gains=(0.3, 1.0, 3.0, 10.0, 30.0),
                             w0s=(0.5, 1.5, 3.0), densities=(0.02, 0.1, 0.4)),
                   N=300, K=20, n_probe=100, res_kw=dict(), sample_ms=6.0,
                   run_type="exp", tag="coarse-w0-skill"),
    "fine":   dict(grid=dict(biases=(0.2, 0.4, 0.6), gains=(1.0, 3.0, 10.0, 30.0),
                             w0s=(0.5, 1.0, 2.0, 3.0), densities=(0.01, 0.05, 0.15, 0.4)),
                   N=1000, K=20, n_probe=150, res_kw=dict(), sample_ms=6.0,
                   run_type="exp", tag="fine-w0-skill-N1000"),
}


def _floats(s): return tuple(float(x) for x in s.split(",")) if s else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS), default="coarse")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--N", type=int, default=None)
    ap.add_argument("--n-probe", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--biases", type=_floats, default=None)
    ap.add_argument("--gains", type=_floats, default=None)
    ap.add_argument("--w0s", type=_floats, default=None)
    ap.add_argument("--densities", type=_floats, default=None)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    pre = PRESETS[args.preset]
    grid = dict(pre["grid"])
    for name, val in [("biases", args.biases), ("gains", args.gains),
                      ("w0s", args.w0s), ("densities", args.densities)]:
        if val is not None:
            grid[name] = val
    N = args.N or pre["N"]
    n_probe = args.n_probe or pre["n_probe"]
    workers = 1 if args.preset == "smoke" else args.workers
    n_cells = int(np.prod([len(v) for v in grid.values()]))

    cfg = dict(grid=grid, N=N, K=pre["K"], n_probe=n_probe, seed=args.seed,
               res_kw=pre["res_kw"], workers=workers, preset=args.preset,
               coupling_mode="w0", note="rev2: sweeps w0 per D014; bias/input_gain is what T0 fixes")
    run = P.new_run("T0", pre["run_type"], project_root=args.project_root,
                    runs_root=args.runs_root, config=cfg, tag=args.tag or pre["tag"],
                    seeds=[args.seed],
                    notes="operating-point landscape in w0 parameterization; fixes bias/input_gain for E9")
    print(f"run: {run.run_id}")
    print(f"grid: {n_cells} cells (N={N}, n_probe={n_probe}, workers={workers})")
    print(f"choosing bias x input_gain; w0 x density is the genome space E9 will explore\n")
    try:
        df = run_cells(grid, N, pre["K"], n_probe, args.seed, pre["res_kw"], workers,
                       sample_ms=pre.get("sample_ms", 6.0))
        df.to_parquet(run.table_path("cells"))
        agg = aggregate(df)
        agg.to_parquet(run.data / "operating_points.parquet")
        ranked = rank(agg)
        ranked.to_parquet(run.data / "operating_points_ranked.parquet")

        print(f"\n=== D030 GATE: does the reservoir beat a linear readout on the RAW INPUT? ===")
        print(f"baseline (raw input) test NMSE: {df.baseline_nmse.median():.3f}")
        print(f"reservoir skill (baseline/reservoir; >1 = helps): "
              f"median {df.best_skill.median():.2f}, max {df.best_skill.max():.2f}")
        nb = int(df.beats_baseline.sum())
        print(f"conditions beating baseline: {nb}/{len(df)}")
        if nb == 0:
            print("  !! NOTHING beats the baseline. The reservoir is not computing anywhere")
            print("     in this grid. Raise input_gain further before trusting any PR result.")
        print(f"\nPR across all conditions: {df.pr.min():.1f} .. {df.pr.max():.1f}")
        print(f"activity across cells: {df.active_frac.min():.2f} .. {df.active_frac.max():.2f}"
              f"  (healthy band {HEALTHY_LO}-{HEALTHY_HI})")
        n_healthy = int(agg.healthy.sum())
        print(f"healthy operating points: {n_healthy}/{len(agg)}")
        if n_healthy == 0:
            if agg.activity_mean.median() > HEALTHY_HI:
                print("  !! SATURATED nearly everywhere -> lower bias / input_gain")
            else:
                print("  !! SILENT nearly everywhere -> raise bias / input_gain")

        best = ranked.iloc[0]
        rel = best.pr_rel
        print(f"\nbest PR responsiveness across the genome space: {100*rel:.0f}% "
              f"(pr {best.pr_min:.1f}..{best.pr_max:.1f})")
        if rel < 0.10:
            print("  !! PR barely moves across (w0 x density) -- E9 has no live dimensionality")
            print("     axis at this substrate. Widen w0/density, or revisit bias/input_gain.")
        else:
            print("  OK: PR is responsive -> E9 has a live dimensionality axis.")

        print("\ntop candidate operating points (gated on skill>1 AND healthy, then ranked):")
        show = ["bias", "input_gain", "skill_med", "frac_beating", "pr_mean", "pr_var_mean",
                "pr_rel", "activity_mean", "useful", "healthy"]
        print(ranked[show].head(8).round(3).to_string(index=False))

        chosen = dict(bias=float(best.bias), input_gain=float(best.input_gain),
                      skill_med=float(best.skill_med), frac_beating=float(best.frac_beating),
                      useful=bool(best.useful),
                      pr_mean=float(best.pr_mean), pr_var_mean=float(best.pr_var_mean),
                      pr_max=float(best.pr_max), pr_rel=float(best.pr_rel),
                      activity_mean=float(best.activity_mean), healthy=bool(best.healthy),
                      N=N, coupling_mode="w0")
        if not bool(best.useful):
            print("\n  !! WARNING: the chosen point does NOT beat baseline. It is not a valid")
            print("     operating point -- widen the gain grid rather than accepting it.")
        (run.analysis / "chosen_operating_point.json").write_text(pd.Series(chosen).to_json(indent=2))
        note = (f"skill_med={best.skill_med:.2f} (baseline {df.baseline_nmse.median():.3f}); "
                f"{nb}/{len(df)} conditions beat baseline; chosen bias={best.bias} "
                f"gain={best.input_gain}; PR_mean={best.pr_mean:.1f} PR_var={best.pr_var_mean:.1f}")
        run.finalize(status="complete", n_conditions=len(df),
                     chosen_operating_point=chosen, notebook_note=note)
        print(f"\nwrote chosen_operating_point.json  (inspect operating_points.parquet before committing)")
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
