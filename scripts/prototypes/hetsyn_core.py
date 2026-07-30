"""hetsyn_core.py - the SINGLE source of the HetSyn block-runner and decoder.

Extracted 2026-07-29 after two prototypes with apparently-identical synapse construction diverged
invisibly: `hetsyn_probe_aligned.py` stashed synapses in `globals()` (which Brian2's magic collection
scans) and worked, while `hetsyn_tau_sweep.py` appended them to a LIST (which it does not) and silently
ran every trial with NO CUE INPUT for an entire 80-job run. Duplicated simulation code is how that
happened; everything downstream now imports from here.

`run_block` uses an EXPLICIT `b2.Network(*objs)` rather than magic collection, plus an assertion on the
synapse count that fails at construction rather than after the run.

Conventions fixed here:
  * P groups of synaptic current, one tau each. Groups 0..P-2 are MEMORY groups (cue synapses are
    distributed across them); group P-1 is the PROBE's fast channel. At P=1 the single group does both.
  * PROBE-ALIGNED readout: 60 ms after probe offset. Under variable delay a trial-end window falls at a
    different position per trial, which is the confound D141's amendment had to exclude.
  * Every trial runs to a common duration, so the readout window is comparable across delays.
"""
from __future__ import annotations

import warnings
import numpy as np

warnings.filterwarnings("ignore")
import brian2 as b2
from brian2 import ms

b2.prefs.codegen.target = "numpy"
b2.BrianLogger.suppress_name("resolution_conflict")

CUE, PROBE, RATE = 100, 100, 40.0


def run_block(P, taus, delays, seed, w=0.3, N=30, per_cat=15, nch=8, n_trials=144):
    """One (P, taus, seed) cell. Probe-aligned readout; cue synapses spread over the MEMORY groups."""
    rng = np.random.default_rng(seed)
    K = 2
    cue = rng.integers(0, K, n_trials)
    probe = rng.integers(0, K, n_trials)
    dsel = rng.integers(0, len(delays), n_trials)
    rel = (cue == probe).astype(int)
    out = np.zeros((n_trials, N))
    cur = " + ".join("I%d" % k for k in range(P))
    eqs = "\n".join(
        ["dv/dt = (-v + %s)/tau_m : 1 (unless refractory)" % cur]
        + ["dI%d/dt = -I%d/tau%d : 1" % (k, k, k) for k in range(P)]
        + ["dr/dt = -r/tau_r : 1"])
    ns = dict(tau_m=20 * ms, tau_r=30 * ms)
    for k, t_ in enumerate(taus):
        ns["tau%d" % k] = t_ * ms
    T_MAX = CUE + max(delays) + PROBE
    for t in range(n_trials):
        D = delays[dsel[t]]
        probe_on = CUE + D
        b2.start_scope()
        G = b2.NeuronGroup(N, eqs, threshold="v>1", reset="v=0; r+=1", refractory=2 * ms,
                           method="euler", namespace=ns)
        def sp(t0, t1):
            ii, tt = [], []
            for ch in range(nch):
                m = max(1, int(RATE * (t1 - t0) / 1000))
                tt += list(rng.uniform(t0, t1, size=m)); ii += [ch] * m
            ii = np.array(ii); tt = np.round(np.array(tt), 1)
            _, k = np.unique(np.stack([ii, tt]), axis=1, return_index=True)
            ii, tt = ii[k], tt[k]
            o = np.argsort(tt)
            return ii[o], tt[o]
        ci, ct = sp(1.0, CUE)
        pi, pt = sp(probe_on, probe_on + PROBE - 1.0)
        CU = b2.SpikeGeneratorGroup(nch, ci, ct * ms)
        PR = b2.SpikeGeneratorGroup(nch, pi, pt * ms)
        ctg = np.arange(cue[t] * per_cat, (cue[t] + 1) * per_cat)
        ptg = np.arange(probe[t] * per_cat, (probe[t] + 1) * per_cat)
        # EXPLICIT NETWORK -- do NOT rely on b2.run()'s magic collection. It scans the calling
        # frame's VARIABLES, so a Synapses object stored only inside a list is invisible to it: the
        # first version of this script appended the cue synapses to `keep` and every trial therefore
        # ran with probe input and NO CUE INPUT AT ALL, silently, while printing plausible progress.
        # Brian2 does warn ("getting deleted, but was never included in a network") but only at garbage
        # collection, long after the results are computed.
        objs = [G, CU, PR]
        mem = list(range(max(1, P - 1)))          # all groups but the last are MEMORY groups
        for gi, grp in enumerate(mem):
            sub = ctg[gi::len(mem)]
            if len(sub) == 0:
                continue
            S = b2.Synapses(CU, G, on_pre="I%d += w" % grp, namespace=dict(w=w))
            S.connect(i=np.repeat(np.arange(nch), len(sub)), j=np.tile(sub, nch))
            objs.append(S)
        fast = P - 1 if P > 1 else 0              # the last group is the PROBE's fast channel
        Sp = b2.Synapses(PR, G, on_pre="I%d += w" % fast, namespace=dict(w=w))
        Sp.connect(i=np.repeat(np.arange(nch), len(ptg)), j=np.tile(ptg, nch))
        objs.append(Sp)
        M = b2.StateMonitor(G, "r", record=True, dt=5 * ms)
        objs.append(M)
        net = b2.Network(*objs)
        # sanity: every cue synapse population must be present, or the trial has no cue input
        n_syn = sum(1 for o in objs if isinstance(o, b2.Synapses))
        assert n_syn == len([g for g in mem if len(ctg[mem.index(g)::len(mem)])]) + 1, \
            "synapse count mismatch -- cue synapses missing from the Network"
        net.run(T_MAX * ms)
        i1 = int((probe_on + PROBE) / 5.0)        # PROBE-ALIGNED: 60 ms after probe offset
        out[t] = M.r[:, max(0, i1 - 12):i1].mean(1)
    return out, rel


def decode(X, y, n_part=3):
    n = len(y); acc = []
    for s in range(n_part):
        idx = np.random.default_rng(s).permutation(n)
        f, e = idx[:n // 2], idx[n // 2:]
        Z = (X - X[f].mean(0)) / (X[f].std(0) + 1e-9)
        A = np.hstack([Z[f], np.ones((len(f), 1))])
        c, *_ = np.linalg.lstsq(A, y[f] * 2.0 - 1, rcond=None)
        acc.append(np.mean(((np.hstack([Z[e], np.ones((len(e), 1))]) @ c) > 0) == (y[e] > 0)))
    return float(np.mean(acc))


