from abc import ABC, abstractmethod
from core.state import SimulationState
from core.forcefields.base import AbstractForcefield
from core.neighbor.cell_list import NeighborList


class AbstractIntegrator(ABC):
    name: str = "AbstractIntegrator"

    @abstractmethod
    def step(
        self,
        state: SimulationState,
        forcefield: AbstractForcefield,
        neighbor_list: NeighborList,
        dt: float,
    ) -> None:
        """Advance state by one time step dt (in-place)."""
