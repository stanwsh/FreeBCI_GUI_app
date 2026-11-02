from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from freebci.api.myConnectionInfo import connectInfo
from freebci.api.wifi_worker import WifiConnectWorker, WifiDiscoveryWorker
from freebci.design.wifi_connection import Ui_wifiDialog


class MyWifiConnection(QtWidgets.QDialog, Ui_wifiDialog):
    _signal = QtCore.pyqtSignal(connectInfo)

    def __init__(self, connect_info, board_id, Logger, parent=None):
        super(MyWifiConnection, self).__init__(parent)
        self.setupUi(self)
        self.connectButton.clicked.connect(self.connect_click)
        self.searchButton.clicked.connect(self.search_click)
        self.connect_info = connect_info
        self.myLogger = Logger
        self.connect_info.board_id = board_id
        self.connect_info.wifi_address = '192.168.4.1'
        self.connect_info.wifi_port = 8899
        self.connect_info.channel_num = self.connect_info.id_list[self.connect_info.board_id - 2023][8]
        self.lineEdit.setText(self.connect_info.wifi_address)
        self.lineEdit_2.setText(str(self.connect_info.wifi_port))
        self.lineEdit_3.setText(str(self.connect_info.channel_num))
        self.lineEdit_3.setReadOnly(True)
        self.lineEdit_3.setAlignment(Qt.AlignCenter)
        self.lineEdit_2.setAlignment(Qt.AlignCenter)
        self.lineEdit.setAlignment(Qt.AlignCenter)
        self._device_layout = QtWidgets.QVBoxLayout(self.widget)
        self._discovery = None
        self._connect_worker = None

    def search_click(self):
        if self._discovery is not None:
            return
        self.searchButton.setEnabled(False)
        self.messageLabel.setText('Searching for boards......')
        self.messageLabel.repaint()
        self._discovery = WifiDiscoveryWorker(self)
        self._discovery.found.connect(self._on_discovered)
        self._discovery.failed.connect(self._on_discovery_failed)
        self._discovery.finished.connect(self._on_discovery_finished)
        self._discovery.start()

    def _clear_devices(self):
        layout = self.widget.layout()
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _on_discovered(self, rows):
        self._clear_devices()
        if not rows:
            self.messageLabel.setText('No boards found')
            return
        for serial_number, ip_address in rows:
            button = QtWidgets.QPushButton(str(serial_number))
            button.clicked.connect(lambda _checked=False, ip=ip_address: self._select_ip(ip))
            self.widget.layout().addWidget(button)
        self.messageLabel.setText('Found %d board(s)' % len(rows))

    def _on_discovery_failed(self, message):
        self.myLogger.write('wifi discovery error: ' + message)
        self.messageLabel.setText('Search failed')

    def _on_discovery_finished(self):
        self._discovery = None
        self.searchButton.setEnabled(True)

    def _select_ip(self, ip_address):
        self.lineEdit.setText(str(ip_address))

    def connect_click(self):
        if self._connect_worker is not None:
            return
        try:
            self.connect_info.wifi_address = str(self.lineEdit.text()).strip()
            self.connect_info.wifi_port = int(self.lineEdit_2.text())
        except ValueError:
            self.messageLabel.setText('Invalid port')
            return
        self.myLogger.write('Networking: [IP]: ' + self.connect_info.wifi_address + ' [Port]: ' + str(self.connect_info.wifi_port))
        self.myLogger.write('board id: ' + str(self.connect_info.board_id))
        self.connectButton.setEnabled(False)
        self.messageLabel.setText('Connecting......')
        self.messageLabel.repaint()
        self._connect_worker = WifiConnectWorker(
            self.connect_info.board_id,
            self.connect_info.wifi_address,
            self.connect_info.wifi_port,
            self.connect_info.channel_num,
            self,
        )
        self._connect_worker.succeeded.connect(self._on_connected)
        self._connect_worker.failed.connect(self._on_failed)
        self._connect_worker.finished.connect(self._on_connect_finished)
        self._connect_worker.start()

    def _on_connected(self, board, response):
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
        self.myLogger.write('wifi connect error: ' + message)
        self.messageLabel.setText('connection failed!')
        self.connectButton.setEnabled(True)

    def _on_connect_finished(self):
        self._connect_worker = None

    def closeEvent(self, event):
        for worker in (self._discovery, self._connect_worker):
            if worker is not None and worker.isRunning():
                worker.wait(5000)
        super(MyWifiConnection, self).closeEvent(event)
