"""STEP 1: does a per-SYNAPSE timescale split make match/non-match linearly decodable?

D128 measured the relation at chance for a linear readout on the full state. The HetSyn claim is that
a neuron receiving "then" through a LONG-tau synapse and "now" through a SHORT-tau synapse becomes a
coincidence detector -- no circuit required. This tests exactly that, minimally.

  HET  : cue channels -> I_slow (long tau);  probe channels -> I_fast (short tau)
  HOM  : cue AND probe -> the same current (our current substrate: one shared timescale)

Neuron j is tuned to category c(j): it receives the cue synapse for c(j) and the probe synapse for
c(j). On a MATCH the decaying cue trace and the fresh probe drive coincide on the same cell.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, brian2 as b2
from brian2 import ms
b2.prefs.codegen.target = "numpy"; b2.BrianLogger.suppress_name('resolution_conflict')

K, PER = 2, 12          # categories, neurons per category
NH = K*PER
CUE_MS, PROBE_MS, RATE = 100, 100, 40.0

def run_trials(delay_ms, mode, n_trials=120, tau_long=500.0, tau_short=5.0, seed=0):
    rng = np.random.default_rng(seed)
    cue = rng.integers(0, K, n_trials); probe = rng.integers(0, K, n_trials)
    rel = (cue == probe).astype(int)
    T = CUE_MS + delay_ms + PROBE_MS
    tl, ts = (tau_long, tau_short) if mode == "HET" else (100.0, 100.0)
    out = np.zeros((n_trials, NH))
    for t in range(n_trials):
        b2.start_scope()
        eqs = """dv/dt = (-v + I_s + I_f)/tau_m : 1
                 dI_s/dt = -I_s/tau_s : 1
                 dI_f/dt = -I_f/tau_f : 1
                 dr/dt  = -r/tau_r : 1"""
        G = b2.NeuronGroup(NH, eqs, threshold="v>1", reset="v=0; r+=1", refractory=2*ms,
                           method="euler", namespace=dict(tau_m=20*ms, tau_s=tl*ms,
                                                          tau_f=ts*ms, tau_r=30*ms))
        # cue input during [0, CUE_MS); probe input during the final PROBE_MS
        n_ch = 10
        def poisson(t0, t1, rate, n):
            """(idx, time) pairs, SORTED BY TIME as SpikeGeneratorGroup requires."""
            lam = rate*(t1-t0)/1000.0
            ii, tt = [], []
            for ch in range(n):
                k = max(1, rng.poisson(lam))
                tt += list(rng.uniform(t0, t1, size=k)); ii += [ch]*k
            ii = np.array(ii); tt = np.round(np.array(tt), 1)
            # SpikeGeneratorGroup rejects DUPLICATE (index, time) pairs, and rounding to the dt grid
            # creates them. Dedupe, then sort by time as it also requires.
            _, keep = np.unique(np.stack([ii, tt]), axis=1, return_index=True)
            ii, tt = ii[keep], tt[keep]
            o = np.argsort(tt)
            return ii[o], tt[o]
        ci, ct = poisson(1.0, CUE_MS, RATE, n_ch)
        pi, pt = poisson(T-PROBE_MS, T-1.0, RATE, n_ch)
        CU = b2.SpikeGeneratorGroup(n_ch, ci, ct*ms)
        PR = b2.SpikeGeneratorGroup(n_ch, pi, pt*ms)
        tgt = np.arange(cue[t]*PER, (cue[t]+1)*PER)      # cue drives its own category's cells
        ptg = np.arange(probe[t]*PER, (probe[t]+1)*PER)  # probe drives its own category's cells
        Sc = b2.Synapses(CU, G, on_pre="I_s += 0.9")     # CUE -> slow current in BOTH modes
        Sc.connect(i=np.repeat(np.arange(n_ch), len(tgt)), j=np.tile(tgt, n_ch))
        # THE ONLY DIFFERENCE: in HET the probe uses the FAST current, in HOM it shares the slow one.
        Sp = b2.Synapses(PR, G, on_pre=("I_f += 0.9" if mode == "HET" else "I_s += 0.9"))
        Sp.connect(i=np.repeat(np.arange(n_ch), len(ptg)), j=np.tile(ptg, n_ch))
        M = b2.StateMonitor(G, "r", record=True, dt=5*ms)
        b2.run(T*ms)
        out[t] = M.r[:, -12:].mean(1)     # last 60 ms
    return out, rel

def decode(X, y):
    n=len(y); fit=np.arange(n)<n//2; te=~fit
    Xz=(X-X[fit].mean(0))/(X[fit].std(0)+1e-9)
    A=np.hstack([Xz[fit], np.ones((fit.sum(),1))])
    c,*_=np.linalg.lstsq(A, y[fit]*2.0-1, rcond=None)
    p=np.hstack([Xz[te], np.ones((te.sum(),1))])@c
    return float(np.mean((p>0)==(y[te]>0)))

print("match/non-match LINEAR decodability at the read stage (chance 0.50)")
print("  delay | HOM (one shared tau) | HET (cue->slow, probe->fast)")
for d in (200, 400, 800):
    a=decode(*run_trials(d,"HOM",seed=1)); b=decode(*run_trials(d,"HET",seed=1))
    print("  %4d  |        %.3f         |        %.3f%s" % (d,a,b,"  <-- MECHANISM WORKS" if b>a+0.15 else ""))
