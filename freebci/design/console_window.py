from freebci.qt import QtCore, QtGui, QtWidgets

class Ui_TerminalDialog(object):
    
    def setupUi(self, TerminalDialog):
        TerminalDialog.setObjectName('TerminalDialog')
        TerminalDialog.resize(634, 449)
        self.gridLayout = QtWidgets.QGridLayout(TerminalDialog)
        self.gridLayout.setObjectName('gridLayout')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName('verticalLayout')
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName('horizontalLayout_2')
        self.openPushButton = QtWidgets.QPushButton(TerminalDialog)
        self.openPushButton.setObjectName('openPushButton')
        self.horizontalLayout_2.addWidget(self.openPushButton)
        self.copyFullPushButton = QtWidgets.QPushButton(TerminalDialog)
        self.copyFullPushButton.setObjectName('copyFullPushButton')
        self.horizontalLayout_2.addWidget(self.copyFullPushButton)
        self.copyLastPushButton = QtWidgets.QPushButton(TerminalDialog)
        self.copyLastPushButton.setObjectName('copyLastPushButton')
        self.horizontalLayout_2.addWidget(self.copyLastPushButton)
        self.jumpPushButton = QtWidgets.QPushButton(TerminalDialog)
        self.jumpPushButton.setObjectName('jumpPushButton')
        self.horizontalLayout_2.addWidget(self.jumpPushButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.textEdit = QtWidgets.QTextEdit(TerminalDialog)
        self.textEdit.setStyleSheet('font: 25 10pt "Segoe UI";')
        self.textEdit.setObjectName('textEdit')
        self.verticalLayout.addWidget(self.textEdit)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.retranslateUi(TerminalDialog)
        QtCore.QMetaObject.connectSlotsByName(TerminalDialog)

    
    def retranslateUi(self, TerminalDialog):
        _translate = QtCore.QCoreApplication.translate
        TerminalDialog.setWindowTitle(_translate('TerminalDialog', 'ConsoleWindow'))
        self.openPushButton.setText(_translate('TerminalDialog', 'Open Log as Text'))
        self.copyFullPushButton.setText(_translate('TerminalDialog', 'Copy Full Text'))
        self.copyLastPushButton.setText(_translate('TerminalDialog', 'Copy Last Line'))
        self.jumpPushButton.setText(_translate('TerminalDialog', 'Jump to Last Line'))


