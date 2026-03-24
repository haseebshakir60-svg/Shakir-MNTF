"""NPT isothermal-isobaric ensemble — integrator + thermostat + barostat."""
import math
import numpy as np
from core.state import SimulationState
from core.integrators.base import AbstractIntegrator
from core.forcefields.base import AbstractForcefield
from core.thermostats.base import AbstractThermostat
from core.neighbor.cell_list import NeighborList


class NPTEnsemble:
    """
    NPT ensemble with Berendsen-style pressure coupling.

    Parameters
    ----------
    P_target  : float   Target pressure (reduced units)
    tau_P     : float   Barostat coupling time (reduced time units)
    compressibility : float   Isothermal compressibility (default ~1e-5 for LJ liquid)
    """

    name = "NPT"

    def __init__(
        self,
        integrator:  AbstractIntegrator,
        thermostat:  AbstractThermostat,
        P_target:    float = 1.0,
        tau_P:       float = 1000.0,
        compressibility: float = 1e-5,
    ):
        self.integrator       = integrator
        self.thermostat       = thermostat
        self.P_target         = P_target
        self.tau_P            = tau_P
        self.compressibility  = compressibility

    def step(
        self,
        state: SimulationState,
        forcefield: AbstractForcefield,
        neighbor_list: NeighborList,
        dt: float,
    ) -> None:
        self.integrator.step(state, forcefield, neighbor_list, dt)
        self.thermostat.apply(state, dt)

        # Berendsen barostat — isotropic scaling
        P = state.pressure
        mu_3 = 1.0 - self.compressibility * (dt / self.tau_P) * (self.P_target - P)
        mu   = mu_3 ** (1.0 / 3.0)

        state.positions *= mu
        state.box       *= mu
        # Rebuild neighbor list on next force call
        neighbor_list._pos_ref = None
