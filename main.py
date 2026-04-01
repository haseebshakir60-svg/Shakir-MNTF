"""
PyMDStudio — entry point.

Run with:
    python main.py

Requirements:
    pip install -r requirements.txt
"""
import sys
import os
import logging

# Set thread count for Numba/NumPy before any import
os.environ.setdefault("NUMBA_NUM_THREADS", str(max(1, os.cpu_count() - 1)))
os.environ.setdefault("OMP_NUM_THREADS",   str(max(1, os.cpu_count() - 1)))
os.environ.setdefault("MKL_NUM_THREADS",   str(max(1, os.cpu_count() - 1)))

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication


from PyQt6.QtCore import Qt

from gui.main_window import MainWindow
from gui.style import DARK_STYLESHEET


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PyMDStudio")
    app.setApplicationVersion("1.0.0")
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
