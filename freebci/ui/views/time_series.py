from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget
from freebci.design.plotWidget import plot_widget
from PyQt5.QtCore import Qt
import math
from freebci.ui.hardware_settings import HardwareSettingsDialog
from freebci.ui.hardware_warning import HardwareWarningDialog
from functools import partial

class TimeSeriesView(QtWidgets.QWidget):
    _signal = QtCore.pyqtSignal(int)
    
    def __init__(self, settings, parent=None):
        super(TimeSeriesView, self).__init__(parent)
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
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
        self.widget_2.setStyleSheet('background-color: #132A44')
        self.widget_2.setObjectName('widget_2')
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_3.setContentsMargins(8, 4, 8, 4)
        self.horizontalLayout_3.setSpacing(8)
        self.horizontalLayout_3.setObjectName('horizontalLayout_3')
        self.layoutComboBox = QtWidgets.QComboBox(self.widget_2)
        self.layoutComboBox.setStyleSheet('font: 9pt "Segoe UI";')
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
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.label_6 = QtWidgets.QLabel(self.widget_2)
        self.label_6.setStyleSheet('font: 9pt "Segoe UI";\ncolor:white;')
        self.label_6.setObjectName('label_6')
        self.horizontalLayout_3.addWidget(self.label_6)
        self.label_7 = QtWidgets.QLabel(self.widget_2)
        self.label_7.setStyleSheet('font: 9pt "Segoe UI";\ncolor:white;')
        self.label_7.setObjectName('label_7')
        self.horizontalLayout_3.addWidget(self.label_7)
        self.horizontalLayout_3.setStretch(0, 6)
        self.horizontalLayout_3.setStretch(1, 15)
        self.horizontalLayout_3.setStretch(2, 5)
        self.horizontalLayout_3.setStretch(3, 5)
        self.gridLayout_2.addWidget(self.widget_2, 0, 0, 1, 1)
        self.widget_3 = QtWidgets.QWidget(self.page)
        self.widget_3.setStyleSheet('background-color:#0F2238')
        self.widget_3.setObjectName('widget_3')
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget_3)
        self.horizontalLayout_4.setContentsMargins(8, 3, 8, 3)
        self.horizontalLayout_4.setSpacing(8)
        self.horizontalLayout_4.setObjectName('horizontalLayout_4')
        self.chanpushButton = QtWidgets.QPushButton(self.widget_3)
        self.chanpushButton.setStyleSheet('font: 9pt "Segoe UI";')
        self.chanpushButton.setObjectName('chanpushButton')
        self.horizontalLayout_4.addWidget(self.chanpushButton)
        self.hardwareButton = QtWidgets.QPushButton(self.widget_3)
        self.hardwareButton.setStyleSheet('font: 9pt "Segoe UI";')
        self.hardwareButton.setObjectName('hardwareButton')
        self.horizontalLayout_4.addWidget(self.hardwareButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.timeComboBox = QtWidgets.QComboBox(self.widget_3)
        self.timeComboBox.setStyleSheet('font: 9pt "Segoe UI";')
        self.timeComboBox.setObjectName('timeComboBox')
        self.timeComboBox.addItem('')
        self.timeComboBox.addItem('')
        self.timeComboBox.addItem('')
        self.timeComboBox.addItem('')
        self.timeComboBox.addItem('')
        self.horizontalLayout_4.addWidget(self.timeComboBox)
        self.voltComboBox = QtWidgets.QComboBox(self.widget_3)
        self.voltComboBox.setStyleSheet('font: 9pt "Segoe UI";')
        self.voltComboBox.setObjectName('voltComboBox')
        self.voltComboBox.addItem('')
        self.voltComboBox.addItem('')
        self.voltComboBox.addItem('')
        self.voltComboBox.addItem('')
        self.voltComboBox.addItem('')
        self.voltComboBox.addItem('')
        self.voltComboBox.addItem('')
        self.voltComboBox.addItem('')
        self.horizontalLayout_4.addWidget(self.voltComboBox)
        self.horizontalLayout_4.setStretch(0, 5)
        self.horizontalLayout_4.setStretch(1, 5)
        self.horizontalLayout_4.setStretch(2, 11)
        self.horizontalLayout_4.setStretch(3, 5)
        self.horizontalLayout_4.setStretch(4, 5)
        self.gridLayout_2.addWidget(self.widget_3, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName('page_2')
        self.gridLayout_3 = QtWidgets.QGridLayout(self.page_2)
        self.gridLayout_3.setObjectName('gridLayout_3')
        self.backpushButton = QtWidgets.QPushButton(self.page_2)
        self.backpushButton.setStyleSheet('border :2px solid ;border-color: cyan; background: dark blue; color: white')
        self.backpushButton.setObjectName('backpushButton')
        self.gridLayout_3.addWidget(self.backpushButton, 2, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_2)
        self.mainLayout.addWidget(self.stackedWidget, 0, 0, 1, 2)
        self.scrollArea = QtWidgets.QScrollArea(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName('scrollArea')
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 758, 524))
        self.scrollAreaWidgetContents.setObjectName('scrollAreaWidgetContents')
        self.gridLayout_7 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_7.setSpacing(0)
        self.gridLayout_7.setObjectName('gridLayout_7')
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName('verticalLayout')
        self.gridLayout_7.addLayout(self.verticalLayout, 1, 3, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.page.setStyleSheet('background-color:#0B1220')
        self.page_2.setStyleSheet('background-color:#0B1220')
        self.scrollArea.setStyleSheet('background-color:#0B1220; border:0')
        self.scrollAreaWidgetContents.setStyleSheet('background-color:#0B1220')
        self.mainLayout.addWidget(self.scrollArea, 1, 0, 1, 1)
        self.mainLayout.setColumnStretch(0, 2)
        self.mainLayout.setRowStretch(0, 2)
        self.mainLayout.setRowStretch(1, 30)
        self._settings = settings
        self._chan = settings['channel']
        self.activeChannels = settings['activeChannels']
        self.window_w = settings['width']
        self.window_h = settings['height']
        self.isTimeSeriesLong = False
        self.plot_widgets = [ plot_widget(i + 1) for i in (range(self._chan)) ]
        self.ischan_pushButtons = []
        self.resistanceList = [ True for i in (range(self._chan)) ]
        self.channelList = [ False for i in (range(self._chan)) ]
        for i in range(self._chan):
            self.ischan_pushButton = QtWidgets.QPushButton(self.page)
            self.ischan_pushButton.setObjectName('ischan_pushButton' + str(i + 1))
            self.ischan_pushButton.setText(str(i + 1))
            self.ischan_pushButton.clicked.connect(partial(self.ischan_pushButton_click, i))
            self.ischan_pushButton.setStyleSheet('border :2px solid ;border-color: cyan; background: dark blue; color: white')
            self.ischan_pushButtons.append(self.ischan_pushButton)
            self.gridLayout_3.addWidget(self.ischan_pushButton, i // 32, i % 32, 1, 1)
        self.gridLayout_3.setSpacing(2)
        self.gridLayout_3.setContentsMargins(2, 2, 2, 2)
        self.chanpushButton.clicked.connect(self.chanChooseBox_click)
        self.backpushButton.clicked.connect(self.backpushButton_click)
        self.layoutComboBox.setCurrentIndex(0)
        self.stackedWidget.setCurrentIndex(0)
        self.plot_widget_height = 840
        self.spcing_height = 6
        self.retranslateText()
        self.refreshPlotWidget()
        self.setLayout(self.mainLayout)

    
    def backpushButton_click(self):
        self.stackedWidget.setCurrentIndex(0)

    
    def chanChooseBox_click(self):
        self.stackedWidget.setCurrentIndex(1)

    
    def screenResize(self, width, height, isLong):
        self.window_w = width
        self.window_h = height
        self.isTimeSeriesLong = isLong
        window_w = self.geometry().width()
        window_h = self.geometry().height()
        self.plot_widget_height = window_h * 30 / 32
        critical_num = math.floor((self.plot_widget_height + self.spcing_height) / (120 + self.spcing_height))
        activeChannels_num = int(self.activeChannels.count(True))
        for i in range(len(self.plot_widgets)):
            if self.activeChannels[i]:
                if not isLong:
                    if activeChannels_num > critical_num:
                        self.plot_widgets[i].dataLabel.move(int(self.window_w / 2 - 260), 100)
                        self.plot_widgets[i].maxLabel.move(int(self.window_w / 50 + 50), 0)
                        self.plot_widgets[i].minLabel.move(int(self.window_w / 50 + 50), 100)
                    else:
                        moveHeight = -25 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if window_h > 500:
                            moveHeight1 = -28 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        else:
                            moveHeight1 = -35 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if activeChannels_num != 1:
                            self.plot_widgets[i].dataLabel.move(int(self.window_w / 2 - 260), moveHeight)
                            self.plot_widgets[i].maxLabel.move(int(self.window_w / 50 + 50), 0)
                            self.plot_widgets[i].minLabel.move(int(self.window_w / 50 + 50), moveHeight)
                        elif activeChannels_num == 1:
                            self.plot_widgets[i].dataLabel.move(int(self.window_w / 2 - 260), moveHeight1)
                            self.plot_widgets[i].maxLabel.move(int(self.window_w / 50 + 50), 0)
                            self.plot_widgets[i].minLabel.move(int(self.window_w / 50 + 50), moveHeight1)
                else:
                    self.plot_widgets[i].dataLabel.move(int(self.window_w - 300), 100)
                    self.plot_widgets[i].maxLabel.move(int(self.window_w / 30 + 90), 0)
                    self.plot_widgets[i].minLabel.move(int(self.window_w / 30 + 90), 100)
                    if activeChannels_num > critical_num:
                        self.plot_widgets[i].dataLabel.move(int(self.window_w - 300), 100)
                        self.plot_widgets[i].maxLabel.move(int(self.window_w / 30 + 90), 0)
                        self.plot_widgets[i].minLabel.move(int(self.window_w / 30 + 90), 100)
                    else:
                        moveHeight = -25 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if window_h > 500:
                            moveHeight1 = -28 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        else:
                            moveHeight1 = -35 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if activeChannels_num != 1:
                            self.plot_widgets[i].dataLabel.move(int(self.window_w - 300), moveHeight)
                            self.plot_widgets[i].maxLabel.move(int(self.window_w / 30 + 90), 0)
                            self.plot_widgets[i].minLabel.move(int(self.window_w / 30 + 90), moveHeight)
                        elif activeChannels_num == 1:
                            self.plot_widgets[i].dataLabel.move(int(self.window_w - 300), moveHeight1)
                            self.plot_widgets[i].maxLabel.move(int(self.window_w / 30 + 90), 0)
                            self.plot_widgets[i].minLabel.move(int(self.window_w / 30 + 90), moveHeight1)

    def ischan_pushButton_click(self, _chan):
        if self.activeChannels[_chan]:
            self.ischan_pushButtons[_chan].setStyleSheet('border :2px solid ;border-color: cyan; background: gray; color: white')
        else:
            self.ischan_pushButtons[_chan].setStyleSheet('border :2px solid ;border-color: cyan; background: dark blue; color: white')
        self.activeChannels[_chan] = not self.activeChannels[_chan]
        self.refreshPlotWidget()

    def refreshPlotWidget(self):
        window_w = self.geometry().width()
        window_h = self.geometry().height()
        self.plot_widget_height = window_h * 30 / 32
        critical_num = math.floor((self.plot_widget_height + self.spcing_height) / (120 + self.spcing_height))
        activeChannels_num = int(self.activeChannels.count(True))
        for i in range(self.verticalLayout.count()):
            widget = self.verticalLayout.itemAt(i).widget()
            chan = int(widget.channelButton.text()) - 1
            self.resistanceList[chan] = widget.isResistance
            self.channelList[chan] = widget.ischannelClick
            widget.deleteLater()
        for i in range(self._chan):
            if self.activeChannels[i]:
                self.plot_widget = plot_widget(i + 1)
                self.plot_widget.setObjectName('plot_widget' + str(i + 1))
                if self.channelList[i] == True:
                    self.plot_widget.channelButton.setStyleSheet('width: 30px;height: 30px; border-radius: 15px;font-size: 15px;color: white; background: gray;')
                    self.plot_widget.ischannelClick = True
                if self.resistanceList[i] == False:
                    self.plot_widget.resistancePushButton.setStyleSheet('QPushButton {width: 30px;height: 30px;border-radius: 15px;font-size: 15px;color: white;font: 12pt "Segoe UI";background: black ;}')
                    self.plot_widget.isResistance = False
                self.plot_widgets[i] = self.plot_widget
                self.verticalLayout.addWidget(self.plot_widget)
                if not self.isTimeSeriesLong:
                    if activeChannels_num > critical_num:
                        self.plot_widget.dataLabel.move(int(self.window_w / 2 - 260), 100)
                        self.plot_widget.maxLabel.move(int(self.window_w / 50 + 50), 0)
                        self.plot_widget.minLabel.move(int(self.window_w / 50 + 50), 100)
                    else:
                        moveHeight = -25 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if window_h > 500:
                            moveHeight1 = -28 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        else:
                            moveHeight1 = -35 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if activeChannels_num != 1:
                            self.plot_widget.dataLabel.move(int(self.window_w / 2 - 260), moveHeight)
                            self.plot_widget.maxLabel.move(int(self.window_w / 50 + 50), 0)
                            self.plot_widget.minLabel.move(int(self.window_w / 50 + 50), moveHeight)
                        elif activeChannels_num == 1:
                            self.plot_widget.dataLabel.move(int(self.window_w / 2 - 260), moveHeight1)
                            self.plot_widget.maxLabel.move(int(self.window_w / 50 + 50), 0)
                            self.plot_widget.minLabel.move(int(self.window_w / 50 + 50), moveHeight1)
                else:
                    if activeChannels_num > critical_num:
                        self.plot_widget.dataLabel.move(int(self.window_w - 300), 100)
                        self.plot_widget.maxLabel.move(int(self.window_w / 30 + 90), 0)
                        self.plot_widget.minLabel.move(int(self.window_w / 30 + 90), 100)
                    else:
                        moveHeight = -25 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if window_h > 500:
                            moveHeight1 = -28 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        else:
                            moveHeight1 = -35 + (self.plot_widget_height - self.spcing_height * (activeChannels_num - 1)) / activeChannels_num
                        if activeChannels_num != 1:
                            self.plot_widget.dataLabel.move(int(self.window_w - 300), moveHeight)
                            self.plot_widget.maxLabel.move(int(self.window_w / 30 + 90), 0)
                            self.plot_widget.minLabel.move(int(self.window_w / 30 + 90), moveHeight)
                        elif activeChannels_num == 1:
                            self.plot_widget.dataLabel.move(int(self.window_w - 300), moveHeight1)
                            self.plot_widget.maxLabel.move(int(self.window_w / 30 + 90), 0)
                            self.plot_widget.minLabel.move(int(self.window_w / 30 + 90), moveHeight1)
                self._signal.emit(i)

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
        self.label_6.setText(_translate('MainWindow', 'Time Window'))
        self.label_7.setText(_translate('MainWindow', 'Vert Scale'))
        self.chanpushButton.setText(_translate('MainWindow', 'Channel'))
        self.hardwareButton.setText(_translate('MainWindow', 'Hardware settings'))
        self.timeComboBox.setItemText(0, _translate('MainWindow', 'Default time 5s'))
        self.timeComboBox.setItemText(1, _translate('MainWindow', '1 sec'))
        self.timeComboBox.setItemText(2, _translate('MainWindow', '3 sec'))
        self.timeComboBox.setItemText(3, _translate('MainWindow', '5 sec'))
        self.timeComboBox.setItemText(4, _translate('MainWindow', '10 sec'))
        self.voltComboBox.setItemText(0, _translate('MainWindow', 'Auto1'))
        self.voltComboBox.setItemText(1, _translate('MainWindow', 'Auto2'))
        self.voltComboBox.setItemText(2, _translate('MainWindow', '50 uV'))
        self.voltComboBox.setItemText(3, _translate('MainWindow', '100 uV'))
        self.voltComboBox.setItemText(4, _translate('MainWindow', '200 uV'))
        self.voltComboBox.setItemText(5, _translate('MainWindow', '400 uV'))
        self.voltComboBox.setItemText(6, _translate('MainWindow', '1000 uV'))
        self.voltComboBox.setItemText(7, _translate('MainWindow', '10000 uV'))
        self.backpushButton.setText(_translate('MainWindow', '↩'))

