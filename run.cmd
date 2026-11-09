@echo off
setlocal
cd /d "%~dp0"

if not defined FREEBCI_VENV (
  if exist ".venv310\Scripts\python.exe" (
    set "FREEBCI_VENV=.venv310"
  ) else (
    set "FREEBCI_VENV=.venv"
  )
)

if not exist "%FREEBCI_VENV%\Scripts\python.exe" (
  echo [run] %FREEBCI_VENV% not found - run setup_env.cmd first, or see README.md
  pause
  exit /b 1
)

set PYQTGRAPH_QT_LIB=PySide6
set QT_API=pyside6
"%FREEBCI_VENV%\Scripts\python.exe" "FreeBCI_GUI.py" %*
if errorlevel 1 (
  echo.
  echo [run] The application exited with an error. See the messages above.
  pause
)
