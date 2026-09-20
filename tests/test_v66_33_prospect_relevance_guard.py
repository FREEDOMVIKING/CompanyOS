from companyos.runtime.verified_web_prospect_discovery import (
    content_like_url,
    page_relevance,
)

def test_blog_source_is_content():
    assert content_like_url("https://example.com/blog/business-email-examples")

def test_contractor_homepage_is_relevant():
    x=page_relevance(
        "ABC Construction is a commercial contractor serving local businesses.",
        {
            "title":"Local Contractor Bid Organizer",
            "audience":"construction contractors",
            "description":"Organize contractor bids",
        },
    )
    assert x["ok"] is True

def test_unrelated_email_marketing_site_is_not_relevant():
    x=page_relevance(
        "Email marketing software, newsletter templates, automation and campaigns.",
        {
            "title":"Local Contractor Bid Organizer",
            "audience":"construction contractors",
            "description":"Organize contractor bids",
        },
    )
    assert x["ok"] is False
