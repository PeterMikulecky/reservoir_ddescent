#!/usr/bin/env python3
r"""
GATE B0 — can the GA reach INTERPOLATION? **The binding risk (D049/D060).**

Classical double descent's peak sits at the **interpolation threshold** — where the model can
*just barely* fit the training data exactly. That presupposes **the optimizer REACHES
interpolation**:
  * least-squares readout: **guaranteed** whenever M >= n (a solved linear system)
  * SGD on deep nets: **achieved** — which is *why* there is a threshold to peak at
  * **a GA on a nonlinear spiking network: UNKNOWN**

**If training error plateaus above zero at every |W|, there is NO threshold, hence NO peak, by
construction** — and we would misread a design failure as a finding about biology.
*(Nakkiran defines **effective model complexity** via the training procedure precisely because
parameter counting fails for nonlinear models.)*

First signal (D060): best_train 0.943 -> 0.937 over 6 generations at pop 12. Far too small to
conclude — but the reason this gate exists.

TWO PARTS
---------
**(A) THE GATE.** Evolve at HIGH |W| (deep in the overparameterized regime) across GA settings.
    pop_size, n_generations and mag_sigma are **LOAD-BEARING, not tuning** (D060).
    Verdict = does best_train approach 0?

**(B) THE POSITIVE CONTROL (PJM).** Bolt a linear readout onto a *random* network and sweep its
    width. That is a **random-features model**, so textbook double descent is *expected*
    (peak at M ~ n). **If it does NOT appear, the apparatus is broken — not the hypothesis.**
    *This is D052's graded logic: it is the bookend where the phenomenon is guaranteed.*

Usage:
  python scripts\run_GateB0_interpolation.py --control      # (B) only: is the apparatus sane?
  python scripts\run_GateB0_interpolation.py                # (A) the gate
  python scripts\run_GateB0_interpolation.py --preset hard  # bigger pop / longer / wider sigma
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse
import numpy as np
import pandas as pd

from ddescent import provenance as P
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.evolve import EvolveConfig, run_evolution
from ddescent import tasks as T
from ddescent.readout import LinearReadout
from ddescent.measures import nmse

INTERP_TOL = 0.05          # best_train below this counts as "interpolating"


# ---------------------------------------------------------------- (B) positive control
def positive_control(net_cfg: EvoNetConfig, task, widths, seed=0) -> pd.DataFrame:
    """Random network + linear readout of varying width = a RANDOM-FEATURES model.
    Textbook double descent expected, peak at M ~ n_train. If absent -> apparatus broken."""
    g = random_genome(net_cfg, 0.3, w0=0.6, seed=seed)
    net = EvoNet(g, net_cfg)
    Xtr = net.behave(task.E_train)["state"]        # (n, N) internal states = the features
    Xte = net.behave(task.E_test)["state"]
    rng = np.random.default_rng(seed)
    rows = []
    for M in widths:
        # M random features (random projections of the state — lets M exceed N)
        Proj = rng.standard_normal((Xtr.shape[1], M)) / np.sqrt(Xtr.shape[1])
        A, B = np.tanh(Xtr @ Proj), np.tanh(Xte @ Proj)
        r = LinearReadout(alpha=0.0).fit(A, task.Y_train)    # min-norm: the DD regime
        rows.append(dict(M=M, n_train=len(task.E_train),
                         ratio=M / len(task.E_train),
                         train=nmse(task.Y_train, r.predict(A)),
                         test=min(nmse(task.Y_test, r.predict(B)), 1e6)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- (A) the gate
def _arm(pl: dict) -> dict:
    task = T.hierarchical_environments(**pl["task_kw"])
    net = EvoNetConfig(**pl["net_kw"])
    cfg = EvolveConfig(**pl["ga_kw"])
    hist, _ = run_evolution(task, net, cfg, n_workers=1, verbose=False)
    h0, hN = hist[0], hist[-1]
    best = min(h["best_train"] for h in hist)
    return dict(pop_size=cfg.pop_size, n_generations=cfg.n_generations,
                mag_sigma=cfg.mag_sigma, density=cfg.density,
                n_params=hN["best_params"], constraints=task.n_constraints(),
                ratio=hN["best_params"] / task.n_constraints(),
                train_start=h0["best_train"], train_end=hN["best_train"], train_best=best,
                test_end=hN["best_test"],
                memoryless_floor=task.headroom()["memoryless_floor"],
                interpolates=bool(best < INTERP_TOL))


PRESETS = {
    "default": dict(pops=(30, 60), gens=(100,), sigmas=(0.2, 0.5), densities=(0.5,)),
    "hard":    dict(pops=(60, 120), gens=(300,), sigmas=(0.1, 0.3, 0.8), densities=(0.5, 0.9)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS), default="default")
    ap.add_argument("--control", action="store_true", help="run only the positive control (B)")
    ap.add_argument("--N", type=int, default=50)
    ap.add_argument("--d", type=int, default=5)
    ap.add_argument("--n-env", type=int, default=50)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    task_kw = dict(K=10, d=args.d, r1=3, n_contexts=4, n_train=args.n_env,
                   n_test=args.n_env, context_dwell=10, seed=args.seed)
    net_kw = dict(N=args.N, n_in=10, d=args.d, bias=0.6, input_gain=1.0, noise_sigma=1.0)

    run = P.new_run("T0", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(preset=args.preset, control_only=args.control,
                                task=task_kw, net=net_kw),
                    tag="gateB0-interpolation", seeds=[args.seed],
                    notes="Gate B0: can the GA reach interpolation? (D049) + bolt-on positive control")
    print(f"run: {run.run_id}")
    try:
        task = T.hierarchical_environments(**task_kw)
        net_cfg = EvoNetConfig(**net_kw)
        print(f"task: constraints = {task.n_constraints()} (n_env x d)")

        # ---- (B) positive control -------------------------------------------------
        print("\n=== (B) POSITIVE CONTROL: random network + linear readout (random features) ===")
        print("    textbook double descent EXPECTED, peak at M ~ n_train. If absent -> apparatus broken.")
        n = len(task.E_train)
        widths = [5, 10, 20, 35, n - 5, n, n + 5, 80, 150, 400]
        pc = positive_control(net_cfg, task, widths, seed=args.seed)
        pc.to_parquet(run.table_path("positive_control"))
        print(f"{'M':>5} {'M/n':>6} {'train':>9} {'test':>10}")
        for _, r in pc.iterrows():
            mark = "  <- threshold" if abs(r.ratio - 1.0) < 0.11 else ""
            print(f"{int(r.M):>5} {r.ratio:>6.2f} {r.train:>9.3f} {r.test:>10.3f}{mark}")
        peak_i = int(pc.test.idxmax())
        print(f"\n  peak test error at M={int(pc.M[peak_i])} (M/n={pc.ratio[peak_i]:.2f}); "
              f"final test at M={int(pc.M.iloc[-1])}: {pc.test.iloc[-1]:.3f}")
        dd = bool(abs(pc.ratio[peak_i] - 1.0) < 0.5 and pc.test.iloc[-1] < pc.test[peak_i])
        print(f"  double descent present: {'YES — apparatus sane' if dd else 'NO — INVESTIGATE'}")
        if args.control:
            run.finalize(status="complete", notebook_note=f"positive control only; DD={dd}")
            return

        # ---- (A) the gate ---------------------------------------------------------
        import itertools
        g = PRESETS[args.preset]
        payloads = [dict(task_kw=task_kw, net_kw=net_kw,
                         ga_kw=dict(pop_size=p, n_generations=gn, mag_sigma=s, density=dn,
                                    selection="replicator", seed=args.seed))
                    for p, gn, s, dn in itertools.product(g["pops"], g["gens"], g["sigmas"],
                                                          g["densities"])]
        print(f"\n=== (A) THE GATE: {len(payloads)} GA settings, deep in the overparameterized regime ===")
        rows = []
        if args.workers <= 1:
            rows = [_arm(pl) for pl in payloads]
        else:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(args.workers) as pool:
                for i, r in enumerate(pool.imap_unordered(_arm, payloads)):
                    rows.append(r); print(f"  [{i+1}/{len(payloads)}]")
        df = pd.DataFrame(rows)
        df.to_parquet(run.table_path("gateB0"))

        print(f"\n{'pop':>5} {'gens':>5} {'sigma':>6} {'|W|':>6} {'|W|/n':>6} | "
              f"{'train_0':>8} {'train_N':>8} {'best':>7} | interp?")
        for _, r in df.iterrows():
            print(f"{int(r.pop_size):>5} {int(r.n_generations):>5} {r.mag_sigma:>6} "
                  f"{int(r.n_params):>6} {r.ratio:>6.2f} | {r.train_start:>8.3f} "
                  f"{r.train_end:>8.3f} {r.train_best:>7.3f} | {'YES' if r.interpolates else '-'}")

        n_ok = int(df.interpolates.sum())
        print(f"\n=== VERDICT ===")
        print(f"interpolating settings: {n_ok}/{len(df)}  (best_train < {INTERP_TOL})")
        print(f"best training error achieved anywhere: {df.train_best.min():.3f}")
        print(f"memoryless floor for reference:        {df.memoryless_floor.iloc[0]:.3f}")
        if n_ok == 0:
            print("  !! THE GA NEVER REACHES INTERPOLATION.")
            print("     -> no interpolation threshold -> NO PEAK, by construction.")
            print("     -> Do NOT interpret this as 'double descent is absent from spiking")
            print("        substrates'. It is a DESIGN failure until ruled out: try --preset hard,")
            print("        larger populations, an evolution strategy (CMA-ES), or fewer")
            print("        constraints (smaller n_env or d).")
        else:
            print("  OK: the GA reaches interpolation -> a threshold exists -> Gate B is live.")
        run.finalize(status="complete", n_conditions=len(df),
                     notebook_note=(f"GateB0: {n_ok}/{len(df)} interpolate; best_train="
                                    f"{df.train_best.min():.3f}; control DD={dd}"))
    except Exception as e:
        run.finalize(status="failed", error=str(e)); raise


if __name__ == "__main__":
    main()
