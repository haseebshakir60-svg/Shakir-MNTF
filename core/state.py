"""
SimulationState — the single source of truth for the MD system.

All arrays are in REDUCED (LJ) units.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class SimulationState:
    """Holds all per-atom and box data for one simulation snapshot."""

    # Per-atom arrays  (N, 3)
    positions:  np.ndarray          # shape (N, 3)
    velocities: np.ndarray          # shape (N, 3)
    forces:     np.ndarray          # shape (N, 3)
    masses:     np.ndarray          # shape (N,)   – reduced mass (=1 if all same)
    species:    List[str]           # length N,  e.g. ["Ar", "Ar", ...]

    # Box (orthorhombic)
    box: np.ndarray                 # shape (3,) = [Lx, Ly, Lz]

    # Simulation clock
    step: int = 0

    # Cached thermodynamic quantities (updated each step)
    pe: float = 0.0    # potential energy (reduced)
    ke: float = 0.0    # kinetic energy   (reduced)
    virial: float = 0.0

    @property
    def n_atoms(self) -> int:
        return len(self.positions)

    @property
    def te(self) -> float:
        return self.pe + self.ke

    @property
    def temperature(self) -> float:
        """Instantaneous temperature in reduced units."""
        n = self.n_atoms
        if n == 0:
            return 0.0
        dof = 3 * n - 3          # subtract 3 for fixed COM
        return 2.0 * self.ke / dof

    @property
    def volume(self) -> float:
        return float(np.prod(self.box))

    @property
    def pressure(self) -> float:
        """Pressure via virial theorem (reduced units)."""
        n = self.n_atoms
        V = self.volume
        if V == 0:
            return 0.0
        return (n * self.temperature + self.virial / 3.0) / V

    @property
    def density(self) -> float:
        return self.n_atoms / self.volume

    def copy(self) -> "SimulationState":
        return SimulationState(
            positions=self.positions.copy(),
            velocities=self.velocities.copy(),
            forces=self.forces.copy(),
            masses=self.masses.copy(),
            species=list(self.species),
            box=self.box.copy(),
            step=self.step,
            pe=self.pe,
            ke=self.ke,
            virial=self.virial,
        )

    @staticmethod
    def create_empty(n_atoms: int, species: str = "Ar",
                     box: Optional[np.ndarray] = None) -> "SimulationState":
        if box is None:
            box = np.ones(3, dtype=np.float64) * 10.0
        return SimulationState(
            positions=np.zeros((n_atoms, 3), dtype=np.float64),
            velocities=np.zeros((n_atoms, 3), dtype=np.float64),
            forces=np.zeros((n_atoms, 3), dtype=np.float64),
            masses=np.ones(n_atoms, dtype=np.float64),
            species=[species] * n_atoms,
            box=np.asarray(box, dtype=np.float64),
        )
