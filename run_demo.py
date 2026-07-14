"""Small end-to-end demo: sweep -> results.csv (written incrementally)."""
import itertools, time, csv, os
import numpy as np
from ddescent.connectivity import ConnectivityConfig, make_recurrent_weights, make_input_weights, _spectral_radius
from ddescent.reservoir import ReservoirConfig, LIFReservoir
from ddescent.measures import participation_ratio, effective_rank, intrinsic_dim_of_inputs
from ddescent import readout as ro
from ddescent import tasks as T

OUT = "results_demo.csv"
N = 200
densities = (0.05, 0.2, 0.6)
radii = (0.7, 1.5)
seeds = (0, 1)
Kdim = 10

grid = list(itertools.product(densities, radii, seeds))
fields = ["density","spectral_radius_target","spectral_radius_measured","seed",
          "synapse_count","log_synapse_count","pr","effective_rank","env_intrinsic_dim",
          "train_err","test_err","novel_err","gen_gap","weight_norm","N"]
with open(OUT,"w",newline="") as f:
    csv.DictWriter(f, fieldnames=fields).writeheader()

t0=time.time()
for i,(density,rho,seed) in enumerate(grid):
    cc=ConnectivityConfig(N=N,density=density,spectral_radius=rho,seed=seed)
    W=make_recurrent_weights(cc)
    Win=make_input_weights(N,Kdim,seed=seed+100)
    res=LIFReservoir(W,Win,ReservoirConfig(N=N,seed=seed+200,noise_sigma=0.05,
                                           present_ms=120,readout_window_ms=50,sample_ms=15))
    task=T.anisotropic_regression(K=Kdim,n_train=50,n_test=50,n_high=3,seed=seed)
    task.U_train_feat=res.run_static(task.U_train)
    task.U_test_feat=res.run_static(task.U_test)
    task.U_novel_feat=res.run_static(task.U_novel)
    pr=participation_ratio(task.U_train_feat)
    perf=ro.evaluate_regression(ro.LinearReadout(alpha=0.0),task)
    row=dict(density=density,spectral_radius_target=rho,
             spectral_radius_measured=round(_spectral_radius(W),3),seed=seed,
             synapse_count=cc.synapse_count(),
             log_synapse_count=round(float(np.log10(max(cc.synapse_count(),1))),4),
             pr=round(pr,3),effective_rank=effective_rank(task.U_train_feat),
             env_intrinsic_dim=round(intrinsic_dim_of_inputs(task.U_train),3),
             train_err=round(perf["train_err"],4),test_err=round(perf["test_err"],4),
             novel_err=round(perf["novel_err"],4),gen_gap=round(perf["gen_gap"],4),
             weight_norm=round(perf["weight_norm"],3),N=N)
    with open(OUT,"a",newline="") as f:
        csv.DictWriter(f,fieldnames=fields).writerow(row)
    print(f"[{i+1}/{len(grid)}] p={density:.2f} rho={rho:.1f} s={seed} "
          f"PR={pr:6.1f} test={perf['test_err']:.3f} novel={perf['novel_err']:.3f} "
          f"({time.time()-t0:.0f}s)")
print("done", round(time.time()-t0,1),"s")
