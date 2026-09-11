#!/usr/bin/env python3
import argparse, json
from companyos.canonicalexec import CanonicalExecutionGateway, ExecutionRequest

p=argparse.ArgumentParser()
s=p.add_subparsers(dest="cmd", required=True)
s.add_parser("status")
t=s.add_parser("test"); t.add_argument("--action", default="health_check")
a=p.parse_args()
g=CanonicalExecutionGateway()
if a.cmd=="status":
    print(json.dumps(g.status(), indent=2, sort_keys=True))
else:
    r=g.execute(ExecutionRequest(action=a.action, payload={"probe":True}))
    print(json.dumps(r.to_dict(), indent=2, sort_keys=True))
