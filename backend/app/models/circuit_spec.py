"""
`CircuitSpec` — Single Source of Truth untuk satu soal rangkaian.

Arsitektur kunci (sudah disepakati):
1. Topologi direpresentasikan sebagai BRANCH REKURSIF (bukan flat graph).
   Sebuah Branch adalah "seri" atau "paralel", dan elemennya bisa berupa
   Component (resistor tunggal) ATAU Branch lain (nested). Ini cukup
   ekspresif untuk semua pola rangkaian SMA standar (seri, paralel,
   campuran A/B/dst.) tanpa kompleksitas circuit solver / node analysis.

2. Sumber tegangan (`source`) adalah field root-level terpisah, BUKAN
   bagian dari topologi yang di-random. Ini menyederhanakan render
   schemdraw (loop tertutup standar) dan sesuai konvensi soal SMA yang
   selalu fokus ke susunan resistor.

3. `difficulty` dan `seed` disimpan permanen di spec final (bukan cuma
   parameter generator sesaat) agar spec bersifat self-describing —
   penting untuk reproduksibilitas/sharing soal lewat seed.

Scalability ke depan:
- RC/RL: tambah ComponentType baru di components.py + field opsional di
  Component (misal `reactance` untuk AC) — struktur Branch tidak berubah.
- Pola baru (misal jembatan Wheatstone): jadi BranchType baru atau modul
  pola tersendiri yang tetap menghasilkan CircuitSpec yang valid.
- Level kesulitan baru: tambah anggota enum Difficulty, tidak mengubah
  struktur data lain.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Union, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.components import Component, VoltageSource


class BranchType(str, Enum):
    """Jenis penyusunan elemen dalam satu Branch."""

    SERIES = "series"
    PARALLEL = "parallel"


class PatternType(str, Enum):
    """Nama pola topologi tingkat-atas. Dipakai untuk filter di endpoint
    generate (?pattern=series) dan untuk metadata/analytics.

    Tambahkan anggota baru di sini setiap kali modul pola baru dibuat di
    app/patterns/ — lihat patterns/series_pattern.py sebagai contoh.
    """

    SERIES_SIMPLE = "series_simple"
    PARALLEL_SIMPLE = "parallel_simple"
    MIXED_BASIC = "mixed_basic"
    # Tambahkan pola baru di sini, misal: WHEATSTONE_BRIDGE = "wheatstone_bridge"


class Difficulty(str, Enum):
    MUDAH = "mudah"
    SEDANG = "sedang"
    SULIT = "sulit"


class Branch(BaseModel):
    """Satu cabang rangkaian: kumpulan elemen yang disusun seri ATAU paralel.

    `elements` adalah list campuran Component dan Branch lain — inilah yang
    membuat struktur ini rekursif/nested. Contoh: rangkaian campuran
    "R1 seri dengan (R2 paralel R3)" direpresentasikan sebagai:

        Branch(
            branch_type=SERIES,
            elements=[
                Component(label="R1", ...),
                Branch(
                    branch_type=PARALLEL,
                    elements=[Component(label="R2", ...), Component(label="R3", ...)],
                ),
            ],
        )
    """

    id: str = Field(default_factory=lambda: f"branch_{uuid4().hex[:8]}")
    branch_type: BranchType
    elements: List[Union[Component, "Branch"]] = Field(
        ..., min_length=2, description="Minimal 2 elemen agar pola seri/paralel valid"
    )

    @field_validator("elements")
    @classmethod
    def _validate_elements_not_empty_branch(
        cls, v: List[Union[Component, "Branch"]]
    ) -> List[Union[Component, "Branch"]]:
        for el in v:
            if isinstance(el, Branch) and len(el.elements) < 2:
                raise ValueError("Sub-branch harus punya minimal 2 elemen")
        return v


Branch.model_rebuild()  # diperlukan karena referensi diri (forward ref "Branch")


class CircuitSpec(BaseModel):
    """Spec lengkap satu soal rangkaian — SINGLE SOURCE OF TRUTH.

    Spec inilah satu-satunya objek yang dikonsumsi oleh tiga konsumen hilir:
    1. `services/renderer.py`      -> gambar SVG (schemdraw)
    2. `services/calculator.py`    -> jawaban matematis (R_total, I, V, dst)
    3. `services/describer.py`     -> deskripsi teks struktural (untuk LLM)

    Tidak ada satupun dari ketiga konsumen itu yang boleh menyimpan logika
    topologi sendiri — semua logika topologi sudah ada di `root`.
    """

    spec_id: str = Field(default_factory=lambda: f"spec_{uuid4().hex[:12]}")
    pattern: PatternType
    difficulty: Difficulty
    seed: int = Field(..., description="Seed RNG yang menghasilkan spec ini, untuk reproduksibilitas")

    source: VoltageSource
    root: Branch = Field(..., description="Branch akar yang merepresentasikan seluruh topologi resistor")

    schema_version: Literal[1] = Field(
        default=1, description="Versi skema spec, untuk migrasi data di masa depan"
    )

    def all_components(self) -> List[Component]:
        """Flatten semua Component dari struktur Branch rekursif.
        Dipakai oleh calculator & describer agar tidak menulis ulang
        logika rekursi di masing-masing service."""

        def _walk(node: Union[Component, Branch]) -> List[Component]:
            if isinstance(node, Component):
                return [node]
            result: List[Component] = []
            for el in node.elements:
                result.extend(_walk(el))
            return result

        return _walk(self.root)
