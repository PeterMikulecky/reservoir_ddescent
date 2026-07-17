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

    # BASELINE (D030's rule, made permanent): a linear readout on the RAW INPUT.
    # If the reservoir states cannot beat this, the network is DESTROYING information, and any
    # curve we draw is a curve over a bad feature set. Always print it beside the sweep.
    from ddescent.baseline import best_nmse
    base = best_nmse(task.E_train, task.Y_train, task.E_test, task.Y_test, standardize=False)[0]

    rows = []
    for M in widths:
        # PER-M SEEDING (D063): the projections must NOT depend on how many draws came before.
        # Sequential draws from one RNG made every M's features change when the width LIST
        # changed — the peak moved 50.4 -> 25.6 at the same nominal seed. Non-reproducible.
        rng = np.random.default_rng(seed * 100_003 + M)
        Proj = rng.standard_normal((Xtr.shape[1], M)) / np.sqrt(Xtr.shape[1])
        A, B = np.tanh(Xtr @ Proj), np.tanh(Xte @ Proj)
        r = LinearReadout(alpha=0.0).fit(A, task.Y_train)    # min-norm: the DD regime
        rows.append(dict(M=M, n_train=len(task.E_train),
                         ratio=M / len(task.E_train),
                         train=nmse(task.Y_train, r.predict(A)),
                         test=min(nmse(task.Y_test, r.predict(B)), 1e6),
                         baseline_raw=base))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- (A) the gate
def _arm(pl: dict) -> dict:
    """One GA setting. **Parallelism is nested INWARD (D064):** workers go to the POPULATION,
    arms run serially.

    The previous nesting parallelised across ARMS with `n_workers=1` inside — so with 4 arms on
    6 workers, two workers idled and **wall clock was set by the SLOWEST SINGLE ARM** (~3.3 h for
    pop 60 x 100 gens). Inward nesting puts all 6 workers on one arm at a time and makes the
    total the SUM of arms, each ~6x faster.
    """
    task = T.hierarchical_environments(**pl["task_kw"])
    net = EvoNetConfig(**pl["net_kw"])
    cfg = EvolveConfig(**pl["ga_kw"])
    hist, _ = run_evolution(task, net, cfg, n_workers=pl.get("workers", 1), verbose=False)
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
    # Gate B0 is a YES/NO question — does training error move AT ALL? D060's signal
    # (0.943 -> 0.937 over 6 generations) suggests we may learn the answer in minutes.
    # **Run `quick` FIRST.** If train is still ~0.94 after 100 generations, that is the
    # important thing, learned without spending hours confirming it four ways.
    "quick":   dict(pops=(30,), gens=(100,), sigmas=(0.3,), densities=(0.5,)),      # 1 arm ~15 min
    "default": dict(pops=(30, 60), gens=(100,), sigmas=(0.2, 0.5), densities=(0.5,)),  # 4 arms
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
        r1 = task_kw["r1"]
        # Widths must start BELOW the classical optimum or the FIRST DESCENT is off the left
        # edge of the sweep (D063 — my earlier table showed only the peak and second descent,
        # and I mislabelled it as showing all three). With K=10 inputs and a rank-r1 level-1
        # map, the intrinsic dimensionality of what is learnable at level 1 is ~r1, so the
        # classical optimum may sit at M ~ r1. **H-B predicts the OPTIMUM tracks r1 while the
        # PEAK tracks n — two different quantities, in two different places.**
        widths = sorted(set([1, 2, 3, 4, 5, 8, 12, 20, 35, n - 5, n, n + 5, 80, 150, 400]))
        pc = positive_control(net_cfg, task, widths, seed=args.seed)
        pc.to_parquet(run.table_path("positive_control"))
        base = float(pc.baseline_raw.iloc[0])
        print(f"    BASELINE — linear readout on the RAW INPUT: test NMSE = {base:.3f}")
        print(f"    (the reservoir states must BEAT this or the network destroys information — D030)\n")
        print(f"{'M':>5} {'M/n':>6} {'train':>9} {'test':>10}  {'vs base':>8}")
        for _, r in pc.iterrows():
            mark = "  <- threshold" if abs(r.ratio - 1.0) < 0.11 else ""
            vs = "BEATS" if r.test < base else "worse"
            print(f"{int(r.M):>5} {r.ratio:>6.2f} {r.train:>9.3f} {r.test:>10.3f}  {vs:>8}{mark}")
        peak_i = int(pc.test.idxmax())
        opt_i = int(pc.loc[pc.M <= n // 2, "test"].idxmin())   # classical optimum, pre-peak
        print(f"\n  classical OPTIMUM (pre-peak) at M={int(pc.M[opt_i])}  "
              f"[r1={r1}: H-B predicts the optimum tracks r1]")
        print(f"  PEAK test error at M={int(pc.M[peak_i])} (M/n={pc.ratio[peak_i]:.2f})  "
              f"[classical DD predicts the peak tracks n]")
        print(f"  final test at M={int(pc.M.iloc[-1])}: {pc.test.iloc[-1]:.3f}")
        first = bool(pc.test[opt_i] < pc.test.iloc[0])          # did error FALL before rising?
        dd = bool(abs(pc.ratio[peak_i] - 1.0) < 0.5 and pc.test.iloc[-1] < pc.test[peak_i])
        print(f"  FIRST descent present:  {'YES' if first else 'NO — optimum is at the smallest M'}")
        print(f"  peak + SECOND descent:  {'YES — apparatus sane' if dd else 'NO — INVESTIGATE'}")
        if not first:
            print("    (if the optimum sits at the smallest M, the first descent is off the left")
            print("     edge — or M~r1 already exceeds what level-1 structure requires.)")
        beats = bool(pc.test.min() < base)
        print(f"  reservoir states beat the raw-input baseline: "
              f"{'YES' if beats else 'NO — the network DESTROYS information (D030)'}")
        if not beats:
            print(f"    best state-based test = {pc.test.min():.3f} vs raw-input {base:.3f}.")
            print("    The DD curve is then a curve over a BAD feature set: the peak and second")
            print("    descent are real, but the whole curve sits above 'no network at all'.")
            print("    This is Gate A's question, and it is unresolved for the evolved case.")
        if args.control:
            run.finalize(status="complete", notebook_note=f"positive control only; DD={dd}")
            return

        # ---- (A) the gate ---------------------------------------------------------
        import itertools
        g = PRESETS[args.preset]
        payloads = [dict(task_kw=task_kw, net_kw=net_kw,
                         workers=args.workers,
                         ga_kw=dict(pop_size=p, n_generations=gn, mag_sigma=s, density=dn,
                                    selection="replicator", seed=args.seed))
                    for p, gn, s, dn in itertools.product(g["pops"], g["gens"], g["sigmas"],
                                                          g["densities"])]
        print(f"\n=== (A) THE GATE: {len(payloads)} GA settings, deep in the overparameterized regime ===")
        # arms SERIAL; workers go to the population inside each arm (D064)
        est = sum(pl["ga_kw"]["pop_size"] * pl["ga_kw"]["n_generations"] for pl in payloads)
        print(f"    {est:,} total evaluations ~ {est*2/max(args.workers,1)/60:.0f} min "
              f"at ~2 s/eval on {args.workers} workers\n")
        rows = []
        for i, pl in enumerate(payloads):
            t0 = __import__("time").time()
            rows.append(_arm(pl))
            print(f"  [{i+1}/{len(payloads)}] pop={pl['ga_kw']['pop_size']} "
                  f"gens={pl['ga_kw']['n_generations']} sigma={pl['ga_kw']['mag_sigma']} "
                  f"-> best_train={rows[-1]['train_best']:.3f}  ({__import__('time').time()-t0:.0f}s)")
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
