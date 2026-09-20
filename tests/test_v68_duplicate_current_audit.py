from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads((ROOT/"audit/COMPANYOS_V68_DUPLICATE_CURRENT_AUDIT.json").read_text())

def test_audit_is_non_destructive():
    d=report()
    assert d["mode"] == "AUDIT_ONLY_NO_FILE_MUTATION"
    assert d["deletion_performed"] is False
    assert d["move_performed"] is False
    assert d["financial_limits_changed"] is False

def test_safe_exact_candidates_have_keeper_and_evidence():
    d=report()
    for row in d["safe_exact_retirement_candidates"]:
        assert row["path"] != row["keeper"]
        assert row["evidence"] == "exact_sha256_duplicate_and_zero_active_refs"

def test_next_step_requires_recovery_and_full_validation():
    d=report()
    req=set(d["next_step"]["requires"])
    assert "remote recovery branch" in req
    assert "full pytest" in req
    assert "runtime health" in req
    assert "launch readiness" in req
    assert "automatic rollback on failure" in req

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
