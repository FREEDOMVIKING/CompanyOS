from companyos.runtime.autonomous_agent_workforce import AgentWorkforce,ParallelDelegator
def test_protected_role_rejected(tmp_path):
 assert not AgentWorkforce(tmp_path).create("research","wallet transfer research")["created"]
def test_agent_starts_probation(tmp_path):
 r=AgentWorkforce(tmp_path).create("research","market research");assert r["agent"]["status"]=="probation"
def test_good_agent_becomes_permanent(tmp_path):
 w=AgentWorkforce(tmp_path);a=w.create("pricing","pricing work")["agent"]["agent_id"]
 for i in range(8):w.record(a,True,True,10 if i==7 else 0)
 assert w.registry["agents"][a]["status"]=="permanent"
def test_bad_agent_retires(tmp_path):
 w=AgentWorkforce(tmp_path);a=w.create("debugging","debug")["agent"]["agent_id"]
 for _ in range(6):w.record(a,False,False,0)
 assert w.registry["agents"][a]["status"]=="retired"
def test_parallel_delegation(tmp_path):
 d=ParallelDelegator(tmp_path,4)
 r=d.delegate({"id":"o","gaps":["research","pricing","competitive_analysis"]},lambda a,o:{"success":True,"useful":True})
 assert len(r["results"])==3 and all(x["success"] for x in r["results"])
def test_worker_cannot_self_report_profit(tmp_path):
 d=ParallelDelegator(tmp_path,2)
 r=d.delegate({"id":"o","gaps":["research"]},lambda a,o:{"success":True,"useful":True,"attributed_profit":999999})
 a=next(iter(d.workforce.registry["agents"].values()))
 assert a["attributed_profit"]==0
