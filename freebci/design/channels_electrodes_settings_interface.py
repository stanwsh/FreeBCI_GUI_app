import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from freebci.design.channels_electrodes_settings import Ui_Channels_electrodes_settings
from freebci.ui.electrodes_position import ElectrodesPosition
from PyQt5.QtCore import Qt
import numpy as np
import numpy as np
import pandas as pd


class channels_electrodes_Settings_interface(QtWidgets.QDialog, Ui_Channels_electrodes_settings):
    def __init__(self, hardwareinfo, parent=None):
        super(channels_electrodes_Settings_interface, self).__init__(parent)
        self.setupUi(self)
        self._chan = hardwareinfo.channel_num
        self.ischanClick = hardwareinfo.activeChannels
        _translate = QtCore.QCoreApplication.translate
        self.colors = [
            'red',
            'green',
            'blue',
            '#E3CF57',
            'rgb(0,255,255)',
            'purple',
            'black',
            'rgb(210,180,140)']
        self.electrodeNameComboBoxs = [ None for i in range(self._chan) ]
        self.nameButtons = [ None for i in range(self._chan) ]
        for i in range(self._chan):
            if self.ischanClick[i]:
                self.nameButton = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
                self.nameButton.setStyleSheet('QPushButton {\n    width: 40px;\n    height: 40px;\n    border-radius: 20px;\n    font-size: 20px;\n    color: white;\n    background: gray ; /* 默认颜色 */\n}\n')
                self.nameButton.setObjectName('nameButton' + str(i + 1))
                self.nameButton.setText(str(i + 1))
                self.nameButton.setMinimumSize(QtCore.QSize(40, 40))
                self.nameButton.setMaximumSize(QtCore.QSize(40, 40))
                self.nameButtons[i] = self.nameButton
                self.gridLayout_2.addWidget(self.nameButton, 2 * i + 1, 0, 1, 1)
                self.electrodeNameComboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
                self.electrodeNameComboBox.setStyleSheet('font: 12pt "黑体";')
                self.electrodeNameComboBox.setObjectName('electrodeNameComboBox' + str(i + 1))
                self.electrodeNameComboBox.setEditable(True)
                self.electrodeNameComboBox.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
                self.electrodeNameComboBox.lineEdit().setStyleSheet('font: 12pt "黑体";')
                self.electrodeNameComboBox_list = [ None for i in range(self._chan) ]
                Electrodes_name = ElectrodesPosition.ElectrodesName_32
                self.channels32 = np.array(Electrodes_name)
                self.channels = np.array(Electrodes_name).tolist()
                for channum in range(self._chan - 1):
                    self.electrodeNameComboBox_list[channum] = str(self.channels[channum])
                self.electrodeNameComboBox_list[self._chan - 1] = 'Unused (leave blank)'
                self.electrodeNameComboBox.addItems(self.electrodeNameComboBox_list)
                self.electrodeNameComboBox.setCurrentIndex(i)
                self.electrodeNameComboBoxs[i] = self.electrodeNameComboBox
                self.gridLayout_2.addWidget(self.electrodeNameComboBox, 2 * i + 1, 1, 1, 1)
                self.spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
                self.gridLayout_2.addItem(self.spacerItem, 2 * i + 2, 1, 1, 1)
        for i in range(self._chan):
            if self.ischanClick[i]:
                self.gridLayout_2.setRowStretch(2 * i + 1, 1)
