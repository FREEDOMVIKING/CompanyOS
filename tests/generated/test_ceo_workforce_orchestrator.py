from companyos.runtime.ceo_workforce_orchestrator import CEOWorkforceOrchestrator
def test_profit_priority_does_not_invent(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 assert c.priority({"expected_profit":None,"confidence":None})==0
def test_adaptive_workers_are_bounded(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 assert c.worker_budget(1000,list("abcdefghij"))<=8
def test_ceo_creates_work_packets(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 r=c.run({"id":"opp1","title":"research pricing market","gaps":["research","pricing","market_validation"],"confidence":.8})
 assert r["opportunity_id"]=="opp1"
 assert len(r["delegation"]["results"])>=1
 assert all(x["success"] for x in r["delegation"]["results"])
def test_no_authority_delegation(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 r=c.run({"id":"opp2","title":"market research","gaps":["research"]})
 assert r["financial_authority_delegated"] is False
 assert r["credential_authority_delegated"] is False
def test_permanent_agent_reused(tmp_path):
 c=CEOWorkforceOrchestrator(tmp_path)
 a=c.workforce.create("research","profit-directed research")["agent"]["agent_id"]
 for i in range(8): c.workforce.record(a,True,True,10 if i==7 else 0)
 r=c.run({"id":"opp3","gaps":["research"],"title":"research"})
 assert r["delegation"]["results"][0]["agent_id"]==a
