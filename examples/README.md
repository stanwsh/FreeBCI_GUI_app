# External integration examples

These examples connect a **separate process** to a running FreeBCI GUI. They do
not import the Qt application, and they do not open the board themselves.

| File | What it demonstrates |
| --- | --- |
| `control_client.py` | The supported high-level Python client: status, start, marker, stop, clock offset. |
| `raw_control.py` | The raw newline-JSON control protocol with only the Python standard library, for porting to MATLAB, C#, JavaScript, or another language. |
| `lsl_receive.py` | Discovering and reading the EEG and marker LSL streams. |

Run all commands from the repository root. The scripts add the repository to
`sys.path`, so an editable checkout does not need to be installed:

```bat
python examples\control_client.py status
python examples\lsl_receive.py --discover
```

The release zip contains this directory too, so the same commands work from an
unpacked release folder.

## Before you start

1. Start FreeBCI GUI and connect a board, or use **File > Start Demo Session**.
2. The GUI creates a loopback control endpoint for its whole lifetime. It writes
   `control.json` to the FreeBCI data directory:
   - `%FREEBCI_HOME%\control.json` when `FREEBCI_HOME` is set;
   - otherwise `%USERPROFILE%\Documents\FreeBCI\control.json`.
3. Keep the GUI open. `shutdown` closes it; `stop` only finalizes the current
   session.
4. The token in `control.json` is a secret for this machine. Do not paste it into
   a shared log or expose the port outside loopback.

If the discovery file is somewhere else, pass it explicitly:

```bat
python examples\control_client.py --discovery D:\FreeBCI_data\control.json status
```

`FREEBCI_CONTROL_FILE` is also accepted by both control examples. The GUI's
**Session Diagnostics** window shows the active endpoint and discovery path.

## Quick start: demo session

This starts the synthetic 16-channel board, waits until it is recording, adds a
marker, runs for five seconds, stops, and waits for the manifest to be finalized:

```bat
python examples\control_client.py demo --duration 5 --marker baseline
```

Typical result (values vary):

```text
discovery: C:\Users\me\Documents\FreeBCI\control.json
start_requested
{
  "state": "recording",
  "session_id": "FreeBCI_demo_...",
  "sample_count": 512,
  ...
}
{
  "label": "baseline",
  "source": "control",
  "sample_index": 512,
  "elapsed_seconds": 2.05,
  "wall_time": "2026-11-02T21:40:00.123456"
}
stop_requested
{
  "state": "finalized",
  ...
  "output_path": "C:\\Users\\me\\Documents\\FreeBCI\\Recordings\\..."
}
```

`start` and `stop` are intentionally asynchronous: the command is queued onto
the GUI thread. `stop_requested` means the request was accepted, not that the
CSV and manifest are already closed. Poll `status` until it reports
`finalized`, `failed`, or `idle` before reading the recording folder.
`control_client.py stop` and `demo` do that polling for you.

Starting a real board uses the same selector rules as the GUI:

```bat
python examples\control_client.py start 2038
python examples\control_client.py start FreeBCI_WiFi_16_I
```

The selector must match the currently connected board. `demo` is always
available while no session is active.

## High-level Python client

The short version, using the same code as `control_client.py`:

```python
from pathlib import Path
from freebci.core import ControlClient

discovery = Path.home() / "Documents" / "FreeBCI" / "control.json"
client = ControlClient.from_discovery(str(discovery))

print(client.status())
print(client.start("demo"))
print(client.wait_started(timeout=15))
print(client.marker("stimulus onset"))
print(client.stop())
print(client.status())
```

Useful methods:

| Method | Purpose |
| --- | --- |
| `ping()` | Validate endpoint and token. |
| `status()` | Current snapshot dictionary. |
| `start("demo" or "2038" or catalog name)` | Queue a session start. |
| `wait_started(timeout=...)` | Poll until state is `armed` or `recording`. |
| `marker("label")` | Append a marker; returns the saved marker record. |
| `stop()` | Queue a stop; returns `stop_requested`, `completed`, etc. |
| `clock_offset(samples=5)` | Estimate GUI-host wall clock offset and uncertainty. |
| `shutdown()` | Stop and close the GUI. |

`ControlError` has a stable `.code`, for example `busy`, `no_session`, or
`invalid_request`. Start returns `busy` if a session is already active or a
start is pending.

## Raw control protocol

`raw_control.py` speaks the wire format directly. The transport is a TCP
connection to `127.0.0.1`, one newline-terminated JSON object per request, and
one JSON object per response:

```json
{"command":"status","token":"<token from control.json>","id":1}
```

```json
{"ok":true,"snapshot":{"state":"idle"},"id":1}
```

Every request includes `token`; `id` is optional but recommended because the
server echoes it. The connection is closed after one reply. Requests are small
(4 MiB maximum). A successful response always has `"ok": true`. A failure is:

```json
{"ok":false,"error":"no active session","code":"no_session","id":2}
```

Commands implemented by the current GUI:

| Request | Extra fields | Success payload |
| --- | --- | --- |
| `ping` | none | `protocol` |
| `time` | `client_send_ns` (integer) | echoed client time, server receive/send times |
| `status` | none | `snapshot` |
| `start` | `board` (string selector) | `status: "start_requested"`, `board` |
| `marker` | `label` (string) | `marker` record |
| `stop` | none | `status`, `snapshot` |
| `shutdown` | none | `status: "shutdown_requested"` |

`status` includes:

- `state`: `idle`, `connected`, `armed`, `recording`, `stopping`, `finalized`,
  or `failed`;
- `session_id`, `channel_count`, `sample_count`, `blocks`;
- `elapsed_seconds`, `display_dropped_samples`, `lost_samples`,
  `seconds_since_block`;
- `markers`, `last_block_wall_ns`, `last_sample_time_ns`, `output_path`;
- `clock_id`, `monotonic_ns`, `wall_ns`.

See the actual request/response exchange:

```bat
python examples\raw_control.py ping
python examples\raw_control.py status
python examples\raw_control.py start demo
python examples\raw_control.py marker "button press"
python examples\raw_control.py stop
python examples\raw_control.py time
```

For a non-Python client, copy the small `RawControlClient.request()` function:
open a TCP socket, write compact JSON plus `\n`, read one line, parse it, check
`id` and `ok`, then close. No framing, compression, or authentication header is
involved beyond the token field.

## LSL streams

LSL is the right path for continuous samples. It is not tunneled through the
control socket.

In the GUI, open **Networking**, select **Time Series** for one or more of the
three streams, and press **Start LSL Stream** before or during a session. The
defaults are:

| Property | Value |
| --- | --- |
| Stream names | `FreeBCI_EEG1`, `FreeBCI_EEG2`, `FreeBCI_EEG3` |
| Type | `EEG` |
| Source id | `FreeBCI:<stream name>` |
| Format | `float32` |
| Channels | The active session channel count |
| Nominal rate | The session sampling rate |
| Marker stream | `FreeBCI_Markers`, one string channel, irregular rate |

The GUI pushes chunks and keeps a bounded 4096-sample queue per stream. If the
consumer cannot keep up, the oldest queued samples are dropped, the drop count
is visible in **Session Diagnostics**, and the recording on disk is unaffected.

Discover and receive:

```bat
python examples\lsl_receive.py --discover
python examples\lsl_receive.py --name FreeBCI_EEG1
python examples\lsl_receive.py --name FreeBCI_EEG1 --duration 10 --json
python examples\lsl_receive.py --source-id FreeBCI:FreeBCI_EEG1 --no-markers
```

Each sample event reports the first LSL timestamp, its age relative to
`pylsl.local_clock()`, the chunk size, and the first channel values. Marker
events arrive on the same loop with their label and LSL timestamp. `--json`
prints one object per line, which is convenient to pipe into another tool.

LSL timestamps are host-clock timestamps assigned when the data reaches the
outlet. They are not hardware sample timestamps. Use them to order events and to
measure consumer latency, not as proof of physical sample-level synchronization.

## Correlating markers with data

For a marker sent through the control API:

- `sample_index` is the number of samples received when the marker was
  requested;
- `elapsed_seconds` is the session-relative elapsed time;
- `wall_time` is an ISO host wall-clock string.

For LSL, the marker has an LSL timestamp. If both the EEG and marker consumers
are on the same machine, `pylsl.local_clock()` is a common time base, so the
difference between a marker timestamp and an EEG chunk timestamp gives ordering
and approximate latency. The GUI clock is documented as `clock_id:
"host-monotonic"`; `status.monotonic_ns` and `status.wall_ns` let a remote
process relate its own clock to the GUI host without assuming the two wall
clocks are identical. `clock_offset()` samples the four-timestamp exchange and
reports half-RTT uncertainty.

The recording manifest contains the authoritative sample counts, timing block,
chunk list, and session markers. Use the manifest plus `markers.jsonl` for
offline analysis; use LSL for online consumers.

## Limitations

- The control endpoint is loopback-only by design. It is a local operator API,
  not a network service.
- There is one active session per GUI process.
- `start` requires either `demo` or the already-connected board selector.
- The control API does not stream raw samples; use LSL for that.
- Firmware and serial-number metadata are not currently exposed in the
  manifest.
- LSL currently publishes **Time Series** only; the view removes the FFT and
  Band Power choices. Read the stream metadata before assuming a channel count.
