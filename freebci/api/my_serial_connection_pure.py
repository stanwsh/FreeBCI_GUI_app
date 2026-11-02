import time
from serial.tools import list_ports
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from freebci.design.serial_connection import Ui_SerialDialog
from freebci.api.hardware_settings_protocol import HardwareSettingsProtocol
from freebci.api.myConnectionInfo import connectInfo
from brainflow import board_shim, data_filter, exit_codes, ml_model
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import AggOperations, DataFilter, FilterTypes, WindowFunctions

class MySerialConnection(QtWidgets.QDialog, Ui_SerialDialog):
    _signal = QtCore.pyqtSignal(connectInfo)
    
    def __init__(self, connect_info, board_id, Logger, parent=None):
        super(MySerialConnection, self).__init__(parent)
        self.setupUi(self)
        self.setStyleSheet('background-color:#F1F3F5')
        self.scan_click()
        self.connectionButton.clicked.connect(self.connect_click)
        self.connect_info = connect_info
        self.myLogger = Logger
        self.connect_info.board_id = board_id
        self.connect_info.baudRate = '115200'
        self.baud_read = self.connect_info.id_list[board_id - 2023][3]
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]

    
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
            if self.connect_info.channel_num == 16:
                type_change = chr(34) + ','
                res6 = self.board.config_board(type_change)
            baud_dict = {
                '115200': 0,
                '921600': 1,
                '2000000': 2,
                '3000000': 3,
                '6040000': 4 }
            baud_command = chr(34) + '_' + str(baud_dict[self.connect_info.id_list[self.connect_info.board_id - 2023][3]])
            res5 = self.board.config_board(baud_command)
            self.board.release_session()
            self.board = BoardShim(5, BrainFlowInputParams())
            self.connect_info.baudRate = self.baud_read
            self.prepare_openbci(2, boardID = self.connect_info.board_id, serial_port = self.connect_info.serial_port, other_info = self.connect_info.baudRate)
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


