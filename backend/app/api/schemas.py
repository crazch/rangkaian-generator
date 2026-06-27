"""Schema Pydantic untuk request/response endpoint API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.circuit_spec import CircuitSpec, Difficulty, PatternType
from app.services.calculator import CircuitSolution


class AdvancedOptions(BaseModel):
    """Opsi lanjutan untuk kontrol lebih detail atas soal yang digenerate.

    Semua field opsional — jika tidak diisi, value_generator memakai
    default per difficulty. Field ini melewati validasi di value_generator,
    bukan di generator pola, agar semua pola otomatis mendapat manfaatnya.
    """

    # Layer 1 — expose parameter yang sudah ada di backend
    n_components: Optional[int] = Field(
        default=None,
        ge=2,
        le=8,
        description="Override jumlah komponen. Jika None, ditentukan otomatis per difficulty.",
    )
    r_min: Optional[float] = Field(
        default=None,
        gt=0,
        description="Batas bawah nilai resistor (Ω). Harus < r_max jika keduanya diisi.",
    )
    r_max: Optional[float] = Field(
        default=None,
        gt=0,
        description="Batas atas nilai resistor (Ω). Harus > r_min jika keduanya diisi.",
    )
    force_identical: Optional[bool] = Field(
        default=None,
        description="True = paksa ada pasang resistor identik. False = tidak boleh identik. None = acak.",
    )

    # Layer 2 — fitur baru
    internal_resistance: Optional[float] = Field(
        default=None,
        ge=0,
        description="Hambatan dalam sumber tegangan (Ω). 0 = sumber ideal. Jika None, pakai 0.",
    )
    show_power: bool = Field(
        default=False,
        description="Jika True, tampilkan daya (P = V·I) per komponen di response.",
    )
    unit_prefix: Optional[str] = Field(
        default=None,
        description="Prefix satuan output: 'auto' (pilih otomatis), 'base' (Ω/A/V, default), 'kilo' (kΩ/mA/V).",
        pattern="^(auto|base|kilo)$",
    )


class GenerateQuestionResponse(BaseModel):
    """Response lengkap satu soal."""

    spec: CircuitSpec
    svg: str
    solution: CircuitSolution
    llm_description: str
    show_power: bool = Field(default=False, description="Apakah kolom daya perlu ditampilkan di frontend")


class GenerateQuestionRequest(BaseModel):
    """Parameter untuk men-generate soal. Semua field opsional."""

    pattern: Optional[PatternType] = None
    difficulty: Optional[Difficulty] = Field(default=Difficulty.SEDANG)
    seed: Optional[int] = None
    advanced: Optional[AdvancedOptions] = None