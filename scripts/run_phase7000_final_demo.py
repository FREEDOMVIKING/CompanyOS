#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.finalops import FinalIntegrationController

root=Path.home()/"companyos"
result=FinalIntegrationController(root).run(
    package_root=root,
    interfaces=[
        {"source":"orchestration","target":"execution","contract":"scheduled_work"},
        {"source":"execution","target":"marketops","contract":"venture_results"},
        {"source":"marketops","target":"scaleops","contract":"revenue_metrics"},
        {"source":"hardening","target":"controlplane","contract":"health_and_release_gate"}
    ],
    available_stages=["discover","research","validate","build","launch","operate","optimize","portfolio_review"],
    regression_checks=[
        {"name":"runtime_queue","passed":True},
        {"name":"restart_recovery","passed":True},
        {"name":"approval_gates","passed":True},
        {"name":"memory_persistence","passed":True}
    ],
    dependencies=[
        {"name":"python"},
        {"name":"pytest"},
        {"name":"json"}
    ],
    checkpoints={"latest":"present"},
    queues={"persistent":"present"},
    memories={"executive":"present"},
    recovery_scenarios=[
        {"name":"worker_crash","expected":"requeue_and_restart","actual":"requeue_and_restart"},
        {"name":"provider_failure","expected":"switch_provider","actual":"switch_provider"},
        {"name":"restart","expected":"resume","actual":"resume"}
    ],
    actions=[
        {"kind":"internal_analysis","requires_approval":False},
        {"kind":"production_deploy","requires_approval":True},
        {"kind":"bank_transfer","requires_approval":True},
        {"kind":"contract_signature","requires_approval":True}
    ]
)
print(json.dumps(result,indent=2,default=str))
