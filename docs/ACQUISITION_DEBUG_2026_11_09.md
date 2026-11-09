# Channel flatline investigation — November 9, 2026

The supplied recording contains exact negative ADC-limit values, and the same
symptom was reproduced directly in the SDK output on the affected PC. With
internal shorted inputs, all 16 channels continued updating for 65 seconds on
the same board, PC, and TP-Link wireless adapter. This supports floating-input
saturation as the explanation for this recording. No Python acquisition or
recording defect was found that creates these constant raw values. Follow-up
analysis also reproduced a GUI filtering artifact that can make a constant
input look like a stationary curved waveform; see below.
It does not establish that every adapter or firmware condition is fault-free.

The user confirmed that **all physical signal inputs were floating**, with no
signal connected. A floating-input comparison between computers does not fix
the analog input conditions. The exact reason the two computers show different
floating-input behavior remains unmeasured; a controlled-input comparison on
both computers is the useful next acceptance test.

## Evidence from the supplied recording

Source: `logs/Recordings/Stream_2026_11_09_144645`.

| Observation | Result |
|---|---|
| Saved samples | 13,766 at configured 250 Hz |
| Channels 5, 6, 7, 8, 9, 16 | Exactly −187500.022352 µV for **every** saved sample |
| Other 10 EEG channels | Continue changing through the final sample |
| AUX data | Continues changing |
| CSV vs TXT | All numeric data rows agree |
| CSV SHA-256 | Matches the original manifest |
| CSV rows vs manifest sample count | Match |

The six affected channels are already at the limit in sample zero. There is no
transition from a valid value to a held arbitrary value in this particular
recording. Earlier recordings have a different set of limited channels;
channel 15 in `Stream_2026_11_09_142839` moves off the negative limit at sample
5981. This is consistent with inputs entering/leaving saturation, rather than
a fixed group of channels failing in the display.

The observed value matches:

```text
microvolts_per_count = 4,500,000 / 24 / (2^23 - 1)
negative_limit      = -2^23 * microvolts_per_count
                    = -187500.02235174447 µV
CSV rounded value   = -187500.022352 µV
```

The ADS1299 uses signed 24-bit conversion codes and clips at `0x800000` and
`0x7FFFFF` when the input exceeds its range. See the
[TI ADS1299 datasheet, section 9.5.1](https://www.ti.com/lit/ds/symlink/ads1299.pdf).
The conversion above follows the
[documented ADS1299/OpenBCI scale](https://docs.openbci.com/Cyton/CytonDataFormat/).
The live SDK log also reports gain 24 for all 16 channels. The analyzer labels
this scale as an assumption because older recordings do not preserve a
hardware gain readback.

## Live comparison on the affected adapter

Connection observed: SSID `FreeBCI-1018`, TP-Link Wireless USB Adapter #2,
802.11n, 150 Mbps negotiated receive/transmit rates, signal 69% at inspection.
Board: FreeBCI Wi-Fi 16 I, id 2038, firmware reports v3.1.2.

The probe uses the production `BrainFlowGateway`, `AcquisitionService`,
`SessionController`, and `RecordingWriter`, without Qt, filters, or plotting.
It separately copies every SDK block **before** recording, including row zero
(frame counter), and saves receive timestamps and block sizes.

| Capture | Samples | Channels fixed at ADC limit | Frame-counter missing frames |
|---|---:|---|---:|
| Normal/floating, 20 seconds | 5,007 | 5–8 and 16 throughout | 3 |
| Internal shorted, 15 seconds | 3,250 | None | 0 |
| Internal shorted, 65 seconds | 16,237 | None | 0 |
| Normal/floating again, 10 seconds | 2,507 | 4, 6–8 and 16 throughout | 0 |

For the 65-second shorted-input capture:

- All 16 channels vary; overall values range from −32.074753 to −14.193358 µV.
- No channel has more than five consecutive identical samples (20 ms at 250 Hz).
- SDK data and CSV values agree within 0.000000500 µV (six-decimal rounding).
- Maximum SDK-read interval is 32.05 ms, measured with the monotonic host clock.
- Recording sample count and SHA-256 checks pass; final status is `completed`.
- The final SDK log confirms `d` restored channel defaults, then the connection
  was released. No settings XML was changed by these probes.

The shorted-input comparison removes the external floating input while retaining
the adapter and software data path. Previously affected channels updating on
this path is strong evidence against a persistent per-channel acquisition freeze.
Returning to normal floating inputs makes the ADC-limit symptom return on a
partly different set of channels, despite zero detected missing frames. This
normal/shorted/normal comparison further separates input behavior from a
persistent transport or display failure.
The limited duration does not replace a long hardware soak or a comparison with
the other PC using a defined signal.

Raw evidence (all paths relative to the repository):

```text
logs/diagnostics/original-analysis.json
logs/diagnostics/normal-probe-analysis.json
logs/diagnostics/shorted-probe-analysis.json
logs/diagnostics/wifi-probe-1794254205549474900/   normal, 20 seconds
logs/diagnostics/wifi-probe-1794254428241810400/   shorted, 15 seconds
logs/diagnostics/wifi-probe-1794254498153810700/   shorted, 65 seconds
logs/diagnostics/wifi-probe-1794254686445992000/   normal again, 10 seconds
```

Each probe directory contains `sdk_rows.npz`, `probe.json`, `brainflow.log`, and
a normal `Recordings/Stream_...` directory. The 65-second directory also contains
`analysis.json`. Logs are ignored by Git; copy these directories when sharing
the results with another PC.

One earlier probe (`wifi-probe-1794254346598081700`) requested shorted inputs
**before** the `v` reset and therefore actually recorded normal floating inputs.
It is excluded from the controlled-input evidence above. The final tool applies
input commands after startup/reset and the 16-channel-mode command, then drains
transitional buffered data. Tests cover this ordering. The `?` register request
returned only `$$$` in the SDK log, so it did not provide usable register readback.

## Diagnostic limitations found in the Python source

Follow-up rendering analysis reproduced the user's observation that a channel
can appear to hold a curve but respond to a changed input voltage.
`MainWindow.shower_fun()` filters each recent window from scratch. When new
samples have the same constant value, each redraw can reproduce the same filter
startup transient at the same horizontal positions. With 50 Hz notch and
1-50 Hz bandpass, a constant input at the negative ADC limit produced a repeated
36.192875 microvolt peak-to-peak curve in the actual renderer. New constant
samples left that curve identical, while a voltage step changed it; `setData()`
was called on every invocation. This is a display-processing artifact, not
evidence that the acquisition worker held an old block.

The channel Railed indicator also uses filtered amplitude, so removing the DC
offset can hide saturation in that indicator. Auto1 and Auto2 only change
vertical scaling; Auto2 fits the visible minimum/maximum and can magnify tiny
variations. These behaviors remain known limitations: the user deferred signal
quality indicators and persistent filter-state changes. Version 0.1.12 changes
only the default display filters to 60 Hz notch and no bandpass; recordings
continue to contain unfiltered values.

`SessionClock.new_block()` assigns a contiguous sample index based on the number
of samples delivered. `RecordingWriter.submit()` detects gaps in **that index**.
Its `lost_samples` field therefore does not detect missing frames upstream of
the SDK read. The GUI separately counts packet/frame-counter jumps on the
display queue, and those counters are not saved in the legacy CSV.

Consequently, `lost_samples: 0` in the original manifest is not evidence of
lossless Wi-Fi delivery. Its saved timestamps are extrapolated from sample index,
not independent arrival measurements. Likewise, `completed` means recording
finalized successfully; it does not certify signal quality. The new live probe
records frame-counter diagnostics independently of GUI display draining.

The frame counter is still a heuristic: repeated values and large restart jumps
are ambiguous. A small counter discontinuity cannot explain five or six channels
being exactly at the ADC limit for every sample while the others change.

## Reproduce and compare

Analyze an existing session without changing it:

```powershell
.venv\Scripts\python.exe tools\analyze_recording.py logs\Recordings\Stream_2026_11_09_144645
```

Disconnect the GUI from the board before running a live probe. These commands
use SDK initialization (which resets channel defaults), 250 Hz, and board 2038.
The shorted-input probe restores channel defaults on exit:

```powershell
.venv\Scripts\python.exe tools\diagnose_wifi.py --seconds 65
.venv\Scripts\python.exe tools\diagnose_wifi.py --input-mode shorted --seconds 65
```

Run the same shorted-input probe on the other PC. Compare `sdk_rows.npz`, frame
counters, receive gaps, and analyzer output. Then use the same defined external
test signal or properly connected electrodes/reference/bias on both computers.
If only one PC fails under that controlled condition, investigate the adapter
and transport with that capture; the floating-input artifact alone cannot
establish that cause.

Validation: 28 focused tests pass, covering the new analyzer and live-probe
lifecycle/order, plus existing acquisition, gateway, packet-counter, recording,
and fault handling tests. The transport, recording path, and filtering algorithm
were left unchanged; follow-up GUI defaults are documented above.
