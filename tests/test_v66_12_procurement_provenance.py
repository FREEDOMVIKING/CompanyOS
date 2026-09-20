from pathlib import Path
from companyos.runtime.procurement_requirement_specifier import (
    _is_procurement_internal_path,
    _self_referential_text,
    _trusted_context_path,
)

def test_procurement_generated_path_is_untrusted():
    assert _is_procurement_internal_path(
        Path.home()/".companyos_runtime/procurement/sourcing_requests.jsonl"
    )
    assert not _trusted_context_path(
        Path.home()/".companyos_runtime/procurement/sourcing_requests.jsonl"
    )

def test_venture_path_is_trusted():
    assert _trusted_context_path(
        Path.home()/".companyos_runtime/ventures/example.json"
    )

def test_sourcing_instruction_is_not_business_requirement():
    assert _self_referential_text(
        "Acquire real external evidence for missing procurement fields. "
        "Do not fabricate vendor, price, payment destination, probability, or profit."
    )

def test_real_business_need_is_not_self_reference():
    assert not _self_referential_text(
        "real-time cryptocurrency market price data for the portfolio analytics product"
    )
