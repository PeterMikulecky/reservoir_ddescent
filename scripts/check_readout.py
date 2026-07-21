"""Can the KNOWN-GOOD engineered ceiling beat the memoryless floor through our fitness readout
(_affine_nmse, D095)? If NOT, the readout is the bottleneck (nothing could beat the floor), not the
evolution. Existence-proof logic (PJM). Logged per D102."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings; warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.evolve import _affine_nmse
from ddescent.engineered_ceiling import build_regulation_ceiling, build_engineered_ceiling
from ddescent import tasks as T

with tee("readout_bottleneck_check",
         header="can the known-good ceiling beat the floor through _affine_nmse? if not, readout is the cap"):
    task = T.hierarchical_environments(K=10,d=3,r1=3,n_contexts=4,n_train=60,n_test=60,context_dwell=10,seed=0)
    floor = task.headroom()["memoryless_floor"]; ceil = task.headroom()["oracle_ceiling"]
    print(f"task floor={floor:.3f} ceiling={ceil:.3f}")
    print("floor = best memoryless NMSE; ceiling = best context-aware NMSE. Beating floor = using context.\n")

    # the engineered regulation ceiling is wired for its OWN cue/probe protocol, not the task's E->Y.
    # But we can still ask: does ANY structured network beat the floor through _affine_nmse on the task?
    # Test 1: a random developed net (baseline - should sit at floor)
    cfg = EvoNetConfig(N=50,n_in=10,d=3,bias=0.6,input_gain=10.0,noise_sigma=1.0,present_ms=50,tau_slow=100.0,nmda_frac=0.5)
    g = random_genome(cfg, 0.3, w0=0.6, seed=0); net = EvoNet(g, cfg)
    B = net.behave(task.E_test, noise_seed=1)
    print(f"random net, _affine_nmse (per-output affine, D095): {_affine_nmse(task.Y_test, B['rates']):.3f}")

    # Test 2: what does the readout look like if we give it MORE capacity? Full ridge on the whole state.
    # This tells us whether the SIGNAL is in the network but the affine readout can't reach it.
    from ddescent.baseline import best_nmse
    full = best_nmse(net.behave(task.E_train,noise_seed=1)['state'], task.Y_train,
                     B['state'], task.Y_test, standardize=True)[0]
    print(f"random net, FULL ridge on whole state (uncapped readout): {full:.3f}")
    print("  if full-ridge ALSO ~floor -> the signal isn't in the state (network isn't computing it)")
    print("  if full-ridge << floor but affine ~floor -> the AFFINE readout is the bottleneck\n")

    # Test 3: the oracle -- fit a SEPARATE affine per context. If even per-context affine can't beat
    # floor, the rates truly carry no context. If it can, context IS in the rates, readout just can't
    # use it single-channel.
    Btr = net.behave(task.E_train, noise_seed=1)
    errs=[]; 
    for c in np.unique(task.C_test):
        mtr, mte = task.C_train==c, task.C_test==c
        if mtr.sum()<5 or mte.sum()<2: continue
        e=_affine_nmse(task.Y_test[mte], Bte_r[mte]) if False else None
    # simpler: per-context full ridge (oracle upper bound through the state)
    oracle_errs=[]
    for c in np.unique(task.C_test):
        mtr, mte = task.C_train==c, task.C_test==c
        if mtr.sum()<5 or mte.sum()<2: continue
        e=best_nmse(Btr['state'][mtr], task.Y_train[mtr], B['state'][mte], task.Y_test[mte], standardize=True)[0]
        oracle_errs.append(e*mte.sum())
    print(f"random net, per-context ORACLE (state, context given): {sum(oracle_errs)/(task.C_test>=0).sum():.3f}")
    print("  << floor => the network state DOES separate by context (info is there, readout/selection problem)")
    print("  ~floor   => the state does NOT carry usable task info at all (deeper representation problem)")
