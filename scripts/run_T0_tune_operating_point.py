#!/usr/bin/env python3
"""
T0 - tune_operating_point : the mandatory Step 0.

Maps participation ratio (PR) against reservoir operating-point hyperparameters
(bias, input_gain, spectral radius) at fixed N, and scores each operating point by
how RESPONSIVE its PR is to connectivity density. The winning operating point is the
one where PR is both large and sensitive to connectivity -- the only regime in which
the E1 fixed-N dissociation has a live independent variable.

Run type is 'exp' (exploratory): this pre-sweep is where the operating point is
chosen, before any pre-registered E1 run. Outputs are fully provenanced.

Usage:
    python scripts/run_T0_tune_operating_point.py            # real grid
    python scripts/run_T0_tune_operating_point.py --smoke    # tiny, for wiring tests
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse
import numpy as np
import pandas as pd

from ddescent import provenance as P
from ddescent.connectivity import ConnectivityConfig, make_recurrent_weights, make_input_weights
from ddescent.reservoir import ReservoirConfig, LIFReservoir
from ddescent.measures import participation_ratio


def sweep(biases, input_gains, radii, densities, N, K, n_probe, seed, res_kw):
    rng = np.random.default_rng(seed)
    U = rng.standard_normal((n_probe, K))
    rows = []
    for bias in biases:
        for ig in input_gains:
            for sr in radii:
                prs = []
                for density in densities:
                    W = make_recurrent_weights(
                        ConnectivityConfig(N=N, density=density, spectral_radius=sr, seed=seed))
                    Win = make_input_weights(N, K, seed=seed + 1)
                    res = LIFReservoir(W, Win, ReservoirConfig(
                        N=N, bias=bias, input_gain=ig, seed=seed + 2, **res_kw))
                    pr = participation_ratio(res.run_static(U))
                    prs.append(pr)
                    rows.append(dict(bias=bias, input_gain=ig, spectral_radius=sr,
                                     density=density, pr=pr))
                # responsiveness = spread of PR across connectivity at this operating point
                for r in rows[-len(densities):]:
                    r["pr_range_over_density"] = float(np.ptp(prs))
                    r["pr_mean_over_density"] = float(np.mean(prs))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None,
                    help="where run outputs go; else $DDESCENT_RUNS_ROOT, else <root>/runs")
    args = ap.parse_args()

    if args.smoke:
        cfg = dict(biases=(0.4, 0.7), input_gains=(0.3,), radii=(0.9, 1.5),
                   densities=(0.05, 0.4), N=120, K=8, n_probe=30,
                   seed=0, res_kw=dict(present_ms=100, readout_window_ms=40))
        run_type, tag = "smoke", "wiring"
    else:
        cfg = dict(biases=(0.3, 0.5, 0.7, 0.9), input_gains=(0.2, 0.4, 0.8),
                   radii=(0.6, 0.9, 1.1, 1.4, 1.8), densities=(0.02, 0.1, 0.4, 0.8),
                   N=1000, K=20, n_probe=200, seed=0, res_kw=dict())
        run_type, tag = "exp", "operating-point-scan"

    run = P.new_run("T0", run_type, project_root=args.project_root, runs_root=args.runs_root,
                    config=cfg, tag=tag, seeds=[cfg["seed"]],
                    notes="PR-vs-operating-point; pick largest, most density-responsive PR")
    try:
        df = sweep(**cfg)
        df.to_parquet(run.table_path())
        # pick the winning operating point: maximize responsiveness, tie-break on mean PR
        by_op = (df.groupby(["bias", "input_gain", "spectral_radius"])
                   .agg(pr_range=("pr_range_over_density", "first"),
                        pr_mean=("pr_mean_over_density", "first"))
                   .reset_index()
                   .sort_values(["pr_range", "pr_mean"], ascending=False))
        by_op.to_parquet(run.data / "operating_points_ranked.parquet")
        winner = by_op.iloc[0].to_dict()
        (run.analysis / "chosen_operating_point.json").write_text(pd.Series(winner).to_json(indent=2))
        run.finalize(status="complete", n_conditions=len(df), chosen_operating_point=winner)
        print("run:", run.run_id)
        print("chosen operating point:", {k: round(v, 3) if isinstance(v, float) else v
                                          for k, v in winner.items()})
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
