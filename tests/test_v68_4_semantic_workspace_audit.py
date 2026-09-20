from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads((ROOT/"audit/COMPANYOS_V68_4_SEMANTIC_WORKSPACE_AUDIT.json").read_text())

def test_audit_is_non_destructive():
    d=report()
    assert d["mode"]=="AUDIT_ONLY_NO_FILE_MUTATION"
    assert d["deletion_performed"] is False
    assert d["move_performed"] is False
    assert d["financial_limits_changed"] is False

def test_expected_semantic_groups_are_present():
    d=report()
    assert d["semantic_group_count"]==2
    for g in d["semantic_groups"]:
        assert len(g["files"])>=2
        assert "decision" in g

def test_semantic_equivalence_is_rechecked():
    d=report()
    for g in d["semantic_groups"]:
        assert isinstance(g["ast_equivalent"],bool)
        assert all("ast_sha256" in x for x in g["details"].values())

def test_workspace_identity_has_file_level_evidence():
    w=report()["workspace_identity_audit"]
    assert w["upper_file_count"]>0
    assert w["lower_file_count"]>0
    assert (
        w["same_relative_file_count"]
        + w["different_relative_file_count"]
        + len(w["upper_only_files"])
        + len(w["lower_only_files"])
    ) > 0
    assert "decision" in w

def test_both_workspace_paths_remain():
    assert (ROOT/"workspace/Local_Contractor_Bid_Organizer").exists()
    assert (ROOT/"workspace/local_contractor_bid_organizer").exists()

def test_canonical_runtime_surface_remains():
    required=[
        "companyos/runtime/service_supervisor.py",
        "companyos/runtime/runtime_control.py",
        "companyos/runtime/autonomous_task_queue.py",
        "companyos/runtime/profit_opportunity_engine.py",
        "companyos/connectors/hosting_router.py",
        "config/companyos_active_component_manifest.json",
    ]
    assert all((ROOT/p).exists() for p in required)
