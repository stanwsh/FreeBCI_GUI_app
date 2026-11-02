@echo off
setlocal
cd /d "%~dp0"

rem Creates the local Python environment and installs dependencies.
rem Requires "uv" (https://docs.astral.sh/uv/). See README.md for a manual setup.

where uv >nul 2>nul
if errorlevel 1 (
  echo [setup] uv was not found on PATH.
  echo [setup] Install it from https://docs.astral.sh/uv/ or follow the manual steps in README.md.
  goto :failed
)

if exist ".venv\Scripts\python.exe" (
  echo [setup] .venv already exists - remove it first to rebuild from scratch.
  goto :failed
)

echo [setup] creating .venv with CPython 3.9 ...
uv venv --python 3.9 .venv || goto :failed

echo [setup] installing requirements.txt ...
uv pip install --python .venv\Scripts\python.exe -r requirements.txt || goto :failed

echo [setup] finishing environment setup ...
.venv\Scripts\python.exe setup_env.py || goto :failed

echo.
echo [setup] done. Start the GUI with:  run.cmd
pause
exit /b 0

:failed
echo.
echo [setup] Setup did not finish. Fix the issue above and run setup_env.cmd again.
pause
exit /b 1
