"""Validate the engineered ceiling (D092/D092b) with a persisted, notebook-logged run.

The ceiling (ddescent/engineered_ceiling.py) is the known-positive control (D088) — a hand-wired
Wang/Compte/Brunel winner-take-all context-memory attractor. This script runs its CARRY validation
and persists the result via provenance, so the ceiling's validation is reproducible from the repo
(not just a sandbox claim).

CARRY test (D092b): cue the network with context-A-igniting vs context-B-igniting input, then an
enforced SILENT DELAY. Measure cluster selectivity (does the cue-matched cluster stay active, the
other suppressed) ACROSS delay lengths. The validated signature (D092b): real attractor memory
DECAYS gracefully across delay (vs the random-net confound, which stayed flat).

Regulation validation (D093, context-selects-map via gating) is a later addition once the ceiling's
regulation half is wired.

Run from repo root:  python scripts/run_ceiling_validation.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np
import brian2 as b2
from brian2 import ms
from ddescent import provenance as P
from ddescent.evonet import EvoNetConfig, EvoNet
from ddescent.engineered_ceiling import build_engineered_ceiling, A_IDX, B_IDX

DELAYS_MS = [0, 100, 300, 600]
CUE_STIM = 5
SAMPLE_MS = 5.0


def delay_state(net, cfg, cue, delay_ms):
    """Drive with a cue run then delay_ms of silence; return mean state during the delay (N,)."""
    c = cfg; n = cue.shape[0]; cue_ms = n * c.present_ms; tot = cue_ms + delay_ms
    n_steps = int(round(tot / c.present_ms))
    drive = np.zeros((n_steps, c.N))
    for k in range(n):
        drive[k, :c.n_in] = c.input_gain * cue[k]
    ta = b2.TimedArray(drive, dt=c.present_ms * ms)
    net.net.restore("init"); net.G.namespace["ta"] = ta
    mon = b2.StateMonitor(net.G, "r", record=True, dt=SAMPLE_MS * ms, name="mon_cv")
    net.net.add(mon); net.net.run(tot * ms)
    r = np.asarray(mon.r); t = np.asarray(mon.t / ms); net.net.remove(mon)
    if len(t): t = t - t[0]
    win = (t > cue_ms) if delay_ms > 0 else (t > cue_ms - 25)   # delay=0 reads last 25ms of cue
    return r[:, win].mean(1)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    ap.add_argument("--nmda", type=float, default=0.7)
    args = ap.parse_args()

    cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=0.5,
                       present_ms=50, tau_slow=100.0, nmda_frac=args.nmda)
    genome = build_engineered_ceiling()
    net = EvoNet(genome, cfg)

    run = P.new_run("E9", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(probe="ceiling_validation", nmda_frac=args.nmda, N=50,
                                delays_ms=DELAYS_MS, P=int(genome.n_params())),
                    tag="ceiling-validation",
                    notes="D092b: validate the engineered-ceiling known-positive. CARRY = cue-matched "
                          "cluster persists+decays through silent delay.")
    print(f"run: {run.run_id}")
    print(f"engineered ceiling validation (D092b) · nmda_frac={args.nmda} · P={genome.n_params()}\n")

    # cue A drives input[:5] (-> cluster A), cue B drives input[5:] (-> cluster B)
    cueA = np.tile(np.concatenate([np.ones(5), np.zeros(5)]), (CUE_STIM, 1))
    cueB = np.tile(np.concatenate([np.zeros(5), np.ones(5)]), (CUE_STIM, 1))

    rows = []
    print("delay_ms | A-cue: clustA clustB | B-cue: clustA clustB | selectivity")
    for dly in DELAYS_MS:
        sA = delay_state(net, cfg, cueA, dly)
        sB = delay_state(net, cfg, cueB, dly)
        aA, aB = float(sA[A_IDX].mean()), float(sA[B_IDX].mean())
        bA, bB = float(sB[A_IDX].mean()), float(sB[B_IDX].mean())
        # selectivity: A-cue should favor clusterA, B-cue clusterB
        sel = ((aA - aB) + (bB - bA)) / 2.0
        rows.append(dict(delay_ms=dly, Acue_clustA=aA, Acue_clustB=aB,
                         Bcue_clustA=bA, Bcue_clustB=bB, selectivity=sel))
        print(f"  {dly:5d}  |  {aA:6.2f} {aB:6.2f}  |  {bA:6.2f} {bB:6.2f}  |  {sel:.3f}")

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_parquet(run.table_path("ceiling_carry"))

    # verdict: selective at short delay AND decays gracefully (the validated memory signature)
    sel0 = df[df.delay_ms == DELAYS_MS[1]]["selectivity"].values[0]  # 100ms
    selL = df[df.delay_ms == DELAYS_MS[-1]]["selectivity"].values[0]  # 600ms
    selective = sel0 > 1.0
    decays = selL < sel0 and selL > 0.1        # decays but not to nothing (graceful)
    print("\n=== VERDICT (D092b) ===")
    print(f"selective at 100ms (sel>1): {selective} (sel={sel0:.3f})")
    print(f"decays gracefully to 600ms (memory signature, not flat confound): {decays} "
          f"(sel {sel0:.3f} -> {selL:.3f})")
    ok = selective and decays
    if ok:
        print("=> CEILING VALIDATED: carries context (cue-selective attractor) that persists and")
        print("   decays through silence. The carry measure (decay-across-delay) is confirmed on the")
        print("   known-positive; trustworthy for developed-net testing (step 3).")
    else:
        print("=> unexpected: re-tune ceiling weights (w_rec/w_inh/w_drive) or nmda_frac.")

    run.finalize(status="complete",
                 notebook_note=f"Engineered-ceiling carry validation (nmda={args.nmda}, P={genome.n_params()}): "
                               f"selectivity {sel0:.2f}(100ms)->{selL:.2f}(600ms); "
                               f"selective={selective}, graceful_decay={decays}. "
                               f"{'VALIDATED known-positive' if ok else 'NEEDS RETUNE'}. "
                               f"Carry measure = decay-across-delay (D092b).")


if __name__ == "__main__":
    main()
