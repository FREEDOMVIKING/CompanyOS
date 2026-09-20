from companyos.runtime.verified_web_prospect_discovery import (
    _extract_candidate_emails,
    _decode_ddg_url,
)

def test_role_email_is_accepted():
    x=_extract_candidate_emails("Contact us at sales@example.com")
    assert "sales@example.com" in x

def test_named_work_email_is_not_auto_outreach_contact():
    x=_extract_candidate_emails("Contact john.smith@example.com")
    assert "john.smith@example.com" not in x

def test_personal_domain_is_rejected():
    x=_extract_candidate_emails("Contact info@gmail.com")
    assert x==[]

def test_ddg_redirect_decode():
    u=_decode_ddg_url(
        "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fcontact"
    )
    assert u=="https://example.com/contact"
