from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from freebci.api.my_electrodes_position import ElectrodesPosition
import sys
import numpy as np
import random
import time
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import pandas as pd
import mne

class MyBrainTopography(QtWidgets.QWidget):
    
    def __init__(self, chan: int, parent=None):
        super(MyBrainTopography, self).__init__(parent)
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setContentsMargins(1, 0, 0, 0)
        self.mainLayout.setSpacing(1)
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
        self.horizontalLayout_3.addWidget(self.layoutComboBox)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
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
        self.chan_electrode_settingspushButton = QtWidgets.QPushButton(self.widget_3)
        self.chan_electrode_settingspushButton.setStyleSheet('font: 75 10pt "等线";')
        self.chan_electrode_settingspushButton.setObjectName('chan_electrode_settingspushButton')
        self.horizontalLayout_4.addWidget(self.chan_electrode_settingspushButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.horizontalLayout_4.setStretch(0, 5)
        self.horizontalLayout_4.setStretch(1, 26)
        self.gridLayout_2.addWidget(self.widget_3, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName('page_2')
        self.stackedWidget.addWidget(self.page_2)
        self.mainLayout.addWidget(self.stackedWidget, 0, 0, 1, 2)
        self.mainLayout.setColumnStretch(0, 2)
        self.mainLayout.setColumnStretch(1, 30)
        self.mainLayout.setRowStretch(0, 6)
        self.mainLayout.setRowStretch(1, 5)
        self.mainLayout.setRowStretch(2, 5)
        self.mainLayout.setRowStretch(3, 5)
        self.mainLayout.setRowStretch(4, 5)
        self.mainLayout.setRowStretch(5, 5)
        self.mainLayout.setRowStretch(6, 5)
        self.mainLayout.setRowStretch(7, 5)
        self.mainLayout.setRowStretch(8, 5)
        self.mainLayout.setRowStretch(9, 5)
        self.mainLayout.setRowStretch(10, 5)
        self.mainLayout.setRowStretch(11, 5)
        self.mainLayout.setRowStretch(12, 5)
        self.retranslateText()
        self._chan = chan
        if self._chan == 32:
            Topography_data = [ [ 0 for col in (range(500)) ] for row in (range(31)) ]

        elif self._chan == 64:
            Topography_data = [ [ 0 for col in (range(500)) ] for row in (range(62)) ]

        elif self._chan == 16:
            Topography_data = [ [ 0 for col in (range(500)) ] for row in (range(16)) ]

        else:
            Topography_data = [ [ 0 for col in (range(500)) ] for row in (range(31)) ]

        Electrodes_Position = ElectrodesPosition()
        electrodes_name = f'''ElectrodesName_{str(self._chan)}'''
        electrodes_pos = f'''ElectrodesPos_{str(self._chan)}'''
        if hasattr(Electrodes_Position, electrodes_name):
            Electrodes_name = getattr(Electrodes_Position, electrodes_name)
        else:
            Electrodes_name = Electrodes_Position.ElectrodesName_32
        if hasattr(Electrodes_Position, electrodes_pos):
            Electrodes_pos = getattr(Electrodes_Position, electrodes_pos)
        else:
            Electrodes_pos = Electrodes_Position.ElectrodesPos_32
        self.channels = np.array(Electrodes_name)
        self.value = np.array(Electrodes_pos)
        self.mne_channels = np.array(Electrodes_name).tolist()
        info = mne.create_info(ch_names=self.mne_channels, sfreq=250, ch_types='eeg')
        list_dic = dict(zip(self.channels, self.value))
        montage = mne.channels.make_dig_montage(ch_pos=list_dic, nasion=[
            5.27205792e-18,
            0.0860992398,
            -0.0401487349], lpa=[
            -0.08609924,
            -0.0,
            -0.04014873], rpa=[
            0.08609924,
            0.0,
            -0.04014873])
        self.topofig_num = 1
        self.plotfig(Topography_data, info, montage)
        self.layoutComboBox.setCurrentIndex(4)
        self.setLayout(self.mainLayout)

    
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
        self.chan_electrode_settingspushButton.setText(_translate('MainWindow', 'Channels-electrodes settings'))

    
    def plotfig(self, Topography_data, info, montage):
        F = MyFigure(width=10, height=10, dpi=50)
        evoked = mne.EvokedArray(Topography_data, info)
        evoked.set_montage(montage)
        step = int(len(Topography_data[0]) / self.topofig_num)
        i = 0
        while i < self.topofig_num:
            F.axes.cla()
            mne.viz.plot_topomap(evoked.data[:, (i + 1) * step - 1], evoked.info, show=False, axes=F.axes)
            F.fig.canvas.draw_idle()
            plt.pause(0.001)
            i += 1

        self.mainLayout.addWidget(F, 2, 0, 15, 2)


class MyFigure(FigureCanvas):

    def __init__(self, width=4, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MyFigure, self).__init__(self.fig)
        self.axes = self.fig.add_subplot(111)

