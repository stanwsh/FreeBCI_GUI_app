import time
from serial.tools import list_ports
from freebci.api.hardware_settings_protocol import HardwareSettingsProtocol
from freebci.design.bluetooth_connection import Ui_BluetoothDialog
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from brainflow import board_shim, data_filter, exit_codes, ml_model
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import AggOperations, DataFilter, FilterTypes, WindowFunctions
from freebci.api.myConnectionInfo import connectInfo
from PyQt5.QtCore import Qt

class MyBluetoothConnection(QtWidgets.QDialog, Ui_BluetoothDialog):
    _signal = QtCore.pyqtSignal(connectInfo)
    
    def __init__(self, connect_info, board_id, Logger, parent=None):
        super(MyBluetoothConnection, self).__init__(parent)
        self.setupUi(self)
        self.setStyleSheet('background-color:#F1F3F5')
        self.scan_click()
        self.scanButton.clicked.connect(self.scan_click)
        self.connectionButton.clicked.connect(self.connect_click)
        self.connect_info = connect_info
        self.myLogger = Logger
        self.connect_info.baudRate = '921600'
        self.connect_info.board_id = board_id
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]
        self.lineEdit.setText(str(self.connect_info.channel_num))
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setAlignment(Qt.AlignCenter)
        self.comboBox.setEditable(True)
        self.L1 = self.comboBox.lineEdit()
        self.L1.setAlignment(Qt.AlignCenter)
        self.baudComboBox.setEditable(True)
        self.L2 = self.baudComboBox.lineEdit()
        self.L2.setAlignment(Qt.AlignCenter)

    
    def scan_click(self):
        self.comboBox.clear()
        self.messageLabel.setText('Scaning Ports......')
        self.messageLabel.repaint()
        self.ports = [port.device for port in list_ports.comports()]
        self.ports.reverse()
        self.comboBox.addItems(self.ports)
        self.messageLabel.setText('Scan successfully!')
        self.messageLabel.repaint()

    
    def connect_click(self):
        chosed_port = str(self.comboBox.currentText())
        self.myLogger.write(chosed_port)
        try:
            self.messageLabel.setText('Bluetooth scanning...')
            self.messageLabel.repaint()
            self.prepare_openbci(2, boardID = self.connect_info.board_id, serial_port = chosed_port, other_info = self.connect_info.baudRate)
            response = self.board.config_board('v')
            response = self.board.config_board(',')
            self.messageLabel.setText('connection successfully!')
            self.myLogger.write('connection successfully')
            self.myLogger.write('=================================================')
            self.myLogger.write('||             INITIALIZING SYSTEM             ||')
            self.myLogger.write('=================================================')
            self.connect_info.board = self.board
            self._signal.emit(self.connect_info)
            self.close()
        except Exception as ex:
            self.myLogger.write('bluetooth connect error: ex' + str(ex))
            self.messageLabel.setText('connection failed!')
            raise

    
    def prepare_openbci(self, connect_type, boardID=0, wifi_address=None, wifi_port=0, serial_port=None, other_info='921600'):
        if connect_type == 1:
            try:
                params = BrainFlowInputParams()
                params.ip_port = wifi_port
                params.ip_address = wifi_address
                params.timeout = 3
                self.connect_info.board_id = boardID
                self.board = BoardShim(self.connect_info.board_id, params)
                self.myLogger.write('preparing......')
                self.board.prepare_session()
                self.myLogger.write('prepared')
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


