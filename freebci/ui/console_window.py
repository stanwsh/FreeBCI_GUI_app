from concurrent.futures import thread
import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import pyperclip
from freebci.design.console_window import Ui_TerminalDialog
from freebci.ui.console_logger import ConsoleLogger

class ConsoleWindow(QtWidgets.QDialog, Ui_TerminalDialog):
    
    def __new__(cls, log_file, Logger):
        if not hasattr(cls, 'instance'):
            cls._ConsoleWindow__instance = super().__new__(cls)
        return cls._ConsoleWindow__instance

    
    def __init__(self, log_file, Logger, parent=None):
        super(ConsoleWindow, self).__init__(parent)
        self.setupUi(self)
        self.log_file = log_file
        self.logger = Logger
        self.refreshText()
        self.textEdit.setReadOnly(True)
        self.openPushButton.clicked.connect(self.openPushButton_click)
        self.copyFullPushButton.clicked.connect(self.copyFullPushButton_click)
        self.copyLastPushButton.clicked.connect(self.copyLastPushButton_click)
        self.jumpPushButton.clicked.connect(self.jumpPushButton_click)

    
    def jumpPushButton_click(self):
        if isinstance(self.textEdit, QtWidgets.QTextEdit):
            self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())

    
    def copyLastPushButton_click(self):
        texts = self.textEdit.toPlainText()
        text = texts.split('\n')
        pyperclip.copy(text[-2])
        self.logger.write('ConsoleLog: Previous line copied to clipboard.')

    
    def copyFullPushButton_click(self):
        pyperclip.copy(self.textEdit.toPlainText())
        self.logger.write('ConsoleLog: Copying console log to clipboard.')

    
    def openPushButton_click(self):
        os.startfile(self.log_file)
        self.logger.write('ConsoleLog: Opening console log as text file.')

    
    def refreshText(self):
        self.logFile = open(self.log_file, 'r+')
        texts = self.logFile.read()
        self.textEdit.setText(texts)
        self.logFile.close()

    
    def appendText(self, message):
        if isinstance(self.textEdit, QtWidgets.QTextEdit):
            self.textEdit.moveCursor(QtGui.QTextCursor.End)
            self.textEdit.insertPlainText(message)
            self.textEdit.moveCursor(QtGui.QTextCursor.End)

    
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.logger.write('ConsoleWindow: Console closed.')
        return super().closeEvent(a0)

    
    def setupUi(self, TerminalDialog):
        super().setupUi(TerminalDialog)
        TerminalDialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)


