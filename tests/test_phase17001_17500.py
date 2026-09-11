from companyos.specialistops import SpecialistCapabilityRouter, SpecialistOpsStatus

def test_router_support():
    r = SpecialistCapabilityRouter("/tmp")
    assert r.supports("research")
    assert r.supports("finance")
    assert not r.supports("unknown")

def test_status():
    s = SpecialistOpsStatus().status()
    assert s["success"] is True
    assert s["approval_boundaries_preserved"] is True
