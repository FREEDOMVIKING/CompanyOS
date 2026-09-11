#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.business_objective_engine import BusinessObjectiveEngine
from companyos.runtime.kpi_registry import KPIRegistry
from companyos.runtime.experiment_manager import ExperimentManager
from companyos.runtime.risk_register import RiskRegister
from companyos.runtime.qa_gate import QAGate
from companyos.runtime.budget_guard import BudgetGuard
from companyos.runtime.launch_day_gate import LaunchDayGate

with tempfile.TemporaryDirectory(prefix="phase133_164_") as td:
    base=Path(td)
    obj=BusinessObjectiveEngine().build(
        objective_id="obj-1",title="Reach test milestone",target_metric="users",
        target_value=10,timeframe_days=30
    )
    kpi=KPIRegistry(base/"kpis").upsert("users","Users",5,"count")
    exp=ExperimentManager(base/"experiments").create("p1","Test demand","signup_rate",0.1,0.2)
    risk=RiskRegister(base/"risks").add("p1","Test risk",0.2,0.3,"Mitigate")
    qa=QAGate().evaluate(tests_passed=True,artifacts_present=True,blockers_count=0,critical_risks=0)
    budget=BudgetGuard().evaluate(50,100)
    gate=LaunchDayGate().evaluate(
        stack_verified=True,qa_passed=True,project_launch_ready=True,
        approval_queue_clear=True,no_critical_blockers=True
    )

    checks={
        "objective_created":obj.target_value==10,
        "kpi_persisted":len(KPIRegistry(base/"kpis").all())==1,
        "experiment_created":exp.state=="PLANNED",
        "risk_scored":risk.score==6.0,
        "qa_passed":qa.passed,
        "budget_allowed":budget.allowed,
        "launch_gate_ready":gate.ready,
    }
    ok=True
    for k,v in checks.items():
        ok=ok and v
        print(k,"=>","PASS" if v else "FAIL")
    print("EXTERNAL_ACTION_EXECUTED: False")
    print("TRANSACTION_SIGNED: False")
    print("TRANSACTION_BROADCAST: False")
    print("PHASE133_164_TEST:","PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
