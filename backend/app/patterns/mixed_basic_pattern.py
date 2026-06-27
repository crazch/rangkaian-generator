from __future__ import annotations
import random
from typing import TYPE_CHECKING, Optional

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.patterns.base import PatternGenerator
from app.patterns.value_generator import pick_resistor_value, pick_voltage, get_internal_resistance

if TYPE_CHECKING:
    from app.api.schemas import AdvancedOptions

_DIFFICULTY_CONFIG: dict[Difficulty, dict] = {
    Difficulty.MUDAH:  {"n_series_outer": 1, "n_parallel_inner": 2, "n_parallel_branches": 2, "n_series_per_branch": 2},
    Difficulty.SEDANG: {"n_series_outer": 2, "n_parallel_inner": 2, "n_parallel_branches": 2, "n_series_per_branch": 2},
    Difficulty.SULIT:  {"n_series_outer": 2, "n_parallel_inner": 3, "n_parallel_branches": 3, "n_series_per_branch": 2},
}


def _make_r(label: str, rng: random.Random, difficulty: Difficulty, advanced: Optional["AdvancedOptions"]) -> Component:
    return Component(label=label, value=pick_resistor_value(rng, difficulty, advanced))


def _build_variant_a(rng, difficulty, cfg, advanced):
    idx = 1
    left = _make_r(f"R{idx}", rng, difficulty, advanced); idx += 1
    inner = Branch(
        branch_type=BranchType.PARALLEL,
        elements=[_make_r(f"R{idx+i}", rng, difficulty, advanced) for i in range(cfg["n_parallel_inner"])],
    ); idx += cfg["n_parallel_inner"]
    elements = [left, inner]
    if cfg["n_series_outer"] == 2:
        elements.append(_make_r(f"R{idx}", rng, difficulty, advanced))
    return Branch(branch_type=BranchType.SERIES, elements=elements)


def _build_variant_b(rng, difficulty, cfg, advanced):
    idx = 1
    branches = []
    for _ in range(cfg["n_parallel_branches"]):
        els = [_make_r(f"R{idx+i}", rng, difficulty, advanced) for i in range(cfg["n_series_per_branch"])]
        idx += cfg["n_series_per_branch"]
        branches.append(Branch(branch_type=BranchType.SERIES, elements=els))
    return Branch(branch_type=BranchType.PARALLEL, elements=branches)


_VARIANTS = [_build_variant_a, _build_variant_b]


class MixedBasicPattern(PatternGenerator):
    pattern_type = PatternType.MIXED_BASIC

    def generate(
        self,
        difficulty: Difficulty,
        seed: int,
        advanced: "Optional[AdvancedOptions]" = None,
    ) -> CircuitSpec:
        rng = self._rng(seed)
        cfg = _DIFFICULTY_CONFIG[difficulty]

        build_fn = rng.choice(_VARIANTS)
        root = build_fn(rng, difficulty, cfg, advanced)

        source = VoltageSource(
            voltage=pick_voltage(rng, difficulty, advanced),
            internal_resistance=get_internal_resistance(advanced),
        )

        return CircuitSpec(
            pattern=self.pattern_type, difficulty=difficulty, seed=seed,
            source=source, root=root,
        )