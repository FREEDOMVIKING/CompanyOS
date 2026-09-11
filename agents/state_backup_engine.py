#!/usr/bin/env python3
import json, shutil, sys, tarfile
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"; B=R/"backups"/"state_snapshots"
CFG=M/"state_backup_config.json"; STATE=M/"state_backup_state.json"; HEALTH=M/"state_backup_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()

def backup():
    cfg=load(CFG,{})
    B.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target=B/f"companyos_state_{stamp}.tar.gz"
    with tarfile.open(target,"w:gz") as tar:
        if M.exists(): tar.add(M,arcname="ceo_memory")
    snaps=sorted(B.glob("companyos_state_*.tar.gz"),key=lambda p:p.stat().st_mtime,reverse=True)
    for old in snaps[int(cfg.get("retention_count",12)):]:
        old.unlink(missing_ok=True)
    state={"last_backup_at":now(),"last_backup":str(target),"backup_count":len(list(B.glob("companyos_state_*.tar.gz")))}
    save(STATE,state);save(HEALTH,{"healthy":target.exists(),"last_checked_at":now(),**state})
    return {"success":target.exists(),"status":"state_backup_complete","state":state}

def list_backups():
    B.mkdir(parents=True,exist_ok=True)
    return {"success":True,"status":"state_backups","backups":[str(x) for x in sorted(B.glob("*.tar.gz"),reverse=True)]}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="backup":r=backup()
elif a=="list":r=list_backups()
elif a=="status":r={"success":True,"status":"state_backup_status","state":load(STATE,{}),"health":load(HEALTH,{})}
else:r={"success":False,"status":"unknown_action","allowed":["backup","list","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
