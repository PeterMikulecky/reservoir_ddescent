#!/usr/bin/env python3
r"""
T0 - readout check : is the trailing-window average MANUFACTURING our headline effect?

The standing check mandated by D026. Our headline finding is "PR falls as density/coupling
rise". But the network never settles (PROTOCOLS.md), so `X_mean` is a time-average over an
attractor -- and averaging destroys variance, with MORE destroyed at stronger coupling.
That mechanism alone could produce the finding with none of it being a property of the
representation.

This script computes PR three ways from the SAME runs:
    PR(X_mean) : trailing-window mean      (current readout)
    PR(X_inst) : one instantaneous sample  (no averaging -- the control)
    PR(X_var)  : within-window variance    (the discarded dynamics as a feature)

Read it like this:
  * PR(X_mean) ~ PR(X_inst), and BOTH fall with density  -> averaging is innocent; the
    effect is a property of the representation. Proceed.
  * PR(X_inst) does NOT fall (or falls far less)          -> the window mean is
    manufacturing the effect. Our headline finding, D014's evidence, and the T0 operating
    point all need revisiting.

Usage (Windows cmd, venv active):
  python scripts\run_T0_readout_check.py --preset coarse    # N=300, fast
  python scripts\run_T0_readout_check.py --preset fine      # N=1000, production
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

U_SEED = 12345


def _cell(pl: dict) -> dict:
    """One (w0, density) condition, three readouts. Top-level/picklable for spawn."""
    U = np.random.default_rng(U_SEED).standard_normal((pl["n_probe"], pl["K"]))
    W = make_recurrent_weights(ConnectivityConfig(
        N=pl["N"], density=pl["density"], w0=pl["w0"], spectral_radius=None, seed=pl["seed"]))
    Win = make_input_weights(pl["N"], pl["K"], seed=pl["seed"] + 1)
    res = LIFReservoir(W, Win, ReservoirConfig(
        N=pl["N"], bias=pl["bias"], input_gain=pl["ig"], seed=pl["seed"] + 2))
    S = res.run_stationary(U, sample_ms=pl["sample_ms"])

    row = dict(w0=pl["w0"], density=pl["density"], bias=pl["bias"], input_gain=pl["ig"],
               N=pl["N"], temporal_cv=S["temporal_cv"], attractor_pr=S["attractor_pr"],
               n_window_samples=S["n_window_samples"])
    for name in ("X_mean", "X_inst", "X_var"):
        b = MET.full_battery(S[name])
        sp = b.pop("spectrum")
        row[f"pr_{name[2:]}"] = b["pr"]
        row[f"edof_{name[2:]}"] = b["edof_k0.01"]
        row[f"active_{name[2:]}"] = b["active_frac"]
        row[f"spectrum_{name[2:]}"] = sp.tolist()
    return row


PRESETS = {
    "coarse": dict(N=300, K=20, n_probe=100, sample_ms=5.0,
                   w0s=(0.5, 1.5, 3.0), densities=(0.02, 0.1, 0.4), tag="readout-check-N300"),
    "fine":   dict(N=1000, K=20, n_probe=150, sample_ms=5.0,
                   w0s=(0.5, 1.0, 2.0, 3.0), densities=(0.01, 0.05, 0.15, 0.4),
                   tag="readout-check-N1000"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS), default="coarse")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--bias", type=float, default=0.4)      # from the T0 fine sweep
    ap.add_argument("--input-gain", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    pre = PRESETS[args.preset]
    cells = list(itertools.product(pre["w0s"], pre["densities"]))
    payloads = [dict(w0=w, density=d, bias=args.bias, ig=args.input_gain,
                     N=pre["N"], K=pre["K"], n_probe=pre["n_probe"],
                     sample_ms=pre["sample_ms"], seed=args.seed) for (w, d) in cells]

    cfg = dict(preset=args.preset, bias=args.bias, input_gain=args.input_gain,
               **{k: v for k, v in pre.items() if k != "tag"})
    run = P.new_run("T0", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=cfg, tag=pre["tag"], seeds=[args.seed],
                    notes="D026 standing check: PR via window-mean vs instantaneous vs variance")
    print(f"run: {run.run_id}")
    print(f"{len(payloads)} conditions at bias={args.bias}, input_gain={args.input_gain}\n")
    try:
        rows = []
        if args.workers <= 1:
            rows = [_cell(pl) for pl in payloads]
        else:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(args.workers) as pool:
                for i, r in enumerate(pool.imap_unordered(_cell, payloads)):
                    rows.append(r)
                    print(f"  [{i+1}/{len(payloads)}]")
        df = pd.DataFrame(rows).sort_values(["w0", "density"])
        df.to_parquet(run.table_path("readout_check"))

        print(f"\nwindow samples per pattern: {df.n_window_samples.iloc[0]}")
        print("\nPR by readout (does the effect survive without averaging?)")
        print(f'{"w0":>5} {"dens":>6} {"PR_mean":>8} {"PR_inst":>8} {"PR_var":>8} {"temp_cv":>8}')
        for _, r in df.iterrows():
            print(f'{r.w0:>5} {r.density:>6} {r.pr_mean:>8.1f} {r.pr_inst:>8.1f} '
                  f'{r.pr_var:>8.1f} {r.temporal_cv:>8.3f}')

        # the verdict: does PR fall with density under BOTH readouts?
        print("\nrelative PR span across density (per w0):")
        verdicts = []
        for w0, sub in df.groupby("w0"):
            sub = sub.sort_values("density")
            def span(col):
                v = sub[col].values
                return 100 * (v.max() - v.min()) / (v.mean() + 1e-9)
            def falls(col):
                v = sub[col].values
                return v[0] > v[-1]
            sm, si = span("pr_mean"), span("pr_inst")
            print(f"  w0={w0}: mean {sm:5.0f}% (falls={falls('pr_mean')})  "
                  f"inst {si:5.0f}% (falls={falls('pr_inst')})")
            verdicts.append((falls("pr_mean"), falls("pr_inst"), sm, si))

        agree = all(a == b for a, b, _, _ in verdicts)
        ratio = np.mean([si / (sm + 1e-9) for _, _, sm, si in verdicts])
        print("\nVERDICT:")
        if agree and ratio > 0.5:
            print("  PR(X_inst) tracks PR(X_mean) -> averaging is INNOCENT.")
            print("  The density/coupling effect is a property of the representation. Proceed.")
        elif not agree:
            print("  !! PR(X_inst) and PR(X_mean) DISAGREE in direction.")
            print("  The window mean is manufacturing the effect. D014's evidence, the")
            print("  headline finding, and the T0 operating point all need revisiting.")
        else:
            print(f"  !! PR(X_inst) span is only {100*ratio:.0f}% of PR(X_mean) span.")
            print("  Averaging is inflating the effect. Interpret the headline finding with care.")

        note = (f"readout check @ bias={args.bias} gain={args.input_gain}: "
                f"inst/mean span ratio {ratio:.2f}, direction agree={agree}")
        run.finalize(status="complete", n_conditions=len(df), notebook_note=note)
    except Exception as e:
        run.finalize(status="failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
