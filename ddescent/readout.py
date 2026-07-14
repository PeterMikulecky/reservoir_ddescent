"""
Readouts.

The readout is the *trained trait* in Frank's mapping: the reservoir is the fixed
regulatory architecture, and selection tunes the readout to the encountered
environments. Two regimes matter for the paper:

  * min-norm interpolation  -> the 'biological' regime Frank emphasizes: complexity
    is NOT penalized, so the full double-descent spike is experienced. Among the
    infinitely many interpolating solutions (a neutral manifold, cf. Gavrilets),
    least-norm least-squares selects the smoothest one (Wilson's implicit bias).
  * ridge regression        -> the 'classical statistics' regime that penalizes
    complexity and smooths the spike away. Used as the contrast in the
    regularization experiment.

All readouts expose fit / predict and report train/test/novel error via the
generalization metrics in measures.py.
"""
from __future__ import annotations
import numpy as np
from . import measures


def _augment(X: np.ndarray) -> np.ndarray:
    """Add a bias column."""
    return np.hstack([X, np.ones((X.shape[0], 1))])


class LinearReadout:
    """Ridge (alpha>0) or min-norm interpolation (alpha==0) linear readout."""

    def __init__(self, alpha: float = 0.0):
        self.alpha = alpha
        self.W = None

    def fit(self, X: np.ndarray, Y: np.ndarray):
        Xa = _augment(X)
        Y = np.asarray(Y)
        if Y.ndim == 1:
            Y = Y[:, None]
        n, d = Xa.shape
        if self.alpha > 0:
            # ridge; solve in whichever space is smaller
            if d <= n:
                A = Xa.T @ Xa + self.alpha * np.eye(d)
                self.W = np.linalg.solve(A, Xa.T @ Y)
            else:
                A = Xa @ Xa.T + self.alpha * np.eye(n)
                self.W = Xa.T @ np.linalg.solve(A, Y)
        else:
            # min-norm least squares / interpolation
            self.W = np.linalg.pinv(Xa) @ Y
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        out = _augment(X) @ self.W
        return out[:, 0] if out.shape[1] == 1 else out

    def weight_norm(self) -> float:
        return float(np.linalg.norm(self.W))


def one_hot(y: np.ndarray, n_classes: int) -> np.ndarray:
    Y = np.zeros((len(y), n_classes))
    Y[np.arange(len(y)), y.astype(int)] = 1.0
    return Y


def evaluate_regression(readout, task) -> dict:
    readout.fit(task.U_train_feat, task.y_train)
    tr = measures.nmse(task.y_train, readout.predict(task.U_train_feat))
    te = measures.nmse(task.y_test, readout.predict(task.U_test_feat))
    out = dict(train_err=tr, test_err=te,
               gen_gap=measures.generalization_gap(tr, te),
               weight_norm=readout.weight_norm())
    if task.U_novel_feat is not None:
        out["novel_err"] = measures.nmse(task.y_novel, readout.predict(task.U_novel_feat))
    return out


def evaluate_classification(readout, task, n_classes: int) -> dict:
    Ytr = one_hot(task.y_train, n_classes)
    readout.fit(task.U_train_feat, Ytr)
    def err(Xf, y):
        pred = np.argmax(readout.predict(Xf), axis=1)
        return measures.classification_error(y, pred)
    tr = err(task.U_train_feat, task.y_train)
    te = err(task.U_test_feat, task.y_test)
    out = dict(train_err=tr, test_err=te,
               gen_gap=measures.generalization_gap(tr, te),
               weight_norm=readout.weight_norm())
    if task.U_novel_feat is not None:
        # out-of-class: we can't score accuracy on unseen label; report decision
        # confidence / entropy as a proxy for spurious over-confident structure.
        pred = readout.predict(task.U_novel_feat)
        p = np.exp(pred - pred.max(axis=1, keepdims=True))
        p /= p.sum(axis=1, keepdims=True)
        out["novel_confidence"] = float(np.mean(np.max(p, axis=1)))
    return out


class OnlineRLS:
    """Recursive least squares readout for the temporal double-descent experiment.

    Provides epoch-wise error curves ('older circuits generalize better'). Hook for
    the temporal experiment; not exercised in the fixed-N sweep.
    """
    def __init__(self, n_features: int, n_outputs: int, delta: float = 1.0):
        self.P = np.eye(n_features + 1) / delta
        self.W = np.zeros((n_features + 1, n_outputs))

    def update(self, x: np.ndarray, y: np.ndarray):
        x = np.append(x, 1.0)[:, None]
        Px = self.P @ x
        k = Px / (1.0 + x.T @ Px)
        err = y[None, :] - x.T @ self.W
        self.W += k @ err
        self.P -= k @ (x.T @ self.P)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return _augment(X) @ self.W
