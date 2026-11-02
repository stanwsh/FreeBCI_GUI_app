import serial
import sys
import time
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from freebci.design.serial_connection import Ui_SerialDialog
from freebci.api.hardware_settings_protocol import HardwareSettingsProtocol
from freebci.api.myConnectionInfo import connectInfo
from brainflow import board_shim, data_filter, exit_codes, ml_model
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import AggOperations, DataFilter, FilterTypes, WindowFunctions

class MySerialConnection(QtWidgets.QDialog, Ui_SerialDialog):
    _signal = QtCore.pyqtSignal(connectInfo)
    
    def __init__(self, connect_info, parent=None):
        super(MySerialConnection, self).__init__(parent)
        self.setupUi(self)
        self.setStyleSheet('background-color:#F1F3F5')
        self.scan_click()
        self.scanButton.clicked.connect(self.scan_click)
        self.connectionButton.clicked.connect(self.connect_click)
        self.baudComboBox.activated.connect(self.baud_choose)
        self.connect_info = connect_info
        self.connect_info.baudRate = '115200'
        self.connect_info.board_id = 24
        self.connect_info.channel_num = 32

    
    def scan_click(self):
        self.comboBox.clear()
        self.messageLabel.setText('Scaning Ports......')
        self.messageLabel.repaint()
        if sys.platform.startswith('win'):
            virtual_ports = [ 'COM%s' % (i + 1) for i in (range(32)) ]
        self.ports = []
        for port in virtual_ports:
            try:
                s = serial.Serial(port)
                s.close()
                self.ports.append(port)
            except (OSError, serial.SerialException) as ex:
                pass
        self.ports.reverse()
        self.comboBox.addItems(self.ports)
        self.messageLabel.setText('Scan successfully!')
        self.messageLabel.repaint()

    
    def channel_choose(self):
        self.connect_info.channel_num = int(self.channelComboBox.currentText())

    
    def board_choose(self):
        self.connect_info.board_id = HardwareSettingsProtocol.serial_boards[self.boardComboBox.currentText()]
        channelIndexDict = {
            '8': 0,
            '16': 1,
            '24': 2,
            '32': 3,
            '56': 4,
            '64': 5,
            '80': 6,
            '128': 7 }
        self.connect_info.channel_num = int(HardwareSettingsProtocol.boards_channel[self.boardComboBox.currentText()])
        self.channelComboBox.setCurrentIndex(int(channelIndexDict[str(self.connect_info.channel_num)]))

    
    def baud_choose(self):
        self.connect_info.baudRate = self.baudComboBox.currentText()

    
    def connect_click(self):
        self.myLogger.write('channel count set to ' + str(self.connect_info.channel_num))
        self.connect_info.serial_port = str(self.comboBox.currentText())
        self.myLogger.write('FreeBCI Port Name = ' + str(self.connect_info.serial_port))
        try:
            self.messageLabel.setText('Calling initSystem......')
            self.messageLabel.repaint()
            self.myLogger.write('Calling initSystem......')
            self.myLogger.write('board id:' + str(self.connect_info.board_id))
            self.prepare_openbci(2, boardID = self.connect_info.board_id, serial_port = self.connect_info.serial_port, other_info = self.connect_info.baudRate)
            response = self.board.config_board('v')
            if '$' in response:
                self.messageLabel.setText('connection successfully!')
                self.myLogger.write('connection successfully')
            self.myLogger.write('=================================================')
            self.myLogger.write('||             INITIALIZING SYSTEM             ||')
            self.myLogger.write('=================================================')
            self.myLogger.write('Board Information: ')
            self.myLogger.write(response)
            self.connect_info.board = self.board
            self._signal.emit(self.connect_info)
            self.close()
        except Exception as ex:
            self.myLogger.write('serial connect error: ex', ex)
            self.messageLabel.setText('connection failed!')
            raise

    
    def prepare_openbci(self, connect_type, boardID=0, wifi_address=None, wifi_port=0, serial_port=None, other_info='115200'):
        if connect_type == 1:
            try:
                params = BrainFlowInputParams()
                params.ip_port = wifi_port
                params.ip_address = wifi_address
                params.timeout = 3
                board_id = boardID
                self.board = BoardShim(board_id, params)
                self.board.prepare_session()
            except board_shim.BrainFlowError as ex:
                self.board.release_session()
                self.board = BoardShim(5, BrainFlowInputParams())
                raise ex
        elif connect_type == 2:
            try:
                params = BrainFlowInputParams()
                params.serial_port = serial_port
                params.timeout = 3
                params.other_info = other_info
                board_id = boardID
                self.board = BoardShim(board_id, params)
                self.board.prepare_session()
                self.myLogger.write('send g..........')
                self.board.config_board('g')
                time.sleep(0.2)
            except board_shim.BrainFlowError as ex:
                self.board.release_session()
                self.board = BoardShim(5, BrainFlowInputParams())
                raise ex


