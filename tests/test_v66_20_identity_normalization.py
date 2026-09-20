from companyos.governance.venture_identity_resolver import canonical_id, is_internal
from companyos.governance.venture_identity_progression import candidate_ventures

def test_version_suffix_collapses():
    assert canonical_id("local_contractor_bid_organizer_v1") == "local_contractor_bid_organizer"

def test_production_sites_is_internal():
    assert is_internal("production_sites") is True

def test_candidate_groups_do_not_emit_version_alias_as_separate_id():
    groups=candidate_ventures()
    assert "local_contractor_bid_organizer_v1" not in groups
    assert "production_sites" not in groups
