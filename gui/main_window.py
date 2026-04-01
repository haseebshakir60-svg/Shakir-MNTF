"""
Shakir MNTF — Main Window.

Layout:
  Left dock   : Atom Builder + Simulation Controls (tabbed)
  Center      : 3-D Visualization Viewport
  Right dock  : Analysis plots (tabbed)
  Bottom dock : Log output
  Status bar  : step / performance info
"""
from __future__ import annotations
import logging
import os
import math
from pathlib import Path


def _fmt_time_s(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} s"
    elif seconds < 3600:
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s:02d}s"
    else:
        h, rem = divmod(int(seconds), 3600)
        m, s   = divmod(rem, 60)
        return f"{h}h {m:02d}m {s:02d}s"

from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QToolBar, QLabel, QApplication,
)
from PyQt6.QtCore import Qt, QThread, pyqtSlot
from PyQt6.QtGui import QIcon, QAction, QActionGroup

from gui.style import apply_theme, current_theme
import numpy as np

from appconfig.config import APP_NAME, APP_VERSION, OUTPUT_DIR
from core.state import SimulationState
from core.units import ELEMENTS, K_to_reduced
from core.forcefields.lennard_jones import LJForcefield
from core.forcefields.morse import MorseForcefield
from core.forcefields.eam import EAMForcefield
from core.integrators.velocity_verlet import VelocityVerletIntegrator
from core.integrators.leapfrog import LeapfrogIntegrator
from core.thermostats.berendsen import BerendsenThermostat
from core.thermostats.rescale import VelocityRescaleThermostat
from core.thermostats.nose_hoover import NoseHooverThermostat
from core.ensembles.nve import NVEEnsemble
from core.ensembles.nvt import NVTEnsemble
from core.ensembles.npt import NPTEnsemble
from core.simulation import SimulationEngine
from workers.simulation_worker import SimulationWorker
from mdio.xyz_io import write_xyz_frame
from mdio.csv_io import ThermoCSVWriter
from mdio.checkpoint import save_checkpoint, load_checkpoint

from gui.panels.atom_builder_panel import AtomBuilderPanel
from gui.panels.simulation_panel import SimulationPanel
from gui.panels.visualization_panel import VisualizationPanel
from gui.panels.analysis_panel import AnalysisPanel
from gui.panels.log_panel import LogPanel

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1600, 900)

        _logo = Path(__file__).parent.parent / "assets" / "logo.svg"
        if _logo.exists():
            self.setWindowIcon(QIcon(str(_logo)))

        self._state:  SimulationState | None = None
        self._worker: SimulationWorker | None = None
        self._xyz_fh = None
        self._csv_writer: ThermoCSVWriter | None = None
        self._save_xyz  = True
        self._save_csv  = True

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._connect_signals()

        log.info("%s %s started.", APP_NAME, APP_VERSION)
        self.status_bar.showMessage("Ready — build a system to begin.")

    # ── UI construction ───────────────────────────────────────────────
    def _build_ui(self):
        # Central widget = visualization viewport
        self.viz_panel = VisualizationPanel()
        self.setCentralWidget(self.viz_panel)

        # Left dock: builder + sim controls
        self.builder_panel = AtomBuilderPanel()
        self.sim_panel     = SimulationPanel()

        left_tabs = QTabWidget()
        left_tabs.addTab(self.builder_panel, "System")
        left_tabs.addTab(self.sim_panel,     "Simulation")
        left_dock = QDockWidget("Setup", self)
        left_dock.setObjectName("left_dock")
        left_dock.setWidget(left_tabs)
        left_dock.setMinimumWidth(280)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

        # Right dock: analysis
        self.analysis_panel = AnalysisPanel()
        right_dock = QDockWidget("Analysis", self)
        right_dock.setObjectName("right_dock")
        right_dock.setWidget(self.analysis_panel)
        right_dock.setMinimumWidth(350)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

        # Bottom dock: log
        self.log_panel = LogPanel()
        bot_dock = QDockWidget("Log", self)
        bot_dock.setObjectName("bot_dock")
        bot_dock.setWidget(self.log_panel)
        bot_dock.setMaximumHeight(200)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bot_dock)

        # Status bar
        self.status_bar   = QStatusBar()
        self.lbl_perf     = QLabel("")
        self.lbl_perf.setObjectName("label_value")
        self.status_bar.addPermanentWidget(self.lbl_perf)
        self.setStatusBar(self.status_bar)

    def _build_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._act_save_ckpt = QAction("Save Checkpoint…", self)
        self._act_save_ckpt.triggered.connect(self._save_checkpoint)
        self._act_load_ckpt = QAction("Load Checkpoint…", self)
        self._act_load_ckpt.triggered.connect(self._load_checkpoint)
        file_menu.addAction(self._act_save_ckpt)
        file_menu.addAction(self._act_load_ckpt)
        file_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # View
        view_menu = mb.addMenu("&View")
        act_reset = QAction("Reset Camera", self)
        act_reset.triggered.connect(self.viz_panel._reset_camera)
        view_menu.addAction(act_reset)

        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("Theme")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        self._act_dark = QAction("Dark", self, checkable=True)
        self._act_light = QAction("Light", self, checkable=True)
        self._act_dark.setChecked(current_theme() == "dark")
        self._act_light.setChecked(current_theme() == "light")
        self._act_dark.triggered.connect(lambda: self._apply_theme("dark"))
        self._act_light.triggered.connect(lambda: self._apply_theme("light"))
        theme_group.addAction(self._act_dark)
        theme_group.addAction(self._act_light)
        theme_menu.addAction(self._act_dark)
        theme_menu.addAction(self._act_light)

        # Help
        help_menu = mb.addMenu("&Help")
        act_about = QAction("About…", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)
        tb.addAction("▶ Run",  self.sim_panel.btn_run.click)
        tb.addAction("■ Stop", self.sim_panel.btn_stop.click)
        tb.addSeparator()
        tb.addAction("Save Checkpoint", self._save_checkpoint)

    def _connect_signals(self):
        self.builder_panel.system_built.connect(self._on_system_built)
        self.sim_panel.run_requested.connect(self._on_run_requested)
        self.sim_panel.stop_requested.connect(self._on_stop_requested)

    # ── Slots ─────────────────────────────────────────────────────────
    @pyqtSlot(object)
    def _on_system_built(self, state: SimulationState) -> None:
        self._state = state
        self.viz_panel.set_system(state.species, state.box)
        self.viz_panel.on_frame_ready(state.positions, state.velocities, 0)
        self.analysis_panel.clear()
        # Tell the analysis panel which element so it can show the right reference
        element = state.species[0] if state.species else "Ar"
        self.analysis_panel.set_element(element)
        self.sim_panel.set_element(element)
        log.info("System ready: %d atoms, box %.2f σ", state.n_atoms, state.box[0])
        self.status_bar.showMessage(
            f"System: {state.n_atoms} atoms  |  Box: {state.box[0]:.2f} σ  |  "
            f"Press ▶ Run to start simulation."
        )

    @pyqtSlot(dict)
    def _on_run_requested(self, params: dict) -> None:
        if self._state is None:
            QMessageBox.warning(self, "No System", "Build a system first (System tab).")
            self.sim_panel.on_finished()
            return

        # Apply parallelism settings
        n_cores = params.get("n_cores", 1)
        try:
            import numba
            numba.set_num_threads(n_cores)
        except Exception:
            pass
        os.environ["OMP_NUM_THREADS"]   = str(n_cores)
        os.environ["MKL_NUM_THREADS"]   = str(n_cores)
        os.environ["OPENBLAS_NUM_THREADS"] = str(n_cores)
        log.info("Parallelism: %d CPU core(s), GPU=%s", n_cores, params.get("use_gpu", False))

        # Resolve hardware backend from GUI checkboxes
        use_gpu  = params.get("use_gpu", False)
        lj_back  = "gpu"          if use_gpu else "cpu_parallel"
        eam_back = "gpu"          if use_gpu else "cpu"

        # Build force field
        if params["forcefield"] == "Lennard-Jones":
            ff = LJForcefield(
                epsilon=params["epsilon"],
                sigma=params["sigma"],
                r_cut=params["r_cut"],
                force_backend=lj_back,
            )
        elif params["forcefield"] == "EAM (Cu)":
            ff = EAMForcefield("Cu_u3.eam", element="Cu", backend=eam_back)
        else:
            ff = MorseForcefield()

        # Build integrator
        if params["integrator"] == "Leapfrog":
            integrator = LeapfrogIntegrator()
        else:
            integrator = VelocityVerletIntegrator()

        # Build ensemble
        ens_name = params["ensemble"]
        if ens_name == "NVE":
            ensemble = NVEEnsemble(integrator)
        else:
            thermo_name = params["thermostat"]
            elem = self._state.species[0]
            eps_J = ELEMENTS.get(elem, ELEMENTS["Ar"]).epsilon_J
            T_red = K_to_reduced(params["T_target_K"], eps_J)

            if thermo_name == "Nosé-Hoover":
                thermo = NoseHooverThermostat(T_target=T_red)
            elif thermo_name == "Velocity Rescale":
                thermo = VelocityRescaleThermostat(T_target=T_red)
            else:
                thermo = BerendsenThermostat(T_target=T_red, tau=params["tau_T"])

            if ens_name == "NPT":
                ensemble = NPTEnsemble(integrator, thermo)
            else:
                ensemble = NVTEnsemble(integrator, thermo)

        # For EAM use the potential's own cutoff (in reduced units) + skin;
        # for LJ/Morse use the panel value.
        if hasattr(ff, "r_cut_reduced"):
            r_cut_sim = ff.r_cut_reduced + 0.3   # 0.3σ skin in reduced units
        else:
            r_cut_sim = params["r_cut"]

        engine = SimulationEngine(
            state=self._state,
            forcefield=ff,
            ensemble=ensemble,
            dt=params["dt"],
            r_cut=r_cut_sim,
        )

        # Open output files
        self._open_output_files()

        # Start worker thread
        self._worker = SimulationWorker(
            engine=engine,
            n_steps=params["n_steps"],
            record_every=params["record_every"],
        )
        sig = self._worker.signals
        sig.frame_ready.connect(self.viz_panel.on_frame_ready)
        sig.thermo_update.connect(self.analysis_panel.update_thermo)
        sig.thermo_update.connect(self.sim_panel.update_thermo)
        sig.thermo_update.connect(self._write_output)
        sig.rdf_ready.connect(self.analysis_panel.update_rdf)
        sig.msd_update.connect(self.analysis_panel.update_msd)
        sig.density_profile_ready.connect(self.analysis_panel.update_density_profile)
        sig.progress.connect(self._on_progress)
        sig.finished.connect(self._on_sim_finished)
        sig.error.connect(self._on_sim_error)

        self._worker.start()
        log.info("Simulation started: %s, %d steps, dt=%.4f  [backend: %s]",
                 ens_name, params["n_steps"], params["dt"], ff.describe().get("backend","?"))

    @pyqtSlot()
    def _on_stop_requested(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.request_stop()
            log.info("Stop requested.")

    @pyqtSlot(int, int, float)
    def _on_progress(self, step: int, total: int, elapsed: float) -> None:
        self.sim_panel.update_progress(step, total, elapsed)
        rate = step / max(elapsed, 1e-6)
        self.lbl_perf.setText(f"  {rate:.0f} steps/s  |  {step:,}/{total:,} steps")

    @pyqtSlot()
    def _on_sim_finished(self) -> None:
        elapsed = self._worker._elapsed_total if self._worker else 0.0
        self.sim_panel.on_finished(total_elapsed=elapsed)
        self._close_output_files()
        log.info("Simulation finished in %.2f s.", elapsed)
        self.status_bar.showMessage(
            f"Simulation complete  —  total time: {_fmt_time_s(elapsed)}"
        )

    @pyqtSlot(str)
    def _on_sim_error(self, tb: str) -> None:
        self.sim_panel.on_finished()
        self._close_output_files()
        QMessageBox.critical(self, "Simulation Error", tb[:1000])

    @pyqtSlot(dict)
    def _write_output(self, thermo: dict) -> None:
        if self._csv_writer:
            try:
                self._csv_writer.write(self._state)
            except Exception:
                pass
        if self._xyz_fh and self._state:
            try:
                write_xyz_frame(self._xyz_fh, self._state)
            except Exception:
                pass

    # ── Output file management ────────────────────────────────────────
    def _open_output_files(self) -> None:
        run_dir = OUTPUT_DIR / f"run_{self._state.step:06d}"
        run_dir.mkdir(parents=True, exist_ok=True)
        if self._save_csv:
            self._csv_writer = ThermoCSVWriter(run_dir / "thermo.csv")
        if self._save_xyz:
            self._xyz_fh = open(run_dir / "trajectory.xyz", "w")
        log.info("Output → %s", run_dir)

    def _close_output_files(self) -> None:
        if self._csv_writer:
            self._csv_writer.close()
            self._csv_writer = None
        if self._xyz_fh:
            self._xyz_fh.close()
            self._xyz_fh = None

    # ── Checkpoint ────────────────────────────────────────────────────
    def _save_checkpoint(self) -> None:
        if self._state is None:
            QMessageBox.information(self, "No State", "Nothing to save yet.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Checkpoint", str(OUTPUT_DIR / "checkpoint.npz"), "NumPy (*.npz)"
        )
        if path:
            save_checkpoint(self._state, path)
            log.info("Checkpoint saved: %s", path)

    def _load_checkpoint(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Checkpoint", str(OUTPUT_DIR), "NumPy (*.npz)"
        )
        if path:
            self._state = load_checkpoint(path)
            self.viz_panel.set_system(self._state.species, self._state.box)
            self.viz_panel.on_frame_ready(
                self._state.positions, self._state.velocities, self._state.step
            )
            log.info("Checkpoint loaded: %s, step %d", path, self._state.step)

    def _apply_theme(self, theme: str) -> None:
        apply_theme(QApplication.instance(), theme)
        self._act_dark.setChecked(theme == "dark")
        self._act_light.setChecked(theme == "light")
        log.info("Theme changed to: %s", theme)

    def _show_about(self) -> None:
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>"
            "<b>Author:</b> Abdul Haseeb Shakir<br>"
            "© 2026 Abdul Haseeb Shakir. All Rights Reserved.<br><br>"
            "A parallel molecular dynamics simulation platform.<br><br>"
            "Built with Python · PyQt6 · Numba · PyVista<br>"
            "GPU acceleration via CuPy (RTX 4060 Ti)<br><br>"
            "Physics engine: Lennard-Jones, Morse, Tersoff<br>"
            "Ensembles: NVE · NVT (Berendsen / Nosé-Hoover) · NPT<br><br>"
            "<i>Do not use without written permission from Abdul Haseeb Shakir.</i>",
        )

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.request_stop()
            self._worker.wait(3000)
        self._close_output_files()
        super().closeEvent(event)
