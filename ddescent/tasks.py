"""
Environments (tasks) for the reservoir.

Frank's framing: inputs are environmental/internal signals, the target is the
adaptive phenotypic response, and *novel environments* are the test set. A task
here is: a set of input vectors U, a target y, and one or more test sets that
probe generalization -- including 'novel-direction' test sets that instantiate
the Schaeffer variance-geometry argument (train samples some directions of
environmental variation; test along weakly-sampled directions).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class TaskData:
    U_train: np.ndarray
    y_train: np.ndarray
    U_test: np.ndarray          # in-distribution ("novel within-class") test
    y_test: np.ndarray
    U_novel: np.ndarray | None = None   # novel-direction / out-of-class test
    y_novel: np.ndarray | None = None
    meta: dict | None = None


def _random_orthonormal(K: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((K, K))
    Q, _ = np.linalg.qr(A)
    return Q


def anisotropic_regression(K: int = 20, n_train: int = 300, n_test: int = 300,
                           n_high: int = 4, hi_var: float = 1.0, lo_var: float = 0.02,
                           noise: float = 0.1, seed: int = 0) -> TaskData:
    """Smooth nonlinear regression over an anisotropically-distributed environment.

    The environment covariance has `n_high` high-variance directions and the rest
    low-variance. Training and in-distribution test samples come from this
    distribution. The *novel* set is generated along the LOW-variance directions
    (weakly sampled during 'evolution'), directly instantiating the Schaeffer
    (2023) geometry argument that Frank invokes.

    Target is a smooth nonlinear function of the input so that generalization
    (capturing structure) is distinct from memorization.
    """
    rng = np.random.default_rng(seed)
    Q = _random_orthonormal(K, seed + 1)          # environmental axes
    var = np.full(K, lo_var); var[:n_high] = hi_var
    std = np.sqrt(var)

    def sample(n, along_low=False):
        z = rng.standard_normal((n, K)) * std
        if along_low:
            # concentrate variance in low-var directions instead
            z = rng.standard_normal((n, K)) * np.sqrt(lo_var)
            z[:, n_high:] += rng.standard_normal((n, K - n_high)) * np.sqrt(hi_var)
        return z @ Q.T

    U_train = sample(n_train)
    U_test = sample(n_test)
    U_novel = sample(n_test, along_low=True)

    # smooth nonlinear target: weighted sum of tanh features on the high-var axes
    w = rng.standard_normal(K)
    def target(U):
        proj = U @ Q                              # back to environmental coords
        return np.tanh(proj @ w) + 0.3 * np.tanh(proj[:, 0] * proj[:, min(1, K-1)])

    y_train = target(U_train) + noise * rng.standard_normal(n_train)
    y_test = target(U_test)
    y_novel = target(U_novel)
    return TaskData(U_train, y_train, U_test, y_test, U_novel, y_novel,
                    meta=dict(kind="anisotropic_regression", K=K, n_high=n_high))


def snakeness_classification(K: int = 20, n_classes: int = 4, per_class_train: int = 60,
                             per_class_test: int = 60, class_spread: float = 0.6,
                             noise: float = 0.2, seed: int = 0) -> TaskData:
    """'Snakeness' task: recognize the essence of a class, not exact exemplars.

    Each class is a prototype (a region of environment space). Training exemplars
    are noisy draws around prototypes. The in-distribution test set holds out NOVEL
    within-class exemplars (does the system recognize snakeness?). The novel set is
    OUT-OF-CLASS inputs from a held-out prototype region (does it wrongly assert
    structure it never saw?). This operationalizes Frank's opening rattlesnake vs.
    snakeness distinction.
    """
    rng = np.random.default_rng(seed)
    prototypes = rng.standard_normal((n_classes + 1, K))  # last one is out-of-class
    prototypes /= np.linalg.norm(prototypes, axis=1, keepdims=True)

    def draw(protos, per_class, labels):
        Us, ys = [], []
        for c in labels:
            base = protos[c]
            X = base + class_spread * rng.standard_normal((per_class, K))
            X += noise * rng.standard_normal((per_class, K))
            Us.append(X); ys.append(np.full(per_class, c))
        return np.vstack(Us), np.concatenate(ys)

    in_labels = list(range(n_classes))
    U_train, y_train = draw(prototypes, per_class_train, in_labels)
    U_test, y_test = draw(prototypes, per_class_test, in_labels)          # novel within-class
    U_novel, y_novel = draw(prototypes, per_class_test, [n_classes])       # out-of-class
    return TaskData(U_train, y_train, U_test, y_test, U_novel, y_novel,
                    meta=dict(kind="snakeness", n_classes=n_classes))
