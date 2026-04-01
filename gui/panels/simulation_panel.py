"""
Simulation control panel.

Provides:
  - Ensemble / integrator / thermostat selection
  - Run parameters (n_steps, dt, record_every)
  - Run / Pause / Stop buttons
  - Progress bar + live thermodynamic readout
"""
from __future__ import annotations
import math
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QProgressBar, QFormLayout, QSizePolicy,
    QCheckBox, QSlider,
)
from PyQt6.QtCore import Qt, pyqtSignal


class SimulationPanel(QWidget):
    """Left-side simulation control dock panel."""

    # Emitted when user clicks Run
    run_requested = pyqtSignal(dict)   # carries parameter dict
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._element = "Ar"
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(8)

        # ── Run parameters ────────────────────────────────────────
        grp_run = QGroupBox("Run Parameters")
        form_run = QFormLayout(grp_run)

        self.spin_steps = QSpinBox()
        self.spin_steps.setRange(100, 50_000_000)
        self.spin_steps.setSingleStep(1000)
        self.spin_steps.setValue(50_000)
        self.spin_steps.setGroupSeparatorShown(True)
        form_run.addRow("Steps:", self.spin_steps)

        self.dspin_dt = QDoubleSpinBox()
        self.dspin_dt.setRange(0.0001, 0.05)
        self.dspin_dt.setDecimals(4)
        self.dspin_dt.setSingleStep(0.001)
        self.dspin_dt.setValue(0.005)
        self.dspin_dt.setSuffix("  τ")
        form_run.addRow("Time step:", self.dspin_dt)

        self.spin_record = QSpinBox()
        self.spin_record.setRange(1, 10_000)
        self.spin_record.setValue(100)
        form_run.addRow("Record every:", self.spin_record)

        root.addWidget(grp_run)

        # ── Ensemble / integrator ─────────────────────────────────
        grp_ens = QGroupBox("Ensemble & Integrator")
        form_ens = QFormLayout(grp_ens)

        self.combo_ensemble = QComboBox()
        self.combo_ensemble.addItems(["NVE", "NVT", "NPT"])
        self.combo_ensemble.currentTextChanged.connect(self._on_ensemble_changed)
        form_ens.addRow("Ensemble:", self.combo_ensemble)

        self.combo_integrator = QComboBox()
        self.combo_integrator.addItems(["Velocity Verlet", "Leapfrog"])
        form_ens.addRow("Integrator:", self.combo_integrator)

        self.combo_thermostat = QComboBox()
        self.combo_thermostat.addItems(["Berendsen", "Velocity Rescale", "Nosé-Hoover"])
        form_ens.addRow("Thermostat:", self.combo_thermostat)

        self.dspin_T_target = QDoubleSpinBox()
        self.dspin_T_target.setRange(1.0, 10000.0)
        self.dspin_T_target.setValue(300.0)
        self.dspin_T_target.setSuffix("  K")
        form_ens.addRow("T target:", self.dspin_T_target)

        self.dspin_tau_T = QDoubleSpinBox()
        self.dspin_tau_T.setRange(1.0, 10000.0)
        self.dspin_tau_T.setValue(100.0)
        self.dspin_tau_T.setSuffix("  τ")
        form_ens.addRow("τ_T:", self.dspin_tau_T)

        self.dspin_P_target = QDoubleSpinBox()
        self.dspin_P_target.setRange(0.0, 1000.0)
        self.dspin_P_target.setValue(1.0)
        self.dspin_P_target.setSuffix("  bar")
        self.dspin_P_target.setEnabled(False)
        form_ens.addRow("P target:", self.dspin_P_target)

        root.addWidget(grp_ens)

        # ── Force field ───────────────────────────────────────────
        grp_ff = QGroupBox("Force Field")
        form_ff = QFormLayout(grp_ff)

        self.combo_ff = QComboBox()
        self.combo_ff.addItems(["Lennard-Jones", "Morse", "EAM (Cu)"])
        self.combo_ff.currentTextChanged.connect(self._on_ff_changed)
        form_ff.addRow("Potential:", self.combo_ff)

        self.dspin_eps = QDoubleSpinBox()
        self.dspin_eps.setRange(0.01, 100.0)
        self.dspin_eps.setValue(1.0)
        self._row_eps = form_ff.addRow("ε:", self.dspin_eps)

        self.dspin_sig = QDoubleSpinBox()
        self.dspin_sig.setRange(0.1, 10.0)
        self.dspin_sig.setValue(1.0)
        self._row_sig = form_ff.addRow("σ:", self.dspin_sig)

        self.dspin_rcut = QDoubleSpinBox()
        self.dspin_rcut.setRange(1.0, 10.0)
        self.dspin_rcut.setValue(2.5)
        self._row_rcut = form_ff.addRow("r_cut (×σ):", self.dspin_rcut)

        self._lbl_eam = QLabel("Cu_u3.eam  (Foiles 1986)")
        self._lbl_eam.setVisible(False)
        form_ff.addRow("File:", self._lbl_eam)

        root.addWidget(grp_ff)

        # ── Run controls ──────────────────────────────────────────
        grp_ctrl = QGroupBox("Controls")
        ctrl_lay = QVBoxLayout(grp_ctrl)

        btn_row = QHBoxLayout()
        self.btn_run  = QPushButton("▶  Run")
        self.btn_run.setObjectName("btn_run")
        self.btn_stop = QPushButton("■  Stop")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setEnabled(False)
        btn_row.addWidget(self.btn_run)
        btn_row.addWidget(self.btn_stop)
        ctrl_lay.addLayout(btn_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        ctrl_lay.addWidget(self.progress)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_lay.addWidget(self.lbl_status)

        # ── Simulation timer ──────────────────────────────────────
        timer_form = QFormLayout()
        timer_form.setContentsMargins(0, 4, 0, 0)

        self.lbl_elapsed   = QLabel("—")
        self.lbl_elapsed.setObjectName("label_value")
        self.lbl_elapsed.setAlignment(Qt.AlignmentFlag.AlignRight)
        timer_form.addRow("Elapsed:", self.lbl_elapsed)

        self.lbl_remaining = QLabel("—")
        self.lbl_remaining.setObjectName("label_value")
        self.lbl_remaining.setAlignment(Qt.AlignmentFlag.AlignRight)
        timer_form.addRow("Remaining:", self.lbl_remaining)

        self.lbl_total_time = QLabel("—")
        self.lbl_total_time.setObjectName("label_value")
        self.lbl_total_time.setAlignment(Qt.AlignmentFlag.AlignRight)
        timer_form.addRow("Total time:", self.lbl_total_time)

        self.lbl_speed = QLabel("—")
        self.lbl_speed.setObjectName("label_value")
        self.lbl_speed.setAlignment(Qt.AlignmentFlag.AlignRight)
        timer_form.addRow("Speed:", self.lbl_speed)

        ctrl_lay.addLayout(timer_form)
        root.addWidget(grp_ctrl)

        # ── Live thermodynamics readout ───────────────────────────
        grp_thermo = QGroupBox("Live Thermodynamics")
        form_t = QFormLayout(grp_thermo)

        self._thermo_labels: dict[str, QLabel] = {}
        for key, text in [
            ("step",        "Step"),
            ("temperature", "Temperature"),
            ("ke",          "KE"),
            ("pe",          "PE"),
            ("te",          "Total E"),
            ("pressure",    "Pressure"),
        ]:
            lbl = QLabel("—")
            lbl.setObjectName("label_value")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            form_t.addRow(f"{text}:", lbl)
            self._thermo_labels[key] = lbl

        root.addWidget(grp_thermo)

        # ── Parallelism ───────────────────────────────────────────
        grp_par = QGroupBox("Parallelism")
        form_par = QFormLayout(grp_par)

        n_physical = os.cpu_count() or 1

        # CPU cores slider + label
        core_row = QHBoxLayout()
        self.slider_cores = QSlider(Qt.Orientation.Horizontal)
        self.slider_cores.setRange(1, n_physical)
        self.slider_cores.setValue(max(1, n_physical - 1))
        self.slider_cores.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_cores.setTickInterval(1)
        self.lbl_cores = QLabel(f"{self.slider_cores.value()} / {n_physical}")
        self.lbl_cores.setObjectName("label_value")
        self.lbl_cores.setMinimumWidth(48)
        self.slider_cores.valueChanged.connect(
            lambda v: self.lbl_cores.setText(f"{v} / {n_physical}")
        )
        core_row.addWidget(self.slider_cores)
        core_row.addWidget(self.lbl_cores)
        form_par.addRow("CPU cores:", core_row)

        # GPU checkbox — detect via numba.cuda (same backend the engine uses)
        self.chk_gpu = QCheckBox("Use GPU (CUDA)  — force calculation on GPU")
        gpu_ok  = False
        gpu_name = "None"
        try:
            from numba import cuda as _nc
            if _nc.is_available():
                gpu_ok   = True
                gpu_name = _nc.get_current_device().name.decode()
        except Exception:
            pass
        self.chk_gpu.setChecked(gpu_ok)
        self.chk_gpu.setEnabled(gpu_ok)
        self.chk_gpu.setToolTip(
            "When checked, force calculations run on the GPU.\n"
            "CPU cores slider controls parallelism when GPU is OFF."
        )
        if not gpu_ok:
            self.chk_gpu.setText("Use GPU (CUDA)  — not available")
        form_par.addRow("Backend:", self.chk_gpu)

        # When GPU is on, CPU core count doesn't affect force calc → grey out
        def _on_gpu_toggled(checked: bool) -> None:
            self.slider_cores.setEnabled(not checked)
            self.lbl_cores.setEnabled(not checked)
        self.chk_gpu.toggled.connect(_on_gpu_toggled)
        _on_gpu_toggled(gpu_ok)   # apply immediately

        # Hardware summary label
        hw_text = f"CPU: {n_physical} logical cores"
        if gpu_name != "None":
            hw_text += f"  |  GPU: {gpu_name}"
        lbl_hw = QLabel(hw_text)
        lbl_hw.setStyleSheet("color: #607898; font-size: 8pt;")
        lbl_hw.setWordWrap(True)
        form_par.addRow("", lbl_hw)

        root.addWidget(grp_par)
        root.addStretch()

        # Wire buttons
        self.btn_run.clicked.connect(self._on_run_clicked)
        self.btn_stop.clicked.connect(self.stop_requested.emit)

    def _on_ff_changed(self, text: str) -> None:
        is_lj = text == "Lennard-Jones"
        self.dspin_eps.setVisible(is_lj)
        self.dspin_sig.setVisible(is_lj)
        self.dspin_rcut.setVisible(is_lj)
        self._lbl_eam.setVisible(text == "EAM (Cu)")

    def _on_ensemble_changed(self, text: str) -> None:
        is_nvt_npt = text in ("NVT", "NPT")
        is_npt     = text == "NPT"
        self.combo_thermostat.setEnabled(is_nvt_npt)
        self.dspin_T_target.setEnabled(is_nvt_npt)
        self.dspin_tau_T.setEnabled(is_nvt_npt)
        self.dspin_P_target.setEnabled(is_npt)

    def _on_run_clicked(self) -> None:
        params = self.get_params()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.run_requested.emit(params)

    def on_finished(self, total_elapsed: float = 0.0) -> None:
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Finished")
        self.progress.setValue(100)
        self.lbl_remaining.setText("—")
        if total_elapsed > 0:
            self.lbl_total_time.setText(_fmt_time(total_elapsed))

    def update_progress(self, step: int, total: int, elapsed: float) -> None:
        pct = int(100 * step / max(total, 1))
        self.progress.setValue(pct)

        remaining = (elapsed / max(step, 1)) * (total - step) if step > 0 else 0
        speed     = step / max(elapsed, 1e-6)

        self.lbl_status.setText(f"Step {step:,} / {total:,}")
        self.lbl_elapsed.setText(_fmt_time(elapsed))
        self.lbl_remaining.setText(_fmt_time(remaining))
        self.lbl_speed.setText(f"{speed:,.0f} steps/s")

    def set_element(self, element: str) -> None:
        self._element = element

    def update_thermo(self, data: dict) -> None:
        from core.units import ELEMENTS, KB_SI
        _EV = 1.602176634e-19   # J per eV
        elem = ELEMENTS.get(self._element)
        if elem:
            data = dict(data)
            eps_eV = elem.epsilon_J / _EV
            if "temperature" in data:
                data["temperature"] = data["temperature"] * elem.epsilon_J / KB_SI
            for key in ("ke", "pe", "te"):
                if key in data:
                    data[key] = data[key] * eps_eV

        for key, lbl in self._thermo_labels.items():
            if key in data:
                val = data[key]
                if key == "step":
                    lbl.setText(f"{int(val):,}")
                elif key == "temperature":
                    lbl.setText(f"{val:.1f} K")
                elif key in ("ke", "pe", "te"):
                    lbl.setText(f"{val:.4f} eV")
                else:
                    lbl.setText(f"{val:.4f}")

    def get_params(self) -> dict:
        return {
            "n_steps":      self.spin_steps.value(),
            "dt":           self.dspin_dt.value(),
            "record_every": self.spin_record.value(),
            "ensemble":     self.combo_ensemble.currentText(),
            "integrator":   self.combo_integrator.currentText(),
            "thermostat":   self.combo_thermostat.currentText(),
            "T_target_K":   self.dspin_T_target.value(),
            "tau_T":        self.dspin_tau_T.value(),
            "P_target_bar": self.dspin_P_target.value(),
            "forcefield":   self.combo_ff.currentText(),
            "epsilon":      self.dspin_eps.value(),
            "sigma":        self.dspin_sig.value(),
            "r_cut":        self.dspin_rcut.value(),
            "n_cores":      self.slider_cores.value(),
            "use_gpu":      self.chk_gpu.isChecked(),
        }


def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"
