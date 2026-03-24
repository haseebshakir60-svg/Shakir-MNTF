"""
Theme stylesheets for Shakir MNTF.

Available themes: "dark" | "light"
"""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════════════════════════
# DARK THEME
# ═══════════════════════════════════════════════════════════════════════════════
DARK_STYLESHEET = """
/* ── Main window & all widgets ────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #12131a;
    color: #e0e4f0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

/* ── Menu bar ─────────────────────────────────────────────────────── */
QMenuBar {
    background-color: #1a1c28;
    color: #c8cce0;
    border-bottom: 1px solid #2e3050;
}
QMenuBar::item:selected { background-color: #2e3a6e; }
QMenu {
    background-color: #1e2030;
    border: 1px solid #30345a;
    color: #c8cce0;
}
QMenu::item:selected { background-color: #2e3a6e; }
QMenu::separator { height: 1px; background: #30345a; margin: 3px 8px; }

/* ── Tool bar ─────────────────────────────────────────────────────── */
QToolBar {
    background-color: #1a1c28;
    border-bottom: 1px solid #2e3050;
    spacing: 4px;
    padding: 2px;
}
QToolButton {
    background-color: transparent;
    color: #c8cce0;
    border-radius: 4px;
    padding: 4px 8px;
}
QToolButton:hover  { background-color: #2a2e50; }
QToolButton:pressed { background-color: #3a4070; }

/* ── Dock widgets ─────────────────────────────────────────────────── */
QDockWidget {
    background-color: #16182a;
    color: #e0e4f0;
}
QDockWidget::title {
    background-color: #1e2038;
    padding: 5px 8px;
    border-top: 2px solid #3d5afe;
    font-weight: bold;
}

/* ── Group boxes ──────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #2a2e50;
    border-radius: 5px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    color: #9098d0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px; top: 0px;
    color: #7080c0;
}

/* ── Buttons ──────────────────────────────────────────────────────── */
QPushButton {
    background-color: #2a3060;
    color: #c8d8ff;
    border: 1px solid #3d50a0;
    border-radius: 5px;
    padding: 5px 14px;
    min-width: 60px;
}
QPushButton:hover   { background-color: #3a4480; border-color: #5060c0; }
QPushButton:pressed { background-color: #1e2850; }
QPushButton:disabled { background-color: #1a1d30; color: #505880; border-color: #252840; }

QPushButton#btn_run {
    background-color: #1a5c2a; border-color: #2aaa44;
    color: #80ff9a; font-weight: bold;
}
QPushButton#btn_run:hover { background-color: #1e7030; }

QPushButton#btn_stop {
    background-color: #5c1a1a; border-color: #aa2a2a;
    color: #ff8080; font-weight: bold;
}
QPushButton#btn_stop:hover { background-color: #702020; }

/* ── Inputs ───────────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #1a1d2e;
    color: #d0d8f8;
    border: 1px solid #2e3258;
    border-radius: 4px;
    padding: 3px 6px;
    selection-background-color: #3d5afe;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #5070ff;
}
QComboBox QAbstractItemView {
    background-color: #1e2038;
    selection-background-color: #3d5afe;
    color: #d0d8f8;
    border: 1px solid #30345a;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #252840;
    border: none; width: 16px;
}

/* ── Sliders ──────────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    height: 4px; background: #2a2e50; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #5070ff; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #3d5afe; border-radius: 2px; }

/* ── Check box ────────────────────────────────────────────────────── */
QCheckBox { color: #c0c8e8; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid #3d50a0; border-radius: 3px;
    background-color: #1a1d2e;
}
QCheckBox::indicator:checked { background-color: #3d5afe; border-color: #5070ff; }

/* ── Tab widget ───────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #2a2e50; background-color: #14162a;
}
QTabBar::tab {
    background-color: #1e2038; color: #8090c0;
    border: 1px solid #2a2e50; border-bottom: none;
    padding: 5px 14px;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #14162a; color: #d0daff;
    border-top: 2px solid #3d5afe;
}
QTabBar::tab:hover { background-color: #252845; }

/* ── Progress bar ─────────────────────────────────────────────────── */
QProgressBar {
    background-color: #1a1d2e; border: 1px solid #2a2e50;
    border-radius: 4px; text-align: center; color: #d0d8f8;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #3d5afe, stop:1 #00e5ff);
    border-radius: 4px;
}

/* ── Table ────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #14162a; gridline-color: #22253c;
    color: #d0d8f8; selection-background-color: #2e3a6e;
}
QHeaderView::section {
    background-color: #1e2038; color: #9098c8;
    border: 1px solid #2a2e50; padding: 4px;
}

/* ── Scroll bar ───────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #14162a; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #2e3a6e; border-radius: 4px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #14162a; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #2e3a6e; border-radius: 4px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Splitter ─────────────────────────────────────────────────────── */
QSplitter::handle { background-color: #2a2e50; width: 2px; height: 2px; }

/* ── Status bar ───────────────────────────────────────────────────── */
QStatusBar {
    background-color: #1a1c28; color: #7080a0;
    border-top: 1px solid #2e3050;
}

/* ── Log panel ────────────────────────────────────────────────────── */
QPlainTextEdit#log_widget {
    background-color: #0e0f18; color: #70d090;
    font-family: "Cascadia Code","Consolas",monospace;
    font-size: 9pt; border: 1px solid #1a2030;
}

/* ── Value labels ─────────────────────────────────────────────────── */
QLabel#label_value { color: #80c8ff; font-weight: bold; }

/* ── Frame ────────────────────────────────────────────────────────── */
QFrame { border: none; }
"""


# ═══════════════════════════════════════════════════════════════════════════════
# LIGHT THEME
# ═══════════════════════════════════════════════════════════════════════════════
LIGHT_STYLESHEET = """
/* ── Main window & all widgets ────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #f0f2f8;
    color: #1a1e2e;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

/* ── Menu bar ─────────────────────────────────────────────────────── */
QMenuBar {
    background-color: #ffffff;
    color: #2a2e48;
    border-bottom: 1px solid #d0d4e8;
}
QMenuBar::item:selected { background-color: #dde4ff; }
QMenu {
    background-color: #ffffff;
    border: 1px solid #c8ccdc;
    color: #2a2e48;
}
QMenu::item:selected { background-color: #dde4ff; color: #1a1e2e; }
QMenu::separator { height: 1px; background: #d0d4e8; margin: 3px 8px; }

/* ── Tool bar ─────────────────────────────────────────────────────── */
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #d0d4e8;
    spacing: 4px; padding: 2px;
}
QToolButton {
    background-color: transparent; color: #2a2e48;
    border-radius: 4px; padding: 4px 8px;
}
QToolButton:hover   { background-color: #e8ecff; }
QToolButton:pressed { background-color: #d0d8ff; }

/* ── Dock widgets ─────────────────────────────────────────────────── */
QDockWidget { background-color: #f8f9fc; color: #1a1e2e; }
QDockWidget::title {
    background-color: #eef0f8;
    padding: 5px 8px;
    border-top: 2px solid #3d5afe;
    font-weight: bold;
    color: #2a3068;
}

/* ── Group boxes ──────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #c8ccdc;
    border-radius: 5px;
    margin-top: 12px; padding-top: 8px;
    font-weight: bold; color: #4050a0;
    background-color: #f8f9fc;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 10px; top: 0px; color: #3040a0;
}

/* ── Buttons ──────────────────────────────────────────────────────── */
QPushButton {
    background-color: #e8ecff;
    color: #1a2870;
    border: 1px solid #a0a8d8;
    border-radius: 5px; padding: 5px 14px; min-width: 60px;
}
QPushButton:hover   { background-color: #d0d8ff; border-color: #6070c8; }
QPushButton:pressed { background-color: #b8c4ff; }
QPushButton:disabled { background-color: #e8eaf0; color: #9098b8; border-color: #c8ccdc; }

QPushButton#btn_run {
    background-color: #d0f0d8; border-color: #2aaa44;
    color: #0a6020; font-weight: bold;
}
QPushButton#btn_run:hover { background-color: #b8e8c4; }

QPushButton#btn_stop {
    background-color: #ffd8d8; border-color: #cc3333;
    color: #880000; font-weight: bold;
}
QPushButton#btn_stop:hover { background-color: #ffbcbc; }

/* ── Inputs ───────────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #1a1e2e;
    border: 1px solid #c0c4d8;
    border-radius: 4px; padding: 3px 6px;
    selection-background-color: #a8b8ff;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #3d5afe;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    selection-background-color: #dde4ff;
    color: #1a1e2e; border: 1px solid #c0c4d8;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #eef0f8; border: none; width: 16px;
}

/* ── Sliders ──────────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    height: 4px; background: #c8ccdc; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #3d5afe; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #6080ff; border-radius: 2px; }

/* ── Check box ────────────────────────────────────────────────────── */
QCheckBox { color: #1a1e2e; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid #a0a8d8; border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked { background-color: #3d5afe; border-color: #3d5afe; }

/* ── Tab widget ───────────────────────────────────────────────────── */
QTabWidget::pane { border: 1px solid #c8ccdc; background-color: #f8f9fc; }
QTabBar::tab {
    background-color: #eef0f8; color: #6070a0;
    border: 1px solid #c8ccdc; border-bottom: none;
    padding: 5px 14px;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #f8f9fc; color: #1a2870;
    border-top: 2px solid #3d5afe;
}
QTabBar::tab:hover { background-color: #dde4ff; }

/* ── Progress bar ─────────────────────────────────────────────────── */
QProgressBar {
    background-color: #e8eaf0; border: 1px solid #c0c4d8;
    border-radius: 4px; text-align: center; color: #2a2e48;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #3d5afe, stop:1 #00b0d8);
    border-radius: 4px;
}

/* ── Table ────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #ffffff; gridline-color: #d8dce8;
    color: #1a1e2e; selection-background-color: #dde4ff;
}
QHeaderView::section {
    background-color: #eef0f8; color: #4050a0;
    border: 1px solid #c8ccdc; padding: 4px;
}

/* ── Scroll bar ───────────────────────────────────────────────────── */
QScrollBar:vertical { background: #eef0f8; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical {
    background: #a0a8d8; border-radius: 4px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #eef0f8; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #a0a8d8; border-radius: 4px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Splitter ─────────────────────────────────────────────────────── */
QSplitter::handle { background-color: #c8ccdc; width: 2px; height: 2px; }

/* ── Status bar ───────────────────────────────────────────────────── */
QStatusBar {
    background-color: #ffffff; color: #6070a0;
    border-top: 1px solid #d0d4e8;
}

/* ── Log panel ────────────────────────────────────────────────────── */
QPlainTextEdit#log_widget {
    background-color: #f4f8f0; color: #1a6030;
    font-family: "Cascadia Code","Consolas",monospace;
    font-size: 9pt; border: 1px solid #c8d4c0;
}

/* ── Value labels ─────────────────────────────────────────────────── */
QLabel#label_value { color: #1a40c0; font-weight: bold; }

/* ── Frame ────────────────────────────────────────────────────────── */
QFrame { border: none; }
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Theme registry + manager
# ═══════════════════════════════════════════════════════════════════════════════

THEMES: dict[str, str] = {
    "dark":  DARK_STYLESHEET,
    "light": LIGHT_STYLESHEET,
}

_CURRENT_THEME: str = "dark"


def get_stylesheet(theme: str = "dark") -> str:
    return THEMES.get(theme, DARK_STYLESHEET)


def current_theme() -> str:
    return _CURRENT_THEME


def apply_theme(app, theme: str) -> None:
    """Apply theme to the QApplication and remember the selection."""
    global _CURRENT_THEME
    _CURRENT_THEME = theme
    app.setStyleSheet(get_stylesheet(theme))
