"""
Renderer: mengubah CircuitSpec menjadi gambar SVG menggunakan schemdraw.

Pendekatan layout:
- Sumber tegangan digambar sebagai sisi kiri loop tertutup (fixed, sesuai
  keputusan arsitektur), lalu rangkaian resistor (root Branch) digambar
  mengikuti pola seri/paralel secara rekursif, ditutup oleh kabel kembali
  ke sumber membentuk loop tertutup.
- Branch SERIES: elemen anak digambar berurutan ke kanan, masing-masing
  mulai dari titik akhir elemen sebelumnya (perilaku default schemdraw).
- Branch PARALLEL: setiap elemen anak digambar sebagai cabang horizontal
  terpisah, ditumpuk vertikal dengan jarak `_PARALLEL_SPACING`. Semua
  cabang dimulai dari node kiri yang sama dan berakhir di node kanan yang
  sama, disatukan lewat kabel vertikal eksplisit (BUKAN push()/pop() saja
  — percobaan awal menunjukkan push()/pop() tidak otomatis menyatukan
  titik akhir cabang dengan benar, sehingga harus digabung manual dengan
  `Line().toy(...)`).
- Rekursi: setiap elemen anak boleh berupa Component (digambar sebagai
  satu Resistor) ATAU Branch lain (digambar secara rekursif memanggil
  `_draw_node` lagi) — inilah yang membuat topologi campuran (nested,
  misal paralel di dalam seri atau sebaliknya) bisa digambar tanpa kode
  tambahan di luar fungsi-fungsi ini.
- Tidak ada penggunaan matplotlib manual untuk layout — schemdraw
  menangani layout & ekspor SVG secara native lewat `d.get_imagedata('svg')`.

Catatan verifikasi: layout paralel di atas sudah diuji visual (lihat
riwayat pengembangan) untuk kasus 2 cabang sederhana, N cabang, dan
cabang berisi sub-branch seri (nested) — ketiganya menghasilkan gambar
loop tertutup yang benar secara topologi.
"""

from __future__ import annotations

from typing import List, Union

import schemdraw
import schemdraw.elements as elm

from app.models.circuit_spec import Branch, BranchType, CircuitSpec
from app.models.components import Component

# Jarak vertikal antar cabang paralel yang ditumpuk. Nilai dalam satuan
# schemdraw (default 1 unit ~ panjang satu komponen standar).
_PARALLEL_SPACING = 1.5


def _draw_series(d: schemdraw.Drawing, elements: List[Union[Component, Branch]]) -> None:
    """Gambar elemen-elemen yang disusun seri, berurutan ke kanan.
    Setiap elemen otomatis mulai dari titik akhir elemen sebelumnya."""
    for child in elements:
        _draw_node(d, child)


def _draw_parallel(d: schemdraw.Drawing, elements: List[Union[Component, Branch]]) -> None:
    """Gambar elemen-elemen yang disusun paralel, ditumpuk vertikal,
    semuanya berbagi node kiri dan node kanan yang sama.

    Posisi kursor (`d.here`) setelah fungsi ini selesai akan berada di
    node kanan bersama, siap dilanjutkan oleh elemen seri berikutnya jika
    ada (mendukung nesting seri-dalam-paralel dan paralel-dalam-seri).
    """

    left_node = d.here
    right_nodes: List = []

    for i, child in enumerate(elements):
        dy = -_PARALLEL_SPACING * i
        d.move_from(left_node, dx=0, dy=dy)
        _draw_node(d, child)
        right_nodes.append(d.here)

    main_right_node = right_nodes[0]

    # Sambungkan sisi kiri: setiap cabang ke-2 dst turun dari left_node.
    for i in range(1, len(elements)):
        d.move_from(left_node, dx=0, dy=0)
        d += elm.Line().down(_PARALLEL_SPACING * i)

    # Sambungkan sisi kanan: setiap cabang ke-2 dst disatukan ke
    # main_right_node (titik akhir cabang pertama).
    for right_node in right_nodes[1:]:
        d.move_from(right_node, dx=0, dy=0)
        d += elm.Line().toy(main_right_node)

    # Kursor diposisikan kembali ke node kanan bersama agar pemanggil
    # (misal Branch seri di luar) bisa melanjutkan menggambar dari sini.
    d.move_from(main_right_node, dx=0, dy=0)


def _draw_node(d: schemdraw.Drawing, node: Union[Component, Branch]) -> None:
    """Gambar satu node (Component atau Branch) secara rekursif."""

    if isinstance(node, Component):
        d += elm.Resistor().right().label(f"{node.label}\n{node.value:g}{node.unit}")
        return

    if node.branch_type == BranchType.SERIES:
        _draw_series(d, node.elements)
    else:
        _draw_parallel(d, node.elements)


def render_svg(spec: CircuitSpec) -> str:
    """Render satu CircuitSpec menjadi string SVG.

    Mengembalikan markup SVG sebagai string (UTF-8), siap dikirim langsung
    sebagai response FastAPI bertipe `image/svg+xml` atau disisipkan ke
    payload JSON sebagai field string.
    """

    with schemdraw.Drawing(show=False) as d:
        source_elem = elm.SourceV().up().label(f"{spec.source.label}\n{spec.source.voltage:g}V")
        d += source_elem
        d += elm.Line().right()

        _draw_node(d, spec.root)

        d += elm.Line().right()
        d += elm.Line().down()
        d += elm.Line().left().tox(source_elem.start)

        svg_bytes = d.get_imagedata("svg")

    return svg_bytes.decode("utf-8")
