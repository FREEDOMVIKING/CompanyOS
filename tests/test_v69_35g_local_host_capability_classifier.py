from companyos.runtime import local_host_capability_classifier as c

def test_ssh_host_ranks_high():
    r=c.classify({"hostname":"server.local"},[22],False)
    assert r["direct_bootstrap"] is True
    assert r["score"] >= 80

def test_windows_candidate():
    r=c.classify({"hostname":"desktop.local"},[445,3389],False)
    assert r["platform_hint"] in {"windows","windows_or_nas"}
    assert r["score"] > 0

def test_current_phone_excluded():
    r=c.classify({"hostname":"phone.local"},[],True)
    assert r["score"] < 0
    assert r["platform_hint"]=="current_phone"

def test_public_ip_rejected():
    assert c.private_ipv4("192.168.1.20")
    assert not c.private_ipv4("8.8.8.8")
