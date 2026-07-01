"""
Jembatan Wheatstone — pola topologi khusus.

Topologi standar yang dipakai:
        A ──R1── B ──R2── C
                 │
                 Rg          (galvanometer / resistor jembatan)
                 │
        A ──R3── D ──R4── C

Koneksi:
  A → B via R1, B → C via R2 (cabang atas)
  A → D via R3, D → C via R4 (cabang bawah)
  B → D via Rg (jembatan)

Sumber tegangan dari A (positif) ke C (negatif/GND).

Kondisi seimbang: R1/R2 = R3/R4
Saat seimbang: Ig = 0, R_total = (R1+R2) ∥ (R3+R4)

Representasi Branch rekursif:
  root = PARALLEL [
    SERIES [R1, R2],   # cabang atas
    SERIES [R3, R4],   # cabang bawah
  ]
  Rg disimpan sebagai metadata di source.label (karena tidak masuk Branch).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.patterns.base import PatternGenerator
from app.patterns.value_generator import pick_resistor_value, pick_voltage, get_internal_resistance

if TYPE_CHECKING:
    from app.api.schemas import AdvancedOptions


_DIFFICULTY_CONFIG: dict[Difficulty, dict] = {
    Difficulty.MUDAH:  {"balanced": True},
    Difficulty.SEDANG: {"balanced": True},
    Difficulty.SULIT:  {"balanced": False},
}


class WheatstoneBridgePattern(PatternGenerator):
    """Generator Jembatan Wheatstone.

    Mudah/Sedang: Bridge seimbang (R1/R2 = R3/R4 → Ig = 0).
      R_total = (R1+R2) ∥ (R3+R4) — dihitung oleh calculator standar.

    Sulit: Bridge tidak seimbang (5 nilai bebas).
      R_total dihitung dengan nodal analysis (solve_wheatstone).
    """

    pattern_type = PatternType.WHEATSTONE_BRIDGE

    def generate(
        self,
        difficulty: Difficulty,
        seed: int,
        advanced: "Optional[AdvancedOptions]" = None,
    ) -> CircuitSpec:
        rng = self._rng(seed)
        cfg = _DIFFICULTY_CONFIG[difficulty]

        if cfg["balanced"]:
            return self._generate_balanced(rng, difficulty, seed, advanced)
        else:
            return self._generate_unbalanced(rng, difficulty, seed, advanced)

    def _generate_balanced(self, rng, difficulty, seed, advanced) -> CircuitSpec:
        """Bridge seimbang: R1/R2 = R3/R4.

        Strategi: pilih R1, R2, dan faktor k ∈ {1,2,3}.
          R3 = k * R1, R4 = k * R2 → R3/R4 = R1/R2 ✓
        """
        from app.patterns.value_generator import _RESISTOR_POOLS
        pool = _RESISTOR_POOLS[difficulty]

        factor = rng.choice([1, 2, 3])
        base_pool = [v for v in pool if v * factor <= max(pool) * 3]
        if len(base_pool) < 2:
            base_pool = pool

        r1 = float(rng.choice(base_pool))
        r2 = float(rng.choice(base_pool))
        r3 = float(r1 * factor)
        r4 = float(r2 * factor)

        # Rg diabaikan kalkulasi (Ig=0), disimpan sebagai metadata
        rg = pick_resistor_value(rng, difficulty, advanced)

        branch_top = Branch(
            branch_type=BranchType.SERIES,
            elements=[Component(label="R1", value=r1), Component(label="R2", value=r2)],
        )
        branch_bot = Branch(
            branch_type=BranchType.SERIES,
            elements=[Component(label="R3", value=r3), Component(label="R4", value=r4)],
        )
        root = Branch(branch_type=BranchType.PARALLEL, elements=[branch_top, branch_bot])

        voltage = pick_voltage(rng, difficulty, advanced)
        source = VoltageSource(
            voltage=voltage,
            internal_resistance=get_internal_resistance(advanced),
        )

        return CircuitSpec(
            pattern=self.pattern_type,
            difficulty=difficulty,
            seed=seed,
            source=source,
            root=root,
            topology_meta={
                "galvanometer": {"label": "Rg", "value": rg, "unit": "Ω"},
                "balanced": True,
            },
        )

    def _generate_unbalanced(self, rng, difficulty, seed, advanced) -> CircuitSpec:
        """Bridge tidak seimbang: 5 nilai resistor bebas."""
        from app.patterns.value_generator import _RESISTOR_POOLS
        pool = _RESISTOR_POOLS[difficulty]

        r1, r2, r3, r4 = [float(rng.choice(pool)) for _ in range(4)]
        rg = float(rng.choice(pool))

        # Representasi Branch: dua cabang paralel (approx visual)
        branch_top = Branch(
            branch_type=BranchType.SERIES,
            elements=[Component(label="R1", value=r1), Component(label="R2", value=r2)],
        )
        branch_bot = Branch(
            branch_type=BranchType.SERIES,
            elements=[Component(label="R3", value=r3), Component(label="R4", value=r4)],
        )
        root = Branch(branch_type=BranchType.PARALLEL, elements=[branch_top, branch_bot])

        r_total = _wheatstone_resistance(r1, r2, r3, r4, rg)
        voltage = pick_voltage(rng, difficulty, advanced)
        source = VoltageSource(
            voltage=voltage,
            internal_resistance=get_internal_resistance(advanced),
        )

        return CircuitSpec(
            pattern=self.pattern_type,
            difficulty=difficulty,
            seed=seed,
            source=source,
            root=root,
            topology_meta={
                "galvanometer": {"label": "Rg", "value": rg, "unit": "Ω"},
                "balanced": False,
                "r_total_override": r_total,
            },
        )


def _wheatstone_resistance(r1: float, r2: float, r3: float, r4: float, rg: float) -> float:
    """Hitung hambatan total Jembatan Wheatstone dengan nodal analysis.

    Topologi:
        A --R1-- B --R2-- C
        A --R3-- D --R4-- C
        B --Rg-- D

    Set V_A = 1, V_C = 0. Unknowns: V_B, V_D.

    KCL di B: (1-VB)/R1 = VB/R2 + (VB-VD)/Rg
      → g1 = VB*(g1+g2+gg) - VD*gg
    KCL di D: (1-VD)/R3 + (VB-VD)/Rg = VD/R4
      → g3 = -VB*gg + VD*(g3+gg+g4)

    I_total = (1-VB)*g1 + (1-VD)*g3
    R_total = 1 / I_total
    """
    g1, g2, g3, g4, gg = 1/r1, 1/r2, 1/r3, 1/r4, 1/rg

    a = g1 + g2 + gg   # koefisien VB di persamaan 1
    b = -gg              # koefisien VD di persamaan 1
    c = -gg              # koefisien VB di persamaan 2
    d = g3 + gg + g4    # koefisien VD di persamaan 2
    e = g1               # RHS persamaan 1
    f = g3               # RHS persamaan 2

    det = a * d - b * c
    vb = (e * d - b * f) / det
    vd = (a * f - e * c) / det

    i_total = (1 - vb) * g1 + (1 - vd) * g3
    return 1.0 / i_total


def _wheatstone_node_voltages(r1: float, r2: float, r3: float, r4: float, rg: float, v_source: float):
    """Sama seperti _wheatstone_resistance, tapi mengembalikan V_B dan V_D
    aktual (dalam skala v_source, bukan dinormalisasi ke V_A=1) plus I_total.
    Dipakai untuk menghitung arus & tegangan tiap resistor pada bridge
    tidak seimbang."""
    g1, g2, g3, g4, gg = 1/r1, 1/r2, 1/r3, 1/r4, 1/rg

    a = g1 + g2 + gg
    b = -gg
    c = -gg
    d = g3 + gg + g4
    e = g1
    f = g3

    det = a * d - b * c
    vb_norm = (e * d - b * f) / det
    vd_norm = (a * f - e * c) / det

    vb = vb_norm * v_source
    vd = vd_norm * v_source
    i_total = (v_source - vb) * g1 + (v_source - vd) * g3

    return vb, vd, i_total


def solve_wheatstone(spec: CircuitSpec, unit_prefix=None):
    """Solver khusus untuk Jembatan Wheatstone TIDAK SEIMBANG.

    calculator.solve() standar TIDAK BOLEH dipakai untuk kasus ini — formula
    paralel sederhana (R1+R2)∥(R3+R4) hanya valid saat bridge balanced
    (Ig=0). Untuk unbalanced, arus mengalir lewat Rg sehingga R1-R4 tidak
    benar-benar dalam susunan seri-paralel murni; perlu nodal analysis.

    Untuk bridge SEIMBANG, fungsi ini tidak dipakai — calculator.solve()
    standar sudah benar karena Branch [R1 seri R2] ∥ [R3 seri R4] valid
    saat Ig=0.
    """
    from app.services.calculator import CircuitSolution, ComponentResult
    from app.services.unit_converter import resolve_unit_set, fmt_r, fmt_v, fmt_i

    meta = spec.topology_meta
    rg = meta["galvanometer"]["value"]
    comps = spec.all_components()  # urutan: R1, R2, R3, R4
    r1, r2, r3, r4 = [c.value for c in comps]

    v_source = spec.source.voltage
    vb, vd, i_total = _wheatstone_node_voltages(r1, r2, r3, r4, rg, v_source)

    i_r1 = (v_source - vb) / r1
    i_r2 = vb / r2
    i_r3 = (v_source - vd) / r3
    i_r4 = vd / r4

    v_r1 = i_r1 * r1
    v_r2 = i_r2 * r2
    v_r3 = i_r3 * r3
    v_r4 = i_r4 * r4

    r_total = meta["r_total_override"]
    units = resolve_unit_set(unit_prefix, r_total)

    def make_result(c: Component, voltage: float, current: float) -> ComponentResult:
        power = voltage * current
        return ComponentResult(
            component_id=c.id,
            label=c.label,
            resistance=c.value,
            voltage_drop=voltage,
            current=current,
            power=power,
            resistance_fmt=fmt_r(c.value, units),
            voltage_drop_fmt=fmt_v(voltage, units),
            current_fmt=fmt_i(current, units),
            power_fmt=f"{power:g} W",
        )

    label_to_result = {
        "R1": make_result(comps[0], v_r1, i_r1),
        "R2": make_result(comps[1], v_r2, i_r2),
        "R3": make_result(comps[2], v_r3, i_r3),
        "R4": make_result(comps[3], v_r4, i_r4),
    }
    ordered = [label_to_result[c.label] for c in comps]

    return CircuitSolution(
        total_resistance=r_total,
        total_current=i_total,
        source_voltage=v_source,
        component_results=ordered,
        unit_resistance=units.resistance,
        unit_current=units.current,
        unit_voltage=units.voltage,
    )
