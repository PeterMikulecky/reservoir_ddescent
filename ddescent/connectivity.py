"""
Connectivity generators for the LIF reservoir.

The whole point of the fixed-N dissociation experiment is that *neuron count* (N),
*connectivity density* (p), and *effective / participation-ratio dimensionality*
(PR) are three different things that Frank's verbal argument tends to conflate.
This module exposes the two structural knobs we can set a priori -- density and
gain (spectral radius) -- while PR is a measured, emergent property (see
measures.participation_ratio). Keeping the a-priori knobs and the measured axis
separate is what lets the analysis regress generalization on all three.

Design choices
--------------
* Weights are returned as a dense (N, N) float array W where W[i, j] is the weight
  of the synapse j -> i (post <- pre). Sparse structure is encoded as exact zeros.
* Spectral radius is controlled on the *linear* connectivity matrix. For a spiking
  network this is only a proxy for the true operating gain, so we treat it as a
  knob that *moves* dynamics, not as ground truth -- PR is measured empirically
  afterwards. This caveat is central to the interpretation (see design_doc.md).
* Dale's law (E/I sign structure) is optional and off by default, so the first
  pass isolates density/gain from biological sign constraints.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class ConnectivityConfig:
    N: int = 1000
    density: float = 0.1          # p: fraction of possible recurrent synapses present
    spectral_radius: float | None = 0.95  # target rho of linear W; None -> use raw gain
    gain: float = 1.0             # scale used when spectral_radius is None
    ei_split: float | None = None # e.g. 0.8 -> 80% excitatory (Dale's law). None -> unsigned
    seed: int | None = None

    def synapse_count(self) -> int:
        """Expected number of nonzero recurrent synapses (our 'parameter count' axis)."""
        return int(round(self.density * self.N * (self.N - 1)))


def make_recurrent_weights(cfg: ConnectivityConfig) -> np.ndarray:
    """Return a dense (N, N) recurrent weight matrix with zero diagonal."""
    rng = np.random.default_rng(cfg.seed)
    N = cfg.N

    # sparse mask (no self-connections)
    mask = rng.random((N, N)) < cfg.density
    np.fill_diagonal(mask, False)

    if cfg.ei_split is None:
        # unsigned Gaussian weights
        W = rng.standard_normal((N, N))
    else:
        # Dale's law: each *presynaptic* neuron is E (+) or I (-)
        n_exc = int(round(cfg.ei_split * N))
        signs = np.ones(N)
        signs[n_exc:] = -1.0
        rng.shuffle(signs)
        W = np.abs(rng.standard_normal((N, N))) * signs[np.newaxis, :]  # column = presyn

    W = W * mask

    W = _rescale_gain(W, cfg, rng)
    return W


def _rescale_gain(W: np.ndarray, cfg: ConnectivityConfig, rng) -> np.ndarray:
    if cfg.spectral_radius is not None:
        rho = _spectral_radius(W)
        if rho > 0:
            W = W * (cfg.spectral_radius / rho)
    else:
        # scale so weight variance ~ gain^2 / (p * N): the classic random-network scaling
        denom = np.sqrt(max(cfg.density * cfg.N, 1.0))
        W = W * (cfg.gain / denom)
    return W


def _spectral_radius(W: np.ndarray) -> float:
    # largest |eigenvalue|. N=1000 dense eig is a few hundred ms; fine for a sweep.
    try:
        ev = np.linalg.eigvals(W)
        return float(np.max(np.abs(ev)))
    except np.linalg.LinAlgError:
        # fall back to a cheap upper bound
        return float(np.max(np.sum(np.abs(W), axis=1)))


def make_input_weights(N: int, K: int, scale: float = 1.0,
                       density: float = 1.0, seed: int | None = None) -> np.ndarray:
    """Input projection W_in of shape (N, K): reservoir_current = W_in @ u."""
    rng = np.random.default_rng(seed)
    W_in = rng.standard_normal((N, K)) * scale
    if density < 1.0:
        W_in *= (rng.random((N, K)) < density)
    return W_in
