# Changelog

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
