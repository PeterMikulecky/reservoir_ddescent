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


# ============================================================================================
# INTEGRATED carry-AND-regulate ceiling (D093/D094): carries context through the delay AND uses
# held context to select the probe->output MAP via disinhibitory gating (b-via-a). This is the
# known-positive for the carrying*regulation fitness term (D094) -- both factors must be real,
# so context must be HELD (not supplied), which this version does.
#
# VERIFIED (sandbox 2026-07-19): held-A opens pathway A, silences B (1.59/0.08 at 600ms delay);
# held-B opens B, silences A -- clean mutual exclusion PERSISTING THROUGH the silent delay.
# Identical probe -> different output by held context (out-diff 0.4-1.5 across delays). The D093
# regulation signature, integrated with carrying.
#
# N=50 allocation:
#   [0:4]   input-cue   (0,1 -> cluster A ; 2,3 -> cluster B)
#   [4:6]   input-probe (drives both sub-pathways)
#   [6:16]  cluster A (10 exc) -- attractor, holds context A
#   [16:26] cluster B (10 exc) -- attractor, holds context B
#   [26:31] inhib pool (5 inh) -- winner-take-all between clusters
#   [31:37] sub-pathway A (6 exc) -- probe transform A, gated by cluster A
#   [37:43] sub-pathway B (6 exc) -- probe transform B, gated by cluster B
#   [43:45] gate-inhibitors (2 inh) -- gI_A blocks pathway A (driven by cluster B); gI_B blocks B (by A)
#   [45:48] output (3 exc)
#   [48:50] spare
# Gating logic (disinhibition, b-via-a): the NON-matching cluster drives the blocker of the OTHER
# pathway. held-A -> drives gI_B -> pathway B blocked -> pathway A open (and vice versa). Run at
# nmda_frac~0.7 (slow current sustains the cluster attractor through the delay).

R_CUE = np.arange(0, 4); R_PROBE = np.arange(4, 6)
R_CA = np.arange(6, 16); R_CB = np.arange(16, 26)
R_INH = np.arange(26, 31); R_PA = np.arange(31, 37); R_PB = np.arange(37, 43)
R_GI = np.arange(43, 45); R_OUT = np.arange(45, 48)


def build_regulation_ceiling(w_rec=4.0, w_cue=1.5, w_inh=1.2, w_probe=1.5,
                             gate_block=20.0, gate_drive=15.0, w_out=3.0):
    """Integrated carry-and-regulate ceiling (D093/D094). Held context both persists through the
    delay (cluster attractor) AND gates which sub-pathway transforms the probe (disinhibition).
    Defaults are the verified crisp-gating working point at nmda_frac~0.7."""
    signs = np.ones(N); signs[R_INH] = -1; signs[R_GI] = -1
    mag = np.zeros((N, N))                       # mag[i,j] = magnitude of synapse j->i
    # cluster attractors (carry)
    for grp in (R_CA, R_CB):
        for i in grp:
            for j in grp:
                if i != j: mag[i, j] = w_rec / len(grp)
    # selective cue -> clusters
    for j in R_CUE[:2]:
        for i in R_CA: mag[i, j] = w_cue
    for j in R_CUE[2:]:
        for i in R_CB: mag[i, j] = w_cue
    # winner-take-all
    for j in np.concatenate([R_CA, R_CB]):
        for i in R_INH: mag[i, j] = 0.1
    for j in R_INH:
        for i in np.concatenate([R_CA, R_CB]): mag[i, j] = w_inh
    # probe -> both sub-pathways
    for j in R_PROBE:
        for i in np.concatenate([R_PA, R_PB]): mag[i, j] = w_probe
    # disinhibitory gate: gate-inhibitor strongly blocks its pathway; NON-matching cluster drives it
    for i in R_PA: mag[i, R_GI[0]] = gate_block
    for i in R_PB: mag[i, R_GI[1]] = gate_block
    for j in R_CB: mag[R_GI[0], j] = gate_drive / len(R_CB)   # cluster B blocks pathway A
    for j in R_CA: mag[R_GI[1], j] = gate_drive / len(R_CA)   # cluster A blocks pathway B
    # DIFFERENT MAPS: pathway A and B -> output with different (permuted) patterns
    mag[R_OUT[0], R_PA[0]] = w_out; mag[R_OUT[0], R_PA[3]] = w_out
    mag[R_OUT[1], R_PA[1]] = w_out; mag[R_OUT[1], R_PA[4]] = w_out
    mag[R_OUT[2], R_PA[2]] = w_out; mag[R_OUT[2], R_PA[5]] = w_out
    mag[R_OUT[0], R_PB[0]] = w_out; mag[R_OUT[0], R_PB[1]] = w_out
    mag[R_OUT[1], R_PB[2]] = w_out; mag[R_OUT[1], R_PB[3]] = w_out
    mag[R_OUT[2], R_PB[4]] = w_out; mag[R_OUT[2], R_PB[5]] = w_out
    return Genome(signs=signs, mag=mag)
