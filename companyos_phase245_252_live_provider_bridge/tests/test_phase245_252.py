from companyos_phase245_252 import ResponseNormalizer, ProviderHealth, ProviderProfile

def test_normalizer():
    r = ResponseNormalizer().normalize({"files":{"x.py":"x=1"}})
    assert r["success"] is True

def test_health():
    assert ProviderHealth().assess({"success":False})["healthy"] is False

def test_profile(tmp_path):
    p = ProviderProfile(tmp_path)
    p.save("x","http://localhost","m")
    assert p.load()["name"] == "x"
