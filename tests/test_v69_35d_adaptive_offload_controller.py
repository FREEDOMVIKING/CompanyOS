from companyos.runtime import adaptive_offload_controller as aoc


def queue_with(statuses):
    jobs=[]
    now=1000.0
    for i,status in enumerate(statuses):
        jobs.append({
            "job_id":f"j{i}",
            "status":status,
            "created_at_unix":now+i,
            "dispatched_at_unix":now+i,
            "updated_at_unix":now+10+i,
            "completed_at_unix":now+10+i,
        })
    return {"jobs":jobs}


def test_baseline_shards():
    assert aoc.baseline_shards(1)==1
    assert aoc.baseline_shards(2)==2
    assert aoc.baseline_shards(5)==4
    assert aoc.baseline_shards(20)==8


def test_high_phone_pressure_accelerates_remote():
    d=aoc.decide(
        kind="research",
        work_items=8,
        queue=queue_with(["completed"]*8),
        phone={
            "cpu_count":8,
            "load1":7.0,
            "load_ratio":0.875,
            "memory_used_ratio":0.8,
            "phone_pressure_score":0.9,
        },
    )
    assert d["recommended_shards"]==8
    assert d["mode"]=="remote_max"


def test_external_failure_rate_throttles():
    d=aoc.decide(
        kind="research",
        work_items=12,
        queue=queue_with(["failed","failed","completed","failed","failed"]),
        phone={
            "cpu_count":8,
            "load1":4.0,
            "load_ratio":0.5,
            "memory_used_ratio":0.5,
            "phone_pressure_score":0.5,
        },
    )
    assert d["recommended_shards"]==1
    assert d["mode"]=="degraded_external"


def test_pytest_keeps_remote_parallelism_when_healthy():
    d=aoc.decide(
        kind="pytest",
        work_items=100,
        queue=queue_with(["completed"]*8),
        phone={
            "cpu_count":8,
            "load1":1.0,
            "load_ratio":0.125,
            "memory_used_ratio":0.4,
            "phone_pressure_score":0.2,
        },
    )
    assert d["recommended_shards"]>=4


def test_worker_metrics_success_rate():
    m=aoc.worker_metrics(queue_with(["completed","completed","failed","completed"]))
    assert m["terminal_jobs"]==4
    assert m["external_success_rate"]==0.75


def test_no_sensitive_external_actions_enabled():
    d=aoc.decide(
        kind="research",
        work_items=4,
        queue=queue_with(["completed"]*4),
        phone={
            "cpu_count":8,
            "load1":1.0,
            "load_ratio":0.125,
            "memory_used_ratio":0.4,
            "phone_pressure_score":0.2,
        },
    )
    assert d["quota_bypass_allowed"] is False
    assert d["arbitrary_shell_payloads_allowed"] is False
    assert d["financial_actions_allowed"] is False
    assert d["account_creation_allowed"] is False
    assert d["deployments_allowed"] is False
