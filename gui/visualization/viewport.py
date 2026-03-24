"""
3-D Molecular Visualization Viewport.

Uses PyVista's QtInteractor for hardware-accelerated OpenGL rendering.
Falls back to a matplotlib 3D scatter if PyVista is not installed.

Atom rendering:
  - Sphere glyphs, sized by covalent radius
  - Colored by element (CPK) or by speed (plasma colormap)
  - Simulation box outline drawn as white wireframe
"""
from __future__ import annotations
import logging
import numpy as np

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

log = logging.getLogger(__name__)

# Try PyVista first, fall back to matplotlib
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    _HAS_PYVISTA = True
except ImportError:
    _HAS_PYVISTA = False
    log.warning("PyVista not found — using matplotlib 3-D fallback.")

from builder.element_data import CPK_COLORS


def _element_colors(species: list[str]) -> np.ndarray:
    """Map element symbols → float RGB array (N, 3) in [0, 1]."""
    colors = np.zeros((len(species), 3))
    for i, s in enumerate(species):
        rgb = CPK_COLORS.get(s, (200, 200, 200))
        colors[i] = [c / 255.0 for c in rgb]
    return colors


class Viewport3D(QWidget):
    """Hardware-accelerated 3-D atom viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._species: list[str] = []
        self._box    = np.ones(3) * 10.0
        self._n_atoms = 0
        self._color_mode = "element"  # "element" | "speed"

        if _HAS_PYVISTA:
            self._init_pyvista()
        else:
            self._init_matplotlib()

    # ── PyVista path ─────────────────────────────────────────────────
    def _init_pyvista(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plotter = QtInteractor(self)
        self._plotter.set_background("#0d0e18")
        layout.addWidget(self._plotter.interactor)

        self._cloud = None   # pv.PolyData — set on first update
        self._mesh_actor = None
        self._box_actor  = None

    def _ensure_pyvista_actors(self, positions: np.ndarray):
        """Create or recreate PyVista actors when N changes."""
        if self._cloud is not None and len(self._cloud.points) == len(positions):
            return  # reuse existing

        self._plotter.clear_actors()

        self._cloud = pv.PolyData(positions.astype(np.float32))
        self._cloud["colors"] = _element_colors(self._species)

        sphere_src = pv.Sphere(radius=0.3, theta_resolution=12, phi_resolution=8)
        glyphs = self._cloud.glyph(geom=sphere_src, orient=False, scale=False)
        self._mesh_actor = self._plotter.add_mesh(
            glyphs,
            scalars="colors",
            rgb=True,
            smooth_shading=True,
            show_scalar_bar=False,
        )

        # Box outline
        box = pv.Box(bounds=(0, self._box[0], 0, self._box[1], 0, self._box[2]))
        edges = box.extract_feature_edges()
        self._box_actor = self._plotter.add_mesh(
            edges, color="white", line_width=1, opacity=0.3
        )
        self._plotter.reset_camera()

    def update_positions(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        step: int,
    ) -> None:
        if not _HAS_PYVISTA:
            self._update_matplotlib(positions)
            return

        self._ensure_pyvista_actors(positions)

        # Update point positions
        self._cloud.points = positions.astype(np.float32)

        if self._color_mode == "speed":
            speeds = np.linalg.norm(velocities, axis=1)
            speeds_norm = (speeds - speeds.min()) / (speeds.ptp() + 1e-10)
            cmap = _plasma_colors(speeds_norm)
            self._cloud["colors"] = cmap

        # Re-glyph
        sphere_src = pv.Sphere(radius=0.3, theta_resolution=12, phi_resolution=8)
        glyphs = self._cloud.glyph(geom=sphere_src, orient=False, scale=False)
        self._plotter.remove_actor(self._mesh_actor)
        self._mesh_actor = self._plotter.add_mesh(
            glyphs, scalars="colors", rgb=True,
            smooth_shading=True, show_scalar_bar=False,
        )
        self._plotter.render()

    def set_system(self, species: list[str], box: np.ndarray) -> None:
        self._species = species
        self._box     = box
        self._cloud   = None   # force actor rebuild

    def set_color_mode(self, mode: str) -> None:
        self._color_mode = mode

    # ── Matplotlib fallback ───────────────────────────────────────────
    def _init_matplotlib(self):
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        from mpl_toolkits.mplot3d import Axes3D

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        fig = Figure(facecolor="#0d0e18")
        self._ax3d = fig.add_subplot(111, projection="3d")
        self._ax3d.set_facecolor("#12131a")
        self._ax3d.tick_params(colors="#606888")
        self._scatter = None

        canvas = FigureCanvasQTAgg(fig)
        layout.addWidget(canvas)
        self._mpl_canvas = canvas

    def _update_matplotlib(self, positions: np.ndarray):
        if self._scatter:
            self._scatter.remove()
        colors = _element_colors(self._species)
        self._scatter = self._ax3d.scatter(
            positions[:, 0], positions[:, 1], positions[:, 2],
            c=colors, s=20, depthshade=True,
        )
        self._ax3d.set_xlim(0, self._box[0])
        self._ax3d.set_ylim(0, self._box[1])
        self._ax3d.set_zlim(0, self._box[2])
        self._mpl_canvas.draw_idle()


def _plasma_colors(t: np.ndarray) -> np.ndarray:
    """Map scalar 0-1 → plasma colormap RGB float array."""
    import matplotlib.cm as cm
    rgba = cm.plasma(t)
    return rgba[:, :3]
