"""Main window: view layouts, log console, and shared window behaviour."""
import os
from datetime import datetime
from functools import partial
import platform
from freebci.design.main_window_ui import Ui_MainWindow
from freebci.design.plotWidget import myplotWidget
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore
from freebci.api.w_fft_plot import MyFFT_plot
from freebci.api.w_band_power import MyBandPower
from freebci.api.w_brain_topography import MyBrainTopography
from freebci.api.w_accelerometer import MyAccelerometer
from freebci.api.w_extrigger import MyExtrigger
from freebci.api.w_networking import MynetWidget
from freebci.api.w_time_series import MyTimeSeries
from freebci.api.w_battery import MyBattery
from freebci.api.my_layout import MyLayout
from freebci.api.my_console_window import MyConsoleWindow
from freebci.api.my_logger import MyLogger
from freebci.api.my_recording import MyRecording


class MainWindowInterface(Ui_MainWindow, QtWidgets.QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self, channel, parent=None):
        super(MainWindowInterface, self).__init__(parent)
        self.setupUi(self)
        self.myRecording = MyRecording()
        self.parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        user_path = os.path.expanduser('~')
        doc_path = os.environ.get('FREEBCI_HOME') or (user_path + '\\Documents\\FreeBCI')
        if not os.path.exists(doc_path):
            os.mkdir(doc_path)
        log_path = doc_path + '\\Console_Data'
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        log_file = doc_path + '\\Console_Data\\' + 'Console_' + datetime.now().strftime('%Y_%m_%d_%H%M%S') + '.txt'
        self.myLogger = MyLogger(log_file)
        self.myLogger.write('Console Log Started at Local Time: ' + datetime.now().strftime('%Y_%m_%d_%H%M%S'))
        self.myLogger.write('Operating System: ' + platform.system())
        self.myLogger.write('Welcome to FreeBCI GUI!')
        self.myLogger.write('openNewLogFile: opened log file: ' + str(log_file))
        self._chan = channel
        self.SamplingRate = 250
        self.log_file = log_file
        self.activeChannels = [ True for i in range(self._chan) ]
        self.FFTactiveChannels = [ False for i in range(self._chan) ]
        self.isSessionOn = False
        self.window_w = self.frameGeometry().width()
        self.window_h = self.frameGeometry().height()
        self.layout_index = 1
        self.initWidget()
        self.setWindowIcon(QtGui.QIcon(self.parent_path + '\\freebci\\design\\main_icon.png'))
        self.stackedWidget.setCurrentIndex(0)
        self.startButton_isclicked = False
        self.my_plot_widgets = []
        self.channel_list = [ str(i + 1) for i in range(self._chan) ]
        self.layoutpushButton.clicked.connect(self.layoutpushButton_click)
        self.terminalButton.clicked.connect(self.terminalButton_click)
        self.gridLayout_dict = {
            0: None,
            1: [
                self.gridLayout_3, self.gridLayout_12, self.gridLayout_13, self.gridLayout_14],
            2: [
                self.gridLayout_4, self.gridLayout_9, self.gridLayout_10],
            3: [
                self.gridLayout_5, self.gridLayout_7],
            4: [
                self.gridLayout_6],
            5: [
                self.gridLayout_18, self.gridLayout_20],
            6: [
                self.gridLayout_22, self.gridLayout_23, self.gridLayout_24],
            7: [
                self.gridLayout_28, self.gridLayout_26, self.gridLayout_27],
            8: [
                self.gridLayout_30, self.gridLayout_31, self.gridLayout_32]}
        self.subWidget_list = [
            'Time Series', 'FFT Plot', 'Band Power', 'External trigger', 'Accelerometer', 'Networking', 'Battery', 'Brain topography']
        self.layoutdic = {
            'test': None}
        self.resized.connect(self.getWindowSize)

    def resizeEvent(self, event):
        self.resized.emit()
        return super(MainWindowInterface, self).resizeEvent(event)

    def getWindowSize(self):
        self.window_w = self.frameGeometry().width()
        self.window_h = self.frameGeometry().height()
        self.myTimeSeries.screenResize(self.window_w, self.window_h, self.isTimeSeriesLong(self.layout_index))

    def layoutpushButton_click(self):
        if self.isSessionOn:
            self.LayoutWindow = MyLayout(self.parent_path)
            self.LayoutWindow.show()
            self.LayoutWindow._signal.connect(self.changeLayout)

    def terminalButton_click(self):
        self.ConsoleWindow = MyConsoleWindow(self.log_file, self.myLogger)
        self.myLogger._signal.connect(self.ConsoleWindow.appendText)
        self.ConsoleWindow.move(self.x() + 60, self.y() + 300)
        self.ConsoleWindow.show()

    def isTimeSeriesLong(self, index):
        if index == 1 or index == 2 or index == 3 or index == 6:
            return False
        else:
            return True

    def changeLayout(self, index):
        self.layout_index = index
        self.stackedWidget.setCurrentIndex(self.layout_index)
        self.myLogger.write('Layout [' + str(self.layout_index) + '] selected.')
        if index != 0:
            gridLayout_list = self.gridLayout_dict[self.layout_index]
            for i in range(len(gridLayout_list)):
                if gridLayout_list[i].itemAt(0) != None:
                    self.hideLayout.addWidget(gridLayout_list[i].itemAt(0).widget())
                gridLayout_list[i].addWidget(self.TextToWidget(self.subWidget_list[i]))
                if isinstance(self.subWidget_list[i], str):
                    self.layoutdic[self.subWidget_list[i]] = gridLayout_list[i]
            self.myTimeSeries.screenResize(self.window_w, self.window_h, self.isTimeSeriesLong(self.layout_index))

    def initWidget(self):
        self.is_myFFTPlot = False
        self.NotchComboBox.setCurrentIndex(1)
        self.BPFiltComboBox.setCurrentIndex(1)
        self.startButton.setStyleSheet('font: 12pt "黑体";background-color: rgb(192, 192, 192)')
        settings = {
            'channel': self._chan, 'activeChannels': self.FFTactiveChannels}
        self.myFFTPlot = MyFFT_plot(settings)
        self.myFFTPlot.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'FFT Plot', self.myFFTPlot.layoutComboBox))
        settings = {
            'channel': self._chan, 'activeChannels': self.activeChannels, 'width': self.window_w, 'height': self.window_h}
        self.is_myTimeSeries = False
        self.myTimeSeries = MyTimeSeries(settings)
        self.myTimeSeries.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Time Series', self.myTimeSeries.layoutComboBox))
        self.is_myBandPower = False
        self.myBandPower = MyBandPower()
        self.myBandPower.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Band Power', self.myBandPower.layoutComboBox))
        self.is_myNetWidget = False
        self.myNetWidget = MynetWidget(self._chan, self.SamplingRate)
        self.myNetWidget.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Networking', self.myNetWidget.layoutComboBox))
        self.is_myExtrigger = False
        self.myExtrigger = MyExtrigger()
        self.myExtrigger.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'External trigger', self.myExtrigger.layoutComboBox))
        self.is_myAccelerometer = False
        self.myAccelerometer = MyAccelerometer()
        self.myAccelerometer.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Accelerometer', self.myAccelerometer.layoutComboBox))
        self.is_myBattery = False
        self.myBattery = MyBattery()
        self.myBattery.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Battery', self.myBattery.layoutComboBox))
        self.is_myBrainTopography = False
        self.myBrainTopography = MyBrainTopography(self._chan)
        self.myBrainTopography.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Brain topography', self.myBrainTopography.layoutComboBox))

    def TextToWidget(self, widgetText):
        if widgetText == 'Time Series':
            self.myTimeSeries.layoutComboBox.setCurrentIndex(0)
            self.is_myTimeSeries = True
            return self.myTimeSeries
        elif widgetText == 'FFT Plot':
            self.is_myFFTPlot = True
            self.myFFTPlot.layoutComboBox.setCurrentIndex(1)
            return self.myFFTPlot
        elif widgetText == 'Band Power':
            self.myBandPower.layoutComboBox.setCurrentIndex(2)
            self.is_myBandPower = True
            return self.myBandPower
        elif widgetText == 'External trigger':
            self.myExtrigger.layoutComboBox.setCurrentIndex(3)
            self.is_myExtrigger = True
            return self.myExtrigger
        elif widgetText == 'Accelerometer':
            self.myAccelerometer.layoutComboBox.setCurrentIndex(4)
            self.is_myAccelerometer = True
            return self.myAccelerometer
        elif widgetText == 'Networking':
            self.is_myNetWidget = True
            self.myNetWidget.layoutComboBox.setCurrentIndex(5)
            return self.myNetWidget
        elif widgetText == 'Battery':
            self.myBattery.layoutComboBox.setCurrentIndex(6)
            self.is_myBattery = True
            return self.myBattery
        elif widgetText == 'Brain topography':
            self.myBrainTopography.layoutComboBox.setCurrentIndex(7)
            self.is_myBrainTopography = True
            return self.myBrainTopography
        self.myLogger.write('find widget fail:' + widgetText)

    def TextToWidget2(self, widgetText):
        if widgetText == 'FFT Plot':
            return self.myFFTPlot
        elif widgetText == 'Networking':
            return self.myNetWidget
        elif widgetText == 'Band Power':
            return self.myBandPower
        elif widgetText == 'External trigger':
            return self.myExtrigger
        elif widgetText == 'Accelerometer':
            return self.myAccelerometer
        elif widgetText == 'Brain topography':
            return self.myBrainTopography
        elif widgetText == 'Time Series':
            return self.myTimeSeries
        self.myLogger.write('Find widget fail1:' + widgetText)

    def TextToState(self, widgetText):
        if widgetText == 'FFT Plot':
            return self.is_myFFTPlot
        elif widgetText == 'Networking':
            return self.is_myNetWidget
        elif widgetText == 'Band Power':
            return self.is_myBandPower
        elif widgetText == 'External trigger':
            return self.is_myExtrigger
        elif widgetText == 'Accelerometer':
            return self.is_myAccelerometer
        elif widgetText == 'Battery':
            return self.is_myBattery
        elif widgetText == 'Brain topography':
            return self.is_myBrainTopography
        elif widgetText == 'Time Series':
            return self.is_myTimeSeries
        self.myLogger.write('Find widget fail2:' + widgetText)

    def changeSubWidget(self, old_sub_text, layoutBox):
        self.myLogger.write('---------')
        self.myLogger.write(self.layoutdic)
        new_sub_text = layoutBox.currentText()
        self.myLogger.write(old_sub_text + '--->' + new_sub_text)
        if new_sub_text == old_sub_text:
            return
        if self.TextToState(new_sub_text) == True:
            self.myLogger.write(new_sub_text + ' is existed')
            newWidget = self.TextToWidget(new_sub_text)
            for i in range(len(self.subWidget_list)):
                if self.TextToState(self.subWidget_list[i]) == False:
                    break
            self.changeSubWidget(new_sub_text, self.TextToWidget2(self.subWidget_list[i]).layoutComboBox)
        layoutBox.setCurrentIndex(self.subWidget_list.index(old_sub_text))
        self.myLogger.write('old_sub_text: ' + old_sub_text)
        self.myLogger.write(self.layoutdic)
        gridLayout = self.layoutdic[old_sub_text]
        if gridLayout.itemAt(0).widget() != None:
            self.hideLayout.addWidget(gridLayout.itemAt(0).widget())
        newWidget = self.TextToWidget(new_sub_text)
        gridLayout.addWidget(newWidget)
        self.layoutdic[new_sub_text] = gridLayout
        self.layoutdic[old_sub_text] = None
        if old_sub_text == 'FFT Plot':
            self.is_myFFTPlot = False
        elif old_sub_text == 'Networking':
            self.is_myNetWidget = False
        elif old_sub_text == 'Band Power':
            self.is_myBandPower = False
        elif old_sub_text == 'External trigger':
            self.is_myExtrigger = False
        elif old_sub_text == 'Accelerometer':
            self.is_myAccelerometer = False
        elif old_sub_text == 'Battery':
            self.is_myBattery = False
        elif old_sub_text == 'Brain topography':
            self.is_myBrainTopography = False
        elif old_sub_text == 'Time Series':
            self.is_myTimeSeries = False
        if new_sub_text == 'FFT Plot':
            self.is_myFFTPlot = True
        elif new_sub_text == 'Networking':
            self.is_myNetWidget = True
        elif new_sub_text == 'Band Power':
            self.is_myBandPower = True
        elif new_sub_text == 'External trigger':
            self.is_myExtrigger = True
        elif new_sub_text == 'Accelerometer':
            self.is_myAccelerometer = True
        elif new_sub_text == 'Battery':
            self.is_myBattery = True
        elif new_sub_text == 'Brain topography':
            self.is_myBrainTopography = True
        elif new_sub_text == 'Time Series':
            self.is_myTimeSeries = True
        self.myLogger.write('New Widget ' + new_sub_text + ' selected.')

    def backpushButton_click(self):
        self.stackedWidget_2.setCurrentIndex(0)

    def chanChooseBox_click(self):
        self.stackedWidget_2.setCurrentIndex(1)
