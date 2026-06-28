"""
Base interface untuk modul pola topologi.

Setiap pola (seri, paralel, campuran, dst.) adalah modul terpisah yang
mengimplementasikan `PatternGenerator`. Untuk menambah pola baru di masa
depan (misal jembatan Wheatstone, atau pola RC), cukup:

1. Buat file baru di app/patterns/, implementasikan PatternGenerator.
2. Tambahkan anggota baru ke `PatternType` enum (models/circuit_spec.py).
3. Daftarkan generator baru ke `PATTERN_REGISTRY` di app/patterns/registry.py.

Tidak ada kode yang sudah ada perlu diubah — inilah yang dimaksud
"scalable tanpa mengubah yang sudah ada".
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from app.models.circuit_spec import CircuitSpec, Difficulty, PatternType

if TYPE_CHECKING:
    from app.api.schemas import AdvancedOptions


class PatternGenerator(ABC):
    """Kontrak yang harus dipenuhi setiap modul pola topologi."""

    pattern_type: PatternType

    @abstractmethod
    def generate(
        self,
        difficulty: Difficulty,
        seed: int,
        advanced: "Optional[AdvancedOptions]" = None,
    ) -> CircuitSpec:
        """Hasilkan satu CircuitSpec baru untuk pola ini.

        `seed` HARUS dipakai untuk menginisialisasi RNG lokal (misal
        `random.Random(seed)`), bukan RNG global, agar generate bersifat
        deterministik dan reproducible murni dari (pattern, difficulty, seed).

        `advanced` berisi override opsional dari UI Advanced Panel —
        teruskan ke fungsi value_generator agar parameter seperti
        n_components, r_min, r_max, force_identical, internal_resistance
        benar-benar dipakai.
        """
        raise NotImplementedError

    def _rng(self, seed: int) -> random.Random:
        """Helper agar semua subclass konsisten membuat RNG lokal."""
        return random.Random(seed)