"""
Konverter satuan untuk output soal rangkaian listrik.

unit_prefix:
  'base' (default) → Ω, A, V   (tidak ada konversi)
  'kilo'           → kΩ, mA, V  (resistansi ×0.001, arus ×1000)
  'auto'           → pilih otomatis berdasarkan magnitude nilai

Modul ini adalah satu-satunya tempat logika konversi satuan didefinisikan.
Dipakai oleh calculator.py dan describer.py.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UnitSet:
    """Satuan yang dipakai untuk satu soal."""
    resistance: str   # "Ω" atau "kΩ"
    current: str      # "A" atau "mA"
    voltage: str      # selalu "V"
    r_scale: float    # faktor pengali untuk resistansi (1.0 atau 0.001)
    i_scale: float    # faktor pengali untuk arus (1.0 atau 1000.0)


BASE = UnitSet(resistance="Ω",  current="A",  voltage="V", r_scale=1.0,    i_scale=1.0)
KILO = UnitSet(resistance="kΩ", current="mA", voltage="V", r_scale=0.001,  i_scale=1000.0)


def resolve_unit_set(unit_prefix: str | None, total_resistance: float) -> UnitSet:
    """Pilih UnitSet berdasarkan unit_prefix dan magnitude hambatan total.

    'base' atau None → BASE
    'kilo'           → KILO
    'auto'           → KILO jika total_resistance >= 1000Ω, BASE jika tidak
    """
    if unit_prefix == "kilo":
        return KILO
    if unit_prefix == "auto":
        return KILO if total_resistance >= 1000.0 else BASE
    return BASE


def fmt_r(value: float, units: UnitSet, precision: int = 4) -> str:
    """Format nilai resistansi dengan satuan yang tepat."""
    converted = value * units.r_scale
    # Hilangkan trailing zero: 1.500 → 1.5, 10.000 → 10
    return f"{converted:g}{units.resistance}"


def fmt_i(value: float, units: UnitSet) -> str:
    """Format nilai arus dengan satuan yang tepat."""
    return f"{value * units.i_scale:g}{units.current}"


def fmt_v(value: float, units: UnitSet) -> str:
    """Format nilai tegangan (selalu V)."""
    return f"{value:g}{units.voltage}"