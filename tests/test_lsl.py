"""Unit tests for the LSL fan-out path."""

from types import SimpleNamespace
from unittest import TestCase

import numpy as np

from freebci.api.my_main_window import MyMainWindow


class _Logger:
    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)


class _Outlet:
    def __init__(self):
        self.samples = []

    def push_sample(self, sample):
        self.samples.append(sample)


class TestLslFanOut(TestCase):
    def test_pushes_each_buffered_sample_to_its_own_outlet(self):
        window = SimpleNamespace(
            LSLbufferData1=np.arange(6, dtype=float).reshape(2, 3),
            LSLbufferData2=np.arange(6, 12, dtype=float).reshape(2, 3),
            myNetWidget=SimpleNamespace(LSLoutlet1=_Outlet(), LSLoutlet2=_Outlet(), LSLoutlet3=None),
            myLogger=_Logger(),
        )

        MyMainWindow.sendLSLStream(window, 1)
        MyMainWindow.sendLSLStream(window, 2)

        self.assertEqual(len(window.myNetWidget.LSLoutlet1.samples), 2)
        self.assertEqual(len(window.myNetWidget.LSLoutlet2.samples), 2)
        np.testing.assert_array_equal(window.myNetWidget.LSLoutlet1.samples[1], [3, 4, 5])
        self.assertEqual(window.LSLbufferData1, [])

    def test_empty_buffer_is_ignored(self):
        window = SimpleNamespace(
            LSLbufferData1=[],
            myNetWidget=SimpleNamespace(LSLoutlet1=_Outlet()),
            myLogger=_Logger(),
        )

        MyMainWindow.sendLSLStream(window, 1)

        self.assertEqual(window.myNetWidget.LSLoutlet1.samples, [])
