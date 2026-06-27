"""Test untuk renderer — memastikan SVG valid dihasilkan tanpa exception
untuk topologi seri, paralel, dan nested (campuran)."""

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.services.renderer import render_svg


def _spec(root: Branch) -> CircuitSpec:
    return CircuitSpec(
        pattern=PatternType.MIXED_BASIC,
        difficulty=Difficulty.SEDANG,
        seed=1,
        source=VoltageSource(voltage=12.0),
        root=root,
    )


def test_render_series_produces_valid_svg():
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[Component(label="R1", value=10.0), Component(label="R2", value=20.0)],
    )
    svg = render_svg(_spec(root))
    assert svg.startswith("<?xml") or svg.startswith("<svg")
    assert "R1" in svg and "R2" in svg


def test_render_parallel_with_four_branches():
    root = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[
            Component(label="R1", value=10.0),
            Component(label="R2", value=20.0),
            Component(label="R3", value=30.0),
            Component(label="R4", value=40.0),
        ],
    )
    svg = render_svg(_spec(root))
    for label in ["R1", "R2", "R3", "R4"]:
        assert label in svg


def test_render_nested_topology_does_not_raise():
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
    svg = render_svg(_spec(root))
    assert len(svg) > 0
