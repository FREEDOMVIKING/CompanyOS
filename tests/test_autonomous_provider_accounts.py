from companyos.runtime.autonomous_provider_accounts import (
    same_provider_host,
    safe_url,
    FormParser,
    choose_form,
    build_form_payload,
)

def test_same_provider_domain():
    assert same_provider_host("app.example.com","example.com")
    assert not same_provider_host("example.evil.com","example.com")

def test_https_same_domain_only():
    assert safe_url("https://accounts.example.com/signup","example.com")
    assert not safe_url("http://example.com/signup","example.com")
    assert not safe_url("https://evil.com/signup","example.com")

def test_simple_signup_form_can_be_filled():
    p=FormParser()
    p.feed("""
    <form method="post" action="/register">
      <input name="email" type="email" required>
      <input name="password" type="password" required>
    </form>
    """)
    f=choose_form(p.forms)
    assert f is not None
    data,unresolved=build_form_payload(f,"bot@example.com","abcDEF123!")
    assert data["email"]=="bot@example.com"
    assert data["password"]=="abcDEF123!"
    assert unresolved==[]

def test_required_checkbox_not_auto_accepted():
    p=FormParser()
    p.feed("""
    <form method="post">
      <input name="email" type="email" required>
      <input name="password" type="password" required>
      <input name="terms" type="checkbox" required>
    </form>
    """)
    f=choose_form(p.forms)
    _,unresolved=build_form_payload(f,"bot@example.com","abcDEF123!")
    assert "required_terms_or_checkbox" in unresolved
