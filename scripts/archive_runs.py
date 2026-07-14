#!/usr/bin/env python3
r"""
archive_runs : move COMPLETED run directories off the local drive to OneDrive.

Live runs write to the local runs root (fast, no sync collisions). When a sweep is
finished, run this to move completed runs to the OneDrive archive, freeing local
space. Design is deliberately minimal -- no resolver, no breadcrumbs, no hidden
indirection. The single invariant is: the pipeline only ever looks in the LOCAL
runs root; anything not there lives in the archive and you copy it back by hand
when (rarely) you need to re-analyze it.

The one safety feature: this is a MOVE, but it copies + verifies every file
(size and SHA-256) at the destination BEFORE deleting the local original. If any
file fails verification, that run is left untouched locally and its partial archive
copy is removed. This matters specifically because the archive is a cloud folder --
you never want a half-synced copy to replace a good local one.

Defaults:
  * archive target : the hardcoded OneDrive path below (override with --archive-root)
  * scope          : every COMPLETED run, PROMPTING y/n per run
  * runs skipped   : any whose manifest status != "complete" (with a printed reason)

Usage (Windows cmd, from the project root with the venv active):
  python scripts\archive_runs.py                 # prompt per completed run
  python scripts\archive_runs.py --dry-run       # show what would move, do nothing
  python scripts\archive_runs.py --yes           # archive all completed, no prompts
  python scripts\archive_runs.py --run <run_id>  # just this one run
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

# Hardcoded default archive location (per project decision). Override with --archive-root.
DEFAULT_ARCHIVE_ROOT = r"C:\Users\Peter Mikulecky\OneDrive\PJM XFERs\Coursework\ASU_CSS_MS\Project\double-descent"

_PATH_WARN_CHARS = 240   # OneDrive path is long; warn before MAX_PATH (260)


def local_runs_root() -> Path:
    """Where live runs are written: DDESCENT_RUNS_ROOT, else ./runs."""
    return Path(os.environ.get("DDESCENT_RUNS_ROOT") or "runs").resolve()


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def find_completed_runs(runs_root: Path):
    """Yield (run_dir, manifest) for every run whose manifest status == 'complete'."""
    if not runs_root.exists():
        return
    for manifest_path in sorted(runs_root.glob("*/*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            continue
        if manifest.get("status") == "complete":       # only completed runs are movable
            yield manifest_path.parent, manifest


def _dir_size_mb(d: Path) -> float:
    total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def verified_move(run_dir: Path, runs_root: Path, archive_root: Path,
                  dry_run: bool = False) -> bool:
    """Copy run_dir to the archive, verify every file, then delete the local original.

    Returns True if the run was moved (or would be, under dry_run).
    """
    rel = run_dir.relative_to(runs_root)          # e.g. E1_fixed_n/<run_id>
    dest = archive_root / rel

    if len(str(dest)) + 40 > _PATH_WARN_CHARS:
        print(f"    ! archive path is long (~{len(str(dest))} chars); if the copy "
              f"fails, enable Windows long paths (LongPathsEnabled=1).")

    if dest.exists():
        print(f"    SKIP: already exists in archive -> {dest}")
        return False

    if dry_run:
        print(f"    would move -> {dest}")
        return True

    # 1) copy the tree
    try:
        shutil.copytree(run_dir, dest)
    except Exception as e:
        print(f"    ERROR during copy: {e}")
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        return False

    # 2) verify every file: exists, same size, same checksum
    ok = True
    for src_file in run_dir.rglob("*"):
        if not src_file.is_file():
            continue
        dst_file = dest / src_file.relative_to(run_dir)
        if not dst_file.exists() or dst_file.stat().st_size != src_file.stat().st_size:
            ok = False; break
        if _sha256(dst_file) != _sha256(src_file):
            ok = False; break

    if not ok:
        print(f"    VERIFY FAILED: {src_file.name} did not copy intact. "
              f"Leaving local copy in place and removing partial archive copy.")
        shutil.rmtree(dest, ignore_errors=True)
        return False

    # 3) all files verified -> safe to delete the local original
    shutil.rmtree(run_dir)
    print(f"    moved and verified -> {dest}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Move completed runs from local to OneDrive.")
    ap.add_argument("--archive-root", default=DEFAULT_ARCHIVE_ROOT)
    ap.add_argument("--runs-root", default=None,
                    help="local runs root; else $DDESCENT_RUNS_ROOT, else ./runs")
    ap.add_argument("--run", default=None, help="archive only this run_id")
    ap.add_argument("--yes", action="store_true", help="archive all completed, no prompts")
    ap.add_argument("--dry-run", action="store_true", help="show what would move; change nothing")
    args = ap.parse_args()

    runs_root = Path(args.runs_root).resolve() if args.runs_root else local_runs_root()
    archive_root = Path(args.archive_root)
    print(f"local runs root : {runs_root}")
    print(f"archive root    : {archive_root}")
    if not args.dry_run:
        archive_root.mkdir(parents=True, exist_ok=True)

    completed = [(d, m) for (d, m) in find_completed_runs(runs_root)]
    if args.run:
        completed = [(d, m) for (d, m) in completed if m.get("run_id") == args.run]

    # report runs that exist but are NOT complete, so nothing silently hides
    all_dirs = {p.parent for p in runs_root.glob("*/*/manifest.json")} if runs_root.exists() else set()
    complete_dirs = {d for d, _ in completed}
    for d in sorted(all_dirs - complete_dirs):
        try:
            st = json.loads((d / "manifest.json").read_text()).get("status")
        except Exception:
            st = "unreadable"
        print(f"skip (status={st}): {d.name}")

    if not completed:
        print("No completed runs to archive.")
        return

    moved = 0
    for run_dir, manifest in completed:
        size = _dir_size_mb(run_dir)
        print(f"\n{manifest.get('run_id', run_dir.name)}  ({size:.1f} MB)")
        if not (args.yes or args.dry_run):
            ans = input("    archive this run to OneDrive? [y/N] ").strip().lower()
            if ans not in ("y", "yes"):
                print("    left local.")
                continue
        if verified_move(run_dir, runs_root, archive_root, dry_run=args.dry_run):
            moved += 1

    verb = "would move" if args.dry_run else "moved"
    print(f"\nDone. {verb} {moved} run(s).")
    if not args.dry_run and moved:
        print("To re-analyze an archived run later, copy its folder from the archive "
              "back into the local runs root, work on it there, then delete the local copy.")


if __name__ == "__main__":
    main()
