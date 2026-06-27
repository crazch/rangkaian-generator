"""Endpoint untuk men-generate soal rangkaian listrik."""

from __future__ import annotations

import random
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import AdvancedOptions, GenerateQuestionResponse
from app.models.circuit_spec import Difficulty, PatternType
from app.patterns.registry import PATTERN_REGISTRY, get_pattern_generator
from app.services import calculator, describer, renderer

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("/generate", response_model=GenerateQuestionResponse)
def generate_question(
    pattern: PatternType | None = Query(default=None),
    difficulty: Difficulty = Query(default=Difficulty.SEDANG),
    seed: int | None = Query(default=None),
    # Advanced — Layer 1
    n_components: int | None = Query(default=None, ge=2, le=8, description="Override jumlah komponen"),
    r_min: float | None = Query(default=None, gt=0, description="Batas bawah nilai resistor (Ω)"),
    r_max: float | None = Query(default=None, gt=0, description="Batas atas nilai resistor (Ω)"),
    force_identical: bool | None = Query(default=None, description="Paksa/larang resistor identik"),
    # Advanced — Layer 2
    internal_resistance: float | None = Query(default=None, ge=0, description="Hambatan dalam sumber (Ω)"),
    show_power: bool = Query(default=False, description="Tampilkan daya per komponen"),
    unit_prefix: str | None = Query(default=None, regex="^(auto|base|kilo)$", description="Prefix satuan output"),
) -> GenerateQuestionResponse:

    resolved_seed = seed if seed is not None else random.randint(0, 2**31 - 1)

    if pattern is None:
        available_patterns = list(PATTERN_REGISTRY.keys())
        pattern = random.Random(resolved_seed).choice(available_patterns)

    try:
        generator = get_pattern_generator(pattern)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Kumpulkan advanced options hanya jika ada yang diisi
    advanced: Optional[AdvancedOptions] = None
    if any(v is not None for v in [n_components, r_min, r_max, force_identical, internal_resistance, unit_prefix]) or show_power:
        advanced = AdvancedOptions(
            n_components=n_components,
            r_min=r_min,
            r_max=r_max,
            force_identical=force_identical,
            internal_resistance=internal_resistance,
            show_power=show_power,
            unit_prefix=unit_prefix,
        )

    spec = generator.generate(difficulty=difficulty, seed=resolved_seed, advanced=advanced)

    svg = renderer.render_svg(spec)
    solution = calculator.solve(spec)
    llm_description = describer.describe_for_llm(spec)

    return GenerateQuestionResponse(
        spec=spec,
        svg=svg,
        solution=solution,
        llm_description=llm_description,
        show_power=show_power,
    )


@router.get("/patterns", response_model=list[PatternType])
def list_available_patterns() -> list[PatternType]:
    return list(PATTERN_REGISTRY.keys())