"""DEVELOPMENT x BETA SWEEP (the joint-tuning test). Maps the 2D landscape of (development-structure,
selection-pressure): does selection AMPLIFY development's faint variation into adaptive climbing, and
where in the joint space? Axes:
  - DEVELOPMENT (wta_gain): competition/funnel strength. 0 = eSTDP-only (no competition control),
    rising = more developable lateral-inhibition competition (D107). eta_e fixed at 5e-3 (eSTDP live).
  - BETA (fitness_beta): replicator selection sharpness. weak (near-neutral drift, the pilot regime)
    -> strong (sharp discrimination). This is B1 from the queue, finally tested UNDER real selection.
Per cell: a real (short) GA run; outcome = fitness CLIMB (slope over gens) + capability emergence
(enc/car/reg) + does best_test drop below floor. Hypothesis: some (wta_gain>0, beta high enough) region
shows climbing that the eSTDP-only / weak-beta corners do not.

D100 COMPLIANT (this is an overnight run): per-cell CHECKPOINTING (each cell -> disk as it finishes,
resumable), disk LOGGING (D102), per-cell + per-gen HEARTBEAT. Grid of INDEPENDENT cells (Azure-portable,
content-hash seeds). Freeze source once launched (workers re-import).

Usage: python dev_beta_sweep.py [--pop 24] [--gens 25] [--workers 6] [--out sweep_runs]
Resumable: re-running skips cells whose checkpoint already exists.
"""
import sys, os, json, time, argparse, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig
from ddescent.evolve import EvolveConfig, run_evolution
from ddescent import tasks as T

WTA_GAINS = [0.0, 0.5, 1.0, 2.0]      # development axis: 0 = eSTDP-only, rising = more competition
BETAS     = [1.0, 5.0, 20.0, 50.0]    # selection axis: weak -> strong

def cell_id(wta, beta):
    return f"wta{wta:g}_beta{beta:g}".replace(".", "p")

def climb_metrics(history):
    """Extract fitness-climb signal from a run's history."""
    ft = np.array([h["fit_mean"] if "fit_mean" in h else h.get("fit_best", np.nan) for h in history])
    bt = np.array([h["best_test"] for h in history])
    car = np.array([h.get("car_best", h.get("carrying_best", 0.0)) for h in history])
    reg = np.array([h.get("reg_best", h.get("regulation_best", 0.0)) for h in history])
    # slope of mean fitness over the last 2/3 of the run (avoid initial transient)
    k = max(3, (2 * len(ft)) // 3); x = np.arange(k)
    slope = float(np.polyfit(x, ft[-k:], 1)[0]) if len(ft) >= k and np.all(np.isfinite(ft[-k:])) else 0.0
    return dict(fit_slope=slope, fit_start=float(ft[0]), fit_end=float(ft[-1]),
                best_test_start=float(bt[0]), best_test_end=float(bt[-1]), best_test_min=float(bt.min()),
                car_end=float(car[-1]), reg_end=float(reg[-1]),
                car_delta=float(car[-1] - car[0]), reg_delta=float(reg[-1] - reg[0]))

def run_cell(wta, beta, args, task, out_dir):
    cid = cell_id(wta, beta)
    ckpt = out_dir / f"{cid}.json"
    if ckpt.exists():
        print(f"[skip] {cid} (checkpoint exists)"); return json.loads(ckpt.read_text())
    t0 = time.time()
    net_cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                           present_ms=50, tau_slow=100.0, nmda_frac=0.5,
                           dev_ee_stdp=True, dev_wta_comp=(wta > 0), wta_gain=max(wta, 1e-9))
    cfg = EvolveConfig(pop_size=args.pop, n_generations=args.gens, dev_ms=800.0, dev_eta=1e-3,
                       n_assays=1, fitness_beta=beta, seed=12345)
    print(f"[cell {cid}] START pop={args.pop} gens={args.gens} wta_gain={wta} beta={beta} "
          f"comp={'on' if wta>0 else 'OFF'}", flush=True)
    history, _ = run_evolution(task, net_cfg, cfg, n_workers=args.workers, verbose=True)
    m = climb_metrics(history)
    m.update(dict(cell=cid, wta_gain=wta, beta=beta, pop=args.pop, gens=args.gens,
                  seconds=round(time.time() - t0, 1),
                  timestamp=datetime.datetime.now().isoformat()))
    ckpt.write_text(json.dumps(m, indent=2))          # D100: checkpoint THIS cell now
    print(f"[cell {cid}] DONE in {m['seconds']}s | fit_slope={m['fit_slope']:+.5f} "
          f"best_test {m['best_test_start']:.3f}->{m['best_test_end']:.3f} (min {m['best_test_min']:.3f}) "
          f"car_delta={m['car_delta']:+.4f} reg_delta={m['reg_delta']:+.4f}", flush=True)
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=24)
    ap.add_argument("--gens", type=int, default=25)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default="sweep_runs")
    args = ap.parse_args()
    out_dir = pathlib.Path(args.out); out_dir.mkdir(exist_ok=True)

    with tee("dev_beta_sweep", log_dir=str(out_dir),
             header=f"dev(wta_gain) x beta sweep; pop={args.pop} gens={args.gens} grid {len(WTA_GAINS)}x{len(BETAS)}"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                           context_dwell=10, seed=0)
        floor = task.headroom()["memoryless_floor"]; ceil = task.headroom()["oracle_ceiling"]
        print(f"task floor={floor:.3f} ceiling={ceil:.3f}")
        print(f"grid: wta_gain={WTA_GAINS} x beta={BETAS} = {len(WTA_GAINS)*len(BETAS)} cells\n")
        cells = []
        total = len(WTA_GAINS) * len(BETAS); done = 0
        t_start = time.time()
        for wta in WTA_GAINS:
            for beta in BETAS:
                m = run_cell(wta, beta, args, task, out_dir)
                cells.append(m); done += 1
                elapsed = time.time() - t_start
                eta = (elapsed / done) * (total - done)
                print(f"  [heartbeat] {done}/{total} cells done | elapsed {elapsed/60:.1f}min "
                      f"| eta {eta/60:.1f}min\n", flush=True)

        # summary grid
        print("\n" + "=" * 74)
        print("FITNESS-CLIMB LANDSCAPE (fit_slope; positive = selection climbing)")
        print("=" * 74)
        print(f"{'wta\\beta':>10} |" + "".join(f"{b:>12}" for b in BETAS))
        for wta in WTA_GAINS:
            row = []
            for beta in BETAS:
                m = next(c for c in cells if c["wta_gain"] == wta and c["beta"] == beta)
                row.append(f"{m['fit_slope']:+.4f}")
            print(f"{wta:>10} |" + "".join(f"{c:>12}" for c in row))
        print("\nbest_test_min across grid (closest any cell got to beating floor):")
        best = min(cells, key=lambda c: c["best_test_min"])
        print(f"  {best['cell']}: best_test_min={best['best_test_min']:.3f} (floor={floor:.3f})")
        # write combined summary
        (out_dir / "_summary.json").write_text(json.dumps(cells, indent=2))
        print(f"\nall {len(cells)} cells -> {out_dir}/  (per-cell checkpoints + _summary.json)")

if __name__ == "__main__":
    main()
