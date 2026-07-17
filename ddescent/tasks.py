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
    U_novel: np.ndarray | None = None   # primary novel set
    y_novel: np.ndarray | None = None
    meta: dict | None = None
    novel_sets: list | None = None      # [(delta, U, y)] -- graded novelty (D029)


def _random_orthonormal(K: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((K, K))
    Q, _ = np.linalg.qr(A)
    return Q


def anisotropic_regression(K: int = 20, n_train: int = 300, n_test: int = 300,
                           n_high: int = 4, hi_var: float = 1.0, lo_var: float = 0.02,
                           noise: float = 0.1, novel_shift: float = 1.5,
                           novel_mode: str = "shift",
                           novel_levels=(0.5, 1.0, 1.5, 2.5, 4.0),
                           seed: int = 0) -> TaskData:
    """Smooth nonlinear regression over an anisotropically-distributed environment.

    The environment covariance has `n_high` high-variance directions and the rest
    low-variance. Training and in-distribution test samples come from this distribution.

    NOVEL ENVIRONMENTS (D029 -- this is the part that was broken).

    `novel_mode="shift"` (DEFAULT, novel-but-related):
        Novel = same covariance, mean DISPLACED along a HIGH-variance (well-sampled) axis.
        The system has seen that axis vary; it has not seen inputs at that offset. This is
        Frank's "essence of snakeness": new instances of a LEARNED class, displaced but
        structurally related. Generalization here is a real question, not a foregone failure.

    `novel_mode="orthogonal"` (the ORIGINAL, kept only for comparison):
        Novel = variance SWAPPED into the low-variance directions. Retained because it
        instantiates the Schaeffer (2023) geometry argument Frank invokes -- but as an
        outcome measure it is broken: it makes the weakly-sampled directions DOMINATE, and
        since the target depends on them through `w` while training barely moves them, the
        readout has no way to have learned their contribution. Every novel NMSE in the
        N=1000 run exceeded 1 (nothing beat predicting the mean). That is orthogonal
        EXTRAPOLATION, not generalization.

    GRADED NOVELTY. `novel_levels` gives shift magnitudes (in units of the high-variance
    std). `TaskData.novel_sets` holds (delta, U, y) per level, so generalization can be
    measured as a CURVE against distance from the training distribution rather than a single
    number. H1's sharper form: does higher dimensionality FLATTEN that curve?
    `U_novel`/`y_novel` remain the single primary set (at `novel_shift`) for API stability.
    """
    rng = np.random.default_rng(seed)
    Q = _random_orthonormal(K, seed + 1)          # environmental axes
    var = np.full(K, lo_var); var[:n_high] = hi_var
    std = np.sqrt(var)

    def sample_z(n):
        return rng.standard_normal((n, K)) * std

    def sample_orthogonal(n):
        z = rng.standard_normal((n, K)) * np.sqrt(lo_var)
        z[:, n_high:] += rng.standard_normal((n, K - n_high)) * np.sqrt(hi_var)
        return z

    def shifted(n, delta):
        """Same covariance; mean displaced by delta*sqrt(hi_var) along a SAMPLED axis."""
        z = sample_z(n)
        z[:, 0] += delta * np.sqrt(hi_var)        # axis 0 is a high-variance direction
        return z

    U_train = sample_z(n_train) @ Q.T
    U_test = sample_z(n_test) @ Q.T

    # smooth nonlinear target: weighted sum of tanh features on the environmental axes
    w = rng.standard_normal(K)
    def target(U):
        proj = U @ Q
        return np.tanh(proj @ w) + 0.3 * np.tanh(proj[:, 0] * proj[:, min(1, K - 1)])

    if novel_mode == "orthogonal":
        U_novel = sample_orthogonal(n_test) @ Q.T
        novel_sets = [(np.nan, U_novel, target(U_novel))]
    elif novel_mode == "shift":
        U_novel = shifted(n_test, novel_shift) @ Q.T
        novel_sets = [(float(d), shifted(n_test, d) @ Q.T, None) for d in novel_levels]
        novel_sets = [(d, U, target(U)) for (d, U, _) in novel_sets]
    else:
        raise ValueError(f"unknown novel_mode {novel_mode!r}")

    y_train = target(U_train) + noise * rng.standard_normal(n_train)
    y_test = target(U_test)
    y_novel = target(U_novel)
    return TaskData(U_train, y_train, U_test, y_test, U_novel, y_novel,
                    meta=dict(kind="anisotropic_regression", K=K, n_high=n_high,
                              novel_mode=novel_mode, novel_shift=novel_shift),
                    novel_sets=novel_sets)


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


# ---------------------------------------------------------------------------
# Profile environments for the evolvable network (D036).
#
# Task triage: the anisotropic ENVIRONMENT STRUCTURE survives -- some directions of
# environmental variation well-sampled, others barely (Schaeffer 2023, which Frank
# explicitly invokes; substrate-independent). The SCALAR TANH TARGET dies: it existed only
# because a linear readout emits a number. A reservoir artifact.
#
# Environments now demand a RESPONSE PROFILE, because that is what a phenotype is.
# Frank: "Phenotypic responses are the outputs. The fitness landscape mirrors the
# training-error surface, ranking parameters by their performance in encountered
# environments."
#
# Two payoffs:
#   * novel-but-related (D029) becomes natural: a NEW TARGET PROFILE from the same class,
#     i.e. Frank's snakeness -- not a geometric hack about displacing along sampled axes.
#   * constraints = n_env * d, not n_env -> a second independent knob on where |W| crosses
#     the interpolation threshold, which the P-vs-D design needs.
# ---------------------------------------------------------------------------

@dataclass
class ProfileTask:
    E_train: np.ndarray      # (n_train, K) environments
    Y_train: np.ndarray      # (n_train, d) demanded response profiles
    E_test: np.ndarray
    Y_test: np.ndarray
    E_novel: np.ndarray | None = None
    Y_novel: np.ndarray | None = None
    meta: dict | None = None

    def n_constraints(self) -> int:
        """n_env * d -- what |W| must be compared against for the interpolation threshold."""
        return int(self.Y_train.shape[0] * self.Y_train.shape[1])


def profile_environments(K: int = 10, d: int = 10, n_train: int = 50, n_test: int = 50,
                         n_high: int = 3, hi_var: float = 1.0, lo_var: float = 0.02,
                         novel_shift: float = 1.5, noise: float = 0.05,
                         seed: int = 0) -> ProfileTask:
    """Anisotropic environments demanding structured response profiles.

    The environment->profile map is the CLASS ("snakeness"): a fixed smooth nonlinear
    function shared by every environment. Generalization = producing the right profile for
    environments never encountered. `novel` = environments displaced along a WELL-SAMPLED
    axis (novel-but-related), never along unsampled ones (that was D029's broken design).
    """
    rng = np.random.default_rng(seed)
    Q = _random_orthonormal(K, seed + 1)
    var = np.full(K, lo_var); var[:n_high] = hi_var
    std = np.sqrt(var)

    def draw(n, shift=0.0):
        z = rng.standard_normal((n, K)) * std
        z[:, 0] += shift * np.sqrt(hi_var)      # displace along a SAMPLED axis
        return z @ Q.T

    # the class: environment -> d-dimensional response profile
    Wc = rng.standard_normal((K, d))
    def profile(E):
        return np.tanh(E @ Q @ Wc)

    E_tr, E_te, E_nv = draw(n_train), draw(n_test), draw(n_test, shift=novel_shift)
    Y_tr = profile(E_tr) + noise * rng.standard_normal((n_train, d))
    return ProfileTask(E_tr, Y_tr, E_te, profile(E_te), E_nv, profile(E_nv),
                       meta=dict(kind="profile_environments", K=K, d=d, n_high=n_high,
                                 novel_shift=novel_shift))


# ===========================================================================
# HIERARCHICAL ENVIRONMENTS (B2/B3/B3a — D045, D048, D051)
#
# Fixes three ways our earlier task GUARANTEED a null result:
#   B2  full-rank level-1 map  -> a waist is mathematically impossible
#                                 (rank(AB) <= min(rank A, rank B); D043)
#   B3  flat environment       -> nothing to "level up" to, so extra parameters can never
#                                 help; we would reproduce R&N by construction (D045)
#   B3a context signalled or carried by the MEAN -> detecting it is a SWITCH, not regulation
#
# THE DESIGN PRINCIPLE (D048, the sharpest constraint we have):
#   **Context changes stimulus STATISTICS, never the mean.** All contexts share mean zero;
#   they differ in COVARIANCE. Therefore:
#       mean over a short window   -> the instantaneous stimulus  -> LEVEL 1
#       variance/covariance over a long window -> the distribution -> CONTEXT -> LEVEL 2
#   The mean CANNOT carry context — context is not in any single stimulus, it is in their
#   spread. So the fluctuation channel is literally where the second-level regularity lives,
#   and reading it REQUIRES integrating over history (D047 Level 2(iii)).
#
#   A memoryless encoder can do no better than the context-averaged map. To beat it a system
#   must infer context from recent statistics and MODULATE the level-1 map — which is gain,
#   not drive. Regulation is forced, not invited.
#
# THE SWEPT AXIS (D051): not "noise level" but the **fraction of unexplained variance that is
# LEARNABLE** — signal-to-*structured*-noise.
#   learnable_frac = 1 -> all unexplained variance is context  -> PC route only
#   learnable_frac = 0 -> all of it is true noise              -> noise-hiding route only
#   0 < f < 1          -> BOTH routes available -> which does selection take?  <- THE EXPERIMENT
# ===========================================================================

@dataclass
class HierarchicalTask:
    E_train: np.ndarray        # (n_train, K) stimuli
    Y_train: np.ndarray        # (n_train, d) demanded response profiles
    C_train: np.ndarray        # (n_train,) latent context index — NEVER given to the network
    E_test: np.ndarray
    Y_test: np.ndarray
    C_test: np.ndarray
    meta: dict | None = None

    def n_constraints(self) -> int:
        """n_env * d — what |W| is compared against for the interpolation threshold."""
        return int(self.Y_train.shape[0] * self.Y_train.shape[1])

    def headroom(self, alphas=(1e-2, 1e-1, 1e0, 1e1, 1e2)) -> dict:
        """The two bounds that make 'levelling up' operational.

        * **memoryless floor** — best NMSE achievable WITHOUT context. Estimated empirically by
          fitting the best memoryless map on (E -> Y). *(Not analytic: the context-averaged map
          is NOT tanh(E @ mean(W)) — Jensen. tanh(mean) != mean(tanh).)*
        * **oracle ceiling** — best NMSE achievable WITH context, fitted as a SEPARATE map per
          context. **Context must select the MAP, not be added as an input**: a one-hot context
          fed additively can only SHIFT the output, never change the E->Y mapping. That is the
          offset-vs-gain distinction (D040) — and it is exactly why regulation, not drive, is
          required.

        **headroom = floor - ceiling.** If ~0 the task has NO room for regulation to pay and the
        design is dead. This is a REQUIRED check before any run.
        """
        from .baseline import best_nmse
        floor = best_nmse(self.E_train, self.Y_train, self.E_test, self.Y_test,
                          alphas=alphas, standardize=False)[0]
        # oracle: a separate map per context (context SELECTS the map)
        errs, wts = [], []
        for c in np.unique(self.C_train):
            mtr, mte = self.C_train == c, self.C_test == c
            if mtr.sum() < 5 or mte.sum() < 2:
                continue
            e = best_nmse(self.E_train[mtr], self.Y_train[mtr],
                          self.E_test[mte], self.Y_test[mte],
                          alphas=alphas, standardize=False)[0]
            errs.append(e * mte.sum()); wts.append(mte.sum())
        ceiling = float(np.sum(errs) / max(np.sum(wts), 1))
        return dict(memoryless_floor=float(floor), oracle_ceiling=ceiling,
                    headroom=float(floor - ceiling))


def hierarchical_environments(K: int = 10, d: int = 10, r1: int = 3,
                              n_contexts: int = 4, n_train: int = 50, n_test: int = 50,
                              context_dwell: int = 10, learnable_frac: float = 1.0,
                              unexplained_scale: float = 0.5, seed: int = 0) -> HierarchicalTask:
    """Two-level environment: context (slow, in the STATISTICS) selects a rank-r1 map (fast).

    Parameters
    ----------
    r1 : rank of every level-1 map. **Must be << min(K,d)** or a waist is impossible (B2).
         **H-B predicts the interpolation peak is set by r1, NOT by n.**
    context_dwell : stimuli per context. The SLOW timescale. Context must be inferred by
         integrating over ~this many stimuli — it is never signalled (B3a).
    learnable_frac : fraction of unexplained variance that is context-driven (learnable)
         rather than true noise (D051). **The experiment's main axis.**
    unexplained_scale : total magnitude of unexplained variance, split by learnable_frac.

    Notes
    -----
    * **Every context has mean-zero stimuli.** Contexts differ ONLY in covariance. Verified by
      `meta['mean_separation']`, which should be ~0.
    * Context indices are returned for ANALYSIS ONLY (e.g. "can context be decoded from the
      internal state?"). They are never inputs.
    """
    rng = np.random.default_rng(seed)
    Q = _random_orthonormal(K, seed + 1)

    # --- per-context stimulus COVARIANCE (mean stays zero everywhere) -------------------
    # each context emphasises a different subset of environmental axes
    covs = []
    for c in range(n_contexts):
        var = np.full(K, 0.15)
        hot = rng.choice(K, size=max(2, K // 3), replace=False)
        var[hot] = 1.0
        covs.append(Q @ np.diag(var) @ Q.T)

    # --- per-context level-1 map, each of RANK r1 (B2) ----------------------------------
    W_ctx = np.empty((n_contexts, K, d))
    for c in range(n_contexts):
        A = rng.standard_normal((K, r1))
        B = rng.standard_normal((r1, d))
        W_ctx[c] = A @ B                                   # rank <= r1 by construction

    def draw(n):
        n_blocks = int(np.ceil(n / context_dwell))
        ctx = np.repeat(rng.integers(0, n_contexts, n_blocks), context_dwell)[:n]
        E = np.empty((n, K))
        for c in range(n_contexts):
            m = ctx == c
            if m.any():
                E[m] = rng.multivariate_normal(np.zeros(K), covs[c], size=int(m.sum()))
        return E, ctx

    def respond(E, ctx):
        Y = np.empty((E.shape[0], d))
        for c in range(n_contexts):
            m = ctx == c
            if m.any():
                Y[m] = np.tanh(E[m] @ W_ctx[c])
        return Y

    E_tr, C_tr = draw(n_train)
    E_te, C_te = draw(n_test)
    Y_tr, Y_te = respond(E_tr, C_tr), respond(E_te, C_te)

    # --- unexplained variance: split into LEARNABLE (context) vs TRUE NOISE (D051) -------
    # the context-driven part is already in Y (it is why the same E maps differently).
    # learnable_frac scales how much TRUE noise we add alongside it.
    noise_sd = unexplained_scale * np.sqrt(max(0.0, 1.0 - learnable_frac))
    if noise_sd > 0:
        Y_tr = Y_tr + noise_sd * rng.standard_normal(Y_tr.shape)
        # test targets stay CLEAN: we score against the generating process, not the noise
    # if learnable_frac < 1 we also dilute the context signal itself
    if learnable_frac < 1.0:
        Wbar = W_ctx.mean(axis=0)
        blend = learnable_frac
        for arr, E_, C_ in ((None, E_tr, C_tr),):
            pass
        Y_tr = blend * Y_tr + (1 - blend) * np.tanh(E_tr @ Wbar)
        Y_te = blend * Y_te + (1 - blend) * np.tanh(E_te @ Wbar)

    mean_sep = float(np.max([np.abs(rng.multivariate_normal(np.zeros(K), covs[c], 2000).mean(0)).max()
                             for c in range(n_contexts)]))
    meta = dict(kind="hierarchical_environments", K=K, d=d, r1=r1, n_contexts=n_contexts,
                context_dwell=context_dwell, learnable_frac=learnable_frac,
                W_ctx=W_ctx, mean_separation=mean_sep)
    return HierarchicalTask(E_tr, Y_tr, C_tr, E_te, Y_te, C_te, meta=meta)
