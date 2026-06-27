"""
Mesin kalkulator: menghitung jawaban matematis dari sebuah CircuitSpec.

Karena topologi dibatasi pada Branch seri/paralel rekursif (bukan graph
bebas), perhitungan hambatan pengganti hanya butuh rekursi sederhana —
tidak perlu node analysis / solver matriks. Ini konsekuensi langsung dari
keputusan arsitektur "template, bukan graph bebas".
"""

from __future__ import annotations

from typing import Dict, Union

from pydantic import BaseModel

from app.models.circuit_spec import Branch, BranchType, CircuitSpec
from app.models.components import Component


class ComponentResult(BaseModel):
    """Hasil arus & tegangan untuk satu komponen spesifik."""

    component_id: str
    label: str
    resistance: float
    voltage_drop: float
    current: float
    power: float


class CircuitSolution(BaseModel):
    """Jawaban lengkap satu soal: hambatan pengganti + rincian per komponen."""

    total_resistance: float
    total_current: float
    source_voltage: float
    component_results: list[ComponentResult]


def _equivalent_resistance(node: Union[Component, Branch]) -> float:
    """Hitung hambatan pengganti dari satu node (Component atau Branch),
    secara rekursif. Inilah satu-satunya tempat rumus seri/paralel
    didefinisikan — single source of truth untuk rumus matematis."""

    if isinstance(node, Component):
        return node.value

    child_resistances = [_equivalent_resistance(el) for el in node.elements]

    if node.branch_type == BranchType.SERIES:
        return sum(child_resistances)

    # PARALLEL
    return 1.0 / sum(1.0 / r for r in child_resistances)


def _resolve_branch(
    node: Union[Component, Branch],
    voltage_across: float,
    results: Dict[str, ComponentResult],
) -> None:
    """Rekursif menjalar ke bawah pohon Branch, menentukan tegangan yang
    jatuh pada tiap node, lalu mengisi `results` untuk setiap Component
    daun yang ditemukan.

    `voltage_across` adalah tegangan total yang melintasi node ini
    (bukan tegangan sumber keseluruhan, kecuali node ini adalah root).
    """

    if isinstance(node, Component):
        current = voltage_across / node.value
        results[node.id] = ComponentResult(
            component_id=node.id,
            label=node.label,
            resistance=node.value,
            voltage_drop=voltage_across,
            current=current,
            power=voltage_across * current,
        )
        return

    if node.branch_type == BranchType.SERIES:
        # Tegangan terbagi proporsional terhadap hambatan masing-masing
        # elemen anak, sebanding dengan hambatan total node ini.
        node_resistance = _equivalent_resistance(node)
        node_current = voltage_across / node_resistance
        for child in node.elements:
            child_resistance = _equivalent_resistance(child)
            child_voltage = node_current * child_resistance
            _resolve_branch(child, child_voltage, results)
    else:
        # PARALLEL: setiap cabang anak mendapat tegangan yang sama persis
        # dengan tegangan yang melintasi node paralel ini.
        for child in node.elements:
            _resolve_branch(child, voltage_across, results)


def solve(spec: CircuitSpec) -> CircuitSolution:
    """Entry point utama: hitung solusi lengkap dari sebuah CircuitSpec."""

    total_resistance = _equivalent_resistance(spec.root)
    total_current = spec.source.voltage / (total_resistance + spec.source.internal_resistance)

    # Tegangan yang benar-benar jatuh pada rangkaian eksternal (setelah
    # dikurangi tegangan hilang akibat hambatan dalam sumber, jika ada).
    voltage_across_circuit = total_current * total_resistance

    results: Dict[str, ComponentResult] = {}
    _resolve_branch(spec.root, voltage_across_circuit, results)

    # Urutkan hasil sesuai urutan komponen pada spec.all_components()
    # agar output deterministik dan mudah dicocokkan dengan label R1, R2, ...
    ordered_results = [results[c.id] for c in spec.all_components()]

    return CircuitSolution(
        total_resistance=total_resistance,
        total_current=total_current,
        source_voltage=spec.source.voltage,
        component_results=ordered_results,
    )
