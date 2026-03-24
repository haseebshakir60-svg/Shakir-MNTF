"""
SimulationWorker — runs SimulationEngine in a background QThread.

Emits Qt signals so the GUI stays responsive during simulation.
Also computes RDF and MSD periodically and emits them for the analysis panel.
"""
from __future__ import annotations
import time
import traceback
import logging

from PyQt6.QtCore import QThread
import numpy as np

from core.simulation import SimulationEngine
from core.observables.thermodynamics import get_thermo_dict
from core.observables.rdf import compute_rdf
from core.observables.msd import MSDTracker
from core.observables.density_profile import compute_density_profile
from signals.sim_signals import SimulationSignals

log = logging.getLogger(__name__)


class SimulationWorker(QThread):
    """
    Background thread that drives the MD engine and emits progress signals.

    Parameters
    ----------
    engine        : SimulationEngine
    n_steps       : total steps to run
    record_every  : emit thermo + frame every N steps
    rdf_every     : compute and emit RDF every N steps (default 10× record_every)
    """

    def __init__(
        self,
        engine:       SimulationEngine,
        n_steps:      int = 10_000,
        record_every: int = 100,
        rdf_every:    int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.engine       = engine
        self.n_steps      = n_steps
        self.record_every = record_every
        self.rdf_every    = rdf_every if rdf_every is not None else max(record_every * 10, 500)
        self.signals        = SimulationSignals()
        self._t_start       = 0.0
        self._elapsed_total = 0.0

    def request_stop(self) -> None:
        self.engine.stop()

    def run(self) -> None:
        """Called by QThread.start() — executes in background thread."""
        self._t_start = time.perf_counter()

        # Initialise MSD tracker with starting positions
        state0   = self.engine.state
        msd_tracker = MSDTracker(state0.positions.copy(), state0.box.copy())
        _rdf_counter = 0

        try:
            total = self.n_steps

            for snapshot in self.engine.run(self.n_steps, self.record_every):
                elapsed = time.perf_counter() - self._t_start

                # ── 3-D visualization frame ───────────────────────
                self.signals.frame_ready.emit(
                    snapshot.positions.copy(),
                    snapshot.velocities.copy(),
                    snapshot.step,
                )

                # ── Thermodynamics ────────────────────────────────
                self.signals.thermo_update.emit(get_thermo_dict(snapshot))

                # ── MSD (every record_every steps) ────────────────
                msd = msd_tracker.update(snapshot.positions, snapshot.step)
                steps_arr, msd_arr = msd_tracker.data
                self.signals.msd_update.emit(
                    steps_arr.copy(),
                    msd_arr.copy(),
                )

                # ── RDF + density profile (every rdf_every steps) ─
                _rdf_counter += self.record_every
                if _rdf_counter >= self.rdf_every:
                    _rdf_counter = 0
                    try:
                        r, g = compute_rdf(
                            snapshot.positions,
                            snapshot.box,
                            n_bins=200,
                        )
                        self.signals.rdf_ready.emit(r.copy(), g.copy())
                    except Exception as exc:
                        log.debug("RDF computation skipped: %s", exc)

                    try:
                        z_mid, rho_z = compute_density_profile(
                            snapshot.positions, snapshot.box, n_bins=50
                        )
                        mean_rho = float(snapshot.n_atoms / snapshot.volume)
                        self.signals.density_profile_ready.emit(
                            z_mid.copy(), rho_z.copy(), mean_rho
                        )
                    except Exception as exc:
                        log.debug("Density profile skipped: %s", exc)

                # ── Progress ──────────────────────────────────────
                self.signals.progress.emit(snapshot.step, total, elapsed)

            self._elapsed_total = time.perf_counter() - self._t_start
            self.signals.finished.emit()

        except Exception:
            tb = traceback.format_exc()
            log.error("SimulationWorker crashed:\n%s", tb)
            self.signals.error.emit(tb)
