from companyos.runtimeintegration import RuntimeRecoveryManager, RuntimeIntegrationStatus

def test_recovery_missing_capability():
    r = RuntimeRecoveryManager().classify_cycle({
        "results":[{"success":False,"status":"capability_missing"}]
    })
    assert r["next_action"] == "discover_or_build_missing_capabilities"

def test_status():
    s = RuntimeIntegrationStatus().status()
    assert s["persistent_checkpointing"] is True
    assert s["approval_pause_and_resume"] is True
