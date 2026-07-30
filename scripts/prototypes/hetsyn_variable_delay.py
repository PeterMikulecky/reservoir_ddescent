"""Does VARIABLE DELAY create genuine demand for multiple timescales?

The test: sweep P=1 over tau under 1, 2 and 3 distinct delays. If P=1's BEST ceiling falls as delays are
added while P=2/P=3 hold up, the task creates the demand the design argument claims. If a single tau
still reaches ~0.85 with three delays, it does not, and variable delay is the wrong lever.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, brian2 as b2
from brian2 import ms
b2.prefs.codegen.target="numpy"; b2.BrianLogger.suppress_name('resolution_conflict')

def run(P, taus, delays, w=0.3, N=30, per_cat=15, nch=8, n_trials=144, seed=1):
    rng=np.random.default_rng(seed); K=2
    CUE,PROBE,RATE=100,100,40.0
    cue=rng.integers(0,K,n_trials); probe=rng.integers(0,K,n_trials)
    dsel=rng.integers(0,len(delays),n_trials)
    rel=(cue==probe).astype(int); out=np.zeros((n_trials,N))
    cur=" + ".join("I%d"%k for k in range(P))
    eqs="\n".join(["dv/dt = (-v + %s)/tau_m : 1 (unless refractory)"%cur]
                  +["dI%d/dt = -I%d/tau%d : 1"%(k,k,k) for k in range(P)]
                  +["dr/dt = -r/tau_r : 1"])
    ns=dict(tau_m=20*ms,tau_r=30*ms)
    for k,t_ in enumerate(taus): ns["tau%d"%k]=t_*ms
    for t in range(n_trials):
        D=delays[dsel[t]]; T=CUE+D+PROBE
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
        out[t]=M.r[:,-12:].mean(1)
    return out,rel

def dec(X,y,seeds=3):
    n=len(y); acc=[]
    for s in range(seeds):
        idx=np.random.default_rng(s).permutation(n); f=idx[:n//2]; e=idx[n//2:]
        Z=(X-X[f].mean(0))/(X[f].std(0)+1e-9)
        A=np.hstack([Z[f],np.ones((len(f),1))])
        c,*_=np.linalg.lstsq(A,y[f]*2.0-1,rcond=None)
        acc.append(np.mean(((np.hstack([Z[e],np.ones((len(e),1))])@c)>0)==(y[e]>0)))
    return float(np.mean(acc))

print("Does adding DELAYS lower the P=1 ceiling? (w=0.3, N=30, chance 0.500)")
print("  delays          | P=1 best (tau)      | P=2 (500,5) | P=3 (500,150,5)")
for delays in ([400],[200,800],[200,400,800]):
    best,bt=0,None
    for tau in (100.,250.,400.,600.):
        a=dec(*run(1,[tau],delays))
        if a>best: best,bt=a,tau
    p2=dec(*run(2,[500.,5.],delays))
    p3=dec(*run(3,[500.,150.,5.],delays))
    print("  %-15s |   %.3f (tau=%3.0f)   |    %.3f    |     %.3f"
          % (str(delays),best,bt,p2,p3))
print("\n  If P=1's best FALLS as delays are added while P>1 holds, variable delay creates the demand.")
