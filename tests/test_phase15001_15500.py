from companyos.daemonops import AutonomousScheduler, TriggerRouter, SelfHealingSupervisor

def test_scheduler():
    assert AutonomousScheduler().due([{"kind":"x","every_ticks":5}],10)

def test_router():
    assert TriggerRouter().route({"kind":"revenue_signal"})["department"]=="growth"

def test_supervisor():
    assert SelfHealingSupervisor().evaluate([{"name":"w","healthy":False,"restart_count":0,"max_restarts":3}])[0]["action"]=="restart"
