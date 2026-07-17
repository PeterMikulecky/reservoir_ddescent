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
    tau_syn: float = 5.0
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
    sample_ms: float = 5.0
    seed: int | None = None

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
        eqs = """
        dv/dt = (v_rest - v + I_syn + I_ext + bias)/tau_m + noise_sigma*sqrt(2/tau_m)*xi : 1 (unless refractory)
        dI_syn/dt = -I_syn/tau_syn : 1
        dr/dt = -r/tau_r : 1
        I_ext = ta(t, i) : 1
        """
        self._dummy = b2.TimedArray(np.zeros((1, c.N)), dt=b2.defaultclock.dt)
        ns = dict(v_rest=c.v_rest, tau_m=c.tau_m * ms, tau_syn=c.tau_syn * ms,
                  tau_r=c.tau_r * ms, bias=c.bias, noise_sigma=c.noise_sigma,
                  v_thresh=c.v_thresh, v_reset=c.v_reset, ta=self._dummy)
        G = b2.NeuronGroup(c.N, eqs, threshold="v > v_thresh",
                           reset="v = v_reset; r += 1", refractory=c.refractory_ms * ms,
                           method="euler", namespace=ns, name="evonet")
        G.v = c.v_rest
        post, pre = np.nonzero(self.W)
        S = b2.Synapses(G, G, model="w : 1", on_pre="I_syn_post += w", name="rec")
        if len(pre):
            S.connect(i=pre, j=post)
            S.w = self.W[post, pre]
        self.G, self.S = G, S
        self.net = b2.Network(G, S)
        self.net.store("init")

    def behave(self, E: np.ndarray) -> dict:
        """Run the network over a batch of environments; return the behavior.

        E : (n_env, n_in) — each row drives the input neurons.
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
            end = (k + 1) * c.present_ms
            m = (t > end - c.readout_window_ms) & (t <= end)
            if not m.any():
                m = (t > end - c.present_ms) & (t <= end)
            win = r[:, m]
            state[k] = win.mean(axis=1)
            state_var[k] = win.var(axis=1)
        return dict(rates=state[:, self.cfg.out_slice()], state=state, state_var=state_var)
