"""Test untuk endpoint API generate soal."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_patterns_returns_registered_patterns():
    r = client.get("/api/questions/patterns")
    assert r.status_code == 200
    patterns = r.json()
    assert "series_simple" in patterns
    assert "parallel_simple" in patterns


def test_generate_question_with_explicit_params():
    r = client.get(
        "/api/questions/generate",
        params={"pattern": "series_simple", "difficulty": "mudah", "seed": 1},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["spec"]["pattern"] == "series_simple"
    assert data["spec"]["difficulty"] == "mudah"
    assert data["spec"]["seed"] == 1
    assert data["solution"]["total_resistance"] > 0
    assert len(data["svg"]) > 0
    assert len(data["llm_description"]) > 0


def _extract_comparable_values(root_json: dict) -> dict:
    """Ambil hanya field yang substansial (bukan id/UUID yang sengaja
    di-random ulang setiap kali objek dibuat) untuk perbandingan
    reproduksibilitas."""
    if "value" in root_json:  # Component
        return {"label": root_json["label"], "value": root_json["value"], "unit": root_json["unit"]}
    return {
        "branch_type": root_json["branch_type"],
        "elements": [_extract_comparable_values(el) for el in root_json["elements"]],
    }


def test_generate_question_same_seed_is_reproducible():
    params = {"pattern": "parallel_simple", "difficulty": "sedang", "seed": 555}
    r1 = client.get("/api/questions/generate", params=params)
    r2 = client.get("/api/questions/generate", params=params)

    root1 = _extract_comparable_values(r1.json()["spec"]["root"])
    root2 = _extract_comparable_values(r2.json()["spec"]["root"])
    assert root1 == root2

    # Tegangan sumber dan jawaban akhir juga harus identik
    assert r1.json()["spec"]["source"]["voltage"] == r2.json()["spec"]["source"]["voltage"]
    assert r1.json()["solution"]["total_resistance"] == r2.json()["solution"]["total_resistance"]


def test_generate_question_unregistered_pattern_returns_400():
    r = client.get("/api/questions/generate", params={"pattern": "mixed_basic"})
    assert r.status_code == 400
