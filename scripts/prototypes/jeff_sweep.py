"""Sweep J_eff toward 1 at inhibition ratio 1, with 100 ms bins. Does tau respond AT ALL?"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
import numpy as np
from ddescent import study_config as SC
from ddescent.evonet import EvoNet, random_genome

GAIN = 6.60                       # measured df/dI, Hz per unit current
DT   = 100.0                      # 100 ms bins: ~80 population spikes/bin (CV 0.11) vs ~8 at 10 ms
NSTEP= 120                        # 12 s per run
RATIO= 1.0                        # J_eff/radius = 3.41 at r=1, so J_eff->1 stays deeply ordered

def acorr(x):
    x=np.asarray(x,float)-np.mean(x)
    if x.std()<1e-12: return None
    c=np.correlate(x,x,'full')[len(x)-1:]; return c/c[0]

nc0=SC.make_net_cfg(N=100,n_in=10)
per_syn = GAIN*nc0.tau_syn/1000.0        # loop gain per unit weight
CE,CI = 24.6,5.8
# J_eff_rate = wE*(CE - CI*RATIO)*per_syn  ->  solve for wE
print("bins=%.0f ms  ratio=%.1f  loop gain/weight=%.4f  (predicted tau = tau_slow/(1-J_eff))" 
      % (DT,RATIO,per_syn))
print("  J_eff | wE     | radius_rate | tau_pred | ac(100) ac(200) ac(400) ac(800) | TAU | Hz")
rows=[]
for target in (0.0, 0.50, 0.75, 0.90, 0.95):
    if target==0.0:
        wE=0.0; lbl="0 (no rec)"
    else:
        wE=target/((CE-CI*RATIO)*per_syn); lbl="%.2f"%target
    A=[];rs=[];rad=[];jr=[]
    for s in range(2):
        w0 = 1e-9 if wE==0 else wE/np.sqrt(2/np.pi)
        nc=SC.make_net_cfg(N=100,n_in=10,present_ms=DT,readout_window_ms=DT)
        g=random_genome(nc,0.3,w0=w0,ei_split=0.8,inh_gain=RATIO,seed=1+s)
        W=g.mag*g.signs[np.newaxis,:]
        rad.append(np.abs(np.linalg.eigvals(W)).max()*per_syn); jr.append(W.sum(1).mean()*per_syn)
        S=EvoNet(g,nc).behave(np.zeros((NSTEP,nc.n_in)),noise_seed=100+s)["state"]
        c=acorr(S.mean(1))
        if c is not None: A.append(c)
        rs.append(float(S.mean()*1000.0/nc.tau_r))
    if not A: print("  %-6s | silent"%lbl); continue
    c=np.mean(A,0); J=np.mean(jr)
    tp = nc0.tau_slow/(1-J) if J<1 else np.inf
    b=np.where(c<np.exp(-0.5))[0]; tm=b[0]*DT if len(b) else NSTEP*DT
    g_=lambda ms:(c[int(ms/DT)] if int(ms/DT)<len(c) else np.nan)
    print("  %-6s| %.3f  |    %.3f    | %7s |  %+.2f   %+.2f   %+.2f   %+.2f  | %4.0f| %.1f"
          % (lbl,wE,np.mean(rad),("%.0f"%tp) if np.isfinite(tp) else "inf",
             g_(100),g_(200),g_(400),g_(800),tm,np.mean(rs)))
print("\n  radius_rate stays < 1 throughout at ratio 1, so none of these is chaotic.")
print("  If TAU does not rise as J_eff -> 0.95, the rate-model mechanism does not transfer.")
