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


def run_stream(P, taus, lam, seed, w=0.3, N=30, n_seg=8, seg_ms=100, nch=8, n_trials=144,
               rate_gain=40.0):
    """STRUCTURED ACCUMULATE: evidence arrives throughout the trial; the target needs TWO timescales.

    target = sum(all segments) + lam * (final segment)

    WHY THIS FORCES TAU COUNT RATHER THAN MAGNITUDE. With a single tau, the trace at read time weights
    segment k by exp(-(T - t_k)/tau). Matching `alpha*sum(x) + beta*x_last` would require that weighting
    to be simultaneously FLAT across the trial (for the sum) and PEAKED at the end (for recency). One
    exponential cannot be both; two can approximate it. This is a provable requirement for the NUMBER of
    time constants -- unlike DMTS, where the delay is dead time and one long tau simply survives it
    (D142).

    `lam` is the knob: lam=0 is pure accumulation (one LONG tau optimal), lam large is pure recency (one
    SHORT tau optimal), and only intermediate lam needs both. That gives a built-in falsification.

    Evidence is delivered as a Poisson RATE modulation on a single channel group, so all neurons see the
    same stream and the task is not about routing.
    """
    rng = np.random.default_rng(seed)
    ev = rng.standard_normal((n_trials, n_seg))                  # independent evidence per segment
    y = ev.sum(1) + lam * ev[:, -1]
    T = n_seg * seg_ms
    cur = " + ".join("I%d" % k for k in range(P))
    eqs = "\n".join(
        ["dv/dt = (-v + %s)/tau_m : 1 (unless refractory)" % cur]
        + ["dI%d/dt = -I%d/tau%d : 1" % (k, k, k) for k in range(P)]
        + ["dr/dt = -r/tau_r : 1"])
    ns = dict(tau_m=20 * ms, tau_r=30 * ms)
    for k, t_ in enumerate(taus):
        ns["tau%d" % k] = t_ * ms
    out = np.zeros((n_trials, N))
    for t in range(n_trials):
        b2.start_scope()
        G = b2.NeuronGroup(N, eqs, threshold="v>1", reset="v=0; r+=1", refractory=2 * ms,
                           method="euler", namespace=ns)
        ii, tt = [], []
        for k in range(n_seg):
            # evidence sets the Poisson rate in this segment (shifted positive)
            r_hz = max(2.0, rate_gain * (1.0 + 0.5 * ev[t, k]))
            for ch in range(nch):
                m = max(1, rng.poisson(r_hz * seg_ms / 1000.0))
                tt += list(rng.uniform(k * seg_ms + 1.0, (k + 1) * seg_ms - 1.0, size=m))
                ii += [ch] * m
        ii = np.array(ii); tt = np.round(np.array(tt), 1)
        _, kp = np.unique(np.stack([ii, tt]), axis=1, return_index=True)
        ii, tt = ii[kp], tt[kp]
        o = np.argsort(tt); ii, tt = ii[o], tt[o]
        SG = b2.SpikeGeneratorGroup(nch, ii, tt * ms)
        objs = [G, SG]
        # input synapses split EVENLY across all P groups -- every group sees the same stream, so the
        # only thing distinguishing them is their tau.
        for grp in range(P):
            sub = np.arange(grp, N, P)
            if len(sub) == 0:
                continue
            S = b2.Synapses(SG, G, on_pre="I%d += w" % grp, namespace=dict(w=w))
            S.connect(i=np.repeat(np.arange(nch), len(sub)), j=np.tile(sub, nch))
            objs.append(S)
        M = b2.StateMonitor(G, "r", record=True, dt=5 * ms)
        objs.append(M)
        b2.Network(*objs).run(T * ms)
        out[t] = M.r[:, -12:].mean(1)                            # last 60 ms of the stream
    return out, y


def decode_reg(X, y):
    """Held-out RIDGE decode for a CONTINUOUS target; returns |Pearson r|."""
    n = len(y); f = np.arange(n) < n // 2; e = ~f
    mu, sd = X[f].mean(0), X[f].std(0) + 1e-9
    Z = (X - mu) / sd
    A = Z[f]; yc = y[f] - y[f].mean()
    c = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ yc)
    p = Z[e] @ c
    return 0.0 if p.std() < 1e-12 else float(abs(np.corrcoef(p, y[e])[0, 1]))


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


