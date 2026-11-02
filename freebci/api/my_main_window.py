from enum import Flag
import sys
import math
import os
import gc
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
from freebci.core.control import ControlServer
from freebci.core.gateway import BrainFlowGateway
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
        self.session_controller = None
        self.control_server = None
        self.startButton_isclicked = False
        self.startLSLButton_isclicked = False
        self.checkFlag = 0
        self.ts_time = 5
        self.SamplingRate = 250
        self.total_len = 0
        self.pak_count = 0
        self.pak_loss = 0
        self.stop_count = 0
        self.buffercount = 0
        self.pak_last = 0
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
        for i in range(self._chan):
            self.myTimeSeries.my_plot_widgets[i].channelButton.clicked.connect(partial(self.channelButtons_click, i))
            self.myTimeSeries.my_plot_widgets[i].resistancePushButton.clicked.connect(partial(self.resistancePushButtons_click, i))
        self.vert_scale = 200
        self.LSLbufferData1 = []
        self.LSLbufferData2 = []
        self.LSLbufferData3 = []
        self.fftFreqLen = 60
        self.fftuvLen = 2
        self.fftLogMode = True
        self.reConFuncToWidget()

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
            self.stop_openbci()
            self.startButton_isclicked = False
            self.startButton.setText('Start Session')
            self.stopThread()
            self.myLogger.write('Data stream stopped.')
        try:
            self.board.release_session()
        except:
            pass
        self.isSessionOn = False
        self.hardwareInfo.isSend = False
        self.myLogger.write('Board Session stopped')
        self.changeLayout(0)
        self.refreshBoardMenu()
        self.stateLabel.setText('Board Session stopped')
        self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(192, 192, 192)')

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
            self.extri_data = np.zeros([self.num_rows, 1], dtype=float64)
            self.topo_data = np.zeros([self.num_rows, 1], dtype=float64)
            self.battery_percentage = np.zeros([self.num_rows, 1], dtype=float64)
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
            if (
                self.session_controller is not None
                or self.control_server is not None
                or self.startButton_isclicked
            ):
                self.stop_openbci()
                self.stopThread()
            if self.board != None:
                self.board.release_session()
                event.accept()
            console = getattr(self, 'ConsoleWindow', None)
            if console is not None:
                console.close()
        except Exception as ex:
            logging.exception(ex)

    def resistancePushButtons_click(self, channel):
        self.resistanceOn[channel] = not self.resistanceOn[channel]
        if self.resistanceOn[channel]:
            command = ''
            command += 'x'
            if self._chan > 16:
                if channel < 9:
                    command += '0' + str(channel + 1)
                else:
                    command += str(channel + 1)
            else:
                command += str(HardwareSettingsProtocol.Channel[channel + 1])
            command += '0'
            command += str(HardwareSettingsProtocol.PCAGainProtocol['X24'])
            command += str(HardwareSettingsProtocol.InputTypeProtocol['Normal'])
            command += str(HardwareSettingsProtocol.BiasIncludeProtocol['Yes'])
            command += str(HardwareSettingsProtocol.SRB2Protocol['On'])
            command += str(HardwareSettingsProtocol.SRB1Protocol['Off'])
            command += 'X'
            if self._chan > 16:
                if self._chan > 16:
                    command += 'z'
                if channel + 1 < 10:
                    command += '0'
                command += str(channel + 1) + '01Z'
            else:
                command += HardwareSettingsProtocol.ImpedanceOn[channel + 1]
            settingCommand = ''
            command = settingCommand + command
            self.myLogger.write('sendCommand: ' + command)
            if self.startButton_isclicked:
                self.board.stop_stream()
            response = self.board.config_board(command)
            time.sleep(0.1)
            if self.startButton_isclicked:
                self.board.start_stream()
                time.sleep(0.5)
            self.myTimeSeries.my_plot_widgets[channel].dataLabel.setStyleSheet('font: 8pt "黑体";background:transparent; color: white')
            self.myTimeSeries.my_plot_widgets[channel].dataLabelColor = 'white'
            self.myTimeSeries.my_plot_widgets[channel].isResistance = False
            self.myTimeSeries.my_plot_widgets[channel].resistancePushButton.setStyleSheet('QPushButton {width: 30px;height: 30px;border-radius: 15px;font-size: 15px;color: white;font: 12pt "黑体";background: black ;}')
        else:
            command = '"'
            if self._chan > 16:
                command += 'z'
                if channel + 1 < 10:
                    command += '0'
                command += str(channel + 1) + '00Z'
            else:
                command += HardwareSettingsProtocol.ImpedanceOff[channel + 1]
            settingCommand = ''
            command = settingCommand + command
            self.myLogger.write('sendCommand: ' + command)
            if self.startButton_isclicked:
                self.board.stop_stream()
            response = self.board.config_board(command)
            if self.startButton_isclicked:
                self.board.start_stream()
            self.myTimeSeries.my_plot_widgets[channel].isResistance = True
            self.myTimeSeries.my_plot_widgets[channel].resistancePushButton.setStyleSheet('QPushButton {width: 30px;height: 30px;border-radius: 15px;font-size: 15px;color: black;font: 12pt "黑体";background: None ;}')

    def channelButtons_click(self, channel):
        if self._chan > 16:
            self.channals_on[channel] = not self.channals_on[channel]
            if self.channals_on[channel]:
                self.myLogger.write('FreeBCI_GUI: deactivating channel ' + str(channel + 1))
                if self.startButton_isclicked:
                    self.board.stop_stream()
                command = '"'
                command += ')'
                if channel + 1 < 10:
                    command += '0' + str(channel + 1)
                else:
                    command += str(channel + 1)
                self.myLogger.write('sendCommand: ' + command)
                response = self.board.config_board(command)
                if self.startButton_isclicked:
                    self.board.start_stream()
            else:
                self.myLogger.write('FreeBCI_GUI: activating channel ' + str(channel + 1))
                if self.startButton_isclicked:
                    self.board.stop_stream()
                command = '"'
                command += '('
                if channel + 1 < 10:
                    command += '0' + str(channel + 1)
                else:
                    command += str(channel + 1)
                self.myLogger.write('sendCommand: ' + command)
                response = self.board.config_board(command)
                if self.startButton_isclicked:
                    self.board.start_stream()
        else:
            self.channals_on[channel] = not self.channals_on[channel]
            if self.channals_on[channel]:
                self.myLogger.write('FreeBCI_GUI: deactivating channel ' + str(channel + 1))
                command = HardwareSettingsProtocol.ChannelOn[channel + 1]
                self.myLogger.write('sendCommand: ' + command)
                if self.startButton_isclicked:
                    self.board.stop_stream()
                response = self.board.config_board(command)
                if self.startButton_isclicked:
                    self.board.start_stream()
            else:
                self.myLogger.write('FreeBCI_GUI: activating channel ' + str(channel + 1))
                command = HardwareSettingsProtocol.ChannelOff[channel + 1]
                self.myLogger.write('sendCommand: ' + command)
                if self.startButton_isclicked:
                    self.board.stop_stream()
                response = self.board.config_board(command)
                if self.startButton_isclicked:
                    self.board.start_stream()
        colors = [*('red', 'green', 'blue', '#E3CF57', 'rgb(0,255,255)', 'purple', 'black', 'rgb(210,180,140)')]
        if self.channals_on[channel] == True:
            self.myTimeSeries.my_plot_widgets[channel].channelButton.setStyleSheet('width: 30px;height: 30px; border-radius: 15px;font-size: 15px;color: white; background: gray;')
            self.myTimeSeries.my_plot_widgets[channel].ischannelClick = True
        else:
            self.myTimeSeries.my_plot_widgets[channel].channelButton.setStyleSheet('width: 30px;height: 30px; border-radius: 15px;font-size: 15px;color: white; background: ' + colors[channel % 8] + ';')
            self.myTimeSeries.my_plot_widgets[channel].ischannelClick = False

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

    def TimingButton_click(self):
        try:
            if self.startButton_isclicked == False:
                time_now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                command = '<' + time_now[2:] + '>'
                self.myLogger.write('sendCommand: ' + command)
                response = self.board.config_board(command)
                self.myLogger.write(response)
            else:
                self.myLogger.write('Please stop streaming first!')
        except Exception as ex:
            self.myLogger.write('Timing error!')
            logging.exception(ex)

    def startExtrigger_click(self):
        self.command = ''
        self.command += HardwareSettingsProtocol.data_mode['External trigger']
        self.myLogger.write(self.command)
        response = self.board.config_board(self.command)
        self.myLogger.write(response)
        self.is_startExtrigger = True
        self.is_startAccelerometer = False
        self.is_startBattery = False

    def startAccelerometer_click(self):
        self.command = ''
        self.command += HardwareSettingsProtocol.data_mode['Accelerometer']
        self.myLogger.write(self.command)
        response = self.board.config_board(self.command)
        self.myLogger.write(response)
        self.is_startAccelerometer = True
        self.is_startExtrigger = False
        self.is_startBattery = False

    def startBattery_click(self):
        self.command = ''
        self.command += HardwareSettingsProtocol.data_mode['Battery']
        self.myLogger.write(self.command)
        response = self.board.config_board(self.command)
        self.myLogger.write(response)
        self.is_startBattery = True
        self.is_startExtrigger = False
        self.is_startAccelerometer = False

    def startLSLButton_click(self):
        try:
            if self.startLSLButton_isclicked == False:
                self.startLSLButton_isclicked = True
                self.myLogger.write('start lsl stream...')
                self.myNetWidget.startLSLButton.setText(' Stop ')
                self.myNetWidget.startLSLButton.setStyleSheet('font: 12pt "黑体";background-color:red')
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
                for index in (1, 2, 3):
                    streamer = getattr(self, 'LSLstreamer%d' % index, None)
                    if streamer is not None:
                        streamer.stop()
                        setattr(self, 'LSLstreamer%d' % index, None)
        except Exception as ex:
            self.myLogger.write('LSL run error! ')
            logging.exception(ex)

    def startButton_click(self):
        try:
            if not self.isSessionOn:
                self.stateLabel.setText('Connect to a board first.')
                return
            if self.isSessionOn == True:
                if self.startButton_isclicked == False:
                    self.stateLabel.setText('session starting..........')
                    self.stateLabel.repaint()
                    self.start_openbci()
                    self.stateLabel.setText('Data stream started.   packet receive: {}'.format(self.total_len))
                    self.startButton.setText('Stop Session')
                    self.startButton.setStyleSheet('font: 12pt "黑体";background-color:red')
                    self.startButton_isclicked = True
                    self.total_len = 0
                    self.pak_count = 0
                    self.pak_loss = 0
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
                else:
                    self.stop_openbci()
                    self.startButton_isclicked = False
                    self.total_len = 0
                    self.pak_count = 0
                    self.pak_loss = 0
                    self.stop_count += 1
                    self.buffercount = 0
                    self.startButton.setText('Start Session')
                    self.stateLabel.setText('Data stream stopped.')
                    self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')
                    self.stopThread()
                    self.myLogger.write('Data stream stopped.')
        except Exception as ex:
            self.myLogger.write('Start stream error!')
            logging.exception(ex)
            self.stop_openbci()
            self.stopThread()
            self.startButton.setText('Start Session')
            self.stateLabel.setText('session error!')
            self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(204,255,153)')

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
                        self.myTimeSeries.my_plot_widgets[j].ts_plot.plot(pen=pg.mkPen(self.colors[j])).setData(bp_nf_data[j])
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
                    self.myTimeSeries.my_plot_widgets[j].ts_plot.plot(pen=pg.mkPen(self.colors[j])).setData(bp_nf_data[j])
                    self.myTimeSeries.my_plot_widgets[j].dataLabel.setText(f'{round(np.average(bp_nf_data[j]), 3)}uV')
                    self.myTimeSeries.my_plot_widgets[j].dataLabel.setText(notification + format(round(std_data, 2), '.2f') + 'uVrms')
            del t_data
            del bp_nf_data
            del nf_data
            gc.collect(generation=1)
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

    def start_openbci(self):
        try:
            time.sleep(0.2)
            self.data = np.zeros([self.num_rows, 1], dtype=float64)
            self.extri_data = np.zeros([self.num_rows, 1], dtype=float64)
            self.topo_data = np.zeros([self.num_rows, 1], dtype=float64)
            self.battery_percentage = np.zeros([self.num_rows, 1], dtype=float64)
            row = self.connect_info.id_list[self.connect_info.board_id - 2023]
            profile = BoardProfile(
                board_id=self.connect_info.board_id,
                name=str(row[0]),
                channels=self._chan,
                sampling_rate=int(self.SamplingRate),
                has_accelerometer=bool(row[9]),
                has_external_trigger=bool(row[10]),
                has_battery=bool(row[11]),
            )
            config = SessionConfig(
                session_id=datetime.datetime.now().strftime('FreeBCI_%Y%m%d_%H%M%S'),
                board=profile,
                sampling_rate=int(self.SamplingRate),
                output_root=self.myRecording.doc_path,
                channel_count=self._chan,
            )
            self.session_controller = SessionController(
                config,
                BrainFlowGateway(self.board, self.connect_info.board_id, self._chan),
            )
            self.session_controller.start()
            self.control_server = ControlServer(
                self.session_controller,
                stop_callback=self._request_control_stop,
            )
            self.control_server.start()
            self.myLogger.write(
                'FreeBCI: session recording started at ' + self.session_controller.output_path
            )
            self.myLogger.write(
                'FreeBCI: control API %s token %s'
                % (self.control_server.address, self.control_server.token)
            )
        except Exception as ex:
            self.myLogger.write('WARNNING: could not start board.')
            if self.control_server is not None:
                try:
                    self.control_server.stop()
                except Exception:
                    pass
                self.control_server = None
            if self.session_controller is not None:
                try:
                    self.session_controller.stop()
                except Exception:
                    pass
                self.session_controller = None
            raise ex

    def stop_openbci(self):
        try:
            self.LSLnewDataLen = 0
            if self.control_server is not None:
                self.control_server.stop()
                self.control_server = None
            if self.session_controller is not None:
                status = self.session_controller.stop()
                self.myLogger.write('FreeBCI: session stopped with status %s' % status.value)
                self.session_controller = None
            self.data = np.zeros([self.num_rows, 1], dtype=float64)
            self.extri_data = np.zeros([self.num_rows, 1], dtype=float64)
            self.topo_data = np.zeros([self.num_rows, 1], dtype=float64)
            self.battery_percentage = np.zeros([self.num_rows, 1], dtype=float64)
            time.sleep(0.2)
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
            if not blocks:
                error = self.session_controller.check_health()
                if error:
                    raise RuntimeError(error)
                return
            buffer_data = np.concatenate([block.data for block in blocks], axis=1)
            self.new_data_len = buffer_data.shape[1]
            self.extri_data = np.append(self.extri_data, buffer_data, axis=1)
            self.battery_percentage = np.append(self.battery_percentage, buffer_data, axis=1)
            if self.stop_count == 0:
                pak_data = list(buffer_data[0])
                temp_len = len(pak_data)
                self.total_len += temp_len
                for pak in range(1, len(pak_data)):
                    if pak_data[pak] < pak_data[pak - 1]:
                        self.pak_count += pak_data[pak] + 255 - pak_data[pak - 1]
                    if pak_data[pak] == pak_data[pak - 1]:
                        self.pak_count += 255
                    if pak_data[pak] > pak_data[pak - 1]:
                        self.pak_count += pak_data[pak] - pak_data[pak - 1] - 1
                if self.buffercount != 0:
                    if pak_data[0] <= self.pak_last:
                        self.pak_count += pak_data[0] + 256 - self.pak_last - 1
                    else:
                        self.pak_count += pak_data[0] - self.pak_last - 1
                self.buffercount += 1
                self.pak_last = pak_data[-1]
                self.pak_loss = 100 * self.pak_count / (self.pak_count + self.total_len)
                self.stateLabel.setText('Data stream started.   fps: {}    packet loss: {}%    packet receive: {}'.format(self.fps_real(), round(self.pak_loss, 2), self.total_len))
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
                self.data = np.append(self.data, buffer_data, axis=1)
            if self.data.shape[1] > 60000:
                self.data = self.data[:, -60000:]
            if self.extri_data.shape[1] > 60000:
                self.extri_data = self.extri_data[:, -60000:]
            if self.battery_percentage.shape[1] > 60000:
                self.battery_percentage = self.battery_percentage[:, -60000:]
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
