"""Visualization panel wrapper — hosts the 3D viewport and color controls."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
)
from PyQt6.QtCore import pyqtSlot
import numpy as np

from gui.visualization.viewport import Viewport3D


class VisualizationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)

        # Toolbar row
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Color by:"))
        self.combo_color = QComboBox()
        self.combo_color.addItems(["Element (CPK)", "Speed"])
        self.combo_color.currentTextChanged.connect(self._on_color_changed)
        toolbar.addWidget(self.combo_color)

        self.btn_reset_cam = QPushButton("Reset Camera")
        self.btn_reset_cam.setFixedWidth(110)
        self.btn_reset_cam.clicked.connect(self._reset_camera)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_reset_cam)
        lay.addLayout(toolbar)

        # 3-D viewport
        self.viewport = Viewport3D(self)
        lay.addWidget(self.viewport, stretch=1)

    @pyqtSlot(np.ndarray, np.ndarray, int)
    def on_frame_ready(self, positions: np.ndarray, velocities: np.ndarray, step: int) -> None:
        self.viewport.update_positions(positions, velocities, step)

    def set_system(self, species: list, box: np.ndarray) -> None:
        self.viewport.set_system(species, box)

    def _on_color_changed(self, text: str) -> None:
        mode = "speed" if "Speed" in text else "element"
        self.viewport.set_color_mode(mode)

    def _reset_camera(self) -> None:
        if hasattr(self.viewport, "_plotter"):
            self.viewport._plotter.reset_camera()
            self.viewport._plotter.render()
