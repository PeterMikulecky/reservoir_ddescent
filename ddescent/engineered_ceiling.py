"""Engineered ceiling (D092): hand-wired Wang/Compte/Brunel winner-take-all attractor as a W genome,
run through the EXISTING EvoNet. The known-positive control (D088) that carries context through a
silent delay -- validates carry/regulation measures against known-strong signal.

VERIFIED (sandbox 2026-07-19): A-cue lights cluster A not B (4.34 vs 0.03), B-cue lights B not A;
selectivity persists through silence and DECAYS gracefully (4.32->3.07->1.57 over 100/300/600 ms) --
the memory signature, distinct from the random-net flat confound (which stayed ~3.3-3.5, non-decaying).

QUARANTINE (D083/D092): this is a GENOME we TEST as a measurement-instrument calibration. NEVER seeded
into evolution, never a template/comparison/seed for evolved networks. Its ONLY roles: known-positive
for validating measures, and (later) a convergence-time bracket.

Layout of N=50:
  [0:10]   input   (first 5 -> cluster A, last 5 -> cluster B : SELECTIVE drive)
  [10:25]  cluster A (15 exc) -- strong within-cluster recurrence via SLOW current (attractor)
  [25:40]  cluster B (15 exc) -- strong within-cluster recurrence
  [40:47]  inhibitory pool (7 inh) -- driven by both clusters, inhibits both (winner-take-all)
  [47:50]  output (3 exc)
Run at nmda_frac ~0.7 (slow reverberation sustains the attractor -- Wang/Brunel mechanism = our D074).
"""
import numpy as np
from ddescent.evonet import Genome

N = 50
A_IDX = np.arange(10, 25); B_IDX = np.arange(25, 40)
INH_IDX = np.arange(40, 47); IN_IDX = np.arange(0, 10); OUT_IDX = np.arange(47, 50)


def build_engineered_ceiling(w_rec=4.0, w_inh=6.0, w_drive=3.0, w_ai=2.0, w_out=1.5):
    """Return a hand-wired Genome instantiating the 2-cluster winner-take-all context-memory attractor.
    Tunables are the Wang-circuit knobs; defaults are the verified working point at nmda_frac~0.7."""
    signs = np.ones(N); signs[INH_IDX] = -1.0
    mag = np.zeros((N, N))                      # mag[i,j] = magnitude of synapse j->i
    # within-cluster recurrent excitation (the attractor)
    for grp in (A_IDX, B_IDX):
        for i in grp:
            for j in grp:
                if i != j:
                    mag[i, j] = w_rec / len(grp)
    # SELECTIVE input drive: input[:5] -> cluster A, input[5:] -> cluster B (symmetry-breaking)
    for j in IN_IDX[:5]:
        for i in A_IDX: mag[i, j] = w_drive / 5
    for j in IN_IDX[5:]:
        for i in B_IDX: mag[i, j] = w_drive / 5
    # clusters -> inhibitory pool -> both clusters (winner-take-all competition)
    for j in np.concatenate([A_IDX, B_IDX]):
        for i in INH_IDX: mag[i, j] = w_ai / 30
    for j in INH_IDX:
        for i in np.concatenate([A_IDX, B_IDX]): mag[i, j] = w_inh / len(INH_IDX)
    # clusters -> output
    for j in np.concatenate([A_IDX, B_IDX]):
        for i in OUT_IDX: mag[i, j] = w_out / 30
    return Genome(signs=signs, mag=mag)
