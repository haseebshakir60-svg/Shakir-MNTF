"""NVE microcanonical ensemble — no thermostat, conserves total energy."""
from core.state import SimulationState
from core.integrators.base import AbstractIntegrator
from core.forcefields.base import AbstractForcefield
from core.neighbor.cell_list import NeighborList


class NVEEnsemble:
    name = "NVE"

    def __init__(self, integrator: AbstractIntegrator):
        self.integrator = integrator

    def step(
        self,
        state: SimulationState,
        forcefield: AbstractForcefield,
        neighbor_list: NeighborList,
        dt: float,
    ) -> None:
        self.integrator.step(state, forcefield, neighbor_list, dt)
