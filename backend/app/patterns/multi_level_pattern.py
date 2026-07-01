"""
Seri-paralel bertingkat lebih dari 2 level.

Pola ini menghasilkan topologi nested 3 level penuh, contoh:

Mudah (3 level, varian A):
    R1 seri [ (R2 seri R3) paralel (R4 seri R5) ] seri R6
    Level 1: SERIES (root)
    Level 2: PARALLEL (grup tengah)
    Level 3: SERIES (tiap cabang paralel)

Sedang (3 level, varian B):
    [ (R1 paralel R2) seri R3 ] paralel [ R4 seri (R5 paralel R6) ]
    Level 1: PARALLEL (root)
    Level 2: SERIES (tiap cabang)
    Level 3: PARALLEL (sub-grup dalam cabang)

Sulit (3 level, varian C — lebih banyak komponen):
    R1 seri [ (R2 paralel R3 paralel R4) seri R5 seri (R6 paralel R7) ]
    Level 1: SERIES (root)
    Level 2: SERIES (grup tengah dalam cabang paralel luar)
    Level 3: PARALLEL (sub-grup dalam grup tengah)
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.patterns.base import PatternGenerator
from app.patterns.value_generator import pick_resistor_value, pick_voltage, get_internal_resistance

if TYPE_CHECKING:
    from app.api.schemas import AdvancedOptions


def _r(label: str, rng: random.Random, difficulty: Difficulty, advanced) -> Component:
    return Component(label=label, value=pick_resistor_value(rng, difficulty, advanced))


# ──────────────────────────────────────────────────────────────────────────────
# Sub-varian builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_variant_a(rng, difficulty, advanced) -> Branch:
    """
    R1 seri [ (R2 seri R3) paralel (R4 seri R5) ] seri R6
    Struktur: SERIES > {Comp, PARALLEL > {SERIES, SERIES}, Comp}
    """
    r1 = _r("R1", rng, difficulty, advanced)
    r6 = _r("R6", rng, difficulty, advanced)

    inner_left = Branch(
        branch_type=BranchType.SERIES,
        elements=[_r("R2", rng, difficulty, advanced), _r("R3", rng, difficulty, advanced)],
    )
    inner_right = Branch(
        branch_type=BranchType.SERIES,
        elements=[_r("R4", rng, difficulty, advanced), _r("R5", rng, difficulty, advanced)],
    )
    mid_parallel = Branch(branch_type=BranchType.PARALLEL, elements=[inner_left, inner_right])

    return Branch(branch_type=BranchType.SERIES, elements=[r1, mid_parallel, r6])


def _build_variant_b(rng, difficulty, advanced) -> Branch:
    """
    [ (R1 paralel R2) seri R3 ] paralel [ R4 seri (R5 paralel R6) ]
    Struktur: PARALLEL > {SERIES > {PARALLEL, Comp}, SERIES > {Comp, PARALLEL}}
    """
    inner_par_left = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[_r("R1", rng, difficulty, advanced), _r("R2", rng, difficulty, advanced)],
    )
    branch_left = Branch(
        branch_type=BranchType.SERIES,
        elements=[inner_par_left, _r("R3", rng, difficulty, advanced)],
    )

    inner_par_right = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[_r("R5", rng, difficulty, advanced), _r("R6", rng, difficulty, advanced)],
    )
    branch_right = Branch(
        branch_type=BranchType.SERIES,
        elements=[_r("R4", rng, difficulty, advanced), inner_par_right],
    )

    return Branch(branch_type=BranchType.PARALLEL, elements=[branch_left, branch_right])


def _build_variant_c(rng, difficulty, advanced) -> Branch:
    """
    R1 seri [ (R2 paralel R3 paralel R4) seri R5 seri (R6 paralel R7) ]
    Struktur: SERIES > {Comp, SERIES > {PARALLEL(3), Comp, PARALLEL(2)}}
    7 komponen, 3 level.
    """
    r1 = _r("R1", rng, difficulty, advanced)

    triple_par = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[
            _r("R2", rng, difficulty, advanced),
            _r("R3", rng, difficulty, advanced),
            _r("R4", rng, difficulty, advanced),
        ],
    )
    r5 = _r("R5", rng, difficulty, advanced)
    dual_par = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[_r("R6", rng, difficulty, advanced), _r("R7", rng, difficulty, advanced)],
    )

    inner_series = Branch(
        branch_type=BranchType.SERIES,
        elements=[triple_par, r5, dual_par],
    )

    return Branch(branch_type=BranchType.SERIES, elements=[r1, inner_series])


_VARIANTS_BY_DIFFICULTY: dict[Difficulty, list] = {
    Difficulty.MUDAH:  [_build_variant_a],
    Difficulty.SEDANG: [_build_variant_a, _build_variant_b],
    Difficulty.SULIT:  [_build_variant_a, _build_variant_b, _build_variant_c],
}


class MultiLevelPattern(PatternGenerator):
    """Generator rangkaian seri-paralel bertingkat > 2 level."""

    pattern_type = PatternType.MULTI_LEVEL

    def generate(
        self,
        difficulty: Difficulty,
        seed: int,
        advanced: "Optional[AdvancedOptions]" = None,
    ) -> CircuitSpec:
        rng = self._rng(seed)
        variants = _VARIANTS_BY_DIFFICULTY[difficulty]
        build_fn = rng.choice(variants)
        root = build_fn(rng, difficulty, advanced)

        source = VoltageSource(
            voltage=pick_voltage(rng, difficulty, advanced),
            internal_resistance=get_internal_resistance(advanced),
        )

        return CircuitSpec(
            pattern=self.pattern_type,
            difficulty=difficulty,
            seed=seed,
            source=source,
            root=root,
        )
