from freebci.qt import QtCore, QtGui, QtWidgets
from freebci.qt import Signal

class BatteryWidget(QtWidgets.QWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wg_container = QtWidgets.QWidget(self)
        self.wg_container.setGeometry(QtCore.QRect(12, 5, 179, 59))
        self.wg_container.setStyleSheet('#wg_container\n{\n    background:rgba(0, 0, 0, 0);\n}')
        self.wg_container.setObjectName('wg_container')
        self.body_head = QtWidgets.QLabel(self.wg_container)
        self.body_head.setGeometry(QtCore.QRect(145, 10, 10, 25))
        self.body_head.setStyleSheet('#body_head\n{\n    background:rgba(0, 0, 0, 0);\n    background:#2e3349;\n    border-radius: 2px;\n}')
        self.body_head.setText('')
        self.body_head.setObjectName('body_head')
        self.body = QtWidgets.QLabel(self.wg_container)
        self.body.setGeometry(QtCore.QRect(0, 0, 146, 45))
        self.body.setStyleSheet('#body\n{\n    border:3px ridge #2e3349;\n    border-radius: 5px;\n}')
        self.body.setText('')
        self.body.setObjectName('body')
        self.lvl_1 = QtWidgets.QLabel(self.wg_container)
        self.lvl_1.setGeometry(QtCore.QRect(5, 5, 25, 35))
        self.lvl_1.setStyleSheet('#lvl_1\n{\n    background:#7CFC00;\n}')
        self.lvl_1.setText('')
        self.lvl_1.setObjectName('lvl_1')
        self.lvl_2 = QtWidgets.QLabel(self.wg_container)
        self.lvl_2.setGeometry(QtCore.QRect(32, 5, 25, 35))
        self.lvl_2.setStyleSheet('#lvl_2\n{\n    background:#7CFC00;\n}')
        self.lvl_2.setText('')
        self.lvl_2.setObjectName('lvl_2')
        self.lvl_3 = QtWidgets.QLabel(self.wg_container)
        self.lvl_3.setGeometry(QtCore.QRect(60, 5, 25, 35))
        self.lvl_3.setStyleSheet('#lvl_3\n{\n    background:#7CFC00;\n}')
        self.lvl_3.setText('')
        self.lvl_3.setObjectName('lvl_3')
        self.lvl_4 = QtWidgets.QLabel(self.wg_container)
        self.lvl_4.setGeometry(QtCore.QRect(88, 5, 25, 35))
        self.lvl_4.setStyleSheet('#lvl_4\n{\n    background:#7CFC00;\n}')
        self.lvl_4.setText('')
        self.lvl_4.setObjectName('lvl_4')
        self.lvl_5 = QtWidgets.QLabel(self.wg_container)
        self.lvl_5.setGeometry(QtCore.QRect(116, 5, 25, 35))
        self.lvl_5.setStyleSheet('#lvl_5\n{\n    background:#7CFC00;\n}')
        self.lvl_5.setText('')
        self.lvl_5.setObjectName('lvl_5')
        self.setValue(50)

    @QtCore.Slot(int)
    def setValue(self, value):
        self.value = value
        if self.value > 100:
            self.value = 100
        elif self.value < 0:
            self.value = 0
        if self.value < 5:
            self.body_head.setStyleSheet('#body_head\n{\n    background:#ff0000;\n    border-radius: 2px;\n}')
            self.body.setStyleSheet('#body\n{\n    border:3px ridge #ff0000;\n    border-radius: 5px;\n}')
            self.lvl_1.setStyleSheet('#lvl_1\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_2.setStyleSheet('#lvl_2\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_3.setStyleSheet('#lvl_3\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_4.setStyleSheet('#lvl_4\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_5.setStyleSheet('#lvl_5\n{\n    background:rgba(0, 0, 0, 0);\n}')
        elif self.value >= 5 and self.value < 20:
            self.body_head.setStyleSheet('#body_head\n{\n    background:rgba(0, 0, 0, 0);\n    background:#2e3349;\n    border-radius: 2px;\n}')
            self.body.setStyleSheet('#body\n{\n    background:rgba(0, 0, 0, 0);\n    border:3px ridge #2e3349;\n    border-radius: 5px;\n}')
            self.lvl_1.setStyleSheet('#lvl_1\n{\n    background:#ff0000;\n}')
            self.lvl_2.setStyleSheet('#lvl_2\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_3.setStyleSheet('#lvl_3\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_4.setStyleSheet('#lvl_4\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_5.setStyleSheet('#lvl_5\n{\n    background:rgba(0, 0, 0, 0);\n}')
        elif self.value >= 20 and self.value < 40:
            self.body_head.setStyleSheet('#body_head\n{\n    background:rgba(0, 0, 0, 0);\n    background:#2e3349;\n    border-radius: 2px;\n}')
            self.body.setStyleSheet('#body\n{\n    background:rgba(0, 0, 0, 0);\n    border:3px ridge #2e3349;\n    border-radius: 5px;\n}')
            self.lvl_1.setStyleSheet('#lvl_1\n{\n    background:#F28500;\n}')
            self.lvl_2.setStyleSheet('#lvl_2\n{\n    background:#F28500;\n}')
            self.lvl_3.setStyleSheet('#lvl_3\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_4.setStyleSheet('#lvl_4\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_5.setStyleSheet('#lvl_5\n{\n    background:rgba(0, 0, 0, 0);\n}')
        elif self.value >= 40 and self.value < 60:
            self.body_head.setStyleSheet('#body_head\n{\n    background:rgba(0, 0, 0, 0);\n    background:#2e3349;\n    border-radius: 2px;\n}')
            self.body.setStyleSheet('#body\n{\n    background:rgba(0, 0, 0, 0);\n    border:3px ridge #2e3349;\n    border-radius: 5px;\n}')
            self.lvl_1.setStyleSheet('#lvl_1\n{\n    background:#ffd700;\n}')
            self.lvl_2.setStyleSheet('#lvl_2\n{\n    background:#ffd700;\n}')
            self.lvl_3.setStyleSheet('#lvl_3\n{\n    background:#ffd700;\n}')
            self.lvl_4.setStyleSheet('#lvl_4\n{\n    background:rgba(0, 0, 0, 0);\n}')
            self.lvl_5.setStyleSheet('#lvl_5\n{\n    background:rgba(0, 0, 0, 0);\n}')
        elif self.value >= 60 and self.value < 80:
            self.body_head.setStyleSheet('#body_head\n{\n    background:rgba(0, 0, 0, 0);\n    background:#2e3349;\n    border-radius: 2px;\n}')
            self.body.setStyleSheet('#body\n{\n    background:rgba(0, 0, 0, 0);\n    border:3px ridge #2e3349;\n    border-radius: 5px;\n}')
            self.lvl_1.setStyleSheet('#lvl_1\n{\n    background:#32cd32;\n}')
            self.lvl_2.setStyleSheet('#lvl_2\n{\n    background:#32cd32;\n}')
            self.lvl_3.setStyleSheet('#lvl_3\n{\n    background:#32cd32;\n}')
            self.lvl_4.setStyleSheet('#lvl_4\n{\n    background:#32cd32;\n}')
            self.lvl_5.setStyleSheet('#lvl_5\n{\n    background:rgba(0, 0, 0, 0);\n}')
        elif self.value >= 80:
            self.body_head.setStyleSheet('#body_head\n{\n    background:rgba(0, 0, 0, 0);\n    background:#2e3349;\n    border-radius: 2px;\n}')
            self.body.setStyleSheet('#body\n{\n    background:rgba(0, 0, 0, 0);\n    border:3px ridge #2e3349;\n    border-radius: 5px;\n}')
            self.lvl_1.setStyleSheet('#lvl_1\n{\n    background:#7CFC00;\n}')
            self.lvl_2.setStyleSheet('#lvl_2\n{\n    background:#7CFC00;\n}')
            self.lvl_3.setStyleSheet('#lvl_3\n{\n    background:#7CFC00;\n}')
            self.lvl_4.setStyleSheet('#lvl_4\n{\n    background:#7CFC00;\n}')
            self.lvl_5.setStyleSheet('#lvl_5\n{\n    background:#7CFC00;\n}')
        self.wg_container.update()


