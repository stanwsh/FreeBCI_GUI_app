from pickle import FALSE
from freebci.qt import QtCore, QtGui, QtWidgets
from freebci.qt import Qt
from pyqtgraph import PlotWidget, TextItem
import pyqtgraph as pg

pg.setConfigOptions(background='#0B1220', foreground='#9FB3C8', antialias=True)


class CustomViewBox(pg.ViewBox):
    
    def __init__(self, parent=None, border=None, lockAspect=False, enableMouse=False, invertY=False, enableMenu=False, name=None, invertX=False, defaultPadding=0.02):
        super().__init__(parent, border, lockAspect, enableMouse, invertY, enableMenu, name, invertX, defaultPadding)

    
    def wheelEvent(self, ev, axis=None):
        ev.ignore()



class plot_widget(QtWidgets.QWidget):
    
    def __init__(self, channel, parent=None):
        super(plot_widget, self).__init__(parent)
        self.setStyleSheet('background-color:#0B1220')
        self.colors = [
            'red',
            'green',
            'blue',
            '#E3CF57',
            'rgb(0,255,255)',
            'purple',
            'black',
            'rgb(210,180,140)']
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setSpacing(1)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.backLabel = QtWidgets.QLabel(self)
        self.backLabel.setObjectName('backLabel_' + str(channel + 1))
        self.mainLayout.addWidget(self.backLabel, 1, 0, 1, 2)
        self.channelButton = QtWidgets.QPushButton(self)
        self.channelButton.setMinimumSize(QtCore.QSize(30, 30))
        self.channelButton.setMaximumSize(QtCore.QSize(30, 30))
        self.channelButton.setStyleSheet('QPushButton {\n    width: 30px;\n    height: 30px;\n    border-radius: 15px;\n    font-size: 15px;\n    color: white;\n    background: ' + self.colors[channel % 8 - 1] + ' ; /* 默认颜色 */\n}\n')
        self.channelButton.setObjectName('channelButton' + str(channel + 1))
        self.channelButton.setText(str(channel))
        self.mainLayout.addWidget(self.channelButton, 1, 0, 1, 1)
        self.resistancePushButton = QtWidgets.QPushButton(self)
        self.resistancePushButton.setStyleSheet('QPushButton {\n    width: 30px;\n    height: 30px;\n    border-radius: 15px;\n    font-size: 15px;\n    color: black;\n    font: 12pt "Segoe UI";\n    /*background: red ;*/ /* 默认颜色 */\n}')
        self.resistancePushButton.setObjectName('resistancePushButton' + str(channel + 1))
        self.resistancePushButton.setText('Ω')
        self.mainLayout.addWidget(self.resistancePushButton, 1, 1, 1, 1)
        self.ts_plot = PlotWidget(self, viewBox=CustomViewBox())
        self.ts_plot.hideButtons()
        self.ts_plot.setMinimumSize(QtCore.QSize(0, 120))
        self.ts_plot.getAxis('left').setStyle(showValues=False)
        self.ts_plot.getAxis('bottom').setStyle(showValues=False)
        self.ts_plot.setObjectName('ts_plot' + str(channel + 1))
        self.mainLayout.addWidget(self.ts_plot, 0, 2, 3, 1)
        self.mainLayout.installEventFilter(self)
        self.mainLayout.setColumnStretch(0, 1)
        self.mainLayout.setColumnStretch(1, 1)
        self.mainLayout.setColumnStretch(2, 20)
        self.dataLabel = QtWidgets.QLabel(self)
        self.dataLabel.setText('Not Railed 0.00% 0.00uVrms')
        self.dataLabel.setStyleSheet('font: 8pt "Segoe UI";background:transparent; color:white')
        self.dataLabel.setMinimumSize(QtCore.QSize(240, 20))
        self.dataLabel.setMaximumSize(QtCore.QSize(240, 20))
        self.maxLabel = QtWidgets.QLabel(self)
        self.maxLabel.setText('+200uV')
        self.maxLabel.setStyleSheet('font: 8pt "Segoe UI";background:transparent ; color:white')
        self.maxLabel.setMinimumSize(QtCore.QSize(100, 20))
        self.maxLabel.setMaximumSize(QtCore.QSize(100, 20))
        self.minLabel = QtWidgets.QLabel(self)
        self.minLabel.setText('-200uV')
        self.minLabel.setStyleSheet('font: 8pt "Segoe UI";background:transparent ; color:white')
        self.minLabel.setMinimumSize(QtCore.QSize(100, 20))
        self.minLabel.setMaximumSize(QtCore.QSize(100, 20))
        self.dataLabelColor = 'white'
        self.ischannelClick = False
        self.isResistance = True
        self.setLayout(self.mainLayout)


