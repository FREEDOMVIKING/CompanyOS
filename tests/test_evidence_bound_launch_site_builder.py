from companyos.runtime.evidence_bound_launch_site_builder import clean_text

def test_internal_instruction_is_rejected():
    assert clean_text("Do not fabricate vendor price or payment destination") is None

def test_normal_public_copy_is_allowed():
    assert clean_text("Automate repetitive field workflows") is not None
