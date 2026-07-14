@echo off
REM One-time project setup. Run from the project root in the VS Code cmd terminal.
REM Creates a venv, installs the package editable, and makes the first git commit
REM (needed so 'reg' confirmatory runs can start on a clean tree).

echo === creating virtual environment ===
python -m venv .venv
call .venv\Scripts\activate.bat

echo === installing dependencies ===
python -m pip install --upgrade pip
pip install -e .

echo === initializing git (local repo; keep OUT of live OneDrive sync) ===
git init
git add -A
git commit -m "initial: reservoir double-descent pilot scaffold"

echo.
echo Setup complete.
echo   Activate later with:  .venv\Scripts\activate.bat
echo   Smoke test:           python scripts\run_T0_tune_operating_point.py --smoke
