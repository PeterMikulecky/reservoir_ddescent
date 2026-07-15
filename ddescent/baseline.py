"""
Baselines: does the reservoir actually help?

THE CHECK THIS PROJECT SKIPPED FOR ITS ENTIRE LIFE (D030).

A reservoir earns its place only if a readout on its state beats a readout on the RAW
INPUT. That is the most basic sanity check in reservoir computing, and we never ran it.
When we finally did (2026-07-16): at T0's chosen operating point (bias 0.4, gain 0.1) the
reservoir scored test NMSE 0.880 against a raw-input baseline of 0.216 -- **four times
WORSE than having no reservoir at all**. It only beat baseline at input_gain=10, which is
100x the gain T0 selected.

Root cause: T0 scored operating points on PR responsiveness alone and never asked whether
the state encodes the input. Those objectives are in OPPOSITION -- low input gain lets
recurrent dynamics dominate, which makes PR beautifully responsive to connectivity AND
makes the state nearly independent of the input. We optimized into a network that ignores
what we feed it.

Hence: `skill` is a GATE, not a metric. An operating point that fails it is disqualified
regardless of how good its dimensionality looks.
"""
from __future__ import annotations
import numpy as np

from .measures import nmse
from . import readout as ro

# ridge grid searched when scoring; we report the BEST achievable test error so the
# comparison is about representational quality, not about tuning luck.
ALPHA_GRID = (1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3, 1e4)


def _standardize(Xtr, others, floor_rel: float = 1e-3):
    """Z-score by training stats, with an sd FLOOR (near-silent units otherwise blow up)."""
    mu = Xtr.mean(0, keepdims=True)
    sd = Xtr.std(0, keepdims=True)
    sd = np.maximum(sd, floor_rel * (sd.mean() + 1e-12))
    return (Xtr - mu) / sd, [(X - mu) / sd for X in others]


def best_nmse(Xtr, ytr, Xte, yte, alphas=ALPHA_GRID, standardize: bool = True) -> tuple:
    """Best test NMSE over a ridge grid. Returns (nmse, alpha, train_nmse_at_that_alpha)."""
    if standardize:
        A, (B,) = _standardize(Xtr, [Xte])
    else:
        A, B = Xtr, Xte
    best = (np.inf, None, np.nan)
    for a in alphas:
        try:
            r = ro.LinearReadout(alpha=a).fit(A, ytr)
            e = nmse(yte, r.predict(B))
            if e < best[0]:
                best = (float(e), float(a), float(nmse(ytr, r.predict(A))))
        except Exception:
            continue
    return best


def raw_input_baseline(task, alphas=ALPHA_GRID) -> float:
    """Best test NMSE from a linear readout on the RAW INPUT. The bar to beat."""
    return best_nmse(task.U_train, task.y_train, task.U_test, task.y_test,
                     alphas=alphas, standardize=False)[0]


def skill(reservoir_nmse: float, baseline_nmse: float) -> float:
    """baseline / reservoir. >1 means the reservoir HELPS; <1 means it HURTS.

    Reported as a ratio so it is scale-free and directly interpretable:
    skill=2 -> half the error of no reservoir; skill=0.25 -> four times worse.
    """
    return float(baseline_nmse / max(reservoir_nmse, 1e-12))


def evaluate_features(S_tr: dict, S_te: dict, task, features=("X_mean", "X_inst", "X_var"),
                      alphas=ALPHA_GRID) -> dict:
    """Score every readout channel against the raw-input baseline.

    S_tr / S_te are `LIFReservoir.run_stationary` outputs. Returns a flat dict with, per
    feature: best test NMSE, the alpha achieving it, train NMSE there, and skill.
    Plus 'baseline_nmse' and 'best_skill' across features.
    """
    base = raw_input_baseline(task, alphas=alphas)
    out = {"baseline_nmse": base}
    for f in features:
        e, a, tr = best_nmse(S_tr[f], task.y_train, S_te[f], task.y_test, alphas=alphas)
        tag = f[2:]
        out[f"test_{tag}"] = e
        out[f"alpha_{tag}"] = a
        out[f"train_{tag}"] = tr
        out[f"skill_{tag}"] = skill(e, base)
    out["best_skill"] = max(out[f"skill_{f[2:]}"] for f in features)
    out["beats_baseline"] = bool(out["best_skill"] > 1.0)
    return out
