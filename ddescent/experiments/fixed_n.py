"""
Flagship experiment: the fixed-N dissociation.

Hold neuron count N fixed and sweep the connectivity knobs (density p, spectral
radius rho) across many random seeds. For each reservoir, push a task's train /
test / novel environments through it, fit a readout, and record three candidate
predictors of generalization plus the outcome:

    predictors : (a) synapse count   -- Frank's raw 'parameter count'
                 (b) density         -- 'connectivity / more wiring'
                 (c) participation ratio (PR) of the train-state covariance
                                       -- measured effective dimensionality
    outcome    : test / novel generalization error and the generalization gap

The hypotheses this feeds (see design_doc.md):
    H1  PR predicts generalization better than count or density.
    H2  density -> generalization is NON-monotonic (dense coupling can collapse PR).
    H3  generalization improves with PR then saturates near the environment's
        intrinsic dimensionality.
    H4  the effect of density on generalization is MEDIATED by PR.
    H5  the interpolation-threshold location scales with PR, not nominal N.

This module only produces the tidy results table. The statistics live in
ddescent.analysis so the same table can be re-analyzed without re-simulating.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import itertools
import numpy as np
import pandas as pd

from ..connectivity import ConnectivityConfig, make_recurrent_weights, make_input_weights, _spectral_radius
from ..reservoir import ReservoirConfig, LIFReservoir
from ..measures import participation_ratio, effective_rank, intrinsic_dim_of_inputs
from .. import readout as ro
from .. import tasks as T


@dataclass
class SweepConfig:
    N: int = 1000
    densities: tuple = (0.02, 0.05, 0.1, 0.2, 0.4, 0.8)
    spectral_radii: tuple = (0.6, 0.9, 1.1, 1.4, 1.8)
    seeds: tuple = (0, 1, 2, 3, 4)
    task: str = "anisotropic_regression"   # or "snakeness"
    task_kwargs: dict = field(default_factory=dict)
    alpha: float = 0.0                     # readout regularization (0 == min-norm)
    input_scale: float = 1.0
    reservoir_kwargs: dict = field(default_factory=dict)


def _make_task(cfg: SweepConfig, seed: int):
    if cfg.task == "anisotropic_regression":
        return T.anisotropic_regression(seed=seed, **cfg.task_kwargs), "regression"
    elif cfg.task == "snakeness":
        return T.snakeness_classification(seed=seed, **cfg.task_kwargs), "classification"
    raise ValueError(cfg.task)


def _attach_features(task, res: LIFReservoir):
    task.U_train_feat = res.run_static(task.U_train)
    task.U_test_feat = res.run_static(task.U_test)
    task.U_novel_feat = res.run_static(task.U_novel) if task.U_novel is not None else None
    return task


def _run_one_cell(payload: dict) -> dict:
    """Compute one (density, rho, seed) cell. TOP-LEVEL and picklable so it works
    under Windows 'spawn' multiprocessing. Each call builds its own Brian2 network;
    no Brian2 objects are shared across processes.
    """
    cfg = payload["cfg"]
    density, rho, seed = payload["density"], payload["rho"], payload["seed"]

    cc = ConnectivityConfig(N=cfg.N, density=density, spectral_radius=rho, seed=seed)
    W = make_recurrent_weights(cc)
    rho_measured = _spectral_radius(W)
    Win = make_input_weights(cfg.N, _task_K(cfg, seed), scale=cfg.input_scale, seed=seed + 100)
    res = LIFReservoir(W, Win, ReservoirConfig(N=cfg.N, seed=seed + 200, **cfg.reservoir_kwargs))

    task, mode = _make_task(cfg, seed)
    task = _attach_features(task, res)

    pr = participation_ratio(task.U_train_feat)
    readout = ro.LinearReadout(alpha=cfg.alpha)
    if mode == "regression":
        perf = ro.evaluate_regression(readout, task)
    else:
        perf = ro.evaluate_classification(readout, task, task.meta["n_classes"])

    return dict(
        density=density, spectral_radius_target=rho, spectral_radius_measured=rho_measured,
        seed=seed, synapse_count=cc.synapse_count(),
        log_synapse_count=float(np.log10(max(cc.synapse_count(), 1))),
        pr=pr, effective_rank=effective_rank(task.U_train_feat),
        env_intrinsic_dim=intrinsic_dim_of_inputs(task.U_train),
        n_train=task.U_train.shape[0], N=cfg.N, **perf,
    )


def run_sweep(cfg: SweepConfig, verbose: bool = True,
              n_workers: int = 1, mp_context: str = "spawn") -> pd.DataFrame:
    """Run the connectivity sweep. One sweep == one run == one results table.

    n_workers > 1 uses a process pool (default 'spawn' context, matching Windows so
    behaviour is identical on the laptop and any Linux node). Provenance stays with
    the PARENT: this function only returns the table; the caller wraps it in a single
    provenance run and writes INDEX.csv once, avoiding concurrent-write races.
    """
    grid = list(itertools.product(cfg.densities, cfg.spectral_radii, cfg.seeds))
    payloads = [dict(cfg=cfg, density=d, rho=r, seed=s) for (d, r, s) in grid]

    rows = []
    if n_workers <= 1:
        for i, p in enumerate(payloads):
            row = _run_one_cell(p)
            rows.append(row)
            if verbose:
                print(f"[{i+1}/{len(grid)}] p={row['density']:.2f} rho={row['spectral_radius_target']:.1f} "
                      f"seed={row['seed']} PR={row['pr']:6.1f} test_err={row['test_err']:.3f}")
    else:
        import multiprocessing as mp
        ctx = mp.get_context(mp_context)
        with ctx.Pool(processes=n_workers) as pool:
            for i, row in enumerate(pool.imap_unordered(_run_one_cell, payloads)):
                rows.append(row)
                if verbose:
                    print(f"[{i+1}/{len(grid)}] p={row['density']:.2f} rho={row['spectral_radius_target']:.1f} "
                          f"seed={row['seed']} PR={row['pr']:6.1f} test_err={row['test_err']:.3f}")
    return pd.DataFrame(rows)


def _task_K(cfg: SweepConfig, seed: int) -> int:
    task, _ = _make_task(cfg, seed)
    return task.U_train.shape[1]


if __name__ == "__main__":
    # tiny demo sweep
    cfg = SweepConfig(N=300, densities=(0.05, 0.2, 0.6), spectral_radii=(0.8, 1.4),
                      seeds=(0, 1), task_kwargs=dict(K=12, n_train=120, n_test=120),
                      reservoir_kwargs=dict(present_ms=150, readout_window_ms=60))
    df = run_sweep(cfg)
    print(df[["density", "spectral_radius_target", "pr", "test_err", "novel_err"]].round(3))
