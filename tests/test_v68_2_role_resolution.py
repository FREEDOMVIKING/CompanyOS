from pathlib import Path
import hashlib
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads((ROOT/"audit/COMPANYOS_V68_2_ROLE_RESOLUTION.json").read_text())

def sha(rel):
    h=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    return h

def test_role_resolution_is_non_destructive():
    d=report()
    assert d["mode"]=="AUDIT_ONLY_NO_FILE_MUTATION"
    assert d["deletion_performed"] is False
    assert d["move_performed"] is False
    assert d["financial_limits_changed"] is False

def test_future_candidates_are_exact_copies_of_keeper_or_verified_retired():
    d=report()
    retirement_path=ROOT/"audit/COMPANYOS_V68_3C_ARCHIVE_RETIREMENT_MANIFEST.json"
    retired={}
    if retirement_path.exists():
        rd=json.loads(retirement_path.read_text())
        retired={row["path"]:row for row in rd.get("candidates",[])}

    for row in d["future_surgical_candidates"]:
        candidate=ROOT/row["path"]
        keeper=ROOT/row["keeper"]

        assert keeper.exists()
        assert sha(row["keeper"])==row["sha256"]

        if candidate.exists():
            assert sha(row["path"])==row["sha256"]
        else:
            retired_row=retired.get(row["path"])
            assert retired_row is not None
            assert retired_row["keeper"]==row["keeper"]
            assert retired_row["sha256"]==row["sha256"]

def test_role_distinct_groups_are_not_future_candidates():
    d=report()
    candidates={x["path"] for x in d["future_surgical_candidates"]}
    for g in d["resolved_groups"]:
        if g["decision"].startswith("KEEP_"):
            assert not (set(g["files"]) & candidates)

def test_semantic_groups_not_retired():
    d=report()
    for g in d["resolved_groups"]:
        if g["kind"]=="semantic":
            assert g["decision"]=="KEEP_PENDING_BEHAVIOR_REVIEW"
            assert not g["future_retirement_candidates"]

def test_canonical_runtime_surface_remains_present():
    required=[
        "companyos/runtime/service_supervisor.py",
        "companyos/runtime/runtime_control.py",
        "companyos/runtime/autonomous_task_queue.py",
        "companyos/runtime/profit_opportunity_engine.py",
        "companyos/connectors/hosting_router.py",
        "config/companyos_active_component_manifest.json",
    ]
    assert all((ROOT/p).exists() for p in required)
