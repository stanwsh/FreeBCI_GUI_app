import os
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from freebci.ui.connection_info import HardwareInfo, ConnectionInfo
from freebci.core.settings import (
    ChannelSettings,
    HardwareSettings,
    SettingsError,
    load_settings,
    save_settings,
    writable_settings_path,
)
from freebci.design.hardware_settings_interface import hardwareSettings_interface
from freebci.core.hardware_settings_protocol import HardwareSettingsProtocol
from freebci.ui.workers.settings_commands import SettingsCommandWorker
from functools import partial
import xml.etree.ElementTree as ET


class HardwareSettingsDialog(hardwareSettings_interface):
    _signal = QtCore.pyqtSignal(HardwareInfo)
    _signal_con = QtCore.pyqtSignal(ConnectionInfo)

    def __init__(self, connect_info, hardwareInfo, Logger):
        super(HardwareSettingsDialog, self).__init__(hardwareInfo)
        self.connect_info = connect_info
        self.board = self.connect_info.board
        self.hardwareInfo = hardwareInfo
        self.logger = Logger
        max_samplingRate = self.connect_info.id_list[self.connect_info.board_id - 2023][5]
        n_rateCombobox = self.rateComboBox.count() - 1
        while n_rateCombobox >= 0:
            if str(max_samplingRate) + ' Hz' == str(self.rateComboBox.itemText(n_rateCombobox)):
                break
            self.rateComboBox.removeItem(n_rateCombobox)
            n_rateCombobox -= 1
        self.saveButton.clicked.connect(self.saveButton_click)
        self.loadButton.clicked.connect(self.loadButton_click)
        self.sendButton.clicked.connect(self.sendButton_click)
        self.isActiveSetting = [ False for i in range(self.hardwareInfo.channel_num) ]
        self.logger.write(self.ischanClick)
        for i in range(len(self.PCAGainComboBoxs)):
            if self.ischanClick[i]:
                self.PCAGainComboBoxs[i].activated.connect(partial(self.PCAGainComboBoxs_click, i))
                self.InputComboBoxs[i].activated.connect(partial(self.InputComboBoxs_click, i))
                self.BiasComboBoxs[i].activated.connect(partial(self.BiasComboBoxs_click, i))
                self.SRB1ComboBoxs[i].activated.connect(partial(self.SRB1ComboBoxs_click, i))
                self.SRB2comboBoxs[i].activated.connect(partial(self.SRB2ComboBoxs_click, i))
        if self.connect_info.id_list[self.connect_info.board_id - 2023][4] == 0:
            for i in range(len(self.PCAGainComboBoxs)):
                self.SRB1ComboBoxs[i].setItemText(0, 'Off')
                self.SRB1ComboBoxs[i].setEnabled(False)
                self.SRB2comboBoxs[i].setItemText(0, 'Off')
                self.SRB2comboBoxs[i].setEnabled(False)
        self.parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_send_path = os.path.join(self.parent_path, 'settings', 'send_settings.xml')
        try:
            self.send_settings_path = writable_settings_path(default_send_path)
        except SettingsError as ex:
            # Keep the dialog usable even when no writable settings location
            # exists; the send operation itself can still succeed.
            self.logger.write('WARNNING: no writable settings directory: %s' % ex)
            self.send_settings_path = default_send_path
        read_send_path = (
            self.send_settings_path
            if os.path.exists(self.send_settings_path)
            else default_send_path
        )
        self.system_xml = ET.parse(self.parent_path + '\\settings\\hardware_settings' + str(self._chan) + '.xml').getroot()
        selected_file = [
            read_send_path,
            'xml files(*.xml)']
        self.loadSendXML([
            self.parent_path + '/settings/hardware_settings' + str(self._chan) + '.xml',
            'xml files(*.xml)'])
        if self.hardwareInfo.isSend == True:
            self.loadSendXML(selected_file)
            self.saveSettings([self.send_settings_path, 'xml files(*.xml)'], True)
        else:
            self.hardwareInfo.SamplingRate = 250
        if self.connect_info.iswifi:
            self.hardwareInfo.sendMode = 'FreeBCI'
            self.label_9.setVisible(0)
            self.sendcomboBox.setVisible(0)
            self.sendcomboBox.setEnabled(0)
            self.baudComboBox.setVisible(0)
            self.label_8.setVisible(0)
            self.comboBox.setVisible(0)
            self.label_7.setVisible(0)
        elif self.connect_info.isbluetooth:
            self.hardwareInfo.sendMode = 'FreeBCI'
            self.label_9.setVisible(0)
            self.sendcomboBox.setEnabled(0)
            self.sendcomboBox.setVisible(0)
            self.label_7.setVisible(0)
            self.comboBox.setVisible(0)
            self.baudComboBox.setVisible(0)
            self.label_8.setVisible(0)
        else:
            self.hardwareInfo.sendMode = 'FreeBCI'
            self.label_9.setVisible(0)
            self.sendcomboBox.setVisible(0)
            self.sendcomboBox.setEnabled(1)
            self.label_7.setVisible(0)
            self.comboBox.setVisible(0)
            self.baudComboBox.setVisible(0)
            self.label_8.setVisible(0)
        self.SamplingRateDict = {
            250: 0,
            500: 1,
            1000: 2,
            2000: 3,
            4000: 4,
            8000: 5,
            16000: 6 }
        self.BuadRateDict = {
            115200: 0,
            500000: 1,
            921600: 2,
            1000000: 3,
            2000000: 4,
            3000000: 5,
            5000000: 6,
            6000000: 7,
            6040000: 8 }
        self.sendModeDict = {
            'FreeBCI': 1,
            'OpenBCI': 0 }
        self.comboBox.setVisible(0)
        self.rateComboBox.setCurrentIndex(self.SamplingRateDict[self.hardwareInfo.SamplingRate])
        self.sendcomboBox.setCurrentIndex(self.sendModeDict[self.hardwareInfo.sendMode])
        self.barTimer = QtCore.QBasicTimer()
        self.step = 0
        self.sendMode = self.sendcomboBox.currentText()

    def refreshHardwareSetting(self):
        for i in range(len(self.isActiveSetting)):
            if self.isActiveSetting[i] == True:
                self.change_line_color(i)
                self.isActiveSetting[i] = False

    def compareLine(self, channel):
        if self.PCAGainComboBoxs[channel].currentText() != self.string_pre(self.system_xml[channel][0]):
            return False
        if self.InputComboBoxs[channel].currentText() != self.string_pre(self.system_xml[channel][1]):
            return False
        if self.BiasComboBoxs[channel].currentText() != self.string_pre(self.system_xml[channel][2]):
            return False
        if self.SRB1ComboBoxs[channel].currentText() != self.string_pre(self.system_xml[channel][4]):
            return False
        if self.SRB2comboBoxs[channel].currentText() != self.string_pre(self.system_xml[channel][3]):
            return False
        return True

    def PCAGainComboBoxs_click(self, channel):
        if self.compareLine(channel):
            if self.isActiveSetting[channel] == True:
                self.change_line_color(channel)
        elif self.isActiveSetting[channel] == False:
            self.change_line_color(channel)

    def InputComboBoxs_click(self, channel):
        if self.compareLine(channel):
            if self.isActiveSetting[channel] == True:
                self.change_line_color(channel)
        elif self.isActiveSetting[channel] == False:
            self.change_line_color(channel)

    def BiasComboBoxs_click(self, channel):
        if self.compareLine(channel):
            if self.isActiveSetting[channel] == True:
                self.change_line_color(channel)
        elif self.isActiveSetting[channel] == False:
            self.change_line_color(channel)
        if self.BiasComboBoxs[channel].currentText() == 'Yes':
            self.BiasComboBoxs[channel].setStyleSheet('font: 12pt "Segoe UI"; background: rgb(240, 255, 240);')
        else:
            self.BiasComboBoxs[channel].setStyleSheet('font: 12pt "Segoe UI"; background: rgb(255, 240, 245);')

    def SRB1ComboBoxs_click(self, channel):
        if self.compareLine(channel):
            if self.isActiveSetting[channel] == True:
                self.change_line_color(channel)
        elif self.isActiveSetting[channel] == False:
            self.change_line_color(channel)
        if self.SRB1ComboBoxs[channel].currentText() == 'On':
            self.SRB1ComboBoxs[channel].setStyleSheet('font: 12pt "Segoe UI"; background: rgb(240, 255, 240);')
        else:
            self.SRB1ComboBoxs[channel].setStyleSheet('font: 12pt "Segoe UI"; background: rgb(255, 240, 245);')

    def SRB2ComboBoxs_click(self, channel):
        if self.compareLine(channel):
            if self.isActiveSetting[channel] == True:
                self.change_line_color(channel)
        elif self.isActiveSetting[channel] == False:
            self.change_line_color(channel)
        if self.SRB2comboBoxs[channel].currentText() == 'On':
            self.SRB2comboBoxs[channel].setStyleSheet('font: 12pt "Segoe UI"; background: rgb(240, 255, 240);')
        else:
            self.SRB2comboBoxs[channel].setStyleSheet('font: 12pt "Segoe UI"; background: rgb(255, 240, 245);')

    def change_line_color(self, channel):
        if self.isActiveSetting[channel] == False:
            self.nameButtons[channel].setStyleSheet('QPushButton {\n    width: 40px;\n    height: 40px;\n    border-radius: 20px;\n    font-size: 20px;\n    color: white;\n    background: ' + self.colors[channel % 8] + ' ; /* 默认颜色 */\n}\n')
            self.isActiveSetting[channel] = True
        else:
            self.nameButtons[channel].setStyleSheet('QPushButton {\n    width: 40px;\n    height: 40px;\n    border-radius: 20px;\n    font-size: 20px;\n    color: white;\n    background: gray ; /* 默认颜色 */\n}\n')
            self.isActiveSetting[channel] = False

    def _build_send_commands(self):
        commands = []
        currentRateStr = str(self.hardwareInfo.SamplingRate) + ' Hz'
        if self.rateComboBox.currentText() != currentRateStr:
            commands.append(
                '~'
                + str(
                    HardwareSettingsProtocol.SamplingRateCommand[
                        self.rateComboBox.currentText()
                    ]
                )
            )
        for i in range(len(self.PCAGainComboBoxs)):
            command = 'x'
            if self._chan > 16:
                if i < 9:
                    command += '0' + str(i + 1)
                else:
                    command += str(i + 1)
            else:
                command += str(HardwareSettingsProtocol.Channel[i + 1])
            command += '0'
            command += str(
                HardwareSettingsProtocol.PCAGainProtocol[
                    self.PCAGainComboBoxs[i].currentText()
                ]
            )
            command += str(
                HardwareSettingsProtocol.InputTypeProtocol[
                    self.InputComboBoxs[i].currentText()
                ]
            )
            command += str(
                HardwareSettingsProtocol.BiasIncludeProtocol[
                    self.BiasComboBoxs[i].currentText()
                ]
            )
            command += str(
                HardwareSettingsProtocol.SRB2Protocol[
                    self.SRB2comboBoxs[i].currentText()
                ]
            )
            command += str(
                HardwareSettingsProtocol.SRB1Protocol[
                    self.SRB1ComboBoxs[i].currentText()
                ]
            )
            command += 'X'
            channelP = [
                40, 41, 42, 43, 44, 45, 46, 47, 32, 33, 34, 35, 36, 37, 38, 39,
                56, 57, 58, 59, 60, 61, 62, 63,
            ]
            if self._chan == 64 and i in channelP:
                if command[6:9] == '100':
                    command = command[0:7] + '1' + command[8:]
            commands.append(command)
        return commands

    def sendButton_click(self):
        if getattr(self, '_send_worker', None) is not None and self._send_worker.isRunning():
            return
        self.progressBar.setFormat('%p%')
        self.progressBar.setValue(0)
        self.sendButton.setEnabled(False)
        self.board = self.connect_info.board
        try:
            commands = self._build_send_commands()
        except Exception as ex:
            self._on_send_failed(str(ex))
            return
        self.logger.write(
            'Send hardware settings: %d command(s)' % len(commands)
        )
        self._send_worker = SettingsCommandWorker(self.board, commands, self)
        self._send_worker.progress.connect(self._on_send_progress)
        self._send_worker.failed.connect(self._on_send_failed)
        self._send_worker.succeeded.connect(self._on_send_succeeded)
        self._send_worker.finished.connect(self._on_send_thread_finished)
        self._send_worker.start()

    def _on_send_progress(self, completed, total):
        self.progressBar.setValue(10 + int(80.0 * completed / max(1, total)))

    def _on_send_failed(self, message):
        self.logger.write('WARNNING: hardware settings failed: %s' % message)
        self.progressBar.setFormat('Failed: %s' % message)
        self.progressBar.setToolTip(message)
        self.sendButton.setEnabled(True)
        self.sendButton.repaint()

    def _on_send_succeeded(self):
        self.hardwareInfo.baudRate = self.connect_info.baudRate
        self.logger.write(self.sendMode)
        self.hardwareInfo.SamplingRate = int(
            HardwareSettingsProtocol.SamplingRate[self.rateComboBox.currentText()]
        )
        if self._chan == 16 and self.sendMode != 'FreeBCI':
            self.hardwareInfo.SamplingRate = int(self.hardwareInfo.SamplingRate / 2)
        self.logger.write(self.hardwareInfo.SamplingRate)
        self.hardwareInfo.isSend = True
        if self.connect_info.board_id == 30:
            self.hardwareInfo.sendMode = self.sendcomboBox.currentText()
        self.progressBar.setValue(100)
        self.sendButton.setEnabled(True)
        self.sendButton.repaint()
        self.connect_info.board = self.board
        self._signal.emit(self.hardwareInfo)
        self._signal_con.emit(self.connect_info)
        selected_file = [
            self.send_settings_path,
            'xml files(*.xml)']
        try:
            self.saveSettings(selected_file, True)
        except Exception as ex:
            # A read-only settings directory must not turn a successful board
            # configuration into a GUI exception.
            self.logger.write('WARNNING: could not save settings: %s' % ex)

    def _on_send_thread_finished(self):
        worker = getattr(self, '_send_worker', None)
        if worker is not None and not worker.isRunning():
            self._send_worker = None

    def closeEvent(self, event):
        worker = getattr(self, '_send_worker', None)
        if worker is not None and worker.isRunning():
            worker.cancel()
            worker.wait(3000)
        super(HardwareSettingsDialog, self).closeEvent(event)

    def string_pre(self, s):
        elem = str(s.text).replace(' ', '')
        elem = elem.replace('\n', '')
        return elem

    def loadSendXML(self, load_xml_path):
        if load_xml_path[0] != '':
            self.logger.write(load_xml_path[0])
            settings = load_settings(load_xml_path[0], expected_channels=len(self.ischanClick))
            for row, channel in enumerate(settings.channels):
                if not self.ischanClick[row]:
                    continue
                values = (
                    channel.pca_gain,
                    channel.input_type,
                    channel.bias_include,
                    channel.srb2,
                    channel.srb1,
                )
                combos = (
                    self.PCAGainComboBoxs[row],
                    self.InputComboBoxs[row],
                    self.BiasComboBoxs[row],
                    self.SRB2comboBoxs[row],
                    self.SRB1ComboBoxs[row],
                )
                for combo, value in zip(combos, values):
                    combobox_index = combo.findText(value, QtCore.Qt.MatchFixedString)
                    if combobox_index >= 0:
                        combo.setCurrentIndex(combobox_index)
                for combo, on_value in (
                    (self.BiasComboBoxs[row], 'Yes'),
                    (self.SRB2comboBoxs[row], 'On'),
                    (self.SRB1ComboBoxs[row], 'On'),
                ):
                    if combo.currentText() == on_value:
                        combo.setStyleSheet('font: 12pt "Segoe UI"; background: rgb(240, 255, 240);')
                    else:
                        combo.setStyleSheet('font: 12pt "Segoe UI"; background: rgb(255, 240, 245);')
                if self.compareLine(row):
                    if self.isActiveSetting[row] == True:
                        self.change_line_color(row)
                elif self.isActiveSetting[row] == False:
                    self.change_line_color(row)

    def loadButton_click(self):
        qFileDialog = QtWidgets.QFileDialog()
        default_dir = os.path.join(self.parent_path, 'settings')
        load_xml_path = qFileDialog.getOpenFileName(self, 'Open file', default_dir, 'xml files(*.xml)')
        if load_xml_path[0] != '':
            self.logger.write('Load xml: ' + load_xml_path[0])
            self.loadSendXML(load_xml_path)

    def saveSettings(self, selected_file, isRefresh):
        if selected_file[0] != '':
            channels = tuple(
                ChannelSettings(
                    pca_gain=self.PCAGainComboBoxs[row].currentText(),
                    input_type=self.InputComboBoxs[row].currentText(),
                    bias_include=self.BiasComboBoxs[row].currentText(),
                    srb2=self.SRB2comboBoxs[row].currentText(),
                    srb1=self.SRB1ComboBoxs[row].currentText(),
                )
                for row in range(len(self.PCAGainComboBoxs))
            )
            try:
                sampling_rate = int(str(self.rateComboBox.currentText()).split()[0])
            except (ValueError, IndexError):
                sampling_rate = self.hardwareInfo.SamplingRate
            try:
                baud_rate = int(str(self.connect_info.baudRate))
            except (TypeError, ValueError):
                baud_rate = None
            save_settings(
                selected_file[0],
                HardwareSettings(
                    channels=channels,
                    sampling_rate=sampling_rate,
                    baud_rate=baud_rate,
                ),
            )
            self.system_xml = ET.parse(selected_file[0]).getroot()
            if isRefresh == True:
                self.refreshHardwareSetting()

    def saveButton_click(self):
        dialog_save = QtWidgets.QFileDialog()
        default_dir = os.path.join(self.parent_path, 'settings')
        selected_file = dialog_save.getSaveFileName(self, 'Open file', default_dir, 'xml files(*.xml)')
        if selected_file[0] != '':
            self.logger.write('Save xml: ' + selected_file[0])
        self.saveSettings(selected_file, False)

