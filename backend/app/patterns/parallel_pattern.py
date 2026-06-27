from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.patterns.base import PatternGenerator
from app.patterns.value_generator import (
    pick_n_components, pick_resistor_values, pick_voltage, get_internal_resistance
)

if TYPE_CHECKING:
    from app.api.schemas import AdvancedOptions


class ParallelSimplePattern(PatternGenerator):
    pattern_type = PatternType.PARALLEL_SIMPLE

    def generate(
        self,
        difficulty: Difficulty,
        seed: int,
        advanced: "Optional[AdvancedOptions]" = None,
    ) -> CircuitSpec:
        rng = self._rng(seed)

        n = pick_n_components(rng, difficulty, advanced)
        values = pick_resistor_values(rng, difficulty, n, allow_identical=True, advanced=advanced)

        components = [Component(label=f"R{i+1}", value=v) for i, v in enumerate(values)]
        root = Branch(branch_type=BranchType.PARALLEL, elements=components)
        source = VoltageSource(
            voltage=pick_voltage(rng, difficulty, advanced),
            internal_resistance=get_internal_resistance(advanced),
        )

        return CircuitSpec(
            pattern=self.pattern_type, difficulty=difficulty, seed=seed,
            source=source, root=root,
        )