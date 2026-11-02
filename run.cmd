@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [run] .venv not found - run setup_env.cmd first, or see README.md
  pause
  exit /b 1
)

set PYQTGRAPH_QT_LIB=PyQt5
".venv\Scripts\python.exe" "FreeBCI_GUI.py" %*
if errorlevel 1 (
  echo.
  echo [run] The application exited with an error. See the messages above.
  pause
)
