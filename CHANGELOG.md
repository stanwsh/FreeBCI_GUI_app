# Changelog

## 0.2.0rc1 - 2026-11-09 (prerelease)

- Migrate the presentation layer from PyQt5 to PySide6 6.8.3 / Qt 6 through
  `freebci/qt.py`; update signals, slots, QtGui actions, event loops, and the
  matplotlib Qt backend. PyQt5 and PySide6 are not mixed in one process.
- Support Python 3.10-3.12 with a new dependency lock; preserve the bundled
  FreeBCI native SDK, data formats, hardware commands, and display-filter defaults.
- Update setup, launch scripts, and CI for isolated environments and a Python
  3.10 / 3.12 test matrix. `run.cmd` accepts `FREEBCI_VENV` and detects `.venv310`.
- Fix combo-box callbacks that receive an extra signal index under PySide6.
- Fix the 16-channel electrode dialog's missing map/image lookup by using the
  existing larger map prefix; leave user settings files unchanged.
- Close console log handles even when messages are not strings.
- Add real Qt regression tests for eight layouts, dialogs, paint paths, custom
  signals, queued session startup, channel buttons, markers, and finalization.
- Validation: 123 tests pass on Python 3.10.22 and Python 3.12.16, including
  native SDK metadata and filtering. The user reported manual testing and
  authorized publication on November 9. The precise manual test matrix was not
  recorded; independent migrated-runtime Wi-Fi/USB/Bluetooth acceptance remains
  unverified. This is a prerelease; v0.1.12 remains the stable rollback release.
- Wi-Fi connection setup may require separate inbound firewall permission for
  a new Python executable. Setup and launch scripts do not change firewall rules.

## 0.1.12 - 2026-11-09

### Changed

- Default GUI notch filter to **60 Hz** and bandpass filter to **None**.
  These are display defaults; saved raw samples retain their existing format.
- Include developer tools and tests in the source release archive, alongside
  the bundled FreeBCI BrainFlow build and setup files.

### Added

- `tools/analyze_recording.py`: inspect numbered recording CSVs for constant
  runs, assumed ADS1299 rail values, manifest sample counts, missing files, and
  SHA-256 integrity. Supports JSON output and an explicit conversion-gain assumption.
- `tools/diagnose_wifi.py`: bounded, hardware-backed probe for FreeBCI Wi-Fi 16 I
  (board 2038), saving unfiltered SDK rows, block sizes, receive clocks,
  frame-counter diagnostics, SDK logs, and the normal recording output.
- Controlled internal-shorted-input capture after startup/reset, with default
  channel settings restored on exit. Probes use 250 Hz and SDK initialization;
  disconnect the GUI from the board before running them.
- Regression coverage for analysis, configuration ordering, probe cleanup, and
  SDK/recording agreement.
- A hardware investigation report and a staged Python 3.10 / PySide6 migration
  plan. The migration is planned, not implemented in this release.

### Findings and known limitations

- The supplied floating-input recording contains exact negative ADC-limit
  values. On the affected TP-Link adapter, all 16 channels continued updating
  during a 65-second internal-shorted-input capture with zero detected missing
  frames. Restoring floating inputs reproduced saturation. This does not
  establish compatibility with every adapter or replace a long hardware soak.
- Refiltering each display window can produce a repeated stationary transient
  for constant input. The Railed indicator currently uses filtered amplitude
  and may hide raw saturation. Neither behavior is fixed by this release.
- Manifest `lost_samples` counts recording-index gaps and cannot establish
  lossless Wi-Fi delivery. Frame-counter diagnostics are a separate heuristic.
- Runtime remains Windows x64, Python 3.9, and PyQt5 5.15.2. Python 3.10 and
  PySide6 compatibility have not been validated. See the migration plan for
  dependency, Qt API, native SDK, and hardware acceptance gates.

See [the investigation](docs/ACQUISITION_DEBUG_2026_11_09.md) for evidence and
reproduction commands.

## 0.1.11

- Add per-sample UTC timestamps to CSV/TXT recording rows while preserving
  fractional AUX values.
- Add reproducible `pyproject.toml` / `uv.lock` packaging for the existing
  Python 3.9 environment.

Earlier changes are tracked in Git history and `ARCHITECTURE_REVIEW.md`.
