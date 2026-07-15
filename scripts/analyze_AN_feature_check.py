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

Both outcomes (test_ = in-distribution, novel_ = novel-direction) are analyzed in ONE run:
they are one analysis, not two. The run directory is auto-discovered if not given.

Usage:
  python scripts\analyze_AN_feature_check.py                       # newest feature-check run
  python scripts\analyze_AN_feature_check.py --run-dir runs\T0_tune_operating_point\<run_id>
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse, json, warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# statsmodels emits a convergence/singularity warning per fit; with 3 features x 2 outcomes
# x 3 models that is ~18 stack traces which bury the results. We surface conditioning
# problems explicitly in the output instead (see `converged` column).
warnings.filterwarnings("ignore")

from ddescent import provenance as P

FEATURES = ("mean", "inst", "var")


def fit_models(df: pd.DataFrame, tag: str, outcome_prefix: str) -> dict:
    """Fit M1/M2/M3 for one feature channel."""
    col = f"{outcome_prefix}{tag}"
    d = df[[f"pr_{tag}", col, "w0", "density", "net_seed"]].dropna().copy()
    d.columns = ["pr", "err", "w0", "density", "net_seed"]
    # LOG-TRANSFORM the outcome. NMSE here spans ~5 orders of magnitude (1.2 to 180,000);
    # a linear model on that fits the handful of catastrophic runs, not the bulk, and
    # statsmodels reports singular covariance / non-PD Hessians / convergence failures.
    # log makes the model multiplicative and outlier-resistant. Coefficients are then in
    # log-NMSE units: beta=-0.3 means ~26% lower error per SD of PR.
    d["err"] = np.log(np.clip(d["err"].values, 1e-6, None))
    for c in ("pr", "w0", "density"):
        sd_ = d[c].std()
        d[c] = (d[c] - d[c].mean()) / (sd_ if sd_ > 0 else 1.0)

    out = {"feature": tag, "n": len(d), "n_seeds": int(d.net_seed.nunique())}
    try:
        m1 = smf.mixedlm("err ~ pr", d, groups=d.net_seed).fit(reml=False)
        out["M1_beta_pr"] = float(m1.params["pr"]); out["M1_p_pr"] = float(m1.pvalues["pr"])
        out["M1_converged"] = bool(getattr(m1, "converged", True))
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


def _find_latest(runs_root: pathlib.Path) -> pathlib.Path | None:
    """Newest run containing a feature_check.parquet. Saves typing a long run ID."""
    hits = sorted(runs_root.glob("*/*/data/feature_check.parquet"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0].parent.parent if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=None,
                    help="feature-check run directory. Omit to auto-use the most recent one.")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    # both outcomes are analyzed in ONE run -- they are one analysis, not two
    outcomes = ["test_", "novel_"]

    if args.run_dir:
        src = pathlib.Path(args.run_dir)
    else:
        import os
        rr = pathlib.Path(args.runs_root or os.environ.get("DDESCENT_RUNS_ROOT") or "runs")
        src = _find_latest(rr)
        if src is None:
            raise SystemExit(f"no feature-check run found under {rr}; pass --run-dir")
        print(f"(auto-selected most recent feature-check run)")
    tbl = src / "data" / "feature_check.parquet"
    if not tbl.exists():
        raise SystemExit(f"no feature_check.parquet under {src}")
    df = pd.read_parquet(tbl)
    up = json.loads((src / "manifest.json").read_text()).get("run_id", src.name)

    run = P.new_run("AN", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(source_run=up, outcomes=outcomes),
                    tag="feature-check-models", upstream_run_ids=[up],
                    notes="M1/M2/M3 x {test_, novel_} on the feature-check table; M2 is D019 screening-off")
    try:
        frames = []
        for oc in outcomes:
            r_ = pd.DataFrame([fit_models(df, t, oc) for t in FEATURES])
            r_.insert(0, "outcome", oc.rstrip("_"))
            frames.append(r_)
        res = pd.concat(frames, ignore_index=True)
        res.to_parquet(run.table_path("models"))

        print(f"source run : {up}")
        print(f"rows={int(res.n.iloc[0])}, seeds={int(res.n_seeds.iloc[0])}, "
              f"outcomes={[o.rstrip('_') for o in outcomes]}")

        for oc in outcomes:
            sub = res[res.outcome == oc.rstrip("_")]
            print(f"\n{'='*66}\nOUTCOME: {oc.rstrip('_')}"
                  + ("   [in-distribution -- the trustworthy one for now]" if oc == "test_"
                     else "   [novel-direction -- currently EXTRAPOLATION, see caveats]"))
            print("M1  err ~ pr + (1|seed)         [PR confounded with w0/density]")
            for _, r in sub.iterrows():
                flag = "" if r.get("M1_converged", True) else "  [DID NOT CONVERGE]"
                print(f"   {r.feature:>4}: beta_pr = {r.M1_beta_pr:+.3f}  p = {r.M1_p_pr:.4f}{flag}")
            print("M2  err ~ pr + w0 + density + (1|seed)   [D019 screening-off -- THE KEY ONE]")
            for _, r in sub.iterrows():
                if not pd.isna(r.get("M2_beta_pr", np.nan)):
                    print(f"   {r.feature:>4}: pr {r.M2_beta_pr:+.3f} (p={r.M2_p_pr:.4f})   "
                          f"w0 {r.M2_beta_w0:+.3f} (p={r.M2_p_w0:.4f})   "
                          f"density {r.M2_beta_density:+.3f} (p={r.M2_p_density:.4f})")
            print("M3  err ~ pr + (1 + pr|seed)     [random slope]")
            for _, r in sub.iterrows():
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
        print("  * novel_ is currently EXTRAPOLATION (novel set drawn along axes training")
        print("    barely sampled). Weight the test_ block more heavily until the task is fixed.")

        note = ("M1/M2/M3 x {test,novel} on " + up + "; M2 beta_pr (test): " +
                ", ".join(f"{r.feature}={r.get('M2_beta_pr', float('nan')):+.2f}"
                          for _, r in res[res.outcome == "test"].iterrows()))
        run.finalize(status="complete", n_conditions=len(df), notebook_note=note)
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
