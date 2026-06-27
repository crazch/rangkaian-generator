"""Test untuk calculator — memverifikasi rumus hambatan pengganti dan
pembagian arus/tegangan untuk kasus seri, paralel, dan nested (campuran)."""

import math

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.services.calculator import solve


def _spec(root: Branch, voltage: float) -> CircuitSpec:
    return CircuitSpec(
        pattern=PatternType.MIXED_BASIC,
        difficulty=Difficulty.SEDANG,
        seed=1,
        source=VoltageSource(voltage=voltage),
        root=root,
    )


def test_series_resistance_is_sum():
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[Component(label="R1", value=10.0), Component(label="R2", value=20.0)],
    )
    solution = solve(_spec(root, voltage=30.0))
    assert solution.total_resistance == 30.0
    assert math.isclose(solution.total_current, 1.0)


def test_parallel_resistance_formula():
    root = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[Component(label="R1", value=20.0), Component(label="R2", value=20.0)],
    )
    solution = solve(_spec(root, voltage=10.0))
    assert math.isclose(solution.total_resistance, 10.0)
    # Tegangan sama di kedua cabang paralel (10V), masing-masing arus 0.5A
    for comp in solution.component_results:
        assert math.isclose(comp.voltage_drop, 10.0)
        assert math.isclose(comp.current, 0.5)


def test_nested_mixed_topology():
    # R1 seri dengan (R2 paralel R3), seri dengan R4
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[
            Component(label="R1", value=10.0),
            Branch(
                branch_type=BranchType.PARALLEL,
                elements=[Component(label="R2", value=20.0), Component(label="R3", value=30.0)],
            ),
            Component(label="R4", value=15.0),
        ],
    )
    solution = solve(_spec(root, voltage=20.0))

    # R23 = 1/(1/20 + 1/30) = 12; R_total = 10 + 12 + 15 = 37
    assert math.isclose(solution.total_resistance, 37.0)
    assert math.isclose(solution.total_current, 20.0 / 37.0)

    results_by_label = {c.label: c for c in solution.component_results}
    # Arus pada R1 dan R4 sama dengan arus total (seri)
    assert math.isclose(results_by_label["R1"].current, solution.total_current)
    assert math.isclose(results_by_label["R4"].current, solution.total_current)
    # Tegangan pada R2 dan R3 sama (paralel)
    assert math.isclose(results_by_label["R2"].voltage_drop, results_by_label["R3"].voltage_drop)
