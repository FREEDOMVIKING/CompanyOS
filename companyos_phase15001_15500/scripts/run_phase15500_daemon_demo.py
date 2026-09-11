#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.daemonops import CEOAutonomousLoop

root=Path.home()/"companyos"
loop=CEOAutonomousLoop(root)

result=loop.run_tick(
    tick=10,
    scheduled_tasks=[
        {"kind":"daily_health","every_ticks":1,"priority":9,"payload":{"scope":"all"}},
        {"kind":"market_scan","every_ticks":5,"priority":8,"payload":{"scope":"opportunities"}},
        {"kind":"portfolio_review","every_ticks":10,"priority":7,"payload":{"scope":"ventures"}}
    ],
    incoming_events=[
        {"kind":"market_signal","priority":9,"payload":{"signal":"new demand spike"}},
        {"kind":"customer_issue","priority":8,"payload":{"severity":"high"}}
    ],
    workers=[
        {"name":"research_worker","healthy":True,"restart_count":0,"max_restarts":3},
        {"name":"build_worker","healthy":False,"restart_count":1,"max_restarts":3},
        {"name":"ops_worker","healthy":True,"restart_count":0,"max_restarts":3}
    ]
)

print(json.dumps(result,indent=2,default=str))
