"""Session diagnostics dialog.

The dialog is deliberately passive: it asks the main window for a plain
snapshot and renders it.  It never touches the board or the recording writer, so
leaving it open cannot interfere with acquisition.
"""
from __future__ import annotations

from typing import Callable, Dict

from PyQt5 import QtCore, QtWidgets


class DiagnosticsDialog(QtWidgets.QDialog):
    def __init__(self, provider: Callable[[], Dict[str, str]], parent=None) -> None:
        super().__init__(parent)
        self.provider = provider
        self.setWindowTitle("Session diagnostics")
        self.resize(760, 560)
        self.setMinimumSize(720, 520)
        self.setModal(False)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(8)
        title = QtWidgets.QLabel("Session diagnostics")
        title.setStyleSheet("font: 700 15pt 'Segoe UI'; color: #14263A;")
        layout.addWidget(title)
        subtitle = QtWidgets.QLabel(
            "Live view of acquisition, recording, and output health. "
            "The dialog refreshes every half second."
        )
        subtitle.setStyleSheet("color: #52657A;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        rows = [
            ("state", "State"),
            ("session", "Session"),
            ("device", "Device"),
            ("elapsed", "Elapsed"),
            ("configured", "Configured rate"),
            ("rate", "Effective rate"),
            ("samples", "Samples received"),
            ("blocks", "Blocks"),
            ("lost", "Lost samples"),
            ("dropped", "Display drops"),
            ("since", "Since last block"),
            ("markers", "Markers"),
            ("files", "Recorded files"),
            ("written", "Samples written"),
            ("queue", "Writer queue"),
            ("write", "Last write"),
            ("manifest", "Manifest status"),
            ("disk", "Disk free"),
            ("recording", "Recording"),
            ("output", "Output folder"),
            ("control", "Control endpoint"),
            ("lsl", "LSL streams"),
            ("error", "Last error"),
        ]
        columns = QtWidgets.QHBoxLayout()
        columns.setSpacing(24)
        self.fields: Dict[str, QtWidgets.QLabel] = {}
        split = 12
        for subset in (rows[:split], rows[split:]):
            form = QtWidgets.QFormLayout()
            form.setLabelAlignment(QtCore.Qt.AlignRight)
            form.setFormAlignment(QtCore.Qt.AlignTop)
            form.setVerticalSpacing(3)
            form.setHorizontalSpacing(8)
            for key, label in subset:
                value = QtWidgets.QLabel("-")
                value.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                value.setWordWrap(True)
                if key in ("output", "control", "lsl", "error"):
                    # Long paths must not force the whole dialog off screen.
                    value.setMinimumWidth(0)
                    value.setSizePolicy(
                        QtWidgets.QSizePolicy.Ignored,
                        QtWidgets.QSizePolicy.Preferred,
                    )
                self.fields[key] = value
                form.addRow(label + ":", value)
            columns.addLayout(form, 1)
        layout.addLayout(columns, 1)

        note = QtWidgets.QLabel(
            "Lost samples come from gaps in the board sample sequence. "
            "Display drops only affect what is drawn, not the recording."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #5F7184; font-size: 9pt;")
        layout.addWidget(note)

        buttons = QtWidgets.QHBoxLayout()
        self.copyButton = QtWidgets.QPushButton("Copy summary")
        self.copyButton.clicked.connect(self.copy_summary)
        self.refreshButton = QtWidgets.QPushButton("Refresh")
        self.refreshButton.clicked.connect(self.refresh)
        closeButton = QtWidgets.QPushButton("Close")
        closeButton.clicked.connect(self.close)
        buttons.addWidget(self.copyButton)
        buttons.addWidget(self.refreshButton)
        buttons.addStretch(1)
        buttons.addWidget(closeButton)
        layout.addLayout(buttons)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        try:
            data = self.provider()
        except Exception as exc:  # noqa: BLE001 - diagnostics must never crash the GUI
            data = {"error": "Could not read session state: %s" % exc}
        self._apply(data)

    def _apply(self, data: Dict[str, str]) -> None:
        state = str(data.get("state", "idle"))
        self.fields["state"].setText(state)
        color = "#1b7f3a" if state == "recording" else "#8a5a00" if state in ("armed", "connected") else "#8b1a1a" if state == "failed" else "#333"
        self.fields["state"].setStyleSheet("font-weight: 700; color: %s;" % color)

        self.fields["session"].setText(str(data.get("session", "-")))
        self.fields["device"].setText(str(data.get("device", "-")))
        self.fields["elapsed"].setText(str(data.get("elapsed", "-")))
        self.fields["configured"].setText(str(data.get("configured", "-")))
        self.fields["rate"].setText(str(data.get("rate", "-")))
        self.fields["samples"].setText(str(data.get("samples", "-")))
        self.fields["blocks"].setText(str(data.get("blocks", "-")))
        self.fields["lost"].setText(str(data.get("lost", "-")))
        self.fields["dropped"].setText(str(data.get("dropped", "-")))
        self.fields["since"].setText(str(data.get("since", "-")))
        self.fields["markers"].setText(str(data.get("markers", "-")))
        self.fields["files"].setText(str(data.get("files", "-")))
        self.fields["written"].setText(str(data.get("written", "-")))
        self.fields["queue"].setText(str(data.get("queue", "-")))
        self.fields["write"].setText(str(data.get("write", "-")))
        self.fields["manifest"].setText(str(data.get("manifest", "-")))
        self.fields["disk"].setText(str(data.get("disk", "-")))
        self.fields["recording"].setText(str(data.get("recording", "-")))
        self.fields["output"].setText(str(data.get("output", "-")))
        self.fields["control"].setText(str(data.get("control", "-")))
        self.fields["lsl"].setText(str(data.get("lsl", "-")))
        error = str(data.get("error") or "-")
        self.fields["error"].setText(error)
        self.fields["error"].setStyleSheet("color: #8b1a1a;" if error != "-" else "")

    def summary_text(self) -> str:
        lines = ["FreeBCI session diagnostics"]
        for key, label in (
            ("state", "State"),
            ("session", "Session"),
            ("device", "Device"),
            ("elapsed", "Elapsed"),
            ("configured", "Configured rate"),
            ("rate", "Effective rate"),
            ("samples", "Samples received"),
            ("blocks", "Blocks"),
            ("lost", "Lost samples"),
            ("dropped", "Display drops"),
            ("since", "Since last block"),
            ("markers", "Markers"),
            ("files", "Recorded files"),
            ("written", "Samples written"),
            ("queue", "Writer queue"),
            ("write", "Last write"),
            ("manifest", "Manifest status"),
            ("disk", "Disk free"),
            ("recording", "Recording"),
            ("output", "Output folder"),
            ("control", "Control endpoint"),
            ("lsl", "LSL streams"),
            ("error", "Last error"),
        ):
            lines.append("%s: %s" % (label, self.fields[key].text()))
        return "\n".join(lines)

    def copy_summary(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self.summary_text())

    def closeEvent(self, event) -> None:
        self.timer.stop()
        super().closeEvent(event)
