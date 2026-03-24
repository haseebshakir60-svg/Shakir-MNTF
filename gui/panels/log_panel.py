"""Log panel — displays Python logging output in a QPlainTextEdit."""
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QTextCharFormat, QFont


class _QtLogHandler(logging.Handler, QObject):
    """Logging handler that emits a Qt signal with each log record."""
    new_record = pyqtSignal(str, int)   # message, level

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.new_record.emit(msg, record.levelno)


class LogPanel(QWidget):
    """
    Dockable log panel.

    Connects to Python's root logger and displays coloured output.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._setup_logger()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)

        self.text = QPlainTextEdit()
        self.text.setObjectName("log_widget")
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(2000)
        lay.addWidget(self.text)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton("Clear")
        btn_clear.setFixedWidth(60)
        btn_clear.clicked.connect(self.text.clear)
        btn_row.addStretch()
        btn_row.addWidget(btn_clear)
        lay.addLayout(btn_row)

    def _setup_logger(self):
        self._handler = _QtLogHandler()
        fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        self._handler.setFormatter(fmt)
        self._handler.new_record.connect(self._append)
        logging.getLogger().addHandler(self._handler)
        logging.getLogger().setLevel(logging.DEBUG)

    def _append(self, msg: str, level: int) -> None:
        if level >= logging.ERROR:
            colour = "#ff6060"
        elif level >= logging.WARNING:
            colour = "#ffcc44"
        elif level >= logging.INFO:
            colour = "#80e880"
        else:
            colour = "#7090a0"
        self.text.appendHtml(f'<span style="color:{colour}">{msg}</span>')
