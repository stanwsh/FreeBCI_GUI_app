import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets


class MyLogger(QtWidgets.QWidget):
    _signal = QtCore.pyqtSignal(str)

    def __init__(self, filename='Default.log'):
        super(MyLogger, self).__init__()
        self.terminal = sys.stdout
        self.file = filename
        self.log = open(filename, 'a')
        self.log.close()

    def write(self, message):
        try:
            self.log = open(self.file, 'a')
            self.log.write(message + '\n')
            self.log.close()
            self._signal.emit(message)
            print(message)
        except:
            pass

    def flush(self):
        pass

