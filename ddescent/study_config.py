"""CANONICAL STUDY CONFIGURATION — the single source of truth.

WHY THIS EXISTS. The `d=3` waist collapse (audit C1) happened because the task dimension was written
out separately in every runner and probe. When one copy changed, the others silently disagreed with it
and with the validated configuration, and nothing noticed for weeks. Parameters that define the STUDY
belong in exactly one place; scripts import them rather than restating them.

Anything that changes here changes everywhere, and `audit.py` checks THIS module's values.
"""
from __future__ import annotations
import numpy as np

from .evonet import EvoNetConfig
from .evolve import EvolveConfig
from . import tasks as T

# =================================================================================================
# TASK — the environment the networks are selected in
# =================================================================================================
# d=10 restores the VALIDATED configuration (audit C1). With d=3 we had r1 == min(K,d) == 3, so the
# rank constraint was vacuous: any K->d map has rank <= d, there was no low-rank waist, and r1 was not
# a free structural parameter — which makes H-B (the peak tracks r1, not the constraint count)
# UNTESTABLE. d=10 gives min(K,d)=10, so r1=3 is a genuine waist and r1 is sweepable over ~{2,3,4,5}
# for the H-B factorial.
TASK = dict(
    K=10,             # stimulus dimension. Its job is to make r1 << min(K,d) possible.
    d=10,             # response dimension. RESTORED from 3 (audit C1).
    r1=3,             # rank of every level-1 map. THE structural quantity H-B predicts the peak at.
    n_contexts=4,
    n_train=60,
    n_val=60,         # D113: selection reads this split, never test.
    n_test=60,        # D113: reporting only.
    context_dwell=10, # the SLOW timescale = the memory demand. Do not shrink: it IS the H-C/H-D difficulty.
    seed=0,
)

# =================================================================================================
# NETWORK
# =================================================================================================
NET = dict(
    N=50,
    n_in=TASK["K"],
    d=TASK["d"],
    bias=0.6,
    # OPERATING POINT — REVERTED to gain 10 / noise 1.0 (PJM, 2026-07-24) alongside the move to the
    # cue-delay-probe task. D119 had adopted gain 5 / noise 2.0 on responsiveness+alpha grounds, but a
    # subsequent audit showed that choice broke FITNESS RELIABILITY (r 0.465 -> 0.066, FAIL): doubling
    # noise_sigma quadruples the measurement noise in every fitness estimate. Reliability is the
    # BINDING constraint — without it selection cannot work at all — whereas alpha is a
    # cortex-likeness criterion: desirable, not load-bearing. Reverted to the reliability-verified
    # setting while the new task is established.
    #   gain 10, noise 1.0 -> responsiveness 0.539, alpha 2.49, RELIABILITY 0.465 (PASS)
    #   gain  5, noise 2.0 -> responsiveness 0.360, alpha 1.23, reliability 0.066 (FAIL)
    # alpha 1.23 sits essentially ON Stringer et al.'s NON-SYMMETRIC prediction (~1.25), which is our
    # correct reference: the cortical band 0.7-0.85 assumes the symmetric connectivity we declined to
    # impose (D117), so measuring against it was measuring against the wrong target.
    # Responsiveness has an OPTIMUM, not a monotone preference: too low and the network ignores its
    # input (T0 rev3's failure mode); too high and the state is a passive relay of the stimulus with
    # nothing left for recurrent dynamics to compute or development to shape. gain 10 / noise 1.0 was
    # the latter (responsiveness 0.54, alpha 2.49 - variance concentrated near the 10-dim input
    # subspace). gain 5 is mid-range on both axes.
    input_gain=10.0,
    noise_sigma=1.0,
    present_ms=50,
    tau_slow=100.0,
    nmda_frac=0.5,
    dev_ee_stdp=True,
    dev_wta_comp=True,
    wta_gain=1.0,
)

# =================================================================================================
# DEVELOPMENT & SELECTION
# =================================================================================================
DEV_PASSES = 3        # full sweeps of the training sequence under plasticity.
                      # 1 pass fixes context COVERAGE but gives each context a single exposure;
                      # 3 gives multiple exposures and multiple transitions per context, at ~1.5x the
                      # cost of 1 (fixed per-evaluation overhead dominates the marginal simulated ms).
WARMUP_MS = 200.0     # plasticity OFF; note it CONSUMES stimulus time, so it is added on top of the
                      # passes rather than taken out of them.

N_ASSAYS = 4          # D115: fitness reliability was ~0.05 at n_assays=1 — selection on ~pure noise.


def sequence_ms() -> float:
    """Simulated ms for ONE pass through the training stimulus sequence."""
    return TASK["n_train"] * NET["present_ms"]


def dev_ms() -> float:
    """Development duration for DEV_PASSES full passes under plasticity."""
    return DEV_PASSES * sequence_ms()


def make_task(**overrides):
    kw = {**TASK, **overrides}
    return T.hierarchical_environments(**kw)


def make_net_cfg(**overrides) -> EvoNetConfig:
    return EvoNetConfig(**{**NET, **overrides})


def make_evolve_cfg(**overrides) -> EvolveConfig:
    base = dict(dev_ms=dev_ms(), dev_eta=1e-3, n_assays=N_ASSAYS,
                fitness_mode="regulation_only", seed=12345)
    return EvolveConfig(**{**base, **overrides})


def summary() -> str:
    return (f"TASK K={TASK['K']} d={TASK['d']} r1={TASK['r1']} "
            f"contexts={TASK['n_contexts']} dwell={TASK['context_dwell']} "
            f"n_train/val/test={TASK['n_train']}/{TASK['n_val']}/{TASK['n_test']}\n"
            f"NET  N={NET['N']} present_ms={NET['present_ms']} tau_slow={NET['tau_slow']}\n"
            f"DEV  {DEV_PASSES} passes = {dev_ms():.0f} ms (+{WARMUP_MS:.0f} ms warmup); "
            f"one pass = {sequence_ms():.0f} ms; n_assays={N_ASSAYS}")

# =================================================================================================
# DRIVE NORMALISATION ACROSS THE P SWEEP
# =================================================================================================
# Measured confound: holding per-synapse magnitude fixed while sweeping density makes TOTAL synaptic
# drive scale linearly with P — a 5x swing from density 0.1 to 0.5 (4.07 -> 19.44 per neuron). An
# error-vs-P curve measured that way confounds CAPACITY with DRIVE, and no peak could be attributed.
#
# Scaling: w0 ~ 1/sqrt(K), where K = expected inputs per neuron = density * N. This is the canonical
# BALANCED-STATE scaling (van Vreeswijk & Sompolinsky): it holds input FLUCTUATIONS O(1) while E/I
# balance cancels the mean. The alternative w0 ~ 1/K (constant mean drive) would SUPPRESS fluctuations
# as P grows — and H-D is specifically about the fluctuation-driven regime, so 1/K would quietly
# destroy the regime our hypothesis is about along the very axis we sweep.
#
# This normalises a nuisance variable so the P axis measures P. It does NOT build in the mechanism
# under test (that is regulation, not drive) — same status as the E/I balance precondition (A5).
DENSITY_REF = 0.3          # reference density at which W0_REF was characterised
W0_REF = 0.6


def w0_for_density(density: float) -> float:
    """Per-synapse magnitude that holds input FLUCTUATIONS constant as density (hence P) varies."""
    if density <= 0:
        return W0_REF
    return W0_REF * float(np.sqrt(DENSITY_REF / density))

# =================================================================================================
# TRIAL TASK (D120) — cue -> delay -> probe with an XOR target
# =================================================================================================
# Replaces the covariance-context task, which required NO memory (context was 98.6% identifiable from
# a single stimulus) and whose control removed nothing. Here the memory demand is imposed by
# construction and the floor is chance BY CONSTRUCTION: with the XOR target, every cue-blind and
# every probe-blind strategy scores exactly 0.500.
TRIAL = dict(
    K=10,                 # shared input channels; cue and probe live in the same space
    n_cues=2,             # start minimal (PJM); ramp later
    n_probes=2,
    n_trials=40,          # per split
    n_val=40,
    n_test=40,
    delay_segments=1,     # 1 x present_ms = 50 ms: BELOW tau_slow, so passive decay can carry the
                          # cue. Steps 1/3/4 tested with step 2 on trainer wheels. SWEEP THIS -- where
                          # maintenance must become active is what H-D is about.
    seed=0,
)

# Development passes over the TRIAL sequence. One pass = n_trials x n_seg x present_ms.
# At 40 trials x 4 segments x 50 ms that is 8000 ms/pass, so passes are ~2.7x more expensive than on
# the old task; 2 passes gives 20 exposures of each of the 4 trial types.
TRIAL_DEV_PASSES = 2


def trial_sequence_ms() -> float:
    from .trial_task import seg_layout
    lay = seg_layout(TRIAL["delay_segments"])
    return TRIAL["n_trials"] * lay["n_seg"] * NET["present_ms"]


def trial_dev_ms() -> float:
    return TRIAL_DEV_PASSES * trial_sequence_ms()


def make_trial_task(**overrides):
    from .trial_task import cue_delay_probe
    return cue_delay_probe(**{**TRIAL, **overrides})


def make_trial_evolve_cfg(**overrides) -> EvolveConfig:
    base = dict(dev_ms=trial_dev_ms(), dev_eta=1e-3, n_assays=N_ASSAYS,
                fitness_mode="trial_xor", seed=12345)
    return EvolveConfig(**{**base, **overrides})


def trial_summary() -> str:
    return (f"TRIAL {TRIAL['n_cues']} cues x {TRIAL['n_probes']} probes, "
            f"delay={TRIAL['delay_segments']}x{NET['present_ms']}ms, "
            f"{TRIAL['n_trials']}/{TRIAL['n_val']}/{TRIAL['n_test']} trials\n"
            f"DEV   {TRIAL_DEV_PASSES} passes = {trial_dev_ms():.0f} ms "
            f"(one pass = {trial_sequence_ms():.0f} ms); n_assays={N_ASSAYS}")
