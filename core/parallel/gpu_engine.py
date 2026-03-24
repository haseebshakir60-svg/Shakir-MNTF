"""
GPU acceleration engine.

Detects CUDA availability (RTX 4060 Ti) and provides a CuPy-based
force computation path that replaces the CPU Numba path.

Falls back transparently to CPU if no CUDA device is found.
"""
from __future__ import annotations
import logging
import numpy as np

log = logging.getLogger(__name__)

_gpu_available = False
_gpu_name      = "None"

try:
    import cupy as cp
    _n = cp.cuda.runtime.getDeviceCount()
    if _n > 0:
        props = cp.cuda.runtime.getDeviceProperties(0)
        _gpu_name      = props["name"].decode()
        _gpu_available = True
        log.info("GPU detected: %s (%d device(s))", _gpu_name, _n)
except Exception as e:
    log.debug("CuPy not available: %s", e)


def check_cuda() -> tuple[bool, str]:
    """Return (available, device_name)."""
    return _gpu_available, _gpu_name


class GPUEngine:
    """
    Thin wrapper: moves arrays to GPU, runs LJ forces via CuPy,
    returns NumPy arrays.
    """

    def __init__(self):
        if not _gpu_available:
            raise RuntimeError("No CUDA device found. Install CuPy for GPU support.")
        import cupy as cp
        self.cp = cp
        log.info("GPUEngine initialised on %s", _gpu_name)

    def lj_forces(
        self,
        positions: np.ndarray,
        box:       np.ndarray,
        epsilon:   float,
        sigma:     float,
        r_cut:     float,
    ) -> tuple[np.ndarray, float, float]:
        """
        Compute LJ forces on GPU.

        Returns (forces_np, pe, virial) — all NumPy.
        """
        cp = self.cp
        pos_gpu = cp.asarray(positions)
        box_gpu = cp.asarray(box)

        N = pos_gpu.shape[0]
        forces_gpu = cp.zeros((N, 3), dtype=cp.float64)
        pe_total   = cp.float64(0.0)
        virial     = cp.float64(0.0)

        r_cut2 = r_cut ** 2
        sig2   = sigma ** 2

        # CuPy vectorised (all pairs — O(N²), fine for small N)
        # For large N, replace with a proper CUDA kernel
        for i in range(N):
            dr = pos_gpu[i] - pos_gpu          # (N, 3)
            dr -= box_gpu * cp.round(dr / box_gpu)
            r2 = cp.sum(dr ** 2, axis=1)

            mask = (r2 < r_cut2) & (r2 > 0)
            r2m  = r2[mask]

            inv_r2  = sig2 / r2m
            inv_r6  = inv_r2 ** 3
            inv_r12 = inv_r6 ** 2

            rc2 = (sigma / r_cut) ** 2
            rc6 = rc2 ** 3
            U_s = 4.0 * epsilon * (rc6 ** 2 - rc6)

            u    = 4.0 * epsilon * (inv_r12 - inv_r6) - U_s
            fmag = 24.0 * epsilon * (2.0 * inv_r12 - inv_r6) / r2m

            dr_m = dr[mask]
            fvec = fmag[:, cp.newaxis] * dr_m

            forces_gpu[i] += cp.sum(fvec, axis=0)

            pe_total += cp.sum(u) * 0.5
            virial   += cp.sum(fmag * r2m) * 0.5

        return (
            cp.asnumpy(forces_gpu),
            float(pe_total),
            float(virial),
        )
