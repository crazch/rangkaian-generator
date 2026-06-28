"""
Describer: menghasilkan deskripsi teks struktural dari CircuitSpec.

Tujuan: teks ini dipakai sebagai bahan prompt untuk LLM lain yang diminta
menjelaskan langkah penyelesaian soal. Deskripsi dijamin konsisten dengan
gambar & jawaban karena dibuat langsung dari CircuitSpec.

Update: describe_for_llm() kini menerima unit_prefix opsional agar label
satuan di teks konsisten dengan label satuan di solution.
"""

from __future__ import annotations

from typing import Optional, Union

from app.models.circuit_spec import Branch, BranchType, CircuitSpec
from app.models.components import Component
from app.services.unit_converter import fmt_r, resolve_unit_set


def _join_natural(items: list[str], mode: str) -> str:
    label = "seri" if mode == "series" else "paralel"
    if len(items) == 2:
        return f"{items[0]} disusun {label} dengan {items[1]}"
    *head, last = items
    return f"{', '.join(head)}, dan {last} disusun {label}"


def _describe_node(node: Union[Component, Branch], unit_suffix: str = "Ω") -> str:
    """Deskripsi rekursif satu node, dengan satuan resistansi yang bisa dikonfigurasi."""
    if isinstance(node, Component):
        return f"{node.label} ({node.value:g}{unit_suffix})"

    child_descriptions = [_describe_node(child, unit_suffix) for child in node.elements]
    mode = "series" if node.branch_type == BranchType.SERIES else "parallel"
    joined = _join_natural(child_descriptions, mode)
    return f"[{joined}]"


def describe_topology(spec: CircuitSpec, unit_suffix: str = "Ω") -> str:
    """Deskripsi singkat struktur topologi."""
    return _describe_node(spec.root, unit_suffix)


def describe_for_llm(
    spec: CircuitSpec,
    unit_prefix: Optional[str] = None,
) -> str:
    """Deskripsi lengkap siap pakai sebagai konteks prompt untuk LLM lain.

    unit_prefix: 'base' | 'kilo' | 'auto' | None — harus konsisten dengan
    nilai yang dikirim ke calculator.solve() agar satuan di teks sama dengan
    di solution.
    """
    from app.services.calculator import _equivalent_resistance
    total_r = _equivalent_resistance(spec.root)
    units = resolve_unit_set(unit_prefix, total_r)

    components = spec.all_components()
    component_lines = "\n".join(
        f"- {c.label}: {fmt_r(c.value, units)}" for c in components
    )

    return (
        f"Soal rangkaian listrik (tingkat kesulitan: {spec.difficulty.value}).\n"
        f"Sumber tegangan: {spec.source.label} = {spec.source.voltage:g} V"
        + (
            f" (hambatan dalam {fmt_r(spec.source.internal_resistance, units)})"
            if spec.source.internal_resistance > 0
            else " (sumber ideal, tanpa hambatan dalam)"
        )
        + ".\n\n"
        f"Daftar komponen:\n{component_lines}\n\n"
        f"Struktur topologi (notasi: [ ] menandai satu kelompok yang disusun "
        f"seri atau paralel sesuai kata penghubungnya):\n"
        f"{describe_topology(spec, units.resistance)}\n\n"
        f"Tugas: jelaskan langkah-langkah menghitung hambatan pengganti, "
        f"arus total, dan arus/tegangan pada setiap komponen, berdasarkan "
        f"struktur topologi di atas."
    )