from companyos.runtime.trusted_procurement_intent_emitter import (
    explicit_items, text_acquisition_intent, category_for
)

def test_generic_opportunity_does_not_emit():
    d={"title":"Marketplace Software Opportunity","expected_profit_usd":500}
    assert explicit_items(d)==[]

def test_structured_dependency_emits():
    d={"required_service":"transactional email delivery API"}
    assert explicit_items(d)==[("required_service","transactional email delivery API")]

def test_explicit_acquisition_text_emits():
    assert text_acquisition_intent("We must subscribe to a transactional email API before launch")

def test_self_reference_does_not_emit():
    d={"objective":"Acquire real external evidence for missing procurement fields. Do not fabricate vendor."}
    assert explicit_items(d)==[]

def test_category_mapping():
    assert category_for("register a production domain","required_resource")=="domain"
