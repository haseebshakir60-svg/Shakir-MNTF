"""Thermodynamic observable calculations."""
import numpy as np
from core.state import SimulationState


def compute_ke(state: SimulationState) -> float:
    v2 = np.sum(state.velocities ** 2 * state.masses[:, np.newaxis])
    return 0.5 * float(v2)


def compute_temperature(state: SimulationState) -> float:
    ke = compute_ke(state)
    dof = 3 * state.n_atoms - 3
    return 2.0 * ke / dof if dof > 0 else 0.0


def compute_pressure(state: SimulationState) -> float:
    return state.pressure


def get_thermo_dict(state: SimulationState) -> dict:
    return {
        "step":        state.step,
        "ke":          state.ke,
        "pe":          state.pe,
        "te":          state.te,
        "temperature": state.temperature,
        "pressure":    state.pressure,
        "density":     state.density,
    }
