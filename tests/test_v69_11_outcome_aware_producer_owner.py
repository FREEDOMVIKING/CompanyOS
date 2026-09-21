from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"companyos/runtime/productive_autonomy_watchdog.py").read_text()

def test_owner_fields_and_timeout_present():
    assert "V69.11 outcome-aware profit-first producer ownership" in S
    assert "COMPANYOS_PROFIT_FIRST_PRODUCER_OWNER_TIMEOUT_SECONDS" in S
    assert "profit_first_producer_owner_orchestration_id" in S
    assert "profit_first_producer_owner_candidate_count_baseline" in S

def test_running_owner_blocks_later_producers():
    assert '"active_profit_first_producer_owner"' in S
    assert "owner_blocking or producer_dispatched_this_tick" in S
    assert "not owner_blocking" in S

def test_terminal_or_timeout_releases_owner():
    assert 'state in {"COMPLETED", "FAILED", "HALTED", "CANCELLED"}' in S
    assert '"terminal_with_candidates"' in S
    assert '"terminal_without_candidates"' in S
    assert '"owner_timeout"' in S
    assert "_clear_profit_first_producer_owner(ws)" in S

def test_candidate_materialization_does_not_release_running_owner():
    assert "Candidate materialization by itself does not release a RUNNING owner." in S

def test_v69_10_handoff_remains_secondary_guard():
    assert "COMPANYOS_PROFIT_FIRST_PRODUCER_HANDOFF_COOLDOWN_SECONDS" in S
    assert '"shared_profit_first_producer_handoff_cooldown"' in S
