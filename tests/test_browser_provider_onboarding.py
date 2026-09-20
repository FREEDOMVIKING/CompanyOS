from companyos.runtime.browser_provider_onboarding import detect_blockers, backend_status

def test_captcha_detection():
    snap={"text":"Please complete the reCAPTCHA","inputs":[]}
    assert "captcha" in detect_blockers(snap)

def test_required_terms_checkbox_detection():
    snap={"text":"","inputs":[{"type":"checkbox","required":True,"name":"terms"}]}
    assert "required_terms_or_checkbox" in detect_blockers(snap)

def test_phone_detection():
    snap={"text":"","inputs":[{"type":"tel","required":True,"name":"phone"}]}
    assert "required_phone" in detect_blockers(snap)

def test_backend_status_shape():
    s=backend_status()
    assert "browser_backend_ready" in s
    assert "backend" in s
