# Naming and provenance convention

Standard for every script, run, and output in this project. Enforced by
`ddescent/provenance.py` — use it rather than hand-naming directories, so the
convention can't drift as the project grows.

## 1. The atomic unit: a *run*

A run is one execution of one entry-point script that produces outputs. Every run
gets a **run ID**, which is simultaneously (a) the name of the run's output
directory and (b) the key in the run registry.

```
{STAGE}-{slug}__{YYYYMMDD-HHMMSS}__{type}__{codever}[__{tag}]
```

| Field | Meaning | Rules |
|---|---|---|
| STAGE | experiment code | `E0`–`E8`, `T0` (tuning/prep), `AN` (analysis-only). Uppercase. |
| slug | stable short name | from the controlled vocabulary below; lowercase snake_case |
| timestamp | run start, **UTC** | `YYYYMMDD-HHMMSS`; sortable; UTC avoids collaborator tz drift |
| type | provenance status | `reg` (pre-registered/confirmatory), `exp` (exploratory), `smoke` (test/demo) |
| codever | code version | `g` + git short hash; append `+dirty` if the working tree is uncommitted |
| tag | optional freeform | `[a-z0-9-]+`, short; e.g. `N1000-seeds0-31`, `biasscan` |

Delimiters: `__` between fields, `-` within a field. No spaces, no dots except
file extensions.

### Controlled STAGE → slug vocabulary
```
E0  readout_width            E5  temporal
E1  fixed_n                  E6  snakeness
E2  vargeo                   E7  ladder
E3  aliasing                 E8  neutral
E4  implicit_bias            T0  tune_operating_point
                             AN  analysis
```
One slug per stage; the mapping lives in `provenance.CANONICAL` and cannot be
overridden ad hoc. New experiments get a new (stage, slug) pair added there.

## 2. The confirmatory firewall

`type` is not cosmetic. The pilot's flagship (E1) is pre-registered, so:

- **`reg` runs abort on a dirty git tree.** A confirmatory result can never come
  from uncommitted code. Override exists (`allow_dirty=True`) but stamps
  `git_dirty: true` loudly in the manifest.
- `exp` and `smoke` runs may run on a dirty tree (flagged in the manifest).
- The operating point chosen in a `T0`/`exp` tuning sweep, and the pre-registered
  predictions, are fixed *before* the first `E1`/`reg` run. Provenance makes that
  auditable: the reg run's manifest records the git hash, which must post-date the
  registration commit.

## 3. Directory layout

```
project_root/
  ddescent/                     # importable package — code, version-controlled
  scripts/                      # runnable entry points (see naming below)
  configs/                      # input configs, version-controlled
  runs/                         # ALL outputs; never hand-edited
    INDEX.csv                   # append-only registry, one row per run
    E1_fixed_n/                 # grouped by {STAGE}_{slug}
      E1-fixed_n__20260713-142530__reg__g1a2b3c__N1000-seeds0-31/   # == run_id
        manifest.json           # full provenance record
        config.snapshot.json    # frozen copy of the exact config used
        env.txt                 # key package versions
        data/
          results.parquet       # tidy per-run table (the analysis input)
          states/               # optional heavy artifacts
        figures/
          {runhash}_pr_vs_gen.png
        analysis/
          h1_mixedmodel.txt
        logs/run.log
```

The grouping directory (`runs/E1_fixed_n/`) and the run directory (the full run ID)
share the `{STAGE}_{slug}` token, so file paths and directory names use one
compatible scheme end to end.

## 4. Standardized filenames inside a run

Because the run directory already carries the full ID, files inside use **role-based
names** so scripts can locate them blindly:

- `manifest.json`, `config.snapshot.json`, `env.txt`
- `data/results.parquet` (headline tidy table), `data/<role>.parquet`
- `figures/{runhash}_<slug>.png` — figures and headline tables get an 8-char
  `runhash` prefix (a hash of the run ID) so a file copied *out* of the run
  directory is still traceable. `manifest.json` maps `runhash -> run_id`.
- `analysis/<hypothesis>_<method>.txt|json`
- `logs/run.log`

## 5. Provenance chain for analysis passes

An `AN` (analysis-only) run that consumes prior simulation runs records their run IDs
in `manifest.upstream_run_ids`. A figure therefore traces: figure filename → runhash
→ manifest → upstream simulation run IDs → their git hashes and configs. No output is
ever an orphan.

## 6. Entry-point script naming

```
scripts/run_{STAGE}_{slug}.py        # produces a simulation run
scripts/analyze_{STAGE}_{slug}.py    # produces an AN run from prior run(s)
scripts/figure_{STAGE}_{slug}.py     # figures (usually folded into analyze_)
```
The script name shares `{STAGE}_{slug}` with the runs it creates, closing the loop
from code to outputs.

## 7. What every manifest records
run_id, runhash, stage, slug, type, tag; git_commit, git_dirty; created_utc,
finished_utc, status; hostname, user, python + key package versions;
config_snapshot path; seeds, n_conditions; script_path, script_argv;
upstream_run_ids; free-text notes.
```
