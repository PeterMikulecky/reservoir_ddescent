# LIF reservoir double-descent pilot

Engine and experiment suite for testing Frank (2026), *Generalization as the great
leap in evolvability*, in a spiking reservoir. See `design_doc.md` for the full
experiment set, hypotheses, and analysis pipeline.

## Install
```
pip install brian2 numpy scipy pandas scikit-learn statsmodels
```

## Quickstart
```python
from ddescent.experiments.fixed_n import SweepConfig, run_sweep
from ddescent import analysis as A

cfg = SweepConfig(N=1000,
                  densities=(0.02, 0.05, 0.1, 0.2, 0.4, 0.8),
                  spectral_radii=(0.6, 0.9, 1.1, 1.4, 1.8),
                  seeds=tuple(range(8)),
                  task="anisotropic_regression",
                  alpha=0.0,                       # min-norm ("biological") readout
                  reservoir_kwargs=dict(bias=0.5, input_gain=0.4))  # TUNE FIRST (see below)
df = run_sweep(cfg)
results = A.run_all(df, outcome="novel_err")
print(A.univariate_r2(df, "novel_err"))
print(results["H1_model"].summary())
```

## Run the demo (small, ~1 min)
```
python run_demo.py           # writes results_demo.csv
```

## IMPORTANT: tune the operating point first
The reservoir must be in a regime where participation ratio (PR) actually *varies*
with connectivity, otherwise the flagship hypotheses are untestable. The default demo
parameters saturate the network and pin PR near the input dimensionality. Before the
real sweep, map PR against `bias`, `input_gain`, and spectral radius at fixed N and
pick the operating point where PR is largest and most responsive. See
`design_doc.md` section 3, "The tuning prerequisite."

## Environment notes (Windows + VS Code + OneDrive)

**Storage.** Keep the `runs/` output tree and the `.git` directory **out of the
OneDrive-synced path** (or excluded from sync). OneDrive locks files mid-sync, which
surfaces as intermittent `PermissionError` on the small files the pipeline rewrites
(`INDEX.csv`, `manifest.json`); those writes are now atomic-with-retry to tolerate it,
but a synced `.git` can still corrupt, and Files-On-Demand can turn large `states/`
artifacts into cloud-only stubs. Code in OneDrive is fine; outputs and the repo are
safer local.

**Path length.** Run-ID directory names are long by design. On Windows, enable long
paths (`LongPathsEnabled=1`) or you may hit the 260-char `MAX_PATH` limit once the
OneDrive-Business org prefix plus a deep `data/states/` file are added. `new_run`
warns when a run path is getting close.

**Parallelism.** The sweep parallelizes over (density, spectral_radius, seed) cells.
Pass `--workers 6` (your 6-of-8 default). It uses the **spawn** start method, matching
Windows, so behaviour is identical on the laptop and any Linux node. One sweep is one
provenance run: workers only compute rows, the parent writes `results.parquet` and
`INDEX.csv` once, so there is no concurrent-write race. Numpy code generation (no C++
compilation) means no compile-cache contention across workers.

**Terminal (cmd).** Usage examples are single-line because cmd has no backslash
line-continuation (use `^` if you must wrap). Paths use `\`.

## Layout
See the code map in `design_doc.md`.
```
ddescent/          engine + experiments + analysis
run_demo.py        end-to-end demo
design_doc.md      experiment set, hypotheses, statistics
```
