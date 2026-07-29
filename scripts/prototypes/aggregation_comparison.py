import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
import numpy as np
from ddescent import study_config as SC
from ddescent.evonet import EvoNet, random_genome
from task_screen import make_accumulate, r_null

nc = SC.make_net_cfg(N=100, n_in=10); cfg = SC.make_trial_evolve_cfg(); dens=0.3
E, y, rows, _ = make_accumulate(300, nc.n_in, seed=1)
ch = r_null(150)
n = len(y); fit = np.arange(n) < n//2; te = ~fit

def per_neuron(S):
    """Each neuron: 2-param affine fitted on the FIT half, prediction on the TEST half."""
    P = np.empty((te.sum(), S.shape[1]))
    for j in range(S.shape[1]):
        A = np.vstack([S[fit,j], np.ones(fit.sum())]).T
        c,*_ = np.linalg.lstsq(A, y[fit], rcond=None)
        P[:,j] = S[te,j]*c[0] + c[1]
    return P

def r(p): 
    return 0.0 if p.std()<1e-12 else abs(np.corrcoef(p, y[te])[0,1])

print("chance |r| = %.3f  (held-out, n_test=%d)\n" % (ch, te.sum()))
print(" g | mean-of-SCORES | mean-of-PREDICTIONS | driven-only preds | designated")
print(" --+----------------+---------------------+-------------------+-----------")
ms, mp, dp, de = [], [], [], []
for gi in range(6):
    g = random_genome(nc, dens, w0=SC.w0_for_density(dens), ei_split=cfg.ei_split, seed=1+gi)
    S = EvoNet(g, nc).behave(E, noise_seed=100)["state"][rows]
    P = per_neuron(S)
    sc = np.array([r(P[:,j]) for j in range(P.shape[1])])
    ms.append(sc.mean()); mp.append(r(P.mean(1))); dp.append(r(P[:,:nc.n_in].mean(1)))
    de.append(sc[nc.N-nc.d])
    print(" %d |     %.3f%s      |       %.3f%s       |      %.3f%s      |   %.3f%s"
          % (gi, ms[-1],"*" if ms[-1]>ch else " ", mp[-1],"*" if mp[-1]>ch else " ",
             dp[-1],"*" if dp[-1]>ch else " ", de[-1],"*" if de[-1]>ch else " "))
print("\n mean over genomes: scores %.3f | predictions %.3f | driven-only %.3f | designated %.3f"
      % (np.mean(ms), np.mean(mp), np.mean(dp), np.mean(de)))
print(" between-genome sd: scores %.3f | predictions %.3f | driven-only %.3f"
      % (np.std(ms,ddof=1), np.std(mp,ddof=1), np.std(dp,ddof=1)))
print("\n * = above chance. Averaging PREDICTIONS uses fixed 1/N weights -- no fitted")
print(" combination across neurons, so D095's capacity bound is untouched.")
