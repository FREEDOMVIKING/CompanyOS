import json
from pathlib import Path

from companyos.runtime import research_output_capture as roc
from companyos.strategy import candidate_materialization_bridge as cmb
from companyos.strategy import orchestration_candidate_extractor_v2 as oce
from companyos.strategy import profit_first_evidence_pipeline as pep


def test_portable_path_accepts_canonical_runtime_outside_repo():
    p = Path.home() / ".companyos_runtime" / "canonical_research_outputs" / "sample.json"
    assert roc._portable_path(p) == str(p)
    assert cmb._portable_path(p) == str(p)
    assert oce._portable_path(p) == str(p)
    assert pep._portable_path(p) == str(p)


def test_research_capture_can_persist_outside_repo_root(tmp_path, monkeypatch):
    raw = tmp_path / "canonical_research_outputs"
    state = tmp_path / "research_output_capture_state.json"
    index = tmp_path / "canonical_research_output_index.jsonl"

    monkeypatch.setattr(roc, "RAW_DIR", raw)
    monkeypatch.setattr(roc, "STATE", state)
    monkeypatch.setattr(roc, "INDEX", index)

    row = roc.persist_capture(
        {
            "started_at_unix": 1234567890.0,
            "goal": "test",
            "returns": [],
            "finished_at_unix": 1234567890.1,
            "result": {"orchestration_id": "v69_14_1_test"},
            "error": None,
        }
    )

    assert row["orchestration_id"] == "v69_14_1_test"
    assert Path(row["path"]).is_absolute()
    assert Path(row["path"]).exists()
    assert index.exists()
    assert state.exists()


def test_candidate_materializer_can_scan_external_runtime_journal(tmp_path, monkeypatch):
    journal = tmp_path / "full_autonomy_journal.jsonl"
    journal.write_text(
        json.dumps(
            {
                "name": "External-runtime candidate",
                "sector": "software",
                "business_model": "subscription",
                "description": "Regression candidate",
                "market_demand": 50,
                "expected_profit": 50,
            }
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cmb, "JOURNAL_CANDIDATES", [journal])
    monkeypatch.setattr(cmb, "SEARCH_ROOTS", [])

    rows = cmb.collect_recent_research_outputs()
    assert rows
    assert rows[0]["name"] == "External-runtime candidate"


def test_evidence_pipeline_external_runtime_path_label_is_safe():
    p = Path.home() / ".companyos_runtime" / "profit_first_candidates" / "candidate.json"
    assert pep._portable_path(p) == str(p)
