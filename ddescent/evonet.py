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
    # ---- development / Vogels inhibitory plasticity (D086/D087) -----------------------------
    # Defaults keep a fresh net IDENTICAL to the pre-development network: eta starts 0 (set by
    # develop()), so these only matter once development runs. The plastic I->E block uses w_fast
    # only (inhibition has no slow component in this substrate -- w_slow=0 for inhibitory synapses,
    # D074), so Vogels tunes the fast inhibitory magnitude.
    tau_stdp_dev: float = 20.0    # inhibitory STDP trace time constant (ms)
    w_eps_dev: float = 1e-9       # support-freeze floor: plastic w clips to [w_eps, gmax], never 0,
    # --- excitatory STDP (eSTDP LEARNER, D103 -- the missing development half) --------------------
    dev_ee_stdp: bool = False     # enable eSTDP on E->E (OFF by default: preserves old behavior until
                                  # develop() is updated to drive it; flip on to build representation)
    tau_estdp_dev: float = 20.0   # excitatory STDP trace time constant (ms)
    estdp_Aplus: float = 1.0      # LTP amplitude (pre-before-post potentiates)
    estdp_Aminus: float = 1.0     # LTD amplitude (post-before-pre depresses); balance vs Aplus tunes
                                  # potentiation/depression bias (Aminus>=Aplus is the stable default)
    dev_gmax_e: float = 5.0       # max plastic excitatory magnitude (Kind-A upper clip)
    # --- lateral-inhibition WTA COMPETITION (D103 third leg; D106 showed eSTDP-alone needs it) --------
    dev_wta_comp: bool = False    # enable DEVELOPABLE lateral-inhibition competition during development.
                                  # OFF by default -> RETAINS the ability to see what selection can do
                                  # against a backdrop of NO a priori competition (PJM). Lateral inhib
                                  # among E neurons is PLASTIC (its own iSTDP, mirroring Vogels) so it
                                  # BREAKS SYMMETRY over developmental time (PJM: a STATIC uniform-all-
                                  # to-all term just damps everyone equally = no selection; the
                                  # differentiating power lives in the competition's DEVELOPABILITY, and
                                  # its effect is TEMPORAL/FUNCTIONAL, not necessarily E->E weight
                                  # variance). Development MACHINERY, outside P (not genome-encoded).
    wta_gain: float = 1.0         # initial strength of the lateral-inhibition competition current
    wta_tau: float = 5.0          # competition inhibition decay (ms); fast (~tau_syn) so the winner
                                  # suppresses others within the integration window
    wta_gmax: float = 20.0        # max plastic competition magnitude
    wta_alpha: float = 0.2        # competition iSTDP target-rate setpoint (Vogels-style)
    w_min_ee: float = 0.02        # PRINCIPLED dynamical floor for E->E plastic weights (D104): derived
                                  # as ~5% of the median active developed E->E weight (~0.41) -> a weight
                                  # here contributes ~5% of a typical synapse's drive = dynamically
                                  # negligible RELATIVE TO PEERS, but stays formally in-support. Weights
                                  # rest here instead of vanishing to ~0, so P_dev,structural =
                                  # P_dev,effective (fork dissolved); floor_fraction = fraction resting
                                  # here = the regularization readout. Derived by measurement (D068,
                                  # analysis_logs/*derive_dynamical_floor_v2*). RECOMPUTE if the study's
                                  # operating point (N, noise_sigma, gains, taus) changes.
                                  #   so a synapse can weaken but never leave P (Kind A, D087)
    dev_alpha: float = 0.2        # target-rate setpoint (Vogels alpha = 2*rho0*tau_stdp); tune per cfg
    dev_gmax: float = 20.0        # max plastic inhibitory magnitude

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


def _window_readout(r, t, n, N, present_ms, readout_window_ms, readout_pos):
    """Extract per-presentation (state_mean, state_var) from a recorded rate trace.

    **SHARED by the single-genome and batched paths (D078) so windowing can never drift between
    them.** r: (N, n_samples) rate trace for ONE block/network. t: (n_samples,) sample times in ms.
    Returns (state (n,N), state_var (n,N)). This is the exact logic that used to live inline in
    EvoNet.behave; factoring it out makes the batched runner's equivalence to the single-genome
    path a property of construction, not of copy-paste.
    """
    import numpy as _np
    state = _np.empty((n, N)); state_var = _np.empty((n, N))
    for k in range(n):
        t0 = k * present_ms
        t1 = (k + 1) * present_ms
        if readout_pos == "leading":
            lo, hi = t0, t0 + readout_window_ms
        elif readout_pos == "trailing":
            lo, hi = t1 - readout_window_ms, t1
        else:
            raise ValueError(f"readout_pos must be 'trailing' or 'leading', got {readout_pos!r}")
        m = (t > lo) & (t <= hi)
        if not m.any():
            m = (t > t0) & (t <= t1)
        win = r[:, m]
        if win.shape[1] == 0:
            # never leave an empty window -> NaN (robust to spike-timing shifts after development).
            # Callers MUST pass a t rebased to run-start (t -= t[0]); this only guards residual gaps.
            state[k] = 0.0; state_var[k] = 0.0
        else:
            state[k] = win.mean(axis=1)
            state_var[k] = win.var(axis=1)
    return state, state_var


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
        dv/dt = (v_rest - v + I_fast + I_slow + I_wta + I_ext + bias)/tau_m + noise_sigma*sqrt(2/tau_m)*xi : 1 (unless refractory)
        dI_fast/dt = -I_fast/tau_syn : 1
        dI_slow/dt = -I_slow/tau_slow : 1
        dI_wta/dt = -I_wta/tau_wta : 1
        dr/dt = -r/tau_r : 1
        I_ext = ta(t, i) : 1
        """
        self._dummy = b2.TimedArray(np.zeros((1, c.N)), dt=b2.defaultclock.dt)
        ns = dict(v_rest=c.v_rest, tau_m=c.tau_m * ms, tau_syn=c.tau_syn * ms,
                  tau_slow=c.tau_slow * ms, tau_wta=c.wta_tau * ms,
                  tau_r=c.tau_r * ms, bias=c.bias, noise_sigma=c.noise_sigma,
                  v_thresh=c.v_thresh, v_reset=c.v_reset, ta=self._dummy)
        G = b2.NeuronGroup(c.N, eqs, threshold="v > v_thresh",
                           reset="v = v_reset; r += 1", refractory=c.refractory_ms * ms,
                           method="euler", namespace=ns, name="evonet")
        G.v = c.v_rest
        # D074: each synapse deposits a FAST and a SLOW component. `w_fast` and `w_slow` are
        # per-synapse so we can route the slow fraction to EXC presynaptic cells only (there is
        # no slow inhibition). nmda_frac=0 => w_slow all zero => I_slow stays 0 => prior model.
        # D087: split the recurrent synapses by pre/post E/I identity. The I->E block is PLASTIC
        # (Vogels-Sprekeler inhibitory plasticity, D086/D087); the other three blocks (E->E, E->I,
        # I->I) are static and keep the D074/D075 two-current (w_fast/w_slow) structure. When
        # plasticity is off (eta=0), the split is behaviourally identical to the single-object net.
        post, pre = np.nonzero(self.W)
        if self.genome is not None:
            signs = self.genome.signs
        else:
            signs = np.ones(c.N)
            for j in range(c.N):
                col = self.W[:, j][self.W[:, j] != 0]
                if len(col):
                    signs[j] = np.sign(col[0])
        exc = signs > 0
        pre_inh = ~exc[pre]; post_exc = exc[post]
        pre_exc_m = exc[pre]
        ie_mask = pre_inh & post_exc          # I->E : plastic (Vogels iSTDP, stabilizer)
        ee_mask = pre_exc_m & post_exc        # E->E : plastic (eSTDP, learner -- D103) if dev_ee_stdp
        # remaining static: E->I, I->I  (and E->E when eSTDP disabled)
        if c.dev_ee_stdp:
            rest_mask = ~ie_mask & ~ee_mask
        else:
            rest_mask = ~ie_mask
            ee_mask = np.zeros_like(ee_mask)  # E->E stays in the static block

        self._syn = []
        self.con_ie = None
        self.con_ee = None

        # --- static block: two-current, charge-conserved (D074/D075) -----------------------------
        if rest_mask.any():
            rp, rq = pre[rest_mask], post[rest_mask]
            S = b2.Synapses(G, G, model="w_fast : 1\nw_slow : 1",
                            on_pre="I_fast_post += w_fast\nI_slow_post += w_slow", name="static")
            S.connect(i=rp, j=rq)
            w = self.W[rq, rp]
            pre_exc = exc[rp]
            # D075: split CHARGE not peak weight (see full derivation in git history / D075):
            #   w_slow = f*w*tau_fast/tau_slow ; w_fast = (1-f)*w ; total charge = w*tau_fast const in f
            f = c.nmda_frac
            charge_scale = c.tau_syn / c.tau_slow
            S.w_slow = np.where(pre_exc, f * w * charge_scale, 0.0)
            S.w_fast = np.where(pre_exc, (1.0 - f) * w, w)   # inh: full w in fast
            self._syn.append(S)

        # --- plastic I->E block: Vogels inhibitory plasticity on w_fast (D086/D087) ---------------
        # I->E is inhibitory, so w_slow=0 (slow is excitatory-only, D074) -- Vogels tunes w_fast.
        # w stored NON-NEGATIVE (magnitude); delivered as inhibition (I_fast_post -= w).
        # eta/alpha/gmax are PER-SYNAPSE (D086 door-opener for the D084 interneuron gene).
        if ie_mask.any():
            vogels = """
            w : 1
            eta : 1
            alpha : 1
            gmax : 1
            dApre/dt  = -Apre/tau_stdp  : 1 (event-driven)
            dApost/dt = -Apost/tau_stdp : 1 (event-driven)
            """
            con_ie = b2.Synapses(
                G, G, model=vogels,
                on_pre="""Apre += 1.
                          w = clip(w + (Apost - alpha)*eta, w_eps, gmax)
                          I_fast_post -= w""",
                on_post="""Apost += 1.
                           w = clip(w + Apre*eta, w_eps, gmax)""",
                namespace=dict(tau_stdp=c.tau_stdp_dev * ms, w_eps=c.w_eps_dev),
                name="ie_plastic")
            con_ie.connect(i=pre[ie_mask], j=post[ie_mask])
            con_ie.w = np.abs(self.W[post[ie_mask], pre[ie_mask]])   # magnitude
            con_ie.eta = 0.0                                          # plasticity OFF by default
            con_ie.alpha = c.dev_alpha
            con_ie.gmax = c.dev_gmax
            self._syn.append(con_ie)
            self.con_ie = con_ie

        # --- plastic E->E block: excitatory STDP (LEARNER, D103) ----------------------------------
        # The MISSING HALF (D103): eSTDP self-organizes stimulus-selective structure. Canonical pair-
        # based rule: pre-before-post -> LTP, post-before-pre -> LTD (Brian2 standard form). Runs
        # SIMULTANEOUSLY with the Vogels iSTDP that stabilizes it (Srinivasa & Cho 2014: eSTDP learns,
        # iSTDP balances -- they are a PAIR; the temporal-paradox blowup risk, Zenke/Gerstner, is why
        # we adopt the tested paired form rather than eSTDP alone). Kind A (D087): w clips to
        # [w_eps, gmax], never 0 -- support frozen, only magnitudes tune. Excitatory, so it deposits
        # BOTH fast and slow currents with the D074/D075 charge split (unlike inhibitory Vogels).
        # eta_e starts 0 (set by develop()); per-synapse eta/gmax (D084 door).
        if ee_mask.any():
            estdp = """
            w : 1
            eta_e : 1
            gmax_e : 1
            wf_scale : 1
            ws_scale : 1
            dapre/dt  = -apre/tau_estdp  : 1 (event-driven)
            dapost/dt = -apost/tau_estdp : 1 (event-driven)
            """
            con_ee = b2.Synapses(
                G, G, model=estdp,
                on_pre="""apre += Aplus_e
                          w = clip(w - apost*eta_e, w_eps_e, gmax_e)
                          I_fast_post += w*wf_scale
                          I_slow_post += w*ws_scale""",
                on_post="""apost += Aminus_e
                           w = clip(w + apre*eta_e, w_eps_e, gmax_e)""",
                namespace=dict(tau_estdp=c.tau_estdp_dev * ms, w_eps_e=c.w_min_ee,
                               Aplus_e=c.estdp_Aplus, Aminus_e=c.estdp_Aminus),
                name="ee_plastic")
            eep, eeq = pre[ee_mask], post[ee_mask]
            con_ee.connect(i=eep, j=eeq)
            con_ee.w = np.abs(self.W[eeq, eep])                       # magnitude
            con_ee.eta_e = 0.0                                        # plasticity OFF by default
            con_ee.gmax_e = c.dev_gmax_e
            # D074/D075 charge split, same as the static excitatory synapses:
            f = c.nmda_frac; charge_scale = c.tau_syn / c.tau_slow
            con_ee.ws_scale = f * charge_scale
            con_ee.wf_scale = (1.0 - f)
            self._syn.append(con_ee)
            self.con_ee = con_ee

        # --- lateral-inhibition WTA COMPETITION (D103 third leg; DEVELOPABLE per PJM) --------------
        # Each excitatory spike deposits fast inhibition (I_wta) onto all OTHER excitatory neurons, and
        # this lateral inhibition is PLASTIC (Vogels-style iSTDP) so it BREAKS SYMMETRY over development:
        # specific suppressive relationships strengthen (this neuron reliably suppresses that one),
        # carving distinct winners rather than uniformly damping the field (the static version's flaw).
        # Its effect is TEMPORAL/FUNCTIONAL (who fires when), not E->E weight variance. Non-genomic,
        # driven by wta_eta in develop() -> development machinery, outside P. Present only when enabled.
        self.con_wta = None
        if c.dev_wta_comp:
            exc_idx = np.nonzero(exc)[0]
            if len(exc_idx) > 1:
                aa, bb = np.meshgrid(exc_idx, exc_idx, indexing="ij")
                off = aa != bb
                src = aa[off].ravel(); tgt = bb[off].ravel()
                wta_model = """
                w : 1
                eta : 1
                alpha : 1
                gmax : 1
                dApre/dt  = -Apre/tau_wstdp  : 1 (event-driven)
                dApost/dt = -Apost/tau_wstdp : 1 (event-driven)
                """
                con_wta = b2.Synapses(
                    G, G, model=wta_model,
                    on_pre="""Apre += 1.
                              w = clip(w + (Apost - alpha)*eta, w_eps, gmax)
                              I_wta_post -= w""",
                    on_post="""Apost += 1.
                               w = clip(w + Apre*eta, w_eps, gmax)""",
                    namespace=dict(tau_wstdp=c.wta_tau * ms, w_eps=c.w_eps_dev),
                    name="wta_comp")
                con_wta.connect(i=src, j=tgt)
                con_wta.w = c.wta_gain          # initial competition strength
                con_wta.eta = 0.0               # plasticity OFF by default (driven by develop())
                con_wta.alpha = c.wta_alpha
                con_wta.gmax = c.wta_gmax
                self._syn.append(con_wta)
                self.con_wta = con_wta

        self.G = G
        self.S = self._syn[0] if self._syn else None                 # back-compat alias
        self.net = b2.Network(G, *self._syn)
        self.net.store("init")

    def behave(self, E: np.ndarray, noise_seed: int | None = None) -> dict:
        """Run the network over a batch of environments; return the behavior.

        E : (n_env, n_in) — each row drives the input neurons.
        noise_seed : if given, re-seed Brian2's RNG right before the run so this assay uses a
            specific, reproducible NOISE realization. Passing different seeds gives independent
            noise draws of the SAME network -> enables distributional evaluation (D085c): average
            component scores over noise realizations so a single lucky/unlucky draw isn't mistaken
            for signal. If None, the RNG stream continues from build/prior calls (legacy behavior).
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
        if noise_seed is not None:
            b2.seed(noise_seed)
        drive = np.zeros((n, c.N))
        drive[:, :c.n_in] = c.input_gain * E          # environment enters the input neurons
        self.net.restore("init")
        # ---- CLOCK-OFFSET CORRECTION (D121) -----------------------------------------------------
        # Brian2's TimedArray is indexed by ABSOLUTE simulation time. develop() re-calls
        # net.store("init") AFTER running warmup+dev_ms, so the stored snapshot carries an ADVANCED
        # clock; restore("init") therefore returns the clock to (e.g.) 16200 ms, not 0. A drive
        # built to start at row 0 is then read from row floor(t_now/present_ms) -> every DEVELOPED
        # network was assayed on TIME-SHIFTED stimuli, targets misaligned with the inputs that
        # produced them. D088 fixed only the MONITOR-timestamp half (the `t = t - t[0]` rebase
        # below), which made the remaining stimulus misalignment invisible. Fix: pad the drive with
        # that many leading zero rows, computed AFTER restore() (restore itself moves the clock), so
        # absolute-time lookup lands on row 0 of E at run start. The pad rows map to absolute times
        # that are never simulated (the run starts at t_now), so they are inert — this re-indexes,
        # it does not change the dynamics.
        offset_rows = int(round(float(self.net.t / (c.present_ms * ms))))
        if offset_rows:
            drive = np.vstack([np.zeros((offset_rows, c.N), dtype=drive.dtype), drive])
        ta = b2.TimedArray(drive, dt=c.present_ms * ms)
        self.G.namespace["ta"] = ta
        mon = b2.StateMonitor(self.G, "r", record=True, dt=c.sample_ms * ms, name="mon")
        self.net.add(mon)
        self.net.run(n * c.present_ms * ms)
        r = np.asarray(mon.r)                          # (N, samples)
        t = np.asarray(mon.t / ms)
        self.net.remove(mon)
        # Brian2's clock is GLOBAL and monotonic: develop() advances it, and restore("init") does
        # NOT reset clock time. Rebase to run-start so the window arithmetic (which assumes
        # t in [0, n*present_ms]) is correct regardless of prior clock advance (D088 baseline fix).
        # D121: ALSO snap to the sample grid. Monitor times are stored in SECONDS (e.g. 16.205 s is
        # not exactly representable), so rebasing at a large absolute clock leaves ~1e-11 ms of float
        # error that flips whether a sample sitting exactly on a readout-window boundary counts as
        # inside -- a CLOCK-DEPENDENT windowing, so a developed net (clock ~16200 ms) and a fresh net
        # windowed the SAME rate trace differently. Samples are emitted on the exact sample_ms grid,
        # so snapping removes the error and makes window membership identical at any clock offset
        # (this is the second half of the D088 rebase; together with the drive padding above it
        # restores bit-identity at noise_sigma=0).
        if len(t):
            t = np.round((t - t[0]) / c.sample_ms) * c.sample_ms

        # D078: windowing now lives in the shared _window_readout helper so the single-genome
        # and batched paths cannot diverge.
        state, state_var = _window_readout(r, t, n, c.N, c.present_ms,
                                           c.readout_window_ms, c.readout_pos)
        return dict(rates=state[:, self.cfg.out_slice()], state=state, state_var=state_var)

    # --- Kind-A development: Vogels inhibitory plasticity, in-simulation (D086/D087) -----------
    def develop(self, E, eta=1e-2, dev_ms=None, warmup_ms=200.0, n_checkpoints=10, seed=None,
                eta_e=None):
        """Mature the network by running plasticity while the stimulus stream drives it. Event-driven
        INSIDE net.run() -- no Python-side weight write-back (the fragility that broke Oja).

        Two paired mechanisms (D103):
          - Vogels iSTDP on I->E (rate `eta`): the STABILIZER (E/I balance, homeostatic).
          - eSTDP on E->E (rate `eta_e`): the LEARNER (self-organizes stimulus-selective structure) --
            the missing "expression" half. Runs SIMULTANEOUSLY with the stabilizer (Srinivasa & Cho:
            eSTDP learns, iSTDP balances; they are a pair, per the temporal-paradox caution). Only
            active if the net has E->E plastic synapses (cfg.dev_ee_stdp). Default eta_e = 0.5*eta
            (excitatory learner a bit slower/comparable to the inhibitory stabilizer; tune per cfg).

        seed : re-seed Brian2 for a reproducible (noisy) development run.
        Kind A (D087): only plastic MAGNITUDES change; support frozen by the w_eps clip (nominal-P
        invariant). Returns convergence trace(s). NaN tripwire aborts loud (Oja lesson).
        """
        c = self.cfg
        has_ie = self.con_ie is not None
        has_ee = self.con_ee is not None
        if not has_ie and not has_ee:
            return dict(converged=True, trace=[], reason="no plastic synapses (nothing to develop)")
        if seed is not None:
            b2.seed(seed)
        if dev_ms is None:
            # DEFAULT = 3 full passes through the stimulus sequence. (The previous expression,
            # 20 * E.shape[0] * present_ms / present_ms, cancelled present_ms and silently yielded
            # 20*n_stimuli ms — a fraction of one pass. Dead code, but wrong; removed.)
            dev_ms = float(3.0 * E.shape[0] * c.present_ms)
        if eta_e is None:
            eta_e = 0.5 * eta

        # --- stimulus supply -------------------------------------------------------------------
        # Brian2's TimedArray CLAMPS past its end (holds the final value) rather than looping, and the
        # warmup CONSUMES stimulus time because the array is indexed by absolute simulation time. So a
        # single copy of E supplies only n*present_ms of drive: with dev_ms beyond that, the last
        # stimulus would be held constant for the remainder. TILE to cover warmup + dev_ms.
        # (Audit D1-D4: at dev_ms=800 development saw 27% of stimuli, 2 of 4 contexts, ONE transition.)
        n = E.shape[0]
        seq_ms = n * c.present_ms
        n_tiles = int(np.ceil((warmup_ms + dev_ms) / max(seq_ms, 1e-9)))
        E_drive = np.tile(E, (max(n_tiles, 1), 1))
        drive = np.zeros((E_drive.shape[0], c.N)); drive[:, :c.n_in] = c.input_gain * E_drive
        ta = b2.TimedArray(drive, dt=c.present_ms * ms)
        self.net.restore("init")
        self.G.namespace["ta"] = ta

        # warm-up: all plasticity off, let dynamics settle
        if has_ie: self.con_ie.eta = 0.0
        if has_ee: self.con_ee.eta_e = 0.0
        if self.con_wta is not None: self.con_wta.eta = 0.0
        if warmup_ms > 0:
            self.net.run(warmup_ms * ms)

        # development: plasticity on (all mechanisms together), checkpointed
        if has_ie: self.con_ie.eta = float(eta)
        if has_ee: self.con_ee.eta_e = float(eta_e)
        if self.con_wta is not None: self.con_wta.eta = float(eta)  # competition develops at the iSTDP rate
        trace, trace_e = [], []
        chunk = dev_ms / max(n_checkpoints, 1)
        for _ in range(n_checkpoints):
            self.net.run(chunk * ms)
            if has_ie:
                w = np.asarray(self.con_ie.w)
                if not np.all(np.isfinite(w)):
                    return dict(converged=False, trace=trace, reason="NaN/inf in I->E weights (abort)")
                trace.append(float(np.mean(w)))
            if has_ee:
                we = np.asarray(self.con_ee.w)
                if not np.all(np.isfinite(we)):
                    return dict(converged=False, trace=trace, trace_e=trace_e,
                                reason="NaN/inf in E->E weights (abort)")
                trace_e.append(float(np.mean(we)))

        if has_ie: self.con_ie.eta = 0.0
        if has_ee: self.con_ee.eta_e = 0.0
        if self.con_wta is not None: self.con_wta.eta = 0.0
        self._commit_developed_weights()
        # reset neuron+trace state to rest, THEN re-store "init", so behave() starts clean but with
        # the DEVELOPED weights.
        self.G.v = c.v_rest
        self.G.I_fast = 0; self.G.I_slow = 0; self.G.r = 0
        if has_ie: self.con_ie.Apre = 0; self.con_ie.Apost = 0
        if has_ee: self.con_ee.apre = 0; self.con_ee.apost = 0
        if self.con_wta is not None: self.con_wta.Apre = 0; self.con_wta.Apost = 0
        self.net.store("init")

        # convergence: primary trace is whichever plastic block exists (prefer the learner if present,
        # since eSTDP settling is the meaningful "representation formed" signal, D103).
        primary = trace_e if has_ee else trace
        conv = (len(primary) >= 2 and abs(primary[-1] - primary[-2]) < 0.01 * (abs(primary[-1]) + 1e-9))
        return dict(converged=bool(conv), trace=trace, trace_e=trace_e, reason="ok")

    def _commit_developed_weights(self):
        """Write developed plastic magnitudes back into self.W so n_params / effective-P / behave
        see the matured network. Support preserved. I->E committed as NEGATIVE (inhibitory, no slow
        component); E->E committed as POSITIVE (excitatory, D103 eSTDP learner)."""
        if self.con_ie is not None:
            i = np.asarray(self.con_ie.i); j = np.asarray(self.con_ie.j)
            w = np.asarray(self.con_ie.w)
            self.W[j, i] = -w              # W[post, pre] = -magnitude (inhibitory)
        if self.con_ee is not None:
            ie = np.asarray(self.con_ee.i); je = np.asarray(self.con_ee.j)
            we = np.asarray(self.con_ee.w)
            self.W[je, ie] = we           # W[post, pre] = +magnitude (excitatory)


def behave_batch(genomes, cfg, E):
    """Run a LIST of genomes as ONE block-diagonal network — the D068 population batching (D078).

    ══════════════════════════════════════════════════════════════════════════════════════════
    WHY A SEPARATE RUNNER, NOT A REWRITE OF EvoNet.behave (design decision, PJM 2026-07-18)
    ══════════════════════════════════════════════════════════════════════════════════════════
    The single-genome `EvoNet.behave` is the VALIDATED reference path — diagnostics, Gate C, the
    positive control all call it. This runner is a SEPARATE, ADDITIVE path used only by the GA
    loop. Consequences, all deliberate:
      * A bug in batching can NEVER silently corrupt the diagnostics — they do not call this.
      * The equivalence check is permanent and trivial: batched block k MUST equal
        EvoNet(genomes[k]).behave(E) exactly. `verify_batch_equivalence` below is that check.
      * Windowing is shared via `_window_readout`, so the ONLY thing this runner adds is the
        block-diagonal assembly and the single run() — not a second copy of the readout logic.

    ══════════════════════════════════════════════════════════════════════════════════════════
    WHAT IS AND IS NOT BATCHED
    ══════════════════════════════════════════════════════════════════════════════════════════
    * WITHIN one genome, the n_env environments stream through ONE continuous run with sequential
      carryover — the network state persists env k -> k+1. **That carryover is D048's context
      mechanism and MUST be preserved.** It already was, in single-genome behave; this runner
      keeps it per block.
    * ACROSS genomes, the `pop_size` networks run SIMULTANEOUSLY as independent diagonal blocks
      of one big (pop*N)-neuron network. No cross-block synapses (guarded below). Every block sees
      the SAME environment sequence E, driven into its own input neurons. One run() replaces
      pop_size runs -> the ~15-25x.

    THREE HAZARDS, each guarded:
      1. Cross-block contamination — the worst failure, and silent. Synapses are assembled with
         per-block offsets so i,j never cross a block boundary; asserted before the run.
      2. Per-neuron noise — Brian2's `xi` is per-neuron, so each block gets an independent noise
         realisation automatically (same as pop_size separate runs with distinct RNG draws). NOT
         common-random-numbers across blocks; that is a separate open question (D077 tier-2).
      3. Memory — pop*N neurons and (step 3) all-to-all-allocated synapses. At pop 30 x N 50 =
         1500 neurons this is small; the ceiling grows with pop*N^2. Flagged, not yet a limit.

    Returns: list of per-genome dicts, each {rates, state, state_var} identical in shape to
    EvoNet.behave's output, in the same order as `genomes`.
    """
    P = len(genomes)
    N = cfg.N
    NT = P * N
    n = E.shape[0]

    # ---- assemble the block-diagonal synapse lists (post, pre in GLOBAL indices) --------
    all_i = []; all_j = []; all_wf = []; all_ws = []
    f = cfg.nmda_frac
    charge_scale = cfg.tau_syn / cfg.tau_slow
    for b, g in enumerate(genomes):
        W = g.W
        off = b * N
        post, pre = np.nonzero(W)
        if len(pre) == 0:
            continue
        w = W[post, pre]
        pre_exc = (g.signs[pre] > 0) if g is not None else (w > 0)
        w_slow = np.where(pre_exc, f * w * charge_scale, 0.0)
        w_fast = np.where(pre_exc, (1.0 - f) * w, w)
        all_i.append(pre + off); all_j.append(post + off)
        all_wf.append(w_fast); all_ws.append(w_slow)
    if all_i:
        gi = np.concatenate(all_i); gj = np.concatenate(all_j)
        gwf = np.concatenate(all_wf); gws = np.concatenate(all_ws)
        # HAZARD 1 guard: every synapse must stay within one block.
        assert np.all(gi // N == gj // N), "cross-block synapse detected — blocks would contaminate"
    else:
        gi = gj = gwf = gws = np.array([], dtype=int)

    # ---- one big NeuronGroup, same equations as _build ----------------------------------
    c = cfg
    eqs = """
    dv/dt = (v_rest - v + I_fast + I_slow + I_ext + bias)/tau_m + noise_sigma*sqrt(2/tau_m)*xi : 1 (unless refractory)
    dI_fast/dt = -I_fast/tau_syn : 1
    dI_slow/dt = -I_slow/tau_slow : 1
    dr/dt = -r/tau_r : 1
    I_ext = ta(t, i) : 1
    """
    ns = dict(v_rest=c.v_rest, tau_m=c.tau_m * ms, tau_syn=c.tau_syn * ms,
              tau_slow=c.tau_slow * ms, tau_r=c.tau_r * ms, bias=c.bias,
              noise_sigma=c.noise_sigma, v_thresh=c.v_thresh, v_reset=c.v_reset,
              ta=b2.TimedArray(np.zeros((1, NT)), dt=b2.defaultclock.dt))
    G = b2.NeuronGroup(NT, eqs, threshold="v > v_thresh", reset="v = v_reset; r += 1",
                       refractory=c.refractory_ms * ms, method="euler", namespace=ns,
                       name="evonet_batch")
    G.v = c.v_rest
    if c.seed is not None:
        b2.seed(c.seed)
    S = b2.Synapses(G, G, model="w_fast : 1\nw_slow : 1",
                    on_pre="I_fast_post += w_fast\nI_slow_post += w_slow", name="rec_batch")
    if len(gi):
        S.connect(i=gi, j=gj)
        S.w_fast = gwf; S.w_slow = gws

    # ---- drive: same E into every block's input neurons ---------------------------------
    # NOTE (D121): unlike single-genome EvoNet.behave, this runner does NOT need a clock-offset
    # correction. It builds a FRESH Network every call, and a fresh Brian2 Network runs from t=0
    # regardless of the global defaultclock (verified: fresh net1.t == 0 after a prior 8 s run), so
    # the absolute-time TimedArray already lands on row 0. The clock bug is specific to behave(),
    # whose PERSISTENT self.net is advanced by develop() and re-stored at that advanced clock.
    drive = np.zeros((n, NT))
    for b in range(P):
        drive[:, b * N : b * N + c.n_in] = c.input_gain * E
    G.namespace["ta"] = b2.TimedArray(drive, dt=c.present_ms * ms)

    mon = b2.StateMonitor(G, "r", record=True, dt=c.sample_ms * ms, name="mon_batch")
    net = b2.Network(G, S, mon)
    net.run(n * c.present_ms * ms)
    r_all = np.asarray(mon.r)            # (NT, samples)
    t = np.asarray(mon.t / ms)
    if len(t):
        t = t - t[0]                     # rebase to run-start (D088); fresh net starts at t=0 so
                                         # there is no large-clock float error to snap away here

    # ---- split back into per-genome results via the SHARED windowing helper -------------
    out = []
    for b in range(P):
        r_b = r_all[b * N : (b + 1) * N, :]
        state, state_var = _window_readout(r_b, t, n, N, c.present_ms,
                                            c.readout_window_ms, c.readout_pos)
        out.append(dict(rates=state[:, cfg.out_slice()], state=state, state_var=state_var))
    return out


def verify_batch_equivalence(genomes, cfg, E, rtol=1e-9, atol=1e-9, verbose=True):
    """D078: the standing check. Batched block k MUST equal EvoNet(genomes[k]).behave(E).

    Noise makes exact equality impossible UNLESS noise is off, so this is meaningful only at
    noise_sigma=0 (deterministic). Returns True/False. Run it whenever the batched path or the
    model equations change — 'a zero-weight synapse is inert' and 'blocks are independent' are
    SHOULDs, and this project's should-be-fines have twice been bugs (the pool that never ran;
    the 16x charge)."""
    import numpy as _np
    assert cfg.noise_sigma == 0, "equivalence check must run at noise_sigma=0 (else noise differs)"
    batched = behave_batch(genomes, cfg, E)
    ok = True
    for k, g in enumerate(genomes):
        single = EvoNet(g, cfg).behave(E)
        for key in ("rates", "state", "state_var"):
            if not _np.allclose(batched[k][key], single[key], rtol=rtol, atol=atol):
                d = float(_np.abs(batched[k][key] - single[key]).max())
                if verbose:
                    print(f"  block {k} '{key}' MISMATCH: max|Δ|={d:.2e}")
                ok = False
    if verbose:
        print("batch == single-genome:", ok)
    return ok
