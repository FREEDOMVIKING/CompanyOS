from companyos.runtime.live_external_execution_router import (
    ACTION_POLICY,
    FORBIDDEN_CONNECTORS,
    FORBIDDEN_ACTIONS,
)

def test_live_allowlist_contains_verified_real_connectors():
    assert ACTION_POLICY[("hosting", "deploy_production")] == "public_deployment"
    assert ACTION_POLICY[("smtp", "send_email")] == "unsolicited_outreach"

def test_companyos_money_handoffs_not_treated_as_live_executors():
    assert "banking" in FORBIDDEN_CONNECTORS
    assert "crypto" in FORBIDDEN_CONNECTORS

def test_old_trading_actions_not_wired():
    assert "execute_signed_swap" in FORBIDDEN_ACTIONS
    assert "sign_transaction" in FORBIDDEN_ACTIONS
