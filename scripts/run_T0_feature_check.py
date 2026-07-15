#!/usr/bin/env python3
r"""
T0 - feature check : which readout feature should fitness use -- and does PR predict
generalization at all?

THIS IS THE FIRST TIME THIS PROJECT MEASURES GENERALIZATION (D015).

Motivation. The N=1000 readout check found PR(X_var) sits at 50-92 across every condition
and stays roughly FLAT, while PR(X_mean) collapses 53 -> 8. At w0=3, p=0.4: PR_mean=23.1
vs PR_var=91.8. Reading: under strong coupling the representation may not collapse -- it may
RELOCATE from the mean into the fluctuations. If so, and if fitness reads X_mean, E9 would
select on the low-dimensional shadow of a high-dimensional representation, and Frank's
mechanism would be invisible to us by construction.

But PR cannot tell structure from noise: high-dimensional NOISE also has high PR. So the
decisive test is not another dimensionality measurement -- it is generalization.

Two questions, one run:

  Q1 (feature choice). Fit min-norm readouts on X_mean / X_inst / X_var; compare error on
      novel environments.
        * X_var predicts BEST            -> it is a representation; fitness feature should
                                            change (a D026-scale decision).
        * X_var predicts WORSE despite     -> its PR is measuring noise, AND **PR is not
          the highest PR                     tracking usable dimensionality** -- which
                                            undercuts D002/D016 at the root.
      Either outcome is major.

  Q2 (H1, first test). Across conditions, does PR predict novel-environment error? This is
      the load-bearing claim of the whole project and has never been measured.

Usage (Windows cmd, venv active):
  python scripts\run_T0_feature_check.py --preset coarse    # N=300
  python scripts\run_T0_feature_check.py --preset fine      # N=1000
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse, itertools
import numpy as np
import pandas as pd

from ddescent import provenance as P
from ddescent.connectivity import ConnectivityConfig, make_recurrent_weights, make_input_weights
from ddescent.reservoir import ReservoirConfig, LIFReservoir
from ddescent import readout as ro
from ddescent import tasks as T
from ddescent.measures import nmse, participation_ratio

FEATURES = ("X_mean", "X_inst", "X_var")


def _cell(pl: dict) -> dict:
    """One (w0, density) condition: three features x (train/test/novel). Picklable."""
    # net_seed and task_seed are SEPARATE: otherwise network variance and environment
    # variance are confounded and a wobble across replicates cannot be attributed.
    task = T.anisotropic_regression(K=pl["K"], n_train=pl["n_train"], n_test=pl["n_test"],
                                    n_high=4, seed=pl["task_seed"])
    W = make_recurrent_weights(ConnectivityConfig(
        N=pl["N"], density=pl["density"], w0=pl["w0"], spectral_radius=None,
        seed=pl["net_seed"]))
    Win = make_input_weights(pl["N"], pl["K"], seed=pl["net_seed"] + 1000)
    res = LIFReservoir(W, Win, ReservoirConfig(
        N=pl["N"], bias=pl["bias"], input_gain=pl["ig"], seed=pl["net_seed"] + 2000))

    S_tr = res.run_stationary(task.U_train, sample_ms=pl["sample_ms"])
    S_te = res.run_stationary(task.U_test, sample_ms=pl["sample_ms"])
    S_nv = res.run_stationary(task.U_novel, sample_ms=pl["sample_ms"])

    row = dict(w0=pl["w0"], density=pl["density"], N=pl["N"], net_seed=pl["net_seed"],
               task_seed=pl["task_seed"], n_train=pl["n_train"], temporal_cv=S_tr["temporal_cv"])
    for f in FEATURES:
        Xtr, Xte, Xnv = S_tr[f], S_te[f], S_nv[f]
        # Standardize per feature so the comparison is not a scale artifact. The sd FLOOR
        # is essential: X_var holds variances (tiny), and dividing by a near-zero train sd
        # amplified near-silent neurons into numerical infinities (novel NMSE ~1e33).
        mu = Xtr.mean(0, keepdims=True)
        sd = Xtr.std(0, keepdims=True)
        sd = np.maximum(sd, 1e-3 * (sd.mean() + 1e-12))     # floor relative to typical scale
        Xtr_, Xte_, Xnv_ = (Xtr - mu) / sd, (Xte - mu) / sd, (Xnv - mu) / sd
        # Small ridge, not pure min-norm. Min-norm interpolation extrapolates without bound
        # onto the novel-direction test set (drawn along LOW-variance axes by construction),
        # which produced meaningless 1e12+ errors. alpha is small enough to stay near the
        # "biological" unregularized regime while remaining numerically defined.
        r = ro.LinearReadout(alpha=pl["alpha"]).fit(Xtr_, task.y_train)
        tag = f[2:]
        row[f"pr_{tag}"] = participation_ratio(Xtr)
        row[f"active_{tag}"] = float((Xtr > 1e-6).mean())
        row[f"train_{tag}"] = nmse(task.y_train, r.predict(Xtr_))
        row[f"test_{tag}"] = nmse(task.y_test, r.predict(Xte_))
        row[f"novel_{tag}"] = min(nmse(task.y_novel, r.predict(Xnv_)), 1e6)  # cap runaway extrapolation
        row[f"wnorm_{tag}"] = r.weight_norm()
    return row


PRESETS = {
    "tiny":   dict(N=120, K=10, n_train=40, n_test=40, sample_ms=10.0,
                   w0s=(0.5, 3.0), densities=(0.01, 0.4), tag="feature-tiny"),
    "quick":  dict(N=200, K=20, n_train=80, n_test=80, sample_ms=6.0,
                   w0s=(0.5, 3.0), densities=(0.01, 0.4), tag="feature-quick"),
    "coarse": dict(N=300, K=20, n_train=150, n_test=150, sample_ms=5.0,
                   w0s=(0.5, 1.5, 3.0), densities=(0.01, 0.05, 0.15, 0.4), tag="feature-N300"),
    "fine":   dict(N=1000, K=20, n_train=150, n_test=150, sample_ms=5.0,
                   w0s=(0.5, 1.0, 2.0, 3.0), densities=(0.01, 0.05, 0.15, 0.4),
                   tag="feature-N1000"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS), default="coarse")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--bias", type=float, default=0.4)
    ap.add_argument("--input-gain", type=float, default=0.1)
    ap.add_argument("--seeds", type=int, default=10,
                    help="number of replicate seeds. Each seed yields ONE corr(PR, err) "
                         "estimate, so 2-3 cannot distinguish a real effect from noise. "
                         "10+ for a first pass; pool with seed as a random effect.")
    ap.add_argument("--alpha", type=float, default=1.0,
                    help="ridge strength; small keeps us near the min-norm regime while "
                         "staying numerically defined on novel-direction inputs")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    pre = PRESETS[args.preset]
    cells = list(itertools.product(pre["w0s"], pre["densities"], range(args.seeds)))
    payloads = [dict(w0=w, density=d, net_seed=s_, task_seed=s_ + 500,
                     bias=args.bias, ig=args.input_gain, N=pre["N"], K=pre["K"],
                     n_train=pre["n_train"], n_test=pre["n_test"],
                     sample_ms=pre["sample_ms"], alpha=args.alpha) for (w, d, s_) in cells]

    cfg = dict(preset=args.preset, bias=args.bias, input_gain=args.input_gain,
               **{k: v for k, v in pre.items() if k != "tag"})
    run = P.new_run("T0", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=cfg, tag=pre["tag"], seeds=list(range(args.seeds)),
                    notes="FIRST generalization measurement (D015). Q1 feature choice; Q2 H1 first test.")
    print(f"run: {run.run_id}")
    print(f"{len(cells)} runs = {len(pre['w0s'])*len(pre['densities'])} conditions x "
          f"{args.seeds} seeds, N={pre['N']}, n_train={pre['n_train']}\n")
    try:
        rows = []
        if args.workers <= 1:
            rows = [_cell(pl) for pl in payloads]
        else:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(args.workers) as pool:
                for i, r in enumerate(pool.imap_unordered(_cell, payloads)):
                    rows.append(r); print(f"  [{i+1}/{len(payloads)}]")
        df = pd.DataFrame(rows).sort_values(["w0", "density"])
        df.to_parquet(run.table_path("feature_check"))

        print("\n=== Q1: which feature generalizes? (NMSE on novel environments) ===")
        print(f'{"w0":>5} {"dens":>6} | {"PR_mean":>7} {"PR_var":>7} | '
              f'{"novel_mean":>10} {"novel_inst":>10} {"novel_var":>9} | best')
        for _, r in df.iterrows():
            errs = {f: r[f"novel_{f[2:]}"] for f in FEATURES}
            best = min(errs, key=errs.get)[2:]
            print(f'{r.w0:>5} {r.density:>6} | {r.pr_mean:>7.1f} {r.pr_var:>7.1f} | '
                  f'{r.novel_mean:>10.3f} {r.novel_inst:>10.3f} {r.novel_var:>9.3f} | {best}')

        wins = {f[2:]: int(sum(df[f"novel_{f[2:]}"] == df[[f"novel_{g[2:]}" for g in FEATURES]].min(axis=1))) for f in FEATURES}
        print(f"\nwins on novel error: {wins}")
        med = {f[2:]: float(df[f"novel_{f[2:]}"].median()) for f in FEATURES}
        print(f"median novel NMSE:   " + "  ".join(f"{k}={v:.3f}" for k, v in med.items()))

        print("\n=== Q2: does PR predict generalization? (H1, first test) ===")
        print("per-seed corr(PR, err), mean +/- sd across seeds -- each seed is ONE estimate:")
        for f in FEATURES:
            tag = f[2:]
            rn, rt = [], []
            for sd_, sub in df.groupby("net_seed"):
                if len(sub) > 2:
                    rn.append(np.corrcoef(sub[f"pr_{tag}"], sub[f"novel_{tag}"])[0, 1])
                    rt.append(np.corrcoef(sub[f"pr_{tag}"], sub[f"test_{tag}"])[0, 1])
            if rn:
                print(f"  {tag:>4}: novel r = {np.mean(rn):+.3f} +/- {np.std(rn):.3f}   "
                      f"test r = {np.mean(rt):+.3f} +/- {np.std(rt):.3f}   (n_seeds={len(rn)})")
        print("  (H1 predicts NEGATIVE corr: more dimensionality -> less error)")
        # pooled: seed as a random effect -- the statistically right way (analysis.py machinery)
        try:
            import statsmodels.formula.api as smf
            print("\npooled mixed model  novel_err ~ PR + (1|net_seed):")
            for f in FEATURES:
                tag = f[2:]
                d = df[[f"pr_{tag}", f"novel_{tag}", "net_seed"]].dropna()
                d.columns = ["pr", "err", "net_seed"]
                d["pr"] = (d.pr - d.pr.mean()) / (d.pr.std() + 1e-9)
                m = smf.mixedlm("err ~ pr", d, groups=d.net_seed).fit(reml=False)
                print(f"  {tag:>4}: beta_PR = {m.params['pr']:+.3f}  p = {m.pvalues['pr']:.4f}")
        except Exception as e:
            print(f"  (pooled model unavailable: {e})")

        best_overall = min(med, key=med.get)
        print("\nVERDICT (read with the caveats below):")
        if best_overall == "var":
            print("  X_var generalizes BEST -> its high PR reflects a real representation.")
            print("  The fitness feature should change from X_mean to X_var (D026-scale decision).")
        elif med["var"] > med["mean"] and float(df.pr_var.median()) > float(df.pr_mean.median()):
            print("  X_var has the HIGHEST PR but generalizes WORSE -> its PR is measuring")
            print("  NOISE, and **PR is not tracking usable dimensionality**. This undercuts")
            print("  D002/D016 at the root: PR may be the wrong operationalization of Frank's")
            print("  'dimensionality'. Consider kernel rank / edof / IPC instead.")
        else:
            print(f"  '{best_overall}' generalizes best; no clean X_var story. Inspect the table.")

        # Caveats the numbers cannot speak for themselves about.
        print("\nCAVEATS:")
        n_seeds = int(df.net_seed.nunique())
        n_cond = int(len(df) / max(n_seeds, 1))
        print(f"  * {n_cond} conditions x {n_seeds} seeds. Each seed gives ONE corr estimate;")
        if n_seeds < 10:
            print(f"    {n_seeds} is too few to separate a real effect from noise -- use >=10.")
        print("    Trust the pooled mixed model over any single-seed correlation.")
        if float(df[[f"novel_{f[2:]}" for f in FEATURES]].min(axis=1).median()) > 1.0:
            print("  * EVERY novel NMSE > 1 -> nothing beats predicting the mean. The novel set")
            print("    is drawn along axes training barely sampled: this is EXTRAPOLATION, not")
            print("    generalization. Prefer test_err until the task is redesigned to be")
            print("    novel-but-related rather than novel-and-orthogonal.")
        print("  * alpha>0 (ridge) was required for numerical stability; this is NOT the pure")
        print("    min-norm 'biological' regime of E4/D-decisions. Sweep alpha before trusting.")

        note = (f"FIRST generalization measurement. median novel NMSE: " +
                ", ".join(f"{k}={v:.3f}" for k, v in med.items()) + f"; best={best_overall}")
        run.finalize(status="complete", n_conditions=len(df), notebook_note=note)
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
