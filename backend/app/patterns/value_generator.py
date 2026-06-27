"""
Modul pembantu untuk menghasilkan nilai komponen yang bervariasi
dan realistis per difficulty level.

Semua fungsi menerima parameter `advanced` opsional (AdvancedOptions)
untuk override dari UI Advanced Panel — tanpa mengubah signature
yang dipakai pattern yang tidak butuh advanced.
"""

from __future__ import annotations
import random
from typing import TYPE_CHECKING, Optional

from app.models.circuit_spec import Difficulty

if TYPE_CHECKING:
    from app.api.schemas import AdvancedOptions


_RESISTOR_POOLS: dict[Difficulty, list[int]] = {
    Difficulty.MUDAH:  [5, 10, 15, 20, 25, 30, 40, 50],
    Difficulty.SEDANG: [15, 20, 25, 30, 35, 40, 50, 60, 75, 80, 100],
    Difficulty.SULIT:  [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82, 100, 120, 150],
}

_N_COMPONENTS_RANGE: dict[Difficulty, tuple[int, int]] = {
    Difficulty.MUDAH:  (2, 3),
    Difficulty.SEDANG: (3, 4),
    Difficulty.SULIT:  (4, 5),
}

_VOLTAGE_POOLS: dict[Difficulty, list[float]] = {
    Difficulty.MUDAH:  [3.0, 4.5, 6.0, 9.0, 12.0],
    Difficulty.SEDANG: [6.0, 9.0, 12.0, 15.0, 18.0, 24.0],
    Difficulty.SULIT:  [9.0, 12.0, 15.0, 18.0, 24.0, 30.0, 36.0],
}

_IDENTICAL_PROB = 0.15


def pick_n_components(
    rng: random.Random,
    difficulty: Difficulty,
    advanced: "Optional[AdvancedOptions]" = None,
) -> int:
    """Jumlah komponen: pakai override jika ada, jika tidak range per difficulty."""
    if advanced and advanced.n_components is not None:
        return advanced.n_components
    lo, hi = _N_COMPONENTS_RANGE[difficulty]
    return rng.randint(lo, hi)


def _build_pool(
    difficulty: Difficulty,
    advanced: "Optional[AdvancedOptions]" = None,
) -> list[float]:
    """Bangun pool nilai resistor: filter pool default dengan r_min/r_max jika ada."""
    base_pool = _RESISTOR_POOLS[difficulty]

    if advanced and (advanced.r_min is not None or advanced.r_max is not None):
        r_min = advanced.r_min or 0.0
        r_max = advanced.r_max or float("inf")
        filtered = [v for v in base_pool if r_min <= v <= r_max]
        # Fallback ke pool penuh jika filter terlalu ketat (menghindari sample error)
        return filtered if len(filtered) >= 2 else base_pool

    return base_pool


def pick_resistor_value(
    rng: random.Random,
    difficulty: Difficulty,
    advanced: "Optional[AdvancedOptions]" = None,
) -> float:
    pool = _build_pool(difficulty, advanced)
    return float(rng.choice(pool))


def pick_resistor_values(
    rng: random.Random,
    difficulty: Difficulty,
    n: int,
    allow_identical: bool = True,
    advanced: "Optional[AdvancedOptions]" = None,
) -> list[float]:
    """
    Pilih n nilai resistor.

    Priority identik:
    1. advanced.force_identical=True  → paksa ada 1 pasang identik
    2. advanced.force_identical=False → tidak boleh identik sama sekali
    3. None                           → probabilistik 15%
    """
    pool = _build_pool(difficulty, advanced)

    # Ambil nilai unik via sample jika memungkinkan
    if n <= len(pool):
        values = [float(v) for v in rng.sample(pool, n)]
    else:
        values = [float(rng.choice(pool)) for _ in range(n)]

    # Tentukan apakah akan ada jebakan identik
    force_identical = advanced.force_identical if advanced else None

    should_identical = (
        force_identical is True
        or (force_identical is None and allow_identical and n >= 2 and rng.random() < _IDENTICAL_PROB)
    )
    no_identical = force_identical is False

    if should_identical and not no_identical and n >= 2:
        idx = rng.randint(1, n - 1)
        values[idx] = values[idx - 1]

    return values


def pick_voltage(
    rng: random.Random,
    difficulty: Difficulty,
    advanced: "Optional[AdvancedOptions]" = None,
) -> float:
    return rng.choice(_VOLTAGE_POOLS[difficulty])


def get_internal_resistance(
    advanced: "Optional[AdvancedOptions]" = None,
) -> float:
    """Ambil hambatan dalam dari advanced options, default 0 (sumber ideal)."""
    if advanced and advanced.internal_resistance is not None:
        return advanced.internal_resistance
    return 0.0