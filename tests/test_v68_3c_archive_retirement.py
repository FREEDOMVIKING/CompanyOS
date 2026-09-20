from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path.home()/"companyos"

def manifest():
    return json.loads((ROOT/"audit/COMPANYOS_V68_3C_ARCHIVE_RETIREMENT_MANIFEST.json").read_text())

def correction():
    return json.loads((ROOT/"audit/COMPANYOS_V68_3C_ROLE_CORRECTION.json").read_text())

def tracked():
    cp=subprocess.run(["git","ls-files"],cwd=ROOT,text=True,capture_output=True,check=True)
    return set(cp.stdout.splitlines())

def sha(rel):
    return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()

def test_nine_archive_copies_retired_only():
    d=manifest()
    assert d["candidate_count"]==9
    assert d["archive_history_exact_copy_count"]==9
    assert d["all_byte_equality_reverified"] is True
    assert d["root_shadow_retained"] is True

def test_retired_archive_candidates_have_live_exact_keeper():
    d=manifest()
    now=tracked()
    for row in d["candidates"]:
        assert row["path"] not in now
        assert not (ROOT/row["path"]).exists()
        assert row["keeper"] in now
        assert (ROOT/row["keeper"]).exists()
        assert sha(row["keeper"])==row["sha256"]

def test_pending_recovery_root_shadow_remains_active():
    d=manifest()
    c=correction()
    now=tracked()

    assert d["root_shadow_path"] in now
    assert d["root_shadow_keeper"] in now
    assert sha(d["root_shadow_path"])==sha(d["root_shadow_keeper"])
    assert c["corrected_decision"]=="KEEP_ACTIVE_ROOT_SHADOW"
    assert c["removal_performed"] is False

    refs=set(d["root_shadow_active_reference_hits"])
    assert "companyos/runtime/health_supervisor.py" in refs
    assert "companyos/runtime/launch_readiness_audit.py" in refs

def test_v68_2_audit_test_is_lifecycle_aware():
    s=(ROOT/"tests/test_v68_2_role_resolution.py").read_text()
    assert "test_future_candidates_are_exact_copies_of_keeper_or_verified_retired" in s
    assert "COMPANYOS_V68_3C_ARCHIVE_RETIREMENT_MANIFEST.json" in s

def test_role_distinct_and_workspace_guards_remain():
    required=[
        "marketplace/packages/knowledge_notes/plugin.py",
        "plugins/installed/knowledge_notes/plugin.py",
        "marketplace/packages/project_metrics/plugin.py",
        "plugins/installed/project_metrics/plugin.py",
        "companyos/workerops/execution_bridge.py",
        "scripts/execution_bridge_phase18000.py",
        "companyos/intelligence/storage.py",
        "companyos/orchestrator/storage.py",
        "workspace/Local_Contractor_Bid_Organizer/prototype/current/server.py",
        "workspace/local_contractor_bid_organizer/prototype/current/server.py",
    ]
    assert all((ROOT/p).exists() for p in required)

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
