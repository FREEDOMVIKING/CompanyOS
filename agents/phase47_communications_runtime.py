#!/usr/bin/env python3
import json, os, sys, hashlib, subprocess, shlex
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase47_communications_config.json"
ALLOW=MEM/"phase47_recipient_allowlist.json"
RECEIPTS=MEM/"phase47_delivery_receipts.json"
IDEM=MEM/"phase47_idempotency.json"
STATE=MEM/"phase47_state.json"
AUDIT=MEM/"phase47_audit.jsonl"

def now():
    return datetime.now(timezone.utc)

def iso():
    return now().isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def audit(x):
    with AUDIT.open("a") as f:
        f.write(json.dumps({"at":iso(),**x})+"\n")

def recipient_allowed(channel,recipient):
    for r in load(ALLOW,{"recipients":[]}).get("recipients",[]):
        if r.get("enabled") and r.get("channel")==channel and r.get("recipient")==recipient:
            return True
    return False

def risky_text(text):
    t=(text or "").lower()
    contractual=("sign this contract","binding agreement","legally binding","execute agreement")
    financial=("guaranteed payment","wire funds","send payment immediately","commit funds")
    if any(x in t for x in contractual): return "contractual_language_requires_owner_approval"
    if any(x in t for x in financial): return "financial_commitment_language_requires_owner_approval"
    return None

def msg_key(channel,recipient,subject,body):
    seed="|".join([channel,recipient,subject or "",body or ""])
    return hashlib.sha256(seed.encode()).hexdigest()

def daily_count(recipient):
    receipts=load(RECEIPTS,{"receipts":[]}).get("receipts",[])
    cutoff=now()-timedelta(hours=24)
    n=0
    for r in receipts:
        if r.get("recipient")!=recipient or not r.get("success"): continue
        try:
            ts=datetime.fromisoformat(r.get("created_at"))
            if ts>=cutoff:n+=1
        except: pass
    return n

def execute(payload):
    cfg=load(CFG,{})
    channel=str(payload.get("channel","email"))
    recipient=str(payload.get("recipient") or payload.get("to") or "")
    subject=str(payload.get("subject") or "")
    body=str(payload.get("body") or payload.get("message") or "")

    reasons=[]
    if not recipient: reasons.append("recipient_missing")
    if not body: reasons.append("message_body_missing")
    if cfg.get("require_recipient_allowlist") and not recipient_allowed(channel,recipient):
        reasons.append("recipient_not_allowlisted")

    risk=risky_text(body)
    if risk: reasons.append(risk)

    if daily_count(recipient)>=int(cfg.get("max_messages_per_recipient_per_day",3)):
        reasons.append("recipient_daily_rate_limit_exceeded")

    key=msg_key(channel,recipient,subject,body)
    idem=load(IDEM,{"message_keys":[]})
    if key in set(idem.get("message_keys",[])):
        reasons.append("duplicate_message_blocked")

    if reasons:
        out={"success":False,"status":"phase47_message_blocked","reasons":reasons}
        audit({"recipient":recipient,"channel":channel,**out})
        return out

    cmd=os.getenv("COMPANYOS_COMMUNICATIONS_COMMAND","").strip()
    if not cmd:
        return {
          "success":False,
          "status":"connector_command_not_configured",
          "required_env":"COMPANYOS_COMMUNICATIONS_COMMAND"
        }

    connector_payload={
      "channel":channel,
      "recipient":recipient,
      "subject":subject,
      "body":body,
      "metadata":payload.get("metadata",{})
    }

    p=subprocess.run(
      shlex.split(cmd),
      input=json.dumps(connector_payload),
      text=True,
      capture_output=True,
      timeout=300,
      env=os.environ.copy()
    )

    try:r=json.loads(p.stdout)
    except:
        r={
          "success":False,
          "status":"invalid_connector_output",
          "return_code":p.returncode,
          "stdout":p.stdout[-1500:],
          "stderr":p.stderr[-1000:]
        }

    success=(p.returncode==0 and bool(r.get("success")))
    receipt={
      "receipt_id":hashlib.sha256(f"{key}|{iso()}".encode()).hexdigest()[:24],
      "created_at":iso(),
      "channel":channel,
      "recipient":recipient,
      "subject":subject,
      "success":success,
      "status":r.get("status"),
      "external_reference":r.get("external_reference") or r.get("id"),
      "message_key":key
    }

    receipts=load(RECEIPTS,{"receipts":[]})
    receipts.setdefault("receipts",[]).append(receipt)
    save(RECEIPTS,receipts)

    if success:
        idem.setdefault("message_keys",[]).append(key)
        save(IDEM,idem)

    out={
      "success":success,
      "status":"phase47_message_delivered" if success else "phase47_message_failed",
      "receipt":receipt,
      "connector_result":r
    }
    audit({"recipient":recipient,"channel":channel,"success":success,"status":out["status"]})
    return out

def status():
    cfg=load(CFG,{})
    allow=load(ALLOW,{"recipients":[]})
    return {
      "success":True,
      "status":"phase47_communications_status",
      "connector_configured":bool(os.getenv("COMPANYOS_COMMUNICATIONS_COMMAND","").strip()),
      "config":cfg,
      "allowlisted_recipient_count":sum(1 for r in allow.get("recipients",[]) if r.get("enabled")),
      "state":load(STATE,{})
    }

a=sys.argv[1] if len(sys.argv)>1 else "status"

if a=="send":
    if len(sys.argv)<3:
        out={"success":False,"status":"usage","usage":"send JSON_PAYLOAD"}
    else:
        out=execute(json.loads(sys.argv[2]))
elif a=="status":
    out=status()
else:
    out={"success":False,"status":"unknown_action"}

print(json.dumps(out,indent=2))
raise SystemExit(0 if out.get("success") else 1)
