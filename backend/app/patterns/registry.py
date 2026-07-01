"""
Registry pola: satu titik pendaftaran untuk semua PatternGenerator yang ada.

Untuk menambah pola baru:
1. Buat modul baru (lihat series_pattern.py / parallel_pattern.py sebagai contoh).
2. Import & daftarkan instance-nya di PATTERN_REGISTRY di bawah.

Tidak ada bagian lain dari aplikasi (endpoint, service) yang perlu diubah.
"""

from __future__ import annotations

from app.models.circuit_spec import PatternType
from app.patterns.base import PatternGenerator
from app.patterns.parallel_pattern import ParallelSimplePattern
from app.patterns.series_pattern import SeriesSimplePattern
from app.patterns.mixed_basic_pattern import MixedBasicPattern
from app.patterns.wheatstone_pattern import WheatstoneBridgePattern
from app.patterns.multi_level_pattern import MultiLevelPattern
from app.patterns.multi_emf_pattern import MultiEMFPattern

PATTERN_REGISTRY: dict[PatternType, PatternGenerator] = {
    PatternType.SERIES_SIMPLE: SeriesSimplePattern(),
    PatternType.PARALLEL_SIMPLE: ParallelSimplePattern(),
    PatternType.MIXED_BASIC: MixedBasicPattern(),
    PatternType.WHEATSTONE_BRIDGE: WheatstoneBridgePattern(),
    PatternType.MULTI_LEVEL: MultiLevelPattern(),
    PatternType.MULTI_EMF: MultiEMFPattern(),
}


def get_pattern_generator(pattern: PatternType) -> PatternGenerator:
    """Ambil generator untuk satu PatternType. Raises KeyError jika belum
    didaftarkan (misal MIXED_BASIC yang masih placeholder)."""
    if pattern not in PATTERN_REGISTRY:
        raise KeyError(f"Pola '{pattern.value}' belum memiliki generator terdaftar")
    return PATTERN_REGISTRY[pattern]