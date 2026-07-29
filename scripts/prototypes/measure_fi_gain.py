import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
import numpy as np
from ddescent import study_config as SC
from ddescent.evonet import EvoNet, random_genome
# measure df/dI: perturb the constant bias, read the change in firing rate
nc0=SC.make_net_cfg(N=100,n_in=10)
print("f-I gain of our neurons (the factor Beiran & Ostojic's J includes and I omitted)")
print("  bias  | rate Hz")
rates={}
for b in (0.5,0.6,0.7):
    nc=SC.make_net_cfg(N=100,n_in=10,bias=b)
    g=random_genome(nc,0.3,w0=1e-9,ei_split=0.8,inh_gain=2.0,seed=1)   # no recurrence: isolated neurons
    S=EvoNet(g,nc).behave(np.zeros((120,nc.n_in)),noise_seed=100)["state"]
    rates[b]=float(S.mean()*1000.0/nc.tau_r)
    print("  %.2f  | %.2f" % (b,rates[b]))
gain=(rates[0.7]-rates[0.5])/0.2
print("\n  df/dI = %.2f Hz per unit current" % gain)
print("  a spike adds w to v, contributing w*(tau_syn/tau_m) of sustained current per Hz of input")
eff = gain*nc0.tau_syn/1000.0
print("  so rate-model J = w * df/dI * (tau_syn/1000) = w * %.4f per synapse" % eff)
print()
for lbl,wE,ig in (("CURRENT",0.482,3.84),("target ratio 2",0.058,2.0)):
    CE,CI=24.6,5.8
    Jrow = CE*wE - CI*wE*ig
    Jrate = Jrow*eff
    print("  %-15s row-sum J=%+.3f -> RATE-MODEL J_eff=%+.4f -> tau=%.0f ms"
          % (lbl,Jrow,Jrate, nc0.tau_slow/(1-Jrate) if Jrate<1 else -1))
print("\n  the row-sum is NOT the rate-model J_eff; the gain factor is what D138 omitted.")
