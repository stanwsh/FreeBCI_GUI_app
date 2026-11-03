# FreeBCI GUI: Architecture Assessment and Reconstruction Plan

USER NOTES: 


- No BT hardware was available for testing, so the Bluetooth path is unverified. The GUI code is present and compiles, but the `bluetooth_connection.py` dialog has not been exercised.
- A real board broadcasting on wifi "FreeBCI-1018" can be used to verify the following, using "FreeBCI_WiFi_16_I" hardware settings preset [Wi-Fi Mode only if prompted]. GUI Connection step: Boards->FreeBCI-WiFi-I-16->Wi-Fi;Prompted IP selection window (preserve original, may need to wait for a few timeout if first connected)->select. The board server has a web interface at http://192.168.4.1/tcp http://192.168.4.1/wifi if connected to the board's AP. The board is a 16-channel Wi-Fi board with a TCP interface. [current mode of the board for wifi testing] You may prompt me to restart the device because some time it is buggy. [closed, turn on only if prompted]

- A real board "USB-Enhanced-SERIAL CH343" connected on COM3 can be used to verify the following, using "FreeBCI_WiFi_16_I_USB" hardware settings preset [USB Mode turned on]. GUI Connection step: Boards->FreeBCI-WiFi-I-16->USB;Prompted Serial Port selection window->select COM3->confirm; Main page: start data stream. The board is a 16-channel Wi-Fi board with a USB serial interface.:

**Status:** Implementation in progress. The Qt-free core, durable session recording, GUI acquisition integration, local control plane, fast port discovery, background serial/Wi-Fi/Bluetooth setup, three-stream LSL output, stalled-acquisition diagnostics, and the redesigned Wi-Fi connector are landed. Real FreeBCI_WiFi_16_I boards were verified on 2026-11-02 in both USB mode (id 2037, COM3, 16 channels, 2 Mbaud) and Wi-Fi mode (id 2038, 192.168.4.1, 16 channels): GUI sessions record CSV/TXT/meta/manifest and finalize with `status: completed`; control-plane stop returns the GUI to idle. The remaining hardware acceptance work is the full transport/channel matrix and long-duration soak, not a correctness gap in the verified paths. The findings below are the original assessment; several items (GUI-thread acquisition/recording, unbounded auxiliary buffers, plot-thread and topography leaks, initial startup state, channel metadata rebuild, blocking connections) are already addressed in the implementation commits.
**Scope:** `freebci/` (51 Python modules), `FreeBCI_GUI.py`, `settings/`, and the Windows/PyQt5 runtime.
**Goal:** Improve maintainability, acquisition reliability, recording integrity, synchronization, and operator usability without discarding the validated BrainFlow/board behavior.
**Current goal (revised):** Preserve the verified USB/Wi-Fi 16-channel paths; finish the remaining observability, logging, packaging, and workflow gaps that are actionable without unavailable hardware; treat the full D/E target and the hardware matrix as future work, not prerequisites for closing the current implementation phase.

### Phase tracker

| Phase | State | Current milestone |
|---|---|---|
| 0 — Baseline/packaging | Accepted | Source release zip is the supported distribution; no wheel package planned. |
| 1 — Recording integrity | Code complete | Endurance gate merged into Phase 6. |
| 2 — Device/acquisition decoupling | Complete | 2.1 DeviceManager, 2.2 async settings, and 2.3 async command/start execution landed; only non-blocking board metadata queries remain on the GUI thread. |
| 3 — Bounded buffers/performance | Complete* | 3.1-3.3 landed and LSL pending counts are in diagnostics; the full 8-hour/64-channel GUI gate is endurance-gated. |
| 4 — Timestamps/control/sync | Complete* | 4.1 clock-offset exchange, selector-based `start`, and manifest clock section landed; real-board control verification remains hardware-gated. |
| 5 — GUI state/workflow | Complete* | 5.1-5.5 landed: action guards, stop confirmation, view-model history, immutable display snapshot, and trigger/battery snapshot rendering. Operator usability testing is external. |
| 6 — Validation/hardware matrix | Partial | USB 16-channel re-verified on COM3 and release/reconnect lifecycle covered by tests. Bluetooth, USB high-speed, 8/24/32/64-channel boards, and multi-hour soak remain hardware/time-gated. |

**Document realignment:** Sections A–I mix the original assessment (written before the reconstruction) with the proposed target architecture. Section D is a **target**, not a description of the current code. The authoritative current status is this phase tracker plus Section M; Appendix A is a planning map, not a file inventory. `freebci/core/catalog.py`, `freebci/core/ring.py`, `freebci/core/settings.py`, `freebci/core/logging.py`, `freebci/ui/`, and `freebci/app.py` now exist; the presentation package was renamed from `freebci/api/my_*`/`w_*` modules to `freebci/ui/*` and `freebci/ui/views/*`. The implemented adapter is `freebci/api/session_view_model.py`, and the bounded display history is ring-backed there rather than in the acquisition fan-out. See Section M for the section-by-section gap register.

### Implementation progress

- `d994181` — Qt-free core: models, gateway, acquisition worker, session lifecycle, bounded queues, durable recording, manifest, simulated-board tests.
- `9dfadc4` — GUI acquisition runs through `SessionController`; recording no longer runs on the Qt timer; channel metadata and topography buffers are rebuilt per board; plots stop with the session.
- `a2e4124` — failed session starts stop GUI timers.
- `1fb67d8` — token-protected loopback control plane with status/snapshot/stop and tests.
- `2d963f5` — roadmap progress recorded in this document.
- `5001e8e` — serial ports discovered with `list_ports` instead of probing COM1..COM256.
- `ab2accc` — sample-index gaps and lost-sample counts recorded in the manifest.
- `6a74592` — manifest checkpointed as `recording` every five seconds, then finalized.
- `5ad184c` — control-plane stop queued onto the GUI thread and reconciled with the button state.
- `9ec1197` — serial board preparation, including the FreeBCI type/baud handshake, moved off the GUI thread.
- `b60ce40` — Wi-Fi discovery and board preparation moved into workers; device buttons now select the correct IP.
- `a001243` — Bluetooth preparation moved into a worker; editable baud rate is honored.
- `3169531` — three independent Time Series LSL streams; unimplemented FFT/Band Power choices removed; Wi-Fi setup retries first-connection timeouts.
- `6a326d2` — Wi-Fi 16-channel mode selected after `start_stream()`; real Wi-Fi session verified end to end.
- `364ce73`, `375b126`, `76c260c` — Wi-Fi connector redesigned around board discovery, Wi-Fi status, and a detected-board list; README screenshot added.
- `ab02570` — stalled-acquisition and lost-sample status; `6a1ebcb` — tested-hardware matrix and control diagnostics.
- Session markers: Ctrl+M / File > Add Marker, `markers.jsonl`, manifest markers, control `marker` command, and `control.json` discovery file.
- Session diagnostics: Ctrl+D / File > Session Diagnostics..., live state, rate, integrity, writer queue, markers, LSL, and control endpoint.
- `71f4b16` — session markers, control discovery file, and the live session diagnostics window.
- `38a2665` — File > Start Demo Session runs the normal GUI pipeline against a synthetic 16-channel board for hardware-free checks.
- Packet-loss accounting now treats repeated counter values in a 16-channel frame as one frame and treats a jump larger than half the counter range as a firmware restart rather than hundreds of false losses (`a5c165b`); a real Wi-Fi session now reports `0.0%` with `lost samples: 0`.
- `fcedc06` — acquisition failures finalize as `partial` instead of `failed`, with fault-injection tests.
- Recording fault tests now cover a board disappearing mid-session, a board that fails to start, and a disk-full error during the final flush; all still write a final manifest with `status: failed`.
- A 100-cycle lifecycle test verifies repeated session start/stop, worker shutdown, and finalized manifests without leaked acquisition threads.
- Simulator pacing now generates samples from elapsed time and advances the packet counter per block; `tools/benchmark_session.py` exercises the full synthetic acquisition/recording path.
- `.github/workflows/tests.yml` runs the dependency install and full test suite on Windows/Python 3.9 for pushes and pull requests.
- Control API now supports `shutdown` in addition to `ping`, `status`, `marker`, and `stop`; the GUI queues shutdown onto its own thread and releases the board.
- `tools/soak_session.py` runs a longer synthetic session and reports throughput, loss, queue depth, and working-set memory; a short run holds `lost=0`, `dropped=0`, `queue=0`, ~34 MB RSS.
- LSL sources now publish stable `FreeBCI:<name>` source ids, and starting LSL creates a `FreeBCI_Markers` string stream fed by GUI and control-plane markers.
- The diagnostics dialog now has an automated offscreen test covering rendering and the copyable summary.
- Real Wi-Fi hardware LSL verification: a `FreeBCI_RealTest` stream (16 channels) delivered samples with timestamps, and `marker_click()` delivered `['manual']` on `FreeBCI_Markers`.
- Control `status` now exposes the host wall time of the latest block and the estimated wall time of its first sample, explicitly documented as host-clock estimates rather than hardware timestamps.
- Diagnostics presentation moved into `freebci/core/diagnostics.py`, so the window only supplies an endpoint/LSL summary and the formatting is testable without Qt.
- Real Wi-Fi control verification: `status` reported positive host timing for the latest block, `marker` succeeded, and `shutdown` closed the GUI and removed `control.json`.
- `tools/build_release.py` creates a self-contained source release zip (application, bundled BrainFlow, settings, docs, setup scripts) with a SHA-256 sidecar; the archive was built, extracted, and smoke-tested from the extracted copy.
- The control endpoint now has an application lifetime: one stable address/token and `control.json` while idle or recording, controller lookup through a provider, and a `start` command that queues the synthetic demo session onto the GUI thread (`start_requested`), then reports `recording` through `status`. Re-verified on the real Wi-Fi board: status, marker, and shutdown still work through the persistent endpoint.
- A first presentation view model (`freebci/api/session_view_model.py`) now owns the diagnostics and marker lookups, so the window no longer reaches into the controller/writer for those surfaces. State-driven enable/disable and the command queue are still open.
- A five-minute synthetic soak (16 channels, 250 Hz) completed 73,624 samples at 244.3 Hz effective, with `lost=0`, `dropped=0`, queue 0, and ~34.4 MB working set; this is a stability check, not the multi-hour soak gate.
- **Phase 2.1:** `freebci/core/device.py` adds `DeviceManager` with explicit `READY`/`STREAMING`/`DISCONNECTED` states, single-owner adoption, replacement-release, and gateway creation. The GUI adopts prepared boards, obtains its gateway from the manager, and releases through it; start/stop no longer sleep on the GUI thread.
- **Phase 2.2:** hardware-settings sends run in `SettingsCommandWorker`; progress is per command, a rejected command stops the sequence with a visible error, the dialog stays responsive, and a read-only settings directory no longer turns a successful board update into an exception.
- **Phase 2.3:** `BoardOperationWorker` serializes impedance, channel-enable, timing, and data-mode commands; `SessionStartWorker` starts the session stream off the GUI thread. The Start button is disabled while starting, failure restores it, and close waits for an in-flight start.
- **Phase 3.1/3.2:** trigger and battery views now share the bounded `self.data` history instead of duplicating two 60,000-sample buffers; the unused topography buffer and periodic `gc.collect()` were removed; time-series traces are decimated to about 2,000 points for rendering while filtering and RMS statistics still use the full-rate block.
- **Phase 3.3:** `freebci/core/history.py` appends a block with one allocation and trims to the newest 60,000 samples. A 2-minute synthetic 64-channel soak completed 29,504 samples at 244.4 Hz with `lost=0`, `dropped=0`, queue 0, and ~34.4 MB working set; the full 8-hour/64-channel GUI gate remains.
- **Phase 3.4:** diagnostics now include the pending sample count for each configured LSL stream.
- **Phase 6.1:** real USB 16-channel hardware re-check on COM3 (board 2037, 2 Mbaud) completed a 10-second session with 2,494 samples, status `completed`, and no lost samples. Display dropped 2,024 samples because this check used the core without a GUI drain loop; that is queue pressure, not transport loss. Full matrix and multi-hour soak remain open.
- **Phase 6.2:** an automated release/reconnect test covers stopping a session, releasing the board, adopting a second simulated board, and completing a fresh session with a finalized manifest.
- **Phase 4.1:** the control protocol added a four-timestamp `time` exchange and `ControlClient.clock_offset()` reports offset plus half-RTT uncertainty. `start` now requires a board selector (`"demo"`, board id, or catalog name); a real selector must match the connected board. `manifest.json` carries a `clock` section with the host timebase and start/stop wall times. README documents the selector and clock semantics.
- **Phase 5.1:** a single `_sync_action_states()` derives menu/action enablement from the current view-model state: Add Marker only while armed/recording, Demo only while idle, Boards only while idle, Disconnect only while a board is connected, and Hardware settings/electrode settings only while stopped.
- **Phase 5.2:** stopping a session with acquired samples, or disconnecting while it is recording, asks for confirmation before finalizing; control-plane stop and window close remain unconfirmed so scripts and shutdown are not blocked.
- **Phase 5.3:** the bounded display history now lives in `SessionViewModel`; `MainWindow.data` is a property over that history, and acquisition appends through `append_block()`. Time-series, FFT, band-power, trigger, battery, and topography consumers still read the shared property, so the remaining work is rendering every view directly from an explicit snapshot model.
- **Phase 5.4:** `SessionViewModel.display_snapshot()` returns an immutable `DisplaySnapshot` (history, state, channel count, sampling rate, sample count). `processor_fun` and `shower_fun` now render from that snapshot instead of reading `self.data` directly.
- **Phase 5.5:** trigger and battery indicators read the same snapshot; the duplicate trigger/battery buffers are gone. Trigger processing tracks a logical sample offset so it handles the bounded history trimming without reprocessing or dropping samples.
- **Phase 3.6 (D.2/E.6):** added `freebci/core/ring.py` with a thread-safe fixed-capacity ring and wrap-safe `latest()`. The session view model now stores its bounded history in the ring.
- **Phase 2.4 (D.2/E.2):** added `freebci/core/catalog.py` as the board-table source; `ConnectionInfo.id_list` is now a legacy-shaped copy of the catalog.
- **Phase 2.5 (D.3/E.11):** added `freebci/core/settings.py`; channel XML load/save is validated and atomically replaced. The hardware-settings dialog uses the typed model and no longer hand-builds XML.
- **Phase 2.6 (D.5/E.7):** added `freebci/core/logging.py`; each recording writes JSON-lines `session.log` with start/close/marker/gap/error events and size rotation.
- **Phase 2.7 (E.7):** recordings now create a `.writing` marker and remove it on finalize. `recover_sessions()` reports unfinished sessions without modifying them, and the main window shows the count at startup.
- **Phase 2.8 (H.2):** the manifest gained the `freebci.session/1` schema string, app version, device/config blocks, start/stop blocks, chunk list, sample count, and stop reason. `freebci/version.py` is now the shared app version and the release tool defaults to it.
- **Phase 2.9 (D.6/F.2):** added `freebci/core/lsl_queue.py` with a bounded per-stream queue and drop counter; LSL sends chunks instead of one sample per call, and diagnostics reports pending/dropped per stream.
- **Phase 2.10 (F.1):** the time-series view now creates one `PlotDataItem` per active channel and updates it with `setData()`; the per-frame `clear()`/`plot()` recreation is gone. Offscreen demo created 16 stable curves.
- **Phase 2.11 (D.4):** added `freebci/core/dsp.py`; the main window uses core FFT/notch/band-pass wrappers and no longer imports BrainFlow. `ConnectionInfo` no longer creates a placeholder `BoardShim`; transport dialogs supply the prepared board.
- **Phase 5.6:** diagnostics now show device id/name, configured rate, written samples, and disk free. Closing the window while recording asks to stop and finalize.
- **Phase 2.12 (G.5):** control requests now carry client-generated ids that are echoed on success and error responses; failures expose stable `busy` and `no_session` codes, and a pending start rejects a duplicate request.
- **Phase 2.13 (I.4):** the writer snapshot reports last-write duration/age and the manifest status, and both appear in Session Diagnostics.
- **Phase 2.14 (D.4):** `prepare_serial_board`/`prepare_wifi_board` in `core/gateway.py` own BrainFlow transport preparation; the serial and Wi-Fi workers no longer import BrainFlow. The old synchronous serial dialog is now a compatibility alias.
- **Phase 2.15 (D.2):** `freebci/app.py` is the Qt composition root; `FreeBCI_GUI.py` only prepares the data directory and delegates.
- **Phase 4.3 (G.6):** `ControlClient.from_runtime_file()` and `wait_started()` cover the documented runtime-file and start-wait flow.
- **Phase 4.4 (G.5):** discovery publishes `schema: freebci.control/1`, host, pid, and creation time alongside the endpoint/token.
- **Phase 4.5 (G.8):** `status` now includes `clock_id`, `monotonic_ns`, and `wall_ns` for the server clock.
- **Phase 5.7 (C.4/I.1):** `core/actions.py` is a pure state-to-action table; the window derives marker/demo/board/release/settings enablement from it.
- **Phase 2.17 (D.4):** `core/gateway.py` is now the only BrainFlow importer; `core/dsp.py` delegates FFT/filter/power calls to it, and the virtual-connection dialog also uses the gateway preparation helpers.

- **Phase 2.18 (D.1–D.3):** the presentation layer moved from `freebci/api/my_*` and `w_*` modules to `freebci/ui/*` and `freebci/ui/views/*`; classes lost the `My` prefix (`MainWindow`, `DiagnosticsDialog`, `TimeSeriesView`, `NetworkView`, and peers), workers moved under `freebci/ui/workers/`, and the generated window/interface imports were updated. The GUI was imported and instantiated offscreen, and the full suite remained 97/97.

Still intentionally open from the roadmap: the full hardware acceptance matrix (Bluetooth, USB high-speed, 8/24/32/64-channel boards), a multi-hour soak run, and the full snapshot-driven rendering refactor.

---

## A. Executive Summary

FreeBCI GUI is a working Windows desktop application, not a prototype. It already connects to a broad family of USB, Bluetooth, and Wi-Fi boards, records multichannel data, renders time-series/FFT/band-power/topography views, and publishes LSL streams. The correct strategy is an **incremental reconstruction around the existing UI and BrainFlow integration**, not a rewrite.

The central architectural defect is that **one GUI thread owns the device, the acquisition loop, filtering, plotting, LSL, and disk writing**. `MainWindow` is a 1,220-line god object; it calls `BoardShim.get_board_data()` from a 50 ms Qt timer, filters every channel, redraws up to 64 plots, and writes CSV files in the same event loop. As a result, a slow disk, a slow plot, a COM-port scan, or a device configuration command freezes the operator interface and can lose samples.

The most serious verified problems are:

1. **Acquisition, processing, and recording run on the GUI thread.** `startButton_click`, `poll_data`, `shower_fun`, `processor_fun`, and `recorder_fun` all execute in the Qt main thread (`freebci/ui/main_window.py:700-752`, `805-1105`, `1144-1201`).
2. **Unbounded auxiliary buffers and leaked objects.** `extri_data`, `topo_data`, and `battery_percentage` are appended on every poll and are only reset when a particular view/mode happens to be active (`main_window.py:1150-1152`). `topo_data` is never read. A new `TopographyCanvas` is added to the topography layout on every update (`freebci/ui/views/topography.py:153-166`). A new `PlotThread` is created on every Start and never stopped (`main_window.py:1209-1219`).
3. **Recording is not a first-class, durable subsystem.** Recording is driven by a GUI timer, starts only after a 60,000-sample buffer threshold, rotates files by call count, has no manifest, no sample index, no gap record, no checksum, and swallows failures. `stop_openbci()` discards the final `get_board_data()` result (`main_window.py:1121-1135`).
4. **Device lifecycle is ad hoc and duplicated.** Five connection dialogs each contain a near-identical `prepare_openbci()`; COM scanning opens 256 ports in a dialog constructor; UPnP discovery runs without timeout; there is no explicit connection state machine, cancellation, disconnect detection, or single-owner rule (`serial_connection.py:29-46`, `wifi_connection.py:36-53`).
5. **There is no timestamp or external-coordination model.** The application stores no sample index or per-block time. Packet-counter deltas are converted to a percentage. The board timing button sends a local wall-clock string (`main_window.py:622-634`). The application does not supply explicit LSL timestamps, and 2 of 3 configured LSL streams are nonfunctional (`main_window.py:770-776`, `1175-1182`).
6. **State is fragmented and initially wrong.** `MainWindowInterface` sets `isSessionOn = True` before any connection (`freebci/design/main_window_interface.py:49`); `MainWindow` defaults to 16 UI channels while `ConnectionInfo` defaults to a 32-channel board (`main_window.py:63,66`); the startup probe showed `mne_nchan=31`, `ts_widgets=16`, `topo_chan=16`, `connect_chan=32`. Start Session can be pressed with `self.board = None`.

The recommended target is a small **Qt-free acquisition core** with explicit boundaries:

```
BoardGateway (BrainFlow adapter)
        ↓
DeviceManager / SessionController (state machine)
        ↓
AcquisitionService (one worker thread, sample-indexed blocks)
        ├── bounded writer queue → RecordingWriter (disk, manifest, checksums)
        ├── display ring buffer → GUI snapshots (lossy display allowed)
        ├── processing worker → FFT/band power/topography
        └── LSL sender → LSL outlets (timestamps, source_id)
```

The GUI becomes a subscriber to immutable snapshots and sends commands through a controller. It never imports BrainFlow or touches a device handle.

**Recommended sequence:** Phase 0 baseline and packaging fix; Phase 1 recording integrity and session manifest; Phase 2 remove device/acquisition work from the GUI thread; Phase 3 bounded buffering and performance; Phase 4 timestamps, control IPC, and markers; Phase 5 state-driven GUI and workflow; Phase 6 hardware validation and documentation. Estimated effort for one experienced engineer is 12–15 weeks, with usable intermediate releases after Phases 1 and 2.

**What not to do:** do not rewrite in another framework, do not introduce microservices, do not add ZeroMQ/gRPC/shared memory before measuring a need, and do not change the recording column format without a versioned migration path. The current CSV/TXT format has downstream value; preserve it and add sidecar metadata.

---

## B. Existing Architecture Assessment

### B.1 Runtime and stack

| Item | Current state |
|---|---|
| OS | Windows 10/11 x64; serial/Bluetooth paths are Windows-specific (`sys.platform.startswith('win')`) |
| Python | 3.9 x64 (README and setup scripts) |
| GUI | PyQt5 5.15.2, pyqtgraph 0.13.3, matplotlib 3.7.2 |
| Device SDK | BrainFlow 4.x (`BoardShim`, `DataFilter`) |
| Signals | MNE 1.6.0 for montage/topography; pylsl 1.16.1 |
| Storage | NumPy/pandas/csv; CSV + TXT per session |
| Packaging | `requirements.txt`, `setup_env.cmd`, `run.cmd`; no `pyproject.toml`, no CI, no tests |
| Entry | `FreeBCI_GUI.py` sets `FREEBCI_HOME`, creates `QApplication`, then `MainWindow.instance()` |

`requirements.txt` currently **does not list `brainflow`**, although every transport path imports it; it does list the unused `nptyping`. A clean `setup_env.cmd` install therefore reports `brainflow MISSING` in `setup_env.py`, and the GUI cannot start. This is a publishing blocker independent of architecture.

### B.2 Module responsibilities

| Area | Modules | Current responsibility |
|---|---|---|
| Entry/composition | `FreeBCI_GUI.py` | Set data root, create QApplication, create singleton main window |
| Main window | `freebci/ui/main_window.py` | Device dialogs, board ownership, hardware commands, timers, acquisition, filters, FFT, plots, LSL, recording, topography, state |
| Window shell | `freebci/design/main_window_interface.py` | Generated UI, layout switching, logging setup, recording directory, view flags |
| Generated UI | `freebci/design/main_window_ui.py` | Widget construction |
| Views | `time_series.py`, `fft_plot.py`, `band_power.py`, `topography.py`, `external_trigger.py`, `accelerometer.py`, `battery.py`, `networking.py` | UI construction plus behavior-specific rendering/LSL configuration |
| Connection dialogs | `wifi_connection.py`, `bluetooth_connection.py`, `serial_connection.py`, `serial_connection.py`, `virtual_connection.py` | Discover/connect and create a BrainFlow `BoardShim`; emit `ConnectionInfo` |
| Board metadata | `connection_info.py` | Hardcoded 28-entry `id_list` (ids 2023–2051); live `BoardShim`; defaults |
| Hardware settings | `hardware_settings.py`, `hardware_settings_protocol.py` | XML-backed per-channel configuration and command strings |
| Channel mapping | `channel_settings.py`, `electrodes_position.py` | Electrode names/positions and XML settings |
| Recording | `recording_paths.py` | Session directory, TXT header, CSV rows, rotation |
| Logging | `console_logger.py`, `console_window.py` | Per-message file append; console dialog |
| Layout | `layout_dialog.py` | Eight preset arrangements |
| Settings data | `settings/*.xml` | 17 presets; no schema/version beyond an XML attribute |

### B.3 End-to-end flows

**Connect flow**

```
Board menu action
  → MainWindow.wifi_click/com_click_pure/bluetooth_click/virtual_click
  → dialog constructor (COM scan / UPnP discovery)
  → dialog.prepare_openbci() → BoardShim.prepare_session()
  → board.config_board(...) (sample rate/type/baud)
  → dialog emits ConnectionInfo
  → MainWindow.initLayout()
  → _chan/channel arrays/buffers
  → initWidget(); changeLayout(2); refreshBoardMenu()
```

The dialog owns the device until it hands a live `BoardShim` to the window. There is no central connection state and no cancellation.

**Acquisition flow**

```
QTimer(50 ms) updater → poll_data()
  → BoardShim.get_board_data_count()
  → BoardShim.get_board_data()
  → append to self.data + extri_data + topo_data + battery_percentage
  → trim self.data at 60k; set record_data / isRecorded
  → packet-counter loss calculation
  → optional LSL buffer fill

QTimer(50 ms) processor → filter all channels, FFT, band power
QTimer(50 ms) shower → filter all channels, redraw plots, trigger/battery/topography
QTimer(500 ms) recorder → np.savetxt/CSV when isRecorded is False
QTimer(10 ms × 3) LSL → sendLSLStream() (only stream 1)
PlotThread → data_queue.get() → Topo_plot() → new TopographyCanvas
```

Everything above is on the GUI thread except `PlotThread`, whose only job is to dequeue already-rendered topography arrays; the actual `mne.viz.plot_topomap` call happens back on the GUI thread via the signal.

**Recording flow**

```
start_openbci() sets self.isRecorded = True
poll_data() only after self.data > 60,000:
    self.record_data = self.data[:, :10000]
    self.data = delete(first 10000)
    self.isRecorded = False
recorder_fun() (500 ms):
    if not isRecorded: isRecorded = True; RecordingPaths.record_data(self.record_data)
stop_openbci():
    get_board_data() result discarded
    record_data(self.data)
    stop_record()
```

The effective recording latency is up to 60,000 samples, not 500 ms, because the recorder is gated by the buffer threshold. On a clean stop, the remaining `self.data` is written; on a crash, whatever is not yet flushed is lost.

**LSL flow**

`networking.py` creates up to three `StreamOutlet` objects based on UI selections. `startLSLButton_click` starts three 10 ms timers, all connected to `sendLSLStream`; that method only reads `LSLbufferData1` and pushes it to `LSLoutlet1`. Streams 2 and 3 and the FFT/Band Power data-type choices are dead paths.

### B.4 Current architecture diagram

```
┌──────────────────────────────────────────────────────────────┐
│ Qt main thread                                               │
│  MainWindowInterface ── MainWindowUi                         │
│        │                                                     │
│        └── MainWindow (1,220 lines)                        │
│              ├── connection dialogs ── BoardShim             │
│              ├── QTimers: poll/filter/plot/record/LSL        │
│              ├── RecordingPaths ── CSV/TXT                      │
│              ├── ConsoleLogger ── per-message file append         │
│              ├── views (time/FFT/band/topography/...)        │
│              └── PlotThread ── queue ── Topo_plot            │
└──────────────────────────────────────────────────────────────┘
        │ direct calls                    │ direct calls
        ▼                                 ▼
  BrainFlow BoardShim              filesystem / LSL
```

There is no domain layer between the window and the SDK. The GUI is the composition root, the device manager, the acquisition loop, the processor, and the recording controller simultaneously.

### B.5 Verified findings

The following are code-path findings, not speculative performance claims. “Confidence” means the code path is clear; runtime impact still needs measurement.

| # | Finding | Evidence | Impact | Confidence |
|---|---|---|---|---|
| 1 | Acquisition poll runs on the GUI thread | `main_window.py:715-729`, `1144-1201`; `updater()` at `791-798` | UI stalls, timer drift, board-buffer overflow under load | High |
| 2 | Filtering and plotting run on the GUI thread every 50 ms | `processor_fun` `805-892`; `shower_fun` `893-1105`; `gc.collect` at `1094`, `1198` | Frame drops, input lag, no isolation from disk/device | High |
| 3 | Recording writes on the GUI thread | `recorder_fun` `800-803`; `RecordingPaths.record_data` `24-66` | `np.savetxt` can freeze UI; stop/start latency | High |
| 4 | Auxiliary buffers are unbounded | `extri_data`/`topo_data`/`battery_percentage` appended at `1150-1152`; reset only in specific branches `974`, `983`, `1111-1113`, `1129-1131`; `topo_data` never read | Memory grows for the life of the session; eventual OOM | High |
| 5 | `np.append` copies the whole `self.data` on every 50 ms poll | `1193-1196`; `self.data` capped at 60k | Memory bandwidth and GC pressure; latency spikes | High |
| 6 | Recording is gated by 60k samples and call-count rotation | `poll_data` `1185-1191`; `recorder_fun` `800-803`; `recording_paths.py:60-66` | Up to 4 minutes of data pending; rotation not time/size based | High |
| 7 | Recording failures are silent | `recorder_fun` sets `isRecorded = True` before write; no try/except; `isRecorded` stays true after failure | Data loss reported as success | High |
| 8 | Final board buffer is discarded on stop | `stop_openbci` calls `get_board_data()` at `1124` and ignores result | Samples between last poll and stop are lost | High |
| 9 | `PlotThread` has no stop path | `1209-1219`; created at `721-723`; never joined/stopped in `stop_openbci`, `actionRelease_click`, `closeEvent` | Thread leak per Start; queue growth | High |
| 10 | Topography creates a new figure each update | `topography.py:153-166`; called from `Topo_plot` `754-755` | Widget/memory leak; increasing layout cost | High |
| 11 | 16-channel topography data is not assigned to `self` | `main_window.py:99-102` assigns local `Topography_data`; `shower_fun` uses `self.Topography_data` at `988-995` | 16ch topography raises `AttributeError`, caught as “Updater error”, stream stops | High |
| 12 | MNE info is built once and never rebuilt | `main_window.py:104-120`; `initLayout` `356-408`; `getHardwareInfo` `571-577` does not update it | Channel names/montage/sfreq wrong after connecting another board or changing rate | High |
| 13 | Startup state is inconsistent | `main_window_interface.py:49` `isSessionOn=True`; `MainWindow.__init__` `_chan=16`; `ConnectionInfo` defaults 32ch (`connection_info.py:397-411`); probe: 31/16/16/32 | Start Session before connect; wrong widgets; misleading UI | High |
| 14 | Start with no board is possible | `startButton_click` checks only `isSessionOn`; `start_openbci` calls `self.board.start_stream()` where `board=None` (`67`) | Generic “session error!”, no actionable message | High |
| 15 | COM scan blocks the dialog constructor | `serial_connection.py:19,29-46`; `bluetooth_connection.py:20,39-56`; 256 `serial.Serial` attempts | Dialog takes seconds; UI frozen; no cancel | High |
| 16 | Wi-Fi discovery has no timeout/cancel and button IP bug | `wifi_connection.py:36-53`; each button writes last `self.STA_ip_address` | Unbounded GUI freeze; clicking earlier device uses wrong IP | High |
| 17 | Device preparation/config is duplicated and blocking | five `prepare_openbci` copies; `serial_connection.py:58-74`; `hardware_settings.py:192-265`; `time.sleep` `214` | Divergent behavior; GUI freeze; no cancellation | High |
| 18 | Hardware settings Send has no try/finally | `hardware_settings.py:192-265`; disables Send at `196`, re-enables only at `254` | Any `config_board` error leaves dialog stuck | High |
| 19 | Settings Send/Apply overwrite preset files | `hardware_settings.py:262-265`; `channel_settings.py:151-154` | User presets silently replaced; no schema validation | High |
| 20 | LSL streams 2/3 and FFT/Band Power are nonfunctional | `main_window.py:666-695`, `770-776`, `1175-1182` | UI promises unavailable features | High |
| 21 | No sample timestamps/sample index in recordings | `recording_paths.py:24-66`; `poll_data` `1144-1201` | Cannot align with video/stimulus; gap analysis impossible | High |
| 22 | Logging is per-message open/append/close, no levels/locks | `console_logger.py:16-24` | Slow, racy, lossy diagnostics; no severity/context | High |
| 23 | Console singleton is broken and signals duplicate | `console_window.py:11-14`; `main_window_interface.py:100-104` | Multiple windows/appends; confusing logs | High |
| 24 | `MainWindow` state is many booleans | `isSessionOn`, `startButton_isclicked`, `isRecorded`, `is_startAccelerometer`, `is_startExtrigger`, `is_startBattery`, `is_fft_plot`, `is_time_series`, ... | Invalid combinations; unreachable/duplicated logic | High |
| 25 | God class / wildcard imports | `main_window.py` imports `from freebci import *`, `from PyQt5.QtWidgets import *`; 1,220 lines | Hard to test, review, or change safely | High |
| 26 | Packaging omits `brainflow`, includes unused `nptyping` | `requirements.txt:4-17`; `setup_env.py` checks brainflow | Fresh setup fails | High |
| 27 | No tests, simulator, CI, or package metadata | repository inventory | Regressions are discovered on hardware | High |
| 28 | Relative/CWD-dependent asset path | `channel_settings.py:74` uses `.\electrodes_pos_<n>.png` | Fails when launched outside repo root | Medium |
| 29 | Board catalog is hardcoded in source | `connection_info.py:3-393` | Adding a board requires code edit; easy to desync UI/capabilities | Medium |
| 30 | Board timing is wall-clock only | `main_window.py:622-634` | No timezone/monotonic/uncertainty; not usable for sync | High |

### B.6 Potential risks that require measurement

These are plausible but not yet proven by a benchmark:

- Sustained 64-channel throughput at 1–16 kHz; whether BrainFlow’s board buffer overflows before the 50 ms poll drains it.
- Actual `get_board_data()` copy cost and `DataFilter` cost per channel per frame.
- Disk throughput and `np.savetxt` latency at 64 channels; whether 500 ms recording is achievable.
- LSL `push_sample` blocking behavior and whether it can stall the GUI.
- Wi-Fi/Bluetooth packet arrival jitter and whether packet-counter loss matches sample loss.
- Whether a board exposes a usable hardware timestamp channel (`BoardShim.get_timestamp_channel`).
- Memory growth rate at 64 channels caused by auxiliary buffers and topography figures.
- Windows COM port enumeration time with many virtual ports.

### B.7 What should be preserved

- BrainFlow as the board SDK and the existing board-ID mapping (until migrated to data).
- The PyQt5/pyqtgraph look and the eight layout presets.
- The existing CSV/TXT column semantics and directory convention, for compatibility.
- The current LSL stream naming/type fields where they work.
- The per-channel hardware command vocabulary in `hardware_settings_protocol.py`.
- The choice of one process and one active device for the first release; multi-device is an extension, not a prerequisite.

---

## C. Architecture and Dependency Analysis

> Historical baseline from the initial assessment. Several concurrency and
> buffer findings have since been addressed; use Section M for current status.

### C.1 Dependency map

| From | To | Coupling | Assessment |
|---|---|---|---|
| `MainWindow` | `BoardShim` | Direct instantiation, `get_board_data`, `config_board`, `start/stop_stream` | Too strong; GUI is the device owner |
| `MainWindow` | dialogs | Constructs dialogs, receives mutable `ConnectionInfo` | Dialogs own transport and device lifetime |
| Dialogs | `BoardShim` | Each creates/prepares/releases | Duplicated lifecycle; no shared policy |
| `MainWindow` | `RecordingPaths` | Direct calls from timer | Recording cannot be tested or run off-thread |
| `MainWindow` | `ConsoleLogger` | Direct calls everywhere | Logging is UI widget, no levels |
| `MainWindow` | views | Direct widget mutation and data access | Views are not passive; logic is split |
| `MainWindowInterface` | `RecordingPaths`, `ConsoleLogger`, `LayoutDialog` | Creates all at startup | Window shell owns infrastructure |
| `topography` | MNE/matplotlib | Plot creation on every update | Rendering owns figure lifecycle |
| `hardware_settings` | `BoardShim` | `config_board` loop in dialog | UI blocks on hardware |
| `ConnectionInfo` | `BoardShim` | Stores a live board handle in a data object | State/data boundary is blurred |
| Views | generated UI | Each view builds its own widgets | Duplicated boilerplate; hard to theme/test |

### C.2 Cohesion and responsibility issues

1. **`MainWindow` has at least eight responsibilities:** connection orchestration, hardware command encoding, acquisition, filtering, FFT, plotting, LSL, recording, topography, and application state. This is the primary maintainability problem.
2. **Connection dialogs mix three concerns:** form validation, transport discovery, and BrainFlow session preparation. The same `prepare_openbci` code appears five times with small differences.
3. **Views are not views.** `networking.py` creates LSL outlets and owns protocol choices; `topography.py` owns MNE rendering and figure lifecycle; `time_series.py` owns channel-button state. They should receive data and emit user intent.
4. **`MainWindowInterface` is both shell and infrastructure factory.** It creates the logger, recording object, layout dictionary, and all views. This makes the window impossible to instantiate without touching the filesystem.
5. **`ConnectionInfo` is mutable shared state with a live device handle.** It is passed by reference to dialogs, the window, and settings dialogs; any of them can replace `board` or `channel_num`.

### C.3 Concurrency model

- **One thread:** the Qt GUI thread executes all timers, filters, plots, `BoardShim` calls, and disk writes.
- **One extra thread:** `PlotThread`, which only blocks on `Queue.get()` and emits a signal; it does not protect acquisition or rendering.
- **No synchronization:** there are no locks, queues, or ownership rules around `self.data`, `connect_info`, or the board handle. Today this is “safe” only because everything is on one thread; the moment acquisition moves to a worker, data races become real.
- **No backpressure:** `self.data` grows until the 60k trim; auxiliary buffers grow without bound; the topography queue is unbounded.
- **No shutdown protocol:** `closeEvent` stops the stream but not `PlotThread`; timers may still fire during teardown; exceptions are swallowed (`main_window.py:416-427`).

### C.4 State model

The application has no single state variable. It infers state from a combination of:

```
isSessionOn
startButton_isclicked
isRecorded
is_startAccelerometer / is_startExtrigger / is_startBattery
is_fft_plot / is_band_power / is_topography / is_external_trigger / ...
```

These flags are set in different methods and are not validated against each other. Examples:

- `isSessionOn=True` at startup, before a board exists.
- `startButton_isclicked=False` while the stream is starting; a second click can race the first.
- `isRecorded` is used both as “recording is armed” and “the current chunk has been handed to the writer”; the semantics change between methods.
- `is_startAccelerometer`, `is_startExtrigger`, and `is_startBattery` are three booleans that must be mutually exclusive but are not enforced by a type.

This is a textbook case for an explicit state machine with guarded transitions.

### C.5 Data ownership

- `self.data` is the display buffer, the recording buffer, the FFT source, and the topography source. Trimming it to 60k affects all consumers.
- `self.record_data` is a borrowed slice of `self.data` passed to a timer; it can be overwritten before the writer consumes it if timing changes.
- `self.topo_data` is appended but never read; it is pure waste.
- `self.extri_data` and `self.battery_percentage` are full board rows, not just the relevant channels; they duplicate data and grow without bound.
- `RecordingPaths` mutates the input array in place to convert AUX values to ints (`recording_paths.py:50-52`); a caller’s buffer is silently changed.

### C.6 Error handling and observability

- Broad `except Exception` blocks log a string and sometimes stop the stream; many swallow the exception entirely (`closeEvent`, `ConsoleLogger`, connection dialogs).
- `start_openbci` raises on failure, but `startButton_click` only resets the button text; it does not release the session or clean up.
- `recorder_fun` has no error path; a disk error is invisible.
- `ConsoleLogger.write` swallows all failures, including disk-full, so the application can lose its own diagnostics.
- There is no correlation ID, session ID, device ID, or severity; log lines are free text.
- There is no “recording completeness” report; a user cannot tell whether a file is complete.

### C.7 Testability and packaging

- No unit tests; no fake board; no dependency injection; hardware is required for nearly every path.
- Importing `main_window` constructs MNE objects and reads display settings (`win32api`), so even a headless test needs Windows display APIs.
- `requirements.txt` is incomplete (no `brainflow`) and contains an unused dependency.
- No `pyproject.toml`, no console entry point, no lockfile; setup is batch-script-specific.
- No CI, no lint/type checks; wildcard imports make static analysis noisy.
- The package is named `freebci`, but the top-level script and data directory assumptions are CWD-sensitive.

### C.8 What is already reasonable

- BrainFlow is the right SDK abstraction for this board family; replacing it would be high risk.
- The board catalog, although hardcoded, contains the capability data needed for validation.
- The CSV/TXT format is simple and usable by downstream scripts; it should be preserved.
- The eight-layout UI is a real usability feature; it should survive the refactor.
- LSL is the right data-plane choice for external consumers; the current implementation is incomplete, not conceptually wrong.

---

## D. Proposed Target Architecture

> **Target only.** This section describes the intended architecture, not the
> current package layout. Current code keeps the view-model adapter in
> `freebci/api/session_view_model.py`, has `core/catalog.py`, `core/ring.py`,
> `core/settings.py`, `core/logging.py`, and an `app.py` Qt bootstrap, and has
> no `freebci/ui/`. See Section M before treating any path or contract here as
> implemented.

### D.1 Principles

1. **One owner per resource.** The device handle is owned by `DeviceManager`; the acquisition thread owns reads; the writer thread owns files; the GUI owns widgets.
2. **The GUI is a subscriber, not a controller of hardware.** It sends commands to `SessionController` and renders immutable snapshots.
3. **Data integrity outranks display smoothness.** Display frames may be dropped or decimated; recorded samples must not be silently dropped.
4. **Explicit states, explicit transitions.** Invalid actions are prevented in the UI and rejected by the core.
5. **Timestamps are block-level and honest.** Do not claim per-sample hardware synchronization that the hardware does not provide.
6. **Preserve compatibility by default.** Keep CSV/TXT v1 and add sidecar metadata; introduce a new format only with an exporter.
7. **Minimal machinery.** Threads, queues, dataclasses, and a small TCP control server are sufficient; no framework, no microservices.
8. **Incremental seams.** Each phase must be independently testable and reversible; keep the old path behind a flag until the new path is validated.

### D.2 Target layers

```
┌─────────────────────────────────────────────────────────────┐
│ Presentation (Qt)                                           │
│  MainWindow, views, dialogs, SessionViewModel               │
│  - no BrainFlow imports                                     │
│  - no file writes except user-chosen exports                │
└──────────────────────────┬──────────────────────────────────┘
                           │ commands / snapshots
┌──────────────────────────▼──────────────────────────────────┐
│ Application services                                        │
│  SessionController, DeviceManager, ControlServer,           │
│  SessionViewModel adapter, LslService                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ Acquisition core (Qt-free)                                  │
│  AcquisitionService, RingBuffer, SampleBlock, SessionClock  │
│  RecordingWriter, Manifest, GapDetector, ProcessingWorker   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ Device abstraction                                          │
│  BoardGateway (Protocol)                                    │
│  BrainFlowBoardGateway, FakeBoardGateway                    │
│  BoardCatalog (data), DeviceConfig, capabilities            │
└─────────────────────────────────────────────────────────────┘
```

### D.3 Module responsibilities

| Module | Responsibility | Must not do |
|---|---|---|
| `freebci/core/models.py` | `BoardProfile`, `DeviceConfig`, `SessionState`, `SampleBlock`, `SessionStats`, `StopReason` | Import Qt, BrainFlow, or touch files |
| `freebci/core/catalog.py` | Load board profiles from data (initially a Python table; later JSON) | Instantiate a board |
| `freebci/core/gateway.py` | `BoardGateway` protocol and `BrainFlowBoardGateway` adapter | Render, record, or manage Qt |
| `freebci/core/device.py` | `DeviceManager`: connect/prepare/start/stop/release; state transitions; cancellation | Read sample blocks or write files |
| `freebci/core/clock.py` | `SessionClock`: monotonic/wall timestamps, sample-index math, uncertainty | Claim hardware sync |
| `freebci/core/acquisition.py` | `AcquisitionService`: worker loop, block assembly, fan-out, stats | Touch widgets or `BoardShim` directly |
| `freebci/core/ring.py` | Fixed-capacity ring buffer for display/processing | Block the producer indefinitely |
| `freebci/core/recording.py` | `RecordingWriter`: bounded queue, writer thread, rotation, manifest, checksums | Depend on Qt or the GUI buffer |
| `freebci/core/session.py` | `SessionController`: orchestrate device + acquisition + writer; expose status; markers | Render |
| `freebci/core/control.py` | Local TCP JSON-lines server/client; request IDs; status | Carry high-rate sample data |
| `freebci/core/logging.py` | Structured logging setup, queue listener, session/device context | Open a file per message |
| `freebci/core/settings.py` | Load/validate/save XML settings atomically; schema version | Auto-overwrite presets |
| `freebci/ui/viewmodel.py` | Qt `QObject` adapter: state/stats/errors as signals; snapshots | Import core internals beyond DTOs |
| `freebci/ui/main_window.py` | Thin window: connect actions, layout, views | Own a board or a timer pipeline |
| `freebci/ui/views/*` | Render arrays and emit user intent | Create LSL outlets or configure devices |
| `freebci/app.py` | Composition root: construct core, UI, control server; shutdown | Business logic |

The existing `freebci/design` generated UI files can remain. `main_window_ui.py` is a generated artifact; it should not be edited manually.

### D.4 Dependency rules

Allowed directions:

```
ui → application → core → gateway
ui → core.models (DTOs only)
application → core
core → gateway
gateway → brainflow
```

Forbidden:

- `core` importing `PyQt5`, `freebci.ui`, or `freebci.design`.
- `ui` importing `brainflow`, `BoardShim`, `DataFilter`, or `pylsl` directly.
- `gateway` importing `freebci.ui` or writing files.
- `recording` importing `SessionController` or reading GUI state.
- Views constructing device commands; they should call controller methods.

### D.5 Process and thread model

One process. No multiprocessing in the first reconstruction. Threads:

| Thread | Owns | Lifetime | Communication |
|---|---|---|---|
| Qt main | widgets, view model, plotting | app | queued signals; reads ring snapshots |
| Device worker | connect/prepare/configure/release | connect or settings operation | result/error callback; cancel event |
| Acquisition | `gateway.read()`, block timestamps, fan-out | streaming | ring buffer, writer queue, LSL queue, stats |
| Writer | files, manifest, checksums | session | bounded `queue.Queue` |
| LSL sender | outlets, push timing | streaming | bounded queue; loss stats |
| Control server | TCP requests | app | controller calls; status snapshot |
| Log listener | log file | app | `QueueHandler` |

GIL note: BrainFlow and NumPy release the GIL for native work, and the writer is I/O-bound. A single acquisition worker plus a writer thread is sufficient for one device at the current rates. Move filtering to a processing worker only if measurements show it is needed; do not add processes preemptively.

### D.6 Target data flow

```
Board → BrainFlowBoardGateway.read()
      → AcquisitionService.build_block()  [sample_index, t_mono, t_wall, packet counter]
      → fan-out
          ├─ writer_queue.put(block)  (bounded, blocking with timeout)
          ├─ ring.write(block)        (overwrite oldest; display may skip)
          ├─ lsl_queue.put(block)     (bounded; loss counted, never blocks acquisition)
          └─ stats.publish(block)
GUI timer (30–60 Hz) → ring.latest(window) → view models → plots
Processing worker (optional) → ring.latest(3 s) → FFT/band power → snapshot
```

### D.7 Seam for incremental migration

Do not rewrite `MainWindow` in one step. Introduce a `AcquisitionService` behind the existing `startButton_click`/`stop_openbci`:

1. Construct `BrainFlowBoardGateway` around the already-connected `BoardShim`.
2. Replace `poll_data` with `AcquisitionService.start()` and a display timer that reads `ring.latest()`.
3. Keep `shower_fun`/`processor_fun` for one phase, but feed them `ring.latest()` instead of `self.data`.
4. Replace `recorder_fun` with `RecordingWriter.submit()`.
5. Once the new path is stable, move connection dialogs to `DeviceManager` and delete the old `prepare_openbci` copies.
6. Finally, make `MainWindow` thin and move views to snapshot inputs.

This allows the old and new acquisition paths to coexist behind a settings flag during validation.

### D.8 Why this shape

- **Not a rewrite:** the board behavior, UI layouts, and file format are valuable and under-tested; a rewrite would discard working behavior.
- **Not microservices:** one operator, one machine, one device; IPC is for external coordination, not internal decomposition.
- **Not multiprocessing:** data rates are modest for NumPy/BrainFlow; process boundaries add serialization and lifecycle complexity without proven need.
- **Qt-free core:** enables pytest, fake gateways, and headless CI.
- **Explicit session:** recording, synchronization, and external control all need the same lifecycle; one controller avoids duplicating it.

---

## E. Module and Interface Specifications

The signatures below are proposed contracts, not implementation. They are deliberately small and typed.

### E.1 Core models (`freebci/core/models.py`)

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Mapping, Optional
import numpy as np


class SessionState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    READY = auto()
    STREAMING = auto()
    STOPPING = auto()
    ERROR = auto()


@dataclass(frozen=True)
class BoardProfile:
    board_id: int
    family: str                 # "USB", "BT", "WiFi"
    channels: int
    max_sampling_rate: int
    transport: str              # "serial", "bluetooth", "wifi", "usb"
    default_baud: int | None
    supports_accelerometer: bool
    supports_extrigger: bool
    supports_battery: bool
    eeg_rows: tuple[int, ...]   # BrainFlow row indexes
    aux_rows: tuple[int, ...]
    packet_counter_row: int | None


@dataclass(frozen=True)
class DeviceConfig:
    board_id: int
    transport: str
    serial_port: str | None = None
    wifi_address: str | None = None
    wifi_port: int | None = None
    baud: int | None = None
    timeout_s: float = 5.0


@dataclass(frozen=True)
class SampleBlock:
    data: np.ndarray             # (n_rows, n_samples), read-only
    sample_index: int            # index of first sample in session
    host_monotonic_ns: int       # receipt time
    host_wall_ns: int
    packet_counter: np.ndarray | None
    device_timestamp_ns: np.ndarray | None
    dropped_before: int = 0

    @property
    def n_samples(self) -> int:
        return int(self.data.shape[1])


@dataclass(frozen=True)
class SessionStats:
    blocks: int
    samples: int
    measured_rate_hz: float
    lost_samples: int
    writer_queue_depth: int
    writer_overflows: int
    lsl_dropped_samples: int
    last_block_monotonic_ns: int | None
```

`SampleBlock.data` includes all BrainFlow rows, including AUX and packet counter, so the recording layer can preserve the current file layout without reconstructing rows. `BoardProfile.eeg_rows`/`aux_rows` tell consumers which rows are signal vs metadata.

### E.2 Board catalog (`freebci/core/catalog.py`)

```python
def load_catalog() -> Mapping[int, BoardProfile]: ...
def get_profile(board_id: int) -> BoardProfile: ...
```

Phase 1 can keep the table in Python. Phase 2 can generate a JSON file under `freebci/data/boards.json` and validate it at startup. The UI must not hardcode channel counts or capability flags; it reads `BoardProfile`.

### E.3 Gateway (`freebci/core/gateway.py`)

```python
from typing import Protocol
import numpy as np
from .models import BoardProfile, DeviceConfig


class BoardGateway(Protocol):
    def prepare(self, config: DeviceConfig) -> BoardProfile: ...
    def start_stream(self) -> None: ...
    def stop_stream(self) -> None: ...
    def data_count(self) -> int: ...
    def read(self) -> np.ndarray: ...          # shape (n_rows, n)
    def configure(self, command: str) -> str: ...
    def sampling_rate(self) -> int: ...
    def release(self) -> None: ...
    @property
    def is_prepared(self) -> bool: ...
```

`BrainFlowBoardGateway` is the only module that imports `brainflow`. It owns `BoardShim` and translates BrainFlow exceptions into `GatewayError` with a stable code (`CONNECT_TIMEOUT`, `SESSION_LOST`, `CONFIG_REJECTED`, `READ_FAILED`).

`FakeBoardGateway` is deterministic: it produces a known multi-channel pattern at a configured rate, supports pause/resume, and can inject gaps and errors. It is the basis for tests and benchmarks.

### E.4 Device manager (`freebci/core/device.py`)

```python
class DeviceManager:
    def __init__(self, gateway_factory: Callable[[], BoardGateway]): ...
    def connect(self, config: DeviceConfig, cancel: threading.Event) -> BoardProfile: ...
    def configure(self, command: str) -> str: ...
    def disconnect(self) -> None: ...
    def start_stream(self) -> None: ...
    def stop_stream(self) -> None: ...
    @property
    def profile(self) -> BoardProfile | None: ...
    @property
    def state(self) -> SessionState: ...
```

Rules:

- `connect` is idempotent for an already-connected identical config; a different config requires `disconnect` first.
- `connect` and `configure` never run on the Qt thread.
- Cancellation is checked between prepare/config steps and passed to blocking operations where the SDK supports it.
- `disconnect` always attempts `stop_stream` then `release`; both are best-effort with logged errors.
- The manager never reads sample blocks; that is the acquisition service's job.

### E.5 Acquisition service (`freebci/core/acquisition.py`)

```python
class BlockSink(Protocol):
    def publish(self, block: SampleBlock) -> None: ...


class AcquisitionService:
    def __init__(
        self,
        gateway: BoardGateway,
        sink: BlockSink,
        clock: SessionClock,
        poll_interval_s: float = 0.01,
        read_timeout_s: float = 1.0,
    ): ...
    def start(self) -> None: ...
    def stop(self, timeout_s: float = 5.0) -> SessionStats: ...
    def stats(self) -> SessionStats: ...
```

Worker loop semantics:

1. Wait for data (`data_count() > 0`) with a short sleep or SDK block; never spin.
2. `read()` returns all available samples; do not assume a fixed block size.
3. Build `SampleBlock` with `sample_index` advanced by `n_samples`; compute `dropped_before` from the board packet counter if available.
4. Publish to the sink; the sink is responsible for not blocking indefinitely.
5. On `GatewayError`, transition to `ERROR`, publish a terminal error event, and stop.
6. `stop()` sets the event, joins with timeout, drains the final block, and returns immutable stats. It must be idempotent.

The acquisition thread must not call `record_data`, `np.savetxt`, `plot`, `QApplication`, or `config_board` (unless a command is explicitly queued and safe).

### E.6 Ring buffer (`freebci/core/ring.py`)

```python
class RingBuffer:
    def __init__(self, rows: int, capacity: int, dtype=np.float64): ...
    def write(self, block: SampleBlock) -> None: ...
    def latest(self, n_samples: int) -> np.ndarray: ...  # copy, shape rows x <= n
    def total_written(self) -> int: ...
    def clear(self) -> None: ...
```

- Preallocate `(rows, capacity)` once; write circularly; handle wrap with at most two copies.
- `latest()` returns a contiguous copy sized to available samples; the GUI may request 5 s, 60 s, etc.
- A single lock protects write/read; the critical section is a memcpy, not filtering.
- Display may read an older window during wrap; that is acceptable. Recorded data never comes from this ring.

### E.7 Recording (`freebci/core/recording.py`)

```python
class RecordingWriter:
    def __init__(self, root: Path, session_id: str, config: RecordingConfig): ...
    def start(self) -> None: ...
    def submit(self, block: SampleBlock) -> None: ...   # may block up to timeout
    def stop(self, reason: StopReason, timeout_s: float = 10.0) -> Manifest: ...
    def abort(self, error: str) -> None: ...
    @property
    def queue_depth(self) -> int: ...
```

Contracts:

- `submit` never silently drops; if the queue is full for longer than `write_timeout_s`, it raises `RecordingBackpressure` and the session transitions to `ERROR`.
- `stop` drains all queued blocks, flushes and fsyncs files, writes the manifest, and returns it.
- `abort` marks the manifest `failed`, closes handles, and leaves recoverable partial files.
- The writer owns file handles; no other module writes session files.
- Rotation is by samples (configurable, default 90,000) or duration; not by call count.
- File format v1 remains `1.txt` + `1.csv`; each chunk gets `1.meta.json`. A future v2 can use a binary chunk format.

### E.8 Session controller (`freebci/core/session.py`)

```python
class SessionController:
    def connect(self, config: DeviceConfig) -> BoardProfile: ...
    def prepare(self) -> None: ...
    def start(self) -> StartInfo: ...
    def stop(self) -> StopInfo: ...
    def status(self) -> StatusSnapshot: ...
    def add_marker(self, event: str, timestamp_ns: int | None = None) -> MarkerInfo: ...
    def shutdown(self) -> None: ...
```

`start()`:

- Requires `READY`.
- Starts the writer before the acquisition thread, so the first block is not lost.
- Calls `gateway.start_stream()` then `acquisition.start()`.
- Returns after the first block is published, with `first_sample_index`, `first_block_monotonic_ns`, `first_block_wall_ns`, and `session_id`. If no block arrives within `start_timeout_s`, stop and raise.

`stop()`:

- Requires `STREAMING`.
- Stops acquisition first, then `gateway.stop_stream()`, then drains/closes the writer.
- Returns final stats and manifest path; idempotent if already stopped.
- On error, still finalizes recording as `partial`/`failed` and reports the reason.

### E.9 Control API (`freebci/core/control.py`)

```python
class ControlServer:
    def __init__(self, controller: SessionController, host="127.0.0.1", port=0): ...
    def start(self) -> ControlEndpoint: ...
    def stop(self) -> None: ...


class ControlClient:
    def __init__(self, endpoint: ControlEndpoint): ...
    def status(self) -> dict: ...
    def start(self) -> dict: ...
    def stop(self) -> dict: ...
    def marker(self, event: str, timestamp_ns: int | None = None) -> dict: ...
```

See Section G for wire format and semantics.

### E.10 View model (`freebci/ui/viewmodel.py`)

```python
class SessionViewModel(QObject):
    state_changed = pyqtSignal(object)     # StateSnapshot
    stats_changed = pyqtSignal(object)     # SessionStats
    error = pyqtSignal(object)             # ErrorInfo
    recording_changed = pyqtSignal(object) # RecordingInfo

    def connect_requested(self, config: DeviceConfig) -> None: ...
    def start_requested(self) -> None: ...
    def stop_requested(self) -> None: ...
    def marker_requested(self, event: str) -> None: ...
```

The view model runs on the GUI thread and receives core events through a Qt signal bridge. It must never call blocking core methods directly; requests go to a command queue or a short-lived worker. It is the only Qt-aware adapter around the core.

### E.11 Settings (`freebci/core/settings.py`)

```python
@dataclass(frozen=True)
class HardwareSettings:
    sampling_rate: int
    baud: int
    data_mode: str
    send_mode: str
    pga_gains: tuple[str, ...]
    input_types: tuple[str, ...]
    bias_include: tuple[str, ...]
    srb1: tuple[str, ...]
    srb2: tuple[str, ...]
    channel_map: tuple[str, ...]
    schema_version: int = 2


def load_settings(path: Path) -> HardwareSettings: ...
def save_settings_atomic(path: Path, settings: HardwareSettings) -> None: ...
def validate(settings: HardwareSettings, profile: BoardProfile) -> list[str]: ...
```

- Parse with a schema/version check; unknown versions produce a clear error, not a crash.
- Save to a temporary file in the same directory, `flush`/`fsync`, then `os.replace`.
- Presets in `settings/` are read-only defaults; user changes go to a separate user file unless the user explicitly saves a preset.

Current implementation note: `core/settings.py` exposes `ChannelSettings` plus optional `sampling_rate`/`baud_rate` metadata, validates channel numbering and required fields, and performs the atomic replace above. The richer v2 fields and profile-aware `validate()` remain target work.

### E.12 Failure semantics

| Failure | Detection | Session state | Recording status | User-visible |
|---|---|---|---|---|
| Device disappears | `GatewayError` on read/stop | `ERROR` | `partial`/`failed` | “Device disconnected; recording stopped at sample N” |
| Write queue full | `submit` timeout | `ERROR` | `failed` | “Disk cannot keep up; recording stopped” |
| Disk full | `OSError` in writer | `ERROR` | `failed` | “Disk full; partial file at …” |
| Config rejected | `configure` exception | remains `READY`/`STREAMING` (depending on command) | unchanged | Command-specific error |
| Start timeout | no first block | `READY` after cleanup | `failed` empty session | “Device did not produce samples” |
| Control client disconnect | socket close | unchanged | unchanged | Log only |
| Cancel connect | cancel event | `DISCONNECTED` | none | “Connect cancelled” |

No failure may leave the UI claiming “recording” when the writer is not writing.

### E.13 Connection lifecycle, retries, and multi-device policy

**Discovery.** Use `serial.tools.list_ports.comports()` for COM enumeration (fast, metadata-rich) instead of opening 256 ports. Run UPnP discovery in the device worker with a caller-supplied timeout and cancellation; each discovered device button must capture its own IP. Wi-Fi remains an explicit “join the board AP first” workflow.

**Lifecycle.** The device layer exposes distinct facts, not one boolean:

| Fact | Meaning |
|---|---|
| `transport_connected` | The socket/serial/UPnP endpoint is reachable |
| `device_ready` | `prepare_session()` succeeded and capabilities were read |
| `streaming` | The board is producing samples; acquisition worker is running |
| `recording` | The writer has an open session and is committing chunks |

A connected device is not assumed to be acquiring valid samples. A streaming device is not assumed to be recording successfully.

**Timeouts and cancellation.** Connect, prepare, configure, start, stop, and release each have a timeout. The worker checks a `threading.Event` between steps and passes cancellation to SDK calls where possible. The UI shows “Connecting…” with Cancel; closing the dialog cancels the worker rather than leaving an orphaned session.

**Retry policy.** Retry only idempotent connection/prepare operations, at most twice, with a short backoff; never silently retry `config_board` commands (they may have partially applied). If a stream is active, an unexpected disconnect stops the session, finalizes the recording as `partial`/`failed`, and reports the last committed sample index. Do not auto-reconnect into an existing recording; start a new session with a new `session_id` and manifest.

**Duplicate connections.** `DeviceManager` refuses a second connect while `CONNECTING`/`READY`/`STREAMING` with a different config. The same config returns the existing profile. This prevents two `BoardShim` instances racing for one COM port.

**Shutdown.** Stop order is fixed: stop display reads → stop acquisition worker → stop board stream → release session → drain/close writer → stop control server → shut down logging. Each step is idempotent and logged. Exceptions are collected, not swallowed; the session status records the first fatal error.

**Multi-device extension.** If required later, instantiate one `DeviceManager` + `AcquisitionService` per device and a `SessionController` that owns a list. Each device has independent state, writer, and failure handling; the session manifest lists all devices. One device failing should mark only that device `ERROR` unless the experiment policy declares the session fatal. This is deliberately out of scope for Phases 0–5.

---

## F. Acquisition and Performance Improvements

### F.1 Current bottlenecks

1. **Poll cadence vs callback duration.** Five timers run at 50 ms/10 ms on one thread. If `shower_fun` takes 80 ms, the 50 ms updater cannot run on schedule; `get_board_data()` returns a larger block and the board’s internal buffer may overflow before the next call.
2. **Repeated full-array copies.** `np.append(self.data, buffer_data)` allocates and copies the entire 60k-sample buffer at 20 Hz. With 64 channels plus AUX rows, that is tens of megabytes per call and hundreds of MB/s of copying, plus garbage collection.
3. **Per-channel Python loops.** `processor_fun` and `shower_fun` loop over 16/32/64 channels, run notch and bandpass per channel, then build lists and convert to arrays. This is CPU work on the GUI thread.
4. **`gc.collect(generation=1)` every 50 ms.** Explicit collection in a real-time path causes pauses; it is a symptom of allocation churn, not a fix.
5. **Disk in the event loop.** `np.savetxt` formats every value in Python and writes through a text file; at 64 channels and 10k samples this is substantial.
6. **Unbounded auxiliary arrays.** Even when the main buffer is capped, the auxiliary buffers grow; the process can exhaust memory over a long session.
7. **Topography figure churn.** Every update constructs a matplotlib canvas and adds it to the layout; layout cost and memory grow monotonically.
8. **Blocking device operations.** COM scanning, UPnP discovery, `prepare_session`, `config_board`, and `time.sleep` all run in the GUI event loop.

### F.2 Target pipeline

```
Acquisition worker:
  read all available rows
  → SampleBlock(data, sample_index, t_mono, t_wall, packet_counter)
  → writer_queue.put (bounded)
  → ring.write
  → lsl_queue.put (bounded, lossy with counter)

Writer:
  pop block → append to current chunk
  every chunk_size samples → close/fsync/checksum/meta
  every N seconds → update manifest checkpoint

Display:
  QTimer 30–60 Hz → ring.latest(window) → downsample if needed → setData

Processing:
  optional worker → ring.latest(3 s) → notch/bandpass/FFT → latest result snapshot
```

### F.3 Buffer and backpressure policy

| Buffer | Bound | Producer behavior when full | Consumer behavior | Loss policy |
|---|---|---|---|---|
| Writer queue | 8–16 blocks | Block up to `write_timeout_s` (e.g., 5 s), then fail session | Drain continuously | Never drop; fail explicitly |
| Display ring | 10–30 s | Overwrite oldest | Read latest; skip frames | Display loss allowed |
| LSL queue | 64 blocks / 2 s | Drop oldest, increment `lsl_dropped_samples` | Push chunks | Explicit, reported |
| Topography queue | 1 latest snapshot | Replace pending | Render latest | Drop intermediate frames |
| Control requests | small queue | Reject with `BUSY` | Serialize | No data loss |

This makes the priority explicit: **recording > acquisition > LSL > display**. If the writer cannot keep up, the session stops and says so; it does not silently lose samples.

### F.4 Concurrency details

- Use `threading.Thread` with `daemon=False` for acquisition/writer, `threading.Event` for stop, and `queue.Queue` for handoff.
- Avoid `QThread` in the core. In the UI, use a `QObject` bridge with `pyqtSignal` emitted from worker threads; Qt queues cross-thread signal delivery automatically.
- Do not call `BoardShim` from two threads. `DeviceManager` serializes connect/configure/stop; acquisition owns `read`.
- Stop order: stop timer/display reads → stop acquisition → stop stream → drain writer → release device. Never close a file while the writer is still using it.
- Use timeouts on `join`; if a thread does not stop, log and mark the session failed rather than hanging the UI.
- Avoid `time.sleep` in the GUI; use timers or worker waits.

### F.5 Recording format and writer

Preserve the existing v1 layout:

```
<FREEBCI_HOME>/Recordings/Stream_YYYY_MM_DD_HHMMSS/
  1.txt
  1.csv
  1.meta.json
  ...
  manifest.json
  markers.jsonl
  session.log
```

`1.csv` keeps the exact header `channel1..channelN,<AUX 0>..<AUX 2>`; `1.txt` keeps the existing metadata header. Add `1.meta.json`:

```json
{
  "schema": "freebci.chunk/1",
  "chunk": 1,
  "first_sample_index": 0,
  "n_samples": 10000,
  "start_monotonic_ns": 123456789,
  "start_wall_ns": 1760000000000000000,
  "sha256": "...",
  "status": "complete"
}
```

Writer rules:

- Open with explicit encoding (`utf-8`/`newline=""` for CSV).
- Rotate at 90,000 samples by default (configurable), independent of timer calls.
- `flush()` after each chunk; `os.fsync()` at chunk close and session finalization.
- On close, rename `*.partial` to final only after checksum and row-count validation.
- Track `first_sample_index`, `n_samples`, `last_sample_index`, `expected_samples`, `gaps`.
- Never mutate the caller’s block; convert AUX values on a copy or during formatting.

Why keep CSV/TXT: downstream users already parse it; changing columns breaks them. A binary format can be added later as an optional `--format fbc2` with an exporter, not as the default.

### F.6 Display and processing

- Cap rendering at 30–60 Hz; decimate/aggregate long windows before `setData`.
- Reuse `PlotDataItem` objects; do not create new pens/items per frame.
- For time series, show a fixed window (e.g., 5 s) and a separate overview if needed; do not hand the whole 60k buffer to pyqtgraph every frame.
- Move filtering/FFT off the GUI if profiling shows >20% of a frame; otherwise keep a single processing worker for determinism.
- Topography: one `FigureCanvas` per view, created once; update the image/contour data and call `draw_idle()`. Do not add a widget per frame.
- Cache filter coefficients; `DataFilter` calls allocate; reuse where the API permits.
- Remove `gc.collect` from periodic paths; fix allocation churn instead.

### F.7 Metrics and benchmarks

| Metric | How measured | Initial target |
|---|---|---|
| Acquisition throughput | samples/s vs configured rate, 1 h | ≥99.9% of expected |
| Block loss | `sample_index` gaps + packet counter | 0 unexplained gaps |
| Acquisition-to-ring latency | `t_ring - t_block` p50/p95/p99 | p99 < 50 ms |
| Block-to-disk latency | writer timestamps | p99 < 500 ms |
| Writer queue depth | gauge | < 50% of bound |
| CPU | process CPU / wall | < 60% of one core at 64ch/1kHz (measure) |
| Memory | RSS over 8 h | < 500 MB and stable |
| GUI responsiveness | event-loop lag | p99 < 100 ms |
| Display rate | frames/s | ≥ 20 fps |
| Disk throughput | MB/s | < 70% of measured device |
| LSL drop | counter | 0 at nominal rates; reported if >0 |

The targets are starting points; Phase 0 must record actual baseline numbers before committing.

### F.8 Migration steps for performance

1. Add `AcquisitionService` and `RingBuffer`, but keep the existing renderer. Feed it `ring.latest()`.
2. Replace `recorder_fun` with `RecordingWriter.submit()`.
3. Remove `extri_data`/`topo_data`/`battery_percentage`; derive trigger/battery from the block’s AUX rows.
4. Remove per-poll `np.append`; use the ring.
5. Move filters to a processing worker only if the measured frame budget requires it.
6. Fix topography to one figure and update-in-place.
7. Re-run benchmarks after each step; keep the old path behind a flag until parity.

---

## G. Synchronization and External Integration Design

### G.1 What “synchronization” means here

There are three different things, and they must not be conflated:

1. **Command coordination:** two applications receive “start” at approximately the same time.
2. **Clock alignment:** timestamps from both applications can be mapped to a common timebase with a measured offset.
3. **Physical sample synchronization:** the hardware actually samples at the same instant, usually requiring a shared trigger/clock.

The current application provides only (1) approximately, and not even that across processes. The reconstruction can provide (2) with host timestamps and a documented uncertainty. It cannot provide (3) without hardware support. The GUI and documentation must say so explicitly.

### G.2 Timestamp model

Use a canonical `SessionClock`:

```python
@dataclass(frozen=True)
class BlockClock:
    first_sample_index: int
    host_monotonic_ns: int       # receipt of the block
    host_wall_ns: int
    sampling_rate: int
    device_timestamp_ns: np.ndarray | None
    uncertainty_ns: int
```

Rules:

- `host_monotonic_ns` is the authoritative ordering clock; `host_wall_ns` is for human display and file naming only.
- The first sample of a block is timestamped at receipt, minus an estimated transport/queue delay if known. Do not pretend the receipt time is the sample time.
- Per-sample times are **estimated** as `t0 + i / fs`; store the block start and the rate, not a fabricated array of exact hardware times.
- If the board exposes a timestamp channel, preserve it as `device_timestamp_ns` and store the mapping to host time; never overwrite it.
- `uncertainty_ns` is a documented estimate, not a guarantee; start with one poll interval plus transport jitter, refine with measurements.
- Packet counters and sample indices are preserved separately; a packet counter is not a time.

### G.3 Session lifecycle

```text
DISCONNECTED
  │ connect()
  ▼
CONNECTING ── cancel/error ──► DISCONNECTED / ERROR
  │ prepared
  ▼
READY
  │ start()
  ▼
STREAMING
  │ stop()
  ▼
STOPPING
  │ writer drained
  ▼
READY
```

Optional `ARMED` state for external coordination:

```
READY → prepare() → ARMED → start() → STREAMING
```

Valid transitions, guards, and idempotency:

- `connect` only from `DISCONNECTED`/`ERROR`; repeated identical connect returns current profile.
- `start` only from `READY`/`ARMED`; repeated start while `STREAMING` returns current `StartInfo` (idempotent).
- `stop` only from `STREAMING`/`STOPPING`; repeated stop returns the same final manifest (idempotent).
- `configure` only when not `STREAMING` (except commands explicitly marked safe, e.g., marker/LSL configuration).
- Every transition has a timeout and an error reason.

### G.4 IPC choice

| Option | Latency | Cross-language | Complexity | Fit |
|---|---|---|---|---|
| Local TCP JSON lines | ~0.1–1 ms | Yes | Low | **Chosen for control plane** |
| Named pipes | Low | Windows-specific | Medium | Rejected: platform lock-in |
| ZeroMQ | Low | Yes | Medium | Rejected: extra dependency/broker semantics |
| gRPC | Low–medium | Yes | High | Rejected: schema/tooling overhead |
| Shared memory | Very low | Language-specific | High | Not needed for control; possible future raw-data path |
| LSL | Low | Yes | Low (already used) | **Chosen for data plane/markers** |

Use TCP for commands/status; use LSL for physiological streams and optional markers. Do not add a second data-plane mechanism.

### G.5 Control protocol

Transport: TCP on `127.0.0.1`, one JSON object per line. Discovery: write `%FREEBCI_HOME%\runtime\control.json`:

```json
{"schema":"freebci.control/1","host":"127.0.0.1","port":49321,"token":"...","pid":1234}
```

A random token is required even on localhost to prevent unrelated local processes from controlling a recording. Bind only to loopback. The server handles one request at a time; long operations return `accepted` and are polled, or block with a bounded timeout.

Request:

```json
{"id":"42","cmd":"start","params":{}}
```

Response:

```json
{"id":"42","ok":true,"result":{"session_id":"...","state":"streaming","first_sample_index":0,"first_block_monotonic_ns":123,"first_block_wall_ns":456}}
```

Errors:

```json
{"id":"42","ok":false,"error":{"code":"INVALID_STATE","message":"start requires READY","state":"DISCONNECTED"}}
```

Commands:

| Command | Semantics |
|---|---|
| `status` | Return state, device, stats, recording path, manifest status, sync info |
| `connect` | Optional; normally GUI-owned. If exposed, validate config and run async |
| `prepare` | Move `READY → ARMED`; allocate writer, open files, do not start stream |
| `start` | Start stream and writer; return after first block or timeout |
| `stop` | Stop acquisition, drain writer, finalize manifest; idempotent |
| `marker` | Append a marker with `event`, `timestamp_ns` (default now), optional `duration_ns`; push LSL marker if enabled |
| `shutdown` | Stop session and close server; GUI may refuse if recording |

Semantics:

- Every request has a client-generated `id`; the server echoes it. Duplicate `id` within 60 s returns the cached response (idempotency).
- `start`/`stop` are serialized; concurrent requests return `BUSY`.
- `marker` is accepted only in `STREAMING` or `ARMED`; it records both host timestamps and an estimated sample index.
- A disconnected client does not stop the session; the GUI remains authoritative.
- The control server never exposes raw samples; high-rate data goes through LSL.

### G.6 Python client

```python
client = ControlClient.from_runtime_file()
status = client.status()
info = client.start()
client.marker("stimulus_onset", timestamp_ns=time.monotonic_ns())
final = client.stop()
```

The client should expose `wait_started(timeout_s)` if `start` is asynchronous. The returned `StartInfo` is the contract external applications use for alignment.

### G.7 LSL integration

- Create one outlet per enabled stream; stream 1/2/3 must actually publish their selected type.
- Set `source_id` to the session ID so consumers can group streams from the same session.
- Set channel names and units in the stream description.
- Push chunks, not one sample at a time, when possible (`push_chunk`); include `pylsl.local_clock()` timestamps.
- LSL timestamps are host-clock timestamps, not device timestamps; document the mapping.
- Add an optional marker outlet (`type="Markers"`) and mirror control-API markers into it.
- If the LSL queue is full, drop the oldest LSL block and increment a counter; never block acquisition. Display the counter in diagnostics.

### G.8 Clock offset and uncertainty

For external applications on the same host, `time.monotonic_ns()` is already a common clock; the main uncertainty is block receipt and transport delay. For remote applications, provide:

- A `ping`/`pong` command with `t0/t1/t2/t3` timestamps to estimate offset and round-trip delay.
- The `status` response includes `clock_id` (boot ID + process start), `monotonic_ns`, and `wall_ns`.
- Document that the estimate is only as good as the network/scheduling jitter; do not claim sub-millisecond without measurement.

Hardware triggers, if available, are the only path to physical sample alignment. Record the trigger channel and expose it in the manifest; do not simulate it in software.

### G.9 Multi-device extension

The current app supports one active board. The interfaces can support multiple `DeviceManager`/`AcquisitionService` instances later, but do not build it now. If required:

- One writer per device, one session manifest listing all devices.
- A shared `SessionClock`; per-device `first_sample_index` and offset.
- Independent failure isolation: one device error must not stop the others unless the session policy says so.
- Control API `devices[]` and per-device status.

This is an extension, not part of Phases 0–5.

---

## H. Logging and Data Integrity Design

### H.1 Logging

Replace `ConsoleLogger`’s per-message open/append/close with the standard library:

```python
logger = logging.getLogger("freebci")
logger.setLevel(logging.INFO)
handler = logging.handlers.QueueHandler(log_queue)
logger.addHandler(handler)
listener = logging.handlers.QueueListener(log_queue, file_handler, console_handler)
```

- `file_handler`: `RotatingFileHandler` or a session-scoped JSONL file; UTF-8; one writer thread.
- `console_handler`: human-readable for developers; the GUI console subscribes to a Qt signal, not to the file.
- Format: JSONL with `ts_monotonic_ns`, `ts_wall`, `level`, `session_id`, `device_id`, `thread`, `event`, `fields`.
- Levels: DEBUG (protocol details), INFO (state transitions, session start/stop), WARNING (retry, queue high), ERROR (device loss, write failure), CRITICAL (cannot continue).
- Never log per sample. Log per block only at DEBUG and sampled.
- Redact tokens and any personal paths if logs are shared.
- `ConsoleLogger` becomes a thin adapter: `write(message)` for legacy call sites, `emit` signal for the console. No file I/O in the adapter.

### H.2 Session manifest

`manifest.json` at the session root:

```json
{
  "schema": "freebci.session/1",
  "session_id": "8f0c...",
  "app_version": "0.2.0",
  "created_wall_ns": 1760000000000000000,
  "device": {
    "board_id": 2049,
    "family": "WiFi",
    "channels": 32,
    "serial_number": "...",
    "firmware": "..."
  },
  "config": {
    "sampling_rate": 1000,
    "baud": 921600,
    "data_mode": "Battery",
    "send_mode": "FreeBCI",
    "pga_gains": ["X24"],
    "input_types": ["Normal"],
    "channel_names": ["eeg1", "..."]
  },
  "clock": {
    "clock_id": "boot-uuid",
    "monotonic_origin_ns": 0,
    "wall_origin_ns": 1760000000000000000,
    "uncertainty_ns": 5000000
  },
  "start": {
    "first_sample_index": 0,
    "host_monotonic_ns": 123,
    "host_wall_ns": 456
  },
  "stop": {
    "last_sample_index": 999999,
    "host_monotonic_ns": 789,
    "host_wall_ns": 101112,
    "reason": "user"
  },
  "chunks": [
    {"file": "1.csv", "first_sample_index": 0, "n_samples": 90000,
     "sha256": "...", "status": "complete"}
  ],
  "sample_count": 1000000,
  "gaps": [
    {"after_sample_index": 12345, "missing": 12, "reason": "packet_loss"}
  ],
  "status": "complete"
}
```

`status` is one of `complete`, `partial`, `failed`. It is written/updated at stop and periodically during streaming (checkpoint). A crash leaves `status: "partial"` and no false success.

### H.3 File layout

```
Stream_YYYY_MM_DD_HHMMSS/
  manifest.json
  1.txt
  1.csv
  1.meta.json
  2.txt
  2.csv
  2.meta.json
  ...
  markers.jsonl
  session.log
```

- Keep `1.txt`/`1.csv` compatible.
- Add sidecars for timing/checksums.
- Use a `.writing` suffix while a chunk is open; rename atomically after `fsync`.
- `markers.jsonl`: one JSON object per marker with `event`, `t_monotonic_ns`, `t_wall_ns`, `sample_index_estimate`, `source`.

### H.4 Gap and loss detection

- `sample_index` is monotonic per session; a gap is any discontinuity.
- If the board packet counter is available, compare expected vs received counts; record `packet_loss` separately from `sample_gap`.
- Compute expected samples from elapsed monotonic time and configured rate only as a sanity check; scheduling jitter makes it an estimate, not ground truth.
- At stop, verify `sum(chunk.n_samples) + sum(gaps.missing) == sample_count`; if not, mark `partial` and record the discrepancy.
- Expose `lost_samples` and `gaps` in `status` and the GUI.

### H.5 Atomicity and durability

- Write chunk data to `<name>.writing`; `flush` + `os.fsync()`; close; compute SHA-256; write `<name>.meta.json`; `os.replace` to final name.
- Manifest writes use the same temp + replace pattern.
- On startup, scan for `.writing`/`.partial` chunks and offer recovery; never silently delete them.
- On clean stop, fsync the directory (where supported) after renames.
- On disk-full or write error, stop the session, set `status: "failed"`, and show the path of the partial file.

### H.6 Crash and power-loss behavior

- A crash can lose the current chunk’s unflushed tail; the manifest must not claim otherwise.
- A checkpoint manifest every N chunks records committed chunks; recovery can list valid chunks.
- Do not promise “zero loss on power failure”; promise “detectable partial recording and verified complete chunks.”
- Provide a `freebci-recover` command later if users need automated salvage; initially document manual recovery.

### H.7 Settings schema

- Add `schema_version` to settings XML or a sidecar.
- Validate ranges (sampling rate allowed per profile, gain/input values, channel map length).
- Save atomically; never overwrite a preset without an explicit “Save as”.
- On load failure, show a clear error and keep the last known-good settings; do not crash at startup.
- Keep a `settings/user.xml` separate from read-only defaults.

### H.8 Compatibility and migration

- v1 CSV/TXT remains the default for at least one release.
- New sidecars are additive; old consumers ignore them.
- If a v2 format is introduced, provide `freebci-export --format csv` and a migration note.
- Document the exact column order, AUX semantics, and timestamp limitations in `README.md`.

---

## I. GUI Reconstruction Proposal

### I.1 View model and state-driven UI

The GUI should render a `StateSnapshot` and send intent, not own acquisition:

```python
@dataclass(frozen=True)
class StateSnapshot:
    state: SessionState
    device: BoardProfile | None
    stats: SessionStats
    recording_path: Path | None
    last_error: ErrorInfo | None
    lsl: LslStatus
```

Mapping:

| State | Connect | Start | Stop | Settings | Layout | Terminal |
|---|---|---|---|---|---|---|
| DISCONNECTED | enabled | disabled | disabled | disabled | enabled | enabled |
| CONNECTING | cancel | disabled | disabled | disabled | enabled | enabled |
| READY | disconnect | enabled | disabled | enabled | enabled | enabled |
| STREAMING | disabled | disabled | enabled | disabled | enabled | enabled |
| STOPPING | disabled | disabled | disabled | disabled | enabled | enabled |
| ERROR | reconnect | disabled | disabled | disabled | enabled | enabled |

The initial state must be `DISCONNECTED`, not `True`. `Start Session` before a board is connected must be impossible, not an exception.

### I.2 Connection workflow

1. User selects a board family and transport.
2. Dialog collects only configuration (IP/port or COM port/baud); no scanning on open.
3. `Connect` sends a request to `DeviceManager.connect()` on a worker; dialog shows a progress state with Cancel.
4. COM ports are discovered with `serial.tools.list_ports.comports()` (fast); a manual refresh is available. Do not open 256 ports.
5. UPnP discovery runs in the worker with a timeout and a Stop button; device buttons capture their own IP, not a shared last value.
6. On success, the UI receives a `BoardProfile` and rebuilds channel-dependent models (MNE info, montage, widgets, FFT arrays, topography).
7. On failure, show a specific error (timeout, wrong port, board busy, protocol mismatch) and keep the dialog open.

### I.3 Streaming workflow

- `Start` is enabled only in `READY`.
- Start runs asynchronously; the UI shows “starting” and disables duplicate clicks.
- On the first block, the UI switches to `STREAMING` and displays the actual measured rate.
- `Stop` is idempotent; it shows “stopping” until the writer is drained.
- Closing the window while streaming prompts “Stop and finalize recording?”; it must not silently kill the writer.
- On error, the UI shows a red banner with the reason and the partial recording path; it does not claim success.

### I.4 Diagnostics panel

Always visible or one click away:

- State and device name/ID.
- Configured vs measured sample rate.
- Samples received, lost samples, packet loss.
- Writer queue depth and last write latency.
- Disk free space at the recording path.
- Recording duration, file path, manifest status.
- LSL stream status and dropped samples.
- Sync/clock status and uncertainty.

This replaces the current single status label and per-view ad hoc labels. It also makes silent data loss visible.

### I.5 Rendering

- One `PlotDataItem` per channel, reused; update with `setData`.
- Decimate to the pixel width; do not plot 60k points per channel per frame.
- One topography `FigureCanvas`; update data in place.
- Use a single display timer at 30–60 Hz; views subscribe to the latest snapshot. Do not let each view run its own filter over the full buffer.
- Keep filters off the GUI thread if profiling shows contention; the view model receives already-filtered windows.

### I.6 Fix the known UI defects during reconstruction

- `isSessionOn` initial value.
- 16/32/64 channel model rebuild in `initLayout`.
- `Topography_data` assignment for 16 channels.
- Topography `sfreq` from the profile/config, not hardcoded 250.
- LSL streams 2/3 and FFT/Band Power, or remove those options until implemented.
- Console singleton and signal duplication.
- `help.pdf` is not part of this task; README already replaces it.
- Settings dialogs: async apply, cancel, try/finally, no auto-overwrite of presets.
- Remove wildcard imports and unused imports (`multiprocessing`, `nptyping`, legacy serial dialog).
- Replace fixed `sleep` calls with waits on conditions/timeouts.

### I.7 Usability principles

- Distinguish device errors from software errors in the message text.
- Prevent invalid actions; do not rely on a warning after the fact.
- Require confirmation for stop-and-discard or overwrite-preset actions.
- Make session setup repeatable: remember last config, offer “Connect again”.
- Show the data destination before starting; users should know where files go.
- Keep the eight layouts; they are useful for different experiments.

---

## J. Prioritized Implementation Roadmap

Effort assumes one experienced engineer familiar with PyQt/BrainFlow; multiply for hardware debugging and review.

### Phase 0 — Baseline, packaging, and safety net (3–5 days)

**Goal:** Make the repo installable and measurable before changing behavior.

- Keep BrainFlow vendored; do **not** add it to `requirements.txt`. Remove `nptyping` if unused; verify a clean Windows install from the release archive.
- No `pyproject.toml` is planned while the source release zip is the supported distribution.
- Add `tests/` with a fake gateway skeleton and smoke tests for imports, board catalog, ring buffer, timestamps.
- Add `tools/benchmark_session.py` with synthetic data; record baseline CPU/RSS/throughput at 16/32/64 channels.
- Add a `--fake` or environment-variable path to launch the GUI without hardware (implemented as the demo session).
- Document the current file format and known limitations.

**Exit criteria:** fresh `setup_env.cmd` succeeds; `pytest` runs headless; baseline metrics captured; no behavior change for hardware users.

### Phase 1 — Recording integrity and session manifest (2–3 weeks)

**Goal:** Never lose data silently; make every session auditable.

- Implement `SampleBlock`, `SessionClock`, `RecordingWriter`, `Manifest`, `GapDetector`.
- Move recording off the GUI timer; writer thread with bounded queue.
- Write `manifest.json`, chunk sidecars, checksums; preserve `1.txt`/`1.csv`.
- Stop path drains writer, fsyncs, finalizes; crash path leaves `partial`.
- Detect gaps from sample index/packet counter; expose in status.
- Add fault injection: disk full, write error, abrupt stop.

**Exit criteria:** 8 h synthetic 64ch session has zero writer drops; manifest sample count matches files; disk-full test reports failure and leaves a readable partial; no GUI freeze during a simulated slow disk.

### Phase 2 — Decouple device and acquisition from GUI (2–3 weeks)

**Goal:** Remove all blocking device/acquisition work from the Qt event loop.

- Implement `BoardGateway`, `BrainFlowBoardGateway`, `FakeBoardGateway`.
- Implement `DeviceManager` with explicit states, cancellation, timeouts, release.
- Implement `AcquisitionService` + `RingBuffer`; replace `poll_data` and `start_openbci`/`stop_openbci`.
- Replace connection dialog `prepare_openbci` copies with manager calls; move scan/discovery to workers.
- Replace `recorder_fun` with `RecordingWriter.submit`.
- Feed existing `shower_fun`/`processor_fun` from `ring.latest()` as an intermediate step.
- Add start/stop timeouts and clean shutdown; stop `PlotThread` and any workers.

**Exit criteria:** no `BoardShim` call on the GUI thread; connect/start/stop do not block the UI >100 ms; 100 start/stop cycles leave no threads/handles; fake gateway end-to-end works.

### Phase 3 — Bounded buffers and performance (2 weeks)

**Goal:** Stable memory and predictable latency at high channel counts.

- Remove auxiliary buffers; derive trigger/battery from the latest block.
- Remove `np.append`/periodic `gc.collect` from acquisition/render paths.
- Implement display decimation and reuse plot items.
- Fix topography to one figure and update-in-place.
- Add writer/LSL queue metrics and overflow policy.
- Move filters/FFT to a processing worker if measurements require it.

**Exit criteria:** 8 h 64ch run has stable RSS (<500 MB), zero unexplained gaps, p99 block-to-disk <500 ms, GUI ≥20 fps; queue depth bounded.

### Phase 4 — Timestamps, control API, and synchronization (2–3 weeks)

**Goal:** Enable coordinated sessions with honest timing.

- Implement `SessionClock`, block timestamps, manifest clock section, marker file.
- Add local TCP control server/client; runtime discovery file + token.
- Implement `status`/`start`/`stop`/`marker`/`shutdown`; idempotency and state guards.
- Add LSL timestamps, `source_id`, real streams 2/3, marker outlet.
- Add clock offset ping/pong and documented uncertainty.
- Add a Python example client; test start/stop/marker from a separate process.

**Exit criteria:** external client can start/stop a session and read the manifest; start returns first-block timestamps; markers align to the correct sample window within one block; LSL consumers see correct timestamps/source IDs; no false physical-sync claims in docs.

### Phase 5 — GUI state, workflow, and diagnostics (2 weeks)

**Goal:** Make the application hard to misuse and easy to diagnose.

- Introduce `SessionViewModel` and state-driven enable/disable.
- Rebuild channel-dependent models on connect/config change.
- Async settings apply with progress/cancel/try-finally.
- Diagnostics panel (rates, loss, queue, disk, recording, LSL, sync).
- Workflow prompts for stop-and-finalize, overwrite preset, and connect-again.
- Remove dead UI options or implement them.

**Exit criteria:** invalid actions impossible; no generic “session error” for a known cause; usability test with 3 operators; all views render from snapshots; settings failures leave the app usable.

### Phase 6 — Validation, hardware matrix, and documentation (1–2 weeks)

**Goal:** Prove the reconstruction on real hardware and publish it.

- Hardware matrix: USB 8/16/32/64, BT 8/16, WiFi 8/16/32/64 at representative rates.
- Soak tests (8 h), disconnect/reconnect, disk-full, sleep/resume.
- CI: headless tests on Windows; hardware tests manual.
- Update README, architecture doc, data format, control API, troubleshooting.
- Migration notes for CSV/TXT and settings XML.

**Exit criteria:** matrix signed off; no P0/P1 defects; docs match behavior; reproducible install.

### Sequencing and PR slices

Suggested PRs:

1. `chore: verify vendored BrainFlow, release build, pytest skeleton`
2. `feat(core): models, catalog, clock, ring buffer + tests`
3. `feat(recording): writer, manifest, checksums, gap detector + tests`
4. `feat(device): gateway, device manager, fake gateway + tests`
5. `feat(acquisition): worker, fan-out, stats; wire start/stop`
6. `refactor(ui): replace poll timer with ring snapshots`
7. `refactor(ui): async connection dialogs; state machine`
8. `perf: remove aux buffers, decimate, fix topography`
9. `feat(sync): control server/client, markers, LSL timestamps`
10. `refactor(ui): view model and diagnostics`
11. `docs: data format, control API, hardware matrix`

Each PR should be independently testable and reversible. Keep the legacy path behind a feature flag until the new path passes the same hardware tests.

---

## K. Validation and Acceptance Criteria

### K.1 Test strategy

**Unit tests (no hardware):**

- `SampleBlock` index arithmetic and timestamp math.
- `RingBuffer` wrap, `latest`, concurrent write/read (stress with threads).
- `SessionState` transitions, guards, idempotency.
- `RecordingWriter`: rotation, checksum, manifest, gap accounting, disk-full injection.
- `BoardCatalog`: profile validation, channel/row mapping.
- `ControlServer` request parsing and error codes.
- Settings load/save/validate/atomic replace.

**Integration tests (fake gateway):**

- Connect → prepare → start → 100 blocks → stop; manifest complete.
- Start timeout, device error, writer backpressure, cancel connect.
- GUI headless (`pytest-qt`, offscreen): state mapping, button enablement, view updates.
- Control client in a separate thread/process: start/stop/marker/status.

**Stress tests:**

- 8 h at 64ch/1kHz (fake), 1 h at max board rate (hardware).
- 100 start/stop cycles; thread/handle leak check.
- Slow disk (throttled writer) and disk full.
- Network interruption (WiFi), USB unplug, Bluetooth drop.
- Long-duration GUI with all views enabled.

**Hardware tests:**

- Each board family at its max and a typical rate.
- Actual sample rate, packet loss, reconnect, recording completeness.
- LSL consumer on a second machine/process.
- Time alignment with a known stimulus marker; measure, do not assume.

### K.2 Phase gates

| Gate | Requirement |
|---|---|
| G0 | Clean install; headless tests; baseline numbers recorded |
| G1 | 8 h synthetic 64ch: 0 writer drops; manifest count exact; disk-full test yields `failed` + readable partial |
| G2 | No device call on GUI thread; UI remains responsive during connect/stream; 100 cycles leak-free |
| G3 | RSS stable <500 MB over 8 h; p99 block-to-disk <500 ms; GUI ≥20 fps; no unbounded queues |
| G4 | External client start/stop/marker works; first-block timestamps returned; LSL source IDs/timestamps correct |
| G5 | Invalid actions blocked; diagnostics visible; operator test passes |
| G6 | Hardware matrix passes; docs accurate; release candidate |

### K.3 Measurable acceptance details

- **Sample completeness:** `sum(recorded samples) + sum(gap.missing) == session.sample_count`; any difference is a failure.
- **Loss:** no unexplained `sample_index` gaps; packet-counter loss reported separately.
- **Latency:** p99 acquisition-to-ring <50 ms; p99 block-to-disk <500 ms (adjust to measured disk).
- **Responsiveness:** GUI event-loop lag p99 <100 ms; no blocking call >100 ms on the GUI thread during connect/start/stop.
- **Memory:** RSS growth <50 MB over 8 h after warm-up.
- **Start/stop:** start returns within 2 s or fails with a specific reason; stop finalizes within 5 s or reports a timeout.
- **Sync:** start command to first block p95 <20 ms on localhost; marker sample index within one block; document uncertainty; do not claim physical sample alignment.
- **LSL:** configured streams publish the selected type; `source_id` is the session ID; dropped LSL samples are counted.

### K.4 Regression policy

- Every fixed defect gets a test at the lowest possible level (unit first, integration if needed).
- Hardware-only behavior is captured in a manual checklist with version/board/rate.
- No behavior change without a before/after metric or a test.
- Keep a 1-page “known limitations” section current.

---

## L. Risks and Open Technical Questions

### L.1 Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| BrainFlow board buffer/timestamp behavior differs by transport | High | High | Measure each family; keep gateway adapter; document limits |
| Sustained 64ch/16kHz not achievable through Python/pyqtgraph | Medium | High | Benchmark early; decimate display; process off-thread; consider binary writer |
| Refactor breaks a board that currently works | Medium | High | Feature flag; hardware regression matrix; keep legacy path |
| CSV consumers depend on exact bytes/columns | Medium | Medium | Preserve v1; additive sidecars; versioned exporter |
| External control API security | Low | Medium | Loopback + token; no network bind; document |
| Clock/sync expectations exceed reality | High | High | Explicit uncertainty; distinguish command/clock/physical; measure |
| Disk-full or slow disk causes silent loss | Medium | High | Bounded writer, fail session, manifest status, diagnostics |
| PyQt5/pyqtgraph performance at 64 channels | High | Medium | Reuse items, decimate, 30–60 Hz, profile |
| Packaging/install drift | Medium | Medium | Source release zip + clean extraction test; no wheel package in current scope |
| Scope creep into multi-device/microservices | Medium | Medium | Phase gates; one device first; no new IPC without need |

### L.2 Open questions for the user

1. Which boards and sampling rates are mandatory for the first release? Is 64-channel sustained recording a real requirement or a capability checkbox?
2. Is simultaneous acquisition from multiple devices required? If so, how many, and must they share a session/manifest?
3. Which external applications must coordinate (video, motion capture, ultrasound, stimulus presentation)? Do they need a Python API, a language-agnostic protocol, or LSL only?
4. Is hardware trigger/clock input available on the target boards? Which connector/signal?
5. What is the acceptable start-command latency and timing uncertainty for the experiment? Is millisecond-level host timing sufficient?
6. Do downstream tools require the current CSV/TXT exactly, or can they consume a versioned format plus an exporter?
7. Is the application Windows-only for the foreseeable future? Is Python 3.9 a hard constraint?
8. Should the control API be enabled by default, and who is allowed to connect?
9. Is there a license decision for the repository? (Not an architecture blocker, but a publishing blocker.)
10. What is the expected session length and disk budget? Should the app preflight free space and stop at a threshold?

### L.3 Assumptions

- One active device per session in the first release.
- BrainFlow remains the SDK; no vendor SDK replacement.
- Windows 10/11 x64 and Python 3.9 remain the deployment target.
- The existing CSV/TXT format has downstream consumers and must remain available.
- The GUI is operator-facing; external integrations use LSL and the control API, not the GUI.
- No cloud connectivity or multi-user server is required.

### L.4 Decision log (proposed)

| Decision | Rationale |
|---|---|
| Incremental reconstruction, not rewrite | Preserves working board behavior and UI; lower risk |
| Qt-free core | Testability, fake gateway, clear ownership |
| One process, threads not processes | Data rates are manageable; avoids serialization/lifecycle complexity |
| TCP JSON control + LSL data | Simple, cross-language, minimal dependencies; LSL already present |
| Keep CSV/TXT v1; add manifest/sidecars | Protects downstream compatibility |
| Block-level timestamps only | Hardware timestamps are not guaranteed; honesty over false precision |
| Bounded writer queue, fail on overflow | Data integrity over silent loss |
| Display may drop/decimate | GUI smoothness must not determine acquisition |
| Source release zip, BrainFlow vendored | Keeps the validated build reproducible without adding a package-install dependency; no wheel packaging in current scope |
| Control `start` requires a board selector | Prevents an idle app from guessing which hardware to start |

---

## M. Implementation Reality and Gap Register (C–I)

This section is authoritative when A–I disagree with the code. It distinguishes **landed**, **partial**, and **target-only** work so the documents do not imply that the D/E architecture is already implemented.

### M.1 What the code actually is

| Area | Current implementation | Status |
|---|---|---|
| Core | `freebci/core`: models, clock, board catalog, gateway adapter, acquisition worker, ring buffer, recording writer, session controller, control server, diagnostics formatter, history helper, device adoption manager | Landed |
| GUI | `freebci/ui`: `MainWindow`, connection dialogs, `views/`, `workers/`, hardware settings, console/logging, recording paths; `freebci/api/session_view_model.py` remains | Landed, still a large coordinator |
| Composition | `FreeBCI_GUI.py` prepares the data directory; `freebci/app.py` owns Qt application/window bootstrap; `freebci/ui/` is the presentation layer; generated `freebci/design` UI remains | Landed |
| Display data | `SessionViewModel` ring-backed history plus `display_snapshot()` | `core/ring.py` exists; acquisition still feeds it through the view-model adapter, not a core fan-out |
| Device lifecycle | `DeviceManager` adopts an already-prepared board, creates gateways, releases | No `connect()/prepare()/configure()` state machine |
| Hardware discovery | Dialogs use `serial_worker`, Wi-Fi discovery workers, Bluetooth worker; serial/Wi-Fi workers call `core.gateway.prepare_*_board` | Preparation is worker-owned, not a DeviceManager `connect()` transition |
| Settings | `core/settings.py` validates and atomically saves XML; the dialog loads/saves through it; apply runs in `SettingsCommandWorker` | No last-known-good or profile-aware fallback |
| Logging | `core/logging.py` writes rotating JSONL `session.log`; `ConsoleLogger` still appends console text | GUI log is not yet a structured queue listener |

### M.2 Section-by-section gaps

| Section | Landed | Still open / target-only | Priority |
|---|---|---|---|
| C.1 dependency map | Core no Qt; writer/acquisition separated; serial, Wi-Fi, and virtual dialogs prepare boards through `core/gateway.py`; no `freebci/api` module imports BrainFlow | `ConnectionInfo` still carries a live board handle; views own LSL outlets | P1 |
| C.2 cohesion | Recording, acquisition, settings apply moved out of the window | `MainWindow` still owns timers, filters, plotting, LSL, menus, and state; views still own LSL/protocol choices | P1 |
| C.3 concurrency | Acquisition, writer, settings, board-command, session-start workers | No core ring; GUI filters/FFTs on its thread; topography queue is unbounded | P1/P2 |
| C.4 state model | Action guards and start/stop confirmation; `core/actions.py` derives menu/connection enablement from state | `isSessionOn`, `startButton_isclicked`, data-mode and view flags still coexist; no single guarded core state machine | P1 |
| C.5 data ownership | Duplicate trigger/battery buffers removed; display history owned by the view model and ring-backed | Acquisition does not fan out into the ring; `Topography_data` still copied through a queue; `RecordingPaths` legacy path remains | P2 |
| C.6 errors/logging | Start failure restores the UI; session errors carry text; sessions write rotating structured `session.log` | GUI `ConsoleLogger` still opens a file per message; no top-level correlation IDs | P2 |
| C.7 tests/packaging | 97 tests, CI, fake board, release zip; BrainFlow vendored | No installable `pyproject.toml` (decision: source release accepted) | Accepted |
| D.2 layers | Core/application/device boundaries exist; catalog, ring, settings, logging, and an `app.py` bootstrap exist; `freebci/ui/` now owns the main window, dialogs, views, and workers | Presentation still owns LSL outlets and view state; a QObject view model is still target-only | P1 |
| D.3 module names | `freebci/ui/main_window.py`, `freebci/ui/diagnostics.py`, `freebci/ui/views/`, and `freebci/ui/workers/` are the real inventory; `freebci/api/session_view_model.py` remains | D names `freebci/ui/viewmodel.py`; do not treat D paths as file inventory | Documentation |
| D.4 dependency rules | Core is Qt-free; `freebci/ui` imports no BrainFlow; dialogs prepare boards through `core/gateway.py`, the only BrainFlow importer | LSL outlets still live in views | P1 |
| D.5 thread model | Device/settings/start workers, acquisition, writer, control server | No LSL sender thread or log listener; control server owns no request queue | P2 |
| D.6 data flow | Block → writer + display queue + view-model history | No acquisition ring fan-out; LSL now uses a bounded chunk queue with a drop counter; no processing-worker snapshot | P2 |
| E.1 models | `BoardProfile`, `SessionConfig`, `SampleBlock`, `SessionClock`, `StateSnapshot` | No `DeviceConfig`/`StopReason` as specified; model fields differ from the proposal | Documentation |
| E.2 catalog | `core/catalog.py` is the board-table source; `ConnectionInfo` consumes its legacy row shape | UI still reads raw row indexes for capability checks | P2 |
| E.3 gateway | `BrainFlowGateway` wraps a prepared `BoardShim`; `prepare_serial_board`/`prepare_wifi_board` own transport preparation | No `configure()/sampling_rate()/is_prepared()` adapter methods; no stable gateway error codes | P2 |
| E.4 DeviceManager | Adopt/release/replace/gateway creation | No connect/prepare/cancel/start-stop ownership; transport dialogs still prepare | P1 |
| E.5 AcquisitionService | Worker loop, block assembly, error stop | Takes a callback, not `BlockSink`; no ring; no `stop()` stats contract | P2 |
| E.6 RingBuffer | `core/ring.py` with bounded, thread-safe `latest()`; used by the view-model history | Acquisition does not fan out into the ring directly; no processing-worker consumer | P2 |
| E.7 RecordingWriter | Thread, bounded queue, rotation, manifest, checksums, gaps, markers, JSONL `session.log`, `.writing` marker and read-only recovery scan | Resume/repair of a recovered session is not implemented | P2 |
| E.8 SessionController | Start/stop, markers, snapshots, clock | Start does not return `StartInfo` after first block; no `connect()/prepare()/shutdown()` contract | P2 |
| E.9 Control API | status/start/stop/marker/shutdown, token, discovery, clock offset, request IDs, `busy`/`no_session` error codes | No `cmd`/`params` envelope, idempotent request cache, `prepare`, or `connect` | P2 |
| E.10 View model | `SessionViewModel` with diagnostics, markers, history, display snapshot | Not a `QObject`; no state/stats/error/recording signals; no command queue | P2 |
| E.11 Settings | `core/settings.py` validates channel files and writes them atomically; the dialog uses it for load/save | No last-known-good fallback; no profile-aware validation; apply is still a command sequence | P2 |
| E.12/E.13 failure/connection semantics | Worker errors, reconnect test, retries | No unified retry/cancel/multi-device policy; dialogs still own lifecycle | P2 |
| F.1 bottlenecks | Aux buffers, `gc.collect`, `np.append` removed; decimation added; time-series plot curves are reused | Per-channel Python filter loops still on GUI thread; FFT/band-power/accelerometer items are recreated each frame | P2 |
| F.2/F.3 pipeline/backpressure | Writer bounded; display may drop; LSL bounded with drop counter | No acquisition ring fan-out, no topography latest-only policy | P2 |
| F.4 concurrency | Workers and writer threads | Some board commands still serialized through one worker rather than DeviceManager; no thread-stop timeout policy | P2 |
| F.5 recording format | CSV/TXT + meta + manifest + markers + `session.log` + `.writing` marker + read-only recovery scan | No directory fsync or resume/repair of partial chunks | P2 |
| F.6 display | Decimation to ~2,000 points; one topography figure claim; time-series curves reused | Other plot items recreated per frame; filtering remains on GUI | P2 |
| F.7 metrics | Bench/soak tools; 64-channel 2-minute run | No 8-hour/64-channel gate; no measured p99 latency/CPU/fps dashboard | P3 |
| G.1–G.3 sync/lifecycle | Host block timestamps, markers, manifest clock, READY/STREAMING device states | No `uncertainty_ns`, clock ID, per-sample estimate; no CONNECTING/ARMED lifecycle as drawn | P2 |
| G.5 protocol | Loopback JSON, token, selector start, clock exchange, request IDs, `busy`/`no_session` codes; discovery publishes `freebci.control/1`, host/pid | No `cmd`/`params` envelope, idempotent request cache, `prepare`/`connect`; discovery lives in the data folder, not `runtime/` | P2 |
| G.6 client | `from_discovery`/`from_runtime_file`, `wait_started`, status/start/stop/marker/clock_offset | No reconnect/backoff helper | P3 |
| G.7 LSL | Three streams, marker outlet, stable source IDs, bounded chunk queue with pending/drop counters | `source_id` is `FreeBCI:<name>`, not session id; no channel names/units; drop counter is UI-side | P2 |
| G.8 clock | `time` exchange + half-RTT uncertainty; status exposes `clock_id`, `monotonic_ns`, `wall_ns` | Manifest clock is host wall only; no per-sample hardware estimate | P2 |
| H.1 logging | Console/file logger exists | Not stdlib `QueueHandler`/JSONL; no levels/context | P2 |
| H.2 manifest | schema string, schema_version, app version, device, config, start/stop, chunks, sample count, clock, samples, blocks, lost, gaps, markers, files, session log, errors | Firmware/serial and PGA/channel-map fields are not available from the current config; `device.family` is `unknown` | P2 |
| H.3 layout | CSV/TXT/meta/manifest/markers/session.log | `.writing` is a JSON marker, not a filename suffix | P2 |
| H.4 gaps/loss | Sample-index gaps and lost counters | Packet counter and sample gap not clearly separated in manifest | P3 |
| H.5–H.6 durability | Atomic manifest, checkpoint, failed status | No recovery scan for partial chunks; no directory fsync | P2 |
| H.7 settings schema | XML presets | No schema version, range validation, last-known-good | P2 |
| I.1 state UI | Initial state fixed; guards added; start disabled while starting; one pure action table | Still flag-driven; no single state-to-enablement contract in the core | P1 |
| I.2 connection | Async discovery/prepare; fast port list | Dialogs still prepare boards; no DeviceManager.connect; no reconnect prompt | P1 |
| I.3 streaming | Async start, stop confirmation, window-close stop/finalize confirmation | Error banner is still a status label | P2 |
| I.4 diagnostics | State, device/id, configured vs effective rate, written samples, disk free, last-write latency, manifest status, counts, loss, queue, files, output, control, LSL, error | Missing clock/sync uncertainty in the GUI | P2 |
| I.5 rendering | One timer per concern? Decimation; topography figure reuse; time-series plot items reused | Other plot items still recreated; each view still filters its own full buffer | P2 |
| I.6 UI defects | Channel rebuild, sfreq, LSL streams, async settings | Wildcard imports, console singleton, and some fixed sleeps remain | P2 |
| I.7 usability | Stop confirmation; destination in diagnostics | No “Connect again”, no remembered last config, no pre-start destination preview | P3 |

### M.3 Revised sequencing

The original Phase 0 packaging goal is closed by decision: the source release zip is the distribution and BrainFlow stays vendored. `pyproject.toml` is not a current goal. The D/E target remains a **future architecture**, not a completion checklist.

Recommended next software order:

1. **P1 — explicit state and ownership:** finish the DeviceManager connect/prepare boundary, remove the remaining presentation BrainFlow imports from connection paths, and replace the flag cluster with a single state-to-action mapping.
2. **P2 — observability and format truth:** structured logging, diagnostics disk/latency/sync fields, LSL chunk/source-id/drop behavior, manifest schema completion, and recovery scan.
3. **P2 — display performance:** reuse plot items, move per-channel filtering off the GUI only if measured, and replace the display queue with a small ring if profiling justifies it.
4. **P3 — validation:** 8-hour/64-channel gate, hardware matrix, and multi-hour soak once hardware/time is available.

Document rules after this realignment:

- Do not cite D/E paths as implemented files.
- Quote the phase tracker and Section M for status, not Sections A–I.
- Mark validation claims with the transport, channel count, and duration actually exercised.
- Keep the source-release decision and vendored-BrainFlow constraint explicit in every packaging update.

---

## Appendix A: File-Level Impact Map

| File/area | Phase | Change |
|---|---|---|
| `requirements.txt` | 0 | BrainFlow stays vendored; source release zip is the distribution; no `pyproject.toml` in current scope |
| `tests/`, `tools/benchmark_session.py` | 0 | Fake gateway, unit/integration tests, benchmarks |
| `freebci/core/models.py` | 1 | DTOs, state enum |
| `freebci/core/recording.py`, `freebci/ui/recording_paths.py` | 1 | Writer thread, manifest, sidecars; keep compatibility wrapper |
| `freebci/core/clock.py` | 1/4 | Block timestamps, sample index |
| `freebci/core/catalog.py` | 2 | Shared board table; GUI consumes the legacy row shape |
| `freebci/core/settings.py` | 2 | Validated atomic channel-settings model |
| `freebci/core/logging.py` | 2 | Rotating structured `session.log` writer |
| `freebci/core/actions.py` | 5 | Pure state-to-action availability table |
| `freebci/core/ring.py` | 3 | Bounded display/processing ring |
| `freebci/core/gateway.py`, `device.py` | 2 | BrainFlow adapter, transport preparation, state manager |
| `freebci/app.py` | 2/5 | Qt composition root and window bootstrap |
| `freebci/core/acquisition.py` | 2/3 | Worker and fan-out; no core ring yet |
| `freebci/ui/main_window.py` | 2–5 | Remove acquisition/timers; use controller/view model |
| `freebci/design/main_window_interface.py` | 2/5 | State-driven UI; logger/recording construction moves to app |
| Connection dialogs | 2 | Config-only; async manager calls; no scan in constructor |
| `freebci/ui/hardware_settings.py` | 2/5 | Async apply; validation; atomic save |
| `freebci/ui/views/topography.py` | 3 | One figure, update-in-place, profile sfreq/channels |
| `freebci/ui/views/networking.py` | 3/4 | Real streams 2/3, timestamps, source IDs |
| `freebci/ui/console_logger.py`, `console_window.py` | 2 | Queue logging; singleton fix |
| `freebci/core/control.py`, `freebci/api/session_view_model.py` | 4/5 | Control server/client; current view-model adapter (D's `freebci/ui/viewmodel.py` is target-only) |
| `README.md` | 6 | Data format, control API, limitations, troubleshooting |

## Appendix B: Evidence Index

Key code references used in this assessment:

- `freebci/ui/main_window.py:62-142` — construction, 16-channel default, 32-channel montage/info, menus.
- `freebci/ui/main_window.py:356-408` — `initLayout`, buffer allocation, widget rebuild.
- `freebci/ui/main_window.py:700-752` — Start/Stop, timers, `PlotThread`.
- `freebci/ui/main_window.py:805-1105` — processing, plotting, topography, `gc.collect`.
- `freebci/ui/main_window.py:1107-1135` — start/stop, discarded final data.
- `freebci/ui/main_window.py:1144-1201` — poll, unbounded aux buffers, recording gate.
- `freebci/ui/main_window.py:1209-1219` — unstoppable `PlotThread`.
- `freebci/ui/recording_paths.py:24-84` — recording, rotation, close.
- `freebci/design/main_window_interface.py:26-104` — paths, logger, `isSessionOn`, console.
- `freebci/ui/serial_connection.py:15-46` — COM scan in constructor.
- `freebci/ui/wifi_connection.py:36-56` — UPnP discovery, shared IP.
- `freebci/ui/hardware_settings.py:192-265` — blocking Send, auto-save.
- `freebci/ui/console_logger.py:16-24` — per-message file I/O.
- `freebci/ui/console_window.py:11-14` — broken singleton.
- `freebci/ui/views/topography.py:122,153-166` — hardcoded sfreq, figure leak.
- `requirements.txt:4-17` — missing `brainflow`, unused `nptyping`.

Runtime probe (offscreen, no hardware): startup menu 20 families, `isSessionOn=True`, `mne_nchan=31`, `ts_widgets=16`, `fft_active_len=16`, `topo_chan=16`, `connect_chan=32`.

---

*This document began as the reconstruction plan. Implementation is in progress: the core, session recording, GUI integration, local control plane, three-stream LSL output, and stalled-acquisition diagnostics are landed. The real FreeBCI-WiFi-16-I (`2038`) was verified over Wi-Fi at 250 Hz with 16 channels and a completed recording; its 16-channel synchronous mode must be selected after `start_stream()`. Remaining phases should proceed through the gates in Section K.*
