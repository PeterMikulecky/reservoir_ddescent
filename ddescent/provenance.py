"""
Provenance and run-management utility. Enforces NAMING.md.

Use `new_run(...)` to start any script that produces outputs. It builds the run ID,
creates the standardized directory tree, captures git + environment provenance,
freezes the config, registers the run, and hands back a `Run` object whose helpers
give you the canonical output paths. Call `run.finalize(...)` at the end.

Nothing here is heavy; it depends only on the standard library so it can wrap any
script without pulling in the scientific stack.
"""
from __future__ import annotations

import csv
import getpass
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

# ------------------------------------------------------------------ vocabularies
CANONICAL = {
    "E0": "readout_width",
    "E1": "fixed_n",
    "E2": "vargeo",
    "E3": "aliasing",
    "E4": "implicit_bias",
    "E5": "temporal",
    "E6": "snakeness",
    "E7": "ladder",
    "E8": "neutral",
    "E9": "evolve",
    "T0": "tune_operating_point",
    "AN": "analysis",
}
TYPES = ("reg", "exp", "smoke")

# Windows MAX_PATH is 260; warn well before it because OneDrive-Business org
# prefixes and the states/ subtree eat the margin fast.
_PATH_WARN_CHARS = 200


def _robust_write(path: Path, text: str, retries: int = 6, backoff: float = 0.3):
    """Atomic write with retry, to survive OneDrive/antivirus file locks on Windows.

    Writes to a temp sibling then os.replace (atomic on the same filesystem). Retries
    with exponential backoff on PermissionError, which is how a mid-sync OneDrive lock
    surfaces. Use for the small, frequently-rewritten provenance files.
    """
    tmp = path.with_name(path.name + ".tmp")
    last = None
    for i in range(retries):
        try:
            tmp.write_text(text)
            os.replace(tmp, path)
            return
        except PermissionError as e:      # OneDrive / AV holding a lock
            last = e
            time.sleep(backoff * (2 ** i))
    raise last

# key packages to pin in env.txt (best-effort; missing ones are skipped)
_PINNED = ("brian2", "numpy", "scipy", "pandas", "statsmodels", "scikit-learn")


# ------------------------------------------------------------------ git / env
def git_info(repo_dir: Path) -> tuple[str, bool]:
    """Return (short_commit, dirty). ('nogit', False) if not a repo."""
    def _git(*args):
        return subprocess.run(["git", "-C", str(repo_dir), *args],
                              capture_output=True, text=True, check=True).stdout.strip()
    try:
        commit = _git("rev-parse", "--short", "HEAD")
        dirty = bool(_git("status", "--porcelain"))
        return commit, dirty
    except Exception:
        return "nogit", False


def git_message(repo_dir: Path) -> str:
    """Return the subject line of HEAD's commit ('' if unavailable). A bare hash is
    opaque in a lab notebook; the message is what makes a run's code state legible."""
    try:
        return subprocess.run(["git", "-C", str(repo_dir), "log", "-1", "--pretty=%s"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""


def _codever(commit: str, dirty: bool) -> str:
    return f"g{commit}" + ("+dirty" if dirty else "")


def _env_lines() -> list[str]:
    lines = [f"python {platform.python_version()}", f"platform {platform.platform()}"]
    try:
        from importlib.metadata import version, PackageNotFoundError
        for pkg in _PINNED:
            try:
                lines.append(f"{pkg} {version(pkg)}")
            except PackageNotFoundError:
                pass
    except Exception:
        pass
    return lines


# ------------------------------------------------------------------ run id
def make_run_id(stage: str, run_type: str, codever: str,
                tag: str | None = None, when: datetime | None = None) -> str:
    if stage not in CANONICAL:
        raise ValueError(f"unknown stage {stage!r}; add it to CANONICAL")
    if run_type not in TYPES:
        raise ValueError(f"type must be one of {TYPES}")
    slug = CANONICAL[stage]
    ts = (when or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    rid = f"{stage}-{slug}__{ts}__{run_type}__{codever}"
    if tag:
        clean = "".join(c if (c.isalnum() or c == "-") else "-" for c in tag.lower())
        rid += f"__{clean}"
    return rid


def runhash(run_id: str) -> str:
    return hashlib.sha1(run_id.encode()).hexdigest()[:8]


# ------------------------------------------------------------------ Run object
@dataclass
class Run:
    run_id: str
    runhash: str
    dir: Path
    manifest: dict = field(default_factory=dict)
    project_root: Path | None = None      # repo root; where LAB_NOTEBOOK.md lives

    # canonical subdirectories
    @property
    def data(self) -> Path: return self._sub("data")
    @property
    def figures(self) -> Path: return self._sub("figures")
    @property
    def analysis(self) -> Path: return self._sub("analysis")
    @property
    def logs(self) -> Path: return self._sub("logs")

    def _sub(self, name: str) -> Path:
        p = self.dir / name
        p.mkdir(exist_ok=True)
        return p

    def figure_path(self, slug: str, ext: str = "png") -> Path:
        """Figure path with a runhash prefix so it stays traceable if copied out."""
        return self.figures / f"{self.runhash}_{slug}.{ext}"

    def table_path(self, slug: str = "results", ext: str = "parquet") -> Path:
        return self.data / f"{slug}.{ext}"

    def finalize(self, status: str = "complete", notebook_note: str | None = None,
                 notebook: bool = True, **extra):
        self.manifest["status"] = status
        self.manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        self.manifest.update(extra)
        _robust_write(self.dir / "manifest.json", json.dumps(self.manifest, indent=2))
        _update_index(self)
        # auto-append the factual skeleton to the lab notebook (skip smoke tests).
        # The interpretation line is left blank on purpose, for a human to fill in.
        if notebook and self.project_root and self.manifest.get("type") != "smoke":
            _append_notebook(self.project_root, self.manifest, notebook_note)


# ------------------------------------------------------------------ notebook
def _append_notebook(project_root: Path, manifest: dict, note: str | None):
    """Append a dated, factual run stub to LAB_NOTEBOOK.md with a blank interpretation
    line. Facts are automatic; meaning is hand-written. The notebook lives in the repo
    (version-controlled), NOT in the runs tree, because it is narrative, not data."""
    nb = Path(project_root) / "LAB_NOTEBOOK.md"
    when = (manifest.get("finished_utc") or "")[:16].replace("T", " ")
    git = manifest.get("git_commit", "?")
    msg = manifest.get("git_message", "")
    gitstr = f"`g{git}`" + (f" ({msg})" if msg else "")
    if manifest.get("git_dirty"):
        gitstr += " +dirty"
    entry = (
        f"\n## {when} — `{manifest.get('run_id','?')}`  <!-- auto -->\n"
        f"- type `{manifest.get('type','?')}` · stage `{manifest.get('stage','?')}` · "
        f"git {gitstr} · status **{manifest.get('status','?')}**\n"
        f"- result: {note or '(no result note passed to finalize)'}\n"
        f"- _interpretation:_ \n"
    )
    try:
        if not nb.exists():
            nb.write_text("# Lab notebook\n\n(newest entries at the bottom; "
                          "`<!-- auto -->` stubs are machine-written, prose is hand-written)\n")
        with open(nb, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass   # never let notebook I/O break a run's finalize


# ------------------------------------------------------------------ factory
def new_run(stage: str, run_type: str, *, project_root: str | Path = ".",
            runs_root: str | Path | None = None,
            config: dict | None = None, tag: str | None = None,
            seeds=None, upstream_run_ids=None, notes: str = "",
            allow_dirty: bool = False, argv=None) -> Run:
    """Create a fully provenanced run directory and return a Run handle.

    project_root : where the git repo lives (used for the code-version hash).
    runs_root    : where output run directories are written. Defaults to the
                   DDESCENT_RUNS_ROOT environment variable, else project_root/runs.
                   Set this to a non-local drive to keep large run data off the
                   laptop's disk while the code repo stays local + on GitHub.
    """
    root = Path(project_root).resolve()
    commit, dirty = git_info(root)
    codever = _codever(commit, dirty)

    if run_type == "reg" and dirty and not allow_dirty:
        raise RuntimeError(
            "Refusing to start a 'reg' (confirmatory) run on a DIRTY git tree. "
            "Commit your code first, or pass allow_dirty=True to override "
            "(the manifest will record git_dirty=true)."
        )

    rid = make_run_id(stage, run_type, codever, tag)
    rh = runhash(rid)
    runs_base = Path(runs_root or os.environ.get("DDESCENT_RUNS_ROOT") or (root / "runs")).resolve()
    run_dir = runs_base / f"{stage}_{CANONICAL[stage]}" / rid

    # Windows/OneDrive path-length guard: warn before writing many files into a
    # path that a deep states/ subtree could push past MAX_PATH (260).
    approx_deep = len(str(run_dir)) + len("/data/states/states_p0.10_sr1.40_seed7.npy")
    if approx_deep > _PATH_WARN_CHARS:
        warnings.warn(
            f"Run path is ~{approx_deep} chars incl. a typical deep artifact; "
            f"on Windows this risks the 260-char MAX_PATH limit. Enable long paths "
            f"(LongPathsEnabled=1) or keep runs/ outside the OneDrive-synced tree.",
            stacklevel=2,
        )

    run_dir.mkdir(parents=True, exist_ok=False)

    # freeze config + environment
    if config is not None:
        _robust_write(run_dir / "config.snapshot.json",
                      json.dumps(config, indent=2, default=str))
    _robust_write(run_dir / "env.txt", "\n".join(_env_lines()))

    manifest = dict(
        run_id=rid, runhash=rh, stage=stage, slug=CANONICAL[stage],
        type=run_type, tag=tag, git_commit=commit, git_dirty=dirty,
        git_message=git_message(root),
        created_utc=datetime.now(timezone.utc).isoformat(), finished_utc=None,
        status="running", hostname=socket.gethostname(), user=_safe_user(),
        runs_root=str(runs_base),
        script_path=(argv or sys.argv)[0] if (argv or sys.argv) else None,
        script_argv=argv or sys.argv,
        seeds=list(seeds) if seeds is not None else None,
        upstream_run_ids=list(upstream_run_ids) if upstream_run_ids else [],
        notes=notes,
    )
    _robust_write(run_dir / "manifest.json", json.dumps(manifest, indent=2))
    run = Run(rid, rh, run_dir, manifest, project_root=root)
    _update_index(run)
    return run


def _safe_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


# ------------------------------------------------------------------ registry
_INDEX_FIELDS = ["run_id", "runhash", "stage", "slug", "type", "git_commit",
                 "git_dirty", "created_utc", "status", "tag"]


def _update_index(run: Run):
    idx = run.dir.parent.parent / "INDEX.csv"      # runs/INDEX.csv
    exists = idx.exists()
    row = {k: run.manifest.get(k) for k in _INDEX_FIELDS}
    # rewrite-in-place: replace an existing row for this run_id, else append
    rows = []
    if exists:
        with open(idx) as f:
            rows = [r for r in csv.DictReader(f) if r["run_id"] != run.run_id]
    rows.append({k: str(row[k]) for k in _INDEX_FIELDS})
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=_INDEX_FIELDS)
    w.writeheader()
    w.writerows(rows)
    _robust_write(idx, buf.getvalue())
