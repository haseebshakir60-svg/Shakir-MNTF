"""Mean Squared Displacement (MSD) tracker."""
import numpy as np


class MSDTracker:
    """
    Tracks MSD = < |r(t) - r(0)|² > over the course of a simulation.

    Unwraps periodic boundary crossings automatically.
    """

    def __init__(self, positions0: np.ndarray, box: np.ndarray):
        self._pos0    = positions0.copy()
        self._pos_prev = positions0.copy()
        self._box     = box.copy()
        self._disp    = np.zeros_like(positions0)  # cumulative unwrapped displacement
        self._msd_log: list[tuple[int, float]] = []

    def update(self, positions: np.ndarray, step: int) -> float:
        diff = positions - self._pos_prev
        # Minimum image unwrapping
        diff -= self._box * np.round(diff / self._box)
        self._disp    += diff
        self._pos_prev = positions.copy()
        msd = float(np.mean(np.sum(self._disp ** 2, axis=1)))
        self._msd_log.append((step, msd))
        return msd

    @property
    def data(self) -> tuple[np.ndarray, np.ndarray]:
        if not self._msd_log:
            return np.array([]), np.array([])
        steps, msds = zip(*self._msd_log)
        return np.array(steps, dtype=float), np.array(msds)

    def diffusion_coefficient(self) -> float:
        """D = MSD / (6t) for 3-D (Einstein relation, long-time limit)."""
        steps, msds = self.data
        if len(steps) < 2:
            return 0.0
        # Simple linear fit to last 50% of data
        n = len(steps)
        half = n // 2
        t = steps[half:]
        m = msds[half:]
        dt = t - t[0]
        if dt[-1] == 0:
            return 0.0
        return float(np.polyfit(dt, m, 1)[0] / 6.0)
