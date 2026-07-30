# prototypes/

Throwaway diagnostics that produced RECORDED FINDINGS. They live here because the findings are cited in
DECISIONS and were, until 2026-07-29, irreproducible: every one of them ran from /tmp and was lost when
the shell exited. Persisting them is not tidiness -- a decision entry that cites a number nobody can
regenerate is a claim without evidence.

These are NOT maintained study code. They hardcode parameters, print rather than persist, and several
duplicate machinery that exists properly in `scripts/`. Read them as the appendix to a decision entry,
not as tools.

| file | produced | cited in |
|---|---|---|
| `measure_fi_gain.py` | df/dI = 6.60 Hz per unit current; the conversion D138 omitted | D138 amendment |
| `jeff_sweep.py` | J_eff 0 -> 0.95 at inhibition ratio 1; ac(100) rises 0.11 -> 0.25, ~15x short of prediction | D138 amendment |
| `spontaneous_timescale.py` | spontaneous autocorrelation vs coupling, with a no-recurrence floor | D138 amendment |
| `aggregation_comparison.py` | mean-of-PREDICTIONS 0.517 vs mean-of-SCORES 0.114 (below chance) | D134 amendment |
| `hetsyn_step1_conjunction.py` | cue->slow / probe->fast: 0.583 -> 0.917 at 400 ms delay | D139 |
| `hetsyn_pgroup_prototype.py` | P-group synaptic timescales; generated equations, P currents per neuron | D140 |
| `hetsyn_drive_bisection.py` | the 0.52 vs 0.98 difference is INPUT DRIVE, not N (24 and 30 identical) | D140 |
| `hetsyn_p1_control.py` | P=1 swept over tau reaches 0.850, not 0.583 -- the gap is 0.13, not 0.33 | D139 amendment |
| `hetsyn_variable_delay.py` | variable delay lowers P=1 (0.819 -> 0.667) but COLLAPSES P=2 to chance | D141 |
| `hetsyn_probe_aligned.py` | probe-aligned readout reproduces the P=2 collapse (0.509); P=3 recovers to 0.690 | D141 amendment |
| `hetsyn_core.py` | **the single source** of `run_block` and `decode`; everything downstream imports it | (infrastructure) |
| `hetsyn_tau_sweep.py` | swept properly, P=1 (0.707) BEATS P=3 (0.662) beats P=2 (0.534) -- `P ~ m+1` refuted | D142 |
| `hetsyn_phase_check.py` | **NOT YET RUN** -- is D142 confounded by commensurate delay/tau lattices? | (pending) |

**A BUG IN `hetsyn_tau_sweep.py` INVALIDATED AN 80-JOB RUN (2026-07-29).** Cue synapses were held in a
LIST and passed to `b2.run()`, whose magic collection scans the calling frame's VARIABLES -- so they were
never added to the network and every trial ran with NO CUE INPUT, silently. Brian2 warns only at garbage
collection, after the results exist. Fixed with an explicit `b2.Network(*objs)` and an assertion on the
synapse count -- and the simulation code was extracted to `hetsyn_core.py`, since DUPLICATED simulation
code is how two prototypes with apparently-identical construction diverged invisibly in the first place. `hetsyn_probe_aligned.py` escaped it by using `globals()`, which collection DOES scan, and
was used to verify the fix (P=1 0.495 / P=2 0.509 / P=3 0.690 reproduced exactly).

`hetsyn_tau_sweep.py` is the exception to "not maintained": it is intended to be RUN LOCALLY with
`--workers 6` (~25 min; 80 jobs at ~106 s each, measured -- an earlier 7 s estimate was wrong by 15x,
which is D066 again). Its reporting path was exercised on synthetic results before hand-off.

**KNOWN BUG in `hetsyn_variable_delay.py` and `hetsyn_pgroup_prototype.py`:** the probe is routed to
group 1 regardless of P, so for P>2 the extra groups are never used and those columns are meaningless.
Fixed understanding in D141: cue synapses must be distributed across the MEMORY groups; the probe needs
only one fast group.

**Standing rule earned here (D140):** if a diagnostic produces a number that enters DECISIONS, its code
is committed in the same commit as the entry. Otherwise the log accumulates claims whose evidence has
been deleted.
