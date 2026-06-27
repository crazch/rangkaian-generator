"""
Model data untuk komponen elektronik tunggal (resistor, dst) dan sumber tegangan.

Catatan desain:
- Saat ini hanya `Resistor` yang didukung (lingkup SMA: rangkaian resistor seri-paralel).
- `ComponentType` dibuat sebagai enum agar mudah ditambah (Capacitor, Inductor)
  tanpa mengubah struktur Branch/CircuitSpec — lihat catatan scalability di
  circuit_spec.py.
"""

from __future__ import annotations

from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Jenis komponen yang didukung. Tambahkan anggota baru di sini saat
    memperluas ke RC/RL (misal CAPACITOR, INDUCTOR) — tidak perlu mengubah
    struktur Branch."""

    RESISTOR = "resistor"
    # CAPACITOR = "capacitor"   # placeholder untuk fase RC mendatang
    # INDUCTOR = "inductor"     # placeholder untuk fase RL mendatang


class Component(BaseModel):
    """Satu komponen diskrit dalam rangkaian (misal satu resistor).

    `id` dipakai sebagai label tampilan (R1, R2, ...) sekaligus kunci untuk
    menautkan hasil kalkulasi (arus/tegangan per komponen) kembali ke
    komponen yang tepat saat membuat deskripsi teks atau jawaban rinci.
    """

    id: str = Field(default_factory=lambda: f"comp_{uuid4().hex[:8]}")
    type: ComponentType = ComponentType.RESISTOR
    label: str = Field(..., description="Label tampilan, misal 'R1', 'R2'")
    value: float = Field(..., gt=0, description="Nilai komponen, misal hambatan dalam Ohm")
    unit: str = Field(default="Ω", description="Satuan tampilan, misal 'Ω', 'kΩ'")

    def __str__(self) -> str:
        return f"{self.label} ({self.value}{self.unit})"


class VoltageSource(BaseModel):
    """Sumber tegangan DC tunggal di root rangkaian.

    Sesuai kesepakatan arsitektur: posisi sumber tegangan selalu fixed
    (root-level), tidak menjadi bagian dari topologi yang di-random.
    """

    label: str = Field(default="V", description="Label tampilan, misal 'V', 'Vs'")
    voltage: float = Field(..., gt=0, description="Tegangan sumber dalam Volt")
    internal_resistance: float = Field(
        default=0.0,
        ge=0,
        description="Hambatan dalam sumber (Ohm). 0 = sumber ideal (default untuk level SMA dasar).",
    )
