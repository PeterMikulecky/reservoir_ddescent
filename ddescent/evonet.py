"""
Evolvable spiking network: W IS the genome.

The model D032/D036 specify. Contrast with the retired reservoir (`reservoir.py`):
there, W was frozen architecture and a linear readout was trained — so the only learned
parameters were the readout weights, which are NOT "regulatory connections", and
genome-level double descent was impossible by construction (the genome was 5 numbers).

Here:
  * **Genome** = W, every recurrent weight. P = |W| ~ density * N^2. **This is Frank's
    x-axis, literally**: regulatory connections as the adjustable parameters.
  * **No trained readout.** Input neurons receive the environment; output neurons' behavior
    IS the phenotype. Selection acts on the whole network.
  * **Phenotype** = the behavior itself (D036). `express()` returns output firing rates as a
    *measurement* of it, because rate is what fitness reads — a defensible design choice
    (expression level is the trait), not a claim that rate IS the phenotype.
  * **d** (number of output neurons) is a property of the NICHE, not the genome: the
    environment demands a response of a given shape. Fixed per arm, varied across arms as the
    second knob on the interpolation threshold (constraints = n_env * d).

Scale: N ~ 100, not 1000. Without a readout there is no need for a large random feature
pool. At N=100, d=10, n_env=50: constraints = 500, and P sweeps 50 -> 5000 as density goes
0.005 -> 0.5. The threshold crossing sits inside a natural density range.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import brian2 as b2
from brian2 import ms

b2.prefs.codegen.target = "numpy"
b2.defaultclock.dt = 0.5 * ms
import logging as _logging
_logging.getLogger("brian2").setLevel(_logging.ERROR)


@dataclass
class EvoNetConfig:
    N: int = 100                 # total neurons
    n_in: int = 10               # input neurons (driven by the environment)
    d: int = 10                  # OUTPUT neurons -> phenotype dimensionality (niche property)
    tau_m: float = 20.0
    tau_syn: float = 5.0          # FAST synaptic current (AMPA / GABA_A). Renamed role: tau_fast.
    tau_slow: float = 100.0       # SLOW excitatory current (NMDA-like decay; D074). tau_r-scale.
    nmda_frac: float = 0.0        # D074: fraction of each EXC weight routed to the slow current.
                                  # 0.0 = today's model bit-for-bit (fast-only). NOT a gene
                                  # (D073: drawn, not evolved -- heritable memory would be a
                                  # shortcut). We take NMDA's KINETICS, never its Mg gate (D074:
                                  # the gate is voltage-dependent multiplicative gain modulation,
                                  # = a ready-made instance of the mechanism H-C tests for).
    tau_r: float = 30.0
    v_thresh: float = 1.0
    v_reset: float = 0.0
    v_rest: float = 0.0
    refractory_ms: float = 2.0
    bias: float = 0.4
    input_gain: float = 10.0     # D030/D033: the useful regime; NOT the PR-optimal one
    noise_sigma: float = 0.0
    present_ms: float = 150.0
    readout_window_ms: float = 60.0
    readout_pos: str = "trailing"   # 'trailing' | 'leading'  -- see below
    sample_ms: float = 5.0
    seed: int | None = None

    # ---- readout_pos: WHERE in the presentation we look. A DIAGNOSTIC KNOB (D072). --------
    # Every timing parameter above is IDENTICAL to `ReservoirConfig` -- inherited across D032
    # untouched, together with their rationale, which reservoir.py states outright:
    #   "With present_ms >> tau_r, cross-pattern carryover fades, so order effects are small."
    # **Carryover-fading was the DESIGN GOAL.** D048 then put context in the statistics across
    # context_dwell=10 stimuli and made carryover THE MECHANISM. Nobody revisited the engine.
    #
    # 'trailing' (default, = every result so far): read the LAST readout_window_ms of the
    #     presentation. 90 ms of settling elapses first = 4.5 tau_m, so any trace of the
    #     previous stimulus has decayed to ~1% BEFORE the readout opens.
    # 'leading' : read the FIRST readout_window_ms. Averaging exp(-t/tau_m) over t in [0,60]
    #     retains ~32% of the previous stimulus -- and `r` (tau_r=30) carries pre-switch spikes
    #     across the boundary, so in practice more.
    #
    # **Why this is a diagnostic and not a fix.** E9 diagnostics measured mem_d1 = 1.000 in all
    # 8 cells -- ZERO information about the previous stimulus. That has two readings:
    # the memory is ABSENT, or the memory is PRESENT AND WE ARE NOT LOOKING AT IT. This knob
    # separates them. It CANNOT reach context_dwell=10: exp(-1500/30) = 0 at any window
    # position, so it buys d1-d2, never d10. Only heterogeneous tau_m spans 1500 ms.
    # **Default is unchanged, so no existing result moves.**

    def n_params(self, density: float) -> int:
        """P = |W|. Frank's x-axis. Compare against n_env * d (the constraint count)."""
        return int(round(density * self.N * (self.N - 1)))

    def out_slice(self):
        """Output neurons are the LAST d units; inputs are the FIRST n_in."""
        return slice(self.N - self.d, self.N)


@dataclass
class Genome:
    """Dale's law with EVOLVABLE per-neuron identity (D038).

    Two gene groups:
      * `signs` : (N,) in {+1,-1} -- each NEURON is excitatory or inhibitory, and ALL of its
        outgoing synapses carry that sign. Mutable: **a neuron can evolve into an inhibitory
        cell.**
      * `mag`   : (N,N) >= 0 -- per-synapse magnitudes. Zeros are absent synapses.

    Why this matters. The previous design used signed weights WITHOUT Dale's law, so 97/100
    neurons excited some targets and inhibited others simultaneously. There was plenty of
    inhibition (52% of synapses) but **no neuron had a coherent role** — and regulatory
    motifs (feedforward inhibition, disinhibition, gain control) all require a cell whose
    *identity* is inhibitory. The architecture could not host the thing the theory is about.

    We do NOT bolt on a regulatory mode. We make the architecture CAPABLE of one, and ask
    whether selection builds it. Whether regulatory motifs emerge — and whether their
    emergence coincides with the second descent — becomes the finding, not the assumption.
    """
    signs: np.ndarray     # (N,) +1 excitatory / -1 inhibitory  -- per NEURON
    mag: np.ndarray       # (N,N) >= 0, mag[i,j] = magnitude of synapse j -> i

    @property
    def W(self) -> np.ndarray:
        """Effective weights. Column j (presynaptic) takes neuron j's sign: Dale's law."""
        return self.mag * self.signs[np.newaxis, :]

    def n_params(self) -> int:
        """P = |W|. Frank's x-axis (signs are N extra genes; magnitudes dominate)."""
        return int((self.mag != 0).sum())

    def exc_fraction(self) -> float:
        return float((self.signs > 0).mean())

    def dale_violations(self) -> int:
        """Should always be 0 by construction. A guard against regressions."""
        W = self.W
        v = 0
        for j in range(W.shape[1]):
            out = W[:, j][W[:, j] != 0]
            if len(out) > 1 and (out > 0).any() and (out < 0).any():
                v += 1
        return v


def random_genome(cfg: EvoNetConfig, density: float, w0: float = 1.5,
                  ei_split: float = 0.8, inh_gain: float | None = None,
                  seed: int | None = None) -> Genome:
    """Initial population member. Dale-compliant AND E/I-BALANCED.

    Fixed per-synapse scale, NO renormalization (D014): adding synapses genuinely increases
    recurrent coupling, which is what makes density a live variable.
    `ei_split` is only the STARTING excitatory fraction — signs are genes and evolve.

    **`inh_gain` (D058, the Gate C fix).** With `ei_split=0.8`, excitatory neurons outnumber
    inhibitory 4:1. If every synapse is drawn from the same magnitude distribution, **excitation
    swamps inhibition ~4:1** — measured E/I current ratios up to **24:1**, firing became purely
    mean-driven (CV_ISI <= 0.44) and **Gate C failed 0/36**: no fluctuation-driven regime, hence
    no divisive gain control, hence no possible regulation (D039).
    The classic balanced-network condition (Brunel 2000; van Vreeswijk & Sompolinsky 1996) scales
    inhibitory weights up to compensate the count asymmetry: **J_I = -g * J_E** with
    **g ≈ ei_split / (1 - ei_split)** (= 4 at ei_split=0.8). `inh_gain=None` uses exactly that.
    *This is a STARTING condition, not a constraint: magnitudes are genes and evolution may
    unbalance the network if that pays.*
    """
    rng = np.random.default_rng(seed)
    if inh_gain is None:
        inh_gain = ei_split / max(1.0 - ei_split, 1e-6)      # balance the count asymmetry
    mag = np.abs(rng.standard_normal((cfg.N, cfg.N))) * w0
    mask = rng.random((cfg.N, cfg.N)) < density
    np.fill_diagonal(mask, False)
    signs = np.where(rng.random(cfg.N) < ei_split, 1.0, -1.0)
    # scale the OUTGOING magnitudes of inhibitory neurons (column j = presynaptic)
    mag = mag * np.where(signs < 0, inh_gain, 1.0)[np.newaxis, :]
    return Genome(signs=signs, mag=mag * mask)


def mutate(g: Genome, mag_sigma: float = 0.2, sign_flip_p: float = 0.01,
           rule: str = "product", rng=None) -> Genome:
    """Mutate magnitudes; rarely flip per-neuron signs.

    **PRODUCT RULE is the default and it is load-bearing (D043, B1).** Friedlander, Mayo,
    Tlusty & Alon (2015): bow-tie architectures evolve only when mutations follow a **product
    rule** (element *multiplied* by a random number) — with **sum-rule** mutations
    **94-97% of runs FAIL** to evolve a waist matching the goal rank. Product-rule is also the
    more biologically realistic of the two. Our previous operator was sum-rule: i.e. the one
    that reliably PREVENTS the thing we are looking for.

    * `product` : mag *= N(1, sigma), clipped at 0. Multiplicative — scale-free, and can drive
      a weight toward extinction gradually.
    * `sum`     : mag += N(0, sigma). Retained ONLY as an experimental contrast (it is a dial
      in the D052 graded series: does the waist require product-rule mutation?).

    A sign flip converts a neuron between excitatory and inhibitory — the mutation that lets a
    regulatory subpopulation evolve (D038). Kept rare: it is a large phenotypic jump.
    """
    rng = rng or np.random.default_rng()
    mag = g.mag.copy()
    nz = mag != 0
    if rule == "product":
        mag[nz] = np.maximum(mag[nz] * rng.normal(1.0, mag_sigma, nz.sum()), 0.0)
    elif rule == "sum":
        mag[nz] = np.abs(mag[nz] + rng.normal(0, mag_sigma, nz.sum()))
    else:
        raise ValueError(f"unknown mutation rule {rule!r}")
    signs = g.signs.copy()
    flip = rng.random(len(signs)) < sign_flip_p
    signs[flip] *= -1
    return Genome(signs=signs, mag=mag)


class EvoNet:
    """A spiking network whose recurrent weights ARE the genome."""

    def __init__(self, genome, cfg: EvoNetConfig):
        # accepts a Genome (preferred) or a raw W array (legacy)
        if isinstance(genome, Genome):
            self.genome = genome
            W = genome.W
        else:
            self.genome = None
            W = genome
        assert W.shape == (cfg.N, cfg.N)
        self.cfg = cfg
        self.W = W
        if cfg.seed is not None:
            b2.seed(cfg.seed)
        self._build()

    def _build(self):
        c = self.cfg
        # D074: two synaptic currents. I_fast = AMPA/GABA_A (tau_syn=5 ms, all synapses);
        # I_slow = NMDA-like (tau_slow=100 ms, EXCITATORY synapses only). Decay-only -- NO Mg
        # gate (that gate is the mechanism H-C measures selection building; installing it would
        # answer H-C by construction). At nmda_frac=0 the slow term is inert and the dynamics
        # equal the prior single-current model exactly.
        eqs = """
        dv/dt = (v_rest - v + I_fast + I_slow + I_ext + bias)/tau_m + noise_sigma*sqrt(2/tau_m)*xi : 1 (unless refractory)
        dI_fast/dt = -I_fast/tau_syn : 1
        dI_slow/dt = -I_slow/tau_slow : 1
        dr/dt = -r/tau_r : 1
        I_ext = ta(t, i) : 1
        """
        self._dummy = b2.TimedArray(np.zeros((1, c.N)), dt=b2.defaultclock.dt)
        ns = dict(v_rest=c.v_rest, tau_m=c.tau_m * ms, tau_syn=c.tau_syn * ms,
                  tau_slow=c.tau_slow * ms,
                  tau_r=c.tau_r * ms, bias=c.bias, noise_sigma=c.noise_sigma,
                  v_thresh=c.v_thresh, v_reset=c.v_reset, ta=self._dummy)
        G = b2.NeuronGroup(c.N, eqs, threshold="v > v_thresh",
                           reset="v = v_reset; r += 1", refractory=c.refractory_ms * ms,
                           method="euler", namespace=ns, name="evonet")
        G.v = c.v_rest
        # D074: each synapse deposits a FAST and a SLOW component. `w_fast` and `w_slow` are
        # per-synapse so we can route the slow fraction to EXC presynaptic cells only (there is
        # no slow inhibition). nmda_frac=0 => w_slow all zero => I_slow stays 0 => prior model.
        post, pre = np.nonzero(self.W)
        S = b2.Synapses(G, G, model="w_fast : 1\nw_slow : 1",
                        on_pre="I_fast_post += w_fast\nI_slow_post += w_slow", name="rec")
        if len(pre):
            S.connect(i=pre, j=post)
            w = self.W[post, pre]
            # presynaptic sign: slow current is excitatory-only. genome.signs is per-NEURON;
            # for a raw-W legacy net, fall back to the weight's own sign.
            if self.genome is not None:
                pre_exc = self.genome.signs[pre] > 0
            else:
                pre_exc = w > 0
            f = c.nmda_frac
            S.w_slow = np.where(pre_exc, f * w, 0.0)
            S.w_fast = w - np.where(pre_exc, f * w, 0.0)   # exc: (1-f)w ; inh: full w in fast
        self.G, self.S = G, S
        self.net = b2.Network(G, S)
        self.net.store("init")

    def behave(self, E: np.ndarray) -> dict:
        """Run the network over a batch of environments; return the behavior.

        E : (n_env, n_in) — each row drives the input neurons.
        The window is `cfg.readout_window_ms` long, placed by `cfg.readout_pos` ('trailing'
        = the inherited default, after settling; 'leading' = at onset, where carryover lives).

        Returns dict with:
          'rates'  : (n_env, d)  output-neuron rates  -> what FITNESS reads
          'state'  : (n_env, N)  full internal state (window mean)
          'state_var' : (n_env, N) within-window variance — the channel D028/D033 say carries
                        the representation. A METRIC, not fitness.
        """
        c = self.cfg
        n = E.shape[0]
        drive = np.zeros((n, c.N))
        drive[:, :c.n_in] = c.input_gain * E          # environment enters the input neurons
        ta = b2.TimedArray(drive, dt=c.present_ms * ms)
        self.net.restore("init")
        self.G.namespace["ta"] = ta
        mon = b2.StateMonitor(self.G, "r", record=True, dt=c.sample_ms * ms, name="mon")
        self.net.add(mon)
        self.net.run(n * c.present_ms * ms)
        r = np.asarray(mon.r)                          # (N, samples)
        t = np.asarray(mon.t / ms)
        self.net.remove(mon)

        state = np.empty((n, c.N)); state_var = np.empty((n, c.N))
        for k in range(n):
            t0 = k * c.present_ms
            t1 = (k + 1) * c.present_ms
            # D072: window POSITION within the presentation. 'trailing' = the inherited
            # behaviour (read after ~4.5 tau_m of settling, when the previous stimulus is
            # gone); 'leading' = read the onset, where the carryover still is.
            if c.readout_pos == "leading":
                lo, hi = t0, t0 + c.readout_window_ms
            elif c.readout_pos == "trailing":
                lo, hi = t1 - c.readout_window_ms, t1
            else:
                raise ValueError(f"readout_pos must be 'trailing' or 'leading', "
                                 f"got {c.readout_pos!r}")
            m = (t > lo) & (t <= hi)
            if not m.any():
                m = (t > t0) & (t <= t1)
            win = r[:, m]
            state[k] = win.mean(axis=1)
            state_var[k] = win.var(axis=1)
        return dict(rates=state[:, self.cfg.out_slice()], state=state, state_var=state_var)
