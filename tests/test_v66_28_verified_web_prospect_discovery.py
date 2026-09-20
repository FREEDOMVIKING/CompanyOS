from companyos.runtime.verified_web_prospect_discovery import verify_prospect

def test_personal_domain_rejected_without_fetch():
    x=verify_prospect({
        "company_name":"Example",
        "public_business_email":"person@gmail.com",
        "official_website":"https://example.com",
        "source_url":"https://example.com/contact",
        "fit_reason":"fit",
    })
    assert x["ok"] is False
    assert "personal_email_domain" in x["reasons"]

def test_missing_source_is_rejected():
    x=verify_prospect({
        "company_name":"Example",
        "public_business_email":"sales@example.com",
        "official_website":"https://example.com",
        "source_url":"",
        "fit_reason":"fit",
    })
    assert x["ok"] is False
    assert "source_url_missing_or_invalid" in x["reasons"]
