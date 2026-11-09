"""Friendly first-run surface shown before a device or demo session starts."""
from __future__ import annotations

from typing import Callable

from freebci.qt import QtCore, QtWidgets


class EmptyState(QtWidgets.QWidget):
    def __init__(
        self,
        on_connect: Callable[[], None],
        on_demo: Callable[[], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyState")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        card = QtWidgets.QFrame(self)
        card.setObjectName("emptyCard")
        card.setMaximumWidth(560)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(34, 30, 34, 30)
        card_layout.setSpacing(12)

        eyebrow = QtWidgets.QLabel("ACQUISITION WORKSPACE", card)
        eyebrow.setObjectName("emptyEyebrow")
        card_layout.addWidget(eyebrow)

        title = QtWidgets.QLabel("Ready to record", card)
        title.setObjectName("emptyTitle")
        card_layout.addWidget(title)

        body = QtWidgets.QLabel(
            "Connect a FreeBCI device to stream and save neural data, or explore "
            "the interface with synthetic data.",
            card,
        )
        body.setObjectName("emptyBody")
        body.setWordWrap(True)
        body.setMinimumHeight(52)
        card_layout.addWidget(body)
        card_layout.addSpacing(8)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(10)
        self.connectButton = QtWidgets.QPushButton("Connect a board", card)
        self.connectButton.setObjectName("emptyPrimary")
        self.connectButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.connectButton.setStyleSheet(
            "QPushButton {color: #FFFFFF; background: #2F80ED; border: 1px solid #4A95F5; "
            "border-radius: 7px; font-weight: 600; padding: 6px 16px;}"
            "QPushButton:hover {background: #3B8CF7;}"
            "QPushButton:pressed {background: #2569C9;}"
        )
        self.connectButton.clicked.connect(on_connect)
        buttons.addWidget(self.connectButton)

        self.demoButton = QtWidgets.QPushButton("Start demo session", card)
        self.demoButton.setObjectName("emptySecondary")
        self.demoButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.demoButton.setStyleSheet(
            "QPushButton {color: #DCE8F5; background: transparent; border: 1px solid #35516E; "
            "border-radius: 7px; padding: 6px 16px;}"
            "QPushButton:hover {background: #1B3552; border-color: #4A7098;}"
        )
        self.demoButton.clicked.connect(on_demo)
        buttons.addWidget(self.demoButton)
        buttons.addStretch(1)
        card_layout.addLayout(buttons)

        hint = QtWidgets.QLabel(
            "Tip: Ctrl+Shift+D starts the demo  ·  Ctrl+D opens diagnostics",
            card,
        )
        hint.setObjectName("emptyHint")
        card_layout.addWidget(hint)

        layout.addStretch(1)
        layout.addWidget(card, 0, QtCore.Qt.AlignCenter)
        layout.addStretch(1)
