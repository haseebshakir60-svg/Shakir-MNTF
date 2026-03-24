"""
Qt signal definitions for thread-safe GUI ↔ simulation communication.

ALL cross-thread communication goes through these signals.
"""
from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np


class SimulationSignals(QObject):
    """
    Signals emitted by SimulationWorker (runs in background QThread)
    and received by GUI widgets in the main thread.
    """

    # Emitted every record_every steps — carries atom positions and current step
    frame_ready = pyqtSignal(np.ndarray, np.ndarray, int)   # pos, vel, step

    # Emitted every record_every steps — carries thermodynamic dict
    thermo_update = pyqtSignal(dict)

    # Emitted when simulation finishes normally
    finished = pyqtSignal()

    # Emitted on unhandled exception in the worker thread
    error = pyqtSignal(str)

    # Progress: (current_step, total_steps, elapsed_seconds)
    progress = pyqtSignal(int, int, float)

    # Emitted every rdf_every steps — r array and g(r) array
    rdf_ready = pyqtSignal(np.ndarray, np.ndarray)

    # Emitted every record_every steps — steps array and MSD array
    msd_update = pyqtSignal(np.ndarray, np.ndarray)

    # Emitted every rdf_every steps — z_mid array, rho(z) array, mean rho scalar
    density_profile_ready = pyqtSignal(np.ndarray, np.ndarray, float)
