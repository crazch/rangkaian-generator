"""
Test renderer — memastikan SVG valid dan struktur topologi benar.

Setiap test paralel kini juga menghitung jumlah elemen <path> atau
kemunculan label untuk memverifikasi bahwa N cabang benar-benar digambar
sebagai N jalur terpisah, bukan sebagai seri tersembunyi.
"""

from __future__ import annotations

import re

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.services.renderer import render_svg


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _spec(root: Branch) -> CircuitSpec:
    return CircuitSpec(
        pattern=PatternType.MIXED_BASIC,
        difficulty=Difficulty.SEDANG,
        seed=1,
        source=VoltageSource(voltage=12.0),
        root=root,
    )


def _count_label(svg: str, label: str) -> int:
    """Hitung berapa kali label muncul di SVG (memverifikasi komponen tergambar)."""
    return svg.count(label)


def _resistor_count(svg: str) -> int:
    """Hitung jumlah elemen resistor di SVG via kemunculan teks 'Ω'."""
    return svg.count("Ω")


# ---------------------------------------------------------------------------
# Test SERI
# ---------------------------------------------------------------------------

def test_render_series_2_components():
    """2 resistor seri — keduanya harus muncul tepat sekali."""
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[Component(label="R1", value=10.0), Component(label="R2", value=20.0)],
    )
    svg = render_svg(_spec(root))
    assert svg.startswith("<?xml") or svg.startswith("<svg")
    assert _count_label(svg, "R1") >= 1
    assert _count_label(svg, "R2") >= 1
    assert _resistor_count(svg) == 2


def test_render_series_3_components():
    """3 resistor seri."""
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[
            Component(label="R1", value=10.0),
            Component(label="R2", value=20.0),
            Component(label="R3", value=30.0),
        ],
    )
    svg = render_svg(_spec(root))
    assert _resistor_count(svg) == 3
    for label in ["R1", "R2", "R3"]:
        assert _count_label(svg, label) >= 1


# ---------------------------------------------------------------------------
# Test PARALEL
# ---------------------------------------------------------------------------

def test_render_parallel_2_branches():
    """2 cabang paralel — keduanya harus tergambar."""
    root = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[
            Component(label="R1", value=10.0),
            Component(label="R2", value=20.0),
        ],
    )
    svg = render_svg(_spec(root))
    assert _resistor_count(svg) == 2, (
        f"Diharapkan 2 resistor di SVG, dapat {_resistor_count(svg)}. "
        "Kemungkinan cabang paralel digambar sebagai seri."
    )
    for label in ["R1", "R2"]:
        assert _count_label(svg, label) >= 1


def test_render_parallel_4_branches():
    """
    4 cabang paralel — ini adalah kasus yang sebelumnya BUG.
    Harus menghasilkan tepat 4 resistor, bukan lebih sedikit.
    """
    root = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[
            Component(label="R1", value=15.0),
            Component(label="R2", value=50.0),
            Component(label="R3", value=35.0),
            Component(label="R4", value=35.0),
        ],
    )
    svg = render_svg(_spec(root))
    assert _resistor_count(svg) == 4, (
        f"Diharapkan 4 resistor di SVG, dapat {_resistor_count(svg)}. "
        "Bug paralel 4 cabang masih ada di renderer."
    )
    for label in ["R1", "R2", "R3", "R4"]:
        assert _count_label(svg, label) >= 1, f"{label} tidak ditemukan di SVG"


def test_render_parallel_3_branches():
    """3 cabang paralel."""
    root = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[
            Component(label="R1", value=10.0),
            Component(label="R2", value=20.0),
            Component(label="R3", value=30.0),
        ],
    )
    svg = render_svg(_spec(root))
    assert _resistor_count(svg) == 3, (
        f"Diharapkan 3 resistor, dapat {_resistor_count(svg)}"
    )


# ---------------------------------------------------------------------------
# Test CAMPURAN (nested)
# ---------------------------------------------------------------------------

def test_render_series_containing_parallel():
    """
    Seri yang mengandung paralel: R1 -- [R2 || R3] -- R4
    Total 4 resistor.
    """
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[
            Component(label="R1", value=10.0),
            Branch(
                branch_type=BranchType.PARALLEL,
                elements=[
                    Component(label="R2", value=20.0),
                    Component(label="R3", value=30.0),
                ],
            ),
            Component(label="R4", value=15.0),
        ],
    )
    svg = render_svg(_spec(root))
    assert _resistor_count(svg) == 4, (
        f"Diharapkan 4 resistor (campuran), dapat {_resistor_count(svg)}"
    )
    for label in ["R1", "R2", "R3", "R4"]:
        assert _count_label(svg, label) >= 1


def test_render_parallel_containing_series():
    """
    Paralel yang mengandung seri:
    Cabang A: R1 -- R2 (seri)
    Cabang B: R3
    Total 3 resistor.
    """
    root = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[
            Branch(
                branch_type=BranchType.SERIES,
                elements=[
                    Component(label="R1", value=10.0),
                    Component(label="R2", value=20.0),
                ],
            ),
            Component(label="R3", value=30.0),
        ],
    )
    svg = render_svg(_spec(root))
    assert _resistor_count(svg) == 3, (
        f"Diharapkan 3 resistor (paralel berisi seri), dapat {_resistor_count(svg)}"
    )
    for label in ["R1", "R2", "R3"]:
        assert _count_label(svg, label) >= 1


def test_render_mixed_basic_pattern():
    """
    Pola campuran typical: R1 seri dengan (R2 paralel R3 paralel R4).
    Total 4 resistor.
    """
    root = Branch(
        branch_type=BranchType.SERIES,
        elements=[
            Component(label="R1", value=10.0),
            Branch(
                branch_type=BranchType.PARALLEL,
                elements=[
                    Component(label="R2", value=20.0),
                    Component(label="R3", value=30.0),
                    Component(label="R4", value=40.0),
                ],
            ),
        ],
    )
    svg = render_svg(_spec(root))
    assert _resistor_count(svg) == 4, (
        f"Diharapkan 4 resistor (mixed_basic), dapat {_resistor_count(svg)}"
    )


# ---------------------------------------------------------------------------
# Test seed reproducibility
# ---------------------------------------------------------------------------

def test_same_seed_produces_same_svg():
    """Seed yang sama harus menghasilkan konten visual yang identik.

    Catatan: tidak membandingkan raw SVG string karena matplotlib menyisipkan
    ID internal (clip-path, metadata) yang berbeda setiap render meskipun
    gambarnya identik secara visual. Yang kita verifikasi: jumlah resistor
    dan label komponen sama persis.
    """
    from app.patterns.registry import PATTERN_REGISTRY

    gen = PATTERN_REGISTRY[PatternType.PARALLEL_SIMPLE]
    spec1 = gen.generate(difficulty=Difficulty.SEDANG, seed=42)
    spec2 = gen.generate(difficulty=Difficulty.SEDANG, seed=42)
    svg1 = render_svg(spec1)
    svg2 = render_svg(spec2)

    # Jumlah resistor harus sama
    assert _resistor_count(svg1) == _resistor_count(svg2)

    # Setiap label di spec1 harus ada di svg2 dengan jumlah kemunculan sama
    for el in spec1.root.elements:
        if hasattr(el, "label"):
            assert _count_label(svg1, el.label) == _count_label(svg2, el.label), (
                f"Label {el.label} muncul berbeda antara dua render dengan seed sama"
            )

    # Spec yang dihasilkan harus identik (ini yang sebenarnya kita uji)
    assert spec1.model_dump() == spec2.model_dump(), (
        "CircuitSpec dengan seed sama seharusnya identik"
    )