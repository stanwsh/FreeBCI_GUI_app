import time
import upnpclient
from urllib.parse import urlparse
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from freebci.design.wifi_connection import Ui_wifiDialog
from freebci.api.myConnectionInfo import connectInfo
from freebci.api.hardware_settings_protocol import HardwareSettingsProtocol
from brainflow import board_shim, data_filter, exit_codes, ml_model
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import AggOperations, DataFilter, FilterTypes, WindowFunctions
from PyQt5.QtCore import Qt

class MyWifiConnection(QtWidgets.QDialog, Ui_wifiDialog):
    _signal = QtCore.pyqtSignal(connectInfo)
    
    def __init__(self, connect_info, board_id, Logger, parent=None):
        super(MyWifiConnection, self).__init__(parent)
        self.setupUi(self)
        self.connectButton.clicked.connect(self.connect_click)
        self.searchButton.clicked.connect(self.search_click)
        self.STA_ip_address = 0
        self.connect_info = connect_info
        self.myLogger = Logger
        self.connect_info = connect_info
        self.connect_info.board_id = board_id
        self.connect_info.wifi_address = '192.168.4.1'
        self.connect_info.wifi_port = 8899
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]
        self.lineEdit_3.setText(str(self.connect_info.channel_num))
        self.lineEdit_3.setReadOnly(True)
        self.lineEdit_3.setAlignment(Qt.AlignCenter)
        self.lineEdit_2.setAlignment(Qt.AlignCenter)
        self.lineEdit.setAlignment(Qt.AlignCenter)

    
    def search_click(self):
        devices = upnpclient.discover()
        device_type = 'urn:schemas-upnp-org:device:Basic:1'
        found_devices = [ device for device in devices if device.device_type == device_type ]
        i = 0
        for device in found_devices:
            self.lineEdit.clear()
            location_url = device.location
            parsed_url = urlparse(location_url)
            ip_address = parsed_url.hostname
            scroll_layout = QtWidgets.QVBoxLayout(self.widget)
            self.button = QtWidgets.QPushButton(f'''Button {i + 1}''')
            i += 1
            self.button.clicked.connect(self.buttonClicked)
            scroll_layout.addWidget(self.button)
            self.button.setText(f'''{device.serial_number}''')
            self.STA_ip_address = ip_address

    
    def buttonClicked(self):
        self.lineEdit.setText(str(self.STA_ip_address))

    
    def connect_click(self):
        try:
            self.myLogger.write('channel count set to ' + str(self.connect_info.channel_num))
            self.connect_info.wifi_address = str(self.lineEdit.text())
            self.connect_info.wifi_port = int(self.lineEdit_2.text())
            self.myLogger.write('Networking: [IP]: ' + str(self.connect_info.wifi_address) + ' [Port]: ' + str(self.connect_info.wifi_port))
            self.messageLabel.setText('Calling initSystem......')
            self.messageLabel.repaint()
            self.myLogger.write('Calling initSystem......')
            self.myLogger.write('board id: ' + str(self.connect_info.board_id))
            self.prepare_openbci(1, boardID = self.connect_info.board_id, wifi_address = self.connect_info.wifi_address, wifi_port = self.connect_info.wifi_port)
            samplingCommand = '~6'
            response7 = self.board.config_board(samplingCommand)
            response = self.board.config_board('v')
            if self.connect_info.channel_num == 16:
                type_change = chr(34) + ','
                res6 = self.board.config_board(type_change)
            self.myLogger.write('=================================================')
            self.myLogger.write('||             INITIALIZING SYSTEM             ||')
            self.myLogger.write('=================================================')
            self.messageLabel.setText('connection successfully!')
            self.connect_info.board = self.board
            self._signal.emit(self.connect_info)
            self.messageLabel.repaint()
            self.connectButton.repaint()
            self.close()
        except Exception as ex:
            self.messageLabel.setText('connection failed!')
            self.connectButton.setEnabled(True)
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
                time.sleep(0.2)
            except board_shim.BrainFlowError as ex:
                self.board.release_session()
                self.board = BoardShim(5, BrainFlowInputParams())
                raise ex


