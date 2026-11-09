"""Inspect saved EEG for constant runs and ADC-limit values without modifying it.

Rail classification assumes ADS1299 scaling in microvolts, 4.5 V reference,
and the selected gain (24 by default). This is a hypothesis check, not board
configuration readback. Saved timestamps are synthesized, so they cannot be
used to measure network jitter or reconstruct missing transport packets.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


class ChannelStats:
    def __init__(self, name, negative_rail, positive_rail):
        self.name = name
        self.negative_rail = negative_rail
        self.positive_rail = positive_rail
        self.count = self.invalid = self.negative = self.positive = 0
        self.minimum = self.maximum = None
        self.previous = None
        self.run_start = self.run_count = self.longest_count = self.longest_start = 0
        self.longest_value = None

    def add(self, value):
        index = self.count
        self.count += 1
        if not math.isfinite(value):
            self.invalid += 1
            self.previous = None
            self.run_count = 0
            return
        self.minimum = value if self.minimum is None else min(value, self.minimum)
        self.maximum = value if self.maximum is None else max(value, self.maximum)
        # CSV has six decimal places: allow its rounding error, never rtol.
        self.negative += abs(value - self.negative_rail) <= 0.000001
        self.positive += abs(value - self.positive_rail) <= 0.000001
        if self.previous is not None and value == self.previous:
            self.run_count += 1
        else:
            self.run_start, self.run_count = index, 1
        self.previous = value
        if self.run_count > self.longest_count:
            self.longest_count = self.run_count
            self.longest_start = self.run_start
            self.longest_value = value

    def summary(self, rate):
        return {
            'channel': self.name, 'samples': self.count, 'nonfinite': self.invalid,
            'minimum_uv': self.minimum, 'maximum_uv': self.maximum,
            'negative_rail_samples': self.negative, 'positive_rail_samples': self.positive,
            'rail_percent': 100 * (self.negative + self.positive) / self.count if self.count else 0,
            'longest_constant': {
                'start_sample': self.longest_start, 'samples': self.longest_count,
                'seconds_at_configured_rate': self.longest_count / rate,
                'value_uv': self.longest_value,
            },
            'tail_constant_start_sample': self.run_start if self.run_count else None,
        }


def analyze(session_dir, gain=24):
    if not math.isfinite(gain) or gain <= 0:
        raise ValueError('gain must be positive and finite')
    path = Path(session_dir)
    manifest = json.loads((path / 'manifest.json').read_text(encoding='utf-8'))
    rate = float(manifest['sampling_rate'])
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError('manifest sampling_rate must be positive and finite')
    scale = 4_500_000 / gain / (2**23 - 1)
    negative_rail, positive_rail = -2**23 * scale, (2**23 - 1) * scale
    paths = sorted((p for p in path.glob('*.csv') if p.stem.isdigit()), key=lambda p: int(p.stem))
    if not paths:
        raise ValueError('no numbered CSV files found')
    columns = None
    stats = []
    checks = []
    expected_hashes = {entry['file']: entry.get('sha256') for entry in manifest.get('files', [])}
    for csv_path in paths:
        with csv_path.open(encoding='utf-8', newline='') as handle:
            reader = csv.reader(handle)
            header = next(reader)
            indices = [i for i, name in enumerate(header) if name.startswith('channel')]
            names = [header[i] for i in indices]
            if columns is None:
                columns = names
                if len(names) != manifest['channel_count']:
                    raise ValueError('CSV channel count differs from manifest')
                stats = [ChannelStats(name, negative_rail, positive_rail) for name in names]
            elif names != columns:
                raise ValueError('channel columns changed in %s' % csv_path.name)
            for row in reader:
                if len(row) != len(header):
                    raise ValueError('incomplete row in %s at CSV line %d' % (csv_path.name, reader.line_num))
                for channel, index in zip(stats, indices):
                    channel.add(float(row[index]))
        digest = hashlib.sha256()
        with csv_path.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        expected = expected_hashes.get(csv_path.name)
        checks.append({'file': csv_path.name, 'sha256': digest.hexdigest(),
                       'matches_manifest': digest.hexdigest() == expected if expected else None})
    samples = stats[0].count if stats else 0
    return {
        'session': path.name, 'board': manifest.get('board'), 'samples': samples,
        'manifest_sample_count_matches': samples == manifest.get('sample_count'),
        'missing_manifest_files': sorted(set(expected_hashes) - {p.name for p in paths}),
        'configured_rate_hz': rate, 'sample_seconds_at_configured_rate': samples / rate,
        'manifest_status': manifest.get('status'),
        'manifest_lost_samples': manifest.get('lost_samples'),
        'transport_loss_note': 'manifest lost_samples counts recording-index gaps; transport loss cannot be established from these CSVs',
        'rail_assumption': {'reference_volts': 4.5, 'gain': gain, 'units': 'microvolts',
                            'negative_rail_uv': negative_rail, 'positive_rail_uv': positive_rail},
        'files': checks, 'channels': [s.summary(rate) for s in stats],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session_dir')
    parser.add_argument('--gain', type=float, default=24, help='assumed SDK conversion gain, not hardware readback')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = analyze(args.session_dir, args.gain)
    if args.json:
        print(json.dumps(result, indent=2, allow_nan=False))
    else:
        print('%s: %d samples at configured %.0f Hz' % (result['session'], result['samples'], result['configured_rate_hz']))
        print('ADC-limit hypothesis: 4.5 V reference, gain %.0f, microvolts' % args.gain)
        print('Channel     Rail %%   Longest identical run (samples / seconds)   Value (uV)')
        for channel in result['channels']:
            run = channel['longest_constant']
            print('%-11s %6.1f   %8d / %8.3f at sample %-8d %s' % (
                channel['channel'], channel['rail_percent'], run['samples'],
                run['seconds_at_configured_rate'], run['start_sample'], run['value_uv']))
        print(result['transport_loss_note'])
        print('Manifest sample count matches: %s' % result['manifest_sample_count_matches'])
        for file in result['files']:
            print('%s hash matches manifest: %s' % (file['file'], file['matches_manifest']))
        if result['missing_manifest_files']:
            print('Missing files: %s' % ', '.join(result['missing_manifest_files']))


if __name__ == '__main__':
    main()
