"""
Rangkaian dengan lebih dari satu sumber tegangan (Multi-EMF).

Topologi yang didukung:
- Dua sumber tegangan searah (aiding) dalam rangkaian seri
- Dua sumber tegangan berlawanan arah (opposing) dalam rangkaian seri
- Sumber tegangan di cabang paralel (masing-masing cabang punya EMF sendiri)

Hukum yang dipakai: Hukum Kirchhoff Tegangan (KVT / KVL).

Untuk topologi seri multi-EMF:
    V_eff = ΣV_i (aiding) atau V1 - V2 (opposing)
    I = V_eff / R_total

Untuk topologi cabang paralel dengan EMF berbeda:
    Gunakan metode superposisi atau mesh analysis.

Arsitektur: pola ini tetap menghasilkan CircuitSpec standar dengan
field `extra_sources` terisi. Calculator.solve() yang sudah ada TIDAK
dimodifikasi — MultiEMF punya solve_multi_emf() tersendiri.

`source` di CircuitSpec = sumber tegangan utama (EMF1).
`extra_sources` = daftar sumber tegangan tambahan.

Untuk mudah/sedang: topologi seri, V_eff = V1 + V2 atau |V1 - V2|.
Untuk sulit: topologi mesh dua loop (dua sumber di cabang berbeda).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.patterns.base import PatternGenerator
from app.patterns.value_generator import (
    pick_resistor_value, pick_n_components, pick_voltage,
    get_internal_resistance, _RESISTOR_POOLS, _VOLTAGE_POOLS
)
from app.services.calculator import CircuitSolution, ComponentResult
from app.services.unit_converter import resolve_unit_set, fmt_r, fmt_v, fmt_i

if TYPE_CHECKING:
    from app.api.schemas import AdvancedOptions


class MultiEMFPattern(PatternGenerator):
    """Generator rangkaian multi sumber tegangan (multi-EMF).

    Mudah/Sedang: dua EMF seri (aiding atau opposing).
    Sulit: dua EMF di dua cabang terpisah (mesh analysis 2-loop).
    """

    pattern_type = PatternType.MULTI_EMF

    def generate(
        self,
        difficulty: Difficulty,
        seed: int,
        advanced: "Optional[AdvancedOptions]" = None,
    ) -> CircuitSpec:
        rng = self._rng(seed)

        if difficulty == Difficulty.SULIT:
            return self._generate_mesh(rng, difficulty, seed, advanced)
        else:
            return self._generate_series_emf(rng, difficulty, seed, advanced)

    # ──────────────────────────────────────────────────────────────────────
    # Seri multi-EMF (mudah / sedang)
    # ──────────────────────────────────────────────────────────────────────

    def _generate_series_emf(self, rng, difficulty, seed, advanced) -> CircuitSpec:
        """
        Topologi: EMF1 dan EMF2 dalam rangkaian seri bersama resistor.

        Konfigurasi dipilih acak:
        - aiding (searah): V_eff = V1 + V2
        - opposing (berlawanan): V_eff = |V1 - V2| (pastikan V1 > V2)
        """
        n = pick_n_components(rng, difficulty, advanced)
        values = [pick_resistor_value(rng, difficulty, advanced) for _ in range(n)]
        components = [Component(label=f"R{i+1}", value=v) for i, v in enumerate(values)]

        root = Branch(branch_type=BranchType.SERIES, elements=components)

        v_pool = _VOLTAGE_POOLS[difficulty]
        v1 = float(rng.choice(v_pool))
        v2 = float(rng.choice(v_pool))

        # Pastikan tidak kebetulan sama (soal trivial)
        while v2 == v1:
            v2 = float(rng.choice(v_pool))

        # Pilih konfigurasi: aiding atau opposing
        is_aiding = rng.choice([True, False])

        if not is_aiding and v2 > v1:
            v1, v2 = v2, v1  # v1 selalu lebih besar untuk opposing

        r_in1 = get_internal_resistance(advanced)
        r_in2 = get_internal_resistance(advanced)

        source1 = VoltageSource(
            label="V1",
            voltage=v1,
            internal_resistance=r_in1,
        )
        source2 = VoltageSource(
            label="V2",
            voltage=v2,
            internal_resistance=r_in2,
            polarity="aiding" if is_aiding else "opposing",
        )

        return CircuitSpec(
            pattern=self.pattern_type,
            difficulty=difficulty,
            seed=seed,
            source=source1,
            extra_sources=[source2],
            root=root,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Mesh dua loop (sulit)
    # ──────────────────────────────────────────────────────────────────────

    def _generate_mesh(self, rng, difficulty, seed, advanced) -> CircuitSpec:
        """
        Topologi dua loop mesh:

            +V1-      R1       R2     -V2+
            |──────────────────────────|
            |          R3              |
            |──────────────────────────|

        Loop 1 (kiri): V1, R1, R3
        Loop 2 (kanan): V2, R2, R3 (berlawanan arah)

        Diselesaikan dengan Kirchhoff mesh analysis:
            I1*(R1+R3) - I2*R3 = V1
           -I1*R3 + I2*(R2+R3) = V2

        Representasi Branch: seri R1-R2-R3 (topologi linear untuk render).
        R3 adalah resistor bersama yang dikenai arus superposisi I1-I2.
        """
        pool = _RESISTOR_POOLS[difficulty]
        r1, r2, r3 = [float(rng.choice(pool)) for _ in range(3)]

        v_pool = _VOLTAGE_POOLS[difficulty]
        v1 = float(rng.choice(v_pool))
        v2 = float(rng.choice(v_pool))
        while v2 == v1:
            v2 = float(rng.choice(v_pool))

        # Representasi Branch: SERIES R1-R2-R3 (paling sederhana dan valid)
        # R3 = resistor bersama; solver mesh akan menggunakan metadata label
        root = Branch(
            branch_type=BranchType.SERIES,
            elements=[
                Component(label="R1", value=r1),
                Component(label="R2", value=r2),
                Component(label="R3", value=r3),
            ],
        )

        source1 = VoltageSource(
            label="V1",
            voltage=v1,
            internal_resistance=get_internal_resistance(advanced),
        )
        source2 = VoltageSource(
            label="V2",
            voltage=v2,
            internal_resistance=get_internal_resistance(advanced),
        )

        return CircuitSpec(
            pattern=self.pattern_type,
            difficulty=difficulty,
            seed=seed,
            source=source1,
            extra_sources=[source2],
            root=root,
            topology_meta={
                "mesh": True,
                "shared_resistor_label": "R3",
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# Solver khusus multi-EMF
# ──────────────────────────────────────────────────────────────────────────────

def solve_multi_emf(spec: CircuitSpec, unit_prefix: Optional[str] = None) -> CircuitSolution:
    """Hitung solusi lengkap untuk rangkaian multi-EMF.

    Mendukung:
    1. Seri aiding/opposing: V_eff = V1 ± V2, I = V_eff / R_total
    2. Mesh 2-loop: diselesaikan dengan Kirchhoff mesh analysis

    Mengembalikan CircuitSolution standar agar compatible dengan endpoint yang ada.
    """
    if not spec.extra_sources:
        # Fallback ke calculator biasa
        from app.services.calculator import solve
        return solve(spec, unit_prefix)

    source2 = spec.extra_sources[0]

    if spec.difficulty != Difficulty.SULIT:
        return _solve_series_emf(spec, source2, unit_prefix)
    else:
        return _solve_mesh_emf(spec, source2, unit_prefix)


def _solve_series_emf(spec: CircuitSpec, source2: VoltageSource, unit_prefix) -> CircuitSolution:
    """Solver untuk multi-EMF seri (aiding atau opposing)."""
    from app.services.calculator import _equivalent_resistance, _resolve_branch

    is_aiding = source2.polarity == "aiding"

    v1 = spec.source.voltage
    v2 = source2.voltage
    r_in1 = spec.source.internal_resistance
    r_in2 = source2.internal_resistance

    v_eff = (v1 + v2) if is_aiding else abs(v1 - v2)
    r_total_resistor = _equivalent_resistance(spec.root)
    r_total = r_total_resistor + r_in1 + r_in2

    total_current = v_eff / r_total if r_total > 0 else 0.0
    voltage_across_circuit = total_current * r_total_resistor

    units = resolve_unit_set(unit_prefix, r_total_resistor)
    results = {}
    _resolve_branch(spec.root, voltage_across_circuit, results, units)

    ordered = [results[c.id] for c in spec.all_components()]

    return CircuitSolution(
        total_resistance=r_total_resistor,
        total_current=total_current,
        source_voltage=v_eff,
        component_results=ordered,
        unit_resistance=units.resistance,
        unit_current=units.current,
        unit_voltage=units.voltage,
    )


def _solve_mesh_emf(spec: CircuitSpec, source2: VoltageSource, unit_prefix) -> CircuitSolution:
    """Solver untuk mesh 2-loop.

    Ekstrak R1, R2, R3 dari spec.root. Selesaikan:
        I1*(R1+R3) - I2*R3 = V1
       -I1*R3 + I2*(R2+R3) = V2

    I total di R3 = I1 - I2 (atau I2 - I1, tergantung konvensi).
    """
    # Ekstrak R3 dari komponen (label sudah dijamin "R3" oleh generator,
    # diverifikasi via topology_meta agar tidak diam-diam memakai fallback salah)
    comps = spec.all_components()
    r3_comp = next((c for c in comps if c.label == spec.topology_meta.get("shared_resistor_label", "R3")), None)
    if r3_comp is None:
        # Fallback aman: ambil komponen terakhir jika label tidak ditemukan
        r3 = comps[-1].value if len(comps) >= 3 else 10.0
    else:
        r3 = r3_comp.value
    r1 = comps[0].value if len(comps) >= 1 else 10.0
    r2 = comps[1].value if len(comps) >= 2 else 10.0

    v1 = spec.source.voltage
    v2 = source2.voltage

    # Mesh analysis:
    # [R1+R3,  -R3  ] [I1]   [V1]
    # [-R3,  R2+R3  ] [I2] = [V2]
    a = r1 + r3
    b = -r3
    c = -r3
    d = r2 + r3
    det = a * d - b * c

    i1 = (v1 * d - b * v2) / det
    i2 = (a * v2 - v1 * c) / det

    # Arus di tiap resistor
    i_r1 = i1
    i_r2 = i2
    i_r3 = abs(i1 - i2)

    v_r1 = i_r1 * r1
    v_r2 = i_r2 * r2
    v_r3 = i_r3 * r3

    r_total_eff = r1 * r2 / (r1 + r2) if (r1 + r2) > 0 else r1  # approx untuk unit display
    units = resolve_unit_set(unit_prefix, max(r1, r2, r3))

    def make_result(c: Component, voltage: float, current: float) -> ComponentResult:
        return ComponentResult(
            component_id=c.id,
            label=c.label,
            resistance=c.value,
            voltage_drop=voltage,
            current=current,
            power=voltage * current,
            resistance_fmt=fmt_r(c.value, units),
            voltage_drop_fmt=fmt_v(voltage, units),
            current_fmt=fmt_i(current, units),
            power_fmt=f"{voltage * current:g} W",
        )

    r1_comp = next((c for c in comps if c.label == "R1"), comps[0])
    r2_comp = next((c for c in comps if c.label == "R2"), comps[1] if len(comps) > 1 else comps[0])
    r3_comp = next((c for c in comps if c.label == "R3"), None)

    results = [
        make_result(r1_comp, v_r1, i_r1),
        make_result(r2_comp, v_r2, i_r2),
    ]
    if r3_comp:
        results.append(make_result(r3_comp, v_r3, i_r3))

    return CircuitSolution(
        total_resistance=r_total_eff,
        total_current=max(i1, i2),
        source_voltage=v1,
        component_results=results,
        unit_resistance=units.resistance,
        unit_current=units.current,
        unit_voltage=units.voltage,
    )
