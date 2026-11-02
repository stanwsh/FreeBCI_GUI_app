from pyqtgraph.Qt import QtWidgets
from freebci.design.hardware_warning import Ui_hardware_warning

class MyHardwareWarning(QtWidgets.QDialog, Ui_hardware_warning):
    def __init__(self, parent=None):
        super(MyHardwareWarning, self).__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.close)
