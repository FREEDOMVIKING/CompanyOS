from companyos.runtime.procurement_intent_validator import (
    acquisition_text_signal,
    explicit_key_signal,
    self_referential,
)

def test_generic_profit_language_not_explicit_purchase():
    d={"title":"Marketplace Software Opportunity","expected_profit_usd":500}
    assert explicit_key_signal(d)==[]
    assert acquisition_text_signal(d)==[]

def test_explicit_required_service_is_purchase_signal():
    d={"required_service":"transactional email API"}
    assert explicit_key_signal(d)

def test_explicit_acquisition_language_is_signal():
    d={"requirement":"must subscribe to an external email delivery service"}
    assert acquisition_text_signal(d)

def test_procurement_boilerplate_is_not_business_need():
    assert self_referential(
        "Acquire real external evidence for missing procurement fields. "
        "Do not fabricate vendor or price."
    )
