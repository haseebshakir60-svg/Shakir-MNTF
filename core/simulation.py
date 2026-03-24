"""
SimulationEngine — master orchestrator for the MD run.

Usage
-----
    engine = SimulationEngine(state, forcefield, ensemble, dt=0.005)
    for snapshot in engine.run(n_steps=10_000, record_every=100):
        # snapshot is a SimulationState copy emitted every record_every steps
        print(snapshot.step, snapshot.temperature)
"""
from __future__ import annotations
import logging
import time
from typing import Generator, Callable

import numpy as np

from core.state import SimulationState
from core.forcefields.base import AbstractForcefield
from core.neighbor.cell_list import NeighborList
from core.observables.thermodynamics import get_thermo_dict

log = logging.getLogger(__name__)


class SimulationEngine:
    """
    Drives the MD time loop.

    Parameters
    ----------
    state        : SimulationState   Initial system state (modified in-place)
    forcefield   : AbstractForcefield
    ensemble     : NVEEnsemble | NVTEnsemble | NPTEnsemble
    dt           : float             Time step (reduced units)
    r_cut        : float             Force cutoff radius (reduced units)
    r_skin       : float             Verlet skin radius (reduced units)
    """

    def __init__(
        self,
        state:       SimulationState,
        forcefield:  AbstractForcefield,
        ensemble,
        dt:          float = 0.005,
        r_cut:       float = 2.5,
        r_skin:      float = 0.3,
    ):
        self.state        = state
        self.forcefield   = forcefield
        self.ensemble     = ensemble
        self.dt           = dt
        self._neighbor    = NeighborList(r_cut=r_cut, r_skin=r_skin)
        self._running     = False
        self._stop_flag   = False

        # Callbacks
        self.on_step:   Callable | None = None   # called every step
        self.on_record: Callable | None = None   # called every record_every steps

        # Initial force calculation
        self.forcefield.compute(self.state, self._neighbor)
        v2 = np.sum(self.state.velocities ** 2 * self.state.masses[:, np.newaxis])
        self.state.ke = 0.5 * float(v2)

    def stop(self) -> None:
        self._stop_flag = True

    def run(
        self,
        n_steps:      int = 10_000,
        record_every: int = 100,
    ) -> Generator[SimulationState, None, None]:
        """
        Run for `n_steps` and yield a copy of the state every `record_every` steps.

        This is a generator so it can be consumed step-by-step in a QThread.
        """
        self._running    = True
        self._stop_flag  = False

        t_start = time.perf_counter()

        for _ in range(n_steps):
            if self._stop_flag:
                log.info("Simulation stopped by user at step %d", self.state.step)
                break

            self.ensemble.step(
                self.state, self.forcefield, self._neighbor, self.dt
            )

            if self.on_step:
                self.on_step(self.state)

            if self.state.step % record_every == 0:
                snapshot = self.state.copy()
                if self.on_record:
                    self.on_record(snapshot)
                yield snapshot

        elapsed = time.perf_counter() - t_start
        log.info(
            "Simulation finished: %d steps in %.2f s (%.0f steps/s)",
            self.state.step, elapsed, self.state.step / max(elapsed, 1e-9),
        )
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
