from companyos.runtime.customer_acquisition_bridge import public_business_contact

def test_public_business_email_with_source_is_allowed():
    d={
        "business_email":"sales@example.com",
        "company":"Example Co",
        "source_url":"https://example.com/contact",
    }
    assert public_business_contact(d,"x.json",set()) is not None

def test_personal_email_without_business_provenance_is_rejected():
    d={"email":"someone@gmail.com","company":"Example"}
    assert public_business_contact(d,"x.json",set()) is None

def test_own_sender_is_rejected():
    d={
        "business_email":"company@example.com",
        "company":"Example",
        "source_url":"https://example.com",
    }
    assert public_business_contact(d,"x.json",{"company@example.com"}) is None
