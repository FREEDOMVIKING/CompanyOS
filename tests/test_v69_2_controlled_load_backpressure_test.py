from pathlib import Path
import json

ROOT = Path.home() / "companyos"

def report():
    return json.loads(
        (ROOT/"audit/COMPANYOS_V69_2_CONTROLLED_LOAD_BACKPRESSURE_TEST.json").read_text()
    )

def test_all_controlled_load_tiers_pass():
    d=report()
    assert d["load_scaling_pass"] is True
    assert all(x["pass"] for x in d["tiers"])

def test_expected_backpressure_thresholds_and_batches():
    d=report()
    expected={
        "LOW":(100,1,16),
        "MEDIUM":(300,2,32),
        "HIGH":(600,3,48),
        "CRITICAL":(900,4,64),
    }
    for row in d["tiers"]:
        load,divisor,batch=expected[row["tier"]]
        assert row["load"]==load
        assert row["decision"]["producer_divisor"]==divisor
        assert row["decision"]["execution_batch"]==batch
        assert row["decision"]["boost_type"]=="research"
        assert row["completed_delta"]==batch
        assert row["failed_delta"]==0
        assert row["queued_delta"]==-batch

def test_execution_batch_has_runtime_consumer():
    d=report()
    assert d["execution_batch_wired"] is True
    assert d["execution_batch_consumers"]

def test_producer_divisor_wiring_is_reported_not_assumed():
    d=report()
    assert isinstance(d["producer_throttle_wired"], bool)
    assert isinstance(d["producer_divisor_consumers"], list)

def test_no_real_queue_or_external_actions():
    d=report()
    assert d["real_companyos_queue_modified"] is False
    assert d["external_actions_performed"] is False
    assert d["financial_actions_performed"] is False
    assert d["email_actions_performed"] is False
    assert d["deployment_actions_performed"] is False
