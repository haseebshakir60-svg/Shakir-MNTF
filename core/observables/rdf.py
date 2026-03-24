"""
Radial Distribution Function  g(r).

Histograms pairwise distances, then normalises by the ideal-gas shell density.
"""
import numpy as np


def compute_rdf(
    positions: np.ndarray,
    box:       np.ndarray,
    n_bins:    int   = 200,
    r_max:     float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns
    -------
    r      : bin centres [reduced units]
    g_r    : g(r) values
    """
    N = positions.shape[0]
    if r_max is None:
        r_max = float(np.min(box)) * 0.5

    dr     = r_max / n_bins
    hist   = np.zeros(n_bins, dtype=np.float64)

    for i in range(N - 1):
        diff = positions[i] - positions[i + 1:]
        diff -= box * np.round(diff / box)
        r    = np.sqrt(np.sum(diff ** 2, axis=1))
        mask = r < r_max
        idx  = (r[mask] / dr).astype(int)
        np.add.at(hist, idx, 1)

    r_lo  = np.arange(n_bins) * dr
    r_hi  = r_lo + dr
    r_mid = 0.5 * (r_lo + r_hi)

    V       = float(np.prod(box))
    rho     = N / V
    shell_V = (4.0 / 3.0) * np.pi * (r_hi ** 3 - r_lo ** 3)
    norm    = 0.5 * N * rho * shell_V

    g_r = hist / norm
    return r_mid, g_r
