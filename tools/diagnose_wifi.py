"""Capture unfiltered SDK rows alongside a normal Wi-Fi session.

Close the GUI's board connection before running. This uses the same 250 Hz
setup and post-start 16-channel command as the GUI. SDK preparation resets
channel settings to board defaults. Optional shorted inputs are restored
to defaults on exit. No Qt or plotting is involved. Only board 2038 is supported.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from freebci.core.gateway import BrainFlowGateway, prepare_wifi_board
from freebci.core.models import BoardProfile, SessionConfig
from freebci.core.packets import PacketLossCounter
from freebci.core.session import SessionController


class ProbeGateway(BrainFlowGateway):
    def __init__(self, board, input_mode='normal'):
        commands = ('\",',)
        if input_mode != 'normal':
            commands += input_commands(input_mode)
        super().__init__(board, 2038, 16, post_start_config=commands)
        self.input_mode = input_mode
        self.blocks = []
        self.received_ns = []
        self.received_monotonic_ns = []
        self.packets = PacketLossCounter()

    def start_stream(self):
        super().start_stream()
        if self.input_mode != 'normal':
            # Startup/reset and channel-mode changes precede controlled inputs.
            # Exclude samples buffered while those commands were being applied.
            self._board.get_board_data()

    def read(self):
        data = super().read()
        self.blocks.append(np.array(data, copy=True))
        self.received_ns.append(time.time_ns())
        self.received_monotonic_ns.append(time.perf_counter_ns())
        self.packets.add(data[0])
        return data


def capture(args):
    if not 0 < args.seconds <= 120:
        raise ValueError('--seconds must be between 0 and 120 (capture is held in memory)')
    from brainflow.board_shim import BoardShim

    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    run_dir = output / ('wifi-probe-%d' % time.time_ns())
    run_dir.mkdir()
    BoardShim.enable_dev_board_logger()
    BoardShim.set_log_file(str(run_dir / 'brainflow.log'))
    board = prepare_wifi_board(2038, args.ip, args.port)
    gateway = ProbeGateway(board, args.input_mode)
    try:
        return _capture_stream(args, run_dir, board, gateway)
    finally:
        try:
            if args.input_mode != 'normal':
                board.config_board('d')
        finally:
            gateway.release()


def input_commands(mode):
    from freebci.core.hardware_settings_protocol import HardwareSettingsProtocol as protocol

    input_type = {'shorted': 'Shorted'}[mode]
    return tuple('x%s06%d110X' % (protocol.Channel[ch], protocol.InputTypeProtocol[input_type])
                 for ch in range(1, 17))


def _capture_stream(args, run_dir, board, gateway):
    controller = None
    error = None
    status = None
    response = None
    try:
        board.config_board('~6')
        time.sleep(0.1)
        response = board.config_board('v')
        config = SessionConfig(
            session_id=run_dir.name,
            board=BoardProfile(2038, 'FreeBCI_WiFi_16_I_WIFI', 16, 250),
            sampling_rate=250,
            output_root=str(run_dir),
            channel_count=16,
        )
        controller = SessionController(config, gateway)
        controller.start()
        deadline = time.perf_counter() + args.seconds
        while time.perf_counter() < deadline:
            controller.drain_display()
            if controller.check_health():
                break
            time.sleep(0.02)
    except Exception as exc:
        error = str(exc)
        response = None
    finally:
        if controller is not None:
            status = controller.stop().value
    data = np.concatenate(gateway.blocks, axis=1) if gateway.blocks else np.empty((0, 0))
    np.savez_compressed(
        run_dir / 'sdk_rows.npz', data=data,
        block_samples=np.array([b.shape[1] for b in gateway.blocks]),
        received_wall_ns=np.array(gateway.received_ns, dtype=np.int64),
        received_monotonic_ns=np.array(gateway.received_monotonic_ns, dtype=np.int64),
    )
    result = {
        'output': str(run_dir), 'recording': controller.output_path if controller else None,
        'status': status, 'error': error or (controller.check_health() if controller else None),
        'board_response': response, 'samples': int(data.shape[1]),
        'input_mode': args.input_mode,
        'packet_counter_received_frames': gateway.packets.received,
        'packet_counter_missing_frames': gateway.packets.lost,
        'packet_counter_loss_percent': gateway.packets.percent,
        'packet_counter_note': 'frame counter heuristic; resets and repeated counters are ambiguous',
        'sdk_row_layout': 'row 0 counter; rows 1..16 EEG; remaining rows SDK metadata/AUX',
    }
    (run_dir / 'probe.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ip', default='192.168.4.1')
    parser.add_argument('--port', type=int, default=8899)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--input-mode', choices=('normal', 'shorted'), default='normal',
                        help='optional controlled input; restores board defaults on exit')
    parser.add_argument('--output', default=str(REPO_ROOT / 'logs' / 'diagnostics'))
    result = capture(parser.parse_args())
    print(json.dumps(result, indent=2))
    return 1 if result['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
