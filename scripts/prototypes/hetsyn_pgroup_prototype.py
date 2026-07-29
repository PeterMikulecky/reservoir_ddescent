"""Prototype: P-group synaptic timescales. P=1 homogeneous ... P=|W| full HetSyn.

Implementation: P synaptic current variables per neuron, each with its own tau; every synapse is
assigned to a group and deposits into that group's current. P=2 reproduces the existing I_fast/I_slow
structure exactly, so the current substrate is the P=2 point on this axis.
"""
import warnings, time; warnings.filterwarnings("ignore")
import numpy as np, brian2 as b2
from brian2 import ms
b2.prefs.codegen.target="numpy"; b2.BrianLogger.suppress_name('resolution_conflict')

def build_eqs(P):
    cur = " + ".join("I%d" % k for k in range(P))
    lines = ["dv/dt = (-v + %s + bias)/tau_m + noise*sqrt(2/tau_m)*xi : 1 (unless refractory)" % cur]
    lines += ["dI%d/dt = -I%d/tau%d : 1" % (k,k,k) for k in range(P)]
    lines += ["dr/dt = -r/tau_r : 1"]
    return "\n".join(lines)

def run_dmts(N=30, P=2, taus=None, K=2, delay_ms=400, n_trials=96, seed=0, per_cat=None, noise=0.3):
    """DMTS: K cue categories on separate channels; hidden cells tuned to a category.
    Synapse group assignment: cue synapses -> group 0 (long tau), probe -> group 1 (short tau)."""
    rng=np.random.default_rng(seed)
    if taus is None: taus=[500.0,5.0]+[50.0]*(P-2)
    per_cat = per_cat or max(2, N//K)
    CUE,PROBE,RATE=100,100,40.0
    T=CUE+delay_ms+PROBE
    cue=rng.integers(0,K,n_trials); probe=rng.integers(0,K,n_trials)
    rel=(cue==probe).astype(int)
    out=np.zeros((n_trials,N))
    ns=dict(tau_m=20*ms,tau_r=30*ms,bias=0.0,noise=noise)
    for k,t_ in enumerate(taus[:P]): ns["tau%d"%k]=t_*ms
    for t in range(n_trials):
        b2.start_scope()
        G=b2.NeuronGroup(N,build_eqs(P),threshold="v>1",reset="v=0; r+=1",
                         refractory=2*ms,method="euler",namespace=ns)
        def spikes(t0,t1,rate,nch):
            ii,tt=[],[]
            for ch in range(nch):
                m=max(1,rng.poisson(rate*(t1-t0)/1000.0))
                tt+=list(rng.uniform(t0,t1,size=m)); ii+=[ch]*m
            ii=np.array(ii); tt=np.round(np.array(tt),1)
            _,keep=np.unique(np.stack([ii,tt]),axis=1,return_index=True)
            ii,tt=ii[keep],tt[keep]; o=np.argsort(tt); return ii[o],tt[o]
        nch=8
        ci,ct=spikes(1.0,CUE,RATE,nch); pi,pt=spikes(T-PROBE,T-1.0,RATE,nch)
        CU=b2.SpikeGeneratorGroup(nch,ci,ct*ms); PR=b2.SpikeGeneratorGroup(nch,pi,pt*ms)
        ctg=np.arange(cue[t]*per_cat,min(N,(cue[t]+1)*per_cat))
        ptg=np.arange(probe[t]*per_cat,min(N,(probe[t]+1)*per_cat))
        Sc=b2.Synapses(CU,G,on_pre="I0 += 0.9")                       # cue -> group 0
        Sc.connect(i=np.repeat(np.arange(nch),len(ctg)),j=np.tile(ctg,nch))
        tgt_probe = "I0" if P==1 else "I1"                            # P=1: no separate timescale
        Sp=b2.Synapses(PR,G,on_pre="%s += 0.9"%tgt_probe)             # probe -> group 1
        Sp.connect(i=np.repeat(np.arange(nch),len(ptg)),j=np.tile(ptg,nch))
        M=b2.StateMonitor(G,"r",record=True,dt=5*ms)
        b2.run(T*ms)
        out[t]=M.r[:,-12:].mean(1)
    return out,rel

def dec(X,y):
    n=len(y); f=np.arange(n)<n//2; e=~f
    Z=(X-X[f].mean(0))/(X[f].std(0)+1e-9)
    A=np.hstack([Z[f],np.ones((f.sum(),1))])
    c,*_=np.linalg.lstsq(A,y[f]*2.0-1,rcond=None)
    p=np.hstack([Z[e],np.ones((e.sum(),1))])@c
    return float(np.mean((p>0)==(y[e]>0)))

print("STEP 2: isolating the noise level (step 1 had NO noise and reached 0.917)")
print("  noise | P=1 (homogeneous) | P=2 (long/short) | s/eval")
for nz in (0.0,0.1,0.3):
    a=dec(*run_dmts(N=30,P=1,taus=[100.0],seed=1,noise=nz))
    t0=time.time(); X,y=run_dmts(N=30,P=2,taus=[500.0,5.0],seed=1,noise=nz); el=time.time()-t0
    b=dec(X,y)
    print("  %.1f   |      %.3f        |      %.3f       | %.3f%s"
          % (nz,a,b,el/len(y),"   <-- separates" if b>a+0.15 else ""))
