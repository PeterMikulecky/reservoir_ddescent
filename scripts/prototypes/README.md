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
| `hetsyn_phase_check.py` | commensurability EXCLUDED: incommensurate delays give the same P=1 > P=3 > P=2 ordering | D142 amendment |
| `hetsyn_stream_demand.py` | YES: inverted U, gap +0.055 at lam=4 (2.7 sd), shrinking to +0.019 / +0.027 at the extremes | (pending entry) |
| `hetsyn_component_scaling.py` | YES: only P=2/m=2 (+0.055, 2.7 sd) and P=3/m=3 (+0.096, 2.2 sd) clear 2 sd | D143 |
| `hetsyn_analyze.py` | re-analyses a persisted run WITHOUT re-simulating: second-best cell, held-out-seed selection, per-seed consistency | (tool) |

**RECONFIGURED 2026-07-29: 320 ms trial (8 x 40 ms), tau grid 20-125 ms.** Trial length and tau cap were
chosen TOGETHER from a stated ratio rather than capping tau for realism and leaving the trial where it
happened to be (D139's lesson). Analytic scan of (trial, cap) pairs:

    trial            cap   m=2 peak   m=3 peak
    800 ms (8x100)   250     P=2         P=3     diagonal holds, but tau=250 exceeds the PNAS band
    400 ms (8x50)    125     P=3 (X)     P=3     near-miss: m=2 gains +0.037 vs +0.042, essentially tied
    320 ms (8x40)    125     P=2         P=3     HOLDS, and 20-125 ms is exactly the PNAS range
    300 ms (6x50)    125     P=2         P=3 (X) only 6 segments: the middle bump overlaps the others

The constraint is a RATIO, **T/tau_max <~ 3**, with enough segments (8, not 6) to keep the components
separable. Below that the "sum" component cannot be captured by one long tau and must be reconstructed
from several short ones, so P_crit stops tracking m and starts tracking how many short taus fake a long
one -- the axis measuring the wrong thing. Side benefits: 3.5x cheaper to simulate (~35-41 s/job vs
~134 s), and the D142 embarrassment of a 1600 ms winner is gone by construction.

**RESULTS ARE NOW PERSISTED (PJM, 2026-07-29).** `hetsyn_core.save_results` writes the RAW per-job rows
to a timestamped JSON under `runs/prototypes/`, so a sweep can be re-analysed -- second-best cells,
different statistics, plots -- without re-simulating. Every prototype result before this lived only in a
terminal buffer, which meant hours of re-running to answer arithmetic.

**THE DIAGONAL, derived analytically before any simulation** (ideal observer, 4000 trials):

    target         | P=1   | P=2   | P=3   | 2-1    | 3-2
    1 component    | 0.998 | 1.000 | 1.000 | +0.002 | +0.000
    2 components   | 0.919 | 1.000 | 1.000 | +0.081 | +0.000
    3 components   | 0.874 | 0.884 | 0.983 | +0.011 | +0.098

The advantage appears exactly at P = m and vanishes beyond it, so **P_crit = m and is POSITIONABLE by
task construction** -- the property D141's `P ~ m + 1` claimed for delay count and failed to deliver.
The difference is that this one was checked analytically first and would have died for twenty lines.

**PERFORMANCE FIX (2026-07-29).** The first `run_stream` rebuilt the entire Brian2 network INSIDE the
trial loop -- 144 constructions per job, ~36,000 across a 252-job run. Per-job cost was ~400 s and
RISING (batches of 10 went 668 s -> 783 -> 634 -> 1815 -> 1708) because Brian2's code-generation cache
grows monotonically within a worker process. Now the network is built ONCE and each trial swaps the
input spikes via `SpikeGeneratorGroup.set_spikes` after `net.restore("init")` -- the same pattern
`EvoNet.behave` uses. Measured ~80-150 s/job (sandbox timings are noisy), a 3-5x speedup that should
also not drift. Also: pool `maxtasksperchild=4` as insurance, and a 5-value tau grid (180 jobs, not
252). Two optimisations were TRIED AND REVERTED -- `dt=1 ms` (SpikeGeneratorGroup rejects two spikes
from one channel in a timestep, and deduplicating would silently lower the effective rate) and a 20 ms
monitor (no measurable gain, and it shifted the scores).

`hetsyn_stream_demand.py` is the first task design in this project with an ANALYTIC PRE-CHECK: an
ideal-observer calculation (no spikes, 4000 trials) showing the two-tau advantage peaks at lam~4
(+0.081) and vanishes at lam=0 and lam=100 -- the inverted-U signature -- BEFORE any simulation was run.
D126, D141 and the variable-delay design were all adopted on mechanistic arguments without such a check,
and all three failed on contact. Smoke test at lam=4, 1 seed, 60 trials: P=1 r=0.485, P=2 r=0.796, a gap
of +0.31 -- LARGER than the ideal observer's, because spiking noise punishes a compromise tau more than
it punishes a matched pair.

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

**THREAD PINNING (2026-07-29).** `hetsyn_core.py` sets `OMP_NUM_THREADS` and friends to 1 before
importing numpy. Harmless and conventional for multiprocessing, and it stays.

⚠ **BUT THE STATED REASON WAS WRONG AND IS WITHDRAWN.** It was introduced on a claim that BLAS
oversubscription cost 2.3x, inferred by comparing a single-process sandbox timing (134 s/job) against a
6-worker wall-clock rate (~312 s/job) -- **two different quantities**. Measured after the fix: ~53 s
wall per job vs ~56 s before. **No speedup.** Brian2's `numpy` codegen target does small-array work
(30 neurons, a few hundred spikes) that never enters multithreaded BLAS paths, so there was no
contention to remove. A diagnosis constructed to explain a gap that may not have existed.

**Where the time actually goes:** Python interpreter overhead per timestep, ~8000 timesteps x 144
trials per job. Two real levers, untested: BATCHING trials into one long `net.run()` (removes the
per-trial Python loop, and is compatible with cython), and the `cython` codegen target -- though PJM
notes cython constrains interwoven Python logic, which is exactly what `set_spikes` + `restore` in a
loop is. Batching first, since it helps either way and does not constrain Python.

**Standing rule earned here (2026-07-29): MEASURE IN THE CONFIGURATION YOU WILL RUN.** Three runtime
estimates were wrong today by 15x, 5x and 2.3x. The first two were arithmetic; the third was measuring
single-process and extrapolating to a parallel pool, which is a different machine state. D066 says
measure rather than estimate; the extension is that a measurement in the wrong configuration is still
an estimate.

**Standing rule earned here (D140):** if a diagnostic produces a number that enters DECISIONS, its code
is committed in the same commit as the entry. Otherwise the log accumulates claims whose evidence has
been deleted.
