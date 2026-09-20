from pathlib import Path
import json

ROOT=Path.home()/"companyos"

def report():
    return json.loads((ROOT/"audit/COMPANYOS_V68_1_PRECISE_DUPLICATE_AUDIT.json").read_text())

def test_audit_is_non_destructive():
    d=report()
    assert d["mode"]=="AUDIT_ONLY_NO_FILE_MUTATION"
    assert d["deletion_performed"] is False
    assert d["move_performed"] is False
    assert d["financial_limits_changed"] is False

def test_package_init_noise_is_not_a_retirement_group():
    d=report()
    for g in d["groups"]:
        assert not all(Path(f).name=="__init__.py" for f in g["files"])

def test_retirement_candidates_are_exact_and_dormant():
    d=report()
    by_path={x["path"]:x for x in d["candidate_retirements"]}
    for g in d["groups"]:
        for f in g["retirement_candidates"]:
            assert g["kind"]=="exact"
            assert f in g["dormant"]
            assert f in by_path
            assert g["keeper"] is not None

def test_role_distinct_plugin_copies_are_not_auto_retired():
    d=report()
    for g in d["groups"]:
        roles=set(g["roles"].values())
        if {"marketplace_source_package","installed_plugin_copy"}.issubset(roles):
            assert not g["retirement_candidates"]

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
