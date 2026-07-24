"""CUE -> DELAY -> PROBE task with an XOR target.

WHY THIS REPLACES `hierarchical_environments` FOR THE CONTEXT-MODULATION QUESTION.
The covariance-context task turned out to require no memory at all: context was ~98.6% identifiable
from a SINGLE stimulus, so nothing ever had to be held across the dwell window. Worse, its matched
control (shuffling stimulus order) removed nothing, because every stimulus independently announced its
own context — so `context_gain ~ 0` was uninformative rather than a substrate finding.

This design imposes the memory requirement by construction, and its controls remove what they claim to.

TRIAL STRUCTURE (all segments share the SAME input channels; role is signalled only by TIMING and by
which pattern appears — never by a dedicated context wire, so context is still INFERRED, not read off
a label):

    [ CUE ] [ DELAY ] [ PROBE ] [ READ ]
      c1/c2  (silent)   p1/p2    (silent; response sampled here)

TARGET = XOR of cue and probe identity:
    (c1,p1) -> +1     (c1,p2) -> -1
    (c2,p1) -> -1     (c2,p2) -> +1

**Why XOR, and not something simpler.** It makes every degenerate strategy score exactly chance:
    ignore the cue, read the probe  -> 50%
    ignore the probe, read the cue  -> 50%
    hold the cue AND read the probe -> up to 100%
So the floor is chance BY CONSTRUCTION. It cannot be beaten by extra capacity, a static nonlinear
expansion, or a lucky random projection — which is exactly the confound that made the old
"memoryless floor" uninterpretable (a static random expansion matched it). Here, without the held
cue, the probe carries ZERO information about the answer. There is nothing left to confound.

WHAT THE NETWORK MUST ACQUIRE (PJM's four steps):
    1. encode the cue patterns discriminably          -- development can build this
    2. MAINTAIN the cue across the delay              -- development can build this (Hebbian
                                                         strengthening of whatever recurrence sustains
                                                         a cue-specific assembly during the silence)
    3. encode the probe patterns discriminably        -- development can build this
    4. bind held-cue x probe -> the XOR sign          -- SELECTION ALONE. The assignment is arbitrary,
                                                         so no unsupervised rule can discover it.

CONTROLS (unlike the old shuffle control, these remove what they claim to):
    omit_cue        -- cue segment blanked. MUST fall to chance. Tests cue use.
    scramble        -- cue/probe pairing permuted across trials. MUST fall to chance. Tests binding.
    delay sweep     -- lengthen the delay past tau_slow. Where does performance break? (H-D)

DIFFICULTY RAMPS, once evolvability is established: longer delay; a filled (non-silent) delay so the
cue must be held WHILE other input is processed; less distinct cues; more contexts/probes; and the
strongest version — cue and probe drawn from the SAME pattern set, so role is signalled by timing alone.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

# Segment layout within a trial. The DELAY is variable-length, so offsets are computed rather than
# fixed:   CUE(1) | DELAY(delay_segments) | PROBE(1) | READ(1)
def seg_layout(delay_segments: int) -> dict:
    return dict(cue=0,
                delay=1,
                probe=1 + delay_segments,
                read=2 + delay_segments,
                n_seg=3 + delay_segments)


@dataclass
class TrialTask:
    """Trials flattened to (n_trials*N_SEG, K) so the existing `behave()` can drive it unchanged:
    each row is one presentation window. The response is sampled from the READ segment."""
    E_train: np.ndarray
    Y_train: np.ndarray
    cue_train: np.ndarray
    probe_train: np.ndarray
    E_val: np.ndarray
    Y_val: np.ndarray
    cue_val: np.ndarray
    probe_val: np.ndarray
    E_test: np.ndarray
    Y_test: np.ndarray
    cue_test: np.ndarray
    probe_test: np.ndarray
    meta: dict | None = None

    # --- split plumbing, mirroring the D113 three-way discipline ---------------------------------
    def _split(self, which: str):
        if which == "train":
            return self.E_train, self.Y_train, self.cue_train, self.probe_train
        if which == "val":
            return self.E_val, self.Y_val, self.cue_val, self.probe_val
        if which == "test":
            return self.E_test, self.Y_test, self.cue_test, self.probe_test
        raise ValueError(f"unknown split {which!r}")

    def response_rows(self, split: str = "test") -> np.ndarray:
        """Row indices of the READ segment — where the response is sampled."""
        m = self.meta or {}
        lay = seg_layout(m.get("delay_segments", 1))
        n_trials = m.get("n_trials", {}).get(split, len(self._split(split)[1]))
        return np.arange(n_trials) * lay["n_seg"] + lay["read"]

    def headroom(self, split: str = "test") -> dict:
        """Chance is exact here, not estimated: without the held cue the probe carries NO information
        about the XOR sign, so any cue-blind strategy scores exactly chance. Reported in the same NMSE
        units the rest of the pipeline uses (predicting the mean gives NMSE 1.0)."""
        _, Y, _, _ = self._split(split)
        return dict(memoryless_floor=1.0,          # cue-blind == predicting the mean == NMSE 1.0
                    oracle_ceiling=0.0,            # perfect binding == zero error
                    chance_accuracy=0.5)


def _orthonormal_patterns(K: int, n: int, rng) -> np.ndarray:
    """n mutually orthonormal K-dim patterns (maximally discriminable — discriminability is NOT what
    this task tests; holding and binding are)."""
    A = rng.standard_normal((K, max(n, K)))
    Q, _ = np.linalg.qr(A)
    return Q[:, :n].T


def cue_delay_probe(K: int = 10,
                    n_cues: int = 2,
                    n_probes: int = 2,
                    n_trials: int = 40,
                    n_val: int | None = None,
                    n_test: int | None = None,
                    delay_segments: int = 1,
                    omit_cue: bool = False,
                    scramble: bool = False,
                    seed: int = 0) -> TrialTask:
    """Build the task.

    delay_segments : how many DELAY windows sit between cue and probe. 1 (= one present_ms) is the
        easy starting point: below tau_slow the substrate can coast on passive decay, so steps 1/3/4
        are tested with step 2 on trainer wheels. SWEEP THIS to find where maintenance must become
        active — that boundary is what H-D is about.
    omit_cue / scramble : the two controls. Both MUST fall to chance if the network is doing the task.
    """
    rng = np.random.default_rng(seed)
    n_val = n_val if n_val is not None else n_trials
    n_test = n_test if n_test is not None else n_trials

    # Cue and probe patterns live in the SAME input space and are all mutually orthogonal. Distinct
    # patterns for cue vs probe keeps the starting version easy; the hard version (shared pattern set,
    # role signalled by timing alone) is a later difficulty ramp.
    pats = _orthonormal_patterns(K, n_cues + n_probes, rng)
    cue_pats, probe_pats = pats[:n_cues], pats[n_cues:]

    lay = seg_layout(delay_segments)

    def build(n, rng_local):
        # balanced over the n_cues x n_probes trial types, then shuffled
        types = np.tile(np.arange(n_cues * n_probes), int(np.ceil(n / (n_cues * n_probes))))[:n]
        rng_local.shuffle(types)
        cue_idx, probe_idx = types // n_probes, types % n_probes
        # XOR target on identity: +1 when indices agree, -1 when they differ
        y = np.where(cue_idx == probe_idx, 1.0, -1.0)[:, None]
        if scramble:
            # BINDING CONTROL. Permute the TARGETS against the stimuli, leaving stimulus statistics
            # (and both marginals) untouched. Because cue-only and probe-only rules are ALREADY at
            # chance, destroying the cue<->probe<->target correspondence makes the task unlearnable:
            # a network doing the real thing must fall to chance here.
            # (A first version permuted probe_idx and then computed y from the PERMUTED pairing —
            # which merely generates a different VALID trial set and removes nothing.)
            y = y[rng_local.permutation(len(y))]
        E = np.zeros((n * lay["n_seg"], K))
        for t in range(n):
            base = t * lay["n_seg"]
            if not omit_cue:
                E[base + lay["cue"]] = cue_pats[cue_idx[t]]
            E[base + lay["probe"]] = probe_pats[probe_idx[t]]
            # DELAY segments and the READ segment stay silent
        return E, y, cue_idx, probe_idx

    Etr, Ytr, ctr, ptr = build(n_trials, rng)
    Eva, Yva, cva, pva = build(n_val, rng)
    Ete, Yte, cte, pte = build(n_test, rng)

    meta = dict(K=K, n_cues=n_cues, n_probes=n_probes, delay_segments=delay_segments,
                n_seg=lay["n_seg"], omit_cue=omit_cue, scramble=scramble, seed=seed,
                cue_patterns=cue_pats, probe_patterns=probe_pats,
                n_trials=dict(train=n_trials, val=n_val, test=n_test))
    return TrialTask(Etr, Ytr, ctr, ptr, Eva, Yva, cva, pva, Ete, Yte, cte, pte, meta=meta)
