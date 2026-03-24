from abc import ABC, abstractmethod
from core.state import SimulationState


class AbstractThermostat(ABC):
    name: str = "AbstractThermostat"

    @abstractmethod
    def apply(self, state: SimulationState, dt: float) -> None:
        """Rescale/modify velocities to maintain target temperature."""
