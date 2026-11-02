import ipaddress
import os

from pyqtgraph.Qt import QtCore, QtWidgets

from freebci.api.myConnectionInfo import connectInfo
from freebci.api.wifi_discovery import (
    DEFAULT_ADDRESS,
    DEFAULT_PORT,
    DiscoveryResult,
    WifiDevice,
)
from freebci.api.wifi_worker import WifiConnectWorker, WifiDiscoveryWorker
from freebci.design.wifi_connection import Ui_wifiDialog


class MyWifiConnection(QtWidgets.QDialog, Ui_wifiDialog):
    _signal = QtCore.pyqtSignal(connectInfo)

    def __init__(self, connect_info, board_id, Logger, parent=None):
        super(MyWifiConnection, self).__init__(parent)
        self.setupUi(self)
        self.connect_info = connect_info
        self.myLogger = Logger
        self.connect_info.board_id = board_id
        self.board_entry = self.connect_info.id_list[board_id - 2023]
        self.connect_info.wifi_address = DEFAULT_ADDRESS
        self.connect_info.wifi_port = DEFAULT_PORT
        self.connect_info.channel_num = self.board_entry[8]

        self.lineEdit.setText(DEFAULT_ADDRESS)
        self.lineEdit_2.setText(str(DEFAULT_PORT))
        self.modelLabel.setText(self._model_text())
        self.messageLabel.setText('Scanning for boards...')

        self._discovery = None
        self._connect_worker = None
        self._selected_device = None
        self._closing = False
        self._ready_to_close = False

        self.searchButton.clicked.connect(self.search_click)
        self.connectButton.clicked.connect(self.connect_click)
        self.cancelButton.clicked.connect(self.close)
        self.openWifiButton.clicked.connect(self.open_wifi_settings)
        self.deviceList.currentItemChanged.connect(self._device_changed)
        self.lineEdit.textEdited.connect(self._manual_address_edited)
        self.lineEdit_2.textEdited.connect(self._manual_address_edited)
        self._update_connect_button()

        # Discovery is automatic; the user should not have to guess an IP.
        QtCore.QTimer.singleShot(0, self.search_click)

    def _model_text(self):
        raw_name = str(self.board_entry[0])
        raw_name = raw_name.replace('_WIFI', '').replace('_USB', '')
        name = raw_name.replace('_', ' ').replace('WiFi', 'Wi-Fi')
        return 'Board model: %s  |  %d channels' % (name, int(self.board_entry[8]))

    def _update_connect_button(self):
        if self._connect_worker is not None or self._discovery is not None:
            self.connectButton.setEnabled(False)
            return
        address = self.lineEdit.text().strip()
        try:
            port = int(self.lineEdit_2.text().strip())
        except ValueError:
            port = 0
        valid_address = False
        try:
            ipaddress.IPv4Address(address)
            valid_address = True
        except ValueError:
            pass
        self.connectButton.setEnabled(valid_address and 1 <= port <= 65535)

    def _manual_address_edited(self):
        self._selected_device = None
        self.deviceList.clearSelection()
        self.messageLabel.setText(
            'Using the address entered below. Select a detected board to use its address.'
        )
        self._update_connect_button()

    def _set_busy(self, busy):
        self.progressBar.setVisible(busy)
        self.searchButton.setEnabled(not busy)
        self.connectButton.setEnabled(not busy)
        self.openWifiButton.setEnabled(not busy)
        if not busy:
            self._update_connect_button()

    def _clear_devices(self):
        self.deviceList.clear()
        self._fit_device_list()

    def _fit_device_list(self):
        count = self.deviceList.count()
        if count <= 1:
            height = 56
        else:
            height = min(128, 48 + 40 * (count - 1))
        self.deviceList.setFixedHeight(height)

    def _device_text(self, device):
        details = [device.address]
        if device.channels:
            details.append('%d ch' % device.channels)
        if device.ready is True:
            details.append('ready')
        elif device.ready is False:
            details.append('board not connected')
        else:
            details.append('detected')
        return 'FreeBCI board  |  %s' % '  |  '.join(details)

    def _set_wifi_status(self, status, device_count=0):
        if status.connected:
            self.wifiLabel.setText('Wi-Fi: %s' % status.ssid)
            if status.is_freebci:
                self.wifiDetailLabel.setText(
                    'Connected to the board access point.'
                )
            else:
                self.wifiDetailLabel.setText(
                    'Different network. Join the FreeBCI-xxxx access point.'
                )
            return
        if device_count:
            self.wifiLabel.setText('Wi-Fi: FreeBCI board network')
            self.wifiDetailLabel.setText(
                'Board detected. Windows did not report the Wi-Fi name.'
            )
            return
        self.wifiLabel.setText('Wi-Fi network')
        if status.detail and status.detail != 'Wi-Fi status unavailable':
            self.wifiDetailLabel.setText(
                '%s. Join the FreeBCI-xxxx access point, then scan again.' % status.detail
            )
        else:
            self.wifiDetailLabel.setText(
                'Wi-Fi status unavailable. Detection below still works when the board is reachable.'
            )

    def _on_discovered(self, result):
        if not isinstance(result, DiscoveryResult):
            self.messageLabel.setText('Discovery returned an unexpected response.')
            return
        self._set_wifi_status(result.wifi, len(result.devices))
        self._clear_devices()
        self._selected_device = None
        if not result.devices:
            if result.wifi.is_freebci:
                self.messageLabel.setText(
                    'Connected to %s, but no board answered. Wait a few seconds and scan again.'
                    % result.wifi.ssid
                )
            else:
                self.messageLabel.setText(
                    'No board detected. Join the board Wi-Fi network and scan again, '
                    'or enter its IP address below.'
                )
            self._update_connect_button()
            return
        for device in result.devices:
            item = QtWidgets.QListWidgetItem(self._device_text(device))
            item.setData(QtCore.Qt.UserRole, device)
            item.setSizeHint(QtCore.QSize(0, 40))
            self.deviceList.addItem(item)
        self._fit_device_list()
        self.messageLabel.setText(
            'Found %d board%s. Select a board and click Connect.'
            % (len(result.devices), '' if len(result.devices) == 1 else 's')
        )
        self.deviceList.setCurrentRow(0)
        self._update_connect_button()

    def _on_discovery_failed(self, message):
        self.myLogger.write('wifi discovery error: ' + message)
        self.wifiLabel.setText('Wi-Fi network')
        self.wifiDetailLabel.setText('Could not read the current network.')
        self.messageLabel.setText(
            'Scan failed: %s. You can still enter the board IP address below.' % message
        )
        self._update_connect_button()

    def _on_discovery_finished(self):
        self._discovery = None
        if self._closing:
            self.close()
        else:
            self._set_busy(False)

    def search_click(self):
        if self._discovery is not None or self._connect_worker is not None:
            return
        self._set_busy(True)
        self.messageLabel.setText('Scanning local networks for a FreeBCI board...')
        self._discovery = WifiDiscoveryWorker((self.lineEdit.text().strip(),), self)
        self._discovery.found.connect(self._on_discovered)
        self._discovery.failed.connect(self._on_discovery_failed)
        self._discovery.finished.connect(self._on_discovery_finished)
        self._discovery.start()

    def _device_changed(self, current, _previous):
        if current is None:
            return
        device = current.data(QtCore.Qt.UserRole)
        if not isinstance(device, WifiDevice):
            return
        self._selected_device = device
        self.lineEdit.setText(device.address)
        self.lineEdit_2.setText(str(device.port))
        if device.channels and int(device.channels) != int(self.board_entry[8]):
            self.messageLabel.setText(
                'Detected %d channels, but the selected model expects %d. '
                'Choose the matching board model from the Boards menu.'
                % (device.channels, int(self.board_entry[8]))
            )
        else:
            self.messageLabel.setText('Selected board at %s. Click Connect.' % device.address)
        self._update_connect_button()

    def open_wifi_settings(self):
        try:
            os.startfile('ms-settings:network-wifi')
            self.messageLabel.setText(
                'Join the FreeBCI-xxxx network in Windows, then click Scan again.'
            )
        except (AttributeError, OSError) as exc:
            self.messageLabel.setText('Could not open Wi-Fi settings: %s' % exc)

    def connect_click(self):
        if self._connect_worker is not None:
            return
        address = self.lineEdit.text().strip()
        try:
            ipaddress.IPv4Address(address)
        except ValueError:
            self.messageLabel.setText('Enter an IPv4 address such as 192.168.4.1.')
            return
        try:
            port = int(self.lineEdit_2.text().strip())
        except ValueError:
            port = 0
        if not 1 <= port <= 65535:
            self.messageLabel.setText('Enter a control port between 1 and 65535.')
            return

        self.connect_info.wifi_address = address
        self.connect_info.wifi_port = port
        self.myLogger.write(
            'Networking: [IP]: %s [Port]: %d' % (self.connect_info.wifi_address, port)
        )
        self._set_busy(True)
        self.messageLabel.setText('Connecting to %s...' % address)
        self._connect_worker = WifiConnectWorker(
            self.connect_info.board_id,
            address,
            port,
            self,
        )
        self._connect_worker.progress.connect(self._on_progress)
        self._connect_worker.succeeded.connect(self._on_connected)
        self._connect_worker.failed.connect(self._on_failed)
        self._connect_worker.finished.connect(self._on_connect_finished)
        self._connect_worker.start()

    def _on_progress(self, message):
        self.messageLabel.setText(message)

    def _on_connected(self, board, response):
        if self._closing:
            try:
                board.release_session()
            except Exception:
                pass
            return
        self.connect_info.board = board
        self._ready_to_close = True
        self.messageLabel.setText('Connected. Preparing the dashboard...')
        self.myLogger.write('connection successfully')
        self.myLogger.write('=================================================')
        self.myLogger.write('||             INITIALIZING SYSTEM             ||')
        self.myLogger.write('=================================================')
        self.myLogger.write('Board Information: ')
        self.myLogger.write(response)
        self._signal.emit(self.connect_info)

    def _on_failed(self, message):
        self.myLogger.write('wifi connect error: ' + message)
        self.messageLabel.setText('Connection failed: %s' % message)
        self._set_busy(False)

    def _on_connect_finished(self):
        self._connect_worker = None
        if self._ready_to_close or self._closing:
            self.close()
        else:
            self._set_busy(False)

    def closeEvent(self, event):
        self._closing = True
        if self._connect_worker is not None:
            self._connect_worker.cancel()
            if self._connect_worker.isRunning():
                self.messageLabel.setText('Cancelling connection...')
                self._set_busy(True)
                event.ignore()
                return
            self._connect_worker = None
        if self._discovery is not None:
            self._discovery.cancel()
            if self._discovery.isRunning():
                self.messageLabel.setText('Stopping scan...')
                self._set_busy(True)
                event.ignore()
                return
            self._discovery = None
        super(MyWifiConnection, self).closeEvent(event)
