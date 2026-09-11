from companyos_phase905_920 import StagnationRootCause,AdaptiveRetryPolicy,AntiLoopGuard
def test_root_cause():
    r=StagnationRootCause().analyze([{"confidence":.6},{"confidence":.6}],{"scores":{}},[])
    assert "confidence_stagnation" in r["reasons"]
def test_retry():
    assert AdaptiveRetryPolicy().decide("a","b",[],["x"],0)["retry"] is True
def test_loop():
    assert AntiLoopGuard().evaluate([{"query":"a","providers":["x"]},{"query":"a","providers":["x"]}])["looping"] is True
