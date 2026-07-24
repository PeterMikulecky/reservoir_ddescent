"""FITNESS RELIABILITY PROBE (post-D113/D114). Is the fitness signal noise-dominated, and would
averaging help?

MOTIVATION. D109 found aggregate fitness non-heritable (r~0). Three candidate causes are on the table:
  (a) SUBSTRATE roughness — rugged genotype→phenotype map (queue N2 tests this),
  (b) ARCHITECTURE scrambling — development/selection destroying transmission,
  (c) MEASUREMENT NOISE — the fitness estimate for a single genome is so noisy that there is nothing
      stable to inherit.
PJM's point: in a flat, at-the-floor region the signal is almost BOUND to be noise-dominated — how could
it not be? True, but "noise-dominated" has two separable causes, and they call for opposite responses:
  * NO TRUE SIGNAL (flat landscape)  -> averaging cannot help; you must change the landscape (density/P).
  * REAL BUT SMALL SIGNAL swamped by measurement error -> averaging DOES help.

THE TEST (free, thanks to the D113 three-way split). `evaluate()` now returns val_err and test_err: two
INDEPENDENT estimates of the same genome's generalisation. Their correlation across a population is a
split-half RELIABILITY of the fitness signal:
    reliability = corr(val_err, test_err)  across genomes
Repeat at n_assays = 1, 2, 4:
  * reliability ~0 and FLAT in n_assays          -> (a)/(b): no true between-genome signal to average up.
  * reliability LOW at 1 but CLIMBING with n_assays -> (c): real signal, measurement-noise-limited.
                                                       n_assays is a cheap lever; it raises realised h²
                                                       (h² = V_g/(V_g+V_e+V_m)) and hence selection response.

Also reports a variance decomposition: between-genome variance vs the val-test discrepancy variance
(a proxy for measurement variance), and the implied heritability ceiling.

D102-logged; writes under runs/ (all outputs live there). n>=30 per the standing statistical rule.

Usage: python fitness_reliability_probe.py [--n 30] [--assays 1 2 4]
"""
import sys, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings
warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, random_genome
from ddescent.evolve import EvolveConfig, evaluate, assert_no_test_leakage
from ddescent import tasks as T


def net_config():
    return EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                        present_ms=50, tau_slow=100.0, nmda_frac=0.5,
                        dev_ee_stdp=True, dev_wta_comp=True, wta_gain=1.0)


def measure(task, n_genomes, n_assays, seed0=4000):
    """Return (val_err, test_err) arrays across genomes at this n_assays."""
    net_cfg = net_config()
    cfg = EvolveConfig(pop_size=n_genomes, n_generations=1, dev_ms=800.0, dev_eta=1e-3,
                       n_assays=n_assays, fitness_beta=5.0, seed=seed0,
                       fitness_mode="regulation_only")
    cfg._gen = 0
    va, te = [], []
    for i in range(n_genomes):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed0 + i)
        r = evaluate(g, task, net_cfg, cfg)
        va.append(r["val_err"]); te.append(r["test_err"])
    return np.array(va), np.array(te)


def report(n_assays, va, te):
    r = float(np.corrcoef(va, te)[0, 1]) if va.std() > 1e-12 and te.std() > 1e-12 else float("nan")
    # variance decomposition: total observed spread vs the val-test discrepancy
    v_total = float(np.var(np.concatenate([va, te])))
    v_disc = float(np.var(va - te) / 2.0)          # per-measurement noise variance estimate
    v_true = max(0.0, v_total - v_disc)            # implied true between-genome variance
    h2_ceiling = v_true / v_total if v_total > 0 else float("nan")
    print(f"  n_assays={n_assays}: reliability r(val,test) = {r:+.3f}")
    print(f"      SD(val)={va.std():.4f}  SD(test)={te.std():.4f}  SD(val-test)={np.std(va-te):.4f}")
    print(f"      implied true-signal fraction (heritability ceiling) = {h2_ceiling:.3f}")
    return dict(n_assays=n_assays, r=r, sd_val=float(va.std()), sd_test=float(te.std()),
                sd_disc=float(np.std(va - te)), h2_ceiling=float(h2_ceiling))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--assays", type=int, nargs="+", default=[1, 2, 4])
    args = ap.parse_args()

    with tee("fitness_reliability_probe",
             header="Is the fitness signal noise-dominated, and would averaging help? (val-vs-test reliability)"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4,
                                           n_train=60, n_val=60, n_test=60,
                                           context_dwell=10, seed=0)
        assert_no_test_leakage(task)          # D113 guard
        print(f"n_genomes={args.n}, n_assays sweep={args.assays}")
        print("val_err and test_err are INDEPENDENT estimates of the same genome's generalisation.\n")
        rows = []
        for k in args.assays:
            va, te = measure(task, args.n, k)
            rows.append(report(k, va, te))
            print()

        print("=" * 72)
        print("VERDICT")
        print("=" * 72)
        r0 = rows[0]["r"]; rN = rows[-1]["r"]
        for row in rows:
            print(f"  n_assays={row['n_assays']:>2}  r={row['r']:+.3f}  h2_ceiling={row['h2_ceiling']:.3f}")
        print()
        if np.isnan(r0):
            print("=> DEGENERATE: no spread in one of the estimates. Investigate before interpreting.")
        elif rN > r0 + 0.15:
            print("=> (c) MEASUREMENT-NOISE-LIMITED: reliability CLIMBS with averaging, so a real")
            print("   between-genome signal exists and is being swamped. n_assays is a cheap lever —")
            print("   it raises realised h2 and therefore the response to selection. Raise n_assays")
            print("   before spending compute on longer/stronger selection runs.")
        elif rN < 0.2:
            print("=> (a)/(b) NO RECOVERABLE SIGNAL: reliability stays ~0 even with averaging, so there is")
            print("   little true between-genome variance to find here. Averaging cannot help. The fix is")
            print("   to CHANGE THE LANDSCAPE (density/P sweep) or the substrate (queue N2), not to")
            print("   measure the current one more precisely.")
        else:
            print("=> INTERMEDIATE: some real signal, partly noise-limited. Averaging helps but is not")
            print("   sufficient on its own; pursue both n_assays and a landscape change.")


if __name__ == "__main__":
    main()
