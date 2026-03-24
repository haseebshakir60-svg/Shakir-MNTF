"""Global application configuration and defaults."""
import os
from pathlib import Path

APP_NAME    = "Shakir MNTF"
APP_VERSION = "1.0.0"
APP_DIR     = Path(__file__).parent.parent

# Default simulation parameters
DEFAULTS = {
    "dt_fs":          2.0,
    "n_steps":        10_000,
    "record_every":   100,
    "T_target_K":     300.0,
    "P_target_bar":   1.0,
    "r_cut_factor":   2.5,      # r_cut = r_cut_factor * sigma
    "skin_factor":    0.3,      # Verlet skin = skin_factor * sigma
    "tau_T_ps":       0.1,      # Berendsen thermostat coupling time
    "tau_P_ps":       1.0,      # Berendsen barostat coupling time
}

# Parallelism
N_CPU_WORKERS = max(1, os.cpu_count() - 1)
USE_GPU       = True   # auto-detected at runtime

# Output
OUTPUT_DIR = Path.home() / "ShakirMNTF_runs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
