from companyos_phase229_236 import ProviderConfig, SelfBuildDaemon, HandoffController

def test_provider_config(tmp_path):
    c = ProviderConfig(tmp_path)
    c.save("x","y","cmd")
    assert c.load()["provider"] == "x"

def test_daemon(tmp_path):
    d = SelfBuildDaemon(tmp_path)
    d.enqueue({"id":1})
    assert d.pop()["id"] == 1

def test_handoff_gate():
    r = HandoffController().evaluate({})
    assert r["ready"] is False
    assert "coder_connected" in r["missing"]
