#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; CONN=ROOT/"connectors"
REG=MEM/"treasury_wallet_registry.json"
OUT=MEM/"deposit_monitor_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run():
    wallets=load(REG,{}).get("wallets",[])
    rows=[]
    for w in wallets:
        adapter=CONN/f"{w.get('chain')}_treasury_adapter.py"
        if not adapter.exists():
            rows.append({"wallet_id":w.get("wallet_id"),"chain":w.get("chain"),"status":"adapter_missing"})
            continue
        p=subprocess.run([sys.executable,str(adapter),"scan",json.dumps(w)],cwd=ROOT,text=True,capture_output=True,timeout=120)
        rows.append({"wallet_id":w.get("wallet_id"),"chain":w.get("chain"),"return_code":p.returncode,
                     "status":"scan_complete" if p.returncode==0 else "scan_failed",
                     "stdout":p.stdout[-1500:],"stderr":p.stderr[-500:]})
    report={"generated_at":now(),"wallet_count":len(wallets),"results":rows}
    OUT.write_text(json.dumps(report,indent=2))
    return {"success":True,"status":"deposit_monitor_cycle_complete","report":report}
print(json.dumps(run(),indent=2))
