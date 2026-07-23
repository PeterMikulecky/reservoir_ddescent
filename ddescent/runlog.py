"""Tee-logging for analysis & troubleshooting scripts (D102): capture terminal output to a durable
log file so the ANALYTIC NARRATIVE survives the terminal closing, not just the data.

Usage:
    from ddescent.runlog import tee
    with tee("sparse_density_sweep"):        # -> logs to analysis_logs/<date>_sparse_density_sweep.log
        print("...everything printed here goes to console AND the log...")

or point it at a specific run dir:
    with tee("threshold_check", log_dir=run.logs()):
        ...
"""
from __future__ import annotations
import sys, os, datetime, contextlib


class _Tee:
    def __init__(self, stream, fh):
        self.stream = stream; self.fh = fh
    def write(self, data):
        self.stream.write(data); self.fh.write(data); self.fh.flush()
    def flush(self):
        self.stream.flush(); self.fh.flush()


@contextlib.contextmanager
def tee(name, log_dir="runs", header=None):
    """Context manager: mirror stdout+stderr to a timestamped log file for the duration of the block.
    Records a header (timestamp, command line) so the log is self-describing (D102).

    **ALL OUTPUTS LIVE UNDER `runs/`** (2026-07-22 convention): one predictable location for every
    artifact this project produces. Probes log to `runs/` directly; multi-cell experiments pass
    `log_dir="runs/<experiment>"` so their log sits with their checkpoints and summary.
    (Supersedes the old `analysis_logs/` default; existing logs there remain as committed history.)"""
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(log_dir, f"{stamp}_{name}.log")
    fh = open(path, "w")
    fh.write(f"# analysis log: {name}\n# timestamp: {datetime.datetime.now().isoformat()}\n")
    fh.write(f"# command: {' '.join(sys.argv)}\n")
    if header:
        fh.write(f"# {header}\n")
    fh.write("#" + "=" * 68 + "\n\n"); fh.flush()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = _Tee(old_out, fh); sys.stderr = _Tee(old_err, fh)
    try:
        print(f"[logging to {path}]")
        yield path
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        fh.close()
        print(f"[analysis log saved: {path}]")
