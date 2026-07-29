"""Which change between step 1 (0.917) and the step 2 prototype (0.52) broke it?"""
import warnings, sys; warnings.filterwarnings("ignore")
sys.path.insert(0,'/tmp')
import numpy as np
import importlib.util
spec=importlib.util.spec_from_file_location("hs","/tmp/hetsyn.py")
# don't exec module-level prints; re-import pieces manually
import brian2 as b2
from brian2 import ms
b2.prefs.codegen.target="numpy"; b2.BrianLogger.suppress_name('resolution_conflict')

def run(N, per_cat, nch, weight, n_trials=96, delay_ms=400, seed=1, noise=0.0, tl=500.0, ts=5.0):
    rng=np.random.default_rng(seed); K=2
    CUE,PROBE,RATE=100,100,40.0; T=CUE+delay_ms+PROBE
    cue=rng.integers(0,K,n_trials); probe=rng.integers(0,K,n_trials)
    rel=(cue==probe).astype(int); out=np.zeros((n_trials,N))
    for t in range(n_trials):
        b2.start_scope()
        eqs="""dv/dt = (-v + I0 + I1)/tau_m : 1 (unless refractory)
               dI0/dt = -I0/tau0 : 1
               dI1/dt = -I1/tau1 : 1
               dr/dt  = -r/tau_r : 1"""
        G=b2.NeuronGroup(N,eqs,threshold="v>1",reset="v=0; r+=1",refractory=2*ms,method="euler",
                         namespace=dict(tau_m=20*ms,tau0=tl*ms,tau1=ts*ms,tau_r=30*ms))
        def sp(t0,t1,nc):
            ii,tt=[],[]
            for ch in range(nc):
                m=max(1,int(RATE*(t1-t0)/1000))
                tt+=list(rng.uniform(t0,t1,size=m)); ii+=[ch]*m
            ii=np.array(ii); tt=np.round(np.array(tt),1)
            _,k=np.unique(np.stack([ii,tt]),axis=1,return_index=True)
            ii,tt=ii[k],tt[k]; o=np.argsort(tt); return ii[o],tt[o]
        ci,ct=sp(1.0,CUE,nch); pi,pt=sp(T-PROBE,T-1.0,nch)
        CU=b2.SpikeGeneratorGroup(nch,ci,ct*ms); PR=b2.SpikeGeneratorGroup(nch,pi,pt*ms)
        ctg=np.arange(cue[t]*per_cat,(cue[t]+1)*per_cat)
        ptg=np.arange(probe[t]*per_cat,(probe[t]+1)*per_cat)
        Sc=b2.Synapses(CU,G,on_pre="I0 += w",namespace=dict(w=weight))
        Sc.connect(i=np.repeat(np.arange(nch),len(ctg)),j=np.tile(ctg,nch))
        Sp=b2.Synapses(PR,G,on_pre="I1 += w",namespace=dict(w=weight))
        Sp.connect(i=np.repeat(np.arange(nch),len(ptg)),j=np.tile(ptg,nch))
        M=b2.StateMonitor(G,"r",record=True,dt=5*ms); b2.run(T*ms)
        out[t]=M.r[:,-12:].mean(1)
    return out,rel

def dec(X,y):
    n=len(y); f=np.arange(n)<n//2; e=~f
    Z=(X-X[f].mean(0))/(X[f].std(0)+1e-9)
    A=np.hstack([Z[f],np.ones((f.sum(),1))])
    c,*_=np.linalg.lstsq(A,y[f]*2.0-1,rcond=None)
    return float(np.mean(((np.hstack([Z[e],np.ones((e.sum(),1))])@c)>0)==(y[e]>0)))

print(" config                          | acc   | mean r | frac cells saturated")
for lbl,N,pc,nch,w in (("step1-like N=24 pc=12 nch=10",24,12,10,0.9),
                       ("N=30 pc=15 nch=10",           30,15,10,0.9),
                       ("N=30 pc=15 nch=8",            30,15, 8,0.9),
                       ("N=30 pc=15 nch=8 w=0.3",      30,15, 8,0.3)):
    X,y=run(N,pc,nch,w)
    sat=float(np.mean(X.std(0)<1e-9))
    print(" %-31s | %.3f | %.3f  | %.2f" % (lbl,dec(X,y),X.mean(),sat))
