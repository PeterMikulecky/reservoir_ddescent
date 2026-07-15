# Measurement protocols

Two protocols, one shared metric core. Per D026.

## Why "stationary", not "settled"

The original design read the **settled state**: drive with a constant input, wait, read the
fixed point. The settling test (2026-07-14, N=200, 400 ms constant drive) shows **there is no
fixed point** in the regime we care about:

| w0 | density | r mean | temporal CV in final 60 ms | verdict |
|---|---|---|---|---|
| 0.05 | 0.1 | 0.52 | 0.077 | drifting |
| 1.5 | 0.1 | 0.89 | 0.133 | drifting |
| 3.0 | 0.1 | 2.90 | 0.158 | **not settled** |
| 1.5 | 0.4 | 2.80 | 0.255 | **not settled** |
| 3.0 | 0.4 | 5.34 | 0.198 | **not settled** |

The network never truly settles, and it settles *less* the stronger the coupling — i.e. worst
exactly where our headline effect lives. A protocol "designed to cleanly measure the settled
state" would be measuring an object that does not exist.

**The reframe.** What *is* well-defined is a **stationary response distribution**: after the
transient, the network occupies an attractor (fixed point, limit cycle, or chaotic set) with a
mean, a covariance, and an autocorrelation time. This is better than "settled" because it is
(a) always well-defined, (b) still faithful to Frank's GRN reading — a cell in a sustained
environment occupies a characteristic expression *regime*, whether or not it is literally
static — and (c) it *tells us what to measure* instead of leaving it to intuition.

**The confound this exposes.** We currently record only the distribution's **mean** (trailing-
window average) and discard the rest. Time-averaging destroys variance, and the amount
destroyed **grows with coupling**. That mechanism alone would produce "PR falls with density
and coupling" — our headline finding — with none of it being a property of the representation.
Recanatesi et al. report the same direction by a different method with no window averaging,
which is real evidence the effect is not purely our artifact; but their model is a linearized
Poisson process, not spiking LIF with reset, so it does not settle the question for us.
Hence the **standing averaging check** below.

---

## Protocol S — stationary  (**this is the fitness protocol**)

**Purpose.** Measure the phenotype expressed in a sustained environment. Frank's core reading:
regulatory networks relaxing into expression states under sustained conditions.

**Procedure.** Stream n patterns, each held `present_ms`; discard the transient; record the
trailing window at `sample_ms` resolution. Per pattern, retain **three** state readouts rather
than one:

| readout | what it is | why |
|---|---|---|
| `X_mean` | window mean (current behaviour) | the distribution's location |
| `X_inst` | a single instantaneous sample | no averaging — the artifact control |
| `X_var` | within-window temporal variance | the discarded dynamics, as a feature in its own right |

**Standing averaging check (never optional).** Every run reports PR on all three. If
PR(`X_mean`) ≈ PR(`X_inst`), averaging is innocent and the effect is real. If they diverge, the
window mean is manufacturing the effect. This is D025's logic applied to a confound rather than
a metric: bake the check in permanently rather than trusting one run from July.

**S-specific metrics** (need sustained drive to be meaningful):
- `temporal_cv` — within-window fluctuation. Is it stationary at all?
- `autocorr_time` — how fast the attractor decorrelates from itself.
- `attractor_pr` — PR of a **single** pattern's within-window trajectory. Conceptually distinct
  from PR *across* patterns; only exists in this protocol.
- `order_dependence` — re-run with patterns shuffled; ΔPR. The carryover check (the stream is
  never reset between patterns, and at high w0 the memory may outlast `present_ms`).

**Cost.** n × `present_ms` of simulated time (150 × 150 ms = 22.5 s). The expensive protocol.

---

## Protocol T — temporal  (**characterization, not fitness**)

**Purpose.** Characterize what evolution actually built, dynamically. A reservoir is a machine
for temporal processing; Protocol S uses it in its least temporal regime. T asks what it can do
when the input has history.

**Procedure.** One continuous band-limited stream via `run_temporal`; sample the trajectory;
discard a washout prefix.

**T-specific metrics** (need a time axis to mean anything):
- `memory_capacity` — reconstruct input at delay d; sum over d. Fading-memory timescale.
- `separation` — do different input histories produce different states? (Maass; Legenstein &
  Maass kernel/generalization rank.)
- `IPC` — Dambre et al.'s task-independent capacity. **Expensive: run on the final evolved
  population or a curated subset, never per-individual in a 5000-eval GA** (D025 tiers).

**Cost.** One stream: ~2500 ms → ~500 samples ≈ **10% of Protocol S**. The asymmetry matters —
adding T is nearly free. We are not choosing between two equal costs; we are adding a cheap
second view.

---

## Shared metric core

Anything derived from a state matrix X, regardless of protocol (`metrics.full_battery`):
- **spectrum** (top-k singular values — the durable record, D025) → PR, edof at several κ,
  effective rank, spectral entropy, numerical/kernel rank
- activity / diversity / synchrony stats, weight norm, synapse count, sparse spectral radius

Protocol S runs the core on **each** of `X_mean`, `X_inst`, `X_var`. Protocol T runs it on the
trajectory samples.

---

## The thing that cannot be plural

**Metrics can be plural. Fitness cannot** — the GA needs one number. So the protocol split
forces a decision, and it is not cosmetic: *stationary* fitness and *temporal* fitness are two
different evolutionary models. Stationary = organisms experience sustained environments and are
selected on the phenotype expressed. Temporal = organisms process signal streams and are
selected on that processing.

**Decision (D026): fitness = Protocol S.** It is Frank's core claim, and it is what
`tasks.anisotropic_regression` already builds. **Protocol T is characterization**, explicitly
descriptive. This division has no forking-path risk: the confirmatory measure is unambiguous
(PR on `X_mean` under S, per D002/D016), and everything T produces is declared exploratory.

**Deferred (not rejected):** two GA arms evolving on S-fitness vs T-fitness, compared. That is
a real experiment about whether environmental structure shapes evolvability — Frank-relevant and
genuinely novel. It doubles the GA budget and adds a second flagship. Worth wanting; not first.
