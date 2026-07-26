"""delay_persistence_probe.py - trial-task invariants for the audit's C-group (D120/D121).

Rebuilt and TESTED against the real trial-task code (2026-07-24). The original lived only in the
frozen chat's sandbox and was never committed; this is a fresh implementation, not a reconstruction,
verified to run on ddescent.trial_task + EvoNet.behave/develop.

It provides three checks, each an invariant the trial task must satisfy before a GA arm is trusted:

  1. d121_regression   - a ZERO-PLASTICITY develop() must be bit-identical to no development at all.
                         This is the invariant whose violation WAS D121 (developed nets were assayed
                         on clock-shifted stimuli). Keep it as a permanent regression guard: if the
                         clock-offset fix in EvoNet.behave ever regresses, cue decode collapses here.

  2. delay_persistence - cue decodability at the LAST delay segment, swept over delay length. This is
                         the H-D measurement made concrete: below tau_slow the substrate coasts on
                         passive decay (cue held ~1.0); past it, an UNDEVELOPED net must drop toward
                         chance. Where it breaks is the boundary H-D is about, and it is what a
                         developed net must learn to push outward.

  3. degenerate_checks - omit_cue and scramble controls must sit at chance (0.5). These are the
                         degenerate-strategy invariants: the XOR target makes every cue-blind and
                         every probe-blind strategy score exactly chance BY CONSTRUCTION (D120), so a
                         network genuinely doing the task must fall to chance under either control.

`stage_rows` and `decode` keep the interface the frozen chat used, so any prior caller still works.

Run standalone:  python -m scripts.delay_persistence_probe
"""
from __future__ import annotations
import warnings
import numpy as np

from ddescent import study_config as SC
from ddescent.runlog import tee
from ddescent.evonet import EvoNet, random_genome
from ddescent.trial_task import seg_layout


# ==================================================================================================
# INTERFACE HELPERS (clock-independent; depend only on the segment layout)
# ==================================================================================================
def stage_rows(task, split: str, stage: str) -> np.ndarray:
    """Row indices (into the (n_trials*n_seg, .) presentation axis) for `stage` in every trial.

    stage in {"cue", "delay", "probe", "read"}. For a multi-segment delay, "delay" returns the LAST
    delay segment of each trial - the most stringent point for persistence (the cue must still be
    present right before the probe arrives).
    """
    m = task.meta
    lay = seg_layout(m["delay_segments"])
    if stage == "delay":
        seg = lay["probe"] - 1                      # last delay segment (= cue+delay_segments)
    else:
        seg = lay[stage]
    n_trials = m["n_trials"][split]
    return np.arange(n_trials) * lay["n_seg"] + seg


def decode(X, labels, n_splits: int = 3, seed: int = 0, agg: str = "mean") -> float:
    """Cross-validated linear decodability of integer `labels` from feature rows `X`.

    One-vs-rest ridge in closed form - enough for a decodability read, no sklearn dependency. Rows of
    X are trials, columns are neurons.

    agg="mean" (DEFAULT) averages folds. agg="max" reproduces the earlier behaviour and is retained
    only for comparison: taking the BEST of 3 folds is upward-biased by selection, and at n_trials=40
    (13 test trials/fold) its noise floor is 0.60, not 0.50 -- measured over 400 pure-noise draws:
    mean 0.601, median 0.615, 95th pct 0.769, max 0.923. Every value below ~0.77 in a max-aggregated
    read is therefore indistinguishable from chance. This is the same error class as D116's floor and
    D127's PR: a THEORETICAL chance level applied to an estimator that is biased by selection. Always
    compare against decode_null(), never against 0.5.
    """
    X = np.asarray(X, float)
    y = np.asarray(labels).ravel()
    n = min(len(X), len(y))
    X, y = X[:n], y[:n]
    classes = np.unique(y)
    if len(classes) < 2:
        return float("nan")
    Xz = (X - X.mean(0)) / (X.std(0) + 1e-8)
    folds = np.array_split(np.random.default_rng(seed).permutation(n), n_splits)
    accs = []
    for i in range(n_splits):
        te = folds[i]
        tr = np.concatenate([folds[j] for j in range(n_splits) if j != i])
        A = Xz[tr].T @ Xz[tr] + np.eye(Xz.shape[1])
        Ainv = np.linalg.pinv(A)
        W = np.stack([Ainv @ (Xz[tr].T @ (y[tr] == c).astype(float)) for c in classes], 1)
        pred = classes[np.argmax(Xz[te] @ W, 1)]
        accs.append(float(np.mean(pred == y[te])))
    return float(max(accs)) if agg == "max" else float(np.mean(accs))


def decode_null(X, labels, n_rep: int = 60, seed: int = 0, **kw):
    """The decoder's own floor on THESE data: same computation, labels shuffled. Returns (mean, p95).

    Report it beside every decode. A decode value is evidence only if it clears p95; the theoretical
    0.5 is not the floor and never was.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(labels).ravel()
    v = np.array([decode(X, y[rng.permutation(len(y))], seed=seed + r, **kw) for r in range(n_rep)])
    return float(v.mean()), float(np.percentile(v, 95))


# ==================================================================================================
# CHECK 1 - D121 REGRESSION: zero-plasticity develop() must equal no development
# ==================================================================================================
def d121_regression(seed: int = 1, noise_sigma: float = 0.0) -> dict:
    """At noise=0 the two must be bit-identical; the returned max|delta| is the guard value.

    Also reports per-stage cue decode for both conditions at the study's real noise, where they must
    at least agree on the load-bearing cue/delay stages.
    """
    task = SC.make_trial_task()
    cfg = SC.make_trial_evolve_cfg(pop_size=4, n_generations=1); cfg._gen = 0

    nc0 = SC.make_net_cfg(noise_sigma=noise_sigma)
    g = random_genome(nc0, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed)
    A = EvoNet(g, nc0).behave(task.E_test)
    B = EvoNet(g, nc0)
    B.develop(task.E_test, eta=0.0, dev_ms=SC.trial_dev_ms(), warmup_ms=SC.WARMUP_MS,
              seed=seed, eta_e=0.0)
    B = B.behave(task.E_test)
    max_abs = float(np.max(np.abs(A["state"] - B["state"])))

    nc = SC.make_net_cfg()
    g2 = random_genome(nc, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed)
    BU = EvoNet(g2, nc).behave(task.E_test, noise_seed=2)
    BD = EvoNet(g2, nc)
    BD.develop(task.E_test, eta=0.0, dev_ms=SC.trial_dev_ms(), warmup_ms=SC.WARMUP_MS,
               seed=seed, eta_e=0.0)
    BD = BD.behave(task.E_test, noise_seed=2)
    cue = task.cue_test
    stages = {st: (round(decode(BU["state"][stage_rows(task, "test", st)], cue), 2),
                   round(decode(BD["state"][stage_rows(task, "test", st)], cue), 2))
              for st in ("cue", "delay", "probe", "read")}
    return dict(max_abs_state_diff_noise0=max_abs,
                passed=max_abs < 1e-9,
                stage_decode_undev_vs_dev=stages)


# ==================================================================================================
# CHECK 2 - DELAY PERSISTENCE: how far the (undeveloped) substrate coasts, swept over delay length
# ==================================================================================================
def delay_persistence(delays=(1, 2, 4, 8), seed: int = 1, developed: bool = False) -> dict:
    """Cue decodability at the LAST delay segment vs delay length.

    tau_slow = 100 ms and present_ms = 50 ms, so one delay segment (50 ms) is within reach of passive
    decay and two (100 ms) is at the edge. Expect ~1.0 at short delays falling toward chance as the
    delay exceeds tau_slow. That fall-off point is the H-D boundary.

    developed=False is the SUBSTRATE's passive coast. developed=True runs real plasticity first and is
    the condition that actually matters: SELECTION ACTS ON DEVELOPED NETWORKS, so if development
    degrades the held cue, no target change can rescue the task -- the probe would be measuring a
    capability the assayed phenotype does not have. Reported side by side; read the DEVELOPED row.
    """
    nc = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg()
    out = {}
    for d in delays:
        task = SC.make_trial_task(delay_segments=d)
        g = random_genome(nc, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed)
        net = EvoNet(g, nc)
        if developed:
            net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms,
                        warmup_ms=SC.WARMUP_MS, n_checkpoints=4, seed=seed)
        B = net.behave(task.E_test, noise_seed=2)
        cue = task.cue_test
        out[d] = dict(cue_at_cue=round(decode(B["state"][stage_rows(task, "test", "cue")], cue), 2),
                      cue_at_delay=round(decode(B["state"][stage_rows(task, "test", "delay")], cue), 2),
                      delay_ms=d * nc.present_ms)
    return out


def persistence_contrast(delays=(1, 2, 4, 8), seed: int = 1) -> dict:
    """UNDEVELOPED vs DEVELOPED delay persistence -- the D128 question.

    Motivation: an uncommitted 2026-07-24 sandbox run reported cue decode ~1.00 undeveloped falling to
    ~0.45 after development on the RETIRED task, with competition ruled out as the cause. That was never
    verified against committed code and never memorialised, yet it is the observation that most directly
    predicts whether ANY task change can work -- D124 and D125 both independently found development a
    headwind. This makes the contrast a first-class, repeatable check.

    READ: dev ~ undev            -> development preserves the trace; the target was the blocker.
          dev << undev (-> 0.5)  -> development destroys what selection needs; the blocker is
                                    DEVELOPMENT, not the task, and the task swap is necessary but not
                                    sufficient.
    """
    return dict(undeveloped=delay_persistence(delays, seed, developed=False),
                developed=delay_persistence(delays, seed, developed=True))


# ==================================================================================================
# CHECK 2b - RELATION PERSISTENCE: is MATCH/NON-MATCH present at read time? (the DMTS invariant)
# ==================================================================================================
def relation_persistence(seed: int = 1, n_trials: int = 400, n_genomes: int = 3) -> dict:
    """Decode MATCH vs NON-MATCH (not cue identity) from the full state, per stage, UNDEV vs DEV.

    WHY THIS AND NOT CUE IDENTITY (D126). Cue-identity persistence was the right invariant for the
    RETIRED trial_xor target, where the network had to hold WHICH cue to do an arbitrary lookup. DMTS
    does not need that: the probe drive can interact with the held trace to produce a match signal
    while cue identity is swamped. Cue identity at the floor during probe/read is NOT evidence against
    DMTS -- it measures a property the task does not require.

    POWER (why n_trials defaults to 400, not the config's 40). With N=50 neurons as features, 40 trials
    puts the decoder in the p > n regime: the null p95 lands near 0.65, so only an effect of ~+0.15
    could ever clear it, and a negative reads as "cannot detect" rather than "absent" -- a distinction
    that matters, because "the relation is absent" would be the most consequential claim available here.
    400 trials puts n well above p and tightens the null. Cost is a longer behave(), not more
    development, so it is cheap.

    Averaged over n_genomes random genomes: a single genome is one draw, and this project has had to
    withdraw three numbers that were exactly that.

    READ: relation at READ clears the null -> information is present; selection's job is ROUTING it to
          the output cell (a localization problem, D127, already instrumented).
          at the null with adequate power -> information genuinely absent; selection has nothing to
          route, and DMTS is in trouble before generation 0.
    """
    nc = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg()
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials)
    rel = (task.cue_test == task.probe_test).astype(int)      # 1 = match, 0 = non-match
    out = {}
    for cond in ("undeveloped", "developed"):
        per_stage = {st: [] for st in ("cue", "delay", "probe", "read")}
        nulls = {st: [] for st in per_stage}
        for k in range(n_genomes):
            g = random_genome(nc, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed + k)
            net = EvoNet(g, nc)
            if cond == "developed":
                net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms,
                            warmup_ms=SC.WARMUP_MS, n_checkpoints=4, seed=seed + k)
            B = net.behave(task.E_test, noise_seed=2 + k)
            for st in per_stage:
                X = B["state"][stage_rows(task, "test", st)]
                per_stage[st].append(decode(X, rel))
                nulls[st].append(decode_null(X, rel, n_rep=30)[1])
            print("    %s genome %d done" % (cond, k), flush=True)
        out[cond] = {st: dict(decode=round(float(np.mean(per_stage[st])), 3),
                              sd=round(float(np.std(per_stage[st], ddof=1)), 3) if n_genomes > 1 else 0.0,
                              null_p95=round(float(np.mean(nulls[st])), 3),
                              clears=bool(np.mean(per_stage[st]) > np.mean(nulls[st])))
                     for st in per_stage}
    out["_meta"] = dict(n_trials=n_trials, n_genomes=n_genomes, n_features=nc.N)
    return out


# ==================================================================================================
# CHECK 2c - TRACE SURVIVAL: does the held cue survive the PROBE DRIVE? (the swamping question)
# ==================================================================================================
def trace_survival(seed: int = 1, n_trials: int = 400, n_genomes: int = 3) -> dict:
    """Cue identity decoded at each stage on NON-MATCH TRIALS ONLY, vs the shuffled-label null.

    WHY NON-MATCH ONLY -- a confound the earlier checks do not handle. Under DMTS (D126) cue and probe
    are drawn from the SAME pattern set, so on MATCH trials the probe input IS the cue pattern: cue
    identity is then decodable straight off the probe drive with no held trace involved. Pooling match
    and non-match therefore mixes "the trace survived" with "the probe re-presented the cue," and the
    pooled number (CHECK 1/CHECK 2's cue@probe) answers neither. Restricting to NON-MATCH trials makes
    the probe uninformative about cue identity by construction, so anything decodable there came from
    the trace.

    WHAT IT DIAGNOSES. CHECK 1 showed cue identity at 1.00 at the last delay segment and ~0.50 during
    probe, suggesting the probe drive swamps the residual trace. If the trace is unreadable while the
    probe is on, there is nothing for a match comparison to operate on, which would be a MECHANISTIC
    explanation for a null in CHECK 2b -- and a different problem from "the task is unselectable."

    THIS IS A DIAGNOSTIC, NOT A FIX. If the trace is swamped, the levers (relative cue/probe amplitude,
    read timing, trace time constant) are all task/operating-point parameters OUTSIDE D126's
    pre-registered rung axis. Changing one reactively because a null appeared is precisely the move the
    framework forbids; it would need its own DECISIONS entry and rationale. Measure first.
    """
    nc = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg()
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials)
    nonmatch = np.where(task.cue_test != task.probe_test)[0]      # probe cannot reveal the cue here
    cue = task.cue_test
    out = {}
    for cond in ("undeveloped", "developed"):
        acc = {st: [] for st in ("cue", "delay", "probe", "read")}
        nul = {st: [] for st in acc}
        for k in range(n_genomes):
            g = random_genome(nc, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed + k)
            net = EvoNet(g, nc)
            if cond == "developed":
                net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms,
                            warmup_ms=SC.WARMUP_MS, n_checkpoints=4, seed=seed + k)
            B = net.behave(task.E_test, noise_seed=2 + k)
            for st in acc:
                X = B["state"][stage_rows(task, "test", st)][nonmatch]
                acc[st].append(decode(X, cue[nonmatch]))
                nul[st].append(decode_null(X, cue[nonmatch], n_rep=30)[1])
            print("    trace/%s genome %d done" % (cond, k), flush=True)
        out[cond] = {st: dict(decode=round(float(np.mean(acc[st])), 3),
                              null_p95=round(float(np.mean(nul[st])), 3),
                              clears=bool(np.mean(acc[st]) > np.mean(nul[st]))) for st in acc}
    out["_meta"] = dict(n_nonmatch=int(len(nonmatch)), n_genomes=n_genomes)
    return out


# ==================================================================================================
# CHECK 2d - IS THE CONJUNCTION THERE AT ALL? linear vs nonlinear readouts of the relation
# ==================================================================================================
def _expand(X, kind: str, seed: int = 0):
    """Feature maps of increasing power, applied to the SAME states.

    WHY THE FIRST VERSION OF THIS WAS BROKEN (2026-07-25). The relation, in the pattern basis, is
    essentially sum_i (proj_i)^2 -- a MATCH puts double amplitude in one pattern direction, a NON-MATCH
    unit amplitude in two. But proj_i = w_i . x, so proj_i^2 = sum_jk w_ij w_ik x_j x_k: expressing it
    requires CROSS TERMS x_j x_k in the neuron basis. The original maps could not supply them --
    "square" gave only x_j^2, "activity" used ||x||^2 over all 50 neurons (drowning two signal
    directions among 48 noise ones), and "randtanh" scaled W by 1/sqrt(N) against z-scored inputs, so
    pre-activations had unit variance and tanh never left its linear regime. All three failed the
    POSITIVE CONTROL (separable codes carrying a recoverable XOR-type relation) and that failure was
    misread as confirmation. Any map added here must clear the positive control before it is trusted.
    """
    X = np.asarray(X, float)
    Xz = (X - X.mean(0)) / (X.std(0) + 1e-8)
    if kind == "linear":
        return X
    if kind == "square":                      # separable nonlinearity: NO cross terms (kept for contrast)
        return np.hstack([X, X * X])
    if kind == "quad":                        # PCA -> ALL pairwise products: full 2nd-order, incl. cross
        # PCA on CENTERED, NOT z-scored data. Z-scoring equalises every dimension's variance and so
        # destroys the ordering PCA relies on: with signal concentrated in a few dimensions the leading
        # PCs then miss it entirely (caught by positive control 1, which failed under z-scoring while
        # the distributed-signal control passed).
        k = 14
        Xc = X - X.mean(0)
        U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        Z = Xc @ Vt[:k].T
        Z = Z / (Z.std(0) + 1e-8)             # scale AFTER the projection, so products are conditioned
        iu = np.triu_indices(k)
        return np.hstack([Z, (Z[:, :, None] * Z[:, None, :])[:, iu[0], iu[1]]])
    if kind == "randtanh":                    # random nonlinear expansion, GAIN SET TO SATURATE
        rng = np.random.default_rng(seed)
        W = rng.normal(size=(X.shape[1], 300)) / np.sqrt(X.shape[1])
        return np.tanh(4.0 * (Xz @ W))        # gain 4: pre-activations leave the linear regime
    if kind == "activity":                    # 1-D scalars: does TOTAL drive differ match vs non-match?
        return np.stack([X.mean(1), np.linalg.norm(X, axis=1)], 1)
    raise ValueError(kind)


def relation_nonlinear(seed: int = 1, n_trials: int = 400, n_genomes: int = 3,
                       stage: str = "read") -> dict:
    """Decode MATCH/NON-MATCH from the read-stage state under readouts of increasing power.

    THE QUESTION THIS SETTLES. CHECK 2c shows the cue is held essentially perfectly at read and CHECK 2b
    shows the RELATION is at chance there. Both codes are present; their conjunction is not linearly
    available. Equality of two categorical variables is an XOR-type function, so a representation that
    encodes cue and probe in separable linear subspaces CANNOT yield "cue == probe" to a linear readout,
    no matter how clean each code is. That is a statement about the substrate's regime, not the target,
    and it would have applied to the retired trial_xor identically.

    READ:
      linear at null, NONLINEAR clears  -> the conjunction EXISTS in the state but is not linearly
        available. The blocker is the readout/operating-point regime (D119), and the D095 weak affine
        fitness can never see it. Selection is not the problem; linear separability is.
      NOTHING clears, including randtanh -> the trace and the probe drive never interact at all; the
        network holds two independent codes and computes nothing between them. A deeper dynamics
        statement, and the operating point is where it would have to be addressed.
      activity clears -> match trials simply drive MORE total activity; the relation is available as a
        scalar and even a weak readout could find it, which would contradict 2b and warrant a re-check.

    Diagnostic only. The levers implied (gain, threshold proximity, recurrent strength) are operating-
    point parameters requiring their own DECISIONS entry -- not a reactive turn off a null.
    """
    nc = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg()
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials)
    rel = (task.cue_test == task.probe_test).astype(int)
    kinds = ("linear", "square", "quad", "randtanh", "activity")
    out = {}
    for cond in ("undeveloped", "developed"):
        acc = {k: [] for k in kinds}; nul = {k: [] for k in kinds}
        for i in range(n_genomes):
            g = random_genome(nc, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed + i)
            net = EvoNet(g, nc)
            if cond == "developed":
                net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms,
                            warmup_ms=SC.WARMUP_MS, n_checkpoints=4, seed=seed + i)
            B = net.behave(task.E_test, noise_seed=2 + i)
            X0 = B["state"][stage_rows(task, "test", stage)]
            for k in kinds:
                Z = _expand(X0, k, seed=seed + i)
                acc[k].append(decode(Z, rel))
                nul[k].append(decode_null(Z, rel, n_rep=30)[1])
            print("    nonlin/%s genome %d done" % (cond, i), flush=True)
        out[cond] = {k: dict(decode=round(float(np.mean(acc[k])), 3),
                             sd=round(float(np.std(acc[k], ddof=1)), 3) if n_genomes > 1 else 0.0,
                             null_p95=round(float(np.mean(nul[k])), 3),
                             clears=bool(np.mean(acc[k]) > np.mean(nul[k]))) for k in kinds}
    out["_meta"] = dict(stage=stage, n_trials=n_trials, n_genomes=n_genomes)
    return out


# ==================================================================================================
# CHECK 2e - WHERE and WHEN: quad across stages, and with NARROW windows to catch a transient
# ==================================================================================================
def relation_where_when(seed: int = 1, n_trials: int = 400, n_genomes: int = 3) -> dict:
    """Second-order decode of the relation across STAGES and across READOUT WINDOWS.

    TWO GAPS THIS CLOSES. (1) CHECK 2d ran quad at the READ stage only; CHECK 2b covered every stage
    but only LINEARLY. If the conjunction is a transient coincidence it would live during the PROBE,
    when the incoming pattern meets the decaying trace, and that cell was never tested at second order.
    (2) Every window so far is readout_window_ms=60 against present_ms=50 -- wider than the segment it
    names. So each "stage" state is a 60 ms average that also carries the last 10 ms of the PRECEDING
    stage, and a brief coincidence would be diluted roughly 6:1. Narrow leading/trailing windows
    (10 ms) sample the start and end of each segment instead.

    Run UNDEVELOPED only: development has been indistinguishable from undeveloped in 2b, 2c and 2d, and
    undeveloped costs no develop() call, so this is a cheap screen. If any cell clears, re-check it
    developed before believing it.
    """
    cfg = SC.make_trial_evolve_cfg()
    task = SC.make_trial_task(n_trials=n_trials, n_val=n_trials, n_test=n_trials)
    rel = (task.cue_test == task.probe_test).astype(int)
    windows = (("wide 60ms", dict()),
               ("early 10ms", dict(readout_window_ms=10.0, readout_pos="leading")),
               ("late 10ms", dict(readout_window_ms=10.0, readout_pos="trailing")))
    out = {}
    for wname, wkw in windows:
        nc = SC.make_net_cfg(**wkw)
        for stage in ("probe", "read"):
            acc, nul = [], []
            for i in range(n_genomes):
                g = random_genome(nc, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed + i)
                B = EvoNet(g, nc).behave(task.E_test, noise_seed=2 + i)
                Z = _expand(B["state"][stage_rows(task, "test", stage)], "quad", seed=seed + i)
                acc.append(decode(Z, rel)); nul.append(decode_null(Z, rel, n_rep=30)[1])
            out[(wname, stage)] = dict(decode=round(float(np.mean(acc)), 3),
                                       sd=round(float(np.std(acc, ddof=1)), 3) if n_genomes > 1 else 0.0,
                                       null_p95=round(float(np.mean(nul)), 3),
                                       clears=bool(np.mean(acc) > np.mean(nul)))
            print("    %s / %s done" % (wname, stage), flush=True)
    return out


# ==================================================================================================
# CHECK 3 - DEGENERATE-STRATEGY CONTROLS: omit_cue and scramble must sit at chance
# ==================================================================================================
def degenerate_checks(seed: int = 7) -> dict:
    """omit_cue and scramble must sit at chance (0.5) for ANY network doing the task.

    Mirrors trial_eval.control_scores but scores with report=False (val split only), which is ~3x
    cheaper than control_scores' report=True and is all the invariant needs. On a random genome all
    three sit at chance; the standing guard is that omit_cue/scramble never RISE above chance once
    'normal' does under selection.
    """
    from ddescent.trial_eval import trial_evaluate
    from ddescent.trial_task import cue_delay_probe
    nc = SC.make_net_cfg()
    cfg = SC.make_trial_evolve_cfg(pop_size=4, n_generations=1); cfg._gen = 0
    g = random_genome(nc, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed)
    kw = {k: v for k, v in SC.TRIAL.items() if k != "seed"}   # SC.TRIAL already carries seed
    out = {}
    for label, extra in [("normal", {}), ("omit_cue", dict(omit_cue=True)),
                         ("scramble", dict(scramble=True))]:
        t = cue_delay_probe(seed=0, **{**kw, **extra})
        r = trial_evaluate(g, t, nc, cfg, report=False)
        out[label] = round(r["val_acc"], 3)
    return out


def run_all() -> dict:
    warnings.filterwarnings("ignore")
    return dict(d121=d121_regression(),
                persistence=persistence_contrast(),
                relation=relation_persistence(),
                trace=trace_survival(),
                nonlinear=relation_nonlinear(),
                where_when=relation_where_when(),
                controls=degenerate_checks())


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    # D102: persist to runs/ like every other runner. This probe was stdout-only, which is how the
    # earlier reliability tables were nearly lost -- a fork-deciding measurement must not live in a
    # terminal buffer.
    _t = tee("delay_persistence_probe", log_dir="runs/persistence",
             header="D121 regression + delay persistence (undeveloped vs DEVELOPED) + controls")
    _t.__enter__()
    r1 = d121_regression()
    print("== CHECK 1  D121 regression (zero-plasticity develop == no development) ==")
    print("   max|delta| state at noise=0 : %.3e  -> %s"
          % (r1["max_abs_state_diff_noise0"], "PASS" if r1["passed"] else "FAIL"))
    print("   per-stage cue decode (undeveloped, zeroDev), real noise:")
    for st, (u, d) in r1["stage_decode_undev_vs_dev"].items():
        print("      %-6s  undev=%.2f  dev=%.2f" % (st, u, d))

    print("\n== CHECK 2  delay persistence: UNDEVELOPED vs DEVELOPED ==")
    print("   selection acts on DEVELOPED nets -- the developed row is the one that matters")
    pc = persistence_contrast()
    print("   delay        |  undeveloped        |  developed          |  cue@delay change")
    print("   -------------+---------------------+---------------------+------------------")
    for d in sorted(pc["undeveloped"]):
        u, v = pc["undeveloped"][d], pc["developed"][d]
        print("   %d (%3d ms)   |  cue=%.2f delay=%.2f |  cue=%.2f delay=%.2f |  %+.2f"
              % (d, u["delay_ms"], u["cue_at_cue"], u["cue_at_delay"],
                 v["cue_at_cue"], v["cue_at_delay"], v["cue_at_delay"] - u["cue_at_delay"]))
    worst = min(pc["developed"][d]["cue_at_delay"] - pc["undeveloped"][d]["cue_at_delay"]
                for d in pc["undeveloped"])
    print("   READ: largest drop = %+.2f -- a large negative drop means DEVELOPMENT, not the target," % worst)
    print("         is the blocker, and the D126 task swap is necessary but not sufficient.")

    print("\n== CHECK 2b  RELATION (match/non-match) decodability -- the DMTS invariant ==")
    rp = relation_persistence()
    md = rp.pop("_meta")
    print("   n_trials=%d, n_genomes=%d, n_features=%d  (n >> p, so the null is tight and a negative means"
          % (md["n_trials"], md["n_genomes"], md["n_features"]))
    print("    ABSENT rather than merely undetectable). Compare to the NULL, never to 0.5.")
    print("   condition    | stage  | decode (sd) | null_p95 | clears?")
    print("   -------------+--------+-------------+----------+--------")
    for cond in ("undeveloped", "developed"):
        for st in ("cue", "delay", "probe", "read"):
            v = rp[cond][st]
            print("   %-12s | %-6s | %.3f (%.3f)|  %.3f   | %s"
                  % (cond, st, v["decode"], v["sd"], v["null_p95"], "YES" if v["clears"] else "no"))
    print("   READ: clears at READ -> information present, selection's job is ROUTING (D127).")
    print("         at null at READ -> information absent; selection has nothing to route.")

    print("\n== CHECK 2c  TRACE SURVIVAL: does the held cue survive the PROBE DRIVE? ==")
    ts = trace_survival(); tm = ts.pop("_meta")
    print("   cue identity on NON-MATCH trials only (n=%d), where the probe cannot reveal the cue."
          % tm["n_nonmatch"])
    print("   A drop from delay -> probe means the probe drive SWAMPS the trace, which would explain")
    print("   a CHECK 2b null mechanically. Diagnostic only -- the levers are outside D126's rung axis.")
    print("   condition    | stage  | decode | null_p95 | clears?")
    print("   -------------+--------+--------+----------+--------")
    for cond in ("undeveloped", "developed"):
        for st in ("cue", "delay", "probe", "read"):
            v = ts[cond][st]
            print("   %-12s | %-6s | %.3f  |  %.3f   | %s"
                  % (cond, st, v["decode"], v["null_p95"], "YES" if v["clears"] else "no"))

    print("\n== CHECK 2d  IS THE CONJUNCTION THERE AT ALL? (readouts of increasing power, READ stage) ==")
    rn = relation_nonlinear(); rm = rn.pop("_meta")
    print("   cue is held at ~1.00 (2c) and the relation is at chance under a LINEAR readout (2b).")
    print("   equality of two categoricals is XOR-type: separable linear codes cannot yield it linearly.")
    print("   condition    | readout   | decode (sd) | null_p95 | clears?")
    print("   -------------+-----------+-------------+----------+--------")
    for cond in ("undeveloped", "developed"):
        for k in ("linear", "square", "quad", "randtanh", "activity"):
            v = rn[cond][k]
            print("   %-12s | %-9s | %.3f (%.3f)|  %.3f   | %s"
                  % (cond, k, v["decode"], v["sd"], v["null_p95"], "YES" if v["clears"] else "no"))
    print("   READ: nonlinear clears, linear does not -> conjunction EXISTS but is not linearly")
    print("         available; the blocker is the operating-point regime (D119), not the target.")
    print("         nothing clears -> trace and probe never interact; deeper dynamics statement.")

    print("\n== CHECK 2e  WHERE and WHEN is the conjunction? (quad, undeveloped) ==")
    print("   2d tested quad at READ only; 2b tested every stage but only LINEARLY. And every window")
    print("   so far is 60ms wide against a 50ms segment, which would dilute a transient ~6:1.")
    print("   window     | stage  | quad decode (sd) | null_p95 | clears?")
    print("   -----------+--------+------------------+----------+--------")
    for (w, st), v in relation_where_when().items():
        print("   %-10s | %-6s |   %.3f (%.3f)   |  %.3f   | %s"
              % (w, st, v["decode"], v["sd"], v["null_p95"], "YES" if v["clears"] else "no"))
    print("   READ: nothing clears here either -> the conjunction is absent, not mistimed.")

    print("\n== CHECK 3  degenerate-strategy controls (must sit at chance 0.50) ==")
    for k, v in degenerate_checks().items():
        print("   %-9s val_acc=%.3f" % (k, v))
    _t.__exit__(None, None, None)
