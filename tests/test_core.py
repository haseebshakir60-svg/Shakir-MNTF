"""
Basic unit tests for the Shakir MNTF physics engine.

Run with:  python -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import numpy as np
import pytest

from core.state import SimulationState
from core.units import K_to_reduced, reduced_to_K, ELEMENTS
from core.neighbor.cell_list import NeighborList
from core.forcefields.lennard_jones import LJForcefield
from core.integrators.velocity_verlet import VelocityVerletIntegrator
from core.thermostats.berendsen import BerendsenThermostat
from core.ensembles.nvt import NVTEnsemble
from core.simulation import SimulationEngine
from builder.lattice import build_fcc


# ── Unit conversions ──────────────────────────────────────────────────────

def test_temperature_roundtrip():
    eps_J = ELEMENTS["Ar"].epsilon_J
    T_K   = 300.0
    T_red = K_to_reduced(T_K, eps_J)
    T_K2  = reduced_to_K(T_red, eps_J)
    assert abs(T_K2 - T_K) < 1e-6


# ── State ──────────────────────────────────────────────────────────────────

def test_state_properties():
    state = SimulationState.create_empty(100, "Ar", box=np.array([10.0, 10.0, 10.0]))
    assert state.n_atoms == 100
    assert state.volume  == pytest.approx(1000.0)
    assert state.density == pytest.approx(0.1)


# ── Neighbor list ─────────────────────────────────────────────────────────

def test_neighbor_list_builds():
    rng = np.random.default_rng(0)
    pos = rng.uniform(0, 10.0, (50, 3))
    box = np.array([10.0, 10.0, 10.0])
    nl  = NeighborList(r_cut=2.5, r_skin=0.3)
    ni, nj = nl.get_pairs(pos, box)
    assert len(ni) == len(nj)
    assert len(ni) > 0
    # All pairs should be within r_cut + r_skin
    for k in range(len(ni)):
        dr = pos[ni[k]] - pos[nj[k]]
        dr -= box * np.round(dr / box)
        r  = math.sqrt(dr @ dr)
        assert r < 2.5 + 0.3 + 1e-9


# ── Force field ────────────────────────────────────────────────────────────

def test_lj_forces_energy_finite():
    state = build_fcc("Ar", n_cells=2, T_K=90.0)
    nl    = NeighborList(r_cut=2.5, r_skin=0.3)
    ff    = LJForcefield(epsilon=1.0, sigma=1.0, r_cut=2.5)
    ff.compute(state, nl)
    assert math.isfinite(state.pe)
    assert np.all(np.isfinite(state.forces))


def test_lj_forces_newton_third_law():
    """Sum of forces must be zero (no net momentum change)."""
    state = build_fcc("Ar", n_cells=2, T_K=90.0)
    nl    = NeighborList(r_cut=2.5, r_skin=0.3)
    ff    = LJForcefield()
    ff.compute(state, nl)
    net = state.forces.sum(axis=0)
    np.testing.assert_allclose(net, 0.0, atol=1e-8)


# ── Integration & energy conservation ─────────────────────────────────────

def test_nve_energy_conservation():
    """
    Total energy drift should be < 5% measured over the SECOND 500-step window.
    We skip the first 500 steps (equilibration) because the perfect FCC
    lattice + random velocities produces large initial force imbalances.
    After equilibration, the velocity Verlet integrator should conserve
    energy well with dt = 0.005 τ.
    """
    state = build_fcc("Ar", n_cells=3, T_K=90.0)
    ff    = LJForcefield()
    intg  = VelocityVerletIntegrator()
    from core.ensembles.nve import NVEEnsemble
    ens   = NVEEnsemble(intg)

    engine = SimulationEngine(state, ff, ens, dt=0.005)

    # Equilibration run (discard)
    list(engine.run(500, record_every=500))

    # Measurement run
    te0 = state.te
    snapshots = list(engine.run(500, record_every=100))
    te1 = snapshots[-1].te

    drift = abs(te1 - te0) / (abs(te0) + 1e-10)
    assert drift < 0.05, f"Energy drift too large after equilibration: {drift:.2%}"


# ── Builder ────────────────────────────────────────────────────────────────

def test_fcc_atom_count():
    state = build_fcc("Ar", n_cells=3)
    assert state.n_atoms == 4 * 3 ** 3   # 108


def test_fcc_positions_in_box():
    state = build_fcc("Ar", n_cells=4)
    assert np.all(state.positions >= 0)
    assert np.all(state.positions < state.box)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
