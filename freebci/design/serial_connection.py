from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SerialDialog(object):
    
    def setupUi(self, SerialDialog):
        SerialDialog.setObjectName('SerialDialog')
        SerialDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SerialDialog.resize(318, 329)
        self.gridLayout = QtWidgets.QGridLayout(SerialDialog)
        self.gridLayout.setObjectName('gridLayout')
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 0, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(SerialDialog)
        self.label.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.label.setObjectName('label')
        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(31, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 1, 4, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 2, 1, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(50, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem4, 3, 0, 1, 1)
        self.connectionButton = QtWidgets.QPushButton(SerialDialog)
        self.connectionButton.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.connectionButton.setObjectName('connectionButton')
        self.gridLayout.addWidget(self.connectionButton, 3, 2, 1, 1)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem5, 3, 3, 1, 1)
        spacerItem6 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem6, 4, 3, 1, 1)
        self.messageLabel = QtWidgets.QLabel(SerialDialog)
        self.messageLabel.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.messageLabel.setText('')
        self.messageLabel.setObjectName('messageLabel')
        self.gridLayout.addWidget(self.messageLabel, 4, 0, 1, 3)
        self.comboBox = QtWidgets.QComboBox(SerialDialog)
        self.comboBox.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.comboBox.setObjectName('comboBox')
        self.gridLayout.addWidget(self.comboBox, 1, 3, 1, 1)
        self.retranslateUi(SerialDialog)
        QtCore.QMetaObject.connectSlotsByName(SerialDialog)

    
    def retranslateUi(self, SerialDialog):
        _translate = QtCore.QCoreApplication.translate
        SerialDialog.setWindowTitle(_translate('SerialDialog', 'Serial Connection'))
        self.label.setText(_translate('SerialDialog', 'Serial Port'))
        self.connectionButton.setText(_translate('SerialDialog', 'Connect'))


