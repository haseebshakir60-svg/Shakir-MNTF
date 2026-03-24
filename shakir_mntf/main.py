"""
Shakir MNTF — launcher entry point for pip-installed package.

Author:  Abdul Haseeb Shakir
© 2026 Abdul Haseeb Shakir. All Rights Reserved.
"""
import sys
import os


def main() -> None:
    # Add the installed package root to sys.path so all submodules resolve
    pkg_root = os.path.dirname(os.path.dirname(__file__))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    os.environ.setdefault("NUMBA_NUM_THREADS", str(max(1, os.cpu_count() - 1)))
    os.environ.setdefault("OMP_NUM_THREADS",   str(max(1, os.cpu_count() - 1)))
    os.environ.setdefault("MKL_NUM_THREADS",   str(max(1, os.cpu_count() - 1)))

    from PyQt6.QtWidgets import QApplication
    from gui.main_window import MainWindow
    from gui.style import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("Shakir MNTF")
    app.setApplicationVersion("1.0.0")
    apply_theme(app, "dark")

    _logo = os.path.join(pkg_root, "assets", "logo.svg")
    if os.path.exists(_logo):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(_logo))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
