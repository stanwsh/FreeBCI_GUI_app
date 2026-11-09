import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from tools.analyze_recording import analyze
from tools.diagnose_wifi import capture
from freebci.core.simulator import SimulatedBoard


class RecordingAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def recording(self, files, rate=2):
        entries = []
        count = 0
        for name, rows in files.items():
            path = self.root / name
            with path.open('w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(['timestamp', 'channel1', 'channel2', '<AUX 0>'])
                writer.writerows([['2026-11-09T19:00:00Z', *row, 0] for row in rows])
            entries.append({'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            count += len(rows)
        (self.root / 'manifest.json').write_text(json.dumps({
            'sampling_rate': rate, 'channel_count': 2, 'sample_count': count,
            'files': entries, 'lost_samples': 0, 'status': 'completed',
        }), encoding='utf-8')

    def test_distinguishes_late_saturation_from_unrelated_flatline(self):
        rail = -187500.022352
        self.recording({'1.csv': [(1, 7), (2, 7), (rail, 7), (rail, 7), (rail, 7)]})
        result = analyze(self.root)
        saturated, flat = result['channels']
        self.assertEqual(saturated['negative_rail_samples'], 3)
        self.assertEqual(saturated['longest_constant']['start_sample'], 2)
        self.assertEqual(saturated['tail_constant_start_sample'], 2)
        self.assertEqual(saturated['longest_constant']['seconds_at_configured_rate'], 1.5)
        self.assertEqual(flat['rail_percent'], 0)
        self.assertEqual(flat['longest_constant']['samples'], 5)
        self.assertTrue(result['manifest_sample_count_matches'])
        self.assertTrue(result['files'][0]['matches_manifest'])

    def test_runs_cross_file_boundaries_in_numeric_order(self):
        self.recording({'10.csv': [(3, 0), (4, 0)], '2.csv': [(2, 0), (3, 0)],
                        '1.csv': [(1, 0), (2, 0)]})
        result = analyze(self.root)
        self.assertEqual([f['file'] for f in result['files']], ['1.csv', '2.csv', '10.csv'])
        self.assertEqual(result['channels'][1]['longest_constant']['samples'], 6)
        self.assertEqual(result['channels'][0]['longest_constant']['samples'], 2)
        self.assertEqual(result['channels'][0]['longest_constant']['start_sample'], 1)

    def test_nan_breaks_runs_and_json_remains_valid(self):
        self.recording({'1.csv': [(7, float('nan')), (float('nan'), float('inf')), (7, 4)]})
        result = analyze(self.root)
        self.assertEqual(result['channels'][0]['nonfinite'], 1)
        self.assertEqual(result['channels'][0]['longest_constant']['samples'], 1)
        self.assertEqual(result['channels'][1]['nonfinite'], 2)
        json.dumps(result, allow_nan=False)

    def test_gain_assumption_and_precise_rail_tolerance(self):
        self.recording({'1.csv': [(-375000.044703, 375000), (-375000, 374999)]})
        result = analyze(self.root, gain=12)
        self.assertEqual(result['channels'][0]['negative_rail_samples'], 1)
        self.assertEqual(result['channels'][1]['positive_rail_samples'], 1)

    def test_detects_tampering_and_missing_files(self):
        self.recording({'1.csv': [(1, 2)], '2.csv': [(3, 4)]})
        with (self.root / '1.csv').open('a', encoding='utf-8') as handle:
            handle.write('2026-11-09T19:00:00Z,7,8,0\n')
        (self.root / '2.csv').unlink()
        result = analyze(self.root)
        self.assertFalse(result['files'][0]['matches_manifest'])
        self.assertEqual(result['missing_manifest_files'], ['2.csv'])


class WifiProbeTests(unittest.TestCase):
    def args(self, root, mode='normal'):
        return SimpleNamespace(seconds=0.12, output=root, ip='192.168.4.1', port=8899, input_mode=mode)

    def test_releases_board_and_restores_defaults_when_configuration_fails(self):
        with tempfile.TemporaryDirectory() as root:
            board = MagicMock()
            board.config_board.side_effect = [RuntimeError('rejected'), None]
            with patch('brainflow.board_shim.BoardShim'), patch('tools.diagnose_wifi.prepare_wifi_board', return_value=board):
                result = capture(self.args(root, 'shorted'))
            self.assertEqual(result['error'], 'rejected')
            self.assertEqual(board.config_board.call_args.args, ('d',))
            board.release_session.assert_called_once()

    def test_sdk_capture_matches_normal_recording(self):
        with tempfile.TemporaryDirectory() as root:
            board = SimulatedBoard(16, 250)
            with patch('brainflow.board_shim.BoardShim'), patch('tools.diagnose_wifi.prepare_wifi_board', return_value=board):
                result = capture(self.args(root))
            self.assertIsNone(result['error'])
            self.assertEqual(result['status'], 'completed')
            self.assertGreater(result['samples'], 0)
            with np.load(Path(result['output']) / 'sdk_rows.npz') as sdk:
                with (Path(result['recording']) / '1.csv').open() as handle:
                    rows = list(csv.reader(handle))[1:]
                saved = np.array([row[1:] for row in rows], float).T
                np.testing.assert_allclose(saved, sdk['data'][1:20], rtol=0, atol=0.000001)
                self.assertEqual(sum(sdk['block_samples']), result['samples'])

    def test_controlled_inputs_follow_resets_and_discard_transition_samples(self):
        with tempfile.TemporaryDirectory() as root:
            board = MagicMock(wraps=SimulatedBoard(16, 250))
            with patch('brainflow.board_shim.BoardShim'), patch('tools.diagnose_wifi.prepare_wifi_board', return_value=board):
                result = capture(self.args(root, 'shorted'))
            self.assertIsNone(result['error'])
            commands = [call.args[0] for call in board.config_board.call_args_list]
            self.assertLess(commands.index('v'), commands.index('\",'))
            self.assertLess(commands.index('\",'), commands.index('x1061110X'))
            self.assertEqual(commands[-2:], ['xI061110X', 'd'])
            calls = board.mock_calls
            configured = calls.index(unittest.mock.call.config_board('xI061110X'))
            self.assertEqual(calls[configured + 1], unittest.mock.call.get_board_data())
            board.release_session.assert_called_once()


if __name__ == '__main__':
    unittest.main()
