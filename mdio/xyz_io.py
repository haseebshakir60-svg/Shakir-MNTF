"""Extended XYZ file reader/writer (OVITO-compatible)."""
from __future__ import annotations
import numpy as np
from pathlib import Path
from core.state import SimulationState


def write_xyz_frame(
    fh,
    state: SimulationState,
    comment: str = "",
) -> None:
    """Append one XYZ frame to an open file handle."""
    N = state.n_atoms
    fh.write(f"{N}\n")
    box = state.box
    lat = f'Lattice="{box[0]:.6f} 0 0 0 {box[1]:.6f} 0 0 0 {box[2]:.6f}"'
    props = 'Properties=species:S:1:pos:R:3:vel:R:3'
    fh.write(f'{lat} {props} step={state.step} {comment}\n')
    for i in range(N):
        s = state.species[i]
        p = state.positions[i]
        v = state.velocities[i]
        fh.write(
            f"{s} {p[0]:.8f} {p[1]:.8f} {p[2]:.8f} "
            f"{v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n"
        )


def read_xyz(path: str | Path) -> list[SimulationState]:
    """Read all frames from an extended XYZ file."""
    from core.state import SimulationState
    frames = []
    lines  = Path(path).read_text().splitlines()
    idx = 0
    while idx < len(lines):
        N = int(lines[idx].strip()); idx += 1
        comment = lines[idx]; idx += 1

        # Parse box from comment
        import re
        m = re.search(r'Lattice="([^"]+)"', comment)
        box = np.array([10.0, 10.0, 10.0])
        if m:
            vals = list(map(float, m.group(1).split()))
            box = np.array([vals[0], vals[4], vals[8]])

        positions, velocities, species = [], [], []
        for _ in range(N):
            parts = lines[idx].split(); idx += 1
            species.append(parts[0])
            positions.append([float(x) for x in parts[1:4]])
            if len(parts) >= 7:
                velocities.append([float(x) for x in parts[4:7]])
            else:
                velocities.append([0.0, 0.0, 0.0])

        state = SimulationState(
            positions=np.array(positions),
            velocities=np.array(velocities),
            forces=np.zeros((N, 3)),
            masses=np.ones(N),
            species=species,
            box=box,
        )
        frames.append(state)
    return frames
