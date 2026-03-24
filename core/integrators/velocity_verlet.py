"""
Velocity Verlet integrator.

  x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt²
  v(t+dt) = v(t) + 0.5*[a(t) + a(t+dt)]*dt
"""
import numpy as np
from core.state import SimulationState
from core.forcefields.base import AbstractForcefield
from core.neighbor.cell_list import NeighborList
from .base import AbstractIntegrator


class VelocityVerletIntegrator(AbstractIntegrator):
    name = "Velocity Verlet"

    def step(
        self,
        state: SimulationState,
        forcefield: AbstractForcefield,
        neighbor_list: NeighborList,
        dt: float,
    ) -> None:
        inv_mass = 1.0 / state.masses[:, np.newaxis]   # (N, 1)

        # Half-step velocity
        state.velocities += 0.5 * dt * state.forces * inv_mass

        # Full-step position
        state.positions += dt * state.velocities

        # Apply periodic boundary conditions
        state.positions %= state.box

        # Recompute forces at new positions
        forcefield.compute(state, neighbor_list)

        # Second half-step velocity
        state.velocities += 0.5 * dt * state.forces * inv_mass

        # Update kinetic energy
        v2 = np.sum(state.velocities ** 2 * state.masses[:, np.newaxis])
        state.ke = 0.5 * v2

        state.step += 1
