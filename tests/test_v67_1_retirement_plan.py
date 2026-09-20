from pathlib import Path
import json

ROOT=Path.home()/"companyos"


def load():
    return json.loads((ROOT/"audit/COMPANYOS_V67_1_RETIREMENT_PLAN.json").read_text())


def test_plan_is_non_destructive():
    d=load()
    assert d["mode"] == "PLAN_ONLY_NO_FILE_MUTATION"
    assert d["deletion_performed"] is False
    assert d["move_performed"] is False
    assert d["financial_limits_changed"] is False


def test_canonical_files_are_protected():
    d=load()
    assert d["summary"]["protected_canonical"]["files"] > 0
    assert d["protected_canonical_count"] >= 39


def test_retirement_is_staged_and_reversible():
    d=load()
    seq=d["retirement_sequence"]
    assert [x["stage"] for x in seq] == ["A","B","C","D"]
    assert all(x["automatic_now"] is False for x in seq)
    assert "recovery branch" in d["next_recommended_batch"]["safety"]
