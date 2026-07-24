"""D111 EXPERIMENT — switch the selection basis to REGULATION ONLY (linear readout) and test whether it
CLIMBS where the hybrid-fitness sweep (D108) was flat.

Motivation (D109/D111): aggregate hybrid fitness is NON-HERITABLE (r~0) while the REGULATION component IS
heritable (r~0.29, replicated). The hybrid has been diluting a transmissible signal with a
non-transmissible one. Selecting on regulation alone is a minimal change that adds ZERO uncounted P (the
readout stays LINEAR -- the P-axis criterion, D111 sec 0).

BETA CALIBRATION (important -- do not skip). Selection is softmax on ABSOLUTE fitness differences
(z = beta*(f - f.max())), so beta is SCALE-DEPENDENT. regulation_only fitness has ~4.3x SMALLER spread
than hybrid (measured: SD 0.0088 vs 0.0382 on 6 unselected genomes). Reusing hybrid's beta would deliver
~4x WEAKER selection and we'd misread the result as "regulation-only doesn't work." So we BRACKET beta
rather than bet on one value: regulation_only at beta~20 is roughly equivalent to hybrid at beta~5.
We keep the selection ALGORITHM untouched (no SD-normalization) so everything stays comparable to D108.

Grid (4 cells, ~1h each):
  regulation_only x beta {5, 20, 50}   <- 20 is the calibrated equivalent; 5 and 50 bracket it
  hybrid          x beta {5}           <- D108-comparable CONTROL (should reproduce the flat result)

Also runs the READOUT-POWER AUDIT (D111): score RANDOM/SCRAMBLED networks with the same readout. If a
random network scores nearly as well as an evolved one, the readout is doing the network's job (the
abandoned-RC failure mode). The (evolved - random) gap is the network's actual contribution.

D100-compliant: per-cell checkpointing (resumable), disk logging (D102), per-cell/per-gen heartbeat,
self-invalidating checkpoints (config+code hash). Writes under runs/ per repo convention.

Usage: python regulation_selection_run.py [--pop 30] [--gens 40] [--workers 6] [--out runs/reg_select]
"""
import sys, os, json, time, argparse, pathlib, datetime, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, random_genome
from ddescent.evolve import (EvolveConfig, run_evolution, evaluate, _fitness,
                             assert_no_test_leakage)
from ddescent import tasks as T

CODE_VERSION = "D115-regsel-2-threeway-nassays4"

# (fitness_mode, beta) cells. D114 showed beta*SD ~ 1 is needed for sharp discrimination and that even
# beta=50 was sub-saturation, so we push higher. beta=0 is the DRIFT CONTROL (uniform selection): any
# improvement above it is attributable to selection rather than mutation drift.
CELLS = [("regulation_only", 0.0),      # drift control
         ("regulation_only", 50.0),
         ("regulation_only", 100.0),
         ("regulation_only", 200.0)]

# D115: fitness reliability at n_assays=1 is ~0.05 -- every prior run selected on approximately pure
# noise. Replication is the cheap lever (noise averages down as 1/sqrt(k)). n_assays=4 costs ~2.1x the
# old baseline per evaluation and lifts reliability off the floor. Raise to 8 if results stay ambiguous.
N_ASSAYS = 4

# density is FIXED at the default here (D108 parity). Density is P_dev and is the NEXT experiment
# (H-A/H-B axis) -- deliberately held constant so this run isolates the SELECTION-BASIS change.
WTA_GAIN = 1.0          # competition ON (D110 showed it improves nonlinear decodability)


def net_config():
    return EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                        present_ms=50, tau_slow=100.0, nmda_frac=0.5,
                        dev_ee_stdp=True, dev_wta_comp=True, wta_gain=WTA_GAIN)


def cell_hash(mode, beta, pop, gens):
    payload = dict(mode=mode, beta=beta, pop=pop, gens=gens, wta_gain=WTA_GAIN,
                   dev_ms=800.0, dev_eta=1e-3, eta_e=5e-3, n_assays=N_ASSAYS, seed=12345,
                   N=50, noise_sigma=1.0, task="hier_K10_d3_r1-3_ctx4_dwell10_seed0",
                   code_version=CODE_VERSION)
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def cell_id(mode, beta):
    return f"{mode}_beta{beta:g}".replace(".", "p")


def climb_metrics(history):
    ft = np.array([h.get("fit_mean", np.nan) for h in history])
    bt = np.array([h["best_test"] for h in history])
    reg = np.array([h.get("reg_best", 0.0) for h in history])
    regm = np.array([h.get("reg_mean", 0.0) for h in history])
    k = max(3, (2 * len(ft)) // 3); x = np.arange(k)
    slope = float(np.polyfit(x, ft[-k:], 1)[0]) if len(ft) >= k and np.all(np.isfinite(ft[-k:])) else 0.0
    reg_slope = float(np.polyfit(x, regm[-k:], 1)[0]) if len(regm) >= k else 0.0
    return dict(fit_slope=slope, reg_slope=reg_slope,
                fit_start=float(ft[0]), fit_end=float(ft[-1]),
                reg_best_start=float(reg[0]), reg_best_end=float(reg[-1]),
                reg_mean_start=float(regm[0]), reg_mean_end=float(regm[-1]),
                best_test_start=float(bt[0]), best_test_end=float(bt[-1]),
                best_test_min=float(bt.min()))


def readout_power_audit(task, cfg, n=10):
    """D111 standing control: how well do RANDOM (unevolved, undeveloped) networks score under this
    readout? If random ~= evolved, the readout is doing the network's job."""
    net_cfg = net_config()
    scores = []
    for i in range(n):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=9000 + i)
        r = evaluate(g, task, net_cfg, cfg)
        scores.append(_fitness(r, r["n_params"], cfg))
    scores = np.array(scores)
    return dict(random_mean=float(scores.mean()), random_sd=float(scores.std()),
                random_max=float(scores.max()), n=n)


def run_cell(mode, beta, args, task, out_dir):
    cid = cell_id(mode, beta)
    h = cell_hash(mode, beta, args.pop, args.gens)
    ckpt = out_dir / f"{cid}.json"
    if ckpt.exists():
        try:
            prev = json.loads(ckpt.read_text())
            if prev.get("config_hash") == h:
                print(f"[skip] {cid} (hash matches)"); return prev
            print(f"[rerun] {cid} (config/code changed)")
        except Exception:
            print(f"[rerun] {cid} (unreadable checkpoint)")
    t0 = time.time()
    net_cfg = net_config()
    cfg = EvolveConfig(pop_size=args.pop, n_generations=args.gens, dev_ms=800.0, dev_eta=1e-3,
                       n_assays=N_ASSAYS, fitness_beta=beta, seed=12345, fitness_mode=mode)
    print(f"[cell {cid}] START mode={mode} beta={beta} pop={args.pop} gens={args.gens} hash={h}",
          flush=True)
    history, _ = run_evolution(task, net_cfg, cfg, n_workers=args.workers, verbose=True)
    m = climb_metrics(history)
    # readout-power audit under THIS fitness mode
    m["audit"] = readout_power_audit(task, cfg)
    m["audit"]["evolved_minus_random"] = m["fit_end"] - m["audit"]["random_mean"]
    m.update(dict(cell=cid, config_hash=h, code_version=CODE_VERSION, fitness_mode=mode, beta=beta,
                  pop=args.pop, gens=args.gens, seconds=round(time.time() - t0, 1),
                  timestamp=datetime.datetime.now().isoformat()))
    ckpt.write_text(json.dumps(m, indent=2))
    a = m["audit"]
    print(f"[cell {cid}] DONE {m['seconds']}s | fit_slope={m['fit_slope']:+.5f} "
          f"reg_slope={m['reg_slope']:+.5f} | reg_mean {m['reg_mean_start']:.4f}->{m['reg_mean_end']:.4f} "
          f"| best_test {m['best_test_start']:.3f}->{m['best_test_end']:.3f} (min {m['best_test_min']:.3f})",
          flush=True)
    print(f"    [audit] random-network mean={a['random_mean']:.4f} (max {a['random_max']:.4f}) vs "
          f"evolved {m['fit_end']:.4f} | gap={a['evolved_minus_random']:+.4f}", flush=True)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=30)
    ap.add_argument("--gens", type=int, default=40)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default="runs/reg_select_v2")
    args = ap.parse_args()
    out_dir = pathlib.Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)

    with tee("regulation_selection_run", log_dir=str(out_dir),
             header=f"D111: regulation-only selection vs hybrid control; pop={args.pop} gens={args.gens}"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4,
                                           n_train=60, n_val=60, n_test=60,
                                           context_dwell=10, seed=0)
        assert_no_test_leakage(task)      # D113: fitness must never see the reporting split
        hr = task.headroom()
        print(f"task floor={hr['memoryless_floor']:.3f} ceiling={hr['oracle_ceiling']:.3f}")
        print(f"cells: {[cell_id(m,b) for m,b in CELLS]}")
        print(f"n_assays={N_ASSAYS} (D115: reliability ~0.05 at n_assays=1 -- prior runs selected on noise)")
        print("THREE-WAY SPLIT (D113): develop on train, SELECT on val, REPORT on test.")
        print("THE QUESTION: does TEST error improve when selection can no longer see it?\n")
        cells, t_start = [], time.time()
        for i, (mode, beta) in enumerate(CELLS):
            cells.append(run_cell(mode, beta, args, task, out_dir))
            el = time.time() - t_start
            print(f"  [heartbeat] {i+1}/{len(CELLS)} cells | elapsed {el/60:.1f}min "
                  f"| eta {(el/(i+1))*(len(CELLS)-i-1)/60:.1f}min\n", flush=True)

        print("\n" + "=" * 78)
        print("REGULATION-ONLY SELECTION — did it climb where hybrid was flat?")
        print("=" * 78)
        print(f"{'cell':>26} | {'fit_slope':>10} | {'reg_slope':>10} | {'reg_mean end':>12} | {'test_min':>9}")
        for m in cells:
            print(f"{m['cell']:>26} | {m['fit_slope']:>+10.5f} | {m['reg_slope']:>+10.5f} | "
                  f"{m['reg_mean_end']:>12.4f} | {m['best_test_min']:>9.3f}")
        print("\nREADOUT-POWER AUDIT (evolved - random; small gap => readout doing the network's job):")
        for m in cells:
            a = m["audit"]
            print(f"  {m['cell']:>26}: random={a['random_mean']:.4f} evolved={m['fit_end']:.4f} "
                  f"gap={a['evolved_minus_random']:+.4f}")
        (out_dir / "_summary.json").write_text(json.dumps(cells, indent=2))
        print(f"\n{len(cells)} cells -> {out_dir}/")
        print("\nREAD AS A CONTRAST: does regulation_only show a POSITIVE reg_slope/fit_slope where the")
        print("hybrid control (and all of D108) drifted? Compare regulation_only@beta20 to hybrid@beta5.")


if __name__ == "__main__":
    main()
