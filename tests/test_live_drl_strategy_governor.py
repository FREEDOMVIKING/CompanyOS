from companyos.runtime.live_drl_strategy_governor import LIVE_AUTHORITY, DRL_ACTION_AUTHORITY
from companyos.runtime import advanced_drl_controller as drl

def test_irreversible_authority_stays_off():
    # CompanyOS may have global permission for governed external actions, but
    # the adaptive DRL learner itself must not directly exercise them.
    assert DRL_ACTION_AUTHORITY["financial_actions"] is False
    assert DRL_ACTION_AUTHORITY["wallet_transactions"] is False
    assert DRL_ACTION_AUTHORITY["credential_changes"] is False
    assert DRL_ACTION_AUTHORITY["paid_ads"] is False
    assert DRL_ACTION_AUTHORITY["unsolicited_outreach"] is False
    assert DRL_ACTION_AUTHORITY["public_deployment"] is False
    assert DRL_ACTION_AUTHORITY["external_irreversible_actions"] is False

def test_live_authority_controls_internal_strategy():
    assert LIVE_AUTHORITY["research_priority"] is True
    assert LIVE_AUTHORITY["economics_validation_priority"] is True
    assert LIVE_AUTHORITY["capability_build_priority"] is True
    assert LIVE_AUTHORITY["candidate_validation_priority"] is True
    assert DRL_ACTION_AUTHORITY["research_priority"] is True
    assert DRL_ACTION_AUTHORITY["economics_validation_priority"] is True
    assert DRL_ACTION_AUTHORITY["capability_build_priority"] is True
    assert DRL_ACTION_AUTHORITY["candidate_validation_priority"] is True

def test_action_space_is_expected():
    assert "build_missing_capability" in drl.ACTIONS
    assert "validate_top_candidate" in drl.ACTIONS
    assert "improve_economics_estimation" in drl.ACTIONS
