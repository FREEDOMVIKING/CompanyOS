from companyos.runtime import adaptive_offload_calibration as cal


def test_duration_seconds_prefers_completed_timestamp():
    job={
        "created_at_unix":10,
        "dispatched_at_unix":20,
        "completed_at_unix":35,
        "updated_at_unix":40,
    }
    assert cal.duration_seconds(job)==15.0


def test_summarize_four_green_runs():
    rows=[
        {"requested_shards":1,"status":"completed","duration_seconds":10,"shard_results":1},
        {"requested_shards":2,"status":"completed","duration_seconds":12,"shard_results":2},
        {"requested_shards":4,"status":"completed","duration_seconds":14,"shard_results":4},
        {"requested_shards":8,"status":"completed","duration_seconds":18,"shard_results":8},
    ]
    s=cal.summarize(rows)
    assert s["runs"]==4
    assert s["completed"]==4
    assert s["failed"]==0
    assert s["success_rate"]==1.0
    assert s["by_shards"]["8"]["shard_results"]==8


def test_plan_is_progressive_capacity_probe():
    assert cal.PLAN==(1,2,4,8)
