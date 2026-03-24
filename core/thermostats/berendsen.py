"""Berendsen weak-coupling thermostat."""
import math
import numpy as np
from core.state import SimulationState
from .base import AbstractThermostat


class BerendsenThermostat(AbstractThermostat):
    """
    Berendsen thermostat: exponential relaxation to T_target.

      λ = sqrt( 1 + (dt/τ) * (T_target/T - 1) )
      v → λ * v

    Parameters
    ----------
    T_target : float   Target temperature (reduced units)
    tau      : float   Coupling time constant (reduced time units)
    """

    name = "Berendsen"

    def __init__(self, T_target: float = 1.0, tau: float = 100.0):
        self.T_target = T_target
        self.tau      = tau

    def apply(self, state: SimulationState, dt: float) -> None:
        T = state.temperature
        if T < 1e-10:
            return
        ratio = self.T_target / T
        lam   = math.sqrt(1.0 + (dt / self.tau) * (ratio - 1.0))
        state.velocities *= lam
        # update KE
        v2 = np.sum(state.velocities ** 2 * state.masses[:, np.newaxis])
        state.ke = 0.5 * v2
