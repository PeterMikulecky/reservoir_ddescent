"""block_genome.py - a STRUCTURED genome that can express clustered topology (D131 step 1).

WHY THIS EXISTS. D130 ablated all recurrent connectivity and found it contributes nothing: where the
task is solvable the ablated network matched or beat intact, and where passive decay fails the intact
network failed identically at every coupling. D092 had found the same on the covariance task by another
route -- random connectivity lacks the attractor topology persistent memory requires. The current genome
is DIRECT (per-synapse `mag` + per-neuron `signs`, D038), and clustered topologies are a vanishing
fraction of that space, so random draws never contain one and single-synapse mutation almost never builds
one. That is a VOCABULARY problem (HYPOTHESIS_LOG ENCODING E1), and this module fixes the vocabulary.

WHAT IT PRODUCES. A `Genome` -- the SAME dataclass `EvoNet` already consumes. Nothing downstream
changes. What changes is how `mag` is CONSTRUCTED: from block statistics rather than per-synapse draws.

THE ENCODING (D131).
    assign : (N,) int in [0, K)        -- which block each neuron belongs to      -> N genes
    B      : (K, K) float >= 0         -- expected magnitude, block j -> block i  -> K^2 genes
    signs  : (N,) +-1                  -- E/I identity, unchanged from D038       -> N genes
  P_gene = N + K^2 (+ N sign genes, as before). The knob is K: "how many kinds of neuron the genome
  can name." Strong diagonal / weak off-diagonal entries in B produce CLUSTERS.

TWO THINGS THAT ARE NOT OPTIONAL, both learned the hard way:

  1. WITHIN-BLOCK HETEROGENEITY (shared xi). Without it every synapse in a block-pair has identical
     strength, a neuron's inputs take at most K distinct values, and top-k selection is a mass of exact
     ties. So `W_ij = B[b_i, b_j] * xi_ij`, with xi drawn ONCE PER RUN and SHARED BY THE WHOLE
     POPULATION -- not per individual (the same genome would build different networks, adding a fitness
     variance term, and fitness unreliability has destroyed three results here: D115/D124/D129) and not
     seeded from the mutable genome (one mutation would rebuild connectivity from scratch, the
     catastrophic-mutation hazard Elbrecht & Schuman 2020 report for CPPN encodings). Shared xi is a
     fixed scaffold of POTENTIAL contacts; genes decide which are realised and how strongly.
     Falsification condition committed in D131: every headline result must replicate across >= 3
     independent xi draws or it does not stand.

  2. PER-NEURON TOP-K sparsification. Every pair gets some strength, so sparsity must be imposed.
     Each neuron keeps its k strongest INPUTS, k = round(density * (N-1)), giving P_syn = N*k EXACTLY.
     Chosen over global top-M because global competition lets one strong cluster consume the whole
     budget and leave neurons with NO inputs, and because fixing in-degree removes a confound this
     project has already been bitten by (D125: best-over-neurons rises with in-degree at fixed N, which
     is why loc_best behaved as a lottery).
     Cost, recorded: real cortex has heterogeneous in-degree and this legislates it away. Revisit by
     making k a per-neuron gene once the uniform version works.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .evonet import EvoNetConfig, Genome


@dataclass
class BlockGenes:
    """The evolvable genes. `to_genome()` renders them into the phenotype EvoNet consumes."""
    assign: np.ndarray        # (N,) int in [0, K)
    B: np.ndarray             # (K, K) >= 0, expected magnitude block j (pre) -> block i (post)
    signs: np.ndarray         # (N,) +1 / -1, per-neuron E/I identity (D038)

    @property
    def K(self) -> int:
        return int(self.B.shape[0])

    def p_gene(self) -> int:
        """P_gene = block assignments + block matrix. THE DOUBLE-DESCENT AXIS (D131).

        SIGNS ARE EXCLUDED, matching the precedent set by `Genome.n_params`, which counts nonzero
        magnitudes only and notes signs as N extra genes the magnitudes dominate. The count of sign
        genes is constant in K, so including them would add a fixed offset of N to every point on the
        axis without changing any shape -- and it would invalidate D131's pre-registered threshold
        arithmetic (P_gene = N + K^2, so P_crit ~ 240 constraints falls near K ~ 12). Use
        `p_gene_total()` where the all-genes count is wanted.

        Distinct from P_syn (the synapse count), which is held FIXED as a nuisance control. Under the
        old direct encoding these were the same number, which is why P was never ambiguous; they
        decouple here and must never be conflated in reporting.
        """
        return int(self.assign.size + self.B.size)

    def p_gene_total(self) -> int:
        """Every evolvable gene, including the N sign genes. Reported alongside, never as the axis."""
        return int(self.assign.size + self.B.size + self.signs.size)


def make_xi(N: int, seed: int) -> np.ndarray:
    """The shared scaffold: a fixed positive multiplier field, drawn ONCE PER RUN.

    Every individual in the population uses the SAME xi. See the module docstring for why. Lognormal
    rather than uniform so the strength distribution has a realistic right tail, which also makes the
    top-k ranking decisive rather than marginal.
    """
    rng = np.random.default_rng(seed)
    xi = rng.lognormal(mean=0.0, sigma=0.5, size=(N, N))
    np.fill_diagonal(xi, 0.0)                      # no autapses
    return xi


def to_genome(genes: BlockGenes, xi: np.ndarray, density: float,
              w0: float = 1.5, inh_gain: float | None = None) -> Genome:
    """Render genes -> phenotype: expected strengths, shared xi, then per-neuron top-k.

    `inh_gain` reproduces D058's balance correction exactly: with more excitatory than inhibitory
    neurons, uniform magnitudes let excitation swamp inhibition (~24:1 measured) and the
    fluctuation-driven regime is lost. Default g = ei_split/(1-ei_split) as in `random_genome`.
    """
    N = genes.assign.size
    if inh_gain is None:
        ei = float((genes.signs > 0).mean())
        inh_gain = ei / max(1.0 - ei, 1e-6)

    # expected magnitude from block statistics, then within-block heterogeneity from the shared field
    expected = genes.B[genes.assign[:, None], genes.assign[None, :]]      # (N, N), [post, pre]
    mag = expected * xi * w0
    mag = mag * np.where(genes.signs < 0, inh_gain, 1.0)[np.newaxis, :]   # column j = presynaptic
    np.fill_diagonal(mag, 0.0)

    # PER-NEURON TOP-K: each row (postsynaptic neuron) keeps its k strongest inputs -> P_syn = N*k
    k = int(round(density * (N - 1)))
    k = max(1, min(k, N - 1))
    keep = np.zeros_like(mag, dtype=bool)
    idx = np.argpartition(-mag, kth=k - 1, axis=1)[:, :k]
    np.put_along_axis(keep, idx, True, axis=1)
    return Genome(signs=genes.signs.copy(), mag=mag * keep)


def random_block_genes(cfg: EvoNetConfig, K: int, ei_split: float = 0.8,
                       seed: int | None = None) -> BlockGenes:
    """A random structured genome. NOT a seeded one -- this is the E2 falsification surface.

    Block assignments are uniform and the block matrix is drawn i.i.d. lognormal with NO imposed
    diagonal bias: nothing here favours within-block over between-block connection. A random draw is
    therefore an arbitrary block structure, not a clustered one, and D131 build step 3 REQUIRES that
    such genomes sit at chance on the task. A structured prior that already performs is a seeded genome
    under another name, whatever its author intended.
    """
    rng = np.random.default_rng(seed)
    assign = rng.integers(0, K, size=cfg.N)
    B = rng.lognormal(mean=0.0, sigma=0.5, size=(K, K))
    signs = np.where(rng.random(cfg.N) < ei_split, 1.0, -1.0)
    return BlockGenes(assign=assign, B=B, signs=signs)


def clustered_block_genes(cfg: EvoNetConfig, K: int, within: float = 4.0, between: float = 0.5,
                          ei_split: float = 0.8, seed: int | None = None) -> BlockGenes:
    """A HAND-SET clustered genome, for the D131 step-2 known-positive check ONLY.

    WARNING - QUARANTINE (D092, extended). This is the ceiling's topology expressed in the new vocabulary. It
    exists to verify the machinery can produce carry at all -- cue selects the matching cluster,
    persists, and DECAYS across the delay (the decay is the validated part of the measure; a flat carry
    is the random-net confound, not memory). It is NEVER a seed, template, initial population, or
    comparison for evolved networks. Any use of this function inside an evolutionary run is a bug.
    """
    rng = np.random.default_rng(seed)
    assign = np.tile(np.arange(K), int(np.ceil(cfg.N / K)))[:cfg.N]
    rng.shuffle(assign)
    B = np.full((K, K), between, dtype=float)
    np.fill_diagonal(B, within)
    signs = np.where(rng.random(cfg.N) < ei_split, 1.0, -1.0)
    return BlockGenes(assign=assign, B=B, signs=signs)


def mutate_blocks(genes: BlockGenes, b_sigma: float = 0.15, assign_p: float = 0.02,
                  sign_flip_p: float = 0.01, seed: int | None = None) -> BlockGenes:
    """Mutation on the STRUCTURED genes.

    Three channels, deliberately of different granularity:
      * B entries       -- multiplicative lognormal jitter. GRADED: shifts the whole strength
                           distribution for a block pair, so which synapses win the top-k competition
                           changes gradually. This is the channel replicator selection can climb.
      * block assignment -- categorical, so it is a DISCRETE jump: one neuron changes type and all its
                           synapses are re-specified. Rate kept low (2%) for that reason. D131 build
                           step 5 measures whether these jumps are catastrophic; if most single-gene
                           mutations are, selection has no gradient regardless of expressivity.
      * signs           -- as D038.
    """
    rng = np.random.default_rng(seed)
    B = genes.B * rng.lognormal(mean=0.0, sigma=b_sigma, size=genes.B.shape)
    assign = genes.assign.copy()
    flip = rng.random(assign.size) < assign_p
    assign[flip] = rng.integers(0, genes.K, size=int(flip.sum()))
    signs = genes.signs.copy()
    s_flip = rng.random(signs.size) < sign_flip_p
    signs[s_flip] *= -1.0
    return BlockGenes(assign=assign, B=np.clip(B, 0.0, None), signs=signs)
