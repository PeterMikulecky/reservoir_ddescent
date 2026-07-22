"""D109 TEST #1: NONLINEAR decodability of the developed state (tests the regulation-is-substrate-native
reframe's FOUNDATION). The reframe claims the stimulus/context is ALREADY present in the network's
distributed, nonlinear, fluctuating dynamics -- just not in the ORDERED LINEAR format our earlier probes
(linear ridge, covariance-linear) decoded for, which came back at chance. Prediction (from the deep-
learning support, D109 #2): a genuinely NONLINEAR decoder should recover context where LINEAR decoders
could not. If so, every prior "encoding at floor / context not decodable" result is reinterpreted as a
decoder-FORMAT artifact, not an absence of information.

Method: develop a population of networks; from each developed state (n_test x N), decode the latent
CONTEXT C with a ladder of decoders of increasing nonlinearity, all cross-validated the same way:
  (0) chance                      -- baseline
  (1) linear ridge (one-vs-rest)  -- the ORDERED-FORMAT decoder that found chance before
  (2) linear SVM                  -- linear, different regularization
  (3) covariance-linear           -- 2nd-order features + linear (the D-series probe)
  (4) RBF-SVM                     -- genuinely nonlinear
  (5) kNN                         -- nonlinear, nonparametric, local
  (6) random forest               -- nonlinear, axis-aligned partitions
Report mean accuracy across genomes for each, vs chance. Reframe SUPPORTED if nonlinear (4-6) >> linear
(1-2) and > covariance (3). Reframe NOT supported if all decoders ~chance (info truly absent) or if
linear already = nonlinear (info is in linear format, contradicting our earlier nulls -> re-check those).
Logged (D102). Held with discipline: this tests the FOUNDATION, not the whole reframe.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings; warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent import tasks as T
from sklearn.svm import SVC, LinearSVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

N_GENOMES = 12
DEV_MS = 800.0

def cov_features(X, q=8):
    """2nd-order features: project to top-q PCs, then squares + pairwise products (the D-series form)."""
    Xc = X - X.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    Z = X @ Vt[:q].T
    feats = [Z, Z**2]
    for a in range(q):
        for b in range(a+1, q):
            feats.append((Z[:, a]*Z[:, b])[:, None])
    return np.hstack(feats)

DECODERS = {
    "1 linear-ridge":  lambda: make_pipeline(StandardScaler(), RidgeClassifier()),
    "2 linear-SVM":    lambda: make_pipeline(StandardScaler(), LinearSVC(max_iter=5000)),
    "4 RBF-SVM":       lambda: make_pipeline(StandardScaler(), SVC(kernel="rbf", C=5, gamma="scale")),
    "5 kNN(5)":        lambda: make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
    "6 randomforest":  lambda: RandomForestClassifier(n_estimators=100, max_depth=None),
}

def decode_all(state, y, cov=None):
    """cross-val accuracy for each decoder on (state -> context y). cov=precomputed cov features."""
    out = {}
    for name, mk in DECODERS.items():
        try:
            out[name] = float(cross_val_score(mk(), state, y, cv=4).mean())
        except Exception as e:
            out[name] = float("nan")
    # covariance-linear as its own entry
    try:
        out["3 cov-linear"] = float(cross_val_score(make_pipeline(StandardScaler(), RidgeClassifier()), cov, y, cv=4).mean())
    except Exception:
        out["3 cov-linear"] = float("nan")
    return out

def run_condition(wta, task, label):
    cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                       present_ms=50, tau_slow=100.0, nmda_frac=0.5, dev_ee_stdp=True,
                       dev_wta_comp=(wta > 0), wta_gain=max(wta, 1e-9))
    acc = {k: [] for k in list(DECODERS) + ["3 cov-linear"]}
    for gi in range(N_GENOMES):
        net = EvoNet(random_genome(cfg, 0.3, w0=0.6, seed=gi), cfg)
        net.develop(task.E_train, eta=1e-3, dev_ms=DEV_MS, warmup_ms=200.0, n_checkpoints=4,
                    seed=1000+gi, eta_e=5e-3)
        st = net.behave(task.E_test, noise_seed=2)["state"]
        cov = cov_features(st)
        res = decode_all(st, task.C_test, cov=cov)
        for k, v in res.items():
            acc[k].append(v)
    chance = 1.0/len(np.unique(task.C_test))
    print(f"\n[{label}] N={N_GENOMES} genomes, chance={chance:.3f}")
    order = ["1 linear-ridge","2 linear-SVM","3 cov-linear","4 RBF-SVM","5 kNN(5)","6 randomforest"]
    for k in order:
        v = np.array(acc[k]); print(f"  {k:16s}: mean={np.nanmean(v):.3f}  SD={np.nanstd(v):.3f}  best={np.nanmax(v):.3f}")
    lin = np.nanmean(acc["1 linear-ridge"]); nl = np.nanmax([np.nanmean(acc[k]) for k in ["4 RBF-SVM","5 kNN(5)","6 randomforest"]])
    print(f"  --> linear={lin:.3f}  best-nonlinear={nl:.3f}  lift={nl-lin:+.3f}  (vs chance {chance:.3f})")
    return acc

def main():
    with tee("nonlinear_decodability_probe",
             header="D109 test#1: is context NONLINEARLY decodable where LINEAR decoders found chance?"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                           context_dwell=10, seed=0)
        a_off = run_condition(0.0, task, "eSTDP only (comp OFF)")
        a_on  = run_condition(1.0, task, "eSTDP + competition (comp ON)")
        ch = 1.0/len(np.unique(task.C_test))
        print("\n" + "="*70 + "\nVERDICT (reframe foundation: nonlinear >> linear?)\n" + "="*70)
        for lab, a in [("comp OFF", a_off), ("comp ON", a_on)]:
            lin = np.nanmean(a["1 linear-ridge"]); cov = np.nanmean(a["3 cov-linear"])
            nl = np.nanmax([np.nanmean(a[k]) for k in ["4 RBF-SVM","5 kNN(5)","6 randomforest"]])
            print(f"  {lab}: linear={lin:.3f}  cov-linear={cov:.3f}  best-nonlinear={nl:.3f}  chance={ch:.3f}")
            if nl > ch + 0.08 and nl > lin + 0.05:
                print(f"    => SUPPORTED: context IS nonlinearly decodable ({nl:.3f}) above chance and above linear.")
                print(f"       Prior 'encoding at floor' was a DECODER-FORMAT artifact. Info is present-but-distributed.")
            elif nl <= ch + 0.05 and lin <= ch + 0.05:
                print(f"    => NOT supported: all decoders ~chance. Info may truly be absent (not just mis-formatted).")
            else:
                print(f"    => AMBIGUOUS: modest nonlinear lift; needs larger n / stronger decoders.")

if __name__ == "__main__":
    main()
