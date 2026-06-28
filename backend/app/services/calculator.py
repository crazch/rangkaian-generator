"""
Mesin kalkulator: menghitung jawaban matematis dari sebuah CircuitSpec.

Karena topologi dibatasi pada Branch seri/paralel rekursif (bukan graph
bebas), perhitungan hambatan pengganti hanya butuh rekursi sederhana —
tidak perlu node analysis / solver matriks.

Update: solve() kini menerima unit_prefix opsional. Nilai numerik di
CircuitSolution tetap dalam satuan SI (Ω, A, V) agar calculator murni
matematis — konversi dan label satuan ada di field *_formatted dan
di UnitSet yang disertakan di response.
"""

from __future__ import annotations

from typing import Dict, Optional, Union

from pydantic import BaseModel

from app.models.circuit_spec import Branch, BranchType, CircuitSpec
from app.models.components import Component
from app.services.unit_converter import UnitSet, fmt_i, fmt_r, fmt_v, resolve_unit_set


class ComponentResult(BaseModel):
    """Hasil arus & tegangan untuk satu komponen spesifik."""

    component_id: str
    label: str
    # Nilai numerik — selalu dalam SI (Ω, A, V)
    resistance: float
    voltage_drop: float
    current: float
    power: float
    # Nilai terformat dengan satuan yang dipilih user
    resistance_fmt: str = ""
    voltage_drop_fmt: str = ""
    current_fmt: str = ""
    power_fmt: str = ""


class CircuitSolution(BaseModel):
    """Jawaban lengkap satu soal: hambatan pengganti + rincian per komponen."""

    total_resistance: float
    total_current: float
    source_voltage: float
    component_results: list[ComponentResult]
    # Satuan yang dipakai — dikirim ke frontend agar label kolom ikut berubah
    unit_resistance: str = "Ω"
    unit_current: str = "A"
    unit_voltage: str = "V"


def _equivalent_resistance(node: Union[Component, Branch]) -> float:
    """Hitung hambatan pengganti rekursif. Single source of truth rumus matematis."""
    if isinstance(node, Component):
        return node.value

    child_resistances = [_equivalent_resistance(el) for el in node.elements]

    if node.branch_type == BranchType.SERIES:
        return sum(child_resistances)

    return 1.0 / sum(1.0 / r for r in child_resistances)


def _resolve_branch(
    node: Union[Component, Branch],
    voltage_across: float,
    results: Dict[str, ComponentResult],
    units: UnitSet,
) -> None:
    """Rekursif menjalar ke bawah pohon Branch, mengisi results untuk setiap
    Component daun. Nilai numerik disimpan dalam SI, nilai terformat memakai
    UnitSet yang dipilih."""

    if isinstance(node, Component):
        current = voltage_across / node.value
        power = voltage_across * current
        results[node.id] = ComponentResult(
            component_id=node.id,
            label=node.label,
            resistance=node.value,
            voltage_drop=voltage_across,
            current=current,
            power=power,
            resistance_fmt=fmt_r(node.value, units),
            voltage_drop_fmt=fmt_v(voltage_across, units),
            current_fmt=fmt_i(current, units),
            power_fmt=f"{power * units.i_scale * 1:g} mW" if units.i_scale > 1 else f"{power:g} W",
        )
        return

    if node.branch_type == BranchType.SERIES:
        node_resistance = _equivalent_resistance(node)
        node_current = voltage_across / node_resistance
        for child in node.elements:
            child_resistance = _equivalent_resistance(child)
            child_voltage = node_current * child_resistance
            _resolve_branch(child, child_voltage, results, units)
    else:
        for child in node.elements:
            _resolve_branch(child, voltage_across, results, units)


def solve(spec: CircuitSpec, unit_prefix: Optional[str] = None) -> CircuitSolution:
    """Entry point utama: hitung solusi lengkap dari sebuah CircuitSpec.

    unit_prefix: 'base' | 'kilo' | 'auto' | None (default: 'base')
    """

    total_resistance = _equivalent_resistance(spec.root)
    total_current = spec.source.voltage / (total_resistance + spec.source.internal_resistance)
    voltage_across_circuit = total_current * total_resistance

    units = resolve_unit_set(unit_prefix, total_resistance)

    results: Dict[str, ComponentResult] = {}
    _resolve_branch(spec.root, voltage_across_circuit, results, units)

    ordered_results = [results[c.id] for c in spec.all_components()]

    return CircuitSolution(
        total_resistance=total_resistance,
        total_current=total_current,
        source_voltage=spec.source.voltage,
        component_results=ordered_results,
        unit_resistance=units.resistance,
        unit_current=units.current,
        unit_voltage=units.voltage,
    )