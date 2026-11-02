import sys
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

class MyAccelerometer(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super(MyAccelerometer, self).__init__(parent)
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setHorizontalSpacing(0)
        self.mainLayout.setVerticalSpacing(0)
        self.mainLayout.setObjectName('mainLayout')
        self.stackedWidget = QtWidgets.QStackedWidget(self)
        self.stackedWidget.setObjectName('stackedWidget')
        self.page = QtWidgets.QWidget()
        self.page.setObjectName('page')
        self.gridLayout_2 = QtWidgets.QGridLayout(self.page)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName('gridLayout_2')
        self.widget_2 = QtWidgets.QWidget(self.page)
        self.widget_2.setStyleSheet('background-color: #969696')
        self.widget_2.setObjectName('widget_2')
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName('horizontalLayout_3')
        self.layoutComboBox = QtWidgets.QComboBox(self.widget_2)
        self.layoutComboBox.setStyleSheet('font: 75 10pt "等线";\nbackground-color: white')
        self.layoutComboBox.setObjectName('layoutComboBox')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.addItem('')
        self.layoutComboBox.setCurrentIndex(4)
        self.horizontalLayout_3.addWidget(self.layoutComboBox)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.horizontalLayout_3.setStretch(0, 6)
        self.horizontalLayout_3.setStretch(1, 25)
        self.gridLayout_2.addWidget(self.widget_2, 0, 0, 1, 1)
        self.widget_3 = QtWidgets.QWidget(self.page)
        self.widget_3.setStyleSheet('background-color:#C8C8C8')
        self.widget_3.setObjectName('widget_3')
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget_3)
        self.horizontalLayout_4.setContentsMargins(0, 1, 0, 1)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName('horizontalLayout_4')
        self.DateModepushButton = QtWidgets.QPushButton(self.widget_3)
        self.DateModepushButton.setStyleSheet('font: 75 10pt "等线";')
        self.DateModepushButton.setObjectName('Start Accelerometer')
        self.horizontalLayout_4.addWidget(self.DateModepushButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.horizontalLayout_4.setStretch(0, 5)
        self.horizontalLayout_4.setStretch(1, 26)
        self.gridLayout_2.addWidget(self.widget_3, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName('page_2')
        self.stackedWidget.addWidget(self.page_2)
        self.mainLayout.addWidget(self.stackedWidget, 0, 0, 1, 5)
        self.xlabel = QtWidgets.QLabel(self)
        self.xlabel.setStyleSheet('color: red;\n\nfont: 14pt "黑体";\n')
        self.xlabel.setObjectName('xlabel')
        self.mainLayout.addWidget(self.xlabel, 1, 0, 1, 1)
        self.zlabel = QtWidgets.QLabel(self)
        self.zlabel.setStyleSheet('color: blue;\n\nfont: 14pt "黑体";')
        self.zlabel.setObjectName('zlabel')
        self.mainLayout.addWidget(self.zlabel, 3, 0, 1, 1)
        self.ylabel = QtWidgets.QLabel(self)
        self.ylabel.setStyleSheet('color: green;\n\nfont: 14pt "黑体";\n')
        self.ylabel.setObjectName('ylabel')
        self.mainLayout.addWidget(self.ylabel, 2, 0, 1, 1)
        self.acc_plot = PlotWidget(self, background='w')
        self.acc_plot.enableMouse(False)
        self.acc_plot.hideButtons()
        self.acc_plot.setMouseEnabled(x=False, y=False)
        self.acc_plot.setMenuEnabled(False)
        self.acc_plot.setObjectName('acc_plot')
        self.mainLayout.addWidget(self.acc_plot, 4, 0, 1, 2)
        self.mainLayout.setColumnStretch(0, 2)
        self.mainLayout.setColumnStretch(1, 30)
        self.mainLayout.setRowStretch(0, 2)
        self.mainLayout.setRowStretch(1, 4)
        self.mainLayout.setRowStretch(2, 4)
        self.mainLayout.setRowStretch(3, 4)
        self.mainLayout.setRowStretch(4, 20)
        self.layoutComboBox.setCurrentIndex(3)
        self.retranslateText()
        self.setLayout(self.mainLayout)
        self.acc_len_z = 60
        self.acc_len_x = 60
        self.acc_len_y = 60
        self.zx = 660
        self.zy = 140 - self.acc_len_z
        self.xx = 660 + self.acc_len_x
        self.xy = 140
        self.yx = 660 + self.acc_len_y / math.sqrt(2)
        self.yy = 140 - self.acc_len_y / math.sqrt(2)

    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        size = self.size()
        x0 = 400
        y0 = 140
        r0 = 80
        angle = math.pi / 3
        pen = QPen(QColor(200, 200, 200), 2, Qt.DotLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(x0, y0 + r0 / 3, x0, y0 - r0)
        painter.drawLine(x0 - r0 / 2, y0, x0 + r0, y0)
        painter.drawLine(x0 + (r0 / 2) * math.sin(angle), y0 - (r0 / 2) * math.cos(angle), x0 - (r0 / 2) * math.sin(angle), y0 + (r0 / 2) * math.cos(angle))
        pen = QPen(QColor(200, 200, 200), 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        for i in range(10, 90, 14):
            painter.drawLine(x0 + i, y0, x0 + i, y0 - r0)
            painter.drawLine(x0, y0 - i, x0 + r0, y0 - i)
            painter.drawLine(x0 - (i / 2) * math.sin(angle), y0 + (i / 2) * math.cos(angle), x0 - (i / 2) * math.sin(angle), y0 + (i / 2) * math.cos(angle) - r0)
            painter.drawLine(x0, y0 - i, x0 - (r0 / 2) * math.sin(angle), (y0 - i) + (r0 / 2) * math.cos(angle))
            painter.drawLine(x0 - (i / 2) * math.sin(angle), y0 + (i / 2) * math.cos(angle), (x0 - (i / 2) * math.sin(angle)) + r0, y0 + (i / 2) * math.cos(angle))
            painter.drawLine(x0 + i, y0, x0 + i - (r0 / 2) * math.sin(angle), y0 + (r0 / 2) * math.cos(angle))
        pen = QPen(Qt.blue, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(x0, y0, x0, y0 - self.acc_len_z)
        pen = QPen(Qt.green, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(x0, y0, x0 + self.acc_len_y, y0)
        pen = QPen(Qt.red, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(x0, y0, x0 - (self.acc_len_x / 2) * math.sin(angle), y0 + (self.acc_len_x / 2) * math.cos(angle))
        painter.setFont(QFont('SimSun', 10))
        gap = 5
        painter.setPen(Qt.blue)
        painter.drawText(x0 + gap, y0 - r0, 'Z')
        painter.setPen(Qt.green)
        painter.drawText(x0 + r0 + gap, y0, 'Y')
        painter.setPen(Qt.red)
        painter.drawText(x0 - (r0 / 2) * math.sin(angle) - 2 * gap, y0 + (r0 / 2) * math.cos(angle), 'X')
        painter.end()

    
    def retranslateText(self):
        _translate = QtCore.QCoreApplication.translate
        self.layoutComboBox.setItemText(0, _translate('MainWindow', 'Time Series'))
        self.layoutComboBox.setItemText(1, _translate('MainWindow', 'FFT Plot'))
        self.layoutComboBox.setItemText(2, _translate('MainWindow', 'Band Power'))
        self.layoutComboBox.setItemText(3, _translate('MainWindow', 'External trigger'))
        self.layoutComboBox.setItemText(4, _translate('MainWindow', 'Accelerometer'))
        self.layoutComboBox.setItemText(5, _translate('MainWindow', 'Networking'))
        self.layoutComboBox.setItemText(6, _translate('MainWindow', 'Battery'))
        self.layoutComboBox.setItemText(7, _translate('MainWindow', 'Brain topography'))
        self.xlabel.setText(_translate('MainWindow', '   X: 0'))
        self.zlabel.setText(_translate('MainWindow', '   Z: 0'))
        self.ylabel.setText(_translate('MainWindow', '   Y: 0'))
        self.DateModepushButton.setText(_translate('MainWindow', 'Start Accelerometer'))



class Figure_Canvas(FigureCanvas):
    
    def __init__(self, parent=None, width=3.9, height=2.7, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=100)
        super(Figure_Canvas, self).__init__(self.fig)
        self.ax = self.fig.add_subplot(111)

    
    def test(self):
        x = [
            1,
            2,
            3,
            4,
            5,
            6,
            7]
        y = [
            2,
            1,
            3,
            5,
            6,
            4,
            3]
        self.ax.plot(x, y)


