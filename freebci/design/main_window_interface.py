"""Main window: view layouts, log console, and shared window behaviour."""
import os
from datetime import datetime
from functools import partial
import platform
from freebci.design.main_window_ui import Ui_MainWindow
from freebci.design.plotWidget import plot_widget
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore
from freebci.ui.views.fft_plot import FFTPlotView
from freebci.ui.views.band_power import BandPowerView
from freebci.ui.views.topography import TopographyView
from freebci.ui.views.accelerometer import AccelerometerView
from freebci.ui.views.external_trigger import ExternalTriggerView
from freebci.ui.views.networking import NetworkView
from freebci.ui.views.time_series import TimeSeriesView
from freebci.ui.views.battery import BatteryView
from freebci.ui.layout_dialog import LayoutDialog
from freebci.ui.console_window import ConsoleWindow
from freebci.ui.console_logger import ConsoleLogger
from freebci.ui.empty_state import EmptyState
from freebci.ui.recording_paths import RecordingPaths


class MainWindowInterface(Ui_MainWindow, QtWidgets.QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self, channel, parent=None):
        super(MainWindowInterface, self).__init__(parent)
        self.setupUi(self)
        self.recording = RecordingPaths()
        self.parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        user_path = os.path.expanduser('~')
        doc_path = os.environ.get('FREEBCI_HOME') or (user_path + '\\Documents\\FreeBCI')
        if not os.path.exists(doc_path):
            os.mkdir(doc_path)
        log_path = doc_path + '\\Console_Data'
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        log_file = doc_path + '\\Console_Data\\' + 'Console_' + datetime.now().strftime('%Y_%m_%d_%H%M%S') + '.txt'
        self.logger = ConsoleLogger(log_file)
        self.logger.write('Console Log Started at Local Time: ' + datetime.now().strftime('%Y_%m_%d_%H%M%S'))
        self.logger.write('Operating System: ' + platform.system())
        self.logger.write('Welcome to FreeBCI GUI!')
        self.logger.write('openNewLogFile: opened log file: ' + str(log_file))
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
        self.empty_state = EmptyState(self._show_board_menu, self.demo_click, self.page_0)
        self.Layout00.hide()
        self.gridLayout.addWidget(self.empty_state, 0, 0, 1, 1)
        self.startButton_isclicked = False
        self.plot_widgets = []
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
        self._apply_compact_layout()
        self.resized.connect(self.getWindowSize)

    def _apply_compact_layout(self):
        """Use consistent gutters between the dashboard panels."""
        for index in range(self.stackedWidget.count()):
            page = self.stackedWidget.widget(index)
            layout = page.layout()
            if layout is not None:
                layout.setContentsMargins(8, 8, 8, 8)
                layout.setSpacing(8)
        for layouts in self.gridLayout_dict.values():
            if not layouts:
                continue
            for layout in layouts:
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(8)

    def _show_board_menu(self):
        button = self.empty_state.connectButton
        self.menu.popup(button.mapToGlobal(QtCore.QPoint(0, button.height())))

    def resizeEvent(self, event):
        self.resized.emit()
        return super(MainWindowInterface, self).resizeEvent(event)

    def getWindowSize(self):
        self.window_w = self.frameGeometry().width()
        self.window_h = self.frameGeometry().height()
        self.time_series.screenResize(self.window_w, self.window_h, self.isTimeSeriesLong(self.layout_index))

    def layoutpushButton_click(self):
        if self.isSessionOn:
            self.LayoutWindow = LayoutDialog(self.parent_path)
            self.LayoutWindow.show()
            self.LayoutWindow._signal.connect(self.changeLayout)

    def terminalButton_click(self):
        self.ConsoleWindow = ConsoleWindow(self.log_file, self.logger)
        self.logger._signal.connect(self.ConsoleWindow.appendText)
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
        self.logger.write('Layout [' + str(self.layout_index) + '] selected.')
        if index != 0:
            gridLayout_list = self.gridLayout_dict[self.layout_index]
            for i in range(len(gridLayout_list)):
                if gridLayout_list[i].itemAt(0) != None:
                    self.hideLayout.addWidget(gridLayout_list[i].itemAt(0).widget())
                gridLayout_list[i].addWidget(self.TextToWidget(self.subWidget_list[i]))
                if isinstance(self.subWidget_list[i], str):
                    self.layoutdic[self.subWidget_list[i]] = gridLayout_list[i]
            self.time_series.screenResize(self.window_w, self.window_h, self.isTimeSeriesLong(self.layout_index))

    def initWidget(self):
        self.is_fft_plot = False
        self.NotchComboBox.setCurrentIndex(1)
        self.BPFiltComboBox.setCurrentIndex(1)
        self.startButton.setStyleSheet('background-color: #64748B; color: #FFFFFF;')
        settings = {
            'channel': self._chan, 'activeChannels': self.FFTactiveChannels}
        self.fft_plot = FFTPlotView(settings)
        self.fft_plot.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'FFT Plot', self.fft_plot.layoutComboBox))
        settings = {
            'channel': self._chan, 'activeChannels': self.activeChannels, 'width': self.window_w, 'height': self.window_h}
        self.is_time_series = False
        self.time_series = TimeSeriesView(settings)
        self.time_series.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Time Series', self.time_series.layoutComboBox))
        self.is_band_power = False
        self.band_power = BandPowerView()
        self.band_power.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Band Power', self.band_power.layoutComboBox))
        self.is_networking = False
        self.networking = NetworkView(self._chan, self.SamplingRate)
        self.networking.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Networking', self.networking.layoutComboBox))
        self.is_external_trigger = False
        self.external_trigger = ExternalTriggerView()
        self.external_trigger.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'External trigger', self.external_trigger.layoutComboBox))
        self.is_accelerometer = False
        self.accelerometer = AccelerometerView()
        self.accelerometer.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Accelerometer', self.accelerometer.layoutComboBox))
        self.is_battery = False
        self.battery = BatteryView()
        self.battery.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Battery', self.battery.layoutComboBox))
        self.is_topography = False
        self.topography = TopographyView(self._chan)
        self.topography.layoutComboBox.activated.connect(partial(self.changeSubWidget, 'Brain topography', self.topography.layoutComboBox))

    def TextToWidget(self, widgetText):
        if widgetText == 'Time Series':
            self.time_series.layoutComboBox.setCurrentIndex(0)
            self.is_time_series = True
            return self.time_series
        elif widgetText == 'FFT Plot':
            self.is_fft_plot = True
            self.fft_plot.layoutComboBox.setCurrentIndex(1)
            return self.fft_plot
        elif widgetText == 'Band Power':
            self.band_power.layoutComboBox.setCurrentIndex(2)
            self.is_band_power = True
            return self.band_power
        elif widgetText == 'External trigger':
            self.external_trigger.layoutComboBox.setCurrentIndex(3)
            self.is_external_trigger = True
            return self.external_trigger
        elif widgetText == 'Accelerometer':
            self.accelerometer.layoutComboBox.setCurrentIndex(4)
            self.is_accelerometer = True
            return self.accelerometer
        elif widgetText == 'Networking':
            self.is_networking = True
            self.networking.layoutComboBox.setCurrentIndex(5)
            return self.networking
        elif widgetText == 'Battery':
            self.battery.layoutComboBox.setCurrentIndex(6)
            self.is_battery = True
            return self.battery
        elif widgetText == 'Brain topography':
            self.topography.layoutComboBox.setCurrentIndex(7)
            self.is_topography = True
            return self.topography
        self.logger.write('find widget fail:' + widgetText)

    def TextToWidget2(self, widgetText):
        if widgetText == 'FFT Plot':
            return self.fft_plot
        elif widgetText == 'Networking':
            return self.networking
        elif widgetText == 'Band Power':
            return self.band_power
        elif widgetText == 'External trigger':
            return self.external_trigger
        elif widgetText == 'Accelerometer':
            return self.accelerometer
        elif widgetText == 'Brain topography':
            return self.topography
        elif widgetText == 'Time Series':
            return self.time_series
        self.logger.write('Find widget fail1:' + widgetText)

    def TextToState(self, widgetText):
        if widgetText == 'FFT Plot':
            return self.is_fft_plot
        elif widgetText == 'Networking':
            return self.is_networking
        elif widgetText == 'Band Power':
            return self.is_band_power
        elif widgetText == 'External trigger':
            return self.is_external_trigger
        elif widgetText == 'Accelerometer':
            return self.is_accelerometer
        elif widgetText == 'Battery':
            return self.is_battery
        elif widgetText == 'Brain topography':
            return self.is_topography
        elif widgetText == 'Time Series':
            return self.is_time_series
        self.logger.write('Find widget fail2:' + widgetText)

    def changeSubWidget(self, old_sub_text, layoutBox):
        self.logger.write('---------')
        self.logger.write(self.layoutdic)
        new_sub_text = layoutBox.currentText()
        self.logger.write(old_sub_text + '--->' + new_sub_text)
        if new_sub_text == old_sub_text:
            return
        if self.TextToState(new_sub_text) == True:
            self.logger.write(new_sub_text + ' is existed')
            newWidget = self.TextToWidget(new_sub_text)
            for i in range(len(self.subWidget_list)):
                if self.TextToState(self.subWidget_list[i]) == False:
                    break
            self.changeSubWidget(new_sub_text, self.TextToWidget2(self.subWidget_list[i]).layoutComboBox)
        layoutBox.setCurrentIndex(self.subWidget_list.index(old_sub_text))
        self.logger.write('old_sub_text: ' + old_sub_text)
        self.logger.write(self.layoutdic)
        gridLayout = self.layoutdic[old_sub_text]
        if gridLayout.itemAt(0).widget() != None:
            self.hideLayout.addWidget(gridLayout.itemAt(0).widget())
        newWidget = self.TextToWidget(new_sub_text)
        gridLayout.addWidget(newWidget)
        self.layoutdic[new_sub_text] = gridLayout
        self.layoutdic[old_sub_text] = None
        if old_sub_text == 'FFT Plot':
            self.is_fft_plot = False
        elif old_sub_text == 'Networking':
            self.is_networking = False
        elif old_sub_text == 'Band Power':
            self.is_band_power = False
        elif old_sub_text == 'External trigger':
            self.is_external_trigger = False
        elif old_sub_text == 'Accelerometer':
            self.is_accelerometer = False
        elif old_sub_text == 'Battery':
            self.is_battery = False
        elif old_sub_text == 'Brain topography':
            self.is_topography = False
        elif old_sub_text == 'Time Series':
            self.is_time_series = False
        if new_sub_text == 'FFT Plot':
            self.is_fft_plot = True
        elif new_sub_text == 'Networking':
            self.is_networking = True
        elif new_sub_text == 'Band Power':
            self.is_band_power = True
        elif new_sub_text == 'External trigger':
            self.is_external_trigger = True
        elif new_sub_text == 'Accelerometer':
            self.is_accelerometer = True
        elif new_sub_text == 'Battery':
            self.is_battery = True
        elif new_sub_text == 'Brain topography':
            self.is_topography = True
        elif new_sub_text == 'Time Series':
            self.is_time_series = True
        self.logger.write('New Widget ' + new_sub_text + ' selected.')

    def backpushButton_click(self):
        self.stackedWidget_2.setCurrentIndex(0)

    def chanChooseBox_click(self):
        self.stackedWidget_2.setCurrentIndex(1)
