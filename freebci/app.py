"""Application composition root.

The entry point only prepares the writable data directory and then delegates
here.  Keeping Qt construction in one small module gives tests and future
tools a place to build the window without importing the launcher script.
"""
from __future__ import annotations

import sys
from typing import Optional, Sequence

from PyQt5 import QtGui, QtWidgets


def create_application(argv: Optional[Sequence[str]] = None) -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(list(argv) if argv is not None else sys.argv)
    app.setFont(QtGui.QFont("Arial", 10))
    return app


def create_window() -> "MainWindow":
    from freebci.ui.main_window import MainWindow

    return MainWindow.instance()


def run(argv: Optional[Sequence[str]] = None) -> int:
    app = create_application(argv)
    window = create_window()
    window.setWindowTitle("FreeBCI GUI")
    window.showMaximized()
    return app.exec_()
