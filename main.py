"""
Shakir MNTF — entry point.

Author:  Abdul Haseeb Shakir
Version: 1.0.0
Year:    2026

© 2026 Abdul Haseeb Shakir. All Rights Reserved.
Do not use, copy, or distribute without written permission
from Abdul Haseeb Shakir.

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
from gui.style import apply_theme


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Shakir MNTF")
    app.setApplicationVersion("1.0.0")
    apply_theme(app, "dark")   # default theme; user can switch via View → Theme

    _logo = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
    if os.path.exists(_logo):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(_logo))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
