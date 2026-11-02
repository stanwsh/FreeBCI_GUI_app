# FreeBCI GUI

FreeBCI GUI is a Windows desktop application for recording and viewing EEG and
other biosignals from FreeBCI acquisition boards. It connects over Wi-Fi, USB, or
Bluetooth, shows the signals live, and writes the raw data to disk.

## Features

- Live multi-channel traces with adjustable time window and vertical scale
- FFT and band-power views
- Brain topography on a 10-20 electrode map
- Accelerometer, external-trigger, and battery views (on supported boards)
- LSL output for use with other acquisition software
- Automatic CSV/TXT recording while streaming
- Per-channel hardware settings and electrode mapping
- Eight window layouts

## Supported boards

| Family | Models | Connection |
| --- | --- | --- |
| USB | FreeBCI-USB-8-I/II, FreeBCI-USB-16-I/II, FreeBCI-USB-24, FreeBCI-USB-32, FreeBCI-USB-64 | USB cable / USB serial port |
| Bluetooth | FreeBCI-BT-8-I/II, FreeBCI-BT-16-I/II | Bluetooth serial port |
| Wi-Fi | FreeBCI-WiFi-8-I/II/III, FreeBCI-WiFi-16-I/II/III, FreeBCI-WiFi-24, FreeBCI-WiFi-32, FreeBCI-WiFi-64 | Wi-Fi |

Accelerometer, external-trigger, and battery data are available only on boards
that provide those inputs. Unsupported views stay disabled.

## Requirements

- Windows 10 or 11, 64-bit
- Python 3.9, 64-bit
- About 700 MB of free disk space for the Python environment
- The FreeBCI board, its power supply, and electrodes
- An internet connection while installing

The BrainFlow build that talks to FreeBCI hardware is included in the
`brainflow/` folder. Do not install a separate BrainFlow package; the copy in
this repository is the tested version for these boards. Its `nptyping`
dependency is installed with the other Python packages.

The USB serial driver recommended by the board manufacturer is required for USB
connections. Bluetooth boards must be paired in Windows before you connect.

## Installation

### Option 1: automatic setup

1. Install [uv](https://docs.astral.sh/uv/):
   ```bat
   winget install --id=astral-sh.uv -e
   ```
2. In Explorer, double-click **`setup_env.cmd`**.

   The script creates a `.venv` folder, downloads Python 3.9 and the required
   packages, and finishes the environment setup. This can take several minutes.

3. Double-click **`run.cmd`** to start the application.

### Option 2: manual setup

Open Command Prompt in this folder and run:

```bat
py -3.9 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe setup_env.py
```

If `py -3.9` is not available, install Python 3.9 (64-bit) from
[python.org](https://www.python.org/downloads/) first.

Then start the GUI:

```bat
run.cmd
```

or:

```bat
.venv\Scripts\python.exe FreeBCI_GUI.py
```

Keep the application files together. The program loads its images, settings,
and bundled BrainFlow library from the repository folder, so moving only the
program files will not work.

## Quick start

1. Connect the board and power it on.
2. Start `run.cmd`.
3. Open **Boards**, choose your board model, then choose the connection type.
4. Fill in the connection dialog and click **Connect**.
5. Click **Start Session**.
6. Click **Stop Session** when you are finished. The recording is saved
   automatically.

## Connecting a board

Open the **Boards** menu and select the exact model printed on the board. Each
model submenu offers the connection methods that model supports.

### Wi-Fi

1. Connect the computer to the board's Wi-Fi network.
2. Choose **WiFi** in the board submenu.
3. Leave the default address `192.168.4.1` and port `8899`, or enter the board's
   address if it is on your local network.
4. Click **SEARCH** to discover the board, then **Connect**.

`SEARCH` uses UPnP. If the board is not found, type its IP address and port
manually. VPN software and restrictive firewalls can block discovery.

### USB serial port

1. Connect the board with a USB cable and install its serial driver if Windows
   does not show a new COM port.
2. Choose **USB Serial Port** in the board submenu.
3. Select the COM port and click **Connect**.

If several ports are listed, unplug the board to see which entry disappears.

For the tested FreeBCI-WiFi-16-I in USB mode, the path is
**Boards > FreeBCI-WiFi-16-I > USB Serial Port**, then select the CH343 port
(usually `COM3`). The application switches the board to 16-channel, 2 Mbaud
operation automatically.

### Bluetooth

1. Pair the board in **Settings > Bluetooth & devices**.
2. In Windows Bluetooth settings, note the **Outgoing** COM port for the board.
3. Choose **Bluetooth Serial Port** in the board submenu.
4. Select the port, keep the baud rate at `921600`, and click **Connect**.
   **Scan** refreshes the list of available ports.

### USB high-speed connection

Some USB boards use a high-speed interface instead of a virtual COM port. Choose
**USB Serial Converter** in the board submenu and click **Connect**.

### After connecting

The dialog reports `connection successfully!` and the main window status changes
to `Session started!`. Click **Start Session** to begin acquisition. If the
connection fails, check the cable, the port, and the board's power, then close the
dialog and try again.

## Main window

The top bar contains:

- **Start Session / Stop Session** - start or stop acquisition and recording.
- **Notch Filter** - None, 50 Hz, or 60 Hz.
- **BP Filter** - None, 5-50 Hz, 7-13 Hz, 15-50 Hz, 1-50 Hz, or 1-100 Hz.
- **Terminal** - open the live console log.
- **Layout** - choose one of eight window arrangements.

The status line below the toolbar shows frames per second, packet loss, and the
number of packets received. Packet loss should stay close to zero. A steadily
rising value usually means a weak Wi-Fi or Bluetooth link.

The notch and band-pass filters affect the plots, FFT, band power, and
topography. They do not change the recorded files, which always contain the raw
samples.

To disconnect, open **Boards > Disconnect**. This also stops the session.

## Views

Each panel has a small dropdown in its header. Use it to change which view is
shown in that panel.

### Time Series

Shows each channel as a scrolling trace.

- **Time Window** - default 5 seconds, or 1, 3, 5, or 10 seconds.
- **Vert Scale** - automatic scaling, or a fixed range from 50 uV to 10000 uV.
- Channel buttons turn an individual trace on or off.
- The round button next to a channel starts an impedance check for that channel.
  A good contact gives a low, stable value.
- **Hardware settings** opens the board configuration dialog. Stop the session
  first.

### FFT Plot

Shows the frequency spectrum of the last few seconds of data.

- **Max Freq** - 20 to 800 Hz.
- **Max uV** - vertical range.
- **Log / Linear** - frequency-axis scale.
- Channel buttons choose which channels are included.

### Band Power

Shows the power in the standard EEG bands for each channel. Use it to compare
activity between regions or over time.

### Brain topography

Draws the selected channels on a 10-20 electrode map. The **Channels-electrodes
settings** button opens the electrode mapping dialog.

## Electrode mapping

The topography view needs to know which electrode each channel is connected to.

1. Stop the session.
2. Open **Brain topography > Channels-electrodes settings**.
3. For each channel, select the electrode position. Leave unused channels as
   **Unused (leave blank)**.
4. Click **Apply** to update the map.
5. Use **Save** and **Load** to keep the mapping as an XML file.

The repository includes example mappings in the `settings` folder.

## Hardware settings

Stop the session before opening **Hardware settings**. The dialog can change:

- **Sample Rate** - 250, 500, 1000, 2000, 4000, 8000, or 16000 Hz, depending on
  the board.
- **Baud Rate** - serial connection speed.
- **Data Mode** - what the auxiliary channels carry: accelerometer, external
  trigger, or battery, depending on the board.
- **Send Mode** - board protocol.
- **PCA Gains** - input gain (X1 to X24).
- **Input Type** - normal, shorted, bias measurement, and other test modes.
- **Bias Include**, **SRB1**, **SRB2** - reference and bias configuration.

**Send** applies the settings to the board. **Save** and **Load** store them as
an XML file. Leave advanced settings at their defaults unless you know the
required configuration for your electrodes.

Changes take effect when you start the session again. Stop the session first,
apply the change, then click **Start Session**.

## LSL output

The **Networking** view can publish the incoming signal as a Lab Streaming Layer
(LSL) stream, so other software can record or process it at the same time.

1. Open the **Networking** view.
2. In the first stream row, set the stream name, for example `FreeBCI_EEG1`.
3. Set **Data Type** to **Time Series**.
4. Set the stream **Type** (the default `EEG` is suitable for EEG data).
5. Click **Start LSL Stream**. Click **Stop** to end it.

The stream then appears in LSL-aware applications such as LabRecorder, OpenViBE,
or MNE.

## Recording

Recording starts automatically when you click **Start Session**. There is no
separate record button.

By default, files are written under `logs` next to the application:

```text
logs\
  Console_Data\
    Console_2026_11_01_143000.txt
  Recordings\
    Stream_2026_11_01_143005\
      1.csv
      1.txt
      1.meta.json
      manifest.json
      2.csv
      2.txt
      2.meta.json
      ...
```

Each session gets its own `Stream_<date>_<time>` folder. Files roll over
automatically: `1.csv` and `1.txt` hold the first 90,000 samples, `2.*` the next
90,000, and so on. Every data file has a matching `.meta.json` sidecar with its
sample count, checksum, and timing information. `manifest.json` describes the
whole session and is finalized when the session stops. It is also written at
session start and refreshed every few seconds, so an interrupted session leaves
a manifest with `status: recording` instead of no metadata. It records
`lost_samples` and a `gaps` list if the board skipped samples.

### CSV files

The first row names the channels, followed by the three auxiliary inputs:

```csv
channel1,channel2,...,channel32,<AUX 0>,<AUX 1>,<AUX 2>
12.345678,...
```

EEG values are in microvolts. Auxiliary values depend on the selected data mode
(accelerometer, trigger, or battery).

### TXT files

The matching `.txt` file is a whitespace-friendly copy with a short header:

```text
FreeBCI Raw Data
Number of Channels: 32
Sampling Rate: 250 Hz
Board: FreeBCI-USB-32
1 2 3 ... <AUX 0><AUX 1><AUX 2>
Start Time:2026_11_01_143005
```

### Changing the data folder

Set the `FREEBCI_HOME` environment variable before starting the application:

```bat
set FREEBCI_HOME=D:\FreeBCI_data
run.cmd
```

The `Console_Data` and `Recordings` folders are created inside that directory.
To make the change permanent, add `FREEBCI_HOME` in Windows **Environment
Variables**.

**File > Open** opens the recordings folder. The **Terminal** button opens the
live console log.

## Control API

Each session also starts a small control endpoint on `127.0.0.1`. It is only
reachable from the same computer and requires the random token printed in the
Terminal log when the session starts:

```text
FreeBCI: control API tcp://127.0.0.1:54321 token ...
```

Use it from another Python process to read status or stop the recording:

```python
from freebci.core import ControlClient

client = ControlClient("127.0.0.1", 54321, "the-token-from-the-log")
print(client.status())
client.stop()
```

`stop()` asks the GUI to stop and returns `"stop_requested"`; the session
finalizes on the next GUI event. `status()` returns the session state, sample
and block counts, elapsed time, display-drop count, lost-sample count, error
text, and output path. The API is a control plane only; physiological data
continues to use the CSV files and LSL.

## Troubleshooting

### `uv` is not found

Install uv with `winget install --id=astral-sh.uv -e`, reopen Command Prompt, and
run `setup_env.cmd` again. Alternatively, follow the manual setup steps above.

### The application does not start

Run `run.cmd` from Command Prompt so the error message stays visible. Common
causes are a missing `.venv`, a 32-bit Python installation, or an interrupted
package install. Re-run `setup_env.cmd` (after removing `.venv`) or reinstall the
requirements.

### `pyqtgraph` reports a Qt binding error

Run `.venv\Scripts\python.exe setup_env.py` again, then start with `run.cmd`. If
you launch Python directly from another shell, set `PYQTGRAPH_QT_LIB=PyQt5`
first.

### No COM port is listed

Install the USB serial driver for the board, use a data-capable USB cable, and
check Windows **Device Manager** for a port marked with a warning. Close other
programs that may be using the port.

### Wi-Fi connection fails

Join the board's own Wi-Fi network first. Disable VPN software temporarily, allow
the application through Windows Firewall, and try entering the board's IP
address directly instead of using **SEARCH**.

### The board connects but the traces are flat

Click **Start Session**. Check that the channel is enabled, the electrode is
attached, and the correct reference and bias settings are selected. Use the
impedance button in the Time Series view to check contact quality.

### Recordings are missing

Recording only runs while a session is active. Check `logs\Recordings`, or the
folder named by `FREEBCI_HOME` if you set it. The current log in
`logs\Console_Data` records connection and save errors.

### Packet loss is high

Move the computer closer to the board, reduce the sample rate in **Hardware
settings**, or use a USB connection instead of Wi-Fi or Bluetooth.

## Project layout

```text
FreeBCI_GUI.py            application entry point
brainflow/                bundled BrainFlow build for FreeBCI hardware
freebci/                  application package
  api/                    acquisition, recording, and view logic
  core/                   session, acquisition, and recording services
  design/                 window and dialog layouts
settings/                 example hardware and electrode XML files
electrodes_pos_32.png     head model for 32-channel topography
electrodes_pos_64.png     head model for 64-channel topography
requirements.txt          Python dependencies
setup_env.cmd             one-step environment setup (uv)
setup_env.py              environment finishing step
run.cmd                   start the application
logs/                     created at first run
```
