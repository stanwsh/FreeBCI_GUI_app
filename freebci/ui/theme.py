"""Shared visual theme for the FreeBCI desktop application.

The application uses Segoe UI when the host provides it and otherwise falls
back to the platform's general UI font.  Widget-local stylesheets still carry
state colours, so the theme only supplies the common surface, spacing, and
control treatment.
"""
from __future__ import annotations

from freebci.qt import QtGui, QtWidgets


def font_family() -> str:
    """Return the preferred UI family, falling back to the system font."""
    if "Segoe UI" in set(QtGui.QFontDatabase.families()):
        return "Segoe UI"
    return QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.GeneralFont).family() or "Sans Serif"


STYLESHEET = """
QMainWindow {
    background: #0B1728;
}
QWidget#centralwidget,
QStackedWidget,
QWidget#Layout00 {
    background: #0B1728;
}
QMainWindow QStackedWidget > QWidget {
    background: #0B1220;
}
QMainWindow QWidget#scrollAreaWidgetContents {
    background: #0B1220;
}
QWidget#widget {
    background: #0F2238;
    border-bottom: 1px solid #1E3A57;
}
QWidget#widget QLabel {
    color: #CBD9E8;
    font-size: 9pt;
    font-weight: 600;
}
QWidget#widget QLabel#brandLabel {
    color: #F8FBFF;
    font-size: 14pt;
    font-weight: 700;
    padding-right: 8px;
}
QMainWindow QLabel#stateLabel {
    background: #EAF2FA;
    color: #14263A;
    border: 0;
    border-top: 1px solid #C9D8E8;
    padding: 4px 12px;
    font-size: 9pt;
}
QMainWindow QPushButton {
    color: #E6EEF8;
    background: #1B3552;
    border: 1px solid #2B4B6F;
    border-radius: 6px;
    padding: 4px 10px;
    min-height: 22px;
}
QMainWindow QPushButton:hover {
    background: #25496F;
    border-color: #3C6A9A;
}
QMainWindow QPushButton:pressed {
    background: #163049;
}
QMainWindow QPushButton:disabled {
    color: #6F8399;
    background: #152538;
    border-color: #24384F;
}
QMainWindow QPushButton#startButton {
    color: #FFFFFF;
    background: #2F7D5B;
    border: 1px solid #3B9A70;
    border-radius: 7px;
    font-size: 10pt;
    font-weight: 600;
    min-width: 132px;
    max-width: 190px;
    min-height: 26px;
    max-height: 30px;
    padding: 2px 14px;
}
QMainWindow QPushButton#startButton:hover {
    background: #37946B;
    border-color: #55B98D;
}
QMainWindow QPushButton#startButton:pressed {
    background: #256348;
}
QMainWindow QPushButton#terminalButton,
QMainWindow QPushButton#layoutpushButton {
    background: transparent;
    border: 1px solid #35516E;
    color: #D7E3F1;
    min-width: 66px;
    max-width: 84px;
    min-height: 26px;
    max-height: 30px;
    padding: 2px 8px;
}
QMainWindow QPushButton#terminalButton:hover,
QMainWindow QPushButton#layoutpushButton:hover {
    background: #1B3552;
    border-color: #4A7098;
}
QMainWindow QComboBox {
    color: #E6EEF8;
    background: #0E1D30;
    border: 1px solid #2B4B6F;
    border-radius: 6px;
    padding: 2px 8px;
    min-height: 24px;
    max-height: 28px;
}
QMainWindow QComboBox:hover {
    border-color: #3C6A9A;
}
QMainWindow QComboBox:focus {
    border-color: #4A90E2;
}
QMainWindow QComboBox QAbstractItemView {
    background: #12233A;
    color: #E6EEF8;
    border: 1px solid #2B4B6F;
    selection-background-color: #2F80ED;
    selection-color: #FFFFFF;
    outline: 0;
    padding: 4px;
}
QMainWindow QScrollBar:vertical {
    background: #0B1728;
    width: 10px;
    margin: 0;
}
QMainWindow QScrollBar::handle:vertical {
    background: #2B4B6F;
    border-radius: 5px;
    min-height: 28px;
}
QMainWindow QScrollBar::handle:vertical:hover {
    background: #3C6A9A;
}
QMainWindow QScrollBar::add-line:vertical,
QMainWindow QScrollBar::sub-line:vertical,
QMainWindow QScrollBar::add-page:vertical,
QMainWindow QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}
QMainWindow QScrollArea {
    border: 0;
    background: #0B1728;
}
QMenuBar {
    background: #0C1C30;
    color: #D6E2F0;
    border-bottom: 1px solid #1F3A58;
    padding: 1px 6px;
}
QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #1B3552;
}
QMenu {
    background: #12233A;
    color: #E6EEF8;
    border: 1px solid #2B4B6F;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 28px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: #2F80ED;
    color: #FFFFFF;
}
QMenu::item:disabled {
    color: #6F8399;
}
QMenu::separator {
    height: 1px;
    background: #2B4B6F;
    margin: 4px 8px;
}
QToolTip {
    color: #F1F5F9;
    background: #1B3552;
    border: 1px solid #3C6A9A;
    padding: 4px 7px;
}
QFrame#emptyCard {
    background: #12233A;
    border: 1px solid #23415F;
    border-radius: 14px;
}
QLabel#emptyEyebrow {
    color: #6FB3FF;
    font-size: 9pt;
    font-weight: 700;
}
QLabel#emptyTitle {
    color: #F5F9FF;
    font-size: 22pt;
    font-weight: 700;
}
QLabel#emptyBody {
    color: #A9BDD2;
    font-size: 10pt;
}
QLabel#emptyHint {
    color: #7F96AD;
    font-size: 8.5pt;
}
QPushButton#emptyPrimary {
    color: #FFFFFF;
    background: #2F80ED;
    border: 1px solid #4A95F5;
    border-radius: 7px;
    font-weight: 600;
    min-height: 30px;
    padding: 3px 16px;
}
QPushButton#emptyPrimary:hover {
    background: #3B8CF7;
}
QPushButton#emptySecondary {
    color: #DCE8F5;
    background: transparent;
    border: 1px solid #35516E;
    border-radius: 7px;
    min-height: 30px;
    padding: 3px 16px;
}
QPushButton#emptySecondary:hover {
    background: #1B3552;
    border-color: #4A7098;
}
QDialog {
    background: #F6F8FB;
    color: #1E293B;
}
QDialog QLabel {
    color: #1E293B;
}
QDialog QLineEdit,
QDialog QComboBox,
QDialog QSpinBox {
    color: #1E293B;
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 3px 7px;
    min-height: 22px;
}
QDialog QLineEdit:focus,
QDialog QComboBox:focus,
QDialog QSpinBox:focus {
    border-color: #2F80ED;
}
QDialog QPushButton {
    color: #1E293B;
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 4px 12px;
    min-height: 24px;
}
QDialog QPushButton:hover {
    background: #EAF2FF;
    border-color: #2F80ED;
}
QDialog QPushButton:pressed {
    background: #DCEBFF;
}
"""


def apply_theme(app: QtWidgets.QApplication) -> None:
    if app.style().objectName().lower() != "fusion":
        app.setStyle("Fusion")
    font = QtGui.QFont(font_family(), 10)
    font.setStyleStrategy(QtGui.QFont.PreferAntialias)
    app.setFont(font)
    app.setStyleSheet(STYLESHEET)
