"""
Morse potential force field.

  U(r) = D_e * [ (1 - exp(-a*(r - r_e)))^2 - 1 ]

Good for diatomic molecules and bond-stretch models.
"""
from __future__ import annotations
import numpy as np

try:
    from numba import njit, prange
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False

from core.state import SimulationState
from core.neighbor.cell_list import NeighborList
from .base import AbstractForcefield


if _HAS_NUMBA:
    @njit(parallel=True, cache=True, fastmath=True)
    def _morse_kernel(pos, box, neigh_i, neigh_j, D_e, a, r_e, r_cut):
        N = pos.shape[0]
        P = neigh_i.shape[0]
        forces  = np.zeros((N, 3))
        pe_arr  = np.zeros(P)
        vir_arr = np.zeros(P)
        r_cut2  = r_cut * r_cut

        for k in prange(P):
            i = neigh_i[k]
            j = neigh_j[k]
            dx = pos[i, 0] - pos[j, 0]
            dy = pos[i, 1] - pos[j, 1]
            dz = pos[i, 2] - pos[j, 2]
            dx -= box[0] * round(dx / box[0])
            dy -= box[1] * round(dy / box[1])
            dz -= box[2] * round(dz / box[2])
            r2 = dx * dx + dy * dy + dz * dz
            if r2 >= r_cut2 or r2 == 0.0:
                continue
            r    = r2 ** 0.5
            e    = np.exp(-a * (r - r_e))
            u    = D_e * ((1.0 - e) ** 2 - 1.0)
            fmag = 2.0 * D_e * a * e * (1.0 - e) / r
            pe_arr[k]  = u
            vir_arr[k] = fmag * r
            forces[i, 0] += fmag * dx
            forces[i, 1] += fmag * dy
            forces[i, 2] += fmag * dz
            forces[j, 0] -= fmag * dx
            forces[j, 1] -= fmag * dy
            forces[j, 2] -= fmag * dz

        return forces, pe_arr.sum(), vir_arr.sum()


class MorseForcefield(AbstractForcefield):
    """Morse pair potential."""

    name = "Morse"

    def __init__(
        self,
        D_e:   float = 1.0,
        a:     float = 1.5,
        r_e:   float = 1.0,
        r_cut: float = 3.5,
    ):
        self.D_e   = D_e
        self.a     = a
        self.r_e   = r_e
        self.r_cut = r_cut

    def compute(self, state: SimulationState, neighbor_list: NeighborList) -> None:
        ni, nj = neighbor_list.get_pairs(state.positions, state.box)
        if _HAS_NUMBA:
            forces, pe, virial = _morse_kernel(
                state.positions, state.box, ni, nj,
                self.D_e, self.a, self.r_e, self.r_cut,
            )
        else:
            raise NotImplementedError("Morse NumPy fallback not implemented yet.")
        state.forces = forces
        state.pe     = pe
        state.virial = virial

    def describe(self) -> dict:
        return {"D_e": self.D_e, "a": self.a, "r_e": self.r_e, "r_cut": self.r_cut}
