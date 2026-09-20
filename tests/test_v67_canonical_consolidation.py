from pathlib import Path
import json

ROOT=Path.home()/"companyos"


def test_manifest_core_paths_present():
    d=json.loads((ROOT/"config/companyos_active_component_manifest.json").read_text())
    assert d["schema"]=="companyos.active_component_manifest.v1"
    s=d["component_status"]
    assert s["control_plane.service_supervisor"]["present"] is True
    assert s["execution.task_queue"]["present"] is True
    assert s["connectors_and_hosting.hosting_router"]["present"] is True


def test_finance_domains_are_separate():
    d=json.loads((ROOT/"config/companyos_active_component_manifest.json").read_text())
    p=d["policy_domains"]
    assert p["solana_live_execution"]["canonical_policy"] != p["treasury_budgeting"]["canonical_policy"]
    assert "COMPANYOS_SOL_DAILY_CAP_SOL" in p["solana_live_execution"]["env_keys"]
    assert "COMPANYOS_AUTONOMOUS_DAILY_LIMIT" in p["treasury_budgeting"]["env_keys"]


def test_consolidation_auditor_does_not_delete_or_change_limits():
    s=(ROOT/"scripts/companyos_consolidation_audit.py").read_text()
    assert '"deletion_performed":False' in s
    assert '"financial_limits_changed":False' in s


def test_canonical_hosting_router_is_real_path():
    assert (ROOT/"companyos/connectors/hosting_router.py").exists()
