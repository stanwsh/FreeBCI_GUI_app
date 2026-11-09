from serial.tools import list_ports
from freebci.qt import QtCore, QtWidgets
from freebci.qt import Qt

from freebci.ui.connection_info import ConnectionInfo
from freebci.ui.workers.serial_connect import BluetoothConnectWorker
from freebci.design.bluetooth_connection import Ui_BluetoothDialog


class BluetoothConnectionDialog(QtWidgets.QDialog, Ui_BluetoothDialog):
    _signal = QtCore.Signal(ConnectionInfo)

    def __init__(self, connect_info, board_id, Logger, parent=None):
        super(BluetoothConnectionDialog, self).__init__(parent)
        self.setupUi(self)
        self.setStyleSheet('background-color:#F1F3F5')
        self.scan_click()
        self.scanButton.clicked.connect(self.scan_click)
        self.connectionButton.clicked.connect(self.connect_click)
        self.connect_info = connect_info
        self.logger = Logger
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
        self.baudComboBox.setCurrentText('921600')
        self.L2 = self.baudComboBox.lineEdit()
        self.L2.setAlignment(Qt.AlignCenter)
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
        port = str(self.comboBox.currentText()).strip()
        baud = str(self.baudComboBox.currentText()).strip()
        if not port:
            self.messageLabel.setText('Select a serial port')
            return
        try:
            int(baud)
        except ValueError:
            self.messageLabel.setText('Invalid baud rate')
            return
        self.connect_info.baudRate = baud
        self.logger.write('Bluetooth Port: ' + port + ' baud: ' + baud)
        self.connectionButton.setEnabled(False)
        self.messageLabel.setText('Connecting......')
        self.messageLabel.repaint()
        self._worker = BluetoothConnectWorker(
            self.connect_info.board_id,
            port,
            baud,
            self,
        )
        self._worker.succeeded.connect(self._on_connected)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_connected(self, board, response):
        self.connect_info.board = board
        self.messageLabel.setText('connection successfully!')
        self.logger.write('connection successfully')
        self.logger.write('=================================================')
        self.logger.write('||             INITIALIZING SYSTEM             ||')
        self.logger.write('=================================================')
        self.logger.write('Board Information: ')
        self.logger.write(response)
        self._signal.emit(self.connect_info)
        self.close()

    def _on_failed(self, message):
        self.logger.write('bluetooth connect error: ' + message)
        self.messageLabel.setText('connection failed!')
        self.connectionButton.setEnabled(True)

    def _on_worker_finished(self):
        self._worker = None

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(5000)
        super(BluetoothConnectionDialog, self).closeEvent(event)
