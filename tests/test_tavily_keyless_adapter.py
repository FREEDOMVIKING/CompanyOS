from companyos.runtime.tavily_keyless_adapter import configured, state

def test_keyless_sdk_available():
    assert configured() is True

def test_state_shape():
    s=state()
    assert s["mode"]=="keyless"
    assert "cooldown_active" in s
