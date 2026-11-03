"""Unit tests for the LSL fan-out path."""

from types import SimpleNamespace
from unittest import TestCase

import numpy as np

from freebci.ui.main_window import MainWindow
from freebci.core.lsl_queue import LslSampleQueue


class _Logger:
    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)


class _Outlet:
    def __init__(self):
        self.chunks = []

    def push_chunk(self, chunk):
        self.chunks.append(chunk)


class _MarkerOutlet:
    def __init__(self):
        self.samples = []

    def push_sample(self, sample):
        self.samples.append(sample)


class TestLslFanOut(TestCase):
    def test_pushes_each_queued_sample_to_its_own_outlet(self):
        first = LslSampleQueue()
        first.push(np.arange(6, dtype=float).reshape(2, 3))
        second = LslSampleQueue()
        second.push(np.arange(6, 12, dtype=float).reshape(2, 3))
        window = SimpleNamespace(
            lsl_queues={1: first, 2: second, 3: LslSampleQueue()},
            networking=SimpleNamespace(LSLoutlet1=_Outlet(), LSLoutlet2=_Outlet(), LSLoutlet3=None),
            logger=_Logger(),
        )

        MainWindow.sendLSLStream(window, 1)
        MainWindow.sendLSLStream(window, 2)

        self.assertEqual(len(window.networking.LSLoutlet1.chunks), 1)
        self.assertEqual(len(window.networking.LSLoutlet1.chunks[0]), 2)
        np.testing.assert_array_equal(window.networking.LSLoutlet1.chunks[0][1], [3, 4, 5])
        self.assertEqual(first.pending, 0)

    def test_empty_buffer_is_ignored(self):
        window = SimpleNamespace(
            lsl_queues={1: LslSampleQueue()},
            networking=SimpleNamespace(LSLoutlet1=_Outlet()),
            logger=_Logger(),
        )

        MainWindow.sendLSLStream(window, 1)

        self.assertEqual(window.networking.LSLoutlet1.chunks, [])

    def test_marker_is_pushed_as_a_string_sample(self):
        window = SimpleNamespace(marker_outlet=_MarkerOutlet())
        MainWindow._on_session_marker(window, {"label": "stimulus on"})
        self.assertEqual(window.marker_outlet.samples, [["stimulus on"]])
