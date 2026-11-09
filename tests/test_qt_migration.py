"""Exercise the Qt 6 binding with real widgets, queued signals, and rendering."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.test-tmp' / 'matplotlib'))

from freebci.app import create_application
from freebci.qt import QtCore, QtWidgets
from freebci.ui.main_window import MainWindow
from freebci.ui.hardware_settings import HardwareSettingsDialog
from freebci.ui.channel_settings import ChannelSettingsDialog
from freebci.ui.layout_dialog import LayoutDialog
from freebci.ui.hardware_warning import HardwareWarningDialog
from freebci.ui.serial_connection import SerialConnectionDialog
from freebci.ui.bluetooth_connection import BluetoothConnectionDialog
from freebci.ui.virtual_connection import VirtualConnectionDialog
from freebci.ui.wifi_connection import WifiConnectionDialog
from freebci.version import VERSION


class QtMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_application([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {'FREEBCI_HOME': self.temp.name})
        self.environment.start()
        self.errors = []
        self.hook = patch.object(sys, 'excepthook', lambda kind, value, tb: self.errors.append(str(value)))
        self.hook.start()
        self.window = MainWindow()
        self.window._force_close = True

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.hook.stop()
        self.environment.stop()
        self.temp.cleanup()
        self.assertEqual(self.errors, [], 'Qt callback/paint exceptions')

    def wait_for(self, condition, seconds=6):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.app.processEvents()
            if condition():
                return
            QtCore.QThread.msleep(5)
        self.fail('timed out waiting for Qt event delivery')

    def test_single_binding_defaults_and_all_layouts_render(self):
        self.assertEqual(QtCore.qVersion(), '6.8.3')
        self.assertFalse(any(name == 'PyQt5' or name.startswith('PyQt5.') for name in sys.modules))
        self.assertEqual(self.window.NotchComboBox.currentText(), '60 Hz')
        self.assertEqual(self.window.BPFiltComboBox.currentText(), 'None')
        self.window.show()
        for index in range(1, 9):
            self.window.changeLayout(index)
            self.app.processEvents()
            self.assertFalse(self.window.grab().isNull())
        self.window.time_series.layoutComboBox.activated.emit(0)
        self.window.accelerometer.acc_len_x = 1.5
        self.window.accelerometer.acc_len_y = -2.25
        self.assertFalse(self.window.accelerometer.grab().isNull())

    def test_demo_queued_start_plots_marker_and_finalized_recording(self):
        # Trigger the QAction so the binding's triggered(bool) argument handling
        # and asynchronous start signal are both exercised.
        self.window.actionDemo.trigger()
        self.wait_for(lambda: self.window.startButton_isclicked)
        controller = self.window.session_controller
        self.wait_for(lambda: len(self.window.ts_curves) == 16)
        self.assertGreater(controller.snapshot().sample_count, 0)
        self.window.actionMarker.trigger()
        self.assertEqual(controller.snapshot().markers, 1)
        self.window.time_series.voltComboBox.setCurrentIndex(1)
        self.window.time_series.voltComboBox.activated.emit(1)
        self.assertEqual(self.window.vert_scale, -2)
        # clicked(bool) on the per-channel partial must not become an extra arg.
        self.window.time_series.plot_widgets[0].channelButton.click()
        self.wait_for(lambda: self.window.channals_on[0])
        self.window.stop_openbci()
        self.window.stopThread()
        self.window.startButton_isclicked = False
        manifest = json.loads((Path(controller.output_path) / 'manifest.json').read_text())
        self.assertEqual(manifest['app_version'], VERSION)
        self.assertEqual(manifest['status'], 'completed')
        self.assertGreater(manifest['sample_count'], 0)
        self.assertFalse(controller.acquisition.running)

    def test_settings_and_transport_dialogs_construct_and_deliver_signals(self):
        self.window.hardwareInfo.channel_num = 16
        self.window.hardwareInfo.activeChannels = [True] * 16
        self.window.hardwareInfo.chanMatched_index = list(range(16))
        self.window.connect_info.board_id = 2038
        self.window.connect_info.channel_num = 16
        self.window.connect_info.board = MagicMock()
        logger = MagicMock()
        hardware = HardwareSettingsDialog(self.window.connect_info, self.window.hardwareInfo, logger)
        layout = LayoutDialog(self.window.parent_path)
        warning = HardwareWarningDialog()
        serial = SerialConnectionDialog(self.window.connect_info, 2037, logger)
        bluetooth = BluetoothConnectionDialog(self.window.connect_info, 2029, logger)
        virtual = VirtualConnectionDialog(self.window.connect_info, 2038, logger)
        channel = ChannelSettingsDialog(self.window.connect_info, self.window.hardwareInfo)
        with patch.object(WifiConnectionDialog, 'search_click'):
            wifi = WifiConnectionDialog(self.window.connect_info, 2038, logger)
        dialogs = [hardware, layout, warning, serial, bluetooth, virtual, channel, wifi]
        try:
            calls = []
            hardware._signal.connect(calls.append)
            hardware._signal.emit(self.window.hardwareInfo)
            self.assertEqual(calls, [self.window.hardwareInfo])
            hardware.PCAGainComboBoxs[0].activated.emit(0)
            for combo in (hardware.InputComboBoxs[0], hardware.BiasComboBoxs[0],
                          hardware.SRB1ComboBoxs[0], hardware.SRB2comboBoxs[0],
                          channel.electrodeNameComboBoxs[0]):
                combo.activated.emit(0)
            for dialog in dialogs:
                dialog.show()
                self.app.processEvents()
                self.assertFalse(dialog.grab().isNull())
        finally:
            for dialog in dialogs:
                dialog.close()
