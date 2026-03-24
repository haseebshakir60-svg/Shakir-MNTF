"""
Atom Builder Panel — lets the user construct a starting configuration.

Supports:
  - FCC / BCC / SC lattice or random gas
  - Element selection
  - N cells / N atoms control
  - Initial temperature
  - "Build" button emits the constructed SimulationState
"""
from __future__ import annotations
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
    QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal

from builder.lattice import build_fcc, build_bcc, build_sc, build_random_gas
from builder.element_data import ELEMENT_DATA
from core.state import SimulationState

log = logging.getLogger(__name__)


class AtomBuilderPanel(QWidget):
    """Panel for constructing the initial atom configuration."""

    system_built = pyqtSignal(object)   # emits SimulationState

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)

        grp = QGroupBox("System Builder")
        form = QFormLayout(grp)

        # Element selector
        self.combo_element = QComboBox()
        self.combo_element.addItems(sorted(ELEMENT_DATA.keys()))
        self.combo_element.setCurrentText("Ar")
        form.addRow("Element:", self.combo_element)

        # Lattice type
        self.combo_lattice = QComboBox()
        self.combo_lattice.addItems(["FCC", "BCC", "SC", "Random Gas"])
        self.combo_lattice.currentTextChanged.connect(self._on_lattice_changed)
        form.addRow("Structure:", self.combo_lattice)

        # Unit cells (for crystal) / N atoms (for gas)
        self.spin_cells = QSpinBox()
        self.spin_cells.setRange(1, 20)
        self.spin_cells.setValue(4)
        form.addRow("Unit cells:", self.spin_cells)

        self.spin_natoms = QSpinBox()
        self.spin_natoms.setRange(10, 100_000)
        self.spin_natoms.setValue(500)
        self.spin_natoms.setVisible(False)
        self.lbl_natoms = QLabel("N atoms:")
        self.lbl_natoms.setVisible(False)
        form.addRow(self.lbl_natoms, self.spin_natoms)

        self.dspin_box = QDoubleSpinBox()
        self.dspin_box.setRange(5.0, 200.0)
        self.dspin_box.setValue(20.0)
        self.dspin_box.setSuffix("  σ")
        self.dspin_box.setVisible(False)
        self.lbl_box = QLabel("Box size:")
        self.lbl_box.setVisible(False)
        form.addRow(self.lbl_box, self.dspin_box)

        # Temperature
        self.dspin_T = QDoubleSpinBox()
        self.dspin_T.setRange(1.0, 10000.0)
        self.dspin_T.setValue(300.0)
        self.dspin_T.setSuffix("  K")
        form.addRow("Temperature:", self.dspin_T)

        # Info label
        self.lbl_info = QLabel("")
        self.lbl_info.setObjectName("label_value")
        form.addRow("", self.lbl_info)

        self.spin_cells.valueChanged.connect(self._update_info)
        self.combo_lattice.currentTextChanged.connect(self._update_info)
        self._update_info()

        root.addWidget(grp)

        # Build button
        self.btn_build = QPushButton("Build System")
        self.btn_build.setObjectName("btn_run")
        self.btn_build.clicked.connect(self._on_build)
        root.addWidget(self.btn_build)
        root.addStretch()

    def _on_lattice_changed(self, text: str) -> None:
        is_gas = text == "Random Gas"
        self.spin_cells.setVisible(not is_gas)
        self.lbl_natoms.setVisible(is_gas)
        self.spin_natoms.setVisible(is_gas)
        self.lbl_box.setVisible(is_gas)
        self.dspin_box.setVisible(is_gas)

    def _update_info(self) -> None:
        lt = self.combo_lattice.currentText()
        n = self.spin_cells.value()
        if lt == "FCC":
            total = 4 * n ** 3
        elif lt in ("BCC",):
            total = 2 * n ** 3
        elif lt == "SC":
            total = n ** 3
        else:
            total = self.spin_natoms.value()
        self.lbl_info.setText(f"{total:,} atoms")

    def _on_build(self) -> None:
        element = self.combo_element.currentText()
        lattice = self.combo_lattice.currentText()
        T_K     = self.dspin_T.value()

        try:
            if lattice == "FCC":
                state = build_fcc(element=element, n_cells=self.spin_cells.value(), T_K=T_K)
            elif lattice == "BCC":
                state = build_bcc(element=element, n_cells=self.spin_cells.value(), T_K=T_K)
            elif lattice == "SC":
                state = build_sc(element=element, n_cells=self.spin_cells.value(), T_K=T_K)
            else:
                state = build_random_gas(
                    element=element,
                    n_atoms=self.spin_natoms.value(),
                    box_size=self.dspin_box.value(),
                    T_K=T_K,
                )
            log.info("Built %s system: %d atoms, box=%.2f σ", lattice, state.n_atoms, state.box[0])
            self.system_built.emit(state)
        except Exception as e:
            log.error("Build failed: %s", e)
