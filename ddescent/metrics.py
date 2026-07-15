"""
Metric battery for reservoir states.

Design principle (PJM, 2026-07-14): collecting is cheaper than re-running. But the
insurance is NOT a longer list of scalars -- it is storing the *object the scalars are
derived from*.

PR, effective rank, kernel rank, and effective degrees of freedom are all functionals of
the SAME eigenvalue spectrum of the state covariance. So we store the spectrum (top-k
singular values, ~200 floats) and derive everything from it, now or later. Any spectral
metric we haven't thought of yet is recoverable without re-running a single simulation.

Cost tiers (see DECISIONS.md D025):
  FREE      - derived from the state matrix X we already compute: everything in this module
  CHEAP     - one extra sim pass: generalization rank (noisy input variants)
  EXPENSIVE - separate protocol per individual: IPC, Lyapunov, robustness interval.
              Do NOT run these per-individual in a 5000-evaluation GA; run them on the
              final evolved population or a curated subset, where they are informative.
"""
from __future__ import annotations
import numpy as np


# ----------------------------------------------------------------- the master record
def spectrum(X: np.ndarray, k: int = 200, center: bool = True) -> np.ndarray:
    """Top-k singular values of the state matrix. THE record to store.

    Every spectral metric below is a functional of this. Storing it future-proofs
    metrics we have not thought of yet.
    """
    Xc = X - X.mean(axis=0, keepdims=True) if center else X
    s = np.linalg.svd(Xc, compute_uv=False)
    return s[:k].astype(np.float32)          # float32: half the storage, ample precision


# ------------------------------------------------- functionals of the spectrum (free)
def pr_from_spectrum(s: np.ndarray) -> float:
    """Participation ratio. Our confirmatory dimensionality measure (D002/D016)."""
    lam = np.asarray(s, dtype=float) ** 2
    denom = np.sum(lam ** 2)
    return float((np.sum(lam) ** 2) / denom) if denom > 0 else 0.0


def edof_from_spectrum(s: np.ndarray, kappa: float) -> float:
    """Normalized effective degrees of freedom, eta_kappa = sum(l^2/(l+kappa)^2).

    Per D018, the RMT-principled quantity governing interpolation-threshold location
    (the peak sits where this -> n). A DIFFERENT functional of the same spectrum than PR
    -- which is exactly why storing the spectrum (not just PR) matters.
    """
    lam = np.asarray(s, dtype=float) ** 2
    return float(np.sum((lam / (lam + kappa)) ** 2))


def effective_rank_from_spectrum(s: np.ndarray, thresh: float = 0.99) -> int:
    """PCs needed to reach `thresh` of variance."""
    var = np.asarray(s, dtype=float) ** 2
    if var.sum() <= 0:
        return 0
    return int(np.searchsorted(np.cumsum(var) / var.sum(), thresh) + 1)


def spectral_entropy(s: np.ndarray) -> float:
    """Shannon entropy of the normalized eigenspectrum; a dimensionality measure that
    weights the tail differently than PR. Free insurance against PR being the wrong
    functional."""
    lam = np.asarray(s, dtype=float) ** 2
    tot = lam.sum()
    if tot <= 0:
        return 0.0
    p = lam / tot
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))


def numerical_rank_from_spectrum(s: np.ndarray, shape, tol: float | None = None) -> int:
    """Kernel rank in the Legenstein & Maass (2007) sense, derived from the spectrum we
    already computed (avoids a second full SVD).

    NOTE (D022): rank is generically full at min(n, M) regardless of PR, so this saturates
    -- record it for the literature link, but do not expect it to discriminate genomes.
    """
    sv = np.asarray(s, dtype=float)
    if sv.size == 0 or sv[0] <= 0:
        return 0
    if tol is None:
        tol = max(shape) * np.finfo(float).eps * sv[0]
    return int((sv > tol).sum())


# ------------------------------------------------------ non-spectral state stats (free)
def activity_stats(X: np.ndarray, eps: float = 1e-6,
                   max_corr_neurons: int = 200) -> dict:
    """Rate, diversity, and synchrony descriptors.

    'Diversity of spike patterns' from the SRN metric list: a population firing uniformly
    and synchronously carries less information than a heterogeneous one. These are the
    cheap health/regime diagnostics that told us 'saturated vs silent' during T0.
    """
    rates = X.mean(axis=0)                       # per-neuron mean feature
    active = X > eps
    out = dict(
        rate_mean=float(X.mean()),
        rate_std=float(rates.std()),
        rate_cv=float(rates.std() / (rates.mean() + 1e-12)),   # diversity across neurons
        active_frac=float(active.mean()),
        silent_frac=float((rates <= eps).mean()),
        saturated_frac=float((active.mean(axis=0) > 0.99).mean()),
    )
    # synchrony: mean pairwise correlation. The full corr matrix is O(N^2); at N=1000 in a
    # 5000-evaluation GA that is a real cost, so estimate from a neuron subsample.
    Xc = X - X.mean(axis=0, keepdims=True)
    sd = Xc.std(axis=0)
    keep = np.flatnonzero(sd > eps)
    if keep.size >= 2:
        if keep.size > max_corr_neurons:
            keep = np.random.default_rng(0).choice(keep, max_corr_neurons, replace=False)
        C = np.corrcoef(Xc[:, keep], rowvar=False)
        iu = np.triu_indices_from(C, k=1)
        out["mean_pairwise_corr"] = float(np.nanmean(C[iu]))
    else:
        out["mean_pairwise_corr"] = np.nan
    return out


def sparse_spectral_radius(W: np.ndarray) -> float:
    """Largest |eigenvalue| via a sparse solver (O(N^2) per iteration, not O(N^3)).

    Recorded as a DESCRIPTOR for comparability with the literature (Recanatesi's density
    effect concentrates near rho -> 1). NOT a tuning target: D014 established that in this
    spiking LIF model the whole rho in [0.5, 2.0] range is a dead zone where recurrence has
    no measurable effect on PR. The rho~1 edge-of-chaos heuristic is a rate-network result.
    """
    try:
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import eigs
        vals = eigs(csr_matrix(W), k=1, which="LM", return_eigenvectors=False,
                    maxiter=5000, tol=1e-6)
        return float(np.abs(vals[0]))
    except Exception:
        # power iteration fallback
        rng = np.random.default_rng(0)
        v = rng.standard_normal(W.shape[0])
        v /= np.linalg.norm(v) + 1e-12
        lam = 0.0
        for _ in range(200):
            u = W @ v
            n = np.linalg.norm(u)
            if n < 1e-12:
                return 0.0
            v = u / n
            lam = n
        return float(lam)


# ------------------------------------------------------------------- the battery
def full_battery(X: np.ndarray, W: np.ndarray | None = None,
                 k: int = 200, kappas=(1e-3, 1e-2, 1e-1)) -> dict:
    """Everything free, plus the stored spectrum. Call once per individual.

    Returns a flat dict of scalars plus 'spectrum' (float32 array) for storage.
    Derived scalars are conveniences -- the spectrum is the durable record.
    """
    s = spectrum(X, k=k)
    out = dict(
        pr=pr_from_spectrum(s),
        effective_rank=effective_rank_from_spectrum(s),
        spectral_entropy=spectral_entropy(s),
        numerical_rank=numerical_rank_from_spectrum(s, X.shape),
        spectrum_total_var=float(np.sum(np.asarray(s, dtype=float) ** 2)),
    )
    for kap in kappas:
        out[f"edof_k{kap:g}"] = edof_from_spectrum(s, kap)
    out.update(activity_stats(X))
    if W is not None:
        out["spectral_radius"] = sparse_spectral_radius(W)
        out["synapse_count"] = int((W != 0).sum())
    out["spectrum"] = s          # <-- store this; everything above is recomputable from it
    return out
