"""SPARSE DENSITY SWEEP -- test PJM's quenching hypothesis (post-pilot queue A1/quenching).

The pilot showed train error stuck at the floor at ALL densities [0.2-0.8] AND development failing to
converge everywhere. Two readings:
  (mine, wrong) underparameterized -> need denser. But this MISPREDICTS: train error is FLAT across
     density; underparameterization would predict it FALLS as density rises. It doesn't.
  (PJM) too DENSE -> the network is pushed past the edge of chaos into a saturated/chaotic regime that
     can't cleanly represent signal OR develop a stable response -> flat train error + dev non-
     convergence, both explained by ONE cause. Predicts: going SPARSER should drop train error AND
     recover dev-convergence, and dense nets should show saturated/input-independent activity.

This sweep discriminates them. For each density (much sparser than the pilot, plus dense refs):
  1. train/test error after development (does it drop below floor when sparse?)
  2. dev convergence fraction (does development settle when sparse?)
  3. ACTIVITY REGIME: mean firing rate, and input-driven vs saturated (state variance explained by
     stimulus vs internal reverberation) -- the MECHANISM, not just the fitness symptom.

Logs all output to disk (D102).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings
warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.evolve import _affine_nmse, _carry_covdecay
from ddescent import tasks as T

DENSITIES = [0.02, 0.05, 0.1, 0.2, 0.4]     # sparse -> dense; pilot was [0.2,0.4,0.6,0.8]
N_NETS = 4                                   # genomes per density (average over draws)
DEV_MS = 800.0


def activity_regime(net, task, noise_seed=1):
    """Is the developed network's activity INPUT-DRIVEN or SATURATED/self-sustained? Returns mean
    firing rate and the fraction of state variance that tracks the stimulus (vs internal reverb)."""
    B = net.behave(task.E_test, noise_seed=noise_seed)
    state = B["state"]                       # (n_env, N)
    rates = B["rates"]
    mean_rate = float(np.mean(state))
    # input-drivenness: correlation of state with the stimulus that produced it. If state is dominated
    # by internal reverberation (saturated/chaotic), it tracks the input weakly; if input-driven, strongly.
    E = task.E_test
    # project state onto stimulus: R^2 of predicting state-per-env from the input (per-env mean input)
    try:
        from numpy.linalg import lstsq
        X = np.hstack([E, np.ones((len(E), 1))])
        pred, *_ = lstsq(X, state, rcond=None)
        resid = state - X @ pred
        r2 = 1.0 - (resid.var() / (state.var() + 1e-12))
    except Exception:
        r2 = float("nan")
    return mean_rate, float(r2)


def main():
    with tee("sparse_density_sweep",
             header="test quenching hypothesis: does going sparser drop train error + recover dev convergence?"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                           context_dwell=10, seed=0)
        floor = task.headroom()["memoryless_floor"]; ceil = task.headroom()["oracle_ceiling"]
        print(f"task floor={floor:.3f} ceiling={ceil:.3f}  (train err at floor = not learning; "
              f"below floor = learning)\n")
        print(f"{'density':>8} | {'train_err':>9} | {'test_err':>8} | {'dev_conv':>8} | "
              f"{'mean_rate':>9} | {'input_R2':>8}")
        print("-" * 66)

        rows = []
        for dens in DENSITIES:
            tr_errs, te_errs, convs, rates, r2s = [], [], [], [], []
            for gi in range(N_NETS):
                cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                                   present_ms=50, tau_slow=100.0, nmda_frac=0.5)
                g = random_genome(cfg, dens, w0=0.6, seed=gi)
                net = EvoNet(g, cfg)
                dev = net.develop(task.E_train, eta=1e-3, dev_ms=DEV_MS, warmup_ms=200.0,
                                  n_checkpoints=4, seed=gi)
                convs.append(1.0 if dev.get("converged", False) else 0.0)
                Btr = net.behave(task.E_train, noise_seed=gi + 1)
                Bte = net.behave(task.E_test, noise_seed=gi + 2)
                tr_errs.append(_affine_nmse(task.Y_train, Btr["rates"]))
                te_errs.append(_affine_nmse(task.Y_test, Bte["rates"]))
                mr, r2 = activity_regime(net, task, noise_seed=gi + 3)
                rates.append(mr); r2s.append(r2)
            row = dict(density=dens, train_err=np.mean(tr_errs), test_err=np.mean(te_errs),
                       dev_conv=np.mean(convs), mean_rate=np.mean(rates), input_r2=np.mean(r2s))
            rows.append(row)
            print(f"{dens:>8} | {row['train_err']:>9.3f} | {row['test_err']:>8.3f} | "
                  f"{row['dev_conv']:>8.2f} | {row['mean_rate']:>9.3f} | {row['input_r2']:>8.3f}")

        print("\n" + "=" * 66)
        print("READING THE RESULT (quenching hypothesis test):")
        print("=" * 66)
        tr = np.array([r["train_err"] for r in rows])
        cv = np.array([r["dev_conv"] for r in rows])
        r2 = np.array([r["input_r2"] for r in rows])
        # does train error drop at sparse densities?
        best_i = int(np.argmin(tr))
        print(f"lowest train error at density={rows[best_i]['density']} "
              f"(err {tr[best_i]:.3f} vs floor {floor:.3f})")
        if tr[best_i] < floor - 0.03 and rows[best_i]['density'] < 0.2:
            print("  => train error DROPS at sparse density -> QUENCHING SUPPORTED (we were too dense).")
        elif np.ptp(tr) < 0.03:
            print("  => train error FLAT across all densities incl. sparse -> quenching NOT the (only) "
                  "cause; learning capped by something else (dev, selection, task).")
        else:
            print("  => mixed; inspect the trend.")
        # does dev convergence recover when sparse?
        print(f"dev convergence: sparse({rows[0]['density']})={cv[0]:.2f} vs "
              f"dense({rows[-1]['density']})={cv[-1]:.2f}", end="  ")
        print("-> recovers when sparse (density/dynamics problem)" if cv[0] > cv[-1] + 0.25
              else "-> does NOT recover when sparse (duration problem or other)")
        # activity regime
        print(f"input-drivenness (R2): sparse={r2[0]:.3f} vs dense={r2[-1]:.3f}", end="  ")
        print("-> sparse more input-driven, dense more saturated (quenching signature)"
              if r2[0] > r2[-1] + 0.1 else "-> no clear input-driven/saturated split by density")

        import pandas as pd
        out = pathlib.Path("analysis_logs") / "sparse_sweep_results.csv"
        pd.DataFrame(rows).to_csv(out, index=False)
        print(f"\nresults table -> {out}")


if __name__ == "__main__":
    main()
