"""
Crystal lattice generators.

All coordinates and masses are in REDUCED (LJ) units.
  - Length in σ
  - Mass = 1 for all atoms in a pure element system
  - Velocities sampled from Maxwell-Boltzmann at reduced temperature T_red

Returns a SimulationState ready for the simulation engine.
"""
from __future__ import annotations
import math
import numpy as np

from core.state import SimulationState
from core.units import ELEMENTS, K_to_reduced
from .element_data import ELEMENT_DATA


def _maxwell_boltzmann(n: int, T_red: float, rng: np.random.Generator) -> np.ndarray:
    """
    Sample velocities from Maxwell-Boltzmann at reduced temperature T_red.

    In reduced LJ units, mass = 1 for all atoms, so:
      sigma_v = sqrt(k_B T / m) = sqrt(T_red)
    """
    sigma_v = math.sqrt(max(T_red, 1e-12))
    vel = rng.normal(0.0, sigma_v, (n, 3))
    # Remove centre-of-mass drift
    vel -= vel.mean(axis=0)
    return vel


def build_fcc(
    element:   str   = "Ar",
    n_cells:   int   = 4,
    T_K:       float = 300.0,
    density:   float | None = None,
    seed:      int   = 42,
) -> SimulationState:
    """
    Build an FCC crystal lattice.

    Parameters
    ----------
    element  : element symbol (must be in ELEMENT_DATA)
    n_cells  : number of unit cells per dimension (total atoms = 4 * n_cells³)
    T_K      : initial temperature [K]
    density  : override density [atoms/σ³];  if None uses LJ equilibrium spacing
    """
    eps_J = ELEMENTS[element].epsilon_J

    # FCC basis (fractional coordinates)
    basis = np.array([
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.0],
        [0.5, 0.0, 0.5],
        [0.0, 0.5, 0.5],
    ])

    positions = []
    for ix in range(n_cells):
        for iy in range(n_cells):
            for iz in range(n_cells):
                for b in basis:
                    positions.append([ix + b[0], iy + b[1], iz + b[2]])

    pos = np.array(positions, dtype=np.float64)
    N   = len(pos)

    # Lattice constant in reduced units σ
    if density is not None:
        a_red = (4.0 / density) ** (1.0 / 3.0)
    else:
        # Place nearest neighbours at the LJ pair minimum 2^(1/6) σ.
        # FCC nearest-neighbour distance = a / sqrt(2), so:
        #   a = 2^(1/6) * sqrt(2) = 2^(2/3) ≈ 1.587 σ
        a_red = 2.0 ** (2.0 / 3.0)

    box = np.array([n_cells * a_red] * 3)
    pos *= a_red
    pos %= box   # wrap to box (no-op for a perfect lattice)

    T_red = K_to_reduced(T_K, eps_J)
    rng   = np.random.default_rng(seed)
    vel   = _maxwell_boltzmann(N, T_red, rng)

    # Masses = 1.0 in reduced units (pure element system)
    return SimulationState(
        positions=pos,
        velocities=vel,
        forces=np.zeros((N, 3)),
        masses=np.ones(N),
        species=[element] * N,
        box=box,
    )


def build_bcc(
    element: str   = "Fe",
    n_cells: int   = 4,
    T_K:     float = 300.0,
    seed:    int   = 42,
) -> SimulationState:
    """Build a BCC crystal lattice."""
    eps_J = ELEMENTS[element].epsilon_J

    basis = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]])

    positions = []
    for ix in range(n_cells):
        for iy in range(n_cells):
            for iz in range(n_cells):
                for b in basis:
                    positions.append([ix + b[0], iy + b[1], iz + b[2]])

    pos   = np.array(positions, dtype=np.float64)
    N     = len(pos)
    # BCC nearest-neighbour distance = a*sqrt(3)/2; put at LJ minimum → a ≈ 1.297 σ
    a_red = 2.0 ** (1.0 / 6.0) * 2.0 / math.sqrt(3.0)
    box   = np.array([n_cells * a_red] * 3)
    pos  *= a_red
    pos  %= box

    T_red = K_to_reduced(T_K, eps_J)
    rng   = np.random.default_rng(seed)
    vel   = _maxwell_boltzmann(N, T_red, rng)

    return SimulationState(
        positions=pos, velocities=vel, forces=np.zeros((N, 3)),
        masses=np.ones(N), species=[element] * N, box=box,
    )


def build_sc(
    element: str   = "Ar",
    n_cells: int   = 5,
    T_K:     float = 300.0,
    seed:    int   = 42,
) -> SimulationState:
    """Build a simple cubic crystal lattice."""
    eps_J = ELEMENTS[element].epsilon_J

    positions = []
    for ix in range(n_cells):
        for iy in range(n_cells):
            for iz in range(n_cells):
                positions.append([float(ix), float(iy), float(iz)])

    pos   = np.array(positions, dtype=np.float64)
    N     = len(pos)
    # SC nearest-neighbour = a; put at LJ minimum
    a_red = 2.0 ** (1.0 / 6.0)
    box   = np.array([n_cells * a_red] * 3)
    pos  *= a_red
    pos  %= box

    T_red = K_to_reduced(T_K, eps_J)
    rng   = np.random.default_rng(seed)
    vel   = _maxwell_boltzmann(N, T_red, rng)

    return SimulationState(
        positions=pos, velocities=vel, forces=np.zeros((N, 3)),
        masses=np.ones(N), species=[element] * N, box=box,
    )


def build_random_gas(
    element:  str   = "Ar",
    n_atoms:  int   = 500,
    box_size: float = 20.0,
    T_K:      float = 300.0,
    seed:     int   = 42,
) -> SimulationState:
    """Place atoms randomly in a box (gas / low-density liquid initial config)."""
    eps_J = ELEMENTS[element].epsilon_J

    rng = np.random.default_rng(seed)
    pos = rng.uniform(0.0, box_size, (n_atoms, 3))
    box = np.array([box_size] * 3)

    T_red = K_to_reduced(T_K, eps_J)
    vel   = _maxwell_boltzmann(n_atoms, T_red, rng)

    return SimulationState(
        positions=pos, velocities=vel, forces=np.zeros((n_atoms, 3)),
        masses=np.ones(n_atoms), species=[element] * n_atoms, box=box,
    )
