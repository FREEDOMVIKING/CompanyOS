from companyos_phase809_824 import RetryLoopGuard, MissionDeduplicator, QueueDrainMetrics

def test_retry_guard():
    assert RetryLoopGuard().evaluate({"attempts":3},4)["allowed"] is True
    assert RetryLoopGuard().evaluate({"attempts":4},4)["allowed"] is False

def test_dedupe():
    missions=[
        {"mission_type":"research","context":{"venture_id":"v","objective":"x"}},
        {"mission_type":"research","context":{"venture_id":"v","objective":"x"}},
    ]
    assert len(MissionDeduplicator().dedupe(missions)["dropped"]) == 1

def test_drain_metrics():
    assert QueueDrainMetrics().compare({"count":5},{"count":3})["drained"] is True
