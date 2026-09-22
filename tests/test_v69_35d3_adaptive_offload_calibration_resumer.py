from companyos.runtime import adaptive_offload_calibration_resumer as r

def test_seconds_until_reset_range():
    assert r.seconds_until_utc_reset(100.0)==86300

def test_required_slots_all_missing():
    assert r.required_slots({"status":"blocked_daily_cap"})==4

def test_required_slots_partial():
    state={"results":[
        {"requested_shards":1,"status":"completed"},
        {"requested_shards":2,"status":"completed"},
    ]}
    assert r.required_slots(state)==2

def test_only_cap_wait_states_auto_resume():
    assert r.resume_eligible_status("blocked_daily_cap") is True
    assert r.resume_eligible_status("waiting_daily_cap") is True
    assert r.resume_eligible_status("failed") is False
    assert r.resume_eligible_status("error") is False
