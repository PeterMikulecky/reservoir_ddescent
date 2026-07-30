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

**KNOWN BUG in `hetsyn_variable_delay.py` and `hetsyn_pgroup_prototype.py`:** the probe is routed to
group 1 regardless of P, so for P>2 the extra groups are never used and those columns are meaningless.
Fixed understanding in D141: cue synapses must be distributed across the MEMORY groups; the probe needs
only one fast group.

**Standing rule earned here (D140):** if a diagnostic produces a number that enters DECISIONS, its code
is committed in the same commit as the entry. Otherwise the log accumulates claims whose evidence has
been deleted.
