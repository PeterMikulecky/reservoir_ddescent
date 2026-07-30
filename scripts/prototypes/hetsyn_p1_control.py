"""THE GATING CONTROL: is the P=2 advantage real at the GOOD operating point (w=0.3)?

D139 reported 0.583 (P=1) vs 0.917 (P=2) -- but that was measured at w=0.9, where D140 showed the cells
saturate. If P=1 also reaches ~0.98 at w=0.3, the mechanism claim collapses and the outline fails here.

P=1 is given the SAME total drive and its single tau is swept, so it gets every chance: no single
timescale should do what two do, and the sweep shows whether that holds or whether we simply picked a
bad tau for the homogeneous case.
"""
import warnings, time; warnings.filterwarnings("ignore")
import numpy as np, brian2 as b2
from brian2 import ms
b2.prefs.codegen.target="numpy"; b2.BrianLogger.suppress_name('resolution_conflict')

def run(P, taus, w=0.3, N=30, per_cat=15, nch=8, n_trials=120, delay_ms=400, seed=1):
    rng=np.random.default_rng(seed); K=2
    CUE,PROBE,RATE=100,100,40.0; T=CUE+delay_ms+PROBE
    cue=rng.integers(0,K,n_trials); probe=rng.integers(0,K,n_trials)
    rel=(cue==probe).astype(int); out=np.zeros((n_trials,N)); rates=[]
    cur=" + ".join("I%d"%k for k in range(P))
    eqs="\n".join(["dv/dt = (-v + %s)/tau_m : 1 (unless refractory)"%cur]
                  +["dI%d/dt = -I%d/tau%d : 1"%(k,k,k) for k in range(P)]
                  +["dr/dt = -r/tau_r : 1"])
    ns=dict(tau_m=20*ms,tau_r=30*ms)
    for k,t_ in enumerate(taus): ns["tau%d"%k]=t_*ms
    for t in range(n_trials):
        b2.start_scope()
        G=b2.NeuronGroup(N,eqs,threshold="v>1",reset="v=0; r+=1",refractory=2*ms,
                         method="euler",namespace=ns)
        def sp(t0,t1):
            ii,tt=[],[]
            for ch in range(nch):
                m=max(1,int(RATE*(t1-t0)/1000))
                tt+=list(rng.uniform(t0,t1,size=m)); ii+=[ch]*m
            ii=np.array(ii); tt=np.round(np.array(tt),1)
            _,k=np.unique(np.stack([ii,tt]),axis=1,return_index=True)
            ii,tt=ii[k],tt[k]; o=np.argsort(tt); return ii[o],tt[o]
        ci,ct=sp(1.0,CUE); pi,pt=sp(T-PROBE,T-1.0)
        CU=b2.SpikeGeneratorGroup(nch,ci,ct*ms); PR=b2.SpikeGeneratorGroup(nch,pi,pt*ms)
        ctg=np.arange(cue[t]*per_cat,(cue[t]+1)*per_cat)
        ptg=np.arange(probe[t]*per_cat,(probe[t]+1)*per_cat)
        Sc=b2.Synapses(CU,G,on_pre="I0 += w",namespace=dict(w=w))
        Sc.connect(i=np.repeat(np.arange(nch),len(ctg)),j=np.tile(ctg,nch))
        tgt="I0" if P==1 else "I1"
        Sp=b2.Synapses(PR,G,on_pre="%s += w"%tgt,namespace=dict(w=w))
        Sp.connect(i=np.repeat(np.arange(nch),len(ptg)),j=np.tile(ptg,nch))
        M=b2.StateMonitor(G,"r",record=True,dt=5*ms); b2.run(T*ms)
        out[t]=M.r[:,-12:].mean(1); rates.append(float(M.r[:,-12:].mean()))
    return out,rel,float(np.mean(rates))

def dec(X,y,seeds=3):
    """held-out linear decode, averaged over train/test partitions"""
    n=len(y); acc=[]
    for s in range(seeds):
        idx=np.random.default_rng(s).permutation(n); f=idx[:n//2]; e=idx[n//2:]
        Z=(X-X[f].mean(0))/(X[f].std(0)+1e-9)
        A=np.hstack([Z[f],np.ones((len(f),1))])
        c,*_=np.linalg.lstsq(A,y[f]*2.0-1,rcond=None)
        acc.append(np.mean(((np.hstack([Z[e],np.ones((len(e),1))])@c)>0)==(y[e]>0)))
    return float(np.mean(acc))

print("THE CONTROL, at the GOOD operating point w=0.3, 400 ms delay, N=30 (chance 0.500)")
print("  condition                        | accuracy | mean r")
for lbl,P,taus in (("P=1  tau=5",1,[5.0]), ("P=1  tau=100",1,[100.0]),
                   ("P=1  tau=250",1,[250.0]), ("P=1  tau=500",1,[500.0]),
                   ("P=2  tau=(500, 5)  HET",2,[500.0,5.0])):
    X,y,r=run(P,taus); print("  %-32s |  %.3f   | %.3f" % (lbl,dec(X,y),r))
print("\n  P=1 is swept over tau so it gets every chance. If any P=1 matches P=2, the claim fails.")
