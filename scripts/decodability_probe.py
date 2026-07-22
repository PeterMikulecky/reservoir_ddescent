"""DECODABILITY-DISTRIBUTION PROBE (D107 follow-up). Tests PJM's funnel hypothesis at the POPULATION
level: competition may act as an undifferentiated FUNNEL (lowering mean across-stimulus response
variability), but under (A) selection acts on the DISTRIBUTION across genomes. So the question is not
"does one funnel preserve input info" but "does competition produce a DISTRIBUTION of decodability whose
SPREAD + UPPER TAIL give selection usable raw material?"

For each of {baseline, eSTDP-only, eSTDP+competition}, across a population of genomes, develop and
measure INPUT-DECODABILITY from the developed state (is the raw material selection needs still there?):
  - stimulus reconstruction: how well the state linearly recovers the input E (1 - nmse)
  - context decodability: how well the state recovers the latent context C (the thing the task needs)
Report per-condition MEAN, SPREAD (SD across genomes), and UPPER TAIL (best genome) -- because selection
climbs the tail. Hypothesis (PJM): competition may LOWER MEAN (funnel) but produce SPREAD + a strong
UPPER TAIL = the heritable variation the pilot lacked, in the functional dimension we care about.
Logged (D102). input-decodability (not task-target) = the "substrate preserved" signature.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings; warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.baseline import best_nmse
from ddescent import tasks as T

N_GENOMES = 30
DEV_MS = 800.0

def input_decodability(net, task, seed):
    """Can the developed state recover the latent context C? CRITICAL (tasks.py): every context is
    MEAN-ZERO; contexts differ ONLY in COVARIANCE. So a LINEAR decoder on the state mean is blind by
    construction. We decode from SECOND-ORDER (covariance) features of the state: per-sample squared
    and cross-product features capture the covariance structure context actually lives in.
    Returns (linear_ctx_acc, cov_ctx_acc): the linear one is the (expected-blind) control; the
    covariance one is the real measure."""
    Btr = net.behave(task.E_train, noise_seed=seed + 1)
    Bte = net.behave(task.E_test, noise_seed=seed + 2)
    Str, Ste = Btr["state"], Bte["state"]
    ctx = np.unique(task.C_train)
    ctx_idx = {c: i for i, c in enumerate(ctx)}
    ytr_i = np.array([ctx_idx[c] for c in task.C_train])
    yte_i = np.array([ctx_idx[c] for c in task.C_test])

    def _decode(Xtr, Xte, lam=1.0):
        """one-vs-rest ridge, return test accuracy."""
        Xtr = (Xtr - Xtr.mean(0)) / (Xtr.std(0) + 1e-8)
        Xte = (Xte - Xte.mean(0)) / (Xte.std(0) + 1e-8)
        Xtr = np.hstack([Xtr, np.ones((len(Xtr), 1))]); Xte = np.hstack([Xte, np.ones((len(Xte), 1))])
        preds = np.zeros((len(Xte), len(ctx)))
        for ci, c in enumerate(ctx):
            y = (task.C_train == c).astype(float)
            w = np.linalg.solve(Xtr.T @ Xtr + lam * np.eye(Xtr.shape[1]), Xtr.T @ y)
            preds[:, ci] = Xte @ w
        return float(np.mean(np.argmax(preds, axis=1) == yte_i))

    # (1) LINEAR decoder (control -- expected blind since contexts are mean-zero)
    lin_acc = _decode(Str, Ste)
    # (2) COVARIANCE-aware: per-sample second-order features. To keep dims manageable, project state to
    # its top-q PCs (fit on train), then use squared + pairwise-product features of those PCs -- these
    # capture the second-order structure context lives in.
    q = 8
    Xc = Str - Str.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    P = Vt[:q].T                      # (N, q) projection to top-q PCs
    Ztr = Str @ P; Zte = Ste @ P      # (n, q)
    def second_order(Z):
        feats = [Z**2]                # squared terms (variance along each PC)
        for a in range(q):
            for b in range(a + 1, q):
                feats.append((Z[:, a] * Z[:, b])[:, None])   # cross terms (covariance)
        return np.hstack(feats)
    cov_acc = _decode(second_order(Ztr), second_order(Zte))
    return lin_acc, cov_acc

def run_condition(ee, wta, label, task):
    cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                       present_ms=50, tau_slow=100.0, nmda_frac=0.5, dev_ee_stdp=ee, dev_wta_comp=wta,
                       wta_gain=1.0)
    lins, covs = [], []
    for gi in range(N_GENOMES):
        net = EvoNet(random_genome(cfg, 0.3, w0=0.6, seed=gi), cfg)
        net.develop(task.E_train, eta=1e-3, dev_ms=DEV_MS, warmup_ms=200.0, n_checkpoints=4,
                    seed=1000 + gi, eta_e=5e-3)
        lin, cov = input_decodability(net, task, seed=1000 + gi)
        lins.append(lin); covs.append(cov)
    lins, covs = np.array(lins), np.array(covs)
    chance = 1.0 / len(np.unique(task.C_test))
    print(f"\n[{label}] N={N_GENOMES} genomes (chance={chance:.3f}):")
    print(f"  LINEAR ctx-decode (control, expected-blind): mean={lins.mean():.3f} SD={lins.std():.3f} tail={lins.max():.3f}")
    print(f"  COVARIANCE ctx-decode (the real measure):    mean={covs.mean():.3f} SD={covs.std():.3f} tail={covs.max():.3f}")
    return dict(lin=lins, cov=covs)

def main():
    with tee("decodability_distribution_probe",
             header="does competition produce a DISTRIBUTION of input-decodability (spread+tail) selection can use?"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                           context_dwell=10, seed=0)
        base = run_condition(False, False, "baseline (no dev plasticity)", task)
        estdp = run_condition(True, False, "eSTDP only", task)
        comp = run_condition(True, True, "eSTDP + dev-competition", task)

        print("\n" + "=" * 70)
        print("VERDICT (PJM funnel-distribution hypothesis)")
        print("=" * 70)
        print(f"stimulus-decodability SPREAD (SD across genomes):")
        print(f"  baseline={base['stim'].std():.3f}  eSTDP={estdp['stim'].std():.3f}  comp={comp['stim'].std():.3f}")
        print(f"context-decodability SPREAD + TAIL:")
        print(f"  baseline: SD={base['acc'].std():.3f} tail={base['acc'].max():.3f}")
        print(f"  eSTDP:    SD={estdp['acc'].std():.3f} tail={estdp['acc'].max():.3f}")
        print(f"  comp:     SD={comp['acc'].std():.3f} tail={comp['acc'].max():.3f}")
        print()
        # is competition producing usable spread/tail even if mean funnels?
        comp_spread_up = comp['stim'].std() > estdp['stim'].std()*1.3 or comp['acc'].std() > estdp['acc'].std()*1.3
        comp_tail_up = comp['acc'].max() > estdp['acc'].max()+0.03 or comp['stim'].max() > estdp['stim'].max()+0.03
        if comp_spread_up or comp_tail_up:
            print("=> competition produces SPREAD and/or a stronger UPPER TAIL in decodability across")
            print("   genomes -- the funnel is a SUBSTRATE (usable variation for selection), not a dead")
            print("   end. Even if mean funnels, selection lives off the distribution. GREEN to selection.")
        else:
            print("=> competition does NOT increase decodability spread or tail over eSTDP-alone. The")
            print("   funnel may be homogenizing to mush (suppression, not usable variation). Investigate")
            print("   competition strength / joint tuning vs beta before selection.")

if __name__ == "__main__":
    main()
