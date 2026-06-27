"""Test untuk model CircuitSpec — memastikan struktur rekursif Branch
divalidasi dengan benar dan all_components() bekerja untuk kasus nested."""

import pytest
from pydantic import ValidationError

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource


def _make_component(label: str, value: float) -> Component:
    return Component(label=label, value=value)


def test_branch_requires_minimum_two_elements():
    with pytest.raises(ValidationError):
        Branch(branch_type=BranchType.SERIES, elements=[_make_component("R1", 10.0)])


def test_nested_branch_all_components_flattened():
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[
            _make_component("R1", 10.0),
            Branch(
                branch_type=BranchType.PARALLEL,
                elements=[_make_component("R2", 20.0), _make_component("R3", 30.0)],
            ),
            _make_component("R4", 15.0),
        ],
    )
    spec = CircuitSpec(
        pattern=PatternType.MIXED_BASIC,
        difficulty=Difficulty.SULIT,
        seed=1,
        source=VoltageSource(voltage=20.0),
        root=root,
    )

    labels = [c.label for c in spec.all_components()]
    assert labels == ["R1", "R2", "R3", "R4"]


def test_circuit_spec_serialization_roundtrip():
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[_make_component("R1", 10.0), _make_component("R2", 20.0)],
    )
    spec = CircuitSpec(
        pattern=PatternType.SERIES_SIMPLE,
        difficulty=Difficulty.MUDAH,
        seed=7,
        source=VoltageSource(voltage=9.0),
        root=root,
    )

    dumped = spec.model_dump_json()
    restored = CircuitSpec.model_validate_json(dumped)

    assert restored.seed == spec.seed
    assert [c.label for c in restored.all_components()] == ["R1", "R2"]
