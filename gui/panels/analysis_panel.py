"""
Analysis Panel — live plots of thermodynamic quantities.

Tabs: Energy | Temperature | Pressure | RDF | MSD | Density
"""
from __future__ import annotations
from collections import deque

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


_DARK = {
    "figure.facecolor":  "#12131a",
    "axes.facecolor":    "#1a1d2e",
    "axes.edgecolor":    "#2e3258",
    "axes.labelcolor":   "#9098c8",
    "xtick.color":       "#606888",
    "ytick.color":       "#606888",
    "text.color":        "#c0c8e8",
    "grid.color":        "#20243a",
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "lines.linewidth":   1.5,
}


def _make_canvas(n_rows: int = 1, figsize=(5, 3)) -> tuple[FigureCanvas, list]:
    with plt.rc_context(_DARK):
        fig = Figure(figsize=figsize, tight_layout=True)
        axes = [fig.add_subplot(n_rows, 1, i + 1) for i in range(n_rows)]
    return FigureCanvas(fig), axes


def _info_label(text: str = "—") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    lbl.setObjectName("label_value")
    return lbl


class AnalysisPanel(QWidget):
    """Tabbed analysis panel with live-updating plots."""

    MAX_POINTS = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[str, deque] = {k: deque(maxlen=self.MAX_POINTS) for k in
            ["step", "ke", "pe", "te", "temperature", "pressure", "density"]}
        self._element = "Ar"    # current element — set by main window
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)

        self.tabs = QTabWidget()
        lay.addWidget(self.tabs)

        self._build_energy_tab()
        self._build_temperature_tab()
        self._build_pressure_tab()
        self._build_rdf_tab()
        self._build_msd_tab()
        self._build_density_tab()

    def _build_energy_tab(self):
        canvas, axes = _make_canvas(1)
        self._canvas_e = canvas
        ax = axes[0]
        ax.set_title("Energy", pad=4)
        ax.set_xlabel("Step"); ax.set_ylabel("Energy (reduced)"); ax.grid(True)
        self._line_ke, = ax.plot([], [], color="#00e5ff", label="KE")
        self._line_pe, = ax.plot([], [], color="#ff4444", label="PE")
        self._line_te, = ax.plot([], [], color="#80ff80", label="TE")
        ax.legend(facecolor="#1a1d2e", edgecolor="#2e3258", labelcolor="#c0c8e8")
        self._ax_e = ax
        w = QWidget(); QVBoxLayout(w).addWidget(canvas)
        self.tabs.addTab(w, "Energy")

    def _build_temperature_tab(self):
        canvas, axes = _make_canvas(1)
        self._canvas_T = canvas
        ax = axes[0]
        ax.set_title("Temperature", pad=4)
        ax.set_xlabel("Step"); ax.set_ylabel("T (reduced)"); ax.grid(True)
        self._line_T, = ax.plot([], [], color="#ffaa00")
        self._ax_T = ax
        w = QWidget(); QVBoxLayout(w).addWidget(canvas)
        self.tabs.addTab(w, "Temperature")

    def _build_pressure_tab(self):
        canvas, axes = _make_canvas(1)
        self._canvas_P = canvas
        ax = axes[0]
        ax.set_title("Pressure", pad=4)
        ax.set_xlabel("Step"); ax.set_ylabel("P (reduced)"); ax.grid(True)
        self._line_P, = ax.plot([], [], color="#c070ff")
        self._ax_P = ax
        w = QWidget(); QVBoxLayout(w).addWidget(canvas)
        self.tabs.addTab(w, "Pressure")

    def _build_rdf_tab(self):
        canvas, axes = _make_canvas(1)
        self._canvas_rdf = canvas
        ax = axes[0]
        ax.set_title("Radial Distribution Function g(r)", pad=4)
        ax.set_xlabel("r (σ)"); ax.set_ylabel("g(r)"); ax.grid(True)
        self._line_rdf, = ax.plot([], [], color="#40e0d0")
        self._ax_rdf = ax
        w = QWidget(); QVBoxLayout(w).addWidget(canvas)
        self.tabs.addTab(w, "RDF")

    def _build_msd_tab(self):
        canvas, axes = _make_canvas(1)
        self._canvas_msd = canvas
        ax = axes[0]
        ax.set_title("Mean Squared Displacement", pad=4)
        ax.set_xlabel("Step"); ax.set_ylabel("MSD (σ²)"); ax.grid(True)
        self._line_msd, = ax.plot([], [], color="#ff80c0")
        self._ax_msd = ax
        w = QWidget(); QVBoxLayout(w).addWidget(canvas)
        self.tabs.addTab(w, "MSD")

    def _build_density_tab(self):
        """
        Density tab — three sections:
          1. ρ*(t) time series with reference line
          2. z-density profile histogram
          3. Comparison table: simulated vs bulk reference
        """
        w = QWidget()
        vlay = QVBoxLayout(w)
        vlay.setContentsMargins(4, 4, 4, 4)
        vlay.setSpacing(6)

        # ── Plot area (top half) ──────────────────────────────────
        canvas, axes = _make_canvas(2, figsize=(5, 4))
        self._canvas_dens = canvas

        # Top subplot: ρ*(t) time series
        self._ax_rho_t = axes[0]
        self._ax_rho_t.set_title("Instantaneous Density ρ*(t)", pad=4)
        self._ax_rho_t.set_xlabel("Step")
        self._ax_rho_t.set_ylabel("ρ* (reduced)")
        self._ax_rho_t.grid(True)
        self._line_rho, = self._ax_rho_t.plot([], [], color="#40c8ff", label="Simulated ρ*")
        # Reference line (horizontal dashed) — added when element is known
        self._ref_hline = self._ax_rho_t.axhline(
            y=0, color="#ff9900", linestyle="--", linewidth=1.2, alpha=0.8, label="Bulk reference"
        )
        self._ax_rho_t.legend(facecolor="#1a1d2e", edgecolor="#2e3258",
                               labelcolor="#c0c8e8", fontsize=8)

        # Bottom subplot: z-density profile
        self._ax_rho_z = axes[1]
        self._ax_rho_z.set_title("Density Profile ρ(z)", pad=4)
        self._ax_rho_z.set_xlabel("z (σ)")
        self._ax_rho_z.set_ylabel("ρ (atoms/σ³)")
        self._ax_rho_z.grid(True)
        self._bar_rho_z = None   # created on first update

        vlay.addWidget(canvas, stretch=2)

        # ── Comparison table (bottom half) ───────────────────────
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background:#16182a; border:1px solid #2a2e50; border-radius:5px; }"
        )
        grid = QGridLayout(frame)
        grid.setContentsMargins(10, 8, 10, 8)
        grid.setSpacing(6)

        def _hdr(txt):
            l = QLabel(txt)
            l.setStyleSheet("color:#7080c0; font-weight:bold; font-size:9pt;")
            return l

        def _val(txt="—"):
            l = QLabel(txt)
            l.setStyleSheet("color:#c0d8ff; font-size:9pt;")
            l.setAlignment(Qt.AlignmentFlag.AlignRight)
            return l

        grid.addWidget(_hdr("Property"),          0, 0)
        grid.addWidget(_hdr("Simulated"),         0, 1)
        grid.addWidget(_hdr("Bulk Reference"),    0, 2)
        grid.addWidget(_hdr("Deviation"),         0, 3)

        # Row 1: reduced density
        grid.addWidget(QLabel("ρ* (reduced)"),    1, 0)
        self._lbl_rho_sim  = _val()
        self._lbl_rho_ref  = _val()
        self._lbl_rho_dev  = _val()
        grid.addWidget(self._lbl_rho_sim,         1, 1)
        grid.addWidget(self._lbl_rho_ref,         1, 2)
        grid.addWidget(self._lbl_rho_dev,         1, 3)

        # Row 2: physical density g/cm³
        grid.addWidget(QLabel("ρ (g/cm³)"),       2, 0)
        self._lbl_phys_sim = _val()
        self._lbl_phys_ref = _val()
        self._lbl_phys_dev = _val()
        grid.addWidget(self._lbl_phys_sim,        2, 1)
        grid.addWidget(self._lbl_phys_ref,        2, 2)
        grid.addWidget(self._lbl_phys_dev,        2, 3)

        # Row 3: element + state label
        grid.addWidget(QLabel("Reference state"), 3, 0)
        self._lbl_ref_state = QLabel("—")
        self._lbl_ref_state.setStyleSheet("color:#80a0c0; font-size:9pt;")
        grid.addWidget(self._lbl_ref_state,       3, 1, 1, 3)

        # Row 4: validation badge
        self._lbl_badge = QLabel("")
        self._lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_badge.setStyleSheet("font-size:10pt; font-weight:bold; padding:4px;")
        grid.addWidget(self._lbl_badge,           4, 0, 1, 4)

        vlay.addWidget(frame, stretch=1)
        self.tabs.addTab(w, "Density")

        # Initialise reference values immediately
        self._refresh_reference_labels()

    # ── Public interface ──────────────────────────────────────────────────

    def set_element(self, element: str) -> None:
        """Called by main window when a new system is built."""
        self._element = element
        self._refresh_reference_labels()

    def update_thermo(self, data: dict) -> None:
        for key in ["step", "ke", "pe", "te", "temperature", "pressure", "density"]:
            if key in data:
                self._data[key].append(data[key])

        step = list(self._data["step"])

        # Energy
        self._line_ke.set_data(step, list(self._data["ke"]))
        self._line_pe.set_data(step, list(self._data["pe"]))
        self._line_te.set_data(step, list(self._data["te"]))
        self._ax_e.relim(); self._ax_e.autoscale_view()
        self._canvas_e.draw_idle()

        # Temperature
        self._line_T.set_data(step, list(self._data["temperature"]))
        self._ax_T.relim(); self._ax_T.autoscale_view()
        self._canvas_T.draw_idle()

        # Pressure
        self._line_P.set_data(step, list(self._data["pressure"]))
        self._ax_P.relim(); self._ax_P.autoscale_view()
        self._canvas_P.draw_idle()

        # Density ρ*(t) time series
        if "density" in data:
            self._line_rho.set_data(step, list(self._data["density"]))
            self._ax_rho_t.relim(); self._ax_rho_t.autoscale_view()
            self._canvas_dens.draw_idle()
            self._update_comparison_table(float(data["density"]))

    def update_rdf(self, r: np.ndarray, g: np.ndarray) -> None:
        self._line_rdf.set_data(r, g)
        self._ax_rdf.relim(); self._ax_rdf.autoscale_view()
        self._canvas_rdf.draw_idle()

    def update_msd(self, steps: np.ndarray, msd: np.ndarray) -> None:
        self._line_msd.set_data(steps, msd)
        self._ax_msd.relim(); self._ax_msd.autoscale_view()
        self._canvas_msd.draw_idle()

    def update_density_profile(self, z_mid: np.ndarray, rho_z: np.ndarray, mean_rho: float) -> None:
        """Update the z-density profile bar chart."""
        self._ax_rho_z.clear()
        self._ax_rho_z.set_title("Density Profile ρ(z)", pad=4)
        self._ax_rho_z.set_xlabel("z (σ)")
        self._ax_rho_z.set_ylabel("ρ (atoms/σ³)")
        self._ax_rho_z.grid(True)
        dz = (z_mid[1] - z_mid[0]) if len(z_mid) > 1 else 1.0
        self._ax_rho_z.bar(z_mid, rho_z, width=dz * 0.9,
                            color="#4080ff", alpha=0.7, edgecolor="none")
        self._ax_rho_z.axhline(mean_rho, color="#ff9900", linestyle="--",
                                linewidth=1.0, label=f"mean ρ* = {mean_rho:.3f}")
        self._ax_rho_z.legend(facecolor="#1a1d2e", edgecolor="#2e3258",
                               labelcolor="#c0c8e8", fontsize=7)
        self._canvas_dens.draw_idle()

    def clear(self) -> None:
        for d in self._data.values():
            d.clear()

    # ── Internal helpers ──────────────────────────────────────────────────

    def _refresh_reference_labels(self) -> None:
        """Update the reference column from element_data bulk values."""
        from builder.element_data import ELEMENT_DATA
        elem = ELEMENT_DATA.get(self._element)
        if elem is None:
            return
        rho_ref = elem.bulk_density_reduced()
        self._ref_hline.set_ydata([rho_ref, rho_ref])
        self._lbl_rho_ref.setText(f"{rho_ref:.4f}")
        self._lbl_phys_ref.setText(f"{elem.bulk_density_gcc:.4f}")
        self._lbl_ref_state.setText(
            f"{elem.name} ({elem.symbol})  —  {elem.bulk_state} at {elem.bulk_T_K:.1f} K"
        )
        self._canvas_dens.draw_idle()

    def _update_comparison_table(self, rho_sim: float) -> None:
        from builder.element_data import ELEMENT_DATA
        elem = ELEMENT_DATA.get(self._element)
        if elem is None:
            return

        rho_ref = elem.bulk_density_reduced()

        # Convert simulated ρ* back to g/cm³
        sigma_cm = elem.sigma_nm * 1e-7
        NA       = 6.02214076e23
        phys_sim = rho_sim * elem.mass_u / (sigma_cm ** 3 * NA)

        dev_pct = 100.0 * (rho_sim - rho_ref) / rho_ref if rho_ref > 0 else 0.0

        self._lbl_rho_sim.setText(f"{rho_sim:.4f}")
        self._lbl_phys_sim.setText(f"{phys_sim:.4f}")
        self._lbl_rho_dev.setText(f"{dev_pct:+.1f}%")
        self._lbl_phys_dev.setText(f"{100*(phys_sim - elem.bulk_density_gcc)/elem.bulk_density_gcc:+.1f}%")

        # Colour-coded validation badge
        abs_dev = abs(dev_pct)
        if abs_dev < 5.0:
            colour, mark = "#40ff80", "✔  Density within 5% of bulk reference — system identity confirmed"
        elif abs_dev < 15.0:
            colour, mark = "#ffcc00", f"⚠  Density within {abs_dev:.0f}% of bulk reference"
        else:
            colour, mark = "#ff5050", f"✗  Density deviates {abs_dev:.0f}% from bulk reference"

        self._lbl_badge.setText(mark)
        self._lbl_badge.setStyleSheet(
            f"font-size:10pt; font-weight:bold; padding:4px; color:{colour};"
        )
        self._lbl_rho_dev.setStyleSheet(
            f"color:{'#40ff80' if abs_dev<5 else '#ffcc00' if abs_dev<15 else '#ff5050'};"
            "font-size:9pt;"
        )
