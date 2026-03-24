"""Abstract base class for all force fields."""
from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from core.state import SimulationState
from core.neighbor.cell_list import NeighborList


class AbstractForcefield(ABC):
    """
    Force field interface.

    All subclasses must implement `compute()`, which fills `state.forces`
    and updates `state.pe` and `state.virial`.
    """

    name: str = "AbstractFF"

    @abstractmethod
    def compute(
        self,
        state: SimulationState,
        neighbor_list: NeighborList,
    ) -> None:
        """Compute forces, potential energy and virial in-place on *state*."""

    def describe(self) -> dict:
        """Return a dict of current parameters for the GUI panel."""
        return {}
