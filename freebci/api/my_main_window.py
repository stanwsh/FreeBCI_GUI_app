from enum import Flag
import sys
import math
import os
import numpy as np
import logging
import pylsl
import time
from functools import partial
from numpy import float64
from freebci import *
import datetime
import win32api
from pyqtgraph.graphicsItems.PlotDataItem import dataType
from freebci.design.main_window_interface import MainWindowInterface
from freebci.api.my_hardware_settings import MyHardwareSettings
from freebci.api.my_channels_electrodes_settings import MyChannels_electrodes_Settings
from freebci.api.my_wifi_connection import MyWifiConnection
from freebci.api.my_diagnostics import MyDiagnostics
from freebci.api.board_worker import BoardOperationWorker
from freebci.api.session_start_worker import SessionStartWorker
from freebci.api.session_view_model import SessionViewModel
from freebci.core import SimulatedBoard
from freebci.core.device import DeviceManager
from freebci.core.history import append_bounded
from freebci.core.packets import PacketLossCounter
from freebci.api.hardware_settings_protocol import HardwareSettingsProtocol
from freebci.api.my_electrodes_position import ElectrodesPosition
from freebci.api.my_serial_connection import MySerialConnection
from freebci.api.my_blueTooth import MyBluetoothConnection
from freebci.api.my_serial_connection_pure import MySerialConnection as MySerialConnectionPure
from freebci.api.my_virtual_connection import MyVirtualConnection
from freebci.api.my_hardware_warn import MyHardwareWarning
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
from freebci.api.myConnectionInfo import HardwareInfo, connectInfo
from freebci.core.control import ControlError, ControlServer
from freebci.core.models import BoardProfile, SessionConfig
from freebci.core.session import SessionController
from brainflow import board_shim, data_filter, exit_codes, ml_model
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import AggOperations, DataFilter, FilterTypes, WindowFunctions
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import multiprocessing
import threading
import mne
import scipy.io
import matplotlib.pyplot as plt
import matplotlib.image as ime
import matplotlib.contour as cot
import numpy as np
import pandas as pd
from queue import Queue
show_page = 1

class MyMainWindow(MainWindowInterface):
    _instance_lock = threading.Lock()
    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(MyMainWindow, '_instance'):
            with MyMainWindow._instance_lock:
                if not hasattr(MyMainWindow, '_instance'):
                    MyMainWindow._instance = MyMainWindow(*args, **kwargs)
        return MyMainWindow._instance

    def __init__(self, parent=None):
        self._chan = 16
        super(MyMainWindow, self).__init__(self._chan)
        self.hardwareInfo = HardwareInfo()
        self.connect_info = connectInfo()
        self.board = None
        self.device_manager = DeviceManager()
        self.board_worker = BoardOperationWorker(self)
        self.board_worker.succeeded.connect(self._on_board_operation_succeeded)
        self.board_worker.failed.connect(self._on_board_operation_failed)
        self.session_controller = None
        self._start_worker = None
        self.control_server = None
        self.control_discovery_path = None
        self.session_view_model = SessionViewModel(
            lambda: self.session_controller,
            lambda: self.myRecording.doc_path,
            self._control_summary,
            self._lsl_summary,
        )
        self.startButton_isclicked = False
        self.startLSLButton_isclicked = False
        self.checkFlag = 0
        self.ts_time = 5
        self.SamplingRate = 250
        self.total_len = 0
        self.pak_count = 0
        self.pak_received = 0
        self.pak_loss = 0
        self.packet_counter = PacketLossCounter()
        self.stop_count = 0
        self.is_startAccelerometer = False
        self.is_startExtrigger = False
        self.is_startBattery = False
        self.start_extri = 0
        self.extri_flag = 1
        self.extri_count = 0
        self.fps_extri = 250
        self.fps_topo = 20
        device = win32api.EnumDisplayDevices()
        settings = win32api.EnumDisplaySettings(device.DeviceName, -1)
        varName = 'DisplayFrequency'
        self.fps_win = getattr(settings, varName)
        self.start_topo = 0
        self.topo_count = 0
        self.topography_path = '.\\Real-time brain_topography.png'
        self.configure_electrodes(self._chan)
        self.data_queue = Queue()
        self.startTIME = 0
        self.LSLnewDataLen = 0
        self.new_data_len = 0
        self.baudRate = '115200'
        self.eeg_scale = 4.5 / float(pow(2, 23) - 1) / 24.0 * 1000000.0
        self.ts_plot_range = int(self.ts_time * self.SamplingRate)
        self.colors = ['r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140), 'r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140), 'r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140), 'r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140), 'r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140), 'r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140), 'r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140), 'r', 'g', 'b', 'y', 'c', 'm', 'w', (210, 180, 140)]
        self.reConBoardMenu()
        self.actionHelp.triggered.connect(self.help_click)
        self.startButton.clicked.connect(self.startButton_click)
        self.actionOpen.triggered.connect(self.open_click)
        self.actionMarker = QtWidgets.QAction('Add Marker', self)
        self.actionMarker.setShortcut('Ctrl+M')
        self.actionMarker.triggered.connect(self.marker_click)
        self.menu_2.addAction(self.actionMarker)
        self.actionDiagnostics = QtWidgets.QAction('Session Diagnostics...', self)
        self.actionDiagnostics.setShortcut('Ctrl+D')
        self.actionDiagnostics.triggered.connect(self.diagnostics_click)
        self.menu_2.addAction(self.actionDiagnostics)
        self.actionDemo = QtWidgets.QAction('Start Demo Session', self)
        self.actionDemo.setShortcut('Ctrl+Shift+D')
        self.actionDemo.triggered.connect(self.demo_click)
        self.menu_2.addAction(self.actionDemo)
        self.diagnostics_window = None
        for i in range(self._chan):
            self.myTimeSeries.my_plot_widgets[i].channelButton.clicked.connect(partial(self.channelButtons_click, i))
            self.myTimeSeries.my_plot_widgets[i].resistancePushButton.clicked.connect(partial(self.resistancePushButtons_click, i))
        self.vert_scale = 200
        self.LSLbufferData1 = []
        self.LSLbufferData2 = []
        self.LSLbufferData3 = []
        self.marker_outlet = None
        self.fftFreqLen = 60
        self.fftuvLen = 2
        self.fftLogMode = True
        self.reConFuncToWidget()
        self._sync_action_states()
        try:
            self._start_control_server()
        except Exception as ex:
            self.control_server = None
            self.myLogger.write('WARNNING: could not start control API: %s' % ex)

    def configure_electrodes(self, channel_count):
        """Build channel names, montage and topography buffers for a board."""
        self._chan = int(channel_count)
        self.chanMatched_index = list(range(self._chan))
        base = 16 if self._chan <= 16 else 32 if self._chan <= 32 else 64
        position_source = ElectrodesPosition()
        names = list(getattr(position_source, 'ElectrodesName_%d' % base))
        positions = list(getattr(position_source, 'ElectrodesPos_%d' % base))
        count = min(self._chan, len(names))
        self.channels = np.array(names[:count])
        self.value = np.array(positions[:count])
        channel_positions = dict(zip(self.channels, self.value))
        self.montage = mne.channels.make_dig_montage(
            ch_pos=channel_positions,
            nasion=[*(5.27205792e-18, 0.0860992398, -0.0401487349)],
            lpa=[*(-0.08609924, -0.0, -0.04014873)],
            rpa=[*(0.08609924, 0.0, -0.04014873)],
        )
        self.info = mne.create_info(
            ch_names=self.channels.tolist(), sfreq=self.SamplingRate, ch_types='eeg'
        )
        rows = {16: 16, 32: 31, 64: 62}.get(self._chan, self._chan)
        columns = 500 if self._chan <= 16 else 1250
        self.Topography_data = [[0 for _ in range(columns)] for _ in range(rows)]

    def reConBoardMenu(self):
        self.actionUSB.triggered.connect(lambda : self.com_click_pure(2023))
        self.actionUSB_2.triggered.connect(lambda : self.com_click_pure(2024))
        self.actionUSB_3.triggered.connect(lambda : self.com_click_pure(2025))
        self.actionUSB_4.triggered.connect(lambda : self.com_click_pure(2026))
        self.actionBluetooth_Serial_Port.triggered.connect(lambda : self.bluetooth_click(2027))
        self.actionBluetooth_Serial_Port_2.triggered.connect(lambda : self.bluetooth_click(2028))
        self.actionBluetooth_Serial_Port_3.triggered.connect(lambda : self.bluetooth_click(2029))
        self.actionBluetooth_Serial_Port_4.triggered.connect(lambda : self.bluetooth_click(2030))
        self.actionUSB_Serial_Port.triggered.connect(lambda : self.com_click_pure(2031))
        self.actionWIFI_2.triggered.connect(lambda : self.wifi_click(2032))
        self.actionUSB_Serial_Port_2.triggered.connect(lambda : self.com_click_pure(2033))
        self.actionWIFI_3.triggered.connect(lambda : self.wifi_click(2034))
        self.actionUSB_Serial_Port_3.triggered.connect(lambda : self.com_click_pure(2035))
        self.actionWIFI_4.triggered.connect(lambda : self.wifi_click(2036))
        self.actionUSB_Serial_Port_4.triggered.connect(lambda : self.com_click_pure(2037))
        self.actionWIFI_5.triggered.connect(lambda : self.wifi_click(2038))
        self.actionUSB_Serial_Port_5.triggered.connect(lambda : self.com_click_pure(2039))
        self.actionWIFI_6.triggered.connect(lambda : self.wifi_click(2040))
        self.actionUSB_Serial_Port_6.triggered.connect(lambda : self.com_click_pure(2041))
        self.actionWIFI_7.triggered.connect(lambda : self.wifi_click(2042))
        self.actionUSB_Serial_Converter.triggered.connect(lambda : self.virtual_click(2043))
        self.actionUSB_Serial_Converter_2.triggered.connect(lambda : self.virtual_click(2044))
        self.actionUSB_Serial_Converter_3.triggered.connect(lambda : self.virtual_click(2045))
        self.actionUSB_Serial_Port_7.triggered.connect(lambda : self.com_click_pure(2046))
        self.actionUSB_Serial_Port_8.triggered.connect(lambda : self.com_click_pure(2048))
        self.actionUSB_Serial_Port_9.triggered.connect(lambda : self.com_click_pure(2050))
        self.actionWIFI_8.triggered.connect(lambda : self.wifi_click(2047))
        self.actionWIFI_9.triggered.connect(lambda : self.wifi_click(2049))
        self.actionWIFI_10.triggered.connect(lambda : self.wifi_click(2051))

    def fft_work(self, bp_nf_data, fft_bound):
        sp = [ [] for row in range(self._chan) ]
        for k in range(self._chan):
            if self.FFTactiveChannels[k] == True:
                sp[k] = DataFilter.perform_fft(bp_nf_data[k][-fft_bound:], 2)
                sp[k] = np.absolute(sp[k]) / (self.SamplingRate * 1.0)
                sp[k][0] = 0.01
                self.myFFTPlot.fft_plot.plot(pen=pg.mkPen(self.colors[k], width=1)).setData(sp[k])

    def refreshBoardMenu(self):
        if self.isSessionOn:
            self.menu.removeAction(self.menuFreeBCI_USB_8_I.menuAction())
            self.menu.removeAction(self.menuFreeBCI_USB_8_II.menuAction())
            self.menu.removeAction(self.menuFreeBCI_USB_16_I.menuAction())
            self.menu.removeAction(self.menuFreeBCI_USB_16_II.menuAction())
            self.menu.removeAction(self.menuFreeBCI_BT_8_I.menuAction())
            self.menu.removeAction(self.menuFreeBCI_BT_8_II.menuAction())
            self.menu.removeAction(self.menuFreeBCI_BT_16_I.menuAction())
            self.menu.removeAction(self.menuFreeBCI_BT_16_II.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_8_I.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_8_II.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_8_III.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_16_I.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_16_II.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_16_III.menuAction())
            self.menu.removeAction(self.menuFreeBCI_USB_24.menuAction())
            self.menu.removeAction(self.menuFreeBCI_USB_32.menuAction())
            self.menu.removeAction(self.menuFreeBCI_USB_64.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_24.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_32.menuAction())
            self.menu.removeAction(self.menuFreeBCI_WiFi_64.menuAction())
            self.actionRelease = QtWidgets.QAction()
            self.actionRelease.setObjectName('actionRelease')
            self.actionRelease.setText('Disconnect')
            self.actionRelease.triggered.connect(self.actionRelease_click)
            self.menu.addAction(self.actionRelease)
        else:
            self.menu.removeAction(self.actionRelease)
            self.menu.addAction(self.menuFreeBCI_USB_8_I.menuAction())
            self.menu.addAction(self.menuFreeBCI_USB_8_II.menuAction())
            self.menu.addAction(self.menuFreeBCI_USB_16_I.menuAction())
            self.menu.addAction(self.menuFreeBCI_USB_16_II.menuAction())
            self.menu.addAction(self.menuFreeBCI_BT_8_I.menuAction())
            self.menu.addAction(self.menuFreeBCI_BT_8_II.menuAction())
            self.menu.addAction(self.menuFreeBCI_BT_16_I.menuAction())
            self.menu.addAction(self.menuFreeBCI_BT_16_II.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_8_I.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_8_II.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_8_III.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_16_I.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_16_II.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_16_III.menuAction())
            self.menu.addAction(self.menuFreeBCI_USB_24.menuAction())
            self.menu.addAction(self.menuFreeBCI_USB_32.menuAction())
            self.menu.addAction(self.menuFreeBCI_USB_64.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_24.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_32.menuAction())
            self.menu.addAction(self.menuFreeBCI_WiFi_64.menuAction())

    def reConFuncToWidget(self):
        self.myTimeSeries.hardwareButton.clicked.connect(self.hardwareButton_click)
        self.myTimeSeries.voltComboBox.activated.connect(self.voltComboBox_click)
        self.myTimeSeries.timeComboBox.activated.connect(self.timeComboBox_click)
        self.myTimeSeries.voltComboBox.setCurrentIndex(2)
        self.myTimeSeries._signal.connect(self.reConChannelButton)
        self.myFFTPlot.freqComboBox.activated.connect(self.freqComboBox_click)
        self.myFFTPlot.uVcomboBox.activated.connect(self.uVcomboBox_click)
        self.myFFTPlot.logComboBox.activated.connect(self.logComboBox_click)
        self.myBrainTopography.chan_electrode_settingspushButton.clicked.connect(self.chan_electrode_settingspushButton_click)
        self.myNetWidget.startLSLButton.clicked.connect(self.startLSLButton_click)
        self.myExtrigger.DateModepushButton.clicked.connect(self.startExtrigger_click)
        self.myAccelerometer.DateModepushButton.clicked.connect(self.startAccelerometer_click)
        self.myBattery.DateModepushButton.clicked.connect(self.startBattery_click)
        for i in range(self._chan):
            self.myTimeSeries.my_plot_widgets[i].channelButton.clicked.connect(partial(self.channelButtons_click, i))
            self.myTimeSeries.my_plot_widgets[i].resistancePushButton.clicked.connect(partial(self.resistancePushButtons_click, i))

    def reConChannelButton(self, chan: int):
        if self.activeChannels[chan] == True:
            self.myTimeSeries.my_plot_widgets[chan].channelButton.clicked.connect(partial(self.channelButtons_click, chan))
            self.myTimeSeries.my_plot_widgets[chan].resistancePushButton.clicked.connect(partial(self.resistancePushButtons_click, chan))

    def freqComboBox_click(self):
        self.fftFreqLen = int(self.myFFTPlot.freqComboBox.currentText())
        self.myLogger.write('self.fftFreqLen: ' + str(self.fftFreqLen))

    def uVcomboBox_click(self):
        if self.myFFTPlot.logComboBox.currentText() == 'Log':
            self.fftuvLen = np.log10(int(self.myFFTPlot.uVcomboBox.currentText()))
        else:
            self.fftuvLen = int(self.myFFTPlot.uVcomboBox.currentText())

    def logComboBox_click(self):
        if self.myFFTPlot.logComboBox.currentText() == 'Log':
            self.fftLogMode = True
            self.fftuvLen = np.log10(int(self.myFFTPlot.uVcomboBox.currentText()))
        else:
            self.fftLogMode = False
            self.fftuvLen = int(self.myFFTPlot.uVcomboBox.currentText())

    def help_click(self):
        help_path = os.path.join(self.parent_path, 'README.md')
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(help_path))
        self.myLogger.write('Help: open README.md.')

    def open_click(self):
        os.startfile(self.myRecording.record_path)

    def bluetooth_click(self, board_id):
        self.stateLabel.setText('Starting bluetooth form...')
        self.stateLabel.repaint()
        self.my_bluetooth_form = MyBluetoothConnection(self.connect_info, board_id, self.myLogger)
        self.my_bluetooth_form.show()
        self.my_bluetooth_form._signal.connect(self.initLayout)
        self.stateLabel.setText('Bluetooth form started.')
        self.connect_info.isbluetooth = True
        self.connect_info.iswifi = False
        self.connect_info.board_id = board_id
        self.connect_info.board = BoardShim(self.connect_info.board_id, BrainFlowInputParams())
        self.connect_info.connect_type = self.connect_info.id_list[self.connect_info.board_id - 2023][2]
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]

    def wifi_click(self, board_id):
        self.stateLabel.setText('Starting WiFi form...')
        self.stateLabel.repaint()
        self.my_wifi_form = MyWifiConnection(self.connect_info, board_id, self.myLogger)
        self.my_wifi_form.show()
        self.my_wifi_form._signal.connect(self.initLayout)
        self.stateLabel.setText('WiFi form started.')
        self.stateLabel.repaint()
        self.connect_info.iswifi = True
        self.connect_info.isbluetooth = False
        self.connect_info.board = BoardShim(self.connect_info.board_id, BrainFlowInputParams())
        self.connect_info.connect_type = self.connect_info.id_list[self.connect_info.board_id - 2023][2]
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]

    def com_click_pure(self, board_id):
        self.stateLabel.setText('Starting Serial form...')
        self.stateLabel.repaint()
        self.my_com_form = MySerialConnectionPure(self.connect_info, board_id, self.myLogger)
        self.my_com_form.show()
        self.my_com_form._signal.connect(self.initLayout)
        self.stateLabel.setText('Serial form started.')
        self.stateLabel.repaint()
        self.connect_info.iswifi = False
        self.connect_info.isbluetooth = False
        self.connect_info.board_id = board_id
        self.connect_info.board = BoardShim(self.connect_info.board_id, BrainFlowInputParams())
        self.connect_info.connect_type = self.connect_info.id_list[self.connect_info.board_id - 2023][2]
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]

    def virtual_click(self, board_id):
        self.my_virtual_form = MyVirtualConnection(self.connect_info, board_id, self.myLogger)
        self.my_virtual_form.show()
        self.my_virtual_form._signal.connect(self.initLayout)
        self.connect_info.board_id = board_id
        self.connect_info.board = BoardShim(self.connect_info.board_id, BrainFlowInputParams())
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]

    def actionRelease_click(self):
        if self.startButton_isclicked == True:
            if not self._confirm_stop():
                return
            self.stop_openbci()
            self.startButton_isclicked = False
            self.startButton.setText('Start Session')
            self.stopThread()
            self.myLogger.write('Data stream stopped.')
        self.device_manager.release()
        self.board = None
        self.connect_info.board = None
        self.isSessionOn = False
        self.hardwareInfo.isSend = False
        self.myLogger.write('Board Session stopped')
        self.changeLayout(0)
        self.refreshBoardMenu()
        self._sync_action_states()
        self.stateLabel.setText('Board Session stopped')
        self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(192, 192, 192)')

    def _board_profile(self):
        row = self.connect_info.id_list[self.connect_info.board_id - 2023]
        return BoardProfile(
            board_id=self.connect_info.board_id,
            name=str(row[0]),
            channels=self._chan,
            sampling_rate=int(self.SamplingRate),
            has_accelerometer=bool(row[9]),
            has_external_trigger=bool(row[10]),
            has_battery=bool(row[11]),
        )

    def initLayout(self, connection_info: connectInfo):
        if isinstance(connection_info, connectInfo):
            self.isSessionOn = True
            self.connect_info = connection_info
            self._chan = self.connect_info.channel_num
            self.board = self.connect_info.board
            self.baudRate = self.connect_info.baudRate
            self.SamplingRate = 250
            if self._chan == 16 and self.hardwareInfo.sendMode != 'FreeBCI' and self.connect_info.isbluetooth == False:
                self.SamplingRate = 125
                self.ts_plot_range = 725
            self.device_manager.adopt(self.board, self._board_profile())
            self.configure_electrodes(self._chan)
            self.activeChannels = [ True for i in range(self._chan) ]
            self.resistanceArray = [ 0 for i in range(self._chan) ]
            self.temp = [ [] for i in range(self._chan) ]
            self.FFTactiveChannels = [ False for i in range(self._chan + 2) ]
            self.resistanceOn = [ False for i in range(self._chan) ]
            self.channals_on = [ False for i in range(self._chan) ]
            eeg_channels = self.board.get_eeg_channels(self.connect_info.board_id)
            other_channels = self.board.get_accel_channels(self.connect_info.board_id)
            other_channels.insert(0, self.board.get_other_channels(self.connect_info.board_id)[0])
            self.channelIndexs = eeg_channels + other_channels
            self.channelNames = [ 'eeg' + str(i + 1) for i in range(self._chan) ] + [ 'other' + str(i + 1) for i in range(4) ]
            self.num_rows = self.board.get_num_rows(self.connect_info.board_id)
            self.data = np.zeros([self.num_rows, 1], dtype=float64)
            self.extri_data = self.data
            self.battery_percentage = self.data
            self.initWidget()
            self.reConFuncToWidget()
            self.startButton.setStyleSheet('font: 12pt "等线"; background-color: rgb(204,255,153)')
            self.changeLayout(2)
            self.refreshBoardMenu()
            self.stateLabel.setText('Session started!')
            if self.connect_info.id_list[self.connect_info.board_id - 2023][9]:
                self.myAccelerometer.DateModepushButton.setEnabled(True)
                self.myAccelerometer.DateModepushButton.setStyleSheet('font: 75 10pt "等线";background-color: rgb(204,255,153)')
                self.myAccelerometer.DateModepushButton.setText('Start Accelerometer')
            else:
                self.myAccelerometer.DateModepushButton.setEnabled(False)
                self.myAccelerometer.DateModepushButton.setText('Start Accelerometer')
            if self.connect_info.id_list[self.connect_info.board_id - 2023][11]:
                self.myBattery.DateModepushButton.setEnabled(True)
                self.myBattery.DateModepushButton.setStyleSheet('font: 75 10pt "等线";background-color: rgb(204,255,153)')
                self.myBattery.DateModepushButton.setText('Start Battery')
            else:
                self.myBattery.DateModepushButton.setEnabled(False)
                self.myBattery.DateModepushButton.setText('Start Battery')
            if self.connect_info.id_list[self.connect_info.board_id - 2023][10]:
                self.myExtrigger.DateModepushButton.setEnabled(True)
                self.myExtrigger.DateModepushButton.setStyleSheet('font: 75 10pt "等线";background-color: rgb(204,255,153)')
                self.myExtrigger.DateModepushButton.setText('Start Extrigger')
            else:
                self.myExtrigger.DateModepushButton.setEnabled(False)
                self.myExtrigger.DateModepushButton.setText('Start Extrigger')
            self._sync_action_states()

    def stopThread(self):
        for attribute in ('timer', 'processor', 'shower'):
            timer = getattr(self, attribute, None)
            if timer is not None:
                timer.stop()
        plot_thread = getattr(self, 'plot_thread', None)
        if plot_thread is not None:
            plot_thread.stop()
            plot_thread.wait(1000)
            self.plot_thread = None

    def closeEvent(self, event):
        try:
            start_worker = getattr(self, '_start_worker', None)
            if start_worker is not None and start_worker.isRunning():
                start_worker.wait(5000)
            if (
                self.session_controller is not None
                or self.startButton_isclicked
            ):
                self.stop_openbci()
                self.stopThread()
            self._stop_control_server()
            self.board_worker.stop()
            self.device_manager.release()
            self.board = None
            event.accept()
            console = getattr(self, 'ConsoleWindow', None)
            if console is not None:
                console.close()
        except Exception as ex:
            logging.exception(ex)

    def _apply_channel_style(self, channel):
        colors = [*('red', 'green', 'blue', '#E3CF57', 'rgb(0,255,255)', 'purple', 'black', 'rgb(210,180,140)')]
        widget = self.myTimeSeries.my_plot_widgets[channel]
        if self.channals_on[channel] == True:
            widget.channelButton.setStyleSheet('width: 30px;height: 30px; border-radius: 15px;font-size: 15px;color: white; background: gray;')
            widget.ischannelClick = True
        else:
            widget.channelButton.setStyleSheet('width: 30px;height: 30px; border-radius: 15px;font-size: 15px;color: white; background: ' + colors[channel % 8] + ';')
            widget.ischannelClick = False

    def _apply_resistance_style(self, channel, enabled):
        widget = self.myTimeSeries.my_plot_widgets[channel]
        if enabled:
            widget.dataLabel.setStyleSheet('font: 8pt "黑体";background:transparent; color: white')
            widget.dataLabelColor = 'white'
            widget.isResistance = False
            widget.resistancePushButton.setStyleSheet('QPushButton {width: 30px;height: 30px;border-radius: 15px;font-size: 15px;color: white;font: 12pt "黑体";background: black ;}')
        else:
            widget.isResistance = True
            widget.resistancePushButton.setStyleSheet('QPushButton {width: 30px;height: 30px;border-radius: 15px;font-size: 15px;color: black;font: 12pt "黑体";background: None ;}')

    def resistancePushButtons_click(self, channel):
        if self.board is None:
            self.stateLabel.setText('Connect to a board first.')
            return
        enabled = not self.resistanceOn[channel]
        command = 'x'
        if self._chan > 16:
            command += ('0' if channel < 9 else '') + str(channel + 1)
        else:
            command += str(HardwareSettingsProtocol.Channel[channel + 1])
        command += '0'
        command += str(HardwareSettingsProtocol.PCAGainProtocol['X24'])
        command += str(HardwareSettingsProtocol.InputTypeProtocol['Normal'])
        command += str(HardwareSettingsProtocol.BiasIncludeProtocol['Yes'])
        command += str(HardwareSettingsProtocol.SRB2Protocol['On'])
        command += str(HardwareSettingsProtocol.SRB1Protocol['Off'])
        command += 'X'
        if enabled:
            if self._chan > 16:
                command += 'z' + ('0' if channel + 1 < 10 else '') + str(channel + 1) + '01Z'
            else:
                command += HardwareSettingsProtocol.ImpedanceOn[channel + 1]
        else:
            command = '"'
            if self._chan > 16:
                command += 'z' + ('0' if channel + 1 < 10 else '') + str(channel + 1) + '00Z'
            else:
                command += HardwareSettingsProtocol.ImpedanceOff[channel + 1]

        self.resistanceOn[channel] = enabled
        self.myLogger.write('sendCommand: ' + command)
        streaming = self.startButton_isclicked

        def operation():
            if streaming:
                self.board.stop_stream()
            try:
                result = self.board.config_board(command)
            finally:
                if streaming:
                    self.board.start_stream()
                    time.sleep(0.5)
            return result

        self._submit_board_operation(
            'resistance:%d:%s' % (channel, 'on' if enabled else 'off'),
            operation,
        )

    def channelButtons_click(self, channel):
        if self.board is None:
            self.stateLabel.setText('Connect to a board first.')
            return
        disabled = not self.channals_on[channel]
        if self._chan > 16:
            command = '"' + (')' if disabled else '(')
            command += ('0' if channel + 1 < 10 else '') + str(channel + 1)
        else:
            command = (
                HardwareSettingsProtocol.ChannelOn[channel + 1]
                if disabled
                else HardwareSettingsProtocol.ChannelOff[channel + 1]
            )
        self.channals_on[channel] = disabled
        self.myLogger.write(
            'FreeBCI_GUI: %s channel %d'
            % ('deactivating' if disabled else 'activating', channel + 1)
        )
        self.myLogger.write('sendCommand: ' + command)
        streaming = self.startButton_isclicked

        def operation():
            if streaming:
                self.board.stop_stream()
            try:
                return self.board.config_board(command)
            finally:
                if streaming:
                    self.board.start_stream()

        self._submit_board_operation('channel:%d' % channel, operation)

    def timeComboBox_click(self):
        if self.myTimeSeries.timeComboBox.currentIndex() == 0:
            self.ts_time = 5
            self.ts_plot_range = 5 * self.SamplingRate
        else:
            self.ts_time = int(str(self.myTimeSeries.timeComboBox.currentText()).split(' ')[0])
            self.ts_plot_range = self.ts_time * self.SamplingRate
        self.myLogger.write(self.ts_plot_range)

    def voltComboBox_click(self):
        vert_scale_str = str(self.myTimeSeries.voltComboBox.currentText())
        if 'Auto1' not in vert_scale_str and 'Auto2' not in vert_scale_str:
            self.vert_scale = int(vert_scale_str.split(' ')[0])
            for i in range(self._chan):
                if self.activeChannels[i]:
                    self.myTimeSeries.my_plot_widgets[i].maxLabel.setText('+' + str(self.vert_scale) + 'uV')
                    self.myTimeSeries.my_plot_widgets[i].minLabel.setText('-' + str(self.vert_scale) + 'uV')
        elif 'Auto1' in vert_scale_str:
            self.vert_scale = -1
        elif 'Auto2' in vert_scale_str:
            self.vert_scale = -2

    def getHardwareInfo(self, hardware_info: HardwareInfo):
        self.hardwareInfo = hardware_info
        self.chanMatched_index = self.hardwareInfo.chanMatched_index
        self.baudRate = self.hardwareInfo.baudRate
        self.SamplingRate = int(self.hardwareInfo.SamplingRate)
        self.info['sfreq'] = self.SamplingRate
        self.myNetWidget.refreshSamplingRate(self.SamplingRate)
        self.ts_plot_range = int(self.ts_time * self.SamplingRate)

    def getConnectInfo(self, connect_info: connectInfo):
        self.connect_info = connect_info
        self.baudRate = self.connect_info.baudRate
        self.board = self.connect_info.board

    def hardwareButton_click(self):
        try:
            if self.startButton_isclicked == False:
                self.hardwareInfo.channel_num = self._chan
                self.hardwareInfo.baudRate = self.baudRate
                self.hardwareInfo.activeChannels = self.activeChannels
                self.hardwareInfo.SamplingRate = self.SamplingRate
                if self._chan == 16 and self.hardwareInfo.sendMode != 'FreeBCI' and self.connect_info.isbluetooth == False:
                    self.hardwareInfo.SamplingRate = self.SamplingRate * 2
                self.my_hardware_form = MyHardwareSettings(self.connect_info, self.hardwareInfo, self.myLogger)
                self.my_hardware_form._signal.connect(self.getHardwareInfo)
                self.my_hardware_form._signal_con.connect(self.getConnectInfo)
                self.my_hardware_form.exec()
            else:
                self.my_hardware_warning = MyHardwareWarning()
                self.my_hardware_warning.label_2.setText(QtCore.QCoreApplication.translate('hardware_warning', 'Streaming needs to be stopped before accessing Hardware Settings'))
                self.my_hardware_warning.exec()
        except Exception as ex:
            self.myLogger.write('Hardware setting error! ')
            logging.exception(ex)

    def chan_electrode_settingspushButton_click(self):
        try:
            if self.startButton_isclicked == False:
                self.hardwareInfo.channel_num = self._chan
                self.hardwareInfo.activeChannels = self.activeChannels
                self.my_chan_electrode_form = MyChannels_electrodes_Settings(self.connect_info, self.hardwareInfo)
                self.my_chan_electrode_form.show()
                self.my_chan_electrode_form._signal.connect(self.getHardwareInfo)
                self.my_chan_electrode_form._signal_con.connect(self.getConnectInfo)
            else:
                self.my_hardware_warning = MyHardwareWarning()
                self.my_hardware_warning.label_2.setText(QtCore.QCoreApplication.translate('hardware_warning', 'Streaming needs to be stopped before accessing Channels-electrodes Settings'))
                self.my_hardware_warning.show()
        except Exception as ex:
            self.myLogger.write('Channels-electrodes setting error! ')
            logging.exception(ex)

    def _submit_board_operation(self, name, operation):
        if self.board is None:
            self.stateLabel.setText('Connect to a board first.')
            return
        self.board_worker.submit(name, operation)

    def _on_board_operation_succeeded(self, name, result):
        if name == 'timing':
            self.myLogger.write(str(result))
        elif name.startswith('data:'):
            mode = name.split(':', 1)[1]
            self.is_startExtrigger = mode == 'External trigger'
            self.is_startAccelerometer = mode == 'Accelerometer'
            self.is_startBattery = mode == 'Battery'
        elif name.startswith('channel:'):
            self._apply_channel_style(int(name.split(':')[1]))
        elif name.startswith('resistance:'):
            _, channel, enabled = name.split(':')
            self._apply_resistance_style(int(channel), enabled == 'on')

    def _on_board_operation_failed(self, name, message):
        self.myLogger.write('WARNNING: board command failed: %s' % message)
        self.stateLabel.setText('Board command failed: %s' % message)
        if name.startswith('channel:'):
            channel = int(name.split(':')[1])
            self.channals_on[channel] = not self.channals_on[channel]
            self._apply_channel_style(channel)
        elif name.startswith('resistance:'):
            _, channel, enabled = name.split(':')
            channel = int(channel)
            self.resistanceOn[channel] = enabled != 'on'
            self._apply_resistance_style(channel, enabled == 'on')
        elif name.startswith('data:'):
            self.is_startExtrigger = False
            self.is_startAccelerometer = False
            self.is_startBattery = False

    def TimingButton_click(self):
        if self.startButton_isclicked:
            self.myLogger.write('Please stop streaming first!')
            return
        time_now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        command = '<' + time_now[2:] + '>'
        self.myLogger.write('sendCommand: ' + command)
        self._submit_board_operation(
            'timing', lambda: self.board.config_board(command)
        )

    def startExtrigger_click(self):
        command = HardwareSettingsProtocol.data_mode['External trigger']
        self.myLogger.write(command)
        self._submit_board_operation(
            'data:External trigger', lambda: self.board.config_board(command)
        )

    def startAccelerometer_click(self):
        command = HardwareSettingsProtocol.data_mode['Accelerometer']
        self.myLogger.write(command)
        self._submit_board_operation(
            'data:Accelerometer', lambda: self.board.config_board(command)
        )

    def startBattery_click(self):
        command = HardwareSettingsProtocol.data_mode['Battery']
        self.myLogger.write(command)
        self._submit_board_operation(
            'data:Battery', lambda: self.board.config_board(command)
        )

    def _ensure_marker_outlet(self):
        if self.marker_outlet is None:
            info = pylsl.StreamInfo(
                'FreeBCI_Markers',
                'Markers',
                1,
                0,
                pylsl.cf_string,
                'FreeBCI_Markers',
            )
            self.marker_outlet = pylsl.StreamOutlet(info)

    def _on_session_marker(self, marker):
        outlet = getattr(self, 'marker_outlet', None)
        if outlet is not None:
            outlet.push_sample([str(marker.get('label', ''))])

    def startLSLButton_click(self):
        try:
            if self.startLSLButton_isclicked == False:
                self.startLSLButton_isclicked = True
                self.myLogger.write('start lsl stream...')
                self.myNetWidget.startLSLButton.setText(' Stop ')
                self.myNetWidget.startLSLButton.setStyleSheet('font: 12pt "黑体";background-color:red')
                self._ensure_marker_outlet()
                for index in (1, 2, 3):
                    if getattr(self.myNetWidget, 'LSLdataType%d' % index) != 'None':
                        streamer = QtCore.QTimer()
                        streamer.timeout.connect(partial(self.sendLSLStream, index))
                        streamer.start(10)
                        setattr(self, 'LSLstreamer%d' % index, streamer)
            else:
                self.startLSLButton_isclicked = False
                self.myLogger.write('close lsl stream.')
                self.myNetWidget.startLSLButton.setText('Start LSL Stream')
                self.myNetWidget.startLSLButton.setStyleSheet('font: 12pt "等线"; background-color: rgb(204,255,153)')
                self.marker_outlet = None
                for index in (1, 2, 3):
                    streamer = getattr(self, 'LSLstreamer%d' % index, None)
                    if streamer is not None:
                        streamer.stop()
                        setattr(self, 'LSLstreamer%d' % index, None)
        except Exception as ex:
            self.myLogger.write('LSL run error! ')
            logging.exception(ex)

    def _begin_session_ui(self):
        self.stateLabel.setText('Data stream started.   samples received: {}'.format(self.total_len))
        self.startButton.setEnabled(True)
        self.startButton.setText('Stop Session')
        self.startButton.setStyleSheet('font: 12pt "黑体";background-color:red')
        self.startButton_isclicked = True
        self.total_len = 0
        self.pak_count = 0
        self.pak_received = 0
        self.pak_loss = 0
        self.packet_counter.reset()
        self.baudRate = self.connect_info.baudRate
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updater)
        self.timer.start(50)
        self.shower = QtCore.QTimer()
        self.shower.timeout.connect(self.shower_fun)
        self.shower.start(50)
        self.data_queue = Queue()
        self.plot_thread = PlotThread(self.data_queue)
        self.plot_thread.update_signal.connect(self.Topo_plot)
        self.plot_thread.start()
        self.processor = QtCore.QTimer()
        self.processor.timeout.connect(self.processor_fun)
        self.processor.start(50)
        self.myLogger.write('Data stream started')
        self._sync_action_states()

    def _on_session_started(self, controller):
        self._start_worker = None
        try:
            self._activate_session(controller)
        except Exception as ex:
            self.myLogger.write('WARNNING: could not publish session: %s' % ex)
            self._on_session_start_failed(str(ex))
            return
        self._begin_session_ui()

    def _on_session_start_failed(self, message):
        worker = self._start_worker
        self._start_worker = None
        if worker is not None:
            try:
                worker.controller.stop()
            except Exception:
                pass
        self.startButton.setEnabled(True)
        self.startButton.setText('Start Session')
        self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')
        self.startButton_isclicked = False
        self.stateLabel.setText('session error: %s' % message)
        self.myLogger.write('WARNNING: session start failed: %s' % message)
        self._sync_action_states()

    def _confirm_stop(self):
        """Ask before finalizing a session that has acquired samples."""
        if self.total_len <= 0:
            return True
        answer = QtWidgets.QMessageBox.question(
            self,
            'Stop session?',
            'Stop acquisition and finalize the current recording?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        return answer == QtWidgets.QMessageBox.Yes

    def startButton_click(self):
        if self.isSessionOn == False:
            self.stateLabel.setText('Connect to a board first.')
            return
        if self.startButton_isclicked == False:
            if self._start_worker is not None:
                return
            self.stateLabel.setText('session starting..........')
            self.stateLabel.repaint()
            self.startButton.setEnabled(False)
            try:
                controller = self._build_session_controller()
            except Exception as ex:
                self._on_session_start_failed(str(ex))
                return
            worker = SessionStartWorker(controller, self)
            worker.succeeded.connect(self._on_session_started)
            worker.failed.connect(self._on_session_start_failed)
            self._start_worker = worker
            worker.start()
            return
        if self.startButton_isclicked == True:
            if not self._confirm_stop():
                return
            self.stop_openbci()
            self.startButton_isclicked = False
            self.total_len = 0
            self.pak_count = 0
            self.pak_received = 0
            self.pak_loss = 0
            self.packet_counter.reset()
            self.stop_count += 1
            self.startButton.setText('Start Session')
            self.stateLabel.setText('Data stream stopped.')
            self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')
            self.stopThread()
            self.myLogger.write('Data stream stopped.')
            self._sync_action_states()

    def Topo_plot(self, Topography_data):
        self.myBrainTopography.plotfig(Topography_data, self.info, self.montage)

    def checkConnection(self):
        self.myLogger.write('NoData Error: Please check connection!')
        self.stop_openbci()
        self.startButton_isclicked = False
        self.startButton.setText('Start Session')
        self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')
        self.stopThread()
        self.stateLabel.setText('Error: Please check connection!')
        self.myLogger.write('Data stream stopped.')

    def sendLSLStream(self, index):
        try:
            buffer_name = 'LSLbufferData%d' % index
            outlet_name = 'LSLoutlet%d' % index
            samples = getattr(self, buffer_name)
            outlet = getattr(self.myNetWidget, outlet_name, None)
            if samples is None or len(samples) == 0 or outlet is None:
                return
            for sample in samples:
                outlet.push_sample(sample)
            setattr(self, buffer_name, [])
        except Exception as ex:
            self.myLogger.write('send LSL stream error!  ' + repr(ex))
            logging.exception(ex)

    def notch_filter(self, val, data, fs):
        DataFilter.perform_bandstop(data, fs, val, 4.0, 2, FilterTypes.BUTTERWORTH, 0.0)
        return data

    def bandpass(self, start, stop, data, fs):
        centerFreq = (start + stop) / 2.0
        bandWidth = stop - start
        DataFilter.perform_bandpass(data, fs, centerFreq, bandWidth, 2, FilterTypes.BUTTERWORTH, 0.0)
        return data

    def updater(self):
        try:
            self.poll_data()
        except Exception as ex:
            self.myLogger.write('poll data error! ')
            self.stateLabel.setText('Poll data error!')
            logging.exception(ex)
            self.stop_openbci()
            self.stopThread()
            self.startButton_isclicked = False
            self.startButton.setText('Start Session')
            self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')

    def processor_fun(self):
        try:
            if self.data.shape[1] < self.SamplingRate * 3:
                return
            start_time = datetime.datetime.now()
            fft_len_dict = {'125': 128, '250': 256, '500': 512, '1000': 1024, '2000': 2048, '4000': 4096, '8000': 8192, '16000': 16384}
            fft_bound = int(fft_len_dict[str(self.SamplingRate)])
            t_data = self.data[1:, -self.SamplingRate * 3:]
            del fft_len_dict
            t_data = np.array(t_data, dtype=float64)
            nf_data = [ [] for row in range(self._chan) ]
            bp_nf_data = [ [] for row in range(self._chan) ]
            notch_text = self.NotchComboBox.currentText()
            if notch_text != 'None':
                notch_text = str(notch_text.split(' ')[0])
                notch_num = int(notch_text)
                for i in range(self._chan):
                    nf_data[i] = self.notch_filter(notch_num, t_data[i], self.SamplingRate)
            else:
                for i in range(self._chan):
                    nf_data[i] = t_data[i]
            bp_text = self.BPFiltComboBox.currentText()
            if bp_text != 'None':
                bp_text = bp_text.split(' ')
                bp_low_bound = int(bp_text[0])
                bp_high_bound = int(bp_text[2])
                for i in range(self._chan):
                    bp_nf_data[i] = self.bandpass(bp_low_bound, bp_high_bound, nf_data[i], self.SamplingRate)
            else:
                for i in range(self._chan):
                    bp_nf_data[i] = nf_data[i]
            if self.is_myFFTPlot:
                sp = [ [] for row in range(self._chan) ]
                freq = [ [] for row in range(self._chan) ]
                fft_len = 8
                min_y = 0
                self.myFFTPlot.fft_plot.clear()
                if self.fftLogMode:
                    self.myFFTPlot.fft_plot.setLogMode(False, True)
                else:
                    self.myFFTPlot.fft_plot.setLogMode(False, False)
                self.myFFTPlot.fft_plot.setXRange(0.01, self.fftFreqLen + 3, padding=0)
                self.myFFTPlot.fft_plot.setYRange(-1, self.fftuvLen, padding=0.05)
                self.myFFTPlot.fft_plot.setLabel('bottom', 'Frequency(Hz)')
                self.myFFTPlot.fft_plot.setLabel('left', 'Amplitude(uV)')
                self.myFFTPlot.fft_plot.showGrid(x=True, y=True)
                for k in range(self._chan):
                    if self.FFTactiveChannels[k] == True:
                        sp[k] = DataFilter.perform_fft(bp_nf_data[k][-fft_bound:], 2)
                        sp[k] = np.absolute(sp[k]) / (self.SamplingRate * 1.0)
                        sp[k][0] = 0.01
                        self.myFFTPlot.fft_plot.plot(pen=pg.mkPen(self.colors[k], width=1)).setData(sp[k])
                if self.FFTactiveChannels[self._chan] == True:
                    for k in range(self._chan):
                        self.FFTactiveChannels[k] = True
                    self.FFTactiveChannels[self._chan] = False
            bandsList = [[0.5, 4], [4, 8], [8, 13], [13, 32], [32, 100]]
            bands = [ 0 for i in range(len(bandsList)) ]
            if self.is_myBandPower:
                tmp = []
                for i in range(self._chan):
                    if self.channals_on[i] == False:
                        tmp.append(i)
                band_data = np.array(bp_nf_data[0:self._chan])[:, -int(fft_bound):]
                bands = DataFilter.get_standard_powers(np.array(band_data), tmp, self.SamplingRate, False)
                target = [ round(np.sqrt(bands[i]), 3) for i in range(5) ]
                bg1 = pg.BarGraphItem(x=[*(1, 2, 3, 4, 5)], y1=target, width=0.6, brushes=[*('b', 'c', 'g', 'y', 'r')])
                self.myBandPower.band_plot.clear()
                waves_xax = self.myBandPower.band_plot.getAxis('bottom')
                waves_xax.setTicks([list(zip(range(6), ('', 'Delta\n1-4Hz', 'Theta\n4-8Hz', 'Alpha\n8-13Hz', 'Beta\n13-30Hz', 'Gama\n30-55Hz')))])
                self.myBandPower.band_plot.setLabel('bottom', 'EEG Power Bands')
                self.myBandPower.band_plot.setLabel('left', 'Power——(uV)^2/Hz')
                self.myBandPower.band_plot.setXRange(1, 5, padding=0.1)
                self.myBandPower.band_plot.addItem(bg1)
                self.myBandPower.band_plot.showGrid(x=True, y=True)
            end_time = datetime.datetime.now()
            if (end_time - start_time).microseconds > 150000:
                self.myLogger.write(str((end_time - start_time).microseconds) + 'processer!!')
        except Exception as ex:
            self.myLogger.write('Updater error!')
            logging.exception(ex)
            self.stopThread()
            self.stop_openbci()
            self.startButton_isclicked = False
            self.startButton.setText('Start Session')
            self.stateLabel.setText('Updater stream error! Data stream stopped!')
            self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')

    def shower_fun(self):
        try:
            if self.data.shape[1] < self.SamplingRate:
                return
            start_time = datetime.datetime.now()
            fft_len_dict = {'125': 128, '250': 256, '500': 512, '1000': 1024, '2000': 2048, '4000': 4096, '8000': 8192, '16000': 16384}
            fft_bound = int(fft_len_dict[str(self.SamplingRate)])
            t_data = self.data[1:, -int(self.ts_plot_range + self.SamplingRate * 2):]
            t_data = np.array(t_data, dtype=float64)
            nf_data = [ [] for row in range(self._chan) ]
            bp_nf_data = [ [] for row in range(self._chan) ]
            notch_text = self.NotchComboBox.currentText()
            if notch_text != 'None':
                notch_text = str(notch_text.split(' ')[0])
                notch_num = int(notch_text)
                for i in range(self._chan):
                    nf_data[i] = self.notch_filter(notch_num, t_data[i], self.SamplingRate)
            else:
                for i in range(self._chan):
                    nf_data[i] = t_data[i]
            bp_text = self.BPFiltComboBox.currentText()
            if bp_text != 'None':
                bp_text = bp_text.split(' ')
                bp_low_bound = int(bp_text[0])
                bp_high_bound = int(bp_text[2])
                for i in range(self._chan):
                    bp_nf_data[i] = self.bandpass(bp_low_bound, bp_high_bound, nf_data[i], self.SamplingRate)
            else:
                for i in range(self._chan):
                    bp_nf_data[i] = nf_data[i]
            bp_nf_data = np.array(bp_nf_data, dtype=float64)
            if self.is_myExtrigger and self.is_startExtrigger:
                if self.extri_count == 0:
                    self.start_extri = time.time()
                while self.extri_flag < len(self.extri_data[0]):
                    if self.extri_data[self._chan + 1][self.extri_flag]:
                        self.myExtrigger.label33.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:lightblue")
                        self.myExtrigger.label33.setText('1')
                        self.myExtrigger.label33.setAlignment(Qt.AlignCenter)
                    else:
                        self.myExtrigger.label33.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:grey")
                        self.myExtrigger.label33.setText('0')
                        self.myExtrigger.label33.setAlignment(Qt.AlignCenter)
                    if self.extri_data[self._chan + 2][self.extri_flag]:
                        self.myExtrigger.label34.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:lightgreen")
                        self.myExtrigger.label34.setText('1')
                        self.myExtrigger.label34.setAlignment(Qt.AlignCenter)
                    else:
                        self.myExtrigger.label34.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:grey")
                        self.myExtrigger.label34.setText('0')
                        self.myExtrigger.label34.setAlignment(Qt.AlignCenter)
                    if self.extri_data[self._chan + 3][self.extri_flag]:
                        self.myExtrigger.label35.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:lightpurple")
                        self.myExtrigger.label35.setText('1')
                        self.myExtrigger.label35.setAlignment(Qt.AlignCenter)
                    else:
                        self.myExtrigger.label35.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:grey")
                        self.myExtrigger.label35.setText('0')
                        self.myExtrigger.label35.setAlignment(Qt.AlignCenter)
                    if self.extri_data[self._chan + 4][self.extri_flag]:
                        self.myExtrigger.label36.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:rgb(0,255,255)")
                        self.myExtrigger.label36.setText('1')
                        self.myExtrigger.label36.setAlignment(Qt.AlignCenter)
                    else:
                        self.myExtrigger.label36.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:grey")
                        self.myExtrigger.label36.setText('0')
                        self.myExtrigger.label36.setAlignment(Qt.AlignCenter)
                    if self.extri_data[self._chan + 5][self.extri_flag]:
                        self.myExtrigger.label37.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:rgb(210,180,140)")
                        self.myExtrigger.label37.setText('1')
                        self.myExtrigger.label37.setAlignment(Qt.AlignCenter)
                    else:
                        self.myExtrigger.label37.setStyleSheet("font: 15pt '黑体';color: black;min-width: 80px; min-height: 80px;max-width:80px; max-height: 80px;border-radius: 40px;  border:1px solid black;background:grey")
                        self.myExtrigger.label37.setText('0')
                        self.myExtrigger.label37.setAlignment(Qt.AlignCenter)
                    self.extri_flag += 1
                self.extri_count += self.extri_flag
                if self.extri_count >= 1000:
                    end_extri = time.time()
                    self.fps_extri = int(self.extri_count / float(end_extri - self.start_extri))
                    self.extri_count = 0
                self.extri_data = np.zeros([self.num_rows, 1], dtype=float64)
                self.extri_flag = 1
            if self.is_myBattery and self.is_startBattery:
                self.hardwareInfo.dataMode = 'Battery'
                battery_get = self.battery_percentage[self._chan + 6][-1] * pow(16, 2) + self.battery_percentage[self._chan + 7][-1]
                battery_percent_volt = battery_get / 500
                battery_percent = battery_percent_volt / 4.2 * 100
                self.myBattery.bat_widget.setValue(int(battery_percent))
                self.myBattery.label.setText(str(int(battery_percent)) + '%')
                self.battery_percentage = np.zeros([self.num_rows, 1], dtype=float64)
            if self.is_myBrainTopography and self.startButton_isclicked == True:
                topodata1 = bp_nf_data[:, -self.ts_plot_range:]
                rows = min(len(self.Topography_data), len(self.chanMatched_index), topodata1.shape[0])
                for j in range(rows):
                    self.Topography_data[j] = topodata1[self.chanMatched_index[j], :]
                self.data_queue.put(self.Topography_data)
            if self.is_myAccelerometer and self.is_startAccelerometer:
                self.myAccelerometer.acc_plot.clear()
                acc_x = round(t_data[self._chan][-1], 3)
                acc_y = round(t_data[self._chan + 1][-1], 3)
                acc_z = round(t_data[self._chan + 2][-1], 3)
                self.myAccelerometer.acc_len_z = acc_z * 60
                self.myAccelerometer.acc_len_x = acc_x * 60
                self.myAccelerometer.acc_len_y = acc_y * 60
                self.myAccelerometer.update()
                self.myAccelerometer.xlabel.setText('    X: ' + str(acc_x))
                self.myAccelerometer.ylabel.setText('    Y: ' + str(acc_y))
                self.myAccelerometer.zlabel.setText('    Z: ' + str(acc_z))
                self.myAccelerometer.acc_plot.showGrid(x=True, y=True, alpha=2.5)
                ax = self.myAccelerometer.acc_plot.getAxis('bottom')
                x_range = range(0, self.ts_plot_range + 1, self.SamplingRate)
                dx = [ (value, str(value)) for value in list(x_range) ]
                ax.setTicks([dx, []])
                ax.setStyle(showValues=False)
                for i in range(3):
                    self.myAccelerometer.acc_plot.plot(pen=pg.mkPen(self.colors[i], width=1)).setData(t_data[self._chan + i][-self.ts_plot_range:])
            RAILED_MAX = self.eeg_scale * float(pow(2, 23))
            if self.is_myTimeSeries:
                t_data = np.array(t_data)[:, -self.ts_plot_range:]
                bp_nf_data = bp_nf_data[:, -self.ts_plot_range:]
                # Draw at most ~2000 points per trace.  Filtering and RMS
                # statistics still use the full-rate block.
                plot_stride = max(1, bp_nf_data.shape[1] // 2000)
                plot_data = bp_nf_data[:, ::plot_stride]
                plot_x = np.arange(0, bp_nf_data.shape[1], plot_stride)
                for j in range(self._chan):
                    if self.activeChannels[j] == False:
                        continue
                    if self.resistanceOn[j] and bp_nf_data[j].shape[-1] > 250:
                        self.temp[j] = bp_nf_data[j]
                        standardDev = np.std(self.temp[j], ddof=1) / 1000000
                        if self.SamplingRate == 500:
                            standardDev = abs(standardDev) * np.sqrt(2.0) / 6e-09 - 3500
                        elif self.SamplingRate <= 250:
                            standardDev = abs(standardDev) * np.sqrt(2.0) / 6e-09 - 2800
                            if standardDev < 0:
                                standardDev = 0
                        else:
                            standardDev = abs(standardDev) * np.sqrt(2.0) / 6e-09 - 3800
                        self.resistanceArray[j] = standardDev
                    self.myTimeSeries.my_plot_widgets[j].ts_plot.clear()
                    self.myTimeSeries.my_plot_widgets[j].ts_plot.showGrid(x=True, y=False, alpha=2.5)
                    self.myTimeSeries.my_plot_widgets[j].ts_plot.setXRange(0, self.ts_plot_range + 1, padding=0)
                    ax = self.myTimeSeries.my_plot_widgets[j].ts_plot.getAxis('bottom')
                    x_range = range(0, self.ts_plot_range + 1, self.SamplingRate)
                    dx = [ (value, str(value)) for value in list(x_range) ]
                    ax.setTicks([dx, []])
                    ax.setStyle(showValues=False)
                    self.myTimeSeries.my_plot_widgets[j].ts_plot.getAxis('left').setStyle(showValues=False)
                    min_data = bp_nf_data[j].min()
                    max_data = bp_nf_data[j].max()
                    bound_data = max(abs(min_data), abs(max_data))
                    y_median = np.median(bp_nf_data[j])
                    if self.vert_scale > 0:
                        self.myTimeSeries.my_plot_widgets[j].ts_plot.setYRange(y_median - self.vert_scale, y_median + self.vert_scale, padding=0.1)
                    elif self.vert_scale == -1:
                        if abs(max_data - min_data) > 10.0:
                            self.myTimeSeries.my_plot_widgets[j].ts_plot.setYRange(-bound_data, bound_data, padding=0)
                            self.myTimeSeries.my_plot_widgets[j].maxLabel.setText('+' + str(format(bound_data, '.2f')) + 'uV')
                            self.myTimeSeries.my_plot_widgets[j].minLabel.setText(str(format(-bound_data, '.2f')) + 'uV')
                        else:
                            self.myTimeSeries.my_plot_widgets[j].maxLabel.setText('+5uV')
                            self.myTimeSeries.my_plot_widgets[j].minLabel.setText('-5uV')
                            self.myTimeSeries.my_plot_widgets[j].ts_plot.setYRange(y_median - 5.0, y_median + 5.0, padding=0)
                    elif self.vert_scale == -2:
                        y_mid = (max_data + min_data) / 2
                        self.myTimeSeries.my_plot_widgets[j].ts_plot.setYRange(y_mid - abs(max_data - min_data) / 2, y_mid + abs(max_data - min_data) / 2, padding=0)
                        if y_mid + abs(max_data - min_data) / 2 > 0:
                            self.myTimeSeries.my_plot_widgets[j].maxLabel.setText('+' + str(format(y_mid + abs(max_data - min_data) / 2, '.2f')) + 'uV')
                        else:
                            self.myTimeSeries.my_plot_widgets[j].maxLabel.setText(str(format(y_mid + abs(max_data - min_data) / 2, '.2f')) + 'uV')
                        if y_mid - abs(max_data - min_data) / 2 > 0:
                            self.myTimeSeries.my_plot_widgets[j].minLabel.setText('+' + str(format(y_mid - abs(max_data - min_data) / 2, '.2f')) + 'uV')
                        else:
                            self.myTimeSeries.my_plot_widgets[j].minLabel.setText(str(format(y_mid - abs(max_data - min_data) / 2, '.2f')) + 'uV')
                    if self.resistanceOn[j]:
                        self.myTimeSeries.my_plot_widgets[j].ts_plot.plot(pen=pg.mkPen(self.colors[j])).setData(plot_x, plot_data[j])
                        self.myTimeSeries.my_plot_widgets[j].dataLabel.setText(f'{round(self.resistanceArray[j] / 1000.0, 3)}kΩ')
                        continue
                    percent = bound_data / RAILED_MAX * 100.0
                    notification = 'Not Railed ' + format(percent, '.2f') + '% '
                    notificationColor = 'white'
                    if percent > 75.0:
                        notification = 'Near Railed ' + format(percent, '.2f') + '% '
                        notificationColor = 'yellow'
                    if percent > 90.0:
                        notification = 'Railed ' + format(percent, '.2f') + '% '
                        notificationColor = 'red'
                    if notificationColor != self.myTimeSeries.my_plot_widgets[j].dataLabelColor:
                        self.myTimeSeries.my_plot_widgets[j].dataLabel.setStyleSheet('font: 8pt "黑体";background:transparent; color:' + notificationColor)
                        self.myTimeSeries.my_plot_widgets[j].dataLabelColor = notificationColor
                    std_data = np.std(bp_nf_data[j][-int(fft_bound):])
                    rms_value = np.sqrt(np.mean(np.square(bp_nf_data[j][-int(fft_bound):])))
                    self.myTimeSeries.my_plot_widgets[j].ts_plot.plot(pen=pg.mkPen(self.colors[j])).setData(plot_x, plot_data[j])
                    self.myTimeSeries.my_plot_widgets[j].dataLabel.setText(f'{round(np.average(bp_nf_data[j]), 3)}uV')
                    self.myTimeSeries.my_plot_widgets[j].dataLabel.setText(notification + format(round(std_data, 2), '.2f') + 'uVrms')
            del t_data
            del bp_nf_data
            del nf_data
            end_time = datetime.datetime.now()
        except Exception as ex:
            self.myLogger.write('Updater error!')
            logging.exception(ex)
            self.stopThread()
            self.stop_openbci()
            self.startButton_isclicked = False
            self.startButton.setText('Start Session')
            self.stateLabel.setText('Updater stream error! Data stream stopped!')
            self.stateLabel.setStyleSheet('')
            self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')

    def _start_control_server(self):
        """Publish one stable loopback endpoint for the application lifetime."""
        self.control_server = ControlServer(
            controller_provider=lambda: self.session_view_model.controller,
            stop_callback=self._request_control_stop,
            shutdown_callback=self._request_control_shutdown,
            start_callback=self._request_control_start,
        )
        self.control_server.start()
        self.control_discovery_path = os.path.join(
            self.myRecording.doc_path, 'control.json'
        )
        self.control_server.write_discovery(self.control_discovery_path)
        self.myLogger.write(
            'FreeBCI: control API %s token %s (discovery %s)'
            % (
                self.control_server.address,
                self.control_server.token,
                self.control_discovery_path,
            )
        )

    def _stop_control_server(self):
        if self.control_server is not None:
            try:
                self.control_server.stop()
            except Exception:
                pass
            self.control_server = None
        self._remove_control_discovery()

    def _request_control_start(self, board):
        """Validate a control-plane board selector and queue the start."""
        selector = str(board).strip()
        if selector != 'demo':
            if not self.isSessionOn or self.connect_info.board is None:
                raise ControlError('board %s is not connected' % selector)
            row = self.connect_info.id_list[self.connect_info.board_id - 2023]
            accepted = (str(self.connect_info.board_id), str(row[0]))
            if selector not in accepted:
                raise ControlError(
                    'board %s is not the connected board (%s)'
                    % (selector, accepted[0])
                )
        if self.startButton_isclicked or self._start_worker is not None:
            raise ControlError('a session is already active or starting')
        QtCore.QMetaObject.invokeMethod(
            self,
            '_start_from_control',
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, selector),
        )

    @QtCore.pyqtSlot(str)
    def _start_from_control(self, board):
        if board == 'demo':
            self.demo_click()
            return
        self.startButton_click()

    def _request_control_stop(self):
        """Queue a control-plane stop onto the GUI thread."""
        QtCore.QMetaObject.invokeMethod(
            self,
            '_stop_from_control',
            QtCore.Qt.QueuedConnection,
        )

    @QtCore.pyqtSlot()
    def _stop_from_control(self):
        if self.session_controller is None:
            return
        self.stop_openbci()
        self.stopThread()
        self.startButton_isclicked = False
        self.startButton.setText('Start Session')
        self.stateLabel.setText('Data stream stopped by control client.')
        self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')

    def _request_control_shutdown(self):
        """Queue a control-plane application shutdown onto the GUI thread."""
        QtCore.QMetaObject.invokeMethod(
            self,
            '_shutdown_from_control',
            QtCore.Qt.QueuedConnection,
        )

    @QtCore.pyqtSlot()
    def _shutdown_from_control(self):
        self.myLogger.write('FreeBCI: shutdown requested by control client')
        self.close()

    def _sync_action_states(self):
        active = self.session_view_model.active
        starting = self._start_worker is not None
        snapshot = self.session_view_model.snapshot()
        state = snapshot.state.value if snapshot is not None else ''
        marker_ok = active and state in ('armed', 'recording')
        self.actionMarker.setEnabled(marker_ok)
        self.actionDemo.setEnabled(not active and not starting)
        self.menu.setEnabled(not active and not starting)
        release = getattr(self, 'actionRelease', None)
        if release is not None:
            release.setEnabled(self.device_manager.connected and not starting)
        hardware_button = getattr(self.myTimeSeries, 'hardwareButton', None)
        if hardware_button is not None:
            hardware_button.setEnabled(not active and not starting)
        channels_button = getattr(self, 'chan_electrode_settingspushButton', None)
        if channels_button is not None:
            channels_button.setEnabled(not active and not starting)

    def marker_click(self):
        if not self.session_view_model.active:
            self.stateLabel.setText('Start a session before adding a marker.')
            return
        try:
            marker = self.session_view_model.add_marker('manual')
        except Exception as ex:
            self.myLogger.write('WARNNING: could not add marker: %s' % ex)
            self.stateLabel.setText('Could not add marker.')
            return
        self.stateLabel.setText(
            'Marker at sample %d.' % marker['sample_index']
        )

    def diagnostics_click(self):
        if self.diagnostics_window is not None and self.diagnostics_window.isVisible():
            self.diagnostics_window.raise_()
            self.diagnostics_window.activateWindow()
            return
        self.diagnostics_window = MyDiagnostics(self.diagnostics_snapshot, self)
        self.diagnostics_window.show()

    def diagnostics_snapshot(self):
        """Collect a read-only status snapshot for the diagnostics dialog."""
        return self.session_view_model.diagnostics()

    def _control_summary(self):
        if self.control_server is None:
            return 'not running'
        control = self.control_server.address
        if self.control_discovery_path:
            control += ' | %s' % self.control_discovery_path
        return control

    def _lsl_summary(self):
        networking = getattr(self, 'myNetWidget', None)
        if networking is None:
            return 'not available'
        running = []
        for index in (1, 2, 3):
            data_type = getattr(networking, 'LSLdataType%d' % index, '')
            if data_type not in ('Time Series', 'FFT', 'Band Power'):
                continue
            streamer = getattr(self, 'LSLstreamer%d' % index, None)
            state = 'running' if streamer is not None and streamer.isActive() else 'stopped'
            name = getattr(networking, 'LSLname%d' % index, 'Stream %d' % index)
            pending = len(getattr(self, 'LSLbufferData%d' % index, []) or [])
            running.append('%s (%s, %s, pending %d)' % (name, data_type, state, pending))
        return '; '.join(running) if running else 'none configured'

    def demo_click(self):
        """Run the GUI against synthetic data when no board is available."""
        if self.isSessionOn or self.startButton_isclicked:
            self.stateLabel.setText('Stop the current session before starting the demo.')
            return
        self.connect_info.board_id = 2037
        self.connect_info.channel_num = 16
        self.connect_info.connect_type = 2
        self.connect_info.baudRate = '2000000'
        self.connect_info.board = SimulatedBoard(16, 250)
        self.initLayout(self.connect_info)
        self.startButton_click()
        self.stateLabel.setText('Demo session - synthetic 16-channel data.')

    def _build_session_controller(self):
        self.data = np.zeros([self.num_rows, 1], dtype=float64)
        self.extri_data = self.data
        self.battery_percentage = self.data
        profile = self.device_manager.profile or self._board_profile()
        config = SessionConfig(
            session_id=datetime.datetime.now().strftime('FreeBCI_%Y%m%d_%H%M%S'),
            board=profile,
            sampling_rate=int(self.SamplingRate),
            output_root=self.myRecording.doc_path,
            channel_count=self._chan,
        )
        # A 16-channel Wi-Fi board resets to 8-channel interleaved frames
        # when its stream starts, so switch it after start_stream().
        post_start_config = ()
        if self.connect_info.connect_type == 1 and self._chan == 16:
            post_start_config = (chr(34) + ',',)
        return SessionController(
            config,
            self.device_manager.gateway(post_start_config=post_start_config),
            marker_callback=self._on_session_marker,
        )

    def _activate_session(self, controller):
        self.session_controller = controller
        self.device_manager.mark_streaming()
        if self.control_server is not None and self.control_discovery_path:
            self.control_server.write_discovery(self.control_discovery_path)
        self.myLogger.write(
            'FreeBCI: session recording started at ' + controller.output_path
        )
        if self.control_server is not None:
            self.myLogger.write(
                'FreeBCI: control API %s (discovery %s)'
                % (self.control_server.address, self.control_discovery_path)
            )

    def start_openbci(self):
        controller = None
        try:
            controller = self._build_session_controller()
            controller.start()
            self._activate_session(controller)
        except Exception as ex:
            self.myLogger.write('WARNNING: could not start board.')
            if controller is not None:
                try:
                    controller.stop()
                except Exception:
                    pass
            if self.control_server is not None and self.control_discovery_path:
                self.control_server.write_discovery(self.control_discovery_path)
            raise ex

    def _remove_control_discovery(self):
        path = self.control_discovery_path
        self.control_discovery_path = None
        if path:
            ControlServer.remove_discovery(path)

    def stop_openbci(self):
        try:
            self.LSLnewDataLen = 0
            if self.session_controller is not None:
                status = self.session_controller.stop()
                self.myLogger.write('FreeBCI: session stopped with status %s' % status.value)
                self.session_controller = None
            self.device_manager.mark_ready()
            if self.control_server is not None and self.control_discovery_path:
                self.control_server.write_discovery(self.control_discovery_path)
            self.data = np.zeros([self.num_rows, 1], dtype=float64)
            self.extri_data = self.data
            self.battery_percentage = self.data
            self.myLogger.write('FreeBCI: stopButton was pressed. Stopping data transfer. wait a few seconds.')
        except Exception as ex:
            self.myLogger.write('WARNNING: could not stop board.')
            logging.exception(ex)

    def fps_real(self):
        if self.is_myTimeSeries:
            if self.is_myExtrigger:
                return min(self.fps_extri, self.fps_win)
            else:
                return self.fps_win

    def poll_data(self):
        try:
            if self.session_controller is None:
                return
            blocks = self.session_controller.drain_display(64)
            snapshot = self.session_controller.snapshot()
            if not blocks:
                error = self.session_controller.check_health()
                if error:
                    raise RuntimeError(error)
                if self.startButton_isclicked and snapshot.seconds_since_block >= 2.0:
                    self.stateLabel.setText(
                        'Waiting for data from the board... no samples for {:.0f} s'.format(
                            snapshot.seconds_since_block
                        )
                    )
                return
            buffer_data = np.concatenate([block.data for block in blocks], axis=1)
            self.new_data_len = buffer_data.shape[1]
            if self.stop_count == 0:
                self.total_len += int(buffer_data.shape[1])
                self.packet_counter.add(buffer_data[0])
                self.pak_count = self.packet_counter.lost
                self.pak_received = self.packet_counter.received
                self.pak_loss = self.packet_counter.percent
                self.stateLabel.setText('Data stream started.   fps: {}    packet loss: {}%    samples received: {}    lost samples: {}'.format(self.fps_real(), round(self.pak_loss, 2), self.total_len, snapshot.lost_samples))
            else:
                self.stop_count -= 1
            if self.startLSLButton_isclicked == True:
                lsl_values = buffer_data[1:self._chan + 1].T
                for index in (1, 2, 3):
                    if getattr(self.myNetWidget, 'LSLdataType%d' % index) == 'Time Series':
                        setattr(self, 'LSLbufferData%d' % index, lsl_values.copy())
            self.new_data_len = 0
            self.checkFlag = 0
            if self.data.shape[1] == 1:
                self.data = buffer_data[:, 1:]
            else:
                self.data = append_bounded(self.data, buffer_data, 60000)
            # The trigger and battery views use the same bounded block history;
            # keeping separate copies doubled memory without adding information.
            self.extri_data = self.data
            self.battery_percentage = self.data
            del buffer_data
        except Exception as ex:
            self.myLogger.write('poll data')
            raise ex

class LogStringAxis(pg.AxisItem):
    def logTickStrings(self, values, scale, spacing):
        estrings = [ '%0.1f' % x for x in 10 ** np.array(values).astype(float) ]
        return estrings


class PlotThread(QThread):
    update_signal = pyqtSignal(object)

    def __init__(self, data_queue):
        super(PlotThread, self).__init__()
        self.data_queue = data_queue
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()
        self.data_queue.put(None)

    def run(self):
        while not self._stop.is_set():
            new_data = self.data_queue.get()
            if new_data is None:
                break
            self.update_signal.emit(new_data)
            self.msleep(50)
