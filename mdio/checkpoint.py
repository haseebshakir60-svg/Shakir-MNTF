"""Binary checkpoint save/load using NumPy .npz format."""
from pathlib import Path
import numpy as np
from core.state import SimulationState


def save_checkpoint(state: SimulationState, path: str | Path) -> None:
    path = Path(path)
    np.savez_compressed(
        str(path),
        positions=state.positions,
        velocities=state.velocities,
        forces=state.forces,
        masses=state.masses,
        species=np.array(state.species),
        box=state.box,
        step=np.array([state.step]),
        pe=np.array([state.pe]),
        ke=np.array([state.ke]),
        virial=np.array([state.virial]),
    )


def load_checkpoint(path: str | Path) -> SimulationState:
    path = Path(path)
    if not path.suffix:
        path = path.with_suffix(".npz")
    data = np.load(str(path), allow_pickle=True)
    return SimulationState(
        positions=data["positions"],
        velocities=data["velocities"],
        forces=data["forces"],
        masses=data["masses"],
        species=list(data["species"]),
        box=data["box"],
        step=int(data["step"][0]),
        pe=float(data["pe"][0]),
        ke=float(data["ke"][0]),
        virial=float(data["virial"][0]),
    )
