"""PRE-FLIGHT VALIDATION SUITE — run this before ANY multi-hour experiment.

WHY THIS EXISTS. Three separate bugs have invalidated multi-hour runs on this project:
  D112  "encoding" and "regulation" were the same measurement offset by a constant.
  D113  fitness was computed from TEST error, so selection optimised the reported generalisation.
  D116  the "memoryless floor" measured representational CAPACITY, not memorylessness — a static
        random tanh expansion beat it with no network, no dynamics and no context.
None of these needed a long run to find. All three were cheap STATIC checks we never ran. Our
validation had consistently confirmed that code EXECUTES (smoke tests, single-cell trials, checkpoint
writes) but never that it MEASURES WHAT IT CLAIMS. Those are different questions.

This suite asks the second question. It is designed to run in minutes and to encode every lesson the
project has already paid for. Run it before launching anything expensive.

CHECKS
  A  LEAKAGE (empirical)   perturb the reporting split; fitness MUST NOT change.
  B  COMPONENT REDUNDANCY  are the fitness components actually distinct measurements?
  C  FITNESS RELIABILITY   split-half reliability at the configured n_assays, with SE.
  D  FLOOR VALIDITY        is the "no context" reference a matched control, or capacity-confounded?
  E  READOUT POWER         how well do RANDOM networks score? (baseline for the evolved-vs-random audit)

Usage: python preflight.py [--n 12] [--assays 4]
Exit status is 0 if all checks PASS, 1 if any FAIL (so it can gate a launch script).
"""
import sys, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings
warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.evolve import (EvolveConfig, evaluate, _fitness, _affine_nmse,
                             context_destroyed_score, assert_no_test_leakage)
from ddescent.baseline import best_nmse
from ddescent import tasks as T

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results = []


def record(name, status, detail):
    results.append((name, status, detail))
    print(f"  [{status}] {name}: {detail}")


def net_config():
    return EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                        present_ms=50, tau_slow=100.0, nmda_frac=0.5,
                        dev_ee_stdp=True, dev_wta_comp=True, wta_gain=1.0)


def check_A_leakage(task, net_cfg, cfg):
    """Empirical proof that the reporting split does not feed selection: corrupt Y_test and confirm
    fitness is bit-identical. Stronger than any assertion about code structure."""
    print("\nA. LEAKAGE — does the REPORTING split influence fitness?")
    g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=1)
    f_before = _fitness(*(lambda r: (r, r["n_params"]))(evaluate(g, task, net_cfg, cfg)), cfg)
    Y_test_backup = task.Y_test.copy()
    task.Y_test = np.random.default_rng(0).normal(size=task.Y_test.shape) * 10.0   # destroy it
    f_after = _fitness(*(lambda r: (r, r["n_params"]))(evaluate(g, task, net_cfg, cfg)), cfg)
    task.Y_test = Y_test_backup
    if abs(f_before - f_after) < 1e-12:
        record("A leakage", PASS, f"fitness unchanged when Y_test destroyed ({f_before:.6f})")
    else:
        record("A leakage", FAIL,
               f"fitness CHANGED when Y_test destroyed: {f_before:.6f} -> {f_after:.6f}. "
               f"The reporting split is feeding selection (D113).")


def check_B_components(task, net_cfg, cfg, n):
    """Are the fitness components distinct measurements, or redundant transforms of one another?"""
    print("\nB. COMPONENT REDUNDANCY — are enc/car/reg distinct measurements?")
    enc, car, reg = [], [], []
    for i in range(n):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=200 + i)
        r = evaluate(g, task, net_cfg, cfg)
        enc.append(r["encoding"]); car.append(r["carrying"]); reg.append(r["regulation"])
    enc, car, reg = map(np.array, (enc, car, reg))
    pairs = [("encoding", "regulation", enc, reg), ("encoding", "carrying", enc, car),
             ("carrying", "regulation", car, reg)]
    worst = None
    for a, b, x, y in pairs:
        if x.std() < 1e-12 or y.std() < 1e-12:
            record(f"B {a} vs {b}", WARN, "one component has zero variance"); continue
        r_ = float(np.corrcoef(x, y)[0, 1])
        rng_ = float(np.ptp(x - y))
        status = FAIL if abs(r_) > 0.99 else PASS
        if status == FAIL:
            worst = (a, b, r_)
        record(f"B {a} vs {b}", status, f"r={r_:+.4f}, range(x-y)={rng_:.2e}"
               + ("  <-- REDUNDANT: same measurement up to a transform (D112)" if status == FAIL else ""))


def check_C_reliability(task, net_cfg, cfg, n):
    """Split-half reliability of the fitness signal at the CONFIGURED n_assays."""
    print(f"\nC. FITNESS RELIABILITY — at n_assays={cfg.n_assays} (D115)")
    va, te = [], []
    for i in range(n):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=300 + i)
        r = evaluate(g, task, net_cfg, cfg, report=True)
        va.append(r["val_err"]); te.append(r["test_err"])
    va, te = np.array(va), np.array(te)
    se = 1.0 / np.sqrt(max(n - 3, 1))
    r_ = float(np.corrcoef(va, te)[0, 1]) if va.std() > 1e-12 and te.std() > 1e-12 else float("nan")
    status = PASS if (not np.isnan(r_) and r_ > 2 * se) else FAIL
    record("C reliability", status,
           f"r(val,test)={r_:+.3f} +/-{se:.3f} at n_assays={cfg.n_assays}; "
           f"{'above' if status == PASS else 'NOT above'} 2 SE. "
           + ("" if status == PASS else "Selection would act largely on noise — raise n_assays."))


def check_D_floor(task, net_cfg, cfg, n_small=3):
    """Is the 'no context' reference a MATCHED control, or confounded by representational capacity?"""
    print("\nD. FLOOR VALIDITY — is the 'memoryless' reference capacity-confounded? (D116)")
    ht = task.headroom(split="test")
    floor_old = ht["memoryless_floor"]
    # a STATIC, memoryless, context-free random expansion of the same input
    rng = np.random.default_rng(0)
    Wr = rng.normal(size=(task.E_train.shape[1], net_cfg.N)) / np.sqrt(task.E_train.shape[1])
    Ftr, Fte = np.tanh(task.E_train @ Wr), np.tanh(task.E_test @ Wr)
    static = float(np.mean([best_nmse(Ftr, task.Y_train[:, k], Fte, task.Y_test[:, k],
                                      standardize=False)[0] for k in range(task.Y_train.shape[1])]))
    if static < floor_old:
        record("D old floor", FAIL,
               f"a STATIC random {net_cfg.N}-dim expansion scores {static:.4f}, BEATING the "
               f"'memoryless floor' {floor_old:.4f}. The floor measures CAPACITY, not memorylessness; "
               f"beating it does not demonstrate context inference.")
    else:
        record("D old floor", PASS, f"static expansion {static:.4f} does not beat floor {floor_old:.4f}")
    # the matched control: same network, context structure destroyed
    gains = []
    for i in range(n_small):
        net = EvoNet(random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=400 + i), net_cfg)
        net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms, warmup_ms=200.0, seed=400 + i, eta_e=5e-3)
        ordered = _affine_nmse(task.Y_test, net.behave(task.E_test, noise_seed=2)["rates"])
        destroyed = context_destroyed_score(net, task, split="test", noise_seed=2)
        gains.append(destroyed - ordered)
    g_mean = float(np.mean(gains))
    record("D matched control", PASS if abs(g_mean) > 1e-9 else WARN,
           f"context gain (destroyed - ordered) = {g_mean:+.4f} over {n_small} nets "
           f"({'networks USE context' if g_mean > 0.01 else 'NO measurable context use'})")


def check_E_readout_power(task, net_cfg, cfg, n):
    """Baseline: how well do RANDOM networks score? Evolved must beat this by a clear margin."""
    print("\nE. READOUT POWER — random-network baseline (D111)")
    fits = []
    for i in range(n):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=500 + i)
        r = evaluate(g, task, net_cfg, cfg)
        fits.append(_fitness(r, r["n_params"], cfg))
    fits = np.array(fits)
    record("E readout power", PASS,
           f"random fitness mean={fits.mean():.4f} sd={fits.std():.4f} max={fits.max():.4f} "
           f"(evolved must clearly exceed max={fits.max():.4f} to claim the NETWORK is contributing)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--assays", type=int, default=4)
    args = ap.parse_args()

    with tee("preflight", header="PRE-FLIGHT VALIDATION — do our measurements measure what they claim?"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4,
                                           n_train=60, n_val=60, n_test=60,
                                           context_dwell=10, seed=0)
        assert_no_test_leakage(task)
        net_cfg = net_config()
        cfg = EvolveConfig(pop_size=args.n, n_generations=1, dev_ms=800.0, dev_eta=1e-3,
                           n_assays=args.assays, fitness_beta=50.0, seed=999,
                           fitness_mode="regulation_only")
        cfg._gen = 0
        print(f"n={args.n} genomes, n_assays={args.assays}, fitness_mode={cfg.fitness_mode}")

        check_A_leakage(task, net_cfg, cfg)
        check_B_components(task, net_cfg, cfg, args.n)
        check_C_reliability(task, net_cfg, cfg, args.n)
        check_D_floor(task, net_cfg, cfg)
        check_E_readout_power(task, net_cfg, cfg, args.n)

        print("\n" + "=" * 74)
        n_fail = sum(1 for _, s, _ in results if s == FAIL)
        n_warn = sum(1 for _, s, _ in results if s == WARN)
        for name, status, _ in results:
            if status != PASS:
                print(f"  {status}: {name}")
        if n_fail:
            print(f"\n{n_fail} CHECK(S) FAILED — do not launch a long run until these are understood.")
            print("A failing check does not always mean 'stop': a KNOWN, DOCUMENTED failure that does")
            print("not affect the contrast you intend to measure may be acceptable. But it must be a")
            print("DECISION, recorded, not an oversight discovered afterwards.")
        else:
            print(f"\nALL CHECKS PASSED ({n_warn} warning(s)). Safe to launch.")
        return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
