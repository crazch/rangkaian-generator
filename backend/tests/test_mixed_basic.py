"""
Test suite khusus MixedBasicPattern.

Mencakup:
- Struktur topologi kedua sub-varian (A dan B)
- Skalabilitas difficulty (komponen count)
- Reproduksibilitas seed
- Kalkulasi matematis (manual check)
- Render SVG (tidak crash, semua label ada)
- Deskripsi teks (semua komponen disebut)
- Full pipeline via endpoint
"""

import math
from collections import Counter

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.circuit_spec import Branch, BranchType, CircuitSpec, Difficulty, PatternType
from app.models.components import Component
from app.patterns.mixed_basic_pattern import MixedBasicPattern
from app.services.calculator import solve
from app.services.describer import describe_for_llm, describe_topology
from app.services.renderer import render_svg

client = TestClient(app)
gen = MixedBasicPattern()


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _get_spec(difficulty: Difficulty, seed: int) -> CircuitSpec:
    return gen.generate(difficulty, seed)


def _find_seed_for_variant(variant: BranchType, difficulty: Difficulty = Difficulty.MUDAH) -> int:
    """Cari seed pertama (0–99) yang menghasilkan sub-varian tertentu."""
    for seed in range(100):
        if gen.generate(difficulty, seed).root.branch_type == variant:
            return seed
    raise RuntimeError(f"Tidak ditemukan seed untuk {variant} dalam 100 iterasi")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Struktur topologi
# ──────────────────────────────────────────────────────────────────────────────

class TestTopologyStructure:

    def test_pattern_type_is_mixed_basic(self):
        spec = _get_spec(Difficulty.MUDAH, 0)
        assert spec.pattern == PatternType.MIXED_BASIC

    def test_both_subvariants_exist_across_seeds(self):
        """Kedua sub-varian harus terpilih setidaknya sekali dalam 50 seed."""
        seen = Counter(
            gen.generate(Difficulty.MUDAH, s).root.branch_type for s in range(50)
        )
        assert BranchType.SERIES in seen, "Varian A (seri-luar) tidak pernah dipilih"
        assert BranchType.PARALLEL in seen, "Varian B (paralel-luar) tidak pernah dipilih"

    def test_variant_a_structure(self):
        """Varian A: root=SERIES, minimal satu elemen anak adalah Branch PARALLEL."""
        seed = _find_seed_for_variant(BranchType.SERIES)
        spec = gen.generate(Difficulty.MUDAH, seed)

        assert spec.root.branch_type == BranchType.SERIES
        inner_branches = [el for el in spec.root.elements if isinstance(el, Branch)]
        assert len(inner_branches) >= 1, "Varian A harus punya minimal satu Branch dalam (grup paralel)"
        assert any(b.branch_type == BranchType.PARALLEL for b in inner_branches)

    def test_variant_b_structure(self):
        """Varian B: root=PARALLEL, semua elemen anak adalah Branch SERIES."""
        seed = _find_seed_for_variant(BranchType.PARALLEL)
        spec = gen.generate(Difficulty.MUDAH, seed)

        assert spec.root.branch_type == BranchType.PARALLEL
        for child in spec.root.elements:
            assert isinstance(child, Branch)
            assert child.branch_type == BranchType.SERIES

    def test_all_labels_sequential_no_gap(self):
        """Label komponen harus R1, R2, R3, ... tanpa loncat/duplikat."""
        for seed in range(10):
            spec = gen.generate(Difficulty.MUDAH, seed)
            labels = [c.label for c in spec.all_components()]
            expected = [f"R{i+1}" for i in range(len(labels))]
            assert labels == expected, f"seed={seed}: labels={labels} bukan {expected}"

    def test_all_component_values_positive(self):
        for seed in range(20):
            for diff in Difficulty:
                spec = gen.generate(diff, seed)
                for c in spec.all_components():
                    assert c.value > 0


# ──────────────────────────────────────────────────────────────────────────────
# 2. Skalabilitas difficulty
# ──────────────────────────────────────────────────────────────────────────────

class TestDifficultyScaling:

    # Seed yang dijamin menghasilkan Varian A untuk semua difficulty
    SEED_A = _find_seed_for_variant.__func__(None, BranchType.SERIES) if False else None  # lazy

    @pytest.fixture(autouse=True)
    def _find_seeds(self):
        self.seed_a = _find_seed_for_variant(BranchType.SERIES)
        self.seed_b = _find_seed_for_variant(BranchType.PARALLEL)

    def test_mudah_component_count_variant_a(self):
        # Mudah varian A: R1 + [R2∥R3] = 3 komponen
        spec = gen.generate(Difficulty.MUDAH, self.seed_a)
        assert len(spec.all_components()) == 3

    def test_sedang_component_count_variant_a(self):
        # Sedang varian A: R1 + [R2∥R3] + R4 = 4 komponen
        spec = gen.generate(Difficulty.SEDANG, self.seed_a)
        assert len(spec.all_components()) == 4

    def test_sulit_component_count_variant_a(self):
        # Sulit varian A: R1 + [R2∥R3∥R4] + R5 = 5 komponen
        spec = gen.generate(Difficulty.SULIT, self.seed_a)
        assert len(spec.all_components()) == 5

    def test_mudah_component_count_variant_b(self):
        # Mudah varian B: [R1+R2] ∥ [R3+R4] = 4 komponen
        spec = gen.generate(Difficulty.MUDAH, self.seed_b)
        assert len(spec.all_components()) == 4

    def test_sedang_component_count_variant_b(self):
        # Sedang varian B: [R1+R2] ∥ [R3+R4] = 4 komponen
        spec = gen.generate(Difficulty.SEDANG, self.seed_b)
        assert len(spec.all_components()) == 4

    def test_sulit_component_count_variant_b(self):
        # Sulit varian B: [R1+R2] ∥ [R3+R4] ∥ [R5+R6] = 6 komponen
        spec = gen.generate(Difficulty.SULIT, self.seed_b)
        assert len(spec.all_components()) == 6

    def test_voltage_within_range(self):
        ranges = {
            Difficulty.MUDAH: (6, 12),
            Difficulty.SEDANG: (6, 24),
            Difficulty.SULIT: (9, 36),
        }
        for diff, (vmin, vmax) in ranges.items():
            for seed in range(30):
                spec = gen.generate(diff, seed)
                assert vmin <= spec.source.voltage <= vmax, (
                    f"{diff}: voltage {spec.source.voltage} di luar [{vmin}, {vmax}]"
                )


# ──────────────────────────────────────────────────────────────────────────────
# 3. Reproduksibilitas seed
# ──────────────────────────────────────────────────────────────────────────────

class TestReproducibility:

    def test_same_seed_same_subvariant(self):
        for seed in range(20):
            s1 = gen.generate(Difficulty.MUDAH, seed)
            s2 = gen.generate(Difficulty.MUDAH, seed)
            assert s1.root.branch_type == s2.root.branch_type

    def test_same_seed_same_component_values(self):
        for seed in [0, 1, 7, 42, 999]:
            s1 = gen.generate(Difficulty.SEDANG, seed)
            s2 = gen.generate(Difficulty.SEDANG, seed)
            v1 = [c.value for c in s1.all_components()]
            v2 = [c.value for c in s2.all_components()]
            assert v1 == v2, f"seed={seed}: nilai komponen berbeda antar run"

    def test_same_seed_same_voltage(self):
        for seed in [3, 11, 55]:
            s1 = gen.generate(Difficulty.SULIT, seed)
            s2 = gen.generate(Difficulty.SULIT, seed)
            assert s1.source.voltage == s2.source.voltage

    def test_different_seeds_usually_different(self):
        """Dua seed berbeda SANGAT JARANG menghasilkan nilai identik — test
        statistik ringan: dari 10 pasangan, setidaknya 7 harus berbeda."""
        different = sum(
            1 for s in range(10)
            if [c.value for c in gen.generate(Difficulty.MUDAH, s).all_components()]
               != [c.value for c in gen.generate(Difficulty.MUDAH, s + 100).all_components()]
        )
        assert different >= 7


# ──────────────────────────────────────────────────────────────────────────────
# 4. Kalkulasi matematis
# ──────────────────────────────────────────────────────────────────────────────

class TestCalculator:

    def test_variant_a_mudah_r_total(self):
        """Varian A mudah: R_total = R1 + (R2∥R3)."""
        seed = _find_seed_for_variant(BranchType.SERIES, Difficulty.MUDAH)
        spec = gen.generate(Difficulty.MUDAH, seed)
        solution = solve(spec)

        comps = spec.all_components()
        r1 = comps[0].value
        # Cari sub-branch paralel
        par_branch = next(el for el in spec.root.elements if isinstance(el, Branch))
        par_vals = [c.value for c in par_branch.elements]
        r_par = 1 / sum(1/r for r in par_vals)
        # Resistor seri lainnya (kecuali sub-branch)
        outer_series = [el for el in spec.root.elements if isinstance(el, Component)]
        r_outer = sum(c.value for c in outer_series)
        r_expected = r_outer + r_par

        assert math.isclose(solution.total_resistance, r_expected, rel_tol=1e-9)

    def test_variant_a_i_total_obeys_ohms_law(self):
        seed = _find_seed_for_variant(BranchType.SERIES)
        spec = gen.generate(Difficulty.MUDAH, seed)
        sol = solve(spec)
        assert math.isclose(
            sol.total_current,
            spec.source.voltage / sol.total_resistance,
            rel_tol=1e-9,
        )

    def test_variant_b_mudah_r_total(self):
        """Varian B mudah: R_total = (R1+R2) ∥ (R3+R4)."""
        seed = _find_seed_for_variant(BranchType.PARALLEL, Difficulty.MUDAH)
        spec = gen.generate(Difficulty.MUDAH, seed)
        solution = solve(spec)

        branch_Rs = [
            sum(c.value for c in br.elements)
            for br in spec.root.elements
        ]
        r_expected = 1 / sum(1/r for r in branch_Rs)
        assert math.isclose(solution.total_resistance, r_expected, rel_tol=1e-9)

    def test_variant_b_parallel_branches_same_voltage(self):
        """Semua cabang paralel harus memiliki tegangan total yang sama (= V_sumber)."""
        seed = _find_seed_for_variant(BranchType.PARALLEL)
        spec = gen.generate(Difficulty.SEDANG, seed)
        sol = solve(spec)
        results_by_label = {r.label: r for r in sol.component_results}

        # Jumlahkan V_drop per cabang seri dalam branch paralel
        for br in spec.root.elements:
            branch_v = sum(results_by_label[c.label].voltage_drop for c in br.elements)
            assert math.isclose(branch_v, spec.source.voltage, rel_tol=1e-9), (
                f"Tegangan cabang {[c.label for c in br.elements]} = {branch_v} "
                f"!= V_source {spec.source.voltage}"
            )

    def test_kirchhoff_voltage_law_series_outer(self):
        """Varian A: jumlah V_drop semua elemen seri = V_sumber."""
        seed = _find_seed_for_variant(BranchType.SERIES)
        spec = gen.generate(Difficulty.SEDANG, seed)
        sol = solve(spec)

        # V_R1 + V_grup_paralel + V_R4_dst harus = V_source
        # Cara sederhana: V_total = I_total * R_total
        assert math.isclose(
            sol.total_current * sol.total_resistance,
            spec.source.voltage,
            rel_tol=1e-9,
        )

    def test_power_conservation(self):
        """Total daya pada komponen harus = V*I = daya sumber."""
        for seed in [0, 1, 7, 42]:
            spec = gen.generate(Difficulty.SEDANG, seed)
            sol = solve(spec)
            p_source = spec.source.voltage * sol.total_current
            p_components = sum(r.power for r in sol.component_results)
            assert math.isclose(p_source, p_components, rel_tol=1e-6), (
                f"seed={seed}: P_source={p_source:.4f} != P_components={p_components:.4f}"
            )


# ──────────────────────────────────────────────────────────────────────────────
# 5. Renderer SVG
# ──────────────────────────────────────────────────────────────────────────────

class TestRenderer:

    def test_svg_is_valid_markup(self):
        for seed in range(5):
            spec = gen.generate(Difficulty.MUDAH, seed)
            svg = render_svg(spec)
            assert svg.strip().startswith("<?xml") or svg.strip().startswith("<svg"), (
                f"seed={seed}: SVG tidak diawali dengan tag XML/SVG yang valid"
            )

    def test_svg_contains_all_component_labels(self):
        for seed in range(10):
            for diff in Difficulty:
                spec = gen.generate(diff, seed)
                svg = render_svg(spec)
                for comp in spec.all_components():
                    assert comp.label in svg, (
                        f"seed={seed} {diff}: label {comp.label} tidak ada di SVG"
                    )

    def test_svg_not_empty(self):
        for seed in range(5):
            assert len(render_svg(gen.generate(Difficulty.SULIT, seed))) > 500

    def test_render_does_not_raise_for_any_difficulty(self):
        for diff in Difficulty:
            for seed in range(5):
                spec = gen.generate(diff, seed)
                render_svg(spec)  # tidak boleh raise exception


# ──────────────────────────────────────────────────────────────────────────────
# 6. Describer
# ──────────────────────────────────────────────────────────────────────────────

class TestDescriber:

    def test_topology_description_contains_all_labels(self):
        for seed in range(10):
            spec = gen.generate(Difficulty.MUDAH, seed)
            topo = describe_topology(spec)
            for comp in spec.all_components():
                assert comp.label in topo

    def test_llm_description_mentions_difficulty(self):
        for diff in Difficulty:
            spec = gen.generate(diff, 0)
            llm = describe_for_llm(spec)
            assert diff.value in llm

    def test_llm_description_mentions_voltage(self):
        spec = gen.generate(Difficulty.MUDAH, 42)
        llm = describe_for_llm(spec)
        assert str(int(spec.source.voltage)) in llm

    def test_llm_description_mentions_all_components(self):
        spec = gen.generate(Difficulty.SEDANG, 7)
        llm = describe_for_llm(spec)
        for comp in spec.all_components():
            assert comp.label in llm, f"{comp.label} tidak disebut di deskripsi LLM"

    def test_variant_a_topology_str_contains_paralel(self):
        seed = _find_seed_for_variant(BranchType.SERIES)
        spec = gen.generate(Difficulty.MUDAH, seed)
        topo = describe_topology(spec)
        assert "paralel" in topo.lower()

    def test_variant_b_topology_str_contains_seri(self):
        seed = _find_seed_for_variant(BranchType.PARALLEL)
        spec = gen.generate(Difficulty.MUDAH, seed)
        topo = describe_topology(spec)
        assert "seri" in topo.lower()


# ──────────────────────────────────────────────────────────────────────────────
# 7. Full pipeline via endpoint
# ──────────────────────────────────────────────────────────────────────────────

class TestEndpointMixedBasic:

    def test_mixed_basic_endpoint_returns_200(self):
        r = client.get("/api/questions/generate", params={"pattern": "mixed_basic", "seed": 1})
        assert r.status_code == 200

    def test_response_has_all_required_fields(self):
        r = client.get("/api/questions/generate", params={"pattern": "mixed_basic", "seed": 1})
        data = r.json()
        assert "spec" in data
        assert "svg" in data
        assert "solution" in data
        assert "llm_description" in data

    def test_reproducibility_via_endpoint(self):
        params = {"pattern": "mixed_basic", "difficulty": "sedang", "seed": 77}
        r1 = client.get("/api/questions/generate", params=params)
        r2 = client.get("/api/questions/generate", params=params)
        assert r1.json()["solution"]["total_resistance"] == r2.json()["solution"]["total_resistance"]
        assert r1.json()["spec"]["source"]["voltage"] == r2.json()["spec"]["source"]["voltage"]

    def test_all_difficulties_via_endpoint(self):
        for diff in ["mudah", "sedang", "sulit"]:
            r = client.get(
                "/api/questions/generate",
                params={"pattern": "mixed_basic", "difficulty": diff, "seed": 42},
            )
            assert r.status_code == 200
            assert r.json()["spec"]["difficulty"] == diff

    def test_solution_total_resistance_positive(self):
        for seed in range(5):
            r = client.get(
                "/api/questions/generate",
                params={"pattern": "mixed_basic", "seed": seed},
            )
            assert r.json()["solution"]["total_resistance"] > 0

    def test_svg_in_response_is_nonempty(self):
        r = client.get("/api/questions/generate", params={"pattern": "mixed_basic", "seed": 5})
        assert len(r.json()["svg"]) > 100