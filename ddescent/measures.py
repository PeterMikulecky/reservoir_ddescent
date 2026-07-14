"""
Measurements that turn Frank's verbal claims into numbers.

The master axis is the *participation ratio* (PR) of the reservoir state covariance:
the effective dimensionality of the representation. Frank's thesis is that PR (not
neuron count, not connectivity density) is what drives generalization. This module
computes PR and the generalization metrics the experiments compare against it.
"""
from __future__ import annotations
import numpy as np


def participation_ratio(X: np.ndarray, center: bool = True) -> float:
    """Effective dimensionality of state matrix X (n_samples x N).

    PR = (sum lambda_i)^2 / sum(lambda_i^2), where lambda_i are eigenvalues of the
    feature covariance. Ranges from 1 (all variance in one direction) to
    min(n_samples, N) (isotropic). This is the empirical, emergent 'dimensionality
    of the regulatory space' in Frank's language.
    """
    Xc = X - X.mean(axis=0, keepdims=True) if center else X
    # eigenvalues of covariance == singular values^2 / (n-1); use SVD for stability
    s = np.linalg.svd(Xc, compute_uv=False)
    lam = s ** 2
    denom = np.sum(lam ** 2)
    if denom <= 0:
        return 0.0
    return float((np.sum(lam) ** 2) / denom)


def effective_rank(X: np.ndarray, thresh: float = 0.99) -> int:
    """Number of principal components needed to reach `thresh` of variance."""
    Xc = X - X.mean(axis=0, keepdims=True)
    s = np.linalg.svd(Xc, compute_uv=False)
    var = s ** 2
    if var.sum() == 0:
        return 0
    c = np.cumsum(var) / var.sum()
    return int(np.searchsorted(c, thresh) + 1)


def intrinsic_dim_of_inputs(U: np.ndarray) -> float:
    """PR of the *input* distribution -- the dimensionality of the environment.

    H3 predicts generalization saturates once reservoir PR exceeds this value.
    """
    return participation_ratio(U)


# ----------------------------------------------------------- generalization
def nmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Normalized mean squared error (1.0 == predicting the mean)."""
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    num = np.mean((y_true - y_pred) ** 2)
    den = np.var(y_true) + 1e-12
    return float(num / den)


def classification_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.asarray(y_true) != np.asarray(y_pred)))


def generalization_gap(train_err: float, test_err: float) -> float:
    """Frank's central quantity: how far test performance falls below training."""
    return float(test_err - train_err)
