from companyos.runtime import adaptive_offload_calibration_resumer as r


def test_seconds_until_utc_reset():
    assert r.seconds_until_utc_reset(0)==86400
    assert r.seconds_until_utc_reset(86399)==1
    assert r.seconds_until_utc_reset(86400)==86400


def test_resume_status_scope():
    assert r.resume_eligible_status("blocked_daily_cap") is True
    assert r.resume_eligible_status("waiting_daily_cap") is True
    assert r.resume_eligible_status("completed") is False
    assert r.resume_eligible_status("incomplete") is False


def test_required_slots_empty_blocked_state():
    assert r.required_slots({"status":"blocked_daily_cap"})==4


def test_required_slots_after_two_completed():
    state={"results":[
        {"requested_shards":1,"status":"completed"},
        {"requested_shards":2,"status":"completed"},
    ]}
    assert r.required_slots(state)==2
