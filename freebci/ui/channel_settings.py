import os
import time
import xml.dom.minidom as minidom
from freebci.qt import QtGui, QtCore, QtWidgets
from freebci.ui.connection_info import HardwareInfo, ConnectionInfo
from freebci.ui.electrodes_position import ElectrodesPosition
from freebci.design.channels_electrodes_settings_interface import channels_electrodes_Settings_interface
from freebci.ui.hardware_warning import HardwareWarningDialog
from functools import partial
import xml.etree.ElementTree as ET
from freebci.qt import QPixmap
from freebci.qt import Qt
import mne
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class ChannelSettingsDialog(channels_electrodes_Settings_interface):
    _signal = QtCore.Signal(HardwareInfo)
    _signal_con = QtCore.Signal(ConnectionInfo)

    def __init__(self, connect_info, hardwareInfo):
        super(ChannelSettingsDialog, self).__init__(hardwareInfo)
        self.connect_info = connect_info
        self.hardwareInfo = hardwareInfo
        self.saveButton.clicked.connect(self.saveButton_click)
        self.loadButton.clicked.connect(self.loadButton_click)
        self.applyButton.clicked.connect(self.applyButton_click)
        self.isActiveSetting = [ False for i in range(self.hardwareInfo.channel_num) ]
        for i in range(len(self.electrodeNameComboBoxs)):
            if self.ischanClick[i]:
                self.electrodeNameComboBoxs[i].activated.connect(partial(self.electrodeNameComboBoxs_click, i))

        self.parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_map = os.path.join(self.parent_path, 'settings', 'channels_electrodes_settings%d.xml' % self._chan)
        if not os.path.isfile(default_map):
            # The distributed maps cover 32/64 channels; smaller boards use
            # the corresponding prefix rather than a missing 8/16-channel file.
            base = 32 if self._chan <= 32 else 64
            default_map = os.path.join(self.parent_path, 'settings', 'channels_electrodes_settings%d.xml' % base)
        self.system_xml = ET.parse(default_map).getroot()
        selected_file = [
            self.parent_path + '/settings/chanels_electrodes_apply_settings.xml',
            'xml files(*.xml)']
        self.loadApplyXML([default_map, 'xml files(*.xml)'])
        if self.hardwareInfo.isApply == True:
            self.loadApplyXML(selected_file)
            self.saveSettings(selected_file, True)

        Electrodes_Position = ElectrodesPosition()
        electrodes_name = f'ElectrodesName_{str(self.connect_info.channel_num)}'
        electrodes_pos = f'ElectrodesPos_{str(self.connect_info.channel_num)}'
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
        self.list_dic = dict(zip(self.channels, self.value))
        self.montage = mne.channels.make_dig_montage(ch_pos=self.list_dic, nasion=[
            5.27205792e-18,
            0.0860992398,
            -0.0401487349], lpa=[
            -0.08609924,
            -0.0,
            -0.04014873], rpa=[
            0.08609924,
            0.0,
            -0.04014873])
        image = os.path.join(self.parent_path, 'electrodes_pos_%d.png' % self._chan)
        if not os.path.isfile(image):
            image = os.path.join(self.parent_path, 'electrodes_pos_%d.png' % (32 if self._chan <= 32 else 64))
        self.label.setPixmap(QPixmap(image))
        self.label.setScaledContents(True)
        self.electrodeNameIndex = [ None for i in range(self.hardwareInfo.channel_num) ]
        self.barTimer = QtCore.QBasicTimer()
        self.step = 0

    def check_mutual_exclusion_electrodes(self):
        for i in range(len(self.electrodeNameComboBoxs)):
            self.electrodeNameIndex[i] = self.electrodeNameComboBoxs[i].currentIndex()

        indexlist = set(self.electrodeNameIndex)
        if len(indexlist) == len(self.electrodeNameIndex):
            return True
        else:
            return False

    def refreshHardwareSetting(self):
        for i in range(len(self.isActiveSetting)):
            if self.isActiveSetting[i] == True:
                self.change_line_color(i)
                self.isActiveSetting[i] = False

    def compareLine(self, channel):
        if self.electrodeNameComboBoxs[channel].currentText() != self.string_pre(self.system_xml[channel][0]):
            return False
        return True

    def electrodeNameComboBoxs_click(self, channel, _index=None):
        if self.compareLine(channel):
            if self.isActiveSetting[channel] == True:
                self.change_line_color(channel)
        elif self.isActiveSetting[channel] == False:
            self.change_line_color(channel)

    def change_line_color(self, channel):
        if self.isActiveSetting[channel] == False:
            self.nameButtons[channel].setStyleSheet('QPushButton {\n    width: 40px;\n    height: 40px;\n    border-radius: 20px;\n    font-size: 20px;\n    color: white;\n    background: ' + self.colors[channel % 8] + ' ; /* 默认颜色 */\n}\n')
            self.isActiveSetting[channel] = True
        else:
            self.nameButtons[channel].setStyleSheet('QPushButton {\n    width: 40px;\n    height: 40px;\n    border-radius: 20px;\n    font-size: 20px;\n    color: white;\n    background: gray ; /* 默认颜色 */\n}\n')
            self.isActiveSetting[channel] = False

    def applyButton_click(self):
        self.step = 0
        self.progressBar.setValue(self.step)
        self.progressBar.repaint()
        self.applyButton.setEnabled(False)
        self.applyButton.repaint()
        if self.check_mutual_exclusion_electrodes() == False:
            self.hardware_warning_dialog = HardwareWarningDialog()
            self.hardware_warning_dialog.label_2.setText(QtCore.QCoreApplication.translate('hardware_warning', 'Multiple channels correspond to one electrode. Set the channels and electrodes to correspond one by one'))
            self.hardware_warning_dialog.show()
            self.applyButton.setEnabled(True)
        else:
            selected_file = [
                self.parent_path + '/settings/chanels_electrodes_apply_settings.xml',
                'xml files(*.xml)']
            self.step = 20
            self.progressBar.setValue(self.step)
            self.progressBar.repaint()
            tempelectrodeIndexes = [ None for n in range(len(self.electrodeNameComboBoxs)) ]
            for i in range(len(self.electrodeNameComboBoxs)):
                tempelectrodeIndexes[i] = self.electrodeNameComboBoxs[i].currentIndex()

            self.hardwareInfo.chanMatched_index = [ m[0] for m in sorted(enumerate(tempelectrodeIndexes), key=lambda x: x[1]) ]
            self.hardwareInfo.isApply = True
            time.sleep(0.2)
            self.step = 80
            self.progressBar.setValue(self.step)
            self.progressBar.repaint()
            self.applyButton.setEnabled(True)
            self.applyButton.repaint()
            self._signal.emit(self.hardwareInfo)
            self._signal_con.emit(self.connect_info)
            self.step = 100
            self.progressBar.setValue(self.step)
            self.progressBar.repaint()
            selected_file = [
                self.parent_path + '/settings/chanels_electrodes_apply_settings.xml',
                'xml files(*.xml)']
            self.saveSettings(selected_file, True)

    def string_pre(self, s):
        elem = str(s.text).replace(' ', '')
        elem = elem.replace('\n', '')
        return elem

    def loadApplyXML(self, load_xml_path):
        file_path = os.path.dirname(__file__)
        qFileDialog = QtWidgets.QFileDialog()
        if load_xml_path[0] != '':
            tree = ET.parse(load_xml_path[0])
            root = tree.getroot()
            for row in range(min(len(root), self._chan)):
                if self.ischanClick[row]:
                    combobox_index = self.electrodeNameComboBoxs[row].findText(self.string_pre(root[row][0]), QtCore.Qt.MatchFixedString)
                    if combobox_index >= 0:
                        self.electrodeNameComboBoxs[row].setCurrentIndex(combobox_index)
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
            tree = ET.parse(load_xml_path[0])
            root = tree.getroot()
            for row in range(min(len(root), self._chan)):
                if self.ischanClick[row]:
                    combobox_index = self.electrodeNameComboBoxs[row].findText(self.string_pre(root[row][0]), QtCore.Qt.MatchFixedString)
                    if combobox_index >= 0:
                        self.electrodeNameComboBoxs[row].setCurrentIndex(combobox_index)
                    if self.compareLine(row):
                        if self.isActiveSetting[row] == True:
                            self.change_line_color(row)
                    elif self.isActiveSetting[row] == False:
                        self.change_line_color(row)

    def saveSettings(self, selected_file, isRefresh):
        if selected_file[0] != '':
            xml_root = ET.Element('Channels')
            xml_root.set('version', '1.0')
            xml_root.set('encoding', 'UTF-8')
            for row in range(len(self.electrodeNameComboBoxs)):
                channel = ET.SubElement(xml_root, 'Channel' + str(row + 1))
                electrode_matched = ET.SubElement(channel, 'electrode_gain')
                electrode_matched.text = self.electrodeNameComboBoxs[row].currentText()
                electrodeindex_matched = ET.SubElement(channel, 'electrodeindex_gain')
                electrodeindex_matched.text = str(self.electrodeNameComboBoxs[row].currentIndex())

            xml_string = ET.tostring(xml_root, encoding='utf-8')
            xml_reparsed = minidom.parseString(xml_string)
            xml_to_file = xml_reparsed.toprettyxml()
            file = open(selected_file[0], 'w', encoding='utf-8')
            file.write(xml_to_file)
            file.close()
            self.system_xml = ET.parse(selected_file[0]).getroot()
            if isRefresh == True:
                self.refreshHardwareSetting()

    def saveButton_click(self):
        dialog_save = QtWidgets.QFileDialog()
        default_dir = os.path.join(self.parent_path, 'settings')
        selected_file = dialog_save.getSaveFileName(self, 'Open file', default_dir, 'xml files(*.xml)')
        if selected_file[0] != '':
            self.saveSettings(selected_file, False)
