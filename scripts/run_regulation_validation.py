"""Validate the REGULATION MEASURE against the integrated ceiling (D093/D094), persisted with provenance.

The integrated ceiling (build_regulation_ceiling) both carries context through a silent delay AND uses
held context to select the probe->output map via disinhibitory gating. This script validates that the
GRADED regulation measure -- the `regulation` factor in the D094 fitness term carrying*regulation --
correctly detects and GRADES context-dependent map-selection.

Validation = sweep gate strength from 0 (no gating -> context-independent -> score ~floor, known-
negative) to strong (crisp gating -> high score). The measure must rise MONOTONICALLY: that is what
makes it a graded partial-credit signal (the GA gradient within the regulation bonus, D094).

Regulation measure: present an identical probe under each held context; score = mean over probes of
||resp(A) - resp(B)|| / (||resp(A)|| + ||resp(B)||). 0 = context-independent (no regulation); higher =
stronger context-dependent map-selection. Graded and continuous by construction.

Run from repo root:  python scripts/run_regulation_validation.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import numpy as np
import brian2 as b2
from brian2 import ms
from ddescent import provenance as P
from ddescent.evonet import EvoNetConfig, EvoNet
from ddescent.engineered_ceiling import build_regulation_ceiling, R_CUE, R_PROBE, R_OUT

GATE_SWEEP = [(0.0, 0.0), (5.0, 4.0), (10.0, 8.0), (15.0, 12.0), (20.0, 15.0)]
N_PROBES = 6
DELAY_MS = 200


def _probe_response(net, cfg, ctx, probe, delay_ms):
    c = cfg; n_cue = 5; n_delay = int(delay_ms / c.present_ms); n_probe = 3
    total = n_cue + n_delay + n_probe
    drive = np.zeros((total, c.N))
    for k in range(n_cue):
        drive[k, R_CUE[:2] if ctx == 'A' else R_CUE[2:]] = c.input_gain
    for k in range(n_cue + n_delay, total):
        drive[k, R_PROBE] = c.input_gain * probe
    ta = b2.TimedArray(drive, dt=c.present_ms * ms)
    net.net.restore("init"); net.G.namespace["ta"] = ta
    mon = b2.StateMonitor(net.G, "r", record=True, dt=5 * ms, name="mon_rv")
    net.net.add(mon); net.net.run(total * c.present_ms * ms)
    r = np.asarray(mon.r); t = np.asarray(mon.t / ms); net.net.remove(mon)
    if len(t): t = t - t[0]
    ps = (n_cue + n_delay) * c.present_ms
    return r[R_OUT][:, t > ps].mean(1)


def regulation_score(net, cfg, n_probes=N_PROBES, delay_ms=DELAY_MS, seed=0):
    """Graded [0, inf): how much the identical-probe OUTPUT depends on held context (D094 factor)."""
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_probes):
        probe = rng.uniform(0.5, 1.5, size=len(R_PROBE))
        rA = _probe_response(net, cfg, 'A', probe, delay_ms)
        rB = _probe_response(net, cfg, 'B', probe, delay_ms)
        scale = np.linalg.norm(rA) + np.linalg.norm(rB) + 1e-6
        diffs.append(np.linalg.norm(rA - rB) / scale)
    return float(np.mean(diffs))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    ap.add_argument("--nmda", type=float, default=0.7)
    args = ap.parse_args()

    cfg = EvoNetConfig(N=50, n_in=6, d=3, bias=0.6, input_gain=10.0, noise_sigma=0.3,
                       present_ms=50, tau_slow=100.0, nmda_frac=args.nmda)

    run = P.new_run("E9", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(probe="regulation_validation", nmda_frac=args.nmda,
                                gate_sweep=GATE_SWEEP, n_probes=N_PROBES, delay_ms=DELAY_MS),
                    tag="regulation-validation",
                    notes="D093/D094: validate the graded regulation measure against the integrated "
                          "carry-and-regulate ceiling. Sweep gate strength; score must rise monotonically.")
    print(f"run: {run.run_id}")
    print(f"regulation-measure validation (D093/D094) · nmda_frac={args.nmda}\n")
    print("gate_block gate_drive | regulation_score")

    rows = []
    for gb, gd in GATE_SWEEP:
        net = EvoNet(build_regulation_ceiling(gate_block=gb, gate_drive=gd), cfg)
        s = regulation_score(net, cfg, seed=0)
        rows.append(dict(gate_block=gb, gate_drive=gd, regulation=s))
        print(f"   {gb:5.1f}   {gd:5.1f}   |   {s:.4f}")

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_parquet(run.table_path("regulation_validation"))

    scores = df["regulation"].values
    monotonic = bool(np.all(np.diff(scores) > -1e-3))     # non-decreasing (allow tiny noise)
    detects = scores[-1] > 2.0 * scores[0]                # strong gating clearly beats no-gating
    print("\n=== VERDICT (D093/D094) ===")
    print(f"score rises with gate strength (monotonic): {monotonic}")
    print(f"detects regulation (strong >> none): {detects} ({scores[0]:.3f} -> {scores[-1]:.3f})")
    ok = monotonic and detects
    if ok:
        print("=> REGULATION MEASURE VALIDATED: detects and GRADES context-dependent map-selection.")
        print("   Graded partial-credit confirmed -> usable as the `regulation` factor in the D094")
        print("   carrying*regulation fitness term. Trustworthy for developed-net testing (step 3).")
    else:
        print("=> unexpected: measure not cleanly graded; inspect before wiring into fitness.")

    run.finalize(status="complete",
                 notebook_note=f"Regulation-measure validation (nmda={args.nmda}): score "
                               f"{scores[0]:.3f}(no-gate)->{scores[-1]:.3f}(crisp), monotonic={monotonic}, "
                               f"detects={detects}. {'VALIDATED graded measure' if ok else 'NEEDS REVIEW'} "
                               f"for the D094 carrying*regulation term.")


if __name__ == "__main__":
    main()
