"""
Brian2 LIF reservoir engine.

Shared engine for every experiment. Builds a recurrent LIF network from a weight
matrix, drives it with input patterns, and returns a *state matrix* X (n_patterns
x N) of filtered firing-rate features. Everything downstream -- readouts,
participation ratio, generalization metrics, the statistical pipeline -- operates
on X and is engine-agnostic.

Performance note: patterns are streamed through a single continuous run driven by
a TimedArray (each pattern held for `present_ms`), and the readout feature is the
rate trace averaged over each pattern's trailing window. This is the standard
liquid-state-machine setup and is orders of magnitude faster than restoring the
network per pattern. With present_ms >> tau_r, cross-pattern carryover fades, so
order effects are small; an optional hard reset between patterns is available for
strict i.i.d. treatment at extra cost.

Neuron model: current-based LIF (dimensionless v), exponential synaptic current,
plus a separate exponential rate trace `r` used purely as the readout feature.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import brian2 as b2
from brian2 import ms

b2.prefs.codegen.target = "numpy"     # no C++ compilation; portable (also avoids
                                      # compile-cache contention under parallelism)
b2.defaultclock.dt = 0.5 * ms
# quiet the per-run INFO chatter so parallel worker output stays readable
import logging as _logging
_logging.getLogger("brian2").setLevel(_logging.WARNING)


def _pr(X):
    """Participation ratio; local copy to avoid a circular import."""
    Xc = X - X.mean(axis=0, keepdims=True)
    sv = np.linalg.svd(Xc, compute_uv=False)
    lam = sv ** 2
    d = np.sum(lam ** 2)
    return float((np.sum(lam) ** 2) / d) if d > 0 else 0.0


@dataclass
class ReservoirConfig:
    N: int = 1000
    tau_m: float = 20.0
    tau_syn: float = 5.0
    tau_r: float = 30.0
    v_thresh: float = 1.0
    v_reset: float = 0.0
    v_rest: float = 0.0
    refractory_ms: float = 2.0
    input_gain: float = 1.0
    bias: float = 0.9
    noise_sigma: float = 0.0        # membrane noise; drives the aliasing experiment
    present_ms: float = 150.0
    readout_window_ms: float = 60.0
    sample_ms: float = 15.0         # state-monitor sampling during streaming
    seed: int | None = None


class LIFReservoir:
    def __init__(self, W_rec: np.ndarray, W_in: np.ndarray, cfg: ReservoirConfig):
        assert W_rec.shape[0] == W_rec.shape[1] == cfg.N
        assert W_in.shape[0] == cfg.N
        self.cfg = cfg
        self.W_rec = W_rec
        self.W_in = W_in
        self.K = W_in.shape[1]
        if cfg.seed is not None:
            b2.seed(cfg.seed)
        self._build()

    def _build(self):
        c = self.cfg
        # I_ext is read from a swappable TimedArray `ta` indexed by (t, neuron).
        eqs = """
        dv/dt = (v_rest - v + I_syn + I_ext + bias)/tau_m + noise_sigma*sqrt(2/tau_m)*xi : 1 (unless refractory)
        dI_syn/dt = -I_syn/tau_syn : 1
        dr/dt = -r/tau_r : 1
        I_ext = ta(t, i) : 1
        """
        self._dummy_ta = b2.TimedArray(np.zeros((1, c.N)), dt=b2.defaultclock.dt)
        ns = dict(v_rest=c.v_rest, tau_m=c.tau_m * ms, tau_syn=c.tau_syn * ms,
                  tau_r=c.tau_r * ms, bias=c.bias, noise_sigma=c.noise_sigma,
                  v_thresh=c.v_thresh, v_reset=c.v_reset, ta=self._dummy_ta)
        G = b2.NeuronGroup(
            c.N, eqs, threshold="v > v_thresh", reset="v = v_reset; r += 1",
            refractory=c.refractory_ms * ms, method="euler", namespace=ns,
            name="reservoir",
        )
        G.v = c.v_rest

        post, pre = np.nonzero(self.W_rec)
        S = b2.Synapses(G, G, model="w : 1", on_pre="I_syn_post += w", name="rec")
        S.connect(i=pre, j=post)
        S.w = self.W_rec[post, pre]

        self.G, self.S = G, S
        self.net = b2.Network(G, S)
        self.net.store("init")

    def run_static(self, U: np.ndarray) -> np.ndarray:
        """Stream static input vectors; return (n_patterns, N) trailing-window features."""
        c = self.cfg
        n = U.shape[0]
        # The drive is constant over each pattern, so one TimedArray row per pattern
        # held for present_ms suffices -- ta(t,i) returns pattern k's value during
        # [k*present_ms, (k+1)*present_ms). This is ~present_ms/dt (~hundreds x)
        # smaller in memory than expanding to per-step resolution, which matters
        # under 6-way parallelism.
        drive = (c.input_gain * (U @ self.W_in.T)).astype(float)   # (n, N)
        ta = b2.TimedArray(drive, dt=c.present_ms * ms)

        self.net.restore("init")
        self.G.namespace["ta"] = ta
        mon = b2.StateMonitor(self.G, "r", record=True,
                              dt=c.sample_ms * ms, name="mon")
        self.net.add(mon)
        self.net.run(n * c.present_ms * ms)
        r = np.asarray(mon.r)                                # (N, n_samples)
        t = np.asarray(mon.t / ms)                           # (n_samples,)
        self.net.remove(mon)

        X = np.empty((n, c.N))
        for k in range(n):
            end = (k + 1) * c.present_ms
            start = end - c.readout_window_ms
            m = (t > start) & (t <= end)
            if not m.any():
                m = (t > (end - c.present_ms)) & (t <= end)
            X[k] = r[:, m].mean(axis=1)
        return X

    def run_temporal(self, U_series: np.ndarray, sample_every_ms: float) -> np.ndarray:
        """Stream a time-varying input; sample the state along the trajectory."""
        c = self.cfg
        dt = b2.defaultclock.dt
        drive = c.input_gain * (U_series @ self.W_in.T)
        ta = b2.TimedArray(drive, dt=dt)
        self.net.restore("init")
        self.G.namespace["ta"] = ta
        mon = b2.StateMonitor(self.G, "r", record=True,
                              dt=sample_every_ms * ms, name="mon_t")
        self.net.add(mon)
        self.net.run(U_series.shape[0] * dt)
        X = np.asarray(mon.r).T
        self.net.remove(mon)
        return X

    def run_stationary(self, U: np.ndarray, sample_ms: float | None = None) -> dict:
        """Protocol S (D026): stream static patterns, return THREE readouts per pattern.

        The network does not settle (see PROTOCOLS.md), so what we sample is a stationary
        response *distribution*, not a fixed point. We therefore keep its location, a
        single unaveraged draw, and its spread -- rather than only the mean:

          X_mean : trailing-window mean            (the original readout)
          X_inst : ONE instantaneous sample        (no averaging -- the artifact control)
          X_var  : within-window temporal variance (the dynamics we would have discarded)

        Plus S-specific diagnostics that only exist under sustained drive:
          temporal_cv  : per-pattern within-window fluctuation (is it stationary?)
          attractor_pr : PR of a SINGLE pattern's within-window trajectory -- the
                         dimensionality of one input's attractor, conceptually distinct
                         from PR across inputs.

        `sample_ms` overrides cfg.sample_ms: the default (15 ms) yields only ~4 samples in
        a 60 ms window, too few to estimate variance or attractor PR. Use ~5 ms here.
        """
        c = self.cfg
        n = U.shape[0]
        dt_s = sample_ms if sample_ms is not None else c.sample_ms
        drive = (c.input_gain * (U @ self.W_in.T)).astype(float)
        ta = b2.TimedArray(drive, dt=c.present_ms * ms)

        self.net.restore("init")
        self.G.namespace["ta"] = ta
        mon = b2.StateMonitor(self.G, "r", record=True, dt=dt_s * ms, name="mon_s")
        self.net.add(mon)
        self.net.run(n * c.present_ms * ms)
        r = np.asarray(mon.r)                     # (N, n_samples)
        t = np.asarray(mon.t / ms)
        self.net.remove(mon)

        X_mean = np.empty((n, c.N)); X_inst = np.empty((n, c.N)); X_var = np.empty((n, c.N))
        temporal_cv = np.empty(n); attractor_pr = np.empty(n)
        for k in range(n):
            end = (k + 1) * c.present_ms
            m = (t > end - c.readout_window_ms) & (t <= end)
            if not m.any():
                m = (t > end - c.present_ms) & (t <= end)
            win = r[:, m]                          # (N, n_win)
            X_mean[k] = win.mean(axis=1)
            X_inst[k] = win[:, -1]                 # last sample: no averaging
            X_var[k] = win.var(axis=1)
            mu = win.mean(axis=1)
            temporal_cv[k] = float(np.mean(win.std(axis=1) / (mu + 1e-9)))
            attractor_pr[k] = _pr(win.T) if win.shape[1] >= 3 else np.nan
        return dict(X_mean=X_mean, X_inst=X_inst, X_var=X_var,
                    temporal_cv=float(np.mean(temporal_cv)),
                    attractor_pr=float(np.nanmean(attractor_pr)),
                    n_window_samples=int(m.sum()))
