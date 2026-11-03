import serial
import sys
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from freebci.design.virtual_connection import Ui_VirtualDialog
from freebci.core.hardware_settings_protocol import HardwareSettingsProtocol
from freebci.ui.connection_info import ConnectionInfo
from freebci.core.gateway import prepare_serial_board, prepare_wifi_board
from PyQt5.QtCore import Qt

class VirtualConnectionDialog(QtWidgets.QDialog, Ui_VirtualDialog):
    _signal = QtCore.pyqtSignal(ConnectionInfo)
    
    def __init__(self, connect_info, board_id, Logger, parent=None):
        super(VirtualConnectionDialog, self).__init__(parent)
        self.setupUi(self)
        self.setStyleSheet('background-color:#F1F3F5')
        self.connectionButton.clicked.connect(self.connect_click)
        self.connect_info = connect_info
        self.logger = Logger
        self.connect_info.baudRate = '6040000'
        self.connect_info.board_id = board_id
        self.connect_info.channel_num = self.connect_info.id_list[board_id - 2023][8]
        self.lineEdit.setText(str(self.connect_info.id_list[board_id - 2023][0]))
        self.lineEdit_2.setText(str(self.connect_info.id_list[board_id - 2023][8]))
        self.lineEdit.setReadOnly(True)
        self.lineEdit_2.setReadOnly(True)
        self.lineEdit.setAlignment(Qt.AlignCenter)
        self.lineEdit_2.setAlignment(Qt.AlignCenter)

    
    def connect_click(self):
        self.logger.write('channel count set to ' + str(self.connect_info.channel_num))
        self.connect_info.serial_port = ''
        self.logger.write('FreeBCI Port Name = ' + str(self.connect_info.serial_port))
        try:
            self.messageLabel.setText('Calling initSystem......')
            self.messageLabel.repaint()
            self.logger.write('Calling initSystem......')
            self.prepare_openbci(2, boardID = self.connect_info.board_id, serial_port = self.connect_info.serial_port, other_info = self.connect_info.baudRate)
            response = self.board.config_board('v')
            if '$' in response:
                self.messageLabel.setText('connection successfully!')
                self.logger.write('connection successfully')
            self.logger.write('=================================================')
            self.logger.write('||             INITIALIZING SYSTEM             ||')
            self.logger.write('=================================================')
            self.logger.write('Board Information: ')
            self.logger.write(response)
            self.connect_info.board = self.board
            self._signal.emit(self.connect_info)
            self.close()
        except Exception as ex:
            self.logger.write('serial connect error: ex', ex)
            self.messageLabel.setText('connection failed!')
            raise

    
    def prepare_openbci(self, connect_type, boardID=0, wifi_address=None, wifi_port=0, serial_port=None, other_info='6040000'):
        if connect_type == 1:
            self.board = prepare_wifi_board(boardID, wifi_address, wifi_port)
        elif connect_type == 2:
            self.board = prepare_serial_board(boardID, serial_port, other_info)
        else:
            raise ValueError('unsupported connection type: %r' % (connect_type,))


