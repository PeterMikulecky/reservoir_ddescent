#!/usr/bin/env python3
r"""
GATE C — can the network REACH the fluctuation-driven balanced regime?

**The prerequisite everything downstream depends on (D039/D047).**

Holt & Koch (1997): shunting inhibition is **subtractive** on firing rates. Chance, Abbott &
Reyes (2002); Prescott & De Koninck (2003): **divisive gain modulation REQUIRES synaptic
noise** — tonic conductance changes are merely subtractive; **fluctuation-based** changes
modulate gain divisively. So:

    tonic regime  -> inhibition subtractive -> NO gain control -> NO regulation -> (H-D) NO second descent
    balanced      -> fluctuation-driven     -> divisive gain available -> regulation CAN emerge

**If no reachable balanced regime exists, H-D has no treatment arm and gain-control regulation
does not exist in the model at all.** That is not a tuning detail; it is a design failure.

OPERATIONAL DEFINITION (the standard one):
  * **mean-driven**:        mean V sits ABOVE threshold -> regular firing -> CV_ISI << 1
  * **fluctuation-driven**: mean V sits BELOW threshold -> spikes caused by fluctuations
                            crossing it -> CV_ISI ~ 1 (Poisson-like)

MEASURED PER CONDITION:
  cv_isi        : coefficient of variation of interspike intervals. **CV ~ 1 = the target.**
  v_mean_sub    : (v_thresh - mean V) / v_thresh. >0 = subthreshold mean = fluctuation-driven.
  v_std         : membrane fluctuation size. Must be non-trivial or nothing crosses.
  rate          : spikes/sec. Must be alive (not silent, not saturated).
  ei_current    : |mean E current| / |mean I current|. ~1 = balanced.

Usage:
  python scripts\run_GateC_regime.py                 # default sweep
  python scripts\run_GateC_regime.py --preset wide   # wider search if nothing lands
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse, itertools
import numpy as np
import brian2 as b2
from brian2 import ms, second

from ddescent import provenance as P
from ddescent.evonet import EvoNetConfig, random_genome
from ddescent import tasks as T

CV_TARGET_LO = 0.6          # CV_ISI above this counts as fluctuation-driven-ish
RATE_LO, RATE_HI = 1.0, 100.0   # Hz — alive but not saturated


def _probe(pl: dict) -> dict:
    """One condition: build a random genome, drive it, measure the dynamical regime."""
    cfg = EvoNetConfig(N=pl["N"], n_in=pl["n_in"], d=pl["d"], bias=pl["bias"],
                       input_gain=pl["ig"], noise_sigma=pl["noise"])
    g = random_genome(cfg, pl["density"], w0=pl["w0"], ei_split=pl["ei"],
                      inh_gain=pl.get("inh_gain"), seed=pl["seed"])
    W = g.W

    # constant stimulus drive (we are measuring the REGIME, not the task)
    rng = np.random.default_rng(pl["seed"] + 7)
    E = rng.standard_normal(pl["n_in"])
    drive = np.zeros(cfg.N); drive[:cfg.n_in] = cfg.input_gain * E

    eqs = """
    dv/dt = (v_rest - v + I_syn + I_ext + bias)/tau_m + noise_sigma*sqrt(2/tau_m)*xi : 1 (unless refractory)
    dI_syn/dt = -I_syn/tau_syn : 1
    I_ext : 1
    """
    ns = dict(v_rest=cfg.v_rest, tau_m=cfg.tau_m*ms, tau_syn=cfg.tau_syn*ms, bias=cfg.bias,
              noise_sigma=cfg.noise_sigma, v_thresh=cfg.v_thresh, v_reset=cfg.v_reset)
    G = b2.NeuronGroup(cfg.N, eqs, threshold="v > v_thresh", reset="v = v_reset",
                       refractory=cfg.refractory_ms*ms, method="euler", namespace=ns, name="gc")
    G.v = cfg.v_rest
    G.I_ext = drive
    post, pre = np.nonzero(W)
    S = b2.Synapses(G, G, model="w : 1", on_pre="I_syn_post += w", name="s")
    if len(pre):
        S.connect(i=pre, j=post); S.w = W[post, pre]
    spk = b2.SpikeMonitor(G, name="spk")
    rec = list(range(min(60, cfg.N)))
    vm = b2.StateMonitor(G, ["v", "I_syn"], record=rec, dt=1*ms, name="vm")
    net = b2.Network(G, S, spk, vm)
    net.run(pl["dur_ms"] * ms)

    # --- CV of ISI, pooled over neurons that spiked enough ---------------------------
    trains = spk.spike_trains()
    cvs = []
    for i, t in trains.items():
        if len(t) >= 4:
            isi = np.diff(np.asarray(t / ms))
            if isi.mean() > 0:
                cvs.append(isi.std() / isi.mean())
    cv = float(np.mean(cvs)) if cvs else np.nan
    rate = float(len(spk.t) / (cfg.N * pl["dur_ms"] / 1000.0))

    v = np.asarray(vm.v)                       # (rec, T)
    v_mean = float(v.mean()); v_std = float(v.std())
    v_sub = float((cfg.v_thresh - v_mean) / cfg.v_thresh)   # >0 => subthreshold mean

    Isyn = np.asarray(vm.I_syn)
    pos, neg = Isyn[Isyn > 0], Isyn[Isyn < 0]
    ei = float(abs(pos.mean()) / (abs(neg.mean()) + 1e-9)) if len(pos) and len(neg) else np.nan

    b2.device.reinit(); b2.device.activate()
    return dict(bias=pl["bias"], input_gain=pl["ig"], w0=pl["w0"], density=pl["density"],
                ei_split=pl["ei"], noise=pl["noise"], cv_isi=cv, rate=rate,
                v_mean=v_mean, v_std=v_std, v_mean_sub=v_sub, ei_current=ei,
                fluctuation_driven=bool((cv > CV_TARGET_LO) and (v_sub > 0)
                                        and (RATE_LO < rate < RATE_HI)))


PRESETS = {
    "default": dict(biases=(0.2, 0.5, 0.8), gains=(1.0, 10.0), w0s=(0.5, 1.5, 3.0),
                    densities=(0.05, 0.2), eis=(0.8,), noises=(0.0,)),
    "balanced": dict(biases=(0.5, 0.8, 1.1), gains=(1.0, 5.0), w0s=(0.3, 0.8, 1.5),
                     densities=(0.1, 0.3), eis=(0.8,), noises=(0.0,)),
    "noise":   dict(biases=(0.6, 0.9), gains=(1.0,), w0s=(0.1, 0.3, 0.6),
                    densities=(0.1, 0.3), eis=(0.8,), noises=(0.2, 0.5, 1.0)),
    "wide":    dict(biases=(0.2, 0.5, 0.8, 1.2), gains=(1.0, 10.0), w0s=(0.5, 1.5, 3.0, 6.0),
                    densities=(0.05, 0.2, 0.5), eis=(0.5, 0.8), noises=(0.0, 0.1, 0.3)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=list(PRESETS), default="default")
    ap.add_argument("--N", type=int, default=100)
    ap.add_argument("--dur-ms", type=float, default=2000.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    g = PRESETS[args.preset]
    cells = list(itertools.product(g["biases"], g["gains"], g["w0s"], g["densities"],
                                   g["eis"], g["noises"]))
    payloads = [dict(bias=b, ig=ig, w0=w, density=dn, ei=ei, noise=nz, N=args.N,
                     n_in=10, d=10, dur_ms=args.dur_ms, seed=args.seed)
                for (b, ig, w, dn, ei, nz) in cells]

    run = P.new_run("T0", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(preset=args.preset, N=args.N, grid=g, dur_ms=args.dur_ms),
                    tag="gateC-regime", seeds=[args.seed],
                    notes="Gate C: is the fluctuation-driven balanced regime reachable? (D039)")
    print(f"run: {run.run_id}\n{len(payloads)} conditions, N={args.N}\n")
    try:
        import pandas as pd
        rows = []
        if args.workers <= 1:
            rows = [_probe(pl) for pl in payloads]
        else:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(args.workers) as pool:
                for i, r in enumerate(pool.imap_unordered(_probe, payloads)):
                    rows.append(r); print(f"  [{i+1}/{len(payloads)}]")
        df = pd.DataFrame(rows).sort_values(["bias", "input_gain", "w0", "density"])
        df.to_parquet(run.table_path("gateC"))

        print(f"\n{'bias':>5} {'gain':>5} {'w0':>5} {'dens':>5} {'nz':>4} | "
              f"{'CV_ISI':>7} {'rate':>7} {'V-thr':>7} {'V_std':>6} {'E/I':>5} | fluct?")
        for _, r in df.iterrows():
            print(f"{r.bias:>5} {r.input_gain:>5} {r.w0:>5} {r.density:>5} {r.noise:>4} | "
                  f"{r.cv_isi:>7.2f} {r.rate:>7.1f} {r.v_mean_sub:>7.2f} {r.v_std:>6.2f} "
                  f"{r.ei_current:>5.2f} | {'YES' if r.fluctuation_driven else '-'}")

        n_ok = int(df.fluctuation_driven.sum())
        print(f"\n=== VERDICT ===")
        print(f"fluctuation-driven conditions: {n_ok}/{len(df)}")
        print(f"CV_ISI range: {df.cv_isi.min():.2f} .. {df.cv_isi.max():.2f}   (target ~1.0)")
        print(f"rate range:   {df.rate.min():.1f} .. {df.rate.max():.1f} Hz")
        if n_ok == 0:
            print("  !! NO reachable fluctuation-driven regime in this grid.")
            print("     -> gain control is UNAVAILABLE, H-D has no treatment arm, and")
            print("        regulation cannot emerge. Try --preset wide (adds noise_sigma>0,")
            print("        stronger w0, lower ei_split). If still nothing, the design needs")
            print("        rethinking BEFORE evolve.py.")
        else:
            best = df[df.fluctuation_driven].sort_values("cv_isi", ascending=False).iloc[0]
            print(f"  OK: reachable. Best CV={best.cv_isi:.2f} at bias={best.bias}, "
                  f"gain={best.input_gain}, w0={best.w0}, density={best.density}, "
                  f"noise={best.noise}")
            print("  -> H-D has both arms: TONIC (CV<<1) vs BALANCED (CV~1).")
        note = (f"Gate C: {n_ok}/{len(df)} fluctuation-driven; CV range "
                f"{df.cv_isi.min():.2f}-{df.cv_isi.max():.2f}")
        run.finalize(status="complete", n_conditions=len(df), notebook_note=note)
    except Exception as e:
        run.finalize(status="failed", error=str(e)); raise


if __name__ == "__main__":
    main()
