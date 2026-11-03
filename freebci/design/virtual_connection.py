from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_VirtualDialog(object):
    
    def setupUi(self, VirtualDialog):
        VirtualDialog.setObjectName('VirtualDialog')
        VirtualDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        VirtualDialog.resize(431, 297)
        self.connectionButton = QtWidgets.QPushButton(VirtualDialog)
        self.connectionButton.setGeometry(QtCore.QRect(136, 214, 75, 25))
        self.connectionButton.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.connectionButton.setObjectName('connectionButton')
        self.messageLabel = QtWidgets.QLabel(VirtualDialog)
        self.messageLabel.setGeometry(QtCore.QRect(50, 260, 211, 21))
        self.messageLabel.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.messageLabel.setText('')
        self.messageLabel.setObjectName('messageLabel')
        self.label_4 = QtWidgets.QLabel(VirtualDialog)
        self.label_4.setGeometry(QtCore.QRect(80, 140, 71, 20))
        self.label_4.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.label_4.setObjectName('label_4')
        self.label_2 = QtWidgets.QLabel(VirtualDialog)
        self.label_2.setGeometry(QtCore.QRect(82, 59, 48, 17))
        self.label_2.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.label_2.setObjectName('label_2')
        self.lineEdit = QtWidgets.QLineEdit(VirtualDialog)
        self.lineEdit.setGeometry(QtCore.QRect(217, 60, 133, 21))
        self.lineEdit.setStyleSheet('font: 75 12pt "Segoe UI";')
        self.lineEdit.setObjectName('lineEdit')
        self.lineEdit_2 = QtWidgets.QLineEdit(VirtualDialog)
        self.lineEdit_2.setGeometry(QtCore.QRect(220, 140, 131, 21))
        self.lineEdit_2.setStyleSheet('font: 75 12pt "Segoe UI";\n\n')
        self.lineEdit_2.setObjectName('lineEdit_2')
        self.retranslateUi(VirtualDialog)
        QtCore.QMetaObject.connectSlotsByName(VirtualDialog)

    
    def retranslateUi(self, VirtualDialog):
        _translate = QtCore.QCoreApplication.translate
        VirtualDialog.setWindowTitle(_translate('VirtualDialog', 'Virtual Connection'))
        self.connectionButton.setText(_translate('VirtualDialog', 'Connect'))
        self.label_4.setText(_translate('VirtualDialog', 'Channel'))
        self.label_2.setText(_translate('VirtualDialog', ' Board'))


