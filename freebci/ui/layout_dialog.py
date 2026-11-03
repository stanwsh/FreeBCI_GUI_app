from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget
from freebci.design.layout_window import Ui_Layout

class LayoutDialog(QtWidgets.QDialog, Ui_Layout):
    _signal = QtCore.pyqtSignal(int)
    
    def __init__(self, parent_path):
        super(LayoutDialog, self).__init__()
        self.setupUi(self)
        icon = QtGui.QIcon()
        self.parent_path = parent_path
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon1.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton1.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon3.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton2.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon4.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton3.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon2.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton4.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon5.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton5.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon7.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton6.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon6.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton7.setIcon(icon)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.parent_path + '\\freebci\\design\\layout_icon8.png'), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton8.setIcon(icon)
        self.pushButton1.clicked.connect(self.slot1)
        self.pushButton2.clicked.connect(self.slot2)
        self.pushButton3.clicked.connect(self.slot3)
        self.pushButton4.clicked.connect(self.slot4)
        self.pushButton5.clicked.connect(self.slot5)
        self.pushButton6.clicked.connect(self.slot6)
        self.pushButton7.clicked.connect(self.slot7)
        self.pushButton8.clicked.connect(self.slot8)

    
    def slot1(self):
        self._signal.emit(1)
        self.close()

    
    def slot2(self):
        self._signal.emit(2)
        self.close()

    
    def slot3(self):
        self._signal.emit(3)
        self.close()

    
    def slot4(self):
        self._signal.emit(4)
        self.close()

    
    def slot5(self):
        self._signal.emit(5)
        self.close()

    
    def slot6(self):
        self._signal.emit(6)
        self.close()

    
    def slot7(self):
        self._signal.emit(7)
        self.close()

    
    def slot8(self):
        self._signal.emit(8)
        self.close()


