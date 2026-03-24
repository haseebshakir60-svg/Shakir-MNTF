"""Element properties: mass, LJ parameters, CPK colors, and bulk reference densities."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ElementInfo:
    symbol:         str
    name:           str
    mass_u:         float          # atomic mass [g/mol]
    epsilon_kJ:     float          # LJ well depth [kJ/mol]
    sigma_nm:       float          # LJ diameter [nm]
    color_hex:      str            # CPK color for visualization
    bulk_density_gcc: float        # physical bulk density [g/cm³] at reference state
    bulk_T_K:       float          # temperature for that bulk density [K]
    bulk_state:     str            # "liquid" | "solid" | "gas"

    def bulk_density_reduced(self) -> float:
        """
        Convert physical bulk density to LJ reduced density:
            ρ* = ρ [g/cm³] × σ³ [cm³] × Nₐ / M [g/mol]

        This is the number density in units of 1/σ³.
        """
        import math
        sigma_cm = self.sigma_nm * 1e-7          # nm → cm
        NA       = 6.02214076e23
        return self.bulk_density_gcc * (sigma_cm ** 3) * NA / self.mass_u


ELEMENT_DATA: dict[str, ElementInfo] = {
    # Noble gases — liquid at boiling point
    "H":  ElementInfo("H",  "Hydrogen",   1.008,  0.0656, 0.2500, "#FFFFFF",
                      bulk_density_gcc=0.0708,  bulk_T_K=20.3,   bulk_state="liquid"),
    "Ne": ElementInfo("Ne", "Neon",       20.180, 0.2984, 0.2749, "#B3E3F5",
                      bulk_density_gcc=1.207,   bulk_T_K=27.1,   bulk_state="liquid"),
    "Ar": ElementInfo("Ar", "Argon",      39.948, 0.9960, 0.3405, "#80D1E3",
                      bulk_density_gcc=1.395,   bulk_T_K=87.3,   bulk_state="liquid"),
    "Kr": ElementInfo("Kr", "Krypton",    83.798, 1.6360, 0.3633, "#5CB8D1",
                      bulk_density_gcc=2.413,   bulk_T_K=119.7,  bulk_state="liquid"),
    "Xe": ElementInfo("Xe", "Xenon",     131.293, 2.2216, 0.3961, "#429EB0",
                      bulk_density_gcc=2.942,   bulk_T_K=165.1,  bulk_state="liquid"),
    # Metals — solid at room temperature
    "Cu": ElementInfo("Cu", "Copper",     63.546, 4.7232, 0.2277, "#C88033",
                      bulk_density_gcc=8.960,   bulk_T_K=293.0,  bulk_state="solid"),
    "Fe": ElementInfo("Fe", "Iron",       55.845, 6.8640, 0.2321, "#E06633",
                      bulk_density_gcc=7.874,   bulk_T_K=293.0,  bulk_state="solid"),
    "Al": ElementInfo("Al", "Aluminum",   26.982, 4.6024, 0.2551, "#BFA6A6",
                      bulk_density_gcc=2.700,   bulk_T_K=293.0,  bulk_state="solid"),
    # Non-metals
    "C":  ElementInfo("C",  "Carbon",     12.011, 0.3598, 0.3400, "#909090",
                      bulk_density_gcc=2.267,   bulk_T_K=293.0,  bulk_state="solid"),
    "N":  ElementInfo("N",  "Nitrogen",   14.007, 0.6276, 0.3310, "#3050F8",
                      bulk_density_gcc=0.808,   bulk_T_K=77.0,   bulk_state="liquid"),
    "O":  ElementInfo("O",  "Oxygen",     15.999, 0.6508, 0.3119, "#FF0D0D",
                      bulk_density_gcc=1.141,   bulk_T_K=90.2,   bulk_state="liquid"),
    "Si": ElementInfo("Si", "Silicon",    28.086, 1.0598, 0.3826, "#F0C8A0",
                      bulk_density_gcc=2.330,   bulk_T_K=293.0,  bulk_state="solid"),
}

# Map element symbol → (R, G, B) 0-255
CPK_COLORS: dict[str, tuple[int, int, int]] = {
    sym: (int(e.color_hex[1:3], 16), int(e.color_hex[3:5], 16), int(e.color_hex[5:7], 16))
    for sym, e in ELEMENT_DATA.items()
}
