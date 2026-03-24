"""
Nosé-Hoover thermostat — generates true NVT canonical ensemble.

Uses a single thermostat variable ξ (xi) with fictitious mass Q.
"""
import math
import numpy as np
from core.state import SimulationState
from .base import AbstractThermostat


class NoseHooverThermostat(AbstractThermostat):
    """
    Nosé-Hoover chain thermostat (single bath).

    Parameters
    ----------
    T_target : float   Target temperature (reduced units)
    Q        : float   Thermostat fictitious mass (default 10 * N * T)
    """

    name = "Nosé-Hoover"

    def __init__(self, T_target: float = 1.0, Q: float | None = None):
        self.T_target = T_target
        self._Q_override = Q
        self._xi  = 0.0   # thermostat variable
        self._v_xi = 0.0  # thermostat velocity

    def apply(self, state: SimulationState, dt: float) -> None:
        n   = state.n_atoms
        dof = 3 * n - 3
        Q   = self._Q_override if self._Q_override else (dof * self.T_target * 10.0)

        T = state.temperature

        # Half-step thermostat velocity
        self._v_xi += 0.5 * dt * (T - self.T_target) / Q

        # Scale atomic velocities
        scale = math.exp(-self._v_xi * dt)
        state.velocities *= scale

        # Update KE
        v2 = np.sum(state.velocities ** 2 * state.masses[:, np.newaxis])
        state.ke = 0.5 * v2

        # Second half-step thermostat
        T_new = state.temperature
        self._v_xi += 0.5 * dt * (T_new - self.T_target) / Q
        self._xi   += self._v_xi * dt
