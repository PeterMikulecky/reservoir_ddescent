#!/usr/bin/env python3
r"""
AN - analyze a feature-check run properly.

The feature-check script prints a deliberately simple model (err ~ PR + (1|net_seed)).
That model is under-specified in two ways -- BOTH fixable at analysis time, because the
saved table already carries w0, density, net_seed, task_seed and every per-feature metric
(D025: store the object, not the summary). No re-run required.

Models fitted here, in increasing honesty:

  M1  err ~ pr + (1|net_seed)
        The printed model. PR is NOT randomly assigned -- it is an emergent property of
        w0 and density, which we DID manipulate. So beta_PR here is confounded with them.

  M2  err ~ pr + w0 + density + (1|net_seed)
        Controls the manipulated structure. Asks: does PR predict error BEYOND w0 and
        density? This is D019's screening-off test in its simplest form -- Frank's claim H
        is that dimensionality SCREENS OFF circuit features. If pr stays significant while
        w0/density fall away, that supports H. If w0/density survive and pr does not,
        structure is doing the work and PR is a bystander.

  M3  err ~ pr + (1 + pr|net_seed)
        Random SLOPE. M1/M2 assume every network has the same PR->error slope and differs
        only in baseline. If the slope itself varies by network, that assumption is wrong
        and the fixed-effect estimate is misleading.

Known limitation NOT fixable here: net_seed and task_seed are ALIASED in the current
design (task_seed = net_seed + 500), so network variance and environment variance cannot
be separated. That needs a CROSSED design (several networks x several task draws) -- an
additional experiment, not a re-analysis.

Usage:
  python scripts\analyze_AN_feature_check.py --run-dir runs\T0_tune_operating_point\<run_id>
  python scripts\analyze_AN_feature_check.py --run-dir <...> --outcome test_
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse, json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from ddescent import provenance as P

FEATURES = ("mean", "inst", "var")


def fit_models(df: pd.DataFrame, tag: str, outcome_prefix: str) -> dict:
    """Fit M1/M2/M3 for one feature channel."""
    col = f"{outcome_prefix}{tag}"
    d = df[[f"pr_{tag}", col, "w0", "density", "net_seed"]].dropna().copy()
    d.columns = ["pr", "err", "w0", "density", "net_seed"]
    # z-score continuous predictors so coefficients are comparable
    for c in ("pr", "w0", "density"):
        s = d[c].std()
        d[c] = (d[c] - d[c].mean()) / (s if s > 0 else 1.0)

    out = {"feature": tag, "n": len(d), "n_seeds": int(d.net_seed.nunique())}
    try:
        m1 = smf.mixedlm("err ~ pr", d, groups=d.net_seed).fit(reml=False)
        out["M1_beta_pr"] = float(m1.params["pr"]); out["M1_p_pr"] = float(m1.pvalues["pr"])
    except Exception as e:
        out["M1_beta_pr"] = np.nan; out["M1_p_pr"] = np.nan; out["M1_err"] = str(e)
    try:
        m2 = smf.mixedlm("err ~ pr + w0 + density", d, groups=d.net_seed).fit(reml=False)
        for v in ("pr", "w0", "density"):
            out[f"M2_beta_{v}"] = float(m2.params[v]); out[f"M2_p_{v}"] = float(m2.pvalues[v])
    except Exception as e:
        out["M2_err"] = str(e)
    try:
        m3 = smf.mixedlm("err ~ pr", d, groups=d.net_seed, re_formula="~pr").fit(reml=False)
        out["M3_beta_pr"] = float(m3.params["pr"]); out["M3_p_pr"] = float(m3.pvalues["pr"])
        out["M3_slope_var"] = float(m3.cov_re.iloc[-1, -1]) if hasattr(m3, "cov_re") else np.nan
    except Exception as e:
        out["M3_beta_pr"] = np.nan; out["M3_err"] = str(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="feature-check run directory")
    ap.add_argument("--outcome", default="novel_", choices=["novel_", "test_"],
                    help="novel_ = novel-direction (currently EXTRAPOLATION, see caveats); "
                         "test_ = in-distribution")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    src = pathlib.Path(args.run_dir)
    tbl = src / "data" / "feature_check.parquet"
    if not tbl.exists():
        raise SystemExit(f"no feature_check.parquet under {src}")
    df = pd.read_parquet(tbl)
    up = json.loads((src / "manifest.json").read_text()).get("run_id", src.name)

    run = P.new_run("AN", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(source_run=up, outcome=args.outcome),
                    tag="feature-check-models", upstream_run_ids=[up],
                    notes="M1/M2/M3 on the feature-check table; M2 is D019 screening-off")
    try:
        res = pd.DataFrame([fit_models(df, t, args.outcome) for t in FEATURES])
        res.to_parquet(run.table_path("models"))

        print(f"source run : {up}")
        print(f"outcome    : {args.outcome}*   n={res.n.iloc[0]} rows, "
              f"{res.n_seeds.iloc[0]} seeds\n")

        print("M1  err ~ pr + (1|seed)         [PR confounded with w0/density]")
        for _, r in res.iterrows():
            print(f"   {r.feature:>4}: beta_pr = {r.M1_beta_pr:+.3f}  p = {r.M1_p_pr:.4f}")

        print("\nM2  err ~ pr + w0 + density + (1|seed)   [D019 screening-off]")
        for _, r in res.iterrows():
            if "M2_beta_pr" in r and not pd.isna(r.get("M2_beta_pr", np.nan)):
                print(f"   {r.feature:>4}: pr {r.M2_beta_pr:+.3f} (p={r.M2_p_pr:.4f})   "
                      f"w0 {r.M2_beta_w0:+.3f} (p={r.M2_p_w0:.4f})   "
                      f"density {r.M2_beta_density:+.3f} (p={r.M2_p_density:.4f})")

        print("\nM3  err ~ pr + (1 + pr|seed)     [random slope: does the slope vary?]")
        for _, r in res.iterrows():
            print(f"   {r.feature:>4}: beta_pr = {r.M3_beta_pr:+.3f}  p = {r.M3_p_pr:.4f}")

        print("\nHOW TO READ:")
        print("  * H1 predicts beta_pr NEGATIVE (more dimensionality -> less error).")
        print("  * M1 vs M2 is the key contrast. If beta_pr survives M2 while w0/density")
        print("    fall away -> PR screens off structure -> supports Frank's claim H.")
        print("    If w0/density survive and pr does not -> structure does the work and PR")
        print("    is a bystander -> challenges H and undercuts D002/D016.")
        print("  * If M1 and M3 disagree, the equal-slopes assumption is wrong; trust M3.")
        print("  * net_seed and task_seed are ALIASED in this design: (1|net_seed) absorbs")
        print("    network AND environment variance together. Separating them needs a")
        print("    crossed design, not a re-analysis.")
        if args.outcome == "novel_":
            print("  * novel_ is currently EXTRAPOLATION (novel set drawn along axes training")
            print("    barely sampled), not generalization. Cross-check with --outcome test_.")

        note = ("M1/M2/M3 on " + up + "; M2 beta_pr: " +
                ", ".join(f"{r.feature}={r.get('M2_beta_pr', float('nan')):+.2f}"
                          for _, r in res.iterrows()))
        run.finalize(status="complete", n_conditions=len(df), notebook_note=note)
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
