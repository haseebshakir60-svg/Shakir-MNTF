"""Thermodynamic data CSV writer."""
import csv
from pathlib import Path
from core.state import SimulationState


class ThermoCSVWriter:
    """
    Opens a CSV file and appends thermodynamic data each time `write()` is called.

    Columns: step, KE, PE, TE, Temperature, Pressure, Density
    """

    FIELDS = ["step", "ke", "pe", "te", "temperature", "pressure", "density"]

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._fh   = open(self._path, "w", newline="")
        self._writer = csv.DictWriter(self._fh, fieldnames=self.FIELDS)
        self._writer.writeheader()

    def write(self, state: SimulationState) -> None:
        self._writer.writerow({
            "step":        state.step,
            "ke":          f"{state.ke:.6f}",
            "pe":          f"{state.pe:.6f}",
            "te":          f"{state.te:.6f}",
            "temperature": f"{state.temperature:.6f}",
            "pressure":    f"{state.pressure:.6f}",
            "density":     f"{state.density:.6f}",
        })

    def close(self) -> None:
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
