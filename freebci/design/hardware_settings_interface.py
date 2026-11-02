import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from freebci.design.hardware_settings_base import Ui_Hardware_settings


class hardwareSettings_interface(QtWidgets.QDialog, Ui_Hardware_settings):
    def __init__(self, hardwareinfo, parent=None):
        super(hardwareSettings_interface, self).__init__(parent)
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
        self.PCAGainComboBoxs = [ None for i in range(self._chan) ]
        self.InputComboBoxs = [ None for i in range(self._chan) ]
        self.BiasComboBoxs = [ None for i in range(self._chan) ]
        self.SRB1ComboBoxs = [ None for i in range(self._chan) ]
        self.SRB2comboBoxs = [ None for i in range(self._chan) ]
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
                self.PCAGainComboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
                self.PCAGainComboBox.setStyleSheet('font: 12pt "黑体";')
                self.PCAGainComboBox.setObjectName('PCAGainComboBox' + str(i + 1))
                self.PCAGainComboBox_list = [
                    'X24',
                    'X1',
                    'X2',
                    'X4',
                    'X6',
                    'X8',
                    'X10',
                    'X12']
                self.PCAGainComboBox.addItems(self.PCAGainComboBox_list)
                self.PCAGainComboBoxs[i] = self.PCAGainComboBox
                self.gridLayout_2.addWidget(self.PCAGainComboBox, 2 * i + 1, 1, 1, 1)
                self.InputComboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
                self.InputComboBox.setStyleSheet('font: 12pt "黑体";')
                self.InputComboBox.setObjectName('InputComboBox' + str(i + 1))
                self.InputComboBox_list = [
                    'Normal',
                    'Temp',
                    'Test',
                    'BIAS DRP',
                    'BIAS DRN',
                    'Shorted',
                    'Bias Meas',
                    'MVDD']
                self.InputComboBox.addItems(self.InputComboBox_list)
                self.InputComboBoxs[i] = self.InputComboBox
                self.gridLayout_2.addWidget(self.InputComboBox, 2 * i + 1, 2, 1, 1)
                self.BiasComboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
                self.BiasComboBox.setStyleSheet('font: 12pt "黑体";')
                self.BiasComboBox.setObjectName('BiasComboBox' + str(i + 1))
                self.BiasComboBox_list = ['Yes', 'No']
                self.BiasComboBox.addItems(self.BiasComboBox_list)
                self.BiasComboBox.setStyleSheet('font: 12pt "黑体"; background: rgb(240, 255, 240);')
                self.BiasComboBoxs[i] = self.BiasComboBox
                self.gridLayout_2.addWidget(self.BiasComboBox, 2 * i + 1, 3, 1, 1)
                self.SRB2comboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
                self.SRB2comboBox.setStyleSheet('font: 12pt "黑体";')
                self.SRB2comboBox.setObjectName('SRB2comboBox' + str(i + 1))
                self.SRB2comboBox_list = ['On', 'Off']
                self.SRB2comboBox.addItems(self.SRB2comboBox_list)
                self.SRB2comboBox.setStyleSheet('font: 12pt "黑体"; background: rgb(240, 255, 240);')
                self.SRB2comboBox.setEnabled(True)
                self.SRB2comboBoxs[i] = self.SRB2comboBox
                self.gridLayout_2.addWidget(self.SRB2comboBox, 2 * i + 1, 4, 1, 1)
                self.SRB1comboBox = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
                self.SRB1comboBox.setStyleSheet('font: 12pt "黑体";')
                self.SRB1comboBox.setObjectName('SRB1comboBox' + str(i + 1))
                self.SRB1comboBox_list = ['Off', 'On']
                self.SRB1comboBox.addItems(self.SRB1comboBox_list)
                self.SRB1comboBox.setStyleSheet('font: 12pt "黑体"; background: rgb(255, 240, 245);')
                self.SRB1comboBox.setEnabled(True)
                self.SRB1ComboBoxs[i] = self.SRB1comboBox
                self.gridLayout_2.addWidget(self.SRB1comboBox, 2 * i + 1, 5, 1, 1)
                self.spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
                self.gridLayout_2.addItem(self.spacerItem, 2 * i + 2, 1, 1, 1)
        for i in range(self._chan):
            if self.ischanClick[i]:
                self.gridLayout_2.setRowStretch(2 * i + 1, 1)
