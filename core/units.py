"""
Unit conversion utilities for molecular dynamics simulations.

Internally everything uses REDUCED (Lennard-Jones) units.
  Energy  : epsilon
  Length  : sigma
  Mass    : m (atomic mass)
  Time    : tau = sigma * sqrt(m/epsilon)

Conversion helpers go from/to SI-derived "real" units:
  Temperature : Kelvin
  Time        : femtoseconds
  Pressure    : bar
"""
from dataclasses import dataclass, field
from typing import Dict

# Boltzmann constant in reduced units: k_B [epsilon / K]
KB_SI   = 1.380649e-23   # J/K
NA      = 6.02214076e23  # /mol
KCAL    = 4184.0         # J/kcal


@dataclass
class ElementParams:
    """LJ parameters and mass for one element."""
    symbol:  str
    mass_u:  float      # atomic mass units [g/mol]
    epsilon_kJ: float   # LJ well depth [kJ/mol]
    sigma_nm:   float   # LJ diameter [nm]

    @property
    def mass_kg(self) -> float:
        return self.mass_u * 1e-3 / NA

    @property
    def epsilon_J(self) -> float:
        return self.epsilon_kJ * 1e3 / NA

    @property
    def sigma_m(self) -> float:
        return self.sigma_nm * 1e-9

    def tau_s(self) -> float:
        """Natural time unit [s]."""
        import math
        return self.sigma_m * math.sqrt(self.mass_kg / self.epsilon_J)

    def tau_fs(self) -> float:
        return self.tau_s() * 1e15


# --- Common element LJ parameters -------------------------------------------
ELEMENTS: Dict[str, ElementParams] = {
    "Ar": ElementParams("Ar", mass_u=39.948,  epsilon_kJ=0.9960, sigma_nm=0.3405),
    "Ne": ElementParams("Ne", mass_u=20.180,  epsilon_kJ=0.2984, sigma_nm=0.2749),
    "Kr": ElementParams("Kr", mass_u=83.798,  epsilon_kJ=1.6360, sigma_nm=0.3633),
    "Xe": ElementParams("Xe", mass_u=131.293, epsilon_kJ=2.2216, sigma_nm=0.3961),
    "Cu": ElementParams("Cu", mass_u=63.546,  epsilon_kJ=4.7232, sigma_nm=0.2277),
    "Fe": ElementParams("Fe", mass_u=55.845,  epsilon_kJ=6.8640, sigma_nm=0.2321),
    "C":  ElementParams("C",  mass_u=12.011,  epsilon_kJ=0.3598, sigma_nm=0.3400),
    "N":  ElementParams("N",  mass_u=14.007,  epsilon_kJ=0.6276, sigma_nm=0.3310),
    "O":  ElementParams("O",  mass_u=15.999,  epsilon_kJ=0.6508, sigma_nm=0.3119),
    "H":  ElementParams("H",  mass_u=1.008,   epsilon_kJ=0.0656, sigma_nm=0.2500),
}


# --- Unit conversion functions -----------------------------------------------

def K_to_reduced(T_K: float, epsilon_J: float) -> float:
    """Convert temperature [K] → reduced units."""
    return T_K * KB_SI / epsilon_J


def reduced_to_K(T_red: float, epsilon_J: float) -> float:
    """Convert reduced temperature → Kelvin."""
    return T_red * epsilon_J / KB_SI


def fs_to_reduced(dt_fs: float, tau_fs: float) -> float:
    """Convert time step [fs] → reduced time units."""
    return dt_fs / tau_fs


def reduced_to_fs(dt_red: float, tau_fs: float) -> float:
    return dt_red * tau_fs


def bar_to_reduced(P_bar: float, epsilon_J: float, sigma_m: float) -> float:
    """Convert pressure [bar] → reduced units."""
    return P_bar * 1e5 * (sigma_m ** 3) / epsilon_J


def reduced_to_bar(P_red: float, epsilon_J: float, sigma_m: float) -> float:
    return P_red * epsilon_J / (sigma_m ** 3) / 1e5
