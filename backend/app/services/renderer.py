"""
Renderer: mengubah CircuitSpec menjadi gambar SVG menggunakan schemdraw.

Fix v4: matplotlib.use("Agg") untuk thread-safety.
Fix v5: tinggi SourceV dihitung dinamis.
Fix v6: tambah _BOTTOM_PADDING agar cabang paralel terakhir tidak overlap.
Fix v7: bungkus d.here dengan Point() — schemdraw 0.19+ menyimpan posisi
        setelah move_from() sebagai plain tuple; nested parallel crash tanpa ini.
Fix v9: render_wheatstone() — gambar topologi berlian (diamond) kustom untuk
        Jembatan Wheatstone. renderer rekursif biasa menghasilkan bentuk
        paralel biasa yang menyesatkan.
Fix v9: render_multi_emf() — V2 digambar sebagai elemen SourceV nyata di
        kanan loop (opposing=flip, aiding=normal), bukan sekadar teks di label.
"""

from __future__ import annotations

from typing import List, Union

import matplotlib
matplotlib.use("Agg")

import schemdraw
import schemdraw.elements as elm
from schemdraw.util import Point

from app.models.circuit_spec import Branch, BranchType, CircuitSpec
from app.models.components import Component

_PARALLEL_SPACING = 1.5
_SOURCE_DEFAULT_HEIGHT = 3.0
_BOTTOM_PADDING = 1.5


# ──────────────────────────────────────────────────────────────────────────────
# Kalkulasi tinggi
# ──────────────────────────────────────────────────────────────────────────────

def _calc_height(node: Union[Component, Branch]) -> float:
    if isinstance(node, Component):
        return 0.0
    if node.branch_type == BranchType.SERIES:
        return max((_calc_height(el) for el in node.elements), default=0.0)
    n = len(node.elements)
    child_heights = [_calc_height(el) for el in node.elements]
    return _PARALLEL_SPACING * (n - 1) + max(child_heights, default=0.0) + _BOTTOM_PADDING


# ──────────────────────────────────────────────────────────────────────────────
# Renderer rekursif (untuk seri/paralel biasa)
# ──────────────────────────────────────────────────────────────────────────────

def _draw_series(d: schemdraw.Drawing, elements: List[Union[Component, Branch]]) -> None:
    for child in elements:
        _draw_node(d, child)


def _draw_parallel(d: schemdraw.Drawing, elements: List[Union[Component, Branch]]) -> None:
    left_anchor = Point(d.here)   # Fix v7: Point() agar .x/.y selalu ada
    right_anchors: List[Point] = []

    for i, child in enumerate(elements):
        d.move_from(left_anchor, dx=0, dy=-_PARALLEL_SPACING * i)
        _draw_node(d, child)
        right_anchors.append(Point(d.here))

    main_right = right_anchors[0]

    for i in range(1, len(elements)):
        d.move_from(left_anchor, dx=0, dy=0)
        d += elm.Line().down(_PARALLEL_SPACING * i)

    for right in right_anchors[1:]:
        d.move_from(right, dx=0, dy=0)
        d += elm.Line().toy(main_right.y)

    d.move_from(main_right, dx=0, dy=0)


def _draw_node(d: schemdraw.Drawing, node: Union[Component, Branch]) -> None:
    if isinstance(node, Component):
        d += elm.Resistor().right().label(f"{node.label}\n{node.value:g}{node.unit}")
        return
    if node.branch_type == BranchType.SERIES:
        _draw_series(d, node.elements)
    else:
        _draw_parallel(d, node.elements)


# ──────────────────────────────────────────────────────────────────────────────
# Renderer kustom: Jembatan Wheatstone (topologi berlian)
# ──────────────────────────────────────────────────────────────────────────────
#
# Topologi:
#          top
#         / \
#       R1   R2
#       /     \
#   left--Rg--right    (left = node A, right = node B)
#       \     /
#       R3   R4
#         \ /
#          bot
#
# Sumber tegangan dari left ke bot (sisi kiri luar berlian).

def _resistor_label(label: str, value: float, unit: str = "Ω") -> str:
    return f"{label}\n{value:g}{unit}"


def _render_wheatstone(spec: CircuitSpec) -> str:
    comps = spec.all_components()            # urutan: R1, R2, R3, R4
    r1, r2, r3, r4 = comps
    meta = spec.topology_meta
    rg_info = meta.get("galvanometer", {"label": "Rg", "value": 0, "unit": "Ω"})

    arm = 2.5   # panjang lengan resistor diagonal
    h   = arm * 0.7  # proyeksi vertikal per lengan (~sin45° * arm)
    w   = arm * 0.7  # proyeksi horizontal per lengan

    with schemdraw.Drawing(show=False) as d:
        # Node kiri (A) = titik awal
        # R1: kiri -> atas (θ=45°)
        r1_el = d.add(elm.Resistor().theta(45).length(arm)
                      .label(_resistor_label(r1.label, r1.value), loc="top"))
        top = Point(d.here)

        # R2: atas -> kanan (θ=-45°)
        r2_el = d.add(elm.Resistor().theta(-45).length(arm)
                      .label(_resistor_label(r2.label, r2.value), loc="top"))
        right = Point(d.here)

        # Kembali ke node kiri untuk menggambar R3
        left = Point(r1_el.start)
        d.move_from(left)

        # R3: kiri -> bawah (θ=-45°)
        r3_el = d.add(elm.Resistor().theta(-45).length(arm)
                      .label(_resistor_label(r3.label, r3.value), loc="bottom"))
        bot = Point(d.here)

        # R4: bawah -> kanan (θ=45°)
        r4_el = d.add(elm.Resistor().theta(45).length(arm)
                      .label(_resistor_label(r4.label, r4.value), loc="bottom"))

        # Galvanometer: top -> bot (vertikal, tengah berlian)
        d.move_from(top)
        rg_el = d.add(
            elm.Resistor()
            .toy(bot.y)
            .label(_resistor_label(rg_info["label"], rg_info["value"], rg_info.get("unit", "Ω")),
                   loc="right")
        )

        # Tutup loop: sumber tegangan dari bot ke kiri (sisi kiri luar)
        # Gambar kabel ke bawah dari bot, lalu SourceV naik ke kiri
        d.move_from(bot)
        d.add(elm.Line().down(0.5))
        bot_ext = Point(d.here)
        d.add(elm.Line().left(w + 0.3))
        src_bot = Point(d.here)
        source_height = 2 * h + 1.0
        src_el = d.add(
            elm.SourceV().up(source_height)
            .label(f"{spec.source.label}\n{spec.source.voltage:g}V")
        )
        d.add(elm.Line().right(w + 0.3))
        d.add(elm.Line().up(0.5).tox(left.x))

        svg_bytes = d.get_imagedata("svg")

    return svg_bytes.decode("utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# Renderer kustom: Multi-EMF
# ──────────────────────────────────────────────────────────────────────────────
#
# V1 di sisi kiri (naik), resistor-resistor di atas, V2 di sisi kanan (turun).
# Opposing: V2 di-flip() sehingga polaritasnya berlawanan dengan V1.
# Aiding:   V2 tidak di-flip, polaritas sama arah dengan V1.
# Mesh (sulit): tidak ada V2 eksplisit dalam spec (polarity=None untuk V2),
#               V2 digambar di kanan tanpa indikator polaritas.

def _render_multi_emf(spec: CircuitSpec) -> str:
    circuit_height = _calc_height(spec.root)
    source_height = max(circuit_height, _SOURCE_DEFAULT_HEIGHT)

    source2 = spec.extra_sources[0] if spec.extra_sources else None
    polarity = source2.polarity if source2 else None

    pol_label_map = {
        "aiding":   "searah",
        "opposing": "berlawanan",
    }

    with schemdraw.Drawing(show=False) as d:
        # V1 di kiri, naik
        v1_el = d.add(
            elm.SourceV().up(source_height)
            .label(f"{spec.source.label}\n{spec.source.voltage:g}V")
        )
        d.add(elm.Line().right())

        # Resistor-resistor (topologi seri/paralel dari spec.root)
        _draw_node(d, spec.root)

        d.add(elm.Line().right())

        if source2 is not None:
            # V2 di kanan, turun
            pol_str = pol_label_map.get(polarity, "")
            v2_label = f"{source2.label}\n{source2.voltage:g}V"
            if pol_str:
                v2_label += f"\n({pol_str})"

            if polarity == "opposing":
                # Berlawanan arah: flip() membalik + dan - terminal
                d.add(elm.SourceV().down(source_height).flip()
                      .label(v2_label, loc="right"))
            else:
                # Searah (aiding) atau mesh (None): tidak di-flip
                d.add(elm.SourceV().down(source_height)
                      .label(v2_label, loc="right"))
        else:
            d.add(elm.Line().down(source_height))

        d.add(elm.Line().left().tox(v1_el.start))

        svg_bytes = d.get_imagedata("svg")

    return svg_bytes.decode("utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def render_svg(spec: CircuitSpec) -> str:
    """Render CircuitSpec ke SVG. Memilih renderer yang tepat berdasarkan pola."""
    from app.models.circuit_spec import PatternType

    if spec.pattern == PatternType.WHEATSTONE_BRIDGE:
        return _render_wheatstone(spec)

    if spec.pattern == PatternType.MULTI_EMF and spec.extra_sources:
        return _render_multi_emf(spec)

    # Renderer umum: seri/paralel rekursif
    circuit_height = _calc_height(spec.root)
    source_height = max(circuit_height, _SOURCE_DEFAULT_HEIGHT)

    with schemdraw.Drawing(show=False) as d:
        source_elem = (
            elm.SourceV()
            .up(source_height)
            .label(f"{spec.source.label}\n{spec.source.voltage:g}V")
        )
        d += source_elem
        d += elm.Line().right()
        _draw_node(d, spec.root)
        d += elm.Line().right()
        d += elm.Line().down(source_height)
        d += elm.Line().left().tox(source_elem.start)

        svg_bytes = d.get_imagedata("svg")

    return svg_bytes.decode("utf-8")
