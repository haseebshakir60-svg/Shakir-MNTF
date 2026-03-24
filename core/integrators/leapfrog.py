"""Leapfrog integrator (equivalent to Velocity Verlet, different phasing)."""
import numpy as np
from core.state import SimulationState
from core.forcefields.base import AbstractForcefield
from core.neighbor.cell_list import NeighborList
from .base import AbstractIntegrator


class LeapfrogIntegrator(AbstractIntegrator):
    name = "Leapfrog"

    def step(
        self,
        state: SimulationState,
        forcefield: AbstractForcefield,
        neighbor_list: NeighborList,
        dt: float,
    ) -> None:
        inv_mass = 1.0 / state.masses[:, np.newaxis]

        # Velocity at half-step
        state.velocities += dt * state.forces * inv_mass

        # Position at full step
        state.positions  += dt * state.velocities
        state.positions  %= state.box

        # New forces
        forcefield.compute(state, neighbor_list)

        # Estimate full-step velocity for thermodynamics
        v_full = state.velocities + 0.5 * dt * state.forces * inv_mass
        v2 = np.sum(v_full ** 2 * state.masses[:, np.newaxis])
        state.ke = 0.5 * v2

        state.step += 1
