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

if not defined FREEBCI_VENV set "FREEBCI_VENV=.venv"

if exist "%FREEBCI_VENV%\Scripts\python.exe" (
  echo [setup] %FREEBCI_VENV% already exists.
  echo [setup] To keep an older environment, set FREEBCI_VENV=.venv310 and run setup again.
  goto :failed
)

echo [setup] creating %FREEBCI_VENV% with CPython 3.10 ...
uv venv --python 3.10 "%FREEBCI_VENV%" || goto :failed

echo [setup] installing locked dependencies ...
set "UV_PROJECT_ENVIRONMENT=%FREEBCI_VENV%"
uv sync --frozen --python "%FREEBCI_VENV%\Scripts\python.exe" || goto :failed

echo [setup] finishing environment setup ...
"%FREEBCI_VENV%\Scripts\python.exe" setup_env.py || goto :failed

echo.
echo [setup] done. Start the GUI with:  run.cmd
pause
exit /b 0

:failed
echo.
echo [setup] Setup did not finish. Fix the issue above and run setup_env.cmd again.
pause
exit /b 1
