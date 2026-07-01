"""
Describer: menghasilkan deskripsi teks struktural dari CircuitSpec.

Tujuan: teks ini dipakai sebagai bahan prompt untuk LLM lain yang diminta
menjelaskan langkah penyelesaian soal. Deskripsi dijamin konsisten dengan
gambar & jawaban karena dibuat langsung dari CircuitSpec.

Update: describe_for_llm() kini menerima unit_prefix opsional agar label
satuan di teks konsisten dengan label satuan di solution.

Fix v2: sertakan extra_sources (multi-EMF) dan topology_meta (galvanometer
Wheatstone) agar deskripsi soal benar-benar lengkap dan konsisten dengan SVG.
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


def _describe_sources(spec: CircuitSpec, units) -> str:
    """Deskripsi semua sumber tegangan — satu baris per sumber."""
    pol_labels = {
        "aiding":   "searah dengan {main} (tegangan dijumlahkan, V_eff = {v1:g}+{v2:g} = {veff:g} V)",
        "opposing": "berlawanan arah dengan {main} (tegangan dikurangi, V_eff = {v1:g}−{v2:g} = {veff:g} V)",
    }

    lines = []
    s1 = spec.source
    r_in1 = spec.source.internal_resistance
    r1_str = (
        f" (hambatan dalam {fmt_r(r_in1, units)})" if r_in1 > 0
        else " (sumber ideal, tanpa hambatan dalam)"
    )
    lines.append(f"- {s1.label} = {s1.voltage:g} V{r1_str}")

    for s2 in spec.extra_sources:
        r_in2 = s2.internal_resistance
        r2_str = (
            f" (hambatan dalam {fmt_r(r_in2, units)})" if r_in2 > 0
            else " (sumber ideal)"
        )
        pol = s2.polarity
        if pol in pol_labels:
            v1, v2 = s1.voltage, s2.voltage
            veff = (v1 + v2) if pol == "aiding" else abs(v1 - v2)
            pol_desc = pol_labels[pol].format(
                main=s1.label, v1=v1, v2=v2, veff=veff
            )
            lines.append(f"- {s2.label} = {s2.voltage:g} V{r2_str} — {pol_desc}")
        else:
            lines.append(f"- {s2.label} = {s2.voltage:g} V{r2_str}")

    return "\n".join(lines)


def _describe_special_components(spec: CircuitSpec, units) -> str:
    """Deskripsi komponen tambahan dari topology_meta (mis. galvanometer Wheatstone)."""
    lines = []
    meta = spec.topology_meta

    if "galvanometer" in meta:
        g = meta["galvanometer"]
        balanced = meta.get("balanced", True)
        bal_str = (
            "bridge seimbang (tidak ada arus mengalir melalui galvanometer, Ig = 0)"
            if balanced
            else "bridge tidak seimbang (ada arus mengalir melalui galvanometer)"
        )
        lines.append(
            f"- {g['label']} = {g['value']:g}{g.get('unit', 'Ω')} "
            f"(galvanometer / resistor jembatan — {bal_str})"
        )

    return "\n".join(lines)


def _describe_task(spec: CircuitSpec) -> str:
    """Kalimat tugas yang disesuaikan dengan tipe pola."""
    has_multi_emf = bool(spec.extra_sources)
    has_wheatstone = bool(spec.topology_meta.get("galvanometer"))

    if has_multi_emf:
        pol = spec.extra_sources[0].polarity if spec.extra_sources else None
        if pol == "aiding":
            return (
                "Tugas: hitung tegangan efektif (V_eff = V1 + V2), hambatan pengganti "
                "total, arus total, dan tegangan/arus pada setiap resistor."
            )
        elif pol == "opposing":
            return (
                "Tugas: hitung tegangan efektif (V_eff = |V1 − V2|), hambatan pengganti "
                "total, arus total, dan tegangan/arus pada setiap resistor."
            )
        else:
            # mesh (sulit)
            return (
                "Tugas: gunakan hukum Kirchhoff (analisis mesh) untuk menghitung arus "
                "pada setiap resistor. Gunakan hukum tegangan Kirchhoff (KVL) pada "
                "masing-masing loop."
            )

    if has_wheatstone:
        balanced = spec.topology_meta.get("balanced", True)
        if balanced:
            return (
                "Tugas: tunjukkan bahwa kondisi bridge seimbang terpenuhi (R1/R2 = R3/R4), "
                "jelaskan mengapa arus galvanometer Ig = 0, lalu hitung hambatan pengganti "
                "total, arus total, dan tegangan pada setiap resistor."
            )
        else:
            return (
                "Tugas: hitung hambatan total menggunakan analisis nodal (bridge tidak "
                "seimbang), lalu tentukan arus dan tegangan pada setiap resistor termasuk "
                "arus yang melalui galvanometer."
            )

    return (
        "Tugas: jelaskan langkah-langkah menghitung hambatan pengganti, "
        "arus total, dan arus/tegangan pada setiap komponen, berdasarkan "
        "struktur topologi di atas."
    )


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

    special = _describe_special_components(spec, units)
    if special:
        component_lines += "\n" + special

    sources_desc = _describe_sources(spec, units)
    multi_emf = bool(spec.extra_sources)

    return (
        f"Soal rangkaian listrik (tingkat kesulitan: {spec.difficulty.value}).\n"
        f"Sumber tegangan:\n{sources_desc}\n\n"
        f"Daftar komponen:\n{component_lines}\n\n"
        f"Struktur topologi (notasi: [ ] menandai satu kelompok yang disusun "
        f"seri atau paralel sesuai kata penghubungnya):\n"
        f"{describe_topology(spec, units.resistance)}\n\n"
        f"{_describe_task(spec)}"
    )
