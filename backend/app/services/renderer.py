"""
Renderer: mengubah CircuitSpec menjadi gambar SVG menggunakan schemdraw.

Fix v4: matplotlib.use("Agg") untuk thread-safety.
Fix v5: tinggi SourceV dihitung dinamis.
Fix v6: tambah padding bawah (_BOTTOM_PADDING) agar cabang paralel terakhir
        tidak overlap dengan kabel penutup loop.
"""

from __future__ import annotations

from typing import List, Union

import matplotlib
matplotlib.use("Agg")

import schemdraw
import schemdraw.elements as elm

from app.models.circuit_spec import Branch, BranchType, CircuitSpec
from app.models.components import Component

_PARALLEL_SPACING = 1.5
_SOURCE_DEFAULT_HEIGHT = 3.0
_BOTTOM_PADDING = 1.5  # ruang antara cabang paralel terakhir dan kabel bawah


def _calc_height(node: Union[Component, Branch]) -> float:
    """Hitung tinggi vertikal yang dibutuhkan sebuah node.

    - Component: 0 (horizontal, tidak menambah tinggi).
    - Branch SERIES: tinggi maksimum elemen anak.
    - Branch PARALLEL: spacing × (n-1) + tinggi cabang nested terdalam
      + BOTTOM_PADDING agar cabang terakhir tidak overlap kabel bawah.
    """
    if isinstance(node, Component):
        return 0.0

    if node.branch_type == BranchType.SERIES:
        return max((_calc_height(el) for el in node.elements), default=0.0)

    # Paralel: tinggi = spacing antar cabang + padding bawah
    n = len(node.elements)
    child_heights = [_calc_height(el) for el in node.elements]
    return _PARALLEL_SPACING * (n - 1) + max(child_heights, default=0.0) + _BOTTOM_PADDING


def _draw_series(d: schemdraw.Drawing, elements: List[Union[Component, Branch]]) -> None:
    for child in elements:
        _draw_node(d, child)


def _draw_parallel(d: schemdraw.Drawing, elements: List[Union[Component, Branch]]) -> None:
    left_anchor = d.here
    right_anchors: List = []

    for i, child in enumerate(elements):
        d.move_from(left_anchor, dx=0, dy=-_PARALLEL_SPACING * i)
        _draw_node(d, child)
        right_anchors.append(d.here)

    main_right = right_anchors[0]

    # Sambungkan sisi kiri
    for i in range(1, len(elements)):
        d.move_from(left_anchor, dx=0, dy=0)
        d += elm.Line().down(_PARALLEL_SPACING * i)

    # Sambungkan sisi kanan ke main_right
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


def render_svg(spec: CircuitSpec) -> str:
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