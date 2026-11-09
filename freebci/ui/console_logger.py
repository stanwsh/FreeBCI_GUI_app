import sys
import os
from freebci.qt import QtCore, QtGui, QtWidgets


class ConsoleLogger(QtWidgets.QWidget):
    _signal = QtCore.Signal(str)

    def __init__(self, filename='Default.log'):
        super(ConsoleLogger, self).__init__()
        self.terminal = sys.stdout
        self.file = filename
        self.log = open(filename, 'a')
        self.log.close()

    def write(self, message):
        try:
            message = str(message)
            with open(self.file, 'a', encoding='utf-8') as log:
                log.write(message + '\n')
            self._signal.emit(message)
            print(message)
        except Exception:
            pass

    def flush(self):
        pass

