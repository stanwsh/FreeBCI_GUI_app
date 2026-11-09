from freebci.qt import QtCore, QtWidgets


class Ui_wifiDialog(object):
    """Connection dialog for a FreeBCI Wi-Fi board.

    The dialog deliberately presents detected boards and the current network
    instead of exposing a BrainFlow board id.  The id is an implementation
    detail chosen by the Boards menu.
    """

    def setupUi(self, wifiDialog):
        wifiDialog.setObjectName('wifiDialog')
        wifiDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        wifiDialog.resize(620, 640)
        wifiDialog.setMinimumWidth(540)
        wifiDialog.setSizeGripEnabled(False)

        self.verticalLayout = QtWidgets.QVBoxLayout(wifiDialog)
        self.verticalLayout.setContentsMargins(20, 16, 20, 16)
        self.verticalLayout.setSpacing(8)

        self.titleLabel = QtWidgets.QLabel(wifiDialog)
        title_font = self.titleLabel.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.titleLabel.setFont(title_font)
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setObjectName('titleLabel')
        self.verticalLayout.addWidget(self.titleLabel)

        self.subtitleLabel = QtWidgets.QLabel(wifiDialog)
        self.subtitleLabel.setWordWrap(True)
        self.subtitleLabel.setObjectName('subtitleLabel')
        self.verticalLayout.addWidget(self.subtitleLabel)

        self.networkFrame = QtWidgets.QFrame(wifiDialog)
        self.networkFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.networkFrame.setObjectName('networkFrame')
        network_layout = QtWidgets.QHBoxLayout(self.networkFrame)
        network_layout.setContentsMargins(10, 8, 10, 8)
        network_layout.setSpacing(8)
        network_text = QtWidgets.QVBoxLayout()
        network_text.setSpacing(2)
        self.wifiLabel = QtWidgets.QLabel(self.networkFrame)
        wifi_font = self.wifiLabel.font()
        wifi_font.setBold(True)
        self.wifiLabel.setFont(wifi_font)
        self.wifiLabel.setWordWrap(True)
        self.wifiLabel.setObjectName('wifiLabel')
        self.wifiDetailLabel = QtWidgets.QLabel(self.networkFrame)
        self.wifiDetailLabel.setWordWrap(True)
        self.wifiDetailLabel.setObjectName('wifiDetailLabel')
        network_text.addWidget(self.wifiLabel)
        network_text.addWidget(self.wifiDetailLabel)
        network_layout.addLayout(network_text, 1)
        self.openWifiButton = QtWidgets.QPushButton(self.networkFrame)
        self.openWifiButton.setObjectName('openWifiButton')
        network_layout.addWidget(self.openWifiButton)
        self.verticalLayout.addWidget(self.networkFrame)

        self.deviceHeader = QtWidgets.QHBoxLayout()
        self.deviceLabel = QtWidgets.QLabel(wifiDialog)
        device_font = self.deviceLabel.font()
        device_font.setBold(True)
        self.deviceLabel.setFont(device_font)
        self.deviceLabel.setObjectName('deviceLabel')
        self.deviceHeader.addWidget(self.deviceLabel)
        self.deviceHeader.addStretch(1)
        self.searchButton = QtWidgets.QPushButton(wifiDialog)
        self.searchButton.setObjectName('searchButton')
        self.deviceHeader.addWidget(self.searchButton)
        self.verticalLayout.addLayout(self.deviceHeader)

        self.deviceList = QtWidgets.QListWidget(wifiDialog)
        self.deviceList.setObjectName('deviceList')
        self.deviceList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.deviceList.setMinimumHeight(64)
        self.deviceList.setMaximumHeight(128)
        self.deviceList.setAlternatingRowColors(True)
        self.deviceList.setWordWrap(True)
        self.verticalLayout.addWidget(self.deviceList)

        self.modelLabel = QtWidgets.QLabel(wifiDialog)
        self.modelLabel.setWordWrap(True)
        self.modelLabel.setObjectName('modelLabel')
        self.verticalLayout.addWidget(self.modelLabel)

        self.advancedGroup = QtWidgets.QGroupBox(wifiDialog)
        self.advancedGroup.setObjectName('advancedGroup')
        self.advancedGroup.setFlat(True)
        advanced_layout = QtWidgets.QFormLayout(self.advancedGroup)
        advanced_layout.setContentsMargins(10, 6, 10, 6)
        advanced_layout.setSpacing(6)
        self.lineEdit = QtWidgets.QLineEdit(self.advancedGroup)
        self.lineEdit.setObjectName('lineEdit')
        self.lineEdit.setPlaceholderText('192.168.4.1')
        self.lineEdit_2 = QtWidgets.QLineEdit(self.advancedGroup)
        self.lineEdit_2.setObjectName('lineEdit_2')
        self.lineEdit_2.setPlaceholderText('8899')
        advanced_layout.addRow('IP address', self.lineEdit)
        advanced_layout.addRow('Control port', self.lineEdit_2)
        self.advancedGroup.setLayout(advanced_layout)
        self.verticalLayout.addWidget(self.advancedGroup)

        self.messageLabel = QtWidgets.QLabel(wifiDialog)
        self.messageLabel.setWordWrap(True)
        self.messageLabel.setMinimumHeight(30)
        self.messageLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.messageLabel.setObjectName('messageLabel')
        self.verticalLayout.addWidget(self.messageLabel)

        self.progressBar = QtWidgets.QProgressBar(wifiDialog)
        self.progressBar.setObjectName('progressBar')
        self.progressBar.setRange(0, 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setVisible(False)
        self.verticalLayout.addWidget(self.progressBar)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        self.cancelButton = QtWidgets.QPushButton(wifiDialog)
        self.cancelButton.setObjectName('cancelButton')
        self.connectButton = QtWidgets.QPushButton(wifiDialog)
        self.connectButton.setObjectName('connectButton')
        self.connectButton.setDefault(True)
        button_layout.addWidget(self.cancelButton)
        button_layout.addWidget(self.connectButton)
        self.verticalLayout.addLayout(button_layout)

        self.retranslateUi(wifiDialog)
        QtCore.QMetaObject.connectSlotsByName(wifiDialog)
        wifiDialog.setTabOrder(self.searchButton, self.deviceList)
        wifiDialog.setTabOrder(self.deviceList, self.connectButton)

    def retranslateUi(self, wifiDialog):
        _translate = QtCore.QCoreApplication.translate
        wifiDialog.setWindowTitle(_translate('wifiDialog', 'Connect to a Wi-Fi board'))
        self.titleLabel.setText(_translate('wifiDialog', 'Connect a FreeBCI Wi-Fi board'))
        self.subtitleLabel.setText(_translate(
            'wifiDialog',
            'Join the board Wi-Fi network first, then choose the board below. '
            'The application detects boards that answer on the local network.',
        ))
        self.wifiLabel.setText(_translate('wifiDialog', 'Wi-Fi network'))
        self.wifiDetailLabel.setText(_translate('wifiDialog', 'Checking current connection...'))
        self.openWifiButton.setText(_translate('wifiDialog', 'Open Wi-Fi settings'))
        self.deviceLabel.setText(_translate('wifiDialog', 'Detected boards'))
        self.searchButton.setText(_translate('wifiDialog', 'Scan again'))
        self.modelLabel.setText(_translate('wifiDialog', 'Selected board model'))
        self.advancedGroup.setTitle(_translate('wifiDialog', 'Advanced connection settings'))
        self.messageLabel.setText(_translate('wifiDialog', 'Scanning for boards...'))
        self.cancelButton.setText(_translate('wifiDialog', 'Cancel'))
        self.connectButton.setText(_translate('wifiDialog', 'Connect'))
