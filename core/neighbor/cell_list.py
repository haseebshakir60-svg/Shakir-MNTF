"""
O(N) Cell-linked list neighbor builder.

Two output formats:
  1. Pair list  (neigh_i, neigh_j)  — used by the legacy serial kernel
  2. CSR format (neigh_start, neigh_list) — used by the fast parallel kernel
     CSR stores BOTH directions: j in i's list AND i in j's list.
     This lets each parallel thread write only to forces[i] — zero race condition.
"""
from __future__ import annotations
import numpy as np
import numba
from numba import njit


# ── Common cell-assignment helper ────────────────────────────────────────────

@njit(nopython=True, cache=True)
def _build_cell_structure(pos, box, r_max):
    """Build cell assignment arrays. Returns (n_cells, cell_size, atom_cell,
    cell_offset, atom_list)."""
    N = pos.shape[0]

    n_cells  = np.empty(3, dtype=numba.int64)
    cell_size = np.empty(3, dtype=numba.float64)
    for d in range(3):
        n_cells[d]   = max(1, int(box[d] / r_max))
        cell_size[d] = box[d] / n_cells[d]

    total_cells = n_cells[0] * n_cells[1] * n_cells[2]

    atom_cell = np.empty(N, dtype=numba.int64)
    for i in range(N):
        cx = int(pos[i, 0] / cell_size[0]) % n_cells[0]
        cy = int(pos[i, 1] / cell_size[1]) % n_cells[1]
        cz = int(pos[i, 2] / cell_size[2]) % n_cells[2]
        atom_cell[i] = cx * n_cells[1] * n_cells[2] + cy * n_cells[2] + cz

    cell_count = np.zeros(total_cells, dtype=numba.int64)
    for i in range(N):
        cell_count[atom_cell[i]] += 1

    cell_offset = np.empty(total_cells + 1, dtype=numba.int64)
    cell_offset[0] = 0
    for c in range(total_cells):
        cell_offset[c + 1] = cell_offset[c] + cell_count[c]

    atom_list = np.empty(N, dtype=numba.int64)
    fill_idx  = cell_offset[:total_cells].copy()
    for i in range(N):
        c = atom_cell[i]
        atom_list[fill_idx[c]] = i
        fill_idx[c] += 1

    return n_cells, cell_size, atom_cell, cell_offset, atom_list


# ── CSR neighbor list (for parallel atom-centric kernel) ─────────────────────

@njit(nopython=True, cache=True)
def build_csr_neighbor_list(pos, box, r_cut, r_skin):
    """
    Build a CSR-format neighbor list.

    Each atom i stores ALL neighbors j within r_cut+r_skin (both directions).
    This lets prange loops over atoms write only to forces[i] — no data race.

    Returns
    -------
    neigh_start : int64[N+1]   prefix-sum offsets
    neigh_list  : int64[M]     flat neighbor indices
    """
    N     = pos.shape[0]
    r_max = r_cut + r_skin
    r_max2 = r_max * r_max

    n_cells, cell_size, atom_cell, cell_offset, atom_list = \
        _build_cell_structure(pos, box, r_max)

    # First pass: count neighbors per atom
    neigh_count = np.zeros(N, dtype=numba.int64)
    for i in range(N):
        cx = int(pos[i, 0] / cell_size[0]) % n_cells[0]
        cy = int(pos[i, 1] / cell_size[1]) % n_cells[1]
        cz = int(pos[i, 2] / cell_size[2]) % n_cells[2]
        for dcx in range(-1, 2):
            for dcy in range(-1, 2):
                for dcz in range(-1, 2):
                    ncx = (cx + dcx) % n_cells[0]
                    ncy = (cy + dcy) % n_cells[1]
                    ncz = (cz + dcz) % n_cells[2]
                    nc  = ncx * n_cells[1] * n_cells[2] + ncy * n_cells[2] + ncz
                    for k in range(cell_offset[nc], cell_offset[nc + 1]):
                        j = atom_list[k]
                        if j == i:
                            continue
                        dx = pos[i, 0] - pos[j, 0]
                        dy = pos[i, 1] - pos[j, 1]
                        dz = pos[i, 2] - pos[j, 2]
                        dx -= box[0] * round(dx / box[0])
                        dy -= box[1] * round(dy / box[1])
                        dz -= box[2] * round(dz / box[2])
                        if dx*dx + dy*dy + dz*dz < r_max2:
                            neigh_count[i] += 1

    # Build prefix-sum offsets
    neigh_start = np.empty(N + 1, dtype=numba.int64)
    neigh_start[0] = 0
    for i in range(N):
        neigh_start[i + 1] = neigh_start[i] + neigh_count[i]

    total_neigh = neigh_start[N]
    neigh_list  = np.empty(total_neigh, dtype=numba.int64)

    # Second pass: fill neighbor list
    fill = neigh_start[:N].copy()
    for i in range(N):
        cx = int(pos[i, 0] / cell_size[0]) % n_cells[0]
        cy = int(pos[i, 1] / cell_size[1]) % n_cells[1]
        cz = int(pos[i, 2] / cell_size[2]) % n_cells[2]
        for dcx in range(-1, 2):
            for dcy in range(-1, 2):
                for dcz in range(-1, 2):
                    ncx = (cx + dcx) % n_cells[0]
                    ncy = (cy + dcy) % n_cells[1]
                    ncz = (cz + dcz) % n_cells[2]
                    nc  = ncx * n_cells[1] * n_cells[2] + ncy * n_cells[2] + ncz
                    for k in range(cell_offset[nc], cell_offset[nc + 1]):
                        j = atom_list[k]
                        if j == i:
                            continue
                        dx = pos[i, 0] - pos[j, 0]
                        dy = pos[i, 1] - pos[j, 1]
                        dz = pos[i, 2] - pos[j, 2]
                        dx -= box[0] * round(dx / box[0])
                        dy -= box[1] * round(dy / box[1])
                        dz -= box[2] * round(dz / box[2])
                        if dx*dx + dy*dy + dz*dz < r_max2:
                            neigh_list[fill[i]] = j
                            fill[i] += 1

    return neigh_start, neigh_list


# ── Legacy pair list (kept for serial fallback) ───────────────────────────────

@njit(nopython=True, cache=True)
def build_neighbor_list_nb(pos, box, r_cut, r_skin):
    N     = pos.shape[0]
    r_max = r_cut + r_skin
    r_max2 = r_max * r_max

    n_cells, cell_size, atom_cell, cell_offset, atom_list = \
        _build_cell_structure(pos, box, r_max)

    max_pairs = N * 200
    ni_buf = np.empty(max_pairs, dtype=numba.int64)
    nj_buf = np.empty(max_pairs, dtype=numba.int64)
    n_pairs = 0

    for i in range(N):
        cx = int(pos[i, 0] / cell_size[0]) % n_cells[0]
        cy = int(pos[i, 1] / cell_size[1]) % n_cells[1]
        cz = int(pos[i, 2] / cell_size[2]) % n_cells[2]
        for dcx in range(-1, 2):
            for dcy in range(-1, 2):
                for dcz in range(-1, 2):
                    ncx = (cx + dcx) % n_cells[0]
                    ncy = (cy + dcy) % n_cells[1]
                    ncz = (cz + dcz) % n_cells[2]
                    nc  = ncx * n_cells[1] * n_cells[2] + ncy * n_cells[2] + ncz
                    for k in range(cell_offset[nc], cell_offset[nc + 1]):
                        j = atom_list[k]
                        if j <= i:
                            continue
                        dx = pos[i, 0] - pos[j, 0]
                        dy = pos[i, 1] - pos[j, 1]
                        dz = pos[i, 2] - pos[j, 2]
                        dx -= box[0] * round(dx / box[0])
                        dy -= box[1] * round(dy / box[1])
                        dz -= box[2] * round(dz / box[2])
                        r2 = dx*dx + dy*dy + dz*dz
                        if r2 < r_max2 and n_pairs < max_pairs:
                            ni_buf[n_pairs] = i
                            nj_buf[n_pairs] = j
                            n_pairs += 1

    return ni_buf[:n_pairs], nj_buf[:n_pairs]


# ── NeighborList class ────────────────────────────────────────────────────────

class NeighborList:
    """
    Manages Verlet neighbor list with automatic rebuild detection.

    Stores both pair-list and CSR formats for different kernels.
    Rebuilds when any atom moves more than r_skin/2 since last build.
    """

    def __init__(self, r_cut: float, r_skin: float = 0.3):
        self.r_cut   = r_cut
        self.r_skin  = r_skin
        self._pos_ref: np.ndarray | None = None

        # Pair list (serial kernel)
        self.neigh_i: np.ndarray = np.empty(0, dtype=np.int64)
        self.neigh_j: np.ndarray = np.empty(0, dtype=np.int64)

        # CSR (parallel / CUDA kernel)
        self.neigh_start: np.ndarray = np.empty(0, dtype=np.int64)
        self.neigh_list:  np.ndarray = np.empty(0, dtype=np.int64)

    def needs_rebuild(self, pos: np.ndarray) -> bool:
        if self._pos_ref is None:
            return True
        disp = pos - self._pos_ref
        # Use minimum image for displacement check
        box = getattr(self, '_box', None)
        if box is not None:
            disp -= box * np.round(disp / box)
        return float(np.max(np.sum(disp ** 2, axis=1))) > (self.r_skin * 0.5) ** 2

    def update(self, pos: np.ndarray, box: np.ndarray) -> None:
        self._box = box.copy()
        self.neigh_i, self.neigh_j = build_neighbor_list_nb(
            pos, box, self.r_cut, self.r_skin
        )
        self.neigh_start, self.neigh_list = build_csr_neighbor_list(
            pos, box, self.r_cut, self.r_skin
        )
        self._pos_ref = pos.copy()

    def get_pairs(self, pos: np.ndarray, box: np.ndarray):
        if self.needs_rebuild(pos):
            self.update(pos, box)
        return self.neigh_i, self.neigh_j

    def get_csr(self, pos: np.ndarray, box: np.ndarray):
        if self.needs_rebuild(pos):
            self.update(pos, box)
        return self.neigh_start, self.neigh_list
