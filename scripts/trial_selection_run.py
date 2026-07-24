"""TRIAL-ARM RUNNER — first GA arm on the cue->delay->probe XOR task (D120), with the D121 clock fix.

Drives the TRIAL task through run_evolution's task-agnostic hooks (added alongside D121):
    eval_fn       = trial_evaluate                  -- population scoring (serial path)
    report_fn     = trial_evaluate(report=True)     -- per-generation best train/test
    worker_scorer = "trial"                          -- so --workers parallelises via the pool

Selection basis is `trial_xor` (study_config.make_trial_evolve_cfg); fitness = trial_score = 1 - val_err,
0.0 == predicting the mean, a zero point that is EXACT because the XOR target puts every cue-blind and
probe-blind strategy at chance by construction (D120).

PRE-ARM GATE (runs before any generation; aborts loudly on failure):
  * LEAKAGE (hard)     -- destroying Y_test must not move val fitness (D113 three-way split).
  * CONTROLS (report)  -- omit_cue / scramble val_acc on a random genome (must not sit ABOVE chance;
                          the decisive control test is post-arm, when 'normal' has risen).
The delay-persistence and full D121-regression invariants live in scripts/delay_persistence_probe.py
(run that separately; it is heavier).

Operational discipline mirrors regulation_selection_run.py: per-cell checkpoint (resumable,
self-invalidating on config/code hash), tee disk logging, heartbeat + ETA.

Usage:
  python trial_selection_run.py [--pop 30] [--gens 40] [--workers 1] [--delay 1]
                                [--dev-ms 16000] [--assays 4] [--out runs/trial_arm]
Serial by default. Run one serial arm to confirm it climbs, then --workers 6 for local sweeps.
"""
import sys, json, time, argparse, pathlib, datetime, hashlib
_here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_here.parent))     # repo root -> `ddescent` importable
sys.path.insert(0, str(_here))            # scripts/  -> sibling probe importable
import numpy as np

from ddescent.runlog import tee
from ddescent import study_config as SC
from ddescent.evonet import random_genome
from ddescent.evolve import run_evolution
from ddescent.trial_eval import trial_evaluate
from ddescent.trial_task import cue_delay_probe

CODE_VERSION = "trial-arm-v1-D121fix"


def cfg_hash(args):
    payload = dict(pop=args.pop, gens=args.gens, delay=args.delay, dev_ms=args.dev_ms,
                   assays=args.assays, code_version=CODE_VERSION,
                   net=dict(gain=SC.NET["input_gain"], noise=SC.NET["noise_sigma"],
                            nmda=SC.NET["nmda_frac"], wta=SC.NET["wta_gain"],
                            dev_ee_stdp=SC.NET["dev_ee_stdp"], dev_wta_comp=SC.NET["dev_wta_comp"]),
                   trial=SC.TRIAL)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def preflight_gate(task, net_cfg, cfg, verbose=True):
    """Trial-task invariants that must hold before the arm runs. Returns (ok, detail)."""
    g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=7)

    # LEAKAGE (hard): destroying Y_test must not move the val-based fitness (D113).
    r1 = trial_evaluate(g, task, net_cfg, cfg)
    y_backup = task.Y_test.copy()
    task.Y_test = np.random.default_rng(0).normal(size=task.Y_test.shape)
    r2 = trial_evaluate(g, task, net_cfg, cfg)
    task.Y_test = y_backup
    leak_delta = abs(r1["trial_score"] - r2["trial_score"])
    leak_ok = leak_delta < 1e-9

    # CONTROLS (report): on a random genome all should sit ~chance; they MUST NOT exceed chance.
    kw = {k: v for k, v in SC.TRIAL.items() if k != "seed"}
    accs = {}
    for label, extra in [("normal", {}), ("omit_cue", dict(omit_cue=True)),
                         ("scramble", dict(scramble=True))]:
        t = cue_delay_probe(seed=0, **{**kw, **extra})
        accs[label] = float(trial_evaluate(g, t, net_cfg, cfg, report=False)["val_acc"])
    ctrl_ok = accs["omit_cue"] <= 0.65 and accs["scramble"] <= 0.65   # random genome => near chance

    if verbose:
        print("PRE-ARM GATE")
        print("  leakage: |Δfitness| when Y_test destroyed = %.2e  -> %s"
              % (leak_delta, "PASS" if leak_ok else "FAIL"))
        print("  controls (random genome): normal=%.3f omit_cue=%.3f scramble=%.3f  -> %s"
              % (accs["normal"], accs["omit_cue"], accs["scramble"],
                 "ok (not above chance)" if ctrl_ok else "SUSPICIOUS (above chance)"))
    return (leak_ok and ctrl_ok), dict(leak_delta=leak_delta, controls=accs)


def climb_metrics(history):
    ft = np.array([h.get("fit_mean", np.nan) for h in history])
    bt = np.array([h["best_test"] for h in history])
    k = max(3, (2 * len(ft)) // 3); x = np.arange(k)
    slope = float(np.polyfit(x, ft[-k:], 1)[0]) if len(ft) >= k and np.all(np.isfinite(ft[-k:])) else 0.0
    return dict(fit_slope=slope, fit_start=float(ft[0]), fit_end=float(ft[-1]),
                best_test_start=float(bt[0]), best_test_end=float(bt[-1]), best_test_min=float(bt.min()))


def post_arm_controls(best_genome, net_cfg, cfg):
    """The DECISIVE control test: on the EVOLVED best, omit_cue and scramble must fall to chance
    while 'normal' is (ideally) above it. Reported, not gated (a first arm may not climb)."""
    kw = {k: v for k, v in SC.TRIAL.items() if k != "seed"}
    out = {}
    for label, extra in [("normal", {}), ("omit_cue", dict(omit_cue=True)),
                         ("scramble", dict(scramble=True))]:
        t = cue_delay_probe(seed=1, **{**kw, **extra})
        out[label] = float(trial_evaluate(best_genome, t, net_cfg, cfg, report=False)["val_acc"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=30)
    ap.add_argument("--gens", type=int, default=40)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--delay", type=int, default=SC.TRIAL["delay_segments"])
    ap.add_argument("--dev-ms", type=float, default=SC.trial_dev_ms())
    ap.add_argument("--assays", type=int, default=SC.N_ASSAYS)
    ap.add_argument("--out", default="runs/trial_arm")
    ap.add_argument("--skip-gate", action="store_true")
    args = ap.parse_args()
    out_dir = pathlib.Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    h = cfg_hash(args)
    ckpt = out_dir / f"trial_delay{args.delay}_pop{args.pop}_gens{args.gens}.json"

    with tee("trial_selection_run", log_dir=str(out_dir),
             header=f"TRIAL ARM: cue->delay->probe XOR; pop={args.pop} gens={args.gens} "
                    f"delay={args.delay} workers={args.workers} hash={h}"):
        if ckpt.exists():
            try:
                prev = json.loads(ckpt.read_text())
                if prev.get("config_hash") == h:
                    print(f"[skip] {ckpt.name} (hash matches)"); return
                print(f"[rerun] {ckpt.name} (config/code changed)")
            except Exception:
                print(f"[rerun] {ckpt.name} (unreadable checkpoint)")

        task    = SC.make_trial_task(delay_segments=args.delay)
        net_cfg = SC.make_net_cfg()
        cfg     = SC.make_trial_evolve_cfg(pop_size=args.pop, n_generations=args.gens,
                                           dev_ms=args.dev_ms, n_assays=args.assays)
        print(SC.trial_summary())
        hr = task.headroom()
        print(f"floor(NMSE)={hr['memoryless_floor']:.3f} ceiling={hr['oracle_ceiling']:.3f} "
              f"chance_acc={hr['chance_accuracy']:.3f}\n")

        if not args.skip_gate:
            ok, detail = preflight_gate(task, net_cfg, cfg)
            if not ok:
                print("\nGATE FAILED — aborting before the arm (would produce scored garbage).")
                (out_dir / "_gate_FAILED.json").write_text(json.dumps(detail, indent=2, default=str))
                sys.exit(1)
            print("gate PASS\n")

        t0 = time.time()
        print(f"[arm] START pop={args.pop} gens={args.gens} workers={args.workers} "
              f"dev_ms={args.dev_ms:.0f} n_assays={args.assays}", flush=True)
        history, pop = run_evolution(
            task, net_cfg, cfg,
            eval_fn      = lambda g: trial_evaluate(g, task, net_cfg, cfg),
            report_fn    = lambda g: trial_evaluate(g, task, net_cfg, cfg, report=True),
            worker_scorer= "trial",
            n_workers    = args.workers, verbose=True)
        secs = round(time.time() - t0, 1)

        m = climb_metrics(history)
        # DECISIVE post-arm control test on the current best genome
        fits = np.array([trial_evaluate(g, task, net_cfg, cfg)["trial_score"] for g in pop])
        best = pop[int(np.argmax(fits))]
        m["post_arm_controls"] = post_arm_controls(best, net_cfg, cfg)
        m.update(dict(config_hash=h, code_version=CODE_VERSION, pop=args.pop, gens=args.gens,
                      delay=args.delay, dev_ms=args.dev_ms, n_assays=args.assays,
                      workers=args.workers, seconds=secs,
                      timestamp=datetime.datetime.now().isoformat(),
                      history=history))
        ckpt.write_text(json.dumps(m, indent=2, default=str))

        print("\n" + "=" * 78)
        print("TRIAL ARM — did it climb?")
        print("=" * 78)
        print(f"  fit_slope={m['fit_slope']:+.5f} | fit {m['fit_start']:.4f}->{m['fit_end']:.4f} "
              f"| best_test {m['best_test_start']:.3f}->{m['best_test_end']:.3f} (min {m['best_test_min']:.3f})")
        c = m["post_arm_controls"]
        print(f"  POST-ARM CONTROLS (decisive): normal={c['normal']:.3f} "
              f"omit_cue={c['omit_cue']:.3f} scramble={c['scramble']:.3f}")
        print("  => a genuine solution has normal ABOVE chance while omit_cue and scramble STAY at 0.5")
        print(f"\n{secs}s -> {ckpt}")


if __name__ == "__main__":
    main()
