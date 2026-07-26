"""TRIAL-STRUCTURED EVALUATION for the cue -> delay -> probe task.

Mirrors `evolve.evaluate()` but scores TRIALS rather than a continuous stimulus stream:
  * development runs over the flattened trial sequence (the drive tiles, so multiple passes work);
  * the response is read from the READ segment of each trial, not averaged over a whole presentation;
  * the three-way split discipline (D113) is preserved exactly — develop on train, SELECT on val,
    REPORT on test — and enforced by the same kind of destroy-a-split audit check.

WHY A SEPARATE SCORE. The XOR target makes chance exact rather than estimated: without the held cue
the probe carries no information about the sign, so every cue-blind strategy scores 0.500 and every
probe-blind strategy scores 0.500 (measured, n=200). NMSE against the trial targets therefore has a
principled zero point — 1.0 is "no better than predicting the mean" — which is what the old
memoryless floor could never provide (a static random expansion matched it, D116).

Accuracy is reported alongside NMSE because the target is binary and chance is exactly 0.5, which
makes the number directly interpretable. NMSE remains the fitness basis so the scale is continuous
and selection sees graded differences rather than a step function.
"""
from __future__ import annotations
import zlib
import numpy as np

from .evonet import EvoNet, EvoNetConfig, Genome
from .evolve import _affine_nmse, covariance_powerlaw_exponent


def _score_split(net, task, split: str, noise_seed: int, want_state: bool = False):
    """(NMSE, accuracy) on one split, read from the READ segment of each trial.

    want_state=True additionally returns the FULL per-neuron state at the read rows, (n_trials, N),
    which the D127 localization diagnostic scores neuron-by-neuron. It costs nothing extra: the state
    is already computed by behave(); only the report path asks for it.
    """
    E, Y, _, _ = task._split(split)
    B = net.behave(E, noise_seed=noise_seed)
    rows = task.response_rows(split)
    R = B["rates"][rows]                       # (n_trials, n_out) -- the D095 designated slice
    err = _affine_nmse(Y, R)
    # accuracy: refit the same affine map and compare signs. The readout is gain+offset on ONE
    # neuron per output (D095) — it cannot mix neurons, so the network must route the answer to the
    # designated output cell rather than have the decoder find it.
    acc_cols = []
    for j in range(Y.shape[1]):
        A = np.vstack([R[:, j], np.ones(len(R))]).T
        coef, *_ = np.linalg.lstsq(A, Y[:, j], rcond=None)
        acc_cols.append(np.sign(A @ coef + 1e-12) == np.sign(Y[:, j]))
    if want_state:
        return float(err), float(np.mean(acc_cols)), B["state"][rows], Y
    return float(err), float(np.mean(acc_cols))


# ==================================================================================================
# D127 - LOCALIZATION: is the computation concentrated on the readout cell, or distributed?
# ==================================================================================================
def _per_neuron_scores(S, y):
    """Accuracy of EVERY neuron scored INDEPENDENTLY, each with its own D095-weak affine readout.

    N weak reads, never one pooled decoder across neurons: pooling would restore exactly the mixing
    power D095 removes, and would reopen the RC degeneracy. Each read is gain+offset on one neuron.
    """
    ones = np.ones(len(y))
    acc = np.empty(S.shape[1])
    for j in range(S.shape[1]):
        A = np.vstack([S[:, j], ones]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        acc[j] = np.mean(np.sign(A @ coef + 1e-12) == np.sign(y))
    return acc


def _participation_ratio(scores, thr: float) -> float:
    """PR = (sum x)^2 / sum x^2 over x = max(0, score - thr): the EFFECTIVE NUMBER of neurons carrying
    task signal. Range ~1..N. Extremum-free, unlike best-over-N, whose expectation rises with in-degree
    at fixed N (D125) -- fatal for a metric read along a P axis.

    thr MUST come from the measured NULL, not from theoretical chance. The per-neuron readout is fit
    IN-SAMPLE, so a pure-noise neuron does not score 0.5: at n_val=200 it floors near 0.56. Subtracting
    0.5 therefore leaves every neuron with positive mass and PR is dominated by the noise floor -- a
    single perfect carrier among 49 noise neurons reads PR ~29 instead of ~1 (measured). Referencing the
    scrambled-target null removes that bias by construction.
    """
    x = np.clip(np.asarray(scores, float) - thr, 0.0, None)
    tot = float(x.sum())
    return float(tot * tot / (float(np.sum(x * x)) + 1e-18)) if tot > 0 else 0.0


def localization_report(S, y, out_index: int, n_null: int = 5, seed: int = 0) -> dict:
    """D127 primary endpoint (PR) plus descriptive secondaries, with PR's own scrambled-target null.

    THE NULL IS NOT OPTIONAL. With every neuron at chance, x = max(0, score - chance) is still
    positive noise and PR returns a number, so "PR = 7" is meaningless on its own. Only PR - PR_null
    is interpreted (D127). The null is recomputed wherever this is called, never reused across P,
    because the per-neuron score-noise distribution may itself vary with P.

    INTERPRETABILITY GATE (D127): do not read PR until loc_mean clears chance. At generation 0 on a
    chance-floor task nothing is above chance and PR is noise against noise.
    """
    sc = _per_neuron_scores(S, y)
    rng = np.random.default_rng(seed)
    null_vecs = [_per_neuron_scores(S, y[rng.permutation(len(y))]) for _ in range(max(1, n_null))]
    null_pool = np.concatenate(null_vecs)
    thr = float(np.percentile(null_pool, 95))     # self-calibrating: 95th pct of the NULL score pool
    pr = _participation_ratio(sc, thr)
    # PR_null: the SAME procedure applied to null draws, so "no signal" has a measured PR, not 0.
    pr_null = float(np.mean([_participation_ratio(v, thr) for v in null_vecs]))
    return dict(
        loc_pr=pr, loc_pr_null=pr_null, loc_pr_excess=pr - pr_null,   # PRIMARY (D127)
        loc_single=float(sc[out_index]),                              # the neuron the FITNESS reads
        loc_mean=float(sc.mean()), loc_best=float(sc.max()),          # secondaries, descriptive only
        loc_gap=float(sc.max() - sc.mean()),
        loc_n_above=int((sc > thr).sum()), loc_thr=thr, loc_null_mean=float(null_pool.mean()),
        loc_n_neurons=int(S.shape[1]),
    )


def trial_evaluate(genome: Genome, task, net_cfg: EvoNetConfig, cfg=None,
                   report: bool = False) -> dict:
    """DEVELOP, then score the developed phenotype on trials, averaged over `n_assays` noise draws.

    Returns `trial_score` = 1.0 - val_err, so 0.0 is "no better than predicting the mean" and larger
    is better. The offset is cosmetic (it cancels in the replicator softmax) but keeps the reported
    scale interpretable against a zero point that is exact rather than estimated.
    """
    net = EvoNet(genome, net_cfg)
    n_assays = 1 if cfg is None else max(1, cfg.n_assays)
    base_seed = 0 if cfg is None else cfg.seed
    gseed = (zlib.crc32(genome.mag.tobytes()) ^ (base_seed & 0xFFFFFFFF)) & 0x7FFFFFFF

    # --- development over the TRIAL sequence -------------------------------------------------
    # E_train is the flattened trial stream, so `develop()` drives it unchanged; the drive tiles to
    # cover warmup + dev_ms, which is what makes multi-pass development possible at all.
    dev_converged, dev_aborted = True, False
    if cfg is None or cfg.dev_ms > 0:
        eta = 1e-3 if cfg is None else cfg.dev_eta
        dev_ms = 3000.0 if cfg is None else cfg.dev_ms
        dev_res = net.develop(task.E_train, eta=eta, dev_ms=dev_ms, warmup_ms=200.0,
                              n_checkpoints=4, seed=gseed)
        dev_converged = bool(dev_res.get("converged", True))
        dev_aborted = ("NaN" in dev_res.get("reason", ""))

    gen_off = 0 if cfg is None else (getattr(cfg, "_gen", 0) * 100003)
    ev, va = [], []                                  # validation err / acc  (SELECTION)
    te, ta, tr, tra = [], [], [], []                 # test / train          (REPORT ONLY)
    alpha, cue_ctrl, scr_ctrl = [], [], []
    loc = {}                                         # D127 localization, report path only
    for a in range(n_assays):
        s_va = (gseed + gen_off + 4 * a + 1) & 0x7FFFFFFF
        if report and a == 0:
            e, acc, S_val, Y_val = _score_split(net, task, "val", s_va, want_state=True)
            loc = localization_report(S_val, Y_val[:, 0],
                                      out_index=net_cfg.N - net_cfg.d,   # LAST d units are the output
                                      seed=gseed & 0xFFFF)
        else:
            e, acc = _score_split(net, task, "val", s_va)  # D113: the ONLY split feeding selection
        ev.append(e); va.append(acc)
        if report:
            s_te = (gseed + gen_off + 4 * a + 2) & 0x7FFFFFFF
            s_tr = (gseed + gen_off + 4 * a + 3) & 0x7FFFFFFF
            e2, a2 = _score_split(net, task, "test", s_te)
            e3, a3 = _score_split(net, task, "train", s_tr)
            te.append(e2); ta.append(a2); tr.append(e3); tra.append(a3)
            B = net.behave(task.E_test, noise_seed=s_te)
            alpha.append(covariance_powerlaw_exponent(B["state"]))

    _nan = float("nan")
    val_err = float(np.mean(ev))
    out = dict(
        trial_score=1.0 - val_err,                   # fitness basis; 0.0 == predicting the mean
        val_err=val_err, val_acc=float(np.mean(va)),
        test_err=float(np.mean(te)) if te else _nan,
        test_acc=float(np.mean(ta)) if ta else _nan,
        train_err=float(np.mean(tr)) if tr else _nan,
        train_acc=float(np.mean(tra)) if tra else _nan,
        cov_powerlaw_alpha=float(np.nanmean(alpha)) if alpha else _nan,
        n_params=int(np.count_nonzero(genome.mag)),
        exc_frac=genome.exc_fraction(),              # run_evolution's history reads this per genome
        dev_converged=dev_converged, dev_aborted=dev_aborted,
        n_assays=n_assays,
        # kept so `_fitness` and the existing history machinery keep working unchanged
        encoding=1.0 - val_err, carrying=0.0, regulation=1.0 - val_err,
    )
    out.update(loc)          # D127: loc_* present only when report=True; absent keys are the signal
    return out


def control_scores(genome: Genome, net_cfg: EvoNetConfig, cfg=None, seed: int = 0,
                   **task_kwargs) -> dict:
    """Run the two controls on a genome, using the SAME development it would normally receive.

    Both must fall to chance for a network that is genuinely holding and binding:
      omit_cue  -- the cue is absent from the input, so nothing can be held
      scramble  -- targets permuted against stimuli, so the binding is unlearnable
    Unlike the shuffle control on the old task, these remove what they claim to (D120).
    """
    from .trial_task import cue_delay_probe
    out = {}
    for label, kw in [("normal", {}), ("omit_cue", dict(omit_cue=True)),
                      ("scramble", dict(scramble=True))]:
        t = cue_delay_probe(seed=seed, **{**task_kwargs, **kw})
        r = trial_evaluate(genome, t, net_cfg, cfg, report=True)
        out[label] = dict(val_acc=r["val_acc"], test_acc=r["test_acc"],
                          val_err=r["val_err"], test_err=r["test_err"])
    return out
