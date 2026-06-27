"""
Describer: menghasilkan deskripsi teks struktural dari CircuitSpec.

Tujuan: teks ini dipakai sebagai bahan prompt untuk LLM lain yang diminta
menjelaskan langkah penyelesaian soal — TANPA LLM tersebut perlu "membaca"
gambar rangkaian (yang rawan salah baca topologi). Karena teks dibuat
langsung dari CircuitSpec (data terstruktur, bukan interpretasi visual),
deskripsi ini dijamin konsisten dengan gambar & jawaban yang dihasilkan
dari spec yang sama.
"""

from __future__ import annotations

from typing import Union

from app.models.circuit_spec import Branch, BranchType, CircuitSpec
from app.models.components import Component


def _join_natural(items: list[str], mode: str) -> str:
    """Gabungkan list deskripsi menjadi satu kalimat natural Bahasa
    Indonesia. Untuk 2 elemen: 'A disusun seri dengan B'. Untuk 3+ elemen:
    'A, B, dan C disusun seri' — menghindari pengulangan kata penghubung
    yang janggal seperti 'A disusun seri dengan B disusun seri dengan C'.
    """

    label = "seri" if mode == "series" else "paralel"

    if len(items) == 2:
        return f"{items[0]} disusun {label} dengan {items[1]}"

    *head, last = items
    return f"{', '.join(head)}, dan {last} disusun {label}"


def _describe_node(node: Union[Component, Branch]) -> str:
    """Hasilkan deskripsi teks rekursif untuk satu node."""

    if isinstance(node, Component):
        return f"{node.label} ({node.value:g}{node.unit})"

    child_descriptions = [_describe_node(child) for child in node.elements]
    mode = "series" if node.branch_type == BranchType.SERIES else "parallel"
    joined = _join_natural(child_descriptions, mode)
    return f"[{joined}]"


def describe_topology(spec: CircuitSpec) -> str:
    """Deskripsi singkat struktur topologi, misal:
    "[R1 (10Ω) disusun seri dengan [R2 (20Ω) disusun paralel dengan R3 (30Ω)]]"
    """
    return _describe_node(spec.root)


def describe_for_llm(spec: CircuitSpec) -> str:
    """Deskripsi lengkap siap pakai sebagai konteks prompt untuk LLM lain
    yang akan menjelaskan langkah penyelesaian soal.

    Sengaja ditulis sebagai teks naratif terstruktur (bukan JSON mentah)
    karena LLM penjelas akan memparafrasekan ini menjadi langkah-langkah
    yang mudah dibaca siswa.
    """

    components = spec.all_components()
    component_lines = "\n".join(f"- {c.label}: {c.value:g}{c.unit}" for c in components)

    return (
        f"Soal rangkaian listrik (tingkat kesulitan: {spec.difficulty.value}).\n"
        f"Sumber tegangan: {spec.source.label} = {spec.source.voltage:g} V"
        + (
            f" (hambatan dalam {spec.source.internal_resistance:g}Ω)"
            if spec.source.internal_resistance > 0
            else " (sumber ideal, tanpa hambatan dalam)"
        )
        + ".\n\n"
        f"Daftar komponen:\n{component_lines}\n\n"
        f"Struktur topologi (notasi: [ ] menandai satu kelompok yang disusun "
        f"seri atau paralel sesuai kata penghubungnya):\n"
        f"{describe_topology(spec)}\n\n"
        f"Tugas: jelaskan langkah-langkah menghitung hambatan pengganti, "
        f"arus total, dan arus/tegangan pada setiap komponen, berdasarkan "
        f"struktur topologi di atas."
    )
