"""Select the application's single Qt binding before loading any Qt consumers."""
import os
import sys

if any(name == 'PyQt5' or name.startswith('PyQt5.') for name in sys.modules):
    raise RuntimeError('FreeBCI uses PySide6; start it in an environment without PyQt5 loaded')

os.environ['PYQTGRAPH_QT_LIB'] = 'PySide6'
os.environ['QT_API'] = 'pyside6'

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtCore import Property, Signal, Slot  # noqa: E402

Qt = QtCore.Qt
QThread = QtCore.QThread
QPixmap = QtGui.QPixmap
QPainter = QtGui.QPainter
QColor = QtGui.QColor
QFont = QtGui.QFont
QPen = QtGui.QPen
QSizePolicy = QtWidgets.QSizePolicy

__all__ = [
    'QtCore', 'QtGui', 'QtWidgets', 'Signal', 'Slot', 'Property', 'Qt',
    'QThread', 'QPixmap', 'QPainter', 'QColor', 'QFont', 'QPen', 'QSizePolicy',
]
