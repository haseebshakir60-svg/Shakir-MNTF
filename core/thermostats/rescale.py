"""Instantaneous velocity rescaling thermostat."""
import math
import numpy as np
from core.state import SimulationState
from .base import AbstractThermostat


class VelocityRescaleThermostat(AbstractThermostat):
    """Direct velocity rescaling to exactly T_target every step."""

    name = "Velocity Rescale"

    def __init__(self, T_target: float = 1.0):
        self.T_target = T_target

    def apply(self, state: SimulationState, dt: float) -> None:
        T = state.temperature
        if T < 1e-10:
            return
        lam = math.sqrt(self.T_target / T)
        state.velocities *= lam
        v2 = np.sum(state.velocities ** 2 * state.masses[:, np.newaxis])
        state.ke = 0.5 * v2
