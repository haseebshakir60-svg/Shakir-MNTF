"""
Lennard-Jones 12-6 force field — three performance tiers.

  U(r) = 4ε [ (σ/r)^12 - (σ/r)^6 ] − U(r_cut)   (shifted)

Tier 1 — CUDA GPU  (RTX 4060 Ti, 4096 cores)
  Each CUDA thread handles one atom. Zero race conditions.
  Fastest for N > ~1000.

Tier 2 — Numba parallel CPU  (all cores via prange)
  Atom-centric loop: thread i handles only atom i → no data race.
  Uses CSR neighbor list. Approaches LAMMPS speed on many-core CPUs.

Tier 3 — Numba serial JIT  (single-core fallback)
  Used when Numba is unavailable or system is very small.

Backend is selected automatically at runtime: GPU → parallel CPU → serial.
"""
from __future__ import annotations
import logging
import numpy as np

log = logging.getLogger(__name__)

# ── Dependency detection ──────────────────────────────────────────────────────
try:
    from numba import njit, prange
    import numba
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False
    log.warning("Numba not found — using slow NumPy fallback.")

_HAS_CUDA = False
if _HAS_NUMBA:
    try:
        from numba import cuda as _numba_cuda
        if _numba_cuda.is_available():
            _HAS_CUDA = True
            log.info("CUDA available — GPU LJ kernel will be used.")
    except Exception:
        pass

from core.state import SimulationState
from core.neighbor.cell_list import NeighborList
from .base import AbstractForcefield


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 1 — CUDA GPU kernel
# ═══════════════════════════════════════════════════════════════════════════════
if _HAS_CUDA:
    from numba import cuda, float64 as nb_f64

    @cuda.jit(fastmath=True)
    def _lj_cuda_kernel(pos, box, neigh_start, neigh_list,
                        forces, pe_arr, eps, sig, r_cut):
        """
        Each CUDA thread i computes ALL forces ON atom i from its neighbors.
        No atomic operations needed — each thread writes only to forces[i].
        """
        i = cuda.grid(1)
        N = pos.shape[0]
        if i >= N:
            return

        r_cut2  = r_cut * r_cut
        sig2    = sig  * sig
        inv_rc2 = sig2 / r_cut2
        inv_rc6 = inv_rc2 * inv_rc2 * inv_rc2
        U_shift = 4.0 * eps * (inv_rc6 * inv_rc6 - inv_rc6)

        fx = nb_f64(0.0)
        fy = nb_f64(0.0)
        fz = nb_f64(0.0)
        pe = nb_f64(0.0)

        xi = pos[i, 0]; yi = pos[i, 1]; zi = pos[i, 2]
        Lx = box[0];    Ly = box[1];    Lz = box[2]

        start = neigh_start[i]
        end   = neigh_start[i + 1]

        for k in range(start, end):
            j  = neigh_list[k]
            dx = xi - pos[j, 0]
            dy = yi - pos[j, 1]
            dz = zi - pos[j, 2]

            # Minimum image
            dx -= Lx * round(dx / Lx)
            dy -= Ly * round(dy / Ly)
            dz -= Lz * round(dz / Lz)

            r2 = dx*dx + dy*dy + dz*dz
            if r2 >= r_cut2 or r2 == 0.0:
                continue

            inv_r2   = sig2 / r2
            inv_r6   = inv_r2 * inv_r2 * inv_r2
            inv_r12  = inv_r6 * inv_r6
            u        = 4.0 * eps * (inv_r12 - inv_r6) - U_shift
            fmag     = 24.0 * eps * (2.0 * inv_r12 - inv_r6) / r2

            fx += fmag * dx
            fy += fmag * dy
            fz += fmag * dz
            pe += u

        forces[i, 0] = fx
        forces[i, 1] = fy
        forces[i, 2] = fz
        pe_arr[i]    = pe * 0.5   # each pair counted by both i and j


    def _lj_gpu(pos, box, neigh_start, neigh_list, eps, sig, r_cut):
        from numba import cuda
        N        = pos.shape[0]
        d_pos    = cuda.to_device(pos.astype(np.float64))
        d_box    = cuda.to_device(box.astype(np.float64))
        d_ns     = cuda.to_device(neigh_start)
        d_nl     = cuda.to_device(neigh_list)
        d_forces = cuda.device_array((N, 3), dtype=np.float64)
        d_pe     = cuda.device_array(N,      dtype=np.float64)

        threads = 128
        blocks  = (N + threads - 1) // threads
        _lj_cuda_kernel[blocks, threads](
            d_pos, d_box, d_ns, d_nl, d_forces, d_pe, eps, sig, r_cut
        )
        cuda.synchronize()
        forces = d_forces.copy_to_host()
        pe_arr = d_pe.copy_to_host()
        return forces, float(pe_arr.sum()), float(np.sum(forces * pos) / 3.0)


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 2 — Parallel CPU kernel (atom-centric prange — no race condition)
# ═══════════════════════════════════════════════════════════════════════════════
if _HAS_NUMBA:

    @njit(parallel=True, cache=True, fastmath=True)
    def _lj_parallel_cpu(pos, box, neigh_start, neigh_list, eps, sig, r_cut):
        """
        prange over N atoms.
        Thread i loops over i's neighbors and writes ONLY to forces[i].
        No two threads share a write target → zero data races.
        PE divided by 2 because each pair (i,j) is visited by both i and j.
        """
        N       = pos.shape[0]
        r_cut2  = r_cut * r_cut
        sig2    = sig  * sig
        inv_rc2 = sig2 / r_cut2
        inv_rc6 = inv_rc2 ** 3
        U_shift = 4.0 * eps * (inv_rc6 ** 2 - inv_rc6)

        forces = np.zeros((N, 3))
        pe_arr = np.zeros(N)

        for i in prange(N):           # ← true parallel, each i independent
            fx = 0.0; fy = 0.0; fz = 0.0; pe_i = 0.0
            xi = pos[i, 0]; yi = pos[i, 1]; zi = pos[i, 2]

            for k in range(neigh_start[i], neigh_start[i + 1]):
                j  = neigh_list[k]
                dx = xi - pos[j, 0]
                dy = yi - pos[j, 1]
                dz = zi - pos[j, 2]

                dx -= box[0] * round(dx / box[0])
                dy -= box[1] * round(dy / box[1])
                dz -= box[2] * round(dz / box[2])

                r2 = dx*dx + dy*dy + dz*dz
                if r2 >= r_cut2 or r2 == 0.0:
                    continue

                inv_r2  = sig2 / r2
                inv_r6  = inv_r2 ** 3
                inv_r12 = inv_r6 ** 2
                u       = 4.0 * eps * (inv_r12 - inv_r6) - U_shift
                fmag    = 24.0 * eps * (2.0 * inv_r12 - inv_r6) / r2

                fx   += fmag * dx
                fy   += fmag * dy
                fz   += fmag * dz
                pe_i += u

            forces[i, 0] = fx
            forces[i, 1] = fy
            forces[i, 2] = fz
            pe_arr[i]    = pe_i * 0.5    # halve: pair counted by i AND j

        # Virial via scalar virial theorem approximation
        virial = -np.sum(forces * pos)
        return forces, pe_arr.sum(), virial


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 3 — Serial Numba JIT (fallback, Newton's 3rd law)
# ═══════════════════════════════════════════════════════════════════════════════
if _HAS_NUMBA:

    @njit(nopython=True, cache=True, fastmath=True)
    def _lj_serial(pos, box, neigh_i, neigh_j, eps, sig, r_cut):
        N       = pos.shape[0]
        P       = neigh_i.shape[0]
        forces  = np.zeros((N, 3))
        pe      = 0.0
        virial  = 0.0
        r_cut2  = r_cut * r_cut
        sig2    = sig * sig
        inv_rc2 = sig2 / r_cut2
        inv_rc6 = inv_rc2 ** 3
        U_shift = 4.0 * eps * (inv_rc6 ** 2 - inv_rc6)

        for k in range(P):
            i  = neigh_i[k]; j = neigh_j[k]
            dx = pos[i,0]-pos[j,0]; dy = pos[i,1]-pos[j,1]; dz = pos[i,2]-pos[j,2]
            dx -= box[0]*round(dx/box[0])
            dy -= box[1]*round(dy/box[1])
            dz -= box[2]*round(dz/box[2])
            r2 = dx*dx+dy*dy+dz*dz
            if r2 >= r_cut2 or r2 == 0.0:
                continue
            inv_r2  = sig2/r2; inv_r6=inv_r2**3; inv_r12=inv_r6**2
            u       = 4.0*eps*(inv_r12-inv_r6)-U_shift
            fmag    = 24.0*eps*(2.0*inv_r12-inv_r6)/r2
            pe     += u; virial += fmag*r2
            forces[i,0]+=fmag*dx; forces[i,1]+=fmag*dy; forces[i,2]+=fmag*dz
            forces[j,0]-=fmag*dx; forces[j,1]-=fmag*dy; forces[j,2]-=fmag*dz

        return forces, pe, virial


# ── NumPy fallback (no Numba) ──────────────────────────────────────────────────
def _lj_numpy(pos, box, neigh_i, neigh_j, eps, sig, r_cut):
    N  = pos.shape[0]
    ri = pos[neigh_i]; rj = pos[neigh_j]
    dr = ri - rj; dr -= box * np.round(dr / box)
    r2 = np.sum(dr**2, axis=1)
    mask = (r2 < r_cut**2) & (r2 > 0)
    r2m  = r2[mask]; drm = dr[mask]
    inv_r2 = (sig**2)/r2m; inv_r6=inv_r2**3; inv_r12=inv_r6**2
    rc6    = ((sig/r_cut)**2)**3
    U_s    = 4.0*eps*(rc6**2-rc6)
    fmag   = (24.0*eps*(2.0*inv_r12-inv_r6)/r2m)[:,np.newaxis]
    fvec   = fmag*drm
    forces = np.zeros((N,3))
    np.add.at(forces, neigh_i[mask], fvec)
    np.add.at(forces, neigh_j[mask], -fvec)
    pe     = float(np.sum(4.0*eps*(inv_r12-inv_r6)-U_s))
    virial = float(np.sum(fmag.ravel()*r2m))
    return forces, pe, virial


# ═══════════════════════════════════════════════════════════════════════════════
# Public force field class
# ═══════════════════════════════════════════════════════════════════════════════

class LJForcefield(AbstractForcefield):
    """
    Lennard-Jones 12-6 force field — auto-selects fastest available backend.

    Priority: CUDA GPU > Parallel CPU (prange) > Serial JIT > NumPy
    """

    name = "Lennard-Jones"

    def __init__(
        self,
        epsilon:     float = 1.0,
        sigma:       float = 1.0,
        r_cut:       float = 2.5,
        force_backend: str = "auto",   # "auto" | "gpu" | "cpu_parallel" | "serial"
    ):
        self.epsilon  = float(epsilon)
        self.sigma    = float(sigma)
        self.r_cut    = float(r_cut)
        self._backend = self._resolve_backend(force_backend)
        log.info("LJ backend: %s", self._backend)

    @staticmethod
    def _resolve_backend(requested: str) -> str:
        if requested == "gpu"          and _HAS_CUDA:   return "gpu"
        if requested == "cpu_parallel" and _HAS_NUMBA:  return "cpu_parallel"
        if requested == "serial"       and _HAS_NUMBA:  return "serial"
        if requested == "auto":
            if _HAS_CUDA:   return "gpu"
            if _HAS_NUMBA:  return "serial"   # start serial; upgrade after N check
        return "numpy"

    @property
    def backend(self) -> str:
        return self._backend

    # N threshold above which parallel CPU beats serial (empirically ~5000 on Windows)
    _PARALLEL_THRESHOLD = 5_000
    # N threshold above which GPU is worth the PCIe transfer overhead
    _GPU_THRESHOLD = 500

    def compute(self, state: SimulationState, neighbor_list: NeighborList) -> None:
        pos = state.positions
        box = state.box
        N   = state.n_atoms

        # Auto-upgrade backend based on system size
        if self._backend == "serial" and _HAS_CUDA and N >= self._GPU_THRESHOLD:
            self._backend = "gpu"
            log.info("Auto-upgraded to GPU backend (N=%d)", N)
        elif self._backend == "serial" and _HAS_NUMBA and N >= self._PARALLEL_THRESHOLD:
            self._backend = "cpu_parallel"
            log.info("Auto-upgraded to cpu_parallel backend (N=%d)", N)

        if self._backend == "gpu":
            ns, nl = neighbor_list.get_csr(pos, box)
            forces, pe, virial = _lj_gpu(
                pos, box, ns, nl, self.epsilon, self.sigma, self.r_cut
            )

        elif self._backend == "cpu_parallel":
            ns, nl = neighbor_list.get_csr(pos, box)
            forces, pe, virial = _lj_parallel_cpu(
                pos, box, ns, nl, self.epsilon, self.sigma, self.r_cut
            )

        elif self._backend == "serial":
            ni, nj = neighbor_list.get_pairs(pos, box)
            forces, pe, virial = _lj_serial(
                pos, box, ni, nj, self.epsilon, self.sigma, self.r_cut
            )

        else:
            ni, nj = neighbor_list.get_pairs(pos, box)
            forces, pe, virial = _lj_numpy(
                pos, box, ni, nj, self.epsilon, self.sigma, self.r_cut
            )

        state.forces = forces
        state.pe     = pe
        state.virial = virial

    def describe(self) -> dict:
        return {
            "epsilon":  self.epsilon,
            "sigma":    self.sigma,
            "r_cut":    self.r_cut,
            "backend":  self._backend,
        }
