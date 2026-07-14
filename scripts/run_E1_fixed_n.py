#!/usr/bin/env python3
"""
E1 - fixed_n : the flagship fixed-N dissociation, provenanced.

Runs the connectivity sweep at the operating point chosen by a prior T0 run, writes
the tidy results table, and runs the H1-H4 analysis battery. This is the
PRE-REGISTERED confirmatory experiment: it runs as type 'reg' and will refuse to
start on a dirty git tree (commit first). Point --operating-point at the
chosen_operating_point.json produced by the T0 run so the operating point is fixed
before this runs, and record that T0 run as upstream.

Usage (single-line; Windows cmd has no backslash line-continuation):
    python scripts\run_E1_fixed_n.py --operating-point runs\T0_...\analysis\chosen_operating_point.json --upstream <T0-run-id> --workers 6
    python scripts\run_E1_fixed_n.py --smoke      # tiny, type=smoke, dirty-tree ok
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse, json
import pandas as pd

from ddescent import provenance as P
from ddescent.experiments.fixed_n import SweepConfig, run_sweep
from ddescent import analysis as A


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--operating-point", default=None,
                    help="path to chosen_operating_point.json from a T0 run")
    ap.add_argument("--upstream", nargs="*", default=[],
                    help="upstream run id(s), e.g. the T0 tuning run")
    ap.add_argument("--outcome", default="novel_err")
    ap.add_argument("--workers", type=int, default=6,
                    help="process pool size (laptop: keep <= 6 of 8 cores)")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None,
                    help="where run outputs go; else $DDESCENT_RUNS_ROOT, else <root>/runs")
    args = ap.parse_args()

    res_kw = {}
    if args.operating_point:
        op = json.loads(open(args.operating_point).read())
        res_kw = dict(bias=op["bias"], input_gain=op["input_gain"])
        sr = (op["spectral_radius"],)
    else:
        sr = (0.6, 0.9, 1.1, 1.4, 1.8)

    if args.smoke:
        sweep_cfg = SweepConfig(N=150, densities=(0.05, 0.4), spectral_radii=(0.9, 1.5),
                                seeds=(0, 1), task_kwargs=dict(K=8, n_train=40, n_test=40),
                                reservoir_kwargs=dict(present_ms=100, readout_window_ms=40, **res_kw))
        run_type, tag = "smoke", "wiring"
    else:
        sweep_cfg = SweepConfig(N=1000, densities=(0.02, 0.05, 0.1, 0.2, 0.4, 0.8),
                                spectral_radii=sr, seeds=tuple(range(8)),
                                task_kwargs=dict(K=20, n_train=300, n_test=300, n_high=4),
                                reservoir_kwargs=res_kw)
        run_type, tag = "reg", "flagship"

    run = P.new_run("E1", run_type, project_root=args.project_root, runs_root=args.runs_root,
                    config=sweep_cfg.__dict__, tag=tag, seeds=list(sweep_cfg.seeds),
                    upstream_run_ids=args.upstream,
                    notes="fixed-N dissociation; H1-H4 on " + args.outcome)
    try:
        df = run_sweep(sweep_cfg, verbose=True,
                       n_workers=1 if args.smoke else args.workers)
        df.to_parquet(run.table_path())

        # manipulation check: did the dissociation actually happen?
        pr_span = (df["pr"].min(), df["pr"].max())
        (run.analysis / "manipulation_check.json").write_text(json.dumps(
            dict(pr_min=float(pr_span[0]), pr_max=float(pr_span[1]),
                 pr_varies=bool(pr_span[1] - pr_span[0] > 1.0)), indent=2))

        results = A.run_all(df, outcome=args.outcome)
        (run.analysis / "univariate_r2.txt").write_text(results["univariate"].to_string())
        (run.analysis / "H1_mixedmodel.txt").write_text(str(results["H1_model"].summary()))
        for h in ("H2", "H3", "H4"):
            (run.analysis / f"{h}.json").write_text(
                json.dumps({k: (float(v) if isinstance(v, float) else v)
                            for k, v in results[h].items()}, indent=2, default=str))

        run.finalize(status="complete", n_conditions=len(df),
                     pr_min=float(pr_span[0]), pr_max=float(pr_span[1]))
        print("run:", run.run_id)
        print("PR span:", tuple(round(x, 2) for x in pr_span))
        print(results["univariate"].round(4).to_string(index=False))
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
