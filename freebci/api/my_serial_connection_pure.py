from serial.tools import list_ports
from pyqtgraph.Qt import QtCore, QtWidgets

from freebci.api.myConnectionInfo import connectInfo
from freebci.api.serial_worker import SerialConnectWorker
from freebci.design.serial_connection import Ui_SerialDialog


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
        self._worker = None

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
        if self._worker is not None:
            return
        self.connect_info.serial_port = str(self.comboBox.currentText())
        self.myLogger.write('FreeBCI Port Name = ' + str(self.connect_info.serial_port))
        self.myLogger.write('board id:' + str(self.connect_info.board_id))
        self.connectionButton.setEnabled(False)
        self.messageLabel.setText('Connecting......')
        self.messageLabel.repaint()

        self._worker = SerialConnectWorker(
            self.connect_info.board_id,
            self.connect_info.serial_port,
            self.connect_info.baudRate,
            self.baud_read,
            self.connect_info.channel_num,
            self,
        )
        self._worker.succeeded.connect(self._on_connected)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_connected(self, board, response):
        self.connect_info.baudRate = self.baud_read
        self.connect_info.board = board
        self.messageLabel.setText('connection successfully!')
        self.myLogger.write('connection successfully')
        self.myLogger.write('=================================================')
        self.myLogger.write('||             INITIALIZING SYSTEM             ||')
        self.myLogger.write('=================================================')
        self.myLogger.write('Board Information: ')
        self.myLogger.write(response)
        self._signal.emit(self.connect_info)
        self.close()

    def _on_failed(self, message):
        self.myLogger.write('serial connect error: ' + message)
        self.messageLabel.setText('connection failed!')
        self.connectionButton.setEnabled(True)

    def _on_worker_finished(self):
        self._worker = None

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(5000)
        super(MySerialConnection, self).closeEvent(event)
