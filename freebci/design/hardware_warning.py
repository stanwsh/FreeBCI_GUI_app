from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_hardware_warning(object):
    
    def setupUi(self, hardware_warning):
        hardware_warning.setObjectName('hardware_warning')
        hardware_warning.resize(400, 218)
        self.label = QtWidgets.QLabel(hardware_warning)
        self.label.setGeometry(QtCore.QRect(140, 10, 151, 51))
        self.label.setStyleSheet('font: 20pt "黑体";')
        self.label.setObjectName('label')
        self.label_2 = QtWidgets.QLabel(hardware_warning)
        self.label_2.setGeometry(QtCore.QRect(20, 80, 361, 81))
        self.label_2.setStyleSheet('font: 12pt "黑体";')
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName('label_2')
        self.pushButton = QtWidgets.QPushButton(hardware_warning)
        self.pushButton.setGeometry(QtCore.QRect(160, 170, 93, 28))
        self.pushButton.setObjectName('pushButton')
        self.retranslateUi(hardware_warning)
        QtCore.QMetaObject.connectSlotsByName(hardware_warning)

    
    def retranslateUi(self, hardware_warning):
        _translate = QtCore.QCoreApplication.translate
        hardware_warning.setWindowTitle(_translate('hardware_warning', 'Dialog'))
        self.label.setText(_translate('hardware_warning', 'Warning'))
        self.label_2.setText(_translate('hardware_warning', 'Streaming needs to be stopped before accessing Hardware Settings'))
        self.pushButton.setText(_translate('hardware_warning', 'OK'))


