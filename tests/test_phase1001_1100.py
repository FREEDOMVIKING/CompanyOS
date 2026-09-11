from companyos_phase1001_1100 import IrreversibleActionGate,LaunchMonitor,RevenueTelemetry

def test_gate():
    assert IrreversibleActionGate().evaluate("production_traffic_cutover")["requires_approval"] is True

def test_health():
    assert LaunchMonitor().evaluate({"error_rate":0.0,"availability":1.0,"p95_latency_ms":100})["healthy"] is True

def test_revenue():
    assert RevenueTelemetry().compute(100,2,20,0)["arpu"]==50.0
