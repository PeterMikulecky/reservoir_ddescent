"""Does PROBE-ALIGNED readout restore P=2 under variable delay? (D141's provisional attribution)

D141 found P=2 collapsing 0.963 -> 0.509 across delays [200,800] and attributed it to a timescale
mismatch (cue trace 0.67 vs 0.20 at the two delays). But the readout was the last 60 ms of the TRIAL,
which under variable delay falls at a different absolute time per trial -- a confound that was never
excluded. Probe-aligned readout removes it: read at a fixed lag after PROBE OFFSET, which is the natural
choice anyway since a response follows the probe.

If P=2 recovers, the collapse was a readout artifact and D141's mechanism claim must be withdrawn.
If it persists, the attribution stands.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, brian2 as b2
from brian2 import ms
b2.prefs.codegen.target="numpy"; b2.BrianLogger.suppress_name('resolution_conflict')

def run(P, taus, delays, align="probe", w=0.3, N=30, per_cat=15, nch=8, n_trials=144, seed=1):
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
    T_MAX=CUE+max(delays)+PROBE
    for t in range(n_trials):
        D=delays[dsel[t]]
        # run every trial to the SAME absolute duration so the readout window is comparable;
        # the probe simply occurs earlier on short-delay trials.
        probe_on = CUE + D
        T = T_MAX
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
        ci,ct=sp(1.0,CUE); pi,pt=sp(probe_on,probe_on+PROBE-1.0)
        CU=b2.SpikeGeneratorGroup(nch,ci,ct*ms); PR=b2.SpikeGeneratorGroup(nch,pi,pt*ms)
        ctg=np.arange(cue[t]*per_cat,(cue[t]+1)*per_cat)
        ptg=np.arange(probe[t]*per_cat,(probe[t]+1)*per_cat)
        # CUE synapses distributed across the MEMORY groups (all but the last); PROBE on the last (fast).
        mem = list(range(max(1,P-1)))
        for gi,grp in enumerate(mem):
            sub = ctg[gi::len(mem)]
            if len(sub)==0: continue
            S=b2.Synapses(CU,G,on_pre="I%d += w"%grp,namespace=dict(w=w))
            S.connect(i=np.repeat(np.arange(nch),len(sub)),j=np.tile(sub,nch))
            globals()['_keep_%d'%gi]=S
        fast = P-1 if P>1 else 0
        Sp=b2.Synapses(PR,G,on_pre="I%d += w"%fast,namespace=dict(w=w))
        Sp.connect(i=np.repeat(np.arange(nch),len(ptg)),j=np.tile(ptg,nch))
        M=b2.StateMonitor(G,"r",record=True,dt=5*ms); b2.run(T*ms)
        if align=="probe":
            i1=int((probe_on+PROBE)/5.0); i0=max(0,i1-12)     # 60 ms after PROBE OFFSET
        else:
            i1=M.r.shape[1]; i0=i1-12                          # last 60 ms of the TRIAL
        out[t]=M.r[:,i0:i1].mean(1)
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

print("Probe-aligned vs trial-end readout, delays [200,800] (chance 0.500)")
print("  P | taus              | trial-end | PROBE-ALIGNED")
for P,taus in ((1,[250.]),(2,[500.,5.]),(3,[800.,250.,5.])):
    a=dec(*run(P,taus,[200,800],align="end")); b=dec(*run(P,taus,[200,800],align="probe"))
    print("  %d | %-17s |   %.3f   |    %.3f" % (P,str(taus),a,b))
print("\n  P=3 now distributes CUE synapses over groups 0 and 1 (800 ms, 250 ms) with the probe on")
print("  group 2 (5 ms) -- the assignment fix. Previously group 2 was never used.")
