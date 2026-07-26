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


def decode(X, labels, n_splits: int = 3, seed: int = 0) -> float:
    """Cross-validated linear decodability of integer `labels` from feature rows `X` (best fold).

    One-vs-rest ridge in closed form - enough for a decodability read, no sklearn dependency. Rows of
    X are trials, columns are neurons. Returns the max over folds (peak decodability), matching how
    the frozen-chat caller used it (`max(decode(...))` there; here the max is folded in).
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
    return max(accs)


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
                controls=degenerate_checks())


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
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

    print("\n== CHECK 3  degenerate-strategy controls (must sit at chance 0.50) ==")
    for k, v in degenerate_checks().items():
        print("   %-9s val_acc=%.3f" % (k, v))
