import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
import numpy as np
from ddescent import study_config as SC
from ddescent.evonet import EvoNet, random_genome
def acorr(x):
    x=np.asarray(x,float)-np.mean(x)
    if x.std()<1e-12: return None
    c=np.correlate(x,x,'full')[len(x)-1:]; return c/c[0]
DT=10.0; NSTEP=400   # 10 ms resolution, non-overlapping windows, 4 s per run
print("Spontaneous activity, %.0f ms sampling (present=readout=%.0f ms), %.1f s" % (DT,DT,NSTEP*DT/1000))
print("NOTE: tau_r=30 ms filters the trace, so ~30 ms is an intrinsic FLOOR regardless of network.\n")
print("  config          | radius | J_eff  | tau_pred | ac(50ms) ac(100) ac(200) ac(400) | TAU_meas | Hz")
for lbl,wE,ig in (("CURRENT (D058)",None,None),("target ratio 2",0.058,2.0),("no recurrence",0.0,2.0)):
    nc=SC.make_net_cfg(N=100,n_in=10,present_ms=DT,readout_window_ms=DT)
    if wE is None: w0=SC.w0_for_density(0.3); ig_use=None
    elif wE==0.0: w0=1e-9; ig_use=ig
    else: w0=wE/np.sqrt(2/np.pi); ig_use=ig
    A=[];rs=[];rad_=[];je_=[]
    for s in range(2):
        g=random_genome(nc,0.3,w0=w0,ei_split=0.8,inh_gain=ig_use,seed=1+s)
        W=g.mag*g.signs[np.newaxis,:]
        rad_.append(np.abs(np.linalg.eigvals(W)).max()); je_.append(W.sum(1).mean())
        S=EvoNet(g,nc).behave(np.zeros((NSTEP,nc.n_in)),noise_seed=100+s)["state"]
        c=acorr(S.mean(1))
        if c is not None: A.append(c)
        rs.append(float(S.mean()*1000.0/nc.tau_r))
    if not A: print("  %-15s | silent" % lbl); continue
    c=np.mean(A,0); je=np.mean(je_)
    tp=nc.tau_slow/(1-je) if je<1 else np.inf
    b=np.where(c<np.exp(-0.5))[0]; tm=b[0]*DT if len(b) else NSTEP*DT
    def at(ms): 
        i=int(ms/DT); return c[i] if i<len(c) else np.nan
    print("  %-15s | %6.2f | %+.3f | %8s |  %.2f    %.2f    %.2f    %.2f  | %5.0f ms | %.1f"
          % (lbl,np.mean(rad_),je,("%.0f"%tp) if np.isfinite(tp) else "unstab",
             at(50),at(100),at(200),at(400),tm,np.mean(rs)))
print("\n  'no recurrence' is the FLOOR: tau_r filter + tau_m only. Target must EXCEED it.")
