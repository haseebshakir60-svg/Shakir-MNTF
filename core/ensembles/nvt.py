"""NVT canonical ensemble — integrator + thermostat."""
from core.state import SimulationState
from core.integrators.base import AbstractIntegrator
from core.forcefields.base import AbstractForcefield
from core.thermostats.base import AbstractThermostat
from core.neighbor.cell_list import NeighborList


class NVTEnsemble:
    name = "NVT"

    def __init__(
        self,
        integrator:  AbstractIntegrator,
        thermostat:  AbstractThermostat,
    ):
        self.integrator = integrator
        self.thermostat = thermostat

    def step(
        self,
        state: SimulationState,
        forcefield: AbstractForcefield,
        neighbor_list: NeighborList,
        dt: float,
    ) -> None:
        self.integrator.step(state, forcefield, neighbor_list, dt)
        self.thermostat.apply(state, dt)
