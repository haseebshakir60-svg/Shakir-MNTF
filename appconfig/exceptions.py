"""Custom exception hierarchy for Shakir MNTF."""


class PyMDError(Exception):
    """Base exception for all Shakir MNTF errors."""


class SimulationError(PyMDError):
    """Raised when the simulation engine encounters a fatal error."""


class ForceFieldError(PyMDError):
    """Raised for invalid force field parameters."""


class IOError(PyMDError):
    """Raised for file read/write errors."""


class BuilderError(PyMDError):
    """Raised when the atom builder cannot construct the requested system."""


class GPUError(PyMDError):
    """Raised when GPU initialization or computation fails."""
