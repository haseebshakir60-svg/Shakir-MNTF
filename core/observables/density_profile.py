"""
Z-axis density profile ρ(z).

Slices the simulation box into bins along the z direction and counts
atoms per bin, normalised to number density [atoms/σ³].
"""
import numpy as np


def compute_density_profile(
    positions: np.ndarray,
    box:       np.ndarray,
    n_bins:    int = 50,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns
    -------
    z_mid   : bin centre positions along z  [σ]
    rho_z   : number density in each bin   [atoms/σ³]
    """
    Lz      = box[2]
    Lx, Ly  = box[0], box[1]
    dz      = Lz / n_bins

    z_vals  = positions[:, 2] % Lz          # wrap z coords to [0, Lz)
    counts, edges = np.histogram(z_vals, bins=n_bins, range=(0.0, Lz))

    bin_volume = Lx * Ly * dz
    rho_z      = counts / bin_volume

    z_mid = 0.5 * (edges[:-1] + edges[1:])
    return z_mid, rho_z.astype(np.float64)
