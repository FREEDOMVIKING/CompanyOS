import json
from companyos.runtime import opportunity_execution_capability_bridge as bridge


def test_runtime_candidate_outside_repo_root_is_loadable(tmp_path, monkeypatch):
    candidate_dir = tmp_path / "profit_first_candidates"
    candidate_dir.mkdir(parents=True)

    candidate = candidate_dir / "runtime_candidate.json"
    candidate.write_text(
        json.dumps(
            {
                "name": "Runtime candidate",
                "target_customer": "small business",
                "market": "software",
                "expected_profit": 1000,
                "probability": 50,
                "readiness": 40,
                "evidence": [{"source": "example"}],
            }
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(bridge, "CANDIDATE_DIR", candidate_dir)
    rows = bridge.load_candidates()

    assert len(rows) == 1
    assert rows[0]["name"] == "Runtime candidate"
    assert rows[0]["source"] == str(candidate.resolve())


def test_repo_local_source_remains_relative(monkeypatch):
    local_dir = bridge.ROOT / ".pytest_v69_18a_candidates"
    local_dir.mkdir(parents=True, exist_ok=True)
    candidate = local_dir / "local_candidate.json"

    try:
        candidate.write_text(
            json.dumps(
                {
                    "name": "Repo local candidate",
                    "target_customer": "buyer",
                    "market": "software",
                    "expected_profit": 1,
                    "probability": 1,
                    "readiness": 1,
                    "evidence": [{"source": "example"}],
                }
            ) + "\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(bridge, "CANDIDATE_DIR", local_dir)
        rows = bridge.load_candidates()

        assert len(rows) == 1
        assert rows[0]["source"] == str(candidate.resolve().relative_to(bridge.ROOT))
    finally:
        candidate.unlink(missing_ok=True)
        try:
            local_dir.rmdir()
        except OSError:
            pass
