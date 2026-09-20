from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WATCHDOG=ROOT/"companyos/runtime/productive_autonomy_watchdog.py"

def source():
    return WATCHDOG.read_text()

def test_shared_handoff_state_is_present():
    s=source()
    assert "V69.10 serialized profit-first producer arbitration" in s
    assert "COMPANYOS_PROFIT_FIRST_PRODUCER_HANDOFF_COOLDOWN_SECONDS" in s
    assert 'ws["profit_first_producer_last_dispatch_unix"]' in s
    assert 'ws["profit_first_producer_last_name"]' in s

def test_all_three_root_producers_pass_through_shared_arbiter():
    s=source()
    assert '_record_profit_first_producer(' in s
    assert '"profit_first_enrichment_expansion"' in s
    assert '"candidate_recovery"' in s
    assert '"profit_first_research"' in s
    assert s.count('"shared_profit_first_producer_handoff_cooldown"') >= 3

def test_same_tick_dispatch_is_serialized():
    s=source()
    assert "producer_dispatched_this_tick" in s
    assert "producer_window_open" in s
    assert "producer_handoff_remaining" in s

def test_existing_producer_specific_cooldowns_remain():
    s=source()
    assert "COMPANYOS_PROFIT_FIRST_ENRICHMENT_COOLDOWN_SECONDS" in s
    assert "COMPANYOS_CANDIDATE_RECOVERY_COOLDOWN_SECONDS" in s
    assert "COMPANYOS_PROFIT_FIRST_RESEARCH_COOLDOWN_SECONDS" in s
