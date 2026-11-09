# Python 3.10 and PySide6 migration plan

Status: **planned; not implemented in v0.1.12**. Current supported installation
remains Windows x64 with Python 3.9 and PyQt5 5.15.2. Target the Qt/runtime work
at the next minor release, tentatively v0.2.0, with hardware acceptance before
changing the default installation.

## Target and constraints

The requested first migration target is Python 3.10 x64 and PySide6 (Qt 6).
Python 3.10 reached end of life on October 1, 2026, according to the
[Python Developer's Guide](https://devguide.python.org/versions/) and
[PEP 619](https://peps.python.org/pep-0619/). Treat 3.10 as a compatibility
transition, not a long-term supported runtime; add a Python 3.12 validation
lane before selecting the next production default. The requested 3.10 path
remains part of this plan.

[Qt's installation guidance](https://doc.qt.io/qtforpython-6/gettingstarted.html)
currently specifies Python 3.10 or newer. Choose and pin a stable PySide6 build
with Windows x64 wheels for the actual Python target during the dependency
spike; do not assume the newest future PySide6 supports Python 3.10.

Preserve board protocols, hardware-setting command strings, channel/AUX units,
sample ordering, timestamps, manifests, control protocol, and LSL behavior.
Keep the bundled FreeBCI BrainFlow DLLs. Replacing them with upstream BrainFlow
is outside this migration: the custom board ids depend on this bundled build.
Do not combine the Qt port with new DSP algorithms or signal-quality features.

## 1. Establish the baseline and dependency matrix

- Preserve the v0.1.12 tag and source archive as the rollback release. Work in
  an isolated migration branch and environment; do not replace a user's `.venv`.
- Run the complete tests and an offscreen GUI smoke test on the baseline.
  Record demo throughput, memory, start/stop behavior, and representative plots.
- Create a separate Python 3.10 x64 environment. First validate the existing
  Qt-free core and bundled BrainFlow imports/DLL loading. Probe the SDK's
  NumPy/nptyping interfaces and retain `setuptools<81` while `pkg_resources`
  remains in the vendored SDK. Do not upgrade NumPy blindly across this boundary.
- Resolve exact compatible versions for PySide6, pyqtgraph, matplotlib, MNE,
  NumPy, SciPy, pandas, pylsl, nptyping, and pywin32. Test the resulting Windows
  wheels before committing the new lock. This plan does not promise that all
  existing pins work unchanged under Qt 6.
- Validate Python 3.12 in a separate lane and record any SDK blockers. Decide
  the production Python default from this evidence and the support lifecycle.

Exit gate: clean install and Qt-free tests succeed on the target matrix;
native SDK compatibility is observed rather than inferred from pure-Python imports.

## 2. Port the Qt binding and APIs

- Add one presentation Qt import boundary and select PySide6 explicitly.
  Convert direct PyQt5 imports throughout `freebci/ui`, `freebci/design`, and
  tests. Do not mix PyQt5 and PySide6 objects in one process; a permanent
  dual-binding compatibility layer is not a requirement.
- Convert `pyqtSignal`, `pyqtSlot`, and `pyqtProperty` to the PySide equivalents.
  Review signal overloads, callback arguments, and cross-thread delivery in
  connection, command, and session-start workers.
- Audit Qt 6 enum scopes, `exec_()` calls, moved classes such as `QAction` and
  `QShortcut`, screen geometry APIs, font metrics, and APIs removed in Qt 6.
  Audit float-to-integer widget sizes/positions and painter arguments that a
  different binding may reject.
- The repository contains Python UI definitions. Preserve layout behavior
  while porting them; if `.ui` sources are introduced, generate with
  `pyside6-uic` and document the generation command.
- Update QApplication creation, dialogs, clipboard, file pickers, shortcuts,
  window close, worker cancellation, object ownership, and deferred deletion.

Use the [Qt for Python porting guide](https://doc.qt.io/qtforpython-6/gettingstarted/porting_from2.html)
as a Qt 5-to-6 API checklist; it does not replace the additional PyQt-to-PySide
signal/import work in this application.

Exit gate: every window/dialog opens offscreen, the demo starts and stops,
all eight layouts render, and no mixed Qt binding is imported.

## 3. Integrate plotting, setup, and CI

- Set `PYQTGRAPH_QT_LIB=PySide6` before importing pyqtgraph. Update the existing
  `sitecustomize.py` setup with its backup behavior and audit `pyqtgraph.Qt`
  imports. A clean environment must contain only the selected Qt binding.
- Move matplotlib imports from `backend_qt5agg` to its Qt-binding-neutral
  `backend_qtagg`, and verify MNE/topography embedding against the pinned stack.
- Update `pyproject.toml`, `requirements.txt`, `uv.lock`, `setup_env.cmd`,
  `setup_env.py`, README commands, and runtime diagnostics together. Replace
  the hard-coded 3.9 environment creation with the validated target; do not
  merely widen `requires-python` without testing the resolver and native wheels.
- Add Windows target CI jobs for Python 3.10 and the supported-version lane.
  Run offscreen tests with PySide6 selected. Retain the baseline release for
  rollback rather than installing both bindings to keep old tests passing.
- Recheck DPI scaling, fonts, plot curves, menus, and mouse/keyboard interaction
  on actual Windows displays; offscreen tests cannot establish these behaviors.

Exit gate: clean `uv sync --frozen` / setup succeeds, all tests pass, and an
extracted source release launches using only its packaged files and locked dependencies.

## 4. Validate lifecycle and hardware

- Repeat demo/control API/markers/LSL tests, repeated start-stop-reconnect,
  recording rotation, writer failure, and shutdown. Compare sample counts,
  CSV/TXT numeric values, manifest fields, and control responses with baseline.
- Test Wi-Fi board 2038 at 250 Hz with normal and internal shorted inputs using
  `tools/diagnose_wifi.py`. Compare SDK rows, frame counters, receive gaps,
  recording agreement, and GUI responsiveness. Floating inputs alone are not
  a reproducible quality test.
- Reverify the USB board 2037/CH343 path when hardware is available. Test a
  multi-minute hardware run and a longer synthetic soak before release.
- Keep Bluetooth and untested channel/transport combinations explicitly
  unverified until hardware checks are completed. Qt migration does not expand
  the tested hardware matrix automatically.

Exit gate: the previously verified USB/Wi-Fi paths work under the new runtime,
workers stop cleanly, recordings finalize correctly, and no unresolved lifecycle
or hardware regression remains in the supported paths.

## 5. Release and rollback

Publish a prerelease built from the migration branch with the exact Python,
PySide6, Qt, scientific-stack, and bundled-SDK versions recorded. Complete
operator checks for all layouts and settings dialogs. Promote the new minor
release only after the gates above pass, documenting Python 3.10's transition
status and the selected supported Python version.

For rollback, extract v0.1.12 into a separate folder and recreate its Python 3.9
environment; do not downgrade packages in the migrated environment. User
recordings remain readable because this migration does not change their format.

Suggested commit sequence: dependency/SDK spike; Qt import and API port;
plotting and setup integration; CI/tests; hardware acceptance; release docs.
