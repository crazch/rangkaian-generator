"""
Test suite untuk tiga pola baru:
  1. WheatstoneBridgePattern  — jembatan Wheatstone
  2. MultiLevelPattern        — seri-paralel bertingkat > 2 level
  3. MultiEMFPattern          — multi sumber tegangan

Setiap pola diuji:
  - Struktur topologi (tipe Branch, jumlah komponen, depth)
  - Reproduksibilitas seed (generate dua kali dengan seed sama → identik)
  - Semua difficulty tidak crash
  - Kalkulasi matematis (cross-check manual)
  - Registrasi di PATTERN_REGISTRY
"""

from __future__ import annotations

import math

import pytest

from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component, VoltageSource
from app.patterns.registry import PATTERN_REGISTRY, get_pattern_generator
from app.patterns.wheatstone_pattern import WheatstoneBridgePattern, _wheatstone_resistance
from app.patterns.multi_level_pattern import MultiLevelPattern
from app.patterns.multi_emf_pattern import MultiEMFPattern, solve_multi_emf
from app.services.calculator import solve


# ═══════════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════════

def _depth(node) -> int:
    """Hitung kedalaman pohon Branch (1 = hanya komponen tunggal)."""
    if isinstance(node, Component):
        return 0
    return 1 + max(_depth(el) for el in node.elements)


def _all_branch_types(node, acc=None) -> set:
    """Kumpulkan semua BranchType yang muncul di pohon."""
    if acc is None:
        acc = set()
    if isinstance(node, Branch):
        acc.add(node.branch_type)
        for el in node.elements:
            _all_branch_types(el, acc)
    return acc


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Registry
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistry:
    def test_all_new_patterns_registered(self):
        assert PatternType.WHEATSTONE_BRIDGE in PATTERN_REGISTRY
        assert PatternType.MULTI_LEVEL in PATTERN_REGISTRY
        assert PatternType.MULTI_EMF in PATTERN_REGISTRY

    def test_get_pattern_generator_wheatstone(self):
        gen = get_pattern_generator(PatternType.WHEATSTONE_BRIDGE)
        assert isinstance(gen, WheatstoneBridgePattern)

    def test_get_pattern_generator_multi_level(self):
        gen = get_pattern_generator(PatternType.MULTI_LEVEL)
        assert isinstance(gen, MultiLevelPattern)

    def test_get_pattern_generator_multi_emf(self):
        gen = get_pattern_generator(PatternType.MULTI_EMF)
        assert isinstance(gen, MultiEMFPattern)

    def test_total_patterns_count(self):
        """Pastikan semua 6 pola terdaftar (3 lama + 3 baru)."""
        assert len(PATTERN_REGISTRY) == 6


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Jembatan Wheatstone
# ═══════════════════════════════════════════════════════════════════════════════

class TestWheatstoneBridge:
    gen = WheatstoneBridgePattern()

    def test_pattern_type(self):
        spec = self.gen.generate(Difficulty.MUDAH, 0)
        assert spec.pattern == PatternType.WHEATSTONE_BRIDGE

    def test_root_is_parallel(self):
        """Root harus PARALLEL (dua cabang utama)."""
        for diff in Difficulty:
            spec = self.gen.generate(diff, 42)
            assert spec.root.branch_type == BranchType.PARALLEL

    def test_has_exactly_two_branches(self):
        """Root paralel harus punya tepat 2 cabang."""
        for diff in [Difficulty.MUDAH, Difficulty.SEDANG]:
            spec = self.gen.generate(diff, 7)
            assert len(spec.root.elements) == 2

    def test_each_branch_is_series(self):
        """Setiap cabang root harus SERIES (R1-R3 dan R2-R4)."""
        spec = self.gen.generate(Difficulty.MUDAH, 1)
        for branch in spec.root.elements:
            assert isinstance(branch, Branch)
            assert branch.branch_type == BranchType.SERIES

    def test_has_four_resistors_balanced(self):
        """Mudah/Sedang: 4 resistor (R1,R2,R3,R4) — tidak termasuk Rg."""
        for diff in [Difficulty.MUDAH, Difficulty.SEDANG]:
            spec = self.gen.generate(diff, 5)
            comps = spec.all_components()
            assert len(comps) == 4, f"Expected 4 resistors, got {len(comps)}"

    def test_balanced_condition_mudah(self):
        """Mudah: R1/R2 = R3/R4 (kondisi seimbang dalam topologi A--R1--B--R2--C, A--R3--D--R4--C)."""
        for seed in range(20):
            spec = self.gen.generate(Difficulty.MUDAH, seed)
            comps = spec.all_components()
            # Cabang atas: R1, R2; cabang bawah: R3, R4
            r1 = comps[0].value  # R1
            r2 = comps[1].value  # R2
            r3 = comps[2].value  # R3
            r4 = comps[3].value  # R4
            assert math.isclose(r1 / r2, r3 / r4, rel_tol=1e-6), \
                f"Jembatan tidak seimbang: R1/R2={r1/r2:.4f} ≠ R3/R4={r3/r4:.4f} (seed={seed})"

    def test_r_total_balanced_formula(self):
        """R_total balanced = (R1+R2) ∥ (R3+R4)."""
        spec = self.gen.generate(Difficulty.MUDAH, 3)
        comps = spec.all_components()
        r1, r2 = comps[0].value, comps[1].value
        r3, r4 = comps[2].value, comps[3].value

        expected = 1.0 / (1.0 / (r1 + r2) + 1.0 / (r3 + r4))
        from app.services.calculator import _equivalent_resistance
        actual = _equivalent_resistance(spec.root)
        assert math.isclose(actual, expected, rel_tol=1e-9)

    def test_seed_reproducibility(self):
        """Generate dua kali dengan seed sama → nilai komponen identik."""
        for diff in Difficulty:
            s1 = self.gen.generate(diff, 99)
            s2 = self.gen.generate(diff, 99)
            c1 = [c.value for c in s1.all_components()]
            c2 = [c.value for c in s2.all_components()]
            assert c1 == c2

    def test_all_difficulties_dont_crash(self):
        for diff in Difficulty:
            for seed in [0, 1, 42, 100]:
                spec = self.gen.generate(diff, seed)
                assert isinstance(spec, CircuitSpec)

    def test_source_voltage_positive(self):
        for diff in Difficulty:
            spec = self.gen.generate(diff, 0)
            assert spec.source.voltage > 0

    def test_rg_in_topology_meta(self):
        """Nilai Rg harus disimpan di topology_meta (bukan di-encode ke label)."""
        for diff in [Difficulty.MUDAH, Difficulty.SEDANG]:
            spec = self.gen.generate(diff, 10)
            assert "galvanometer" in spec.topology_meta
            assert spec.topology_meta["galvanometer"]["value"] > 0
            assert spec.topology_meta["balanced"] is True
            # Label sumber tetap bersih, tidak ada metadata mentah
            assert "|" not in spec.source.label


class TestWheatstoneMath:
    def test_balanced_bridge_rg_irrelevant(self):
        """Bridge seimbang (R1/R2=R3/R4): ubah Rg → R_total tidak berubah.
        Topologi: A--R1--B--R2--C, A--R3--D--R4--C, B--Rg--D.
        Balanced jika R1/R2 = R3/R4.
        """
        r1, r2, r3, r4 = 10.0, 20.0, 10.0, 20.0  # R1/R2 = R3/R4 = 0.5
        rg_values = [5.0, 50.0, 500.0, 0.001]
        results = [_wheatstone_resistance(r1, r2, r3, r4, rg) for rg in rg_values]
        for i in range(1, len(results)):
            assert math.isclose(results[0], results[i], rel_tol=1e-4), \
                f"R_total berubah dengan Rg: {results[0]:.4f} vs {results[i]:.4f}"

    def test_balanced_bridge_equals_parallel_formula(self):
        """Bridge seimbang: R_total = (R1+R2) ∥ (R3+R4)."""
        r1, r2, r3, r4 = 10.0, 20.0, 15.0, 30.0  # R1/R2 = R3/R4 = 0.5
        rg = 100.0
        expected = 1.0 / (1.0 / (r1 + r2) + 1.0 / (r3 + r4))
        actual = _wheatstone_resistance(r1, r2, r3, r4, rg)
        assert math.isclose(actual, expected, rel_tol=1e-4), \
            f"actual={actual:.4f}, expected={expected:.4f}"

    def test_all_equal_resistance(self):
        """Bridge simetri R1=R2=R3=R4=Rg=R: R_total = R.
        VB=VD=0.5V (simetri) → Ig=0. I_total=1/R. R_total=R.
        """
        r = 10.0
        result = _wheatstone_resistance(r, r, r, r, r)
        expected = r  # balanced: (2R)||(2R) = R
        assert math.isclose(result, expected, rel_tol=1e-6), \
            f"R_total = {result:.6f}, expected {expected:.6f}"

    def test_positive_resistance(self):
        """R_total selalu positif untuk semua nilai resistor positif."""
        import random as _random
        rng = _random.Random(777)
        for _ in range(50):
            vals = [float(rng.randint(5, 200)) for _ in range(5)]
            r = _wheatstone_resistance(*vals)
            assert r > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Multi-Level (seri-paralel bertingkat)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiLevel:
    gen = MultiLevelPattern()

    def test_pattern_type(self):
        spec = self.gen.generate(Difficulty.MUDAH, 0)
        assert spec.pattern == PatternType.MULTI_LEVEL

    def test_minimum_depth_is_3(self):
        """Semua varian harus punya kedalaman Branch ≥ 3."""
        for diff in Difficulty:
            for seed in range(30):
                spec = self.gen.generate(diff, seed)
                d = _depth(spec.root)
                assert d >= 3, f"Depth={d} pada diff={diff}, seed={seed}"

    def test_contains_both_branch_types(self):
        """Harus ada SERIES dan PARALLEL dalam pohon (bukan satu tipe saja)."""
        for diff in Difficulty:
            for seed in range(10):
                spec = self.gen.generate(diff, seed)
                types = _all_branch_types(spec.root)
                assert BranchType.SERIES in types, \
                    f"Tidak ada SERIES di diff={diff}, seed={seed}"
                assert BranchType.PARALLEL in types, \
                    f"Tidak ada PARALLEL di diff={diff}, seed={seed}"

    def test_component_count_mudah(self):
        """Varian A (mudah): 6 komponen."""
        spec = self.gen.generate(Difficulty.MUDAH, 0)
        # Mudah hanya punya varian A (6 komponen)
        assert len(spec.all_components()) == 6

    def test_component_count_sedang(self):
        """Sedang: varian A (6) atau B (6)."""
        for seed in range(20):
            spec = self.gen.generate(Difficulty.SEDANG, seed)
            n = len(spec.all_components())
            assert n == 6, f"Expected 6 components, got {n} (seed={seed})"

    def test_component_count_sulit(self):
        """Sulit: varian A (6), B (6), atau C (7)."""
        for seed in range(30):
            spec = self.gen.generate(Difficulty.SULIT, seed)
            n = len(spec.all_components())
            assert n in (6, 7), f"Expected 6 or 7 components, got {n} (seed={seed})"

    def test_sulit_has_variant_c_with_7_components(self):
        """Pastikan varian C (7 komponen) muncul setidaknya sekali dalam 50 seed."""
        found = any(
            len(self.gen.generate(Difficulty.SULIT, s).all_components()) == 7
            for s in range(50)
        )
        assert found, "Varian C (7 komponen) tidak pernah dipilih dalam 50 seed"

    def test_seed_reproducibility(self):
        for diff in Difficulty:
            s1 = self.gen.generate(diff, 123)
            s2 = self.gen.generate(diff, 123)
            assert [c.value for c in s1.all_components()] == \
                   [c.value for c in s2.all_components()]

    def test_all_components_have_positive_value(self):
        for diff in Difficulty:
            spec = self.gen.generate(diff, 55)
            for c in spec.all_components():
                assert c.value > 0

    def test_calculator_works_on_all_variants(self):
        """solve() tidak crash pada semua varian multi-level."""
        for diff in Difficulty:
            for seed in range(15):
                spec = self.gen.generate(diff, seed)
                sol = solve(spec)
                assert sol.total_resistance > 0
                assert sol.total_current > 0

    def test_variant_a_r_total_manual(self):
        """Variant A: R1 seri [ (R2 seri R3) ∥ (R4 seri R5) ] seri R6.
        Pilih seed yang menghasilkan varian A dan hitung secara manual.
        """
        # Cari seed yang menghasilkan varian A (root = SERIES)
        seed_a = None
        for s in range(50):
            spec = self.gen.generate(Difficulty.MUDAH, s)
            if spec.root.branch_type == BranchType.SERIES:
                seed_a = s
                break
        assert seed_a is not None, "Tidak ditemukan seed varian A"

        spec = self.gen.generate(Difficulty.MUDAH, seed_a)
        comps = spec.all_components()
        r1, r2, r3, r4, r5, r6 = [c.value for c in comps]

        # Manual: R23 = R2+R3, R45 = R4+R5, R_mid = R23∥R45
        r23 = r2 + r3
        r45 = r4 + r5
        r_mid = 1.0 / (1.0 / r23 + 1.0 / r45)
        r_total_expected = r1 + r_mid + r6

        sol = solve(spec)
        assert math.isclose(sol.total_resistance, r_total_expected, rel_tol=1e-9)

    def test_variant_b_r_total_manual(self):
        """Variant B: [ (R1∥R2) seri R3 ] ∥ [ R4 seri (R5∥R6) ].
        """
        # Cari seed yang menghasilkan varian B (root = PARALLEL)
        seed_b = None
        for s in range(50):
            spec = self.gen.generate(Difficulty.SEDANG, s)
            if spec.root.branch_type == BranchType.PARALLEL:
                seed_b = s
                break
        assert seed_b is not None, "Tidak ditemukan seed varian B"

        spec = self.gen.generate(Difficulty.SEDANG, seed_b)
        comps = spec.all_components()
        r1, r2, r3, r4, r5, r6 = [c.value for c in comps]

        # Manual
        r12 = 1.0 / (1.0 / r1 + 1.0 / r2)
        branch_left = r12 + r3
        r56 = 1.0 / (1.0 / r5 + 1.0 / r6)
        branch_right = r4 + r56
        r_total_expected = 1.0 / (1.0 / branch_left + 1.0 / branch_right)

        sol = solve(spec)
        assert math.isclose(sol.total_resistance, r_total_expected, rel_tol=1e-9)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Multi-EMF
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiEMF:
    gen = MultiEMFPattern()

    def test_pattern_type(self):
        spec = self.gen.generate(Difficulty.MUDAH, 0)
        assert spec.pattern == PatternType.MULTI_EMF

    def test_has_extra_source(self):
        """Harus ada tepat 1 sumber tegangan tambahan."""
        for diff in Difficulty:
            spec = self.gen.generate(diff, 7)
            assert len(spec.extra_sources) == 1

    def test_source_voltages_positive(self):
        for diff in Difficulty:
            spec = self.gen.generate(diff, 3)
            assert spec.source.voltage > 0
            assert spec.extra_sources[0].voltage > 0

    def test_seed_reproducibility(self):
        for diff in Difficulty:
            s1 = self.gen.generate(diff, 42)
            s2 = self.gen.generate(diff, 42)
            assert s1.source.voltage == s2.source.voltage
            assert s1.extra_sources[0].voltage == s2.extra_sources[0].voltage
            assert [c.value for c in s1.all_components()] == \
                   [c.value for c in s2.all_components()]

    def test_series_emf_polarity_field(self):
        """Field polarity V2 harus 'aiding' atau 'opposing' untuk mudah/sedang,
        dan label tetap bersih (tidak ada metadata di-encode ke string)."""
        for diff in [Difficulty.MUDAH, Difficulty.SEDANG]:
            for seed in range(20):
                spec = self.gen.generate(diff, seed)
                polarity = spec.extra_sources[0].polarity
                assert polarity in ("aiding", "opposing"), \
                    f"Polarity V2 tidak valid: {polarity}"
                assert "|" not in spec.extra_sources[0].label

    def test_both_aiding_and_opposing_appear(self):
        """Kedua konfigurasi harus muncul setidaknya sekali dalam 30 seed."""
        aiding_seen = False
        opposing_seen = False
        for seed in range(30):
            spec = self.gen.generate(Difficulty.MUDAH, seed)
            polarity = spec.extra_sources[0].polarity
            if polarity == "aiding":
                aiding_seen = True
            if polarity == "opposing":
                opposing_seen = True
        assert aiding_seen, "Konfigurasi aiding tidak pernah muncul"
        assert opposing_seen, "Konfigurasi opposing tidak pernah muncul"

    def test_sulit_uses_series_root(self):
        """Sulit (mesh): root harus SERIES (R1-R2-R3 linear untuk render)."""
        for seed in range(10):
            spec = self.gen.generate(Difficulty.SULIT, seed)
            assert spec.root.branch_type == BranchType.SERIES

    def test_sulit_has_three_resistors(self):
        """Sulit (mesh): R1, R2, R3."""
        for seed in range(10):
            spec = self.gen.generate(Difficulty.SULIT, seed)
            comps = spec.all_components()
            assert len(comps) == 3

    def test_all_difficulties_dont_crash(self):
        for diff in Difficulty:
            for seed in [0, 1, 50, 99]:
                spec = self.gen.generate(diff, seed)
                assert isinstance(spec, CircuitSpec)


class TestMultiEMFSolver:
    gen = MultiEMFPattern()

    def test_solve_multi_emf_aiding(self):
        """Aiding: I = (V1+V2) / R_total."""
        # Buat spec aiding secara manual
        root = Branch(
            branch_type=BranchType.SERIES,
            elements=[Component(label="R1", value=10.0), Component(label="R2", value=20.0)],
        )
        spec = CircuitSpec(
            pattern=PatternType.MULTI_EMF,
            difficulty=Difficulty.MUDAH,
            seed=0,
            source=VoltageSource(label="V1", voltage=12.0),
            extra_sources=[VoltageSource(label="V2", voltage=6.0, polarity="aiding")],
            root=root,
        )
        sol = solve_multi_emf(spec)
        # V_eff = 12 + 6 = 18, R = 30, I = 0.6
        assert math.isclose(sol.total_current, 0.6, rel_tol=1e-9)
        assert math.isclose(sol.source_voltage, 18.0)

    def test_solve_multi_emf_opposing(self):
        """Opposing: I = |V1 - V2| / R_total."""
        root = Branch(
            branch_type=BranchType.SERIES,
            elements=[Component(label="R1", value=10.0), Component(label="R2", value=15.0)],
        )
        spec = CircuitSpec(
            pattern=PatternType.MULTI_EMF,
            difficulty=Difficulty.SEDANG,
            seed=0,
            source=VoltageSource(label="V1", voltage=12.0),
            extra_sources=[VoltageSource(label="V2", voltage=6.0, polarity="opposing")],
            root=root,
        )
        sol = solve_multi_emf(spec)
        # V_eff = |12 - 6| = 6, R = 25, I = 0.24
        assert math.isclose(sol.total_current, 0.24, rel_tol=1e-9)
        assert math.isclose(sol.source_voltage, 6.0)

    def test_solve_multi_emf_mesh_kirchhoff(self):
        """Mesh: I1 dan I2 dari Kirchhoff, I_R3 = |I1 - I2|.

        Contoh: R1=10, R2=20, R3=5, V1=12, V2=6
          [R1+R3,  -R3  ] [I1]   [V1]   [15, -5 ] [I1]   [12]
          [-R3,  R2+R3  ] [I2] = [V2] → [-5,  25] [I2] = [6 ]
          det = 15*25 - (-5)(-5) = 375 - 25 = 350
          I1 = (12*25 - (-5)*6) / 350 = (300 + 30) / 350 = 330/350 ≈ 0.9429
          I2 = (15*6 - 12*(-5)) / 350 = (90 + 60) / 350 = 150/350 ≈ 0.4286
        """
        r1, r2, r3 = 10.0, 20.0, 5.0
        v1, v2 = 12.0, 6.0

        # Buat spec mesh secara manual — root SERIES R1-R2-R3 (sesuai generator)
        root = Branch(
            branch_type=BranchType.SERIES,
            elements=[
                Component(label="R1", value=r1),
                Component(label="R2", value=r2),
                Component(label="R3", value=r3),
            ],
        )

        spec = CircuitSpec(
            pattern=PatternType.MULTI_EMF,
            difficulty=Difficulty.SULIT,
            seed=0,
            source=VoltageSource(label="V1", voltage=v1),
            extra_sources=[VoltageSource(label="V2", voltage=v2)],
            root=root,
            topology_meta={"mesh": True, "shared_resistor_label": "R3"},
        )
        sol = solve_multi_emf(spec)

        # Manual Kirchhoff
        a, b, c, d = r1 + r3, -r3, -r3, r2 + r3
        det = a * d - b * c
        i1 = (v1 * d - b * v2) / det
        i2 = (a * v2 - v1 * c) / det

        assert math.isclose(sol.total_current, max(i1, i2), rel_tol=1e-6)

    def test_solve_multi_emf_voltage_conservation_aiding(self):
        """KVL: jumlah V_drop komponen = V_eff (aiding)."""
        root = Branch(
            branch_type=BranchType.SERIES,
            elements=[
                Component(label="R1", value=10.0),
                Component(label="R2", value=20.0),
                Component(label="R3", value=30.0),
            ],
        )
        spec = CircuitSpec(
            pattern=PatternType.MULTI_EMF,
            difficulty=Difficulty.MUDAH,
            seed=0,
            source=VoltageSource(label="V1", voltage=9.0),
            extra_sources=[VoltageSource(label="V2", voltage=3.0, polarity="aiding")],
            root=root,
        )
        sol = solve_multi_emf(spec)
        total_drop = sum(c.voltage_drop for c in sol.component_results)
        # V_eff = 12, R=60, I=0.2, total drop = 12
        assert math.isclose(total_drop, sol.source_voltage, rel_tol=1e-9)

    def test_solver_generator_consistency(self):
        """solve_multi_emf pada spec yang di-generate tidak crash."""
        for diff in Difficulty:
            for seed in range(10):
                spec = self.gen.generate(diff, seed)
                sol = solve_multi_emf(spec)
                assert sol.total_resistance > 0 or diff == Difficulty.SULIT
                assert len(sol.component_results) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Cross-pattern sanity check
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossPatternSanity:
    """Pastikan semua pola baru menghasilkan CircuitSpec valid."""

    @pytest.mark.parametrize("pattern_type", [
        PatternType.WHEATSTONE_BRIDGE,
        PatternType.MULTI_LEVEL,
        PatternType.MULTI_EMF,
    ])
    @pytest.mark.parametrize("difficulty", list(Difficulty))
    def test_generate_returns_valid_spec(self, pattern_type, difficulty):
        gen = get_pattern_generator(pattern_type)
        spec = gen.generate(difficulty, seed=42)
        assert isinstance(spec, CircuitSpec)
        assert spec.pattern == pattern_type
        assert spec.difficulty == difficulty
        assert spec.seed == 42
        assert spec.source.voltage > 0
        assert len(spec.all_components()) >= 2

    @pytest.mark.parametrize("pattern_type", [
        PatternType.WHEATSTONE_BRIDGE,
        PatternType.MULTI_LEVEL,
    ])
    def test_calculator_solve_does_not_crash(self, pattern_type):
        """solve() standar harus bekerja pada Wheatstone dan MultiLevel."""
        gen = get_pattern_generator(pattern_type)
        for diff in Difficulty:
            for seed in range(5):
                spec = gen.generate(diff, seed)
                sol = solve(spec)
                assert sol.total_resistance > 0
                assert sol.total_current > 0
                assert len(sol.component_results) >= 2

    def test_all_components_labels_unique_per_spec(self):
        """Label komponen (R1, R2, ...) harus unik dalam satu spec."""
        for pt in [PatternType.WHEATSTONE_BRIDGE, PatternType.MULTI_LEVEL, PatternType.MULTI_EMF]:
            gen = get_pattern_generator(pt)
            for diff in Difficulty:
                spec = gen.generate(diff, 77)
                labels = [c.label for c in spec.all_components()]
                assert len(labels) == len(set(labels)), \
                    f"Label duplikat di {pt}, {diff}: {labels}"

    def test_schema_version_is_1(self):
        for pt in [PatternType.WHEATSTONE_BRIDGE, PatternType.MULTI_LEVEL, PatternType.MULTI_EMF]:
            gen = get_pattern_generator(pt)
            spec = gen.generate(Difficulty.SEDANG, 0)
            assert spec.schema_version == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Full pipeline via HTTP endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestNewPatternsEndpoint:
    """Pastikan ketiga pola baru bekerja end-to-end lewat endpoint FastAPI
    (generator → renderer SVG → calculator/solve_multi_emf → describer)."""

    @pytest.fixture(autouse=True)
    def _client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    @pytest.mark.parametrize("pattern", ["wheatstone_bridge", "multi_level", "multi_emf"])
    @pytest.mark.parametrize("difficulty", ["mudah", "sedang", "sulit"])
    def test_generate_endpoint_succeeds(self, pattern, difficulty):
        r = self.client.get(
            "/api/questions/generate",
            params={"pattern": pattern, "difficulty": difficulty, "seed": 1},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "svg" in data and len(data["svg"]) > 0
        assert "solution" in data
        assert data["solution"]["total_current"] > 0
        assert "llm_description" in data and len(data["llm_description"]) > 0

    def test_multi_emf_uses_dedicated_solver_via_endpoint(self):
        """Multi-EMF endpoint harus memakai solve_multi_emf (bukan calculator.solve
        standar) — terdeteksi dari source_voltage = V_eff (bukan V1 mentah saja)."""
        r = self.client.get(
            "/api/questions/generate",
            params={"pattern": "multi_emf", "difficulty": "mudah", "seed": 5},
        )
        assert r.status_code == 200
        data = r.json()
        spec = data["spec"]
        solution = data["solution"]
        v1 = spec["source"]["voltage"]
        v2 = spec["extra_sources"][0]["voltage"]
        is_aiding = spec["extra_sources"][0]["polarity"] == "aiding"
        expected_v_eff = (v1 + v2) if is_aiding else abs(v1 - v2)
        assert solution["source_voltage"] == pytest.approx(expected_v_eff)

    def test_new_patterns_listed_in_patterns_endpoint(self):
        r = self.client.get("/api/questions/patterns")
        assert r.status_code == 200
        patterns = r.json()
        assert "wheatstone_bridge" in patterns
        assert "multi_level" in patterns
        assert "multi_emf" in patterns

    def test_unbalanced_wheatstone_uses_dedicated_solver_via_endpoint(self):
        """Bridge tidak seimbang (Sulit) harus pakai solve_wheatstone (nodal
        analysis) lewat endpoint, BUKAN calculator.solve() standar — formula
        paralel naif (R1+R2)||(R3+R4) salah saat ada arus lewat Rg."""
        r = self.client.get(
            "/api/questions/generate",
            params={"pattern": "wheatstone_bridge", "difficulty": "sulit", "seed": 3},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["spec"]["topology_meta"]["balanced"] is False
        expected = data["spec"]["topology_meta"]["r_total_override"]
        actual = data["solution"]["total_resistance"]
        assert actual == pytest.approx(expected, rel=1e-9), \
            f"Endpoint R_total={actual} tidak cocok dengan nodal solution={expected}"

    def test_balanced_wheatstone_topology_meta_in_response(self):
        """Bridge seimbang (Mudah/Sedang) harus menyertakan topology_meta.galvanometer
        di response agar frontend bisa tampilkan Rg secara terpisah."""
        r = self.client.get(
            "/api/questions/generate",
            params={"pattern": "wheatstone_bridge", "difficulty": "mudah", "seed": 1},
        )
        data = r.json()
        assert data["spec"]["topology_meta"]["balanced"] is True
        assert "galvanometer" in data["spec"]["topology_meta"]
        assert data["spec"]["topology_meta"]["galvanometer"]["value"] > 0
        # Label sumber harus bersih (tidak ada metadata di-encode ke string)
        assert "|" not in data["spec"]["source"]["label"]


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Renderer regression tests (crash fixes)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRendererRegressions:
    """Tes regresi untuk bug renderer yang sudah diperbaiki.
    Semua test di sini pernah crash di production — jangan hapus."""

    def test_multi_level_parallel_in_parallel_no_crash(self):
        """Regresi: schemdraw move_from() crash saat nested parallel (depth>=3).

        Bug: d.here setelah move_from() adalah plain tuple, bukan Point.
        Panggilan move_from() berikutnya mencoba tuple.x → AttributeError.
        Fix: bungkus d.here dengan Point() sebelum dipakai sebagai anchor.

        Terjadi pada varian B multi_level (root=PARALLEL, berisi SERIES yang
        berisi sub-PARALLEL) — terpicu di sedang/sulit tapi TIDAK di mudah
        (mudah hanya punya varian A yang root=SERIES).
        """
        from app.services.renderer import render_svg
        gen = get_pattern_generator(PatternType.MULTI_LEVEL)

        # Pastikan SEMUA seed dan difficulty tidak crash
        for diff in Difficulty:
            for seed in range(30):
                spec = gen.generate(diff, seed)
                try:
                    svg = render_svg(spec)
                    assert len(svg) > 0
                except AttributeError as e:
                    pytest.fail(
                        f"Renderer crash (tuple .x bug) di multi_level "
                        f"diff={diff.value} seed={seed}: {e}"
                    )

    def test_multi_level_variant_b_specifically(self):
        """Varian B (root=PARALLEL) adalah yang paling rentan terhadap bug ini
        karena menghasilkan 3 level nested (PARALLEL > SERIES > PARALLEL).
        Pastikan setidaknya 5 seed varian B di-render tanpa crash."""
        from app.services.renderer import render_svg
        gen = get_pattern_generator(PatternType.MULTI_LEVEL)

        variant_b_count = 0
        for seed in range(100):
            spec = gen.generate(Difficulty.SEDANG, seed)
            if spec.root.branch_type == BranchType.PARALLEL:
                svg = render_svg(spec)
                assert len(svg) > 0
                variant_b_count += 1
                if variant_b_count >= 5:
                    break

        assert variant_b_count >= 5, "Tidak cukup varian B ditemukan untuk tes regresi"

    def test_all_new_patterns_render_without_crash(self):
        """Semua pola baru harus bisa di-render untuk semua difficulty."""
        from app.services.renderer import render_svg
        for pt in [PatternType.WHEATSTONE_BRIDGE, PatternType.MULTI_LEVEL, PatternType.MULTI_EMF]:
            gen = get_pattern_generator(pt)
            for diff in Difficulty:
                for seed in range(10):
                    spec = gen.generate(diff, seed)
                    svg = render_svg(spec)
                    assert len(svg) > 0, f"SVG kosong: {pt.value}/{diff.value}/seed={seed}"

    def test_multi_emf_v2_appears_in_svg(self):
        """V2 (sumber kedua) harus muncul di dalam SVG untuk pola multi_emf."""
        from app.services.renderer import render_svg
        gen = get_pattern_generator(PatternType.MULTI_EMF)
        for diff in Difficulty:
            spec = gen.generate(diff, seed=1)
            svg = render_svg(spec)
            assert "V2" in svg, \
                f"V2 tidak muncul di SVG multi_emf/{diff.value}"

    def test_multi_emf_polarity_in_svg(self):
        """Label polaritas (searah/lawan) harus muncul di SVG saat extra_sources
        punya polarity field."""
        from app.services.renderer import render_svg
        gen = get_pattern_generator(PatternType.MULTI_EMF)

        aiding_found = False
        opposing_found = False
        for seed in range(30):
            spec = gen.generate(Difficulty.MUDAH, seed)
            svg = render_svg(spec)
            if "searah" in svg:
                aiding_found = True
            if "lawan" in svg:
                opposing_found = True
        assert aiding_found, "Label 'searah' tidak pernah muncul di SVG"
        assert opposing_found, "Label 'lawan' tidak pernah muncul di SVG"


class TestDescriberCompleteness:
    """Pastikan describer menyebut semua informasi relevan per pola."""

    def test_multi_emf_v2_in_description(self):
        """V2 harus selalu disebut di deskripsi soal multi-EMF."""
        from app.services.describer import describe_for_llm
        gen = get_pattern_generator(PatternType.MULTI_EMF)
        for diff in Difficulty:
            for seed in range(10):
                spec = gen.generate(diff, seed)
                desc = describe_for_llm(spec)
                assert "V2" in desc, \
                    f"V2 tidak ada di deskripsi multi_emf/{diff.value}/seed={seed}"

    def test_multi_emf_veff_formula_in_description(self):
        """Formula V_eff harus muncul di deskripsi aiding/opposing."""
        from app.services.describer import describe_for_llm
        gen = get_pattern_generator(PatternType.MULTI_EMF)

        for seed in range(30):
            spec = gen.generate(Difficulty.MUDAH, seed)
            desc = describe_for_llm(spec)
            pol = spec.extra_sources[0].polarity
            if pol == "aiding":
                assert "V_eff" in desc and "+" in desc
            elif pol == "opposing":
                assert "V_eff" in desc and "−" in desc

    def test_wheatstone_rg_in_description(self):
        """Rg harus disebut di deskripsi Wheatstone (balanced maupun tidak)."""
        from app.services.describer import describe_for_llm
        gen = get_pattern_generator(PatternType.WHEATSTONE_BRIDGE)
        for diff in Difficulty:
            spec = gen.generate(diff, seed=5)
            desc = describe_for_llm(spec)
            assert "Rg" in desc, \
                f"Rg tidak ada di deskripsi wheatstone/{diff.value}"

    def test_wheatstone_balanced_flag_in_description(self):
        """Status seimbang/tidak seimbang harus eksplisit di deskripsi."""
        from app.services.describer import describe_for_llm
        gen = get_pattern_generator(PatternType.WHEATSTONE_BRIDGE)

        spec_bal = gen.generate(Difficulty.MUDAH, seed=1)
        assert "seimbang" in describe_for_llm(spec_bal)

        spec_unbal = gen.generate(Difficulty.SULIT, seed=1)
        assert "tidak seimbang" in describe_for_llm(spec_unbal)

    def test_old_patterns_describer_not_broken(self):
        """Pola lama (series/parallel/mixed) harus tetap menghasilkan deskripsi
        yang valid setelah refaktor describer."""
        from app.services.describer import describe_for_llm
        for pt in [PatternType.SERIES_SIMPLE, PatternType.PARALLEL_SIMPLE, PatternType.MIXED_BASIC]:
            gen = get_pattern_generator(pt)
            for diff in Difficulty:
                spec = gen.generate(diff, seed=42)
                desc = describe_for_llm(spec)
                assert len(desc) > 100
                assert spec.source.label in desc
                assert f"{spec.source.voltage:g}" in desc
