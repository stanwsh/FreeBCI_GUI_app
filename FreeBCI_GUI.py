"""FreeBCI GUI entry point.

Run this file from the repository root (``run.cmd`` does that for you) so the
application package and the image assets can be found.
"""
import logging
import os
import sys

from PyQt5 import QtWidgets

# Writable data (console logs and recordings) lives in logs\ next to the app.
# Set FREEBCI_HOME to keep it somewhere else.
DATA_ROOT = os.environ.get("FREEBCI_HOME") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs"
)
os.environ["FREEBCI_HOME"] = DATA_ROOT
os.makedirs(DATA_ROOT, exist_ok=True)


def main():
    from freebci.api.my_main_window import MyMainWindow

    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow.instance()
    window.setWindowTitle("FreeBCI GUI")
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("FreeBCI GUI failed to start")
        raise
