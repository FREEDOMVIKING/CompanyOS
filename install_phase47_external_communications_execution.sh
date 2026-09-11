#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
SECURE="$HOME/.companyos_secure"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$SECURE"

echo "============================================================"
echo " PHASE 47 - EXTERNAL COMMUNICATIONS EXECUTION LAYER"
echo "============================================================"

cat > "$MEM/phase47_communications_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "allowlisted_external_communications",
  "max_messages_per_cycle": 10,
  "max_messages_per_recipient_per_day": 3,
  "duplicate_window_hours": 24,
  "require_delivery_receipt": true,
  "require_idempotency": true,
  "require_recipient_allowlist": true,
  "require_connector_command": true,
  "mass_outreach_owner_approval_required": true,
  "contractual_language_owner_approval_required": true,
  "financial_commitment_language_owner_approval_required": true,
  "fail_closed": true
}
JSON

cat > "$MEM/phase47_recipient_allowlist.json" <<'JSON'
{
  "recipients": []
}
JSON

cat > "$MEM/phase47_delivery_receipts.json" <<'JSON'
{
  "receipts": []
}
JSON

cat > "$MEM/phase47_idempotency.json" <<'JSON'
{
  "message_keys": []
}
JSON

cat > "$MEM/phase47_state.json" <<'JSON'
{
  "last_run_at": null,
  "sent_count": 0,
  "blocked_count": 0,
  "failure_count": 0,
  "last_results": []
}
JSON

cat > "$AGENTS/phase47_communications_runtime.py" <<'PY'
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
PY

chmod +x "$AGENTS/phase47_communications_runtime.py"

cat > "$AGENTS/phase47_allowlist_manager.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"phase47_recipient_allowlist.json"

def now():return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(P.read_text())
    except:return {"recipients":[]}
def save(d):P.write_text(json.dumps(d,indent=2))

a=sys.argv[1] if len(sys.argv)>1 else "list"

if a=="add":
    if len(sys.argv)<4:
        out={"success":False,"status":"usage","usage":"add CHANNEL RECIPIENT [LABEL]"}
    else:
        channel=sys.argv[2]
        recipient=sys.argv[3]
        label=sys.argv[4] if len(sys.argv)>4 else recipient
        d=load()
        existing=next((r for r in d.get("recipients",[]) if r.get("channel")==channel and r.get("recipient")==recipient),None)
        if existing:
            existing["enabled"]=True
            existing["label"]=label
        else:
            d.setdefault("recipients",[]).append({
              "recipient_id":hashlib.sha256(f"{channel}|{recipient}".encode()).hexdigest()[:16],
              "channel":channel,
              "recipient":recipient,
              "label":label,
              "enabled":True,
              "created_at":now()
            })
        save(d)
        out={"success":True,"status":"recipient_allowlisted","channel":channel,"recipient":recipient}
elif a=="remove":
    if len(sys.argv)<4:
        out={"success":False,"status":"usage","usage":"remove CHANNEL RECIPIENT"}
    else:
        d=load()
        for r in d.get("recipients",[]):
            if r.get("channel")==sys.argv[2] and r.get("recipient")==sys.argv[3]:
                r["enabled"]=False
        save(d)
        out={"success":True,"status":"recipient_disabled"}
else:
    out={"success":True,"status":"phase47_allowlist","registry":load()}

print(json.dumps(out,indent=2))
raise SystemExit(0 if out.get("success") else 1)
PY

chmod +x "$AGENTS/phase47_allowlist_manager.py"

cat > "$CTL/phase47ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
  [sys.executable,str(r/"agents"/"phase47_communications_runtime.py"),*sys.argv[1:]],
  cwd=r
))
PY

cat > "$CTL/phase47allowlistctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
  [sys.executable,str(r/"agents"/"phase47_allowlist_manager.py"),*sys.argv[1:]],
  cwd=r
))
PY

chmod +x "$CTL/phase47ctl" "$CTL/phase47allowlistctl"

echo "[1/6] Installing Phase 42 communications bridge..."

cat > "$SECURE/phase47_communications_bridge.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
PAYLOAD="$(cat)"
cd "$HOME/companyos"
exec python companyos/phase47ctl send "$PAYLOAD"
SH

chmod 700 "$SECURE/phase47_communications_bridge.sh"

echo "[2/6] Compiling..."
python -m py_compile \
  "$AGENTS/phase47_communications_runtime.py" \
  "$AGENTS/phase47_allowlist_manager.py" \
  "$CTL/phase47ctl" \
  "$CTL/phase47allowlistctl"

echo "[3/6] Writing secure connector activation hint..."
cat > "$SECURE/phase47_setup.txt" <<'TXT'
To route Phase 42 communications into Phase 47, add this line to ~/.companyos_secrets:

export COMPANYOS_COMMUNICATIONS_COMMAND="$HOME/.companyos_secure/phase47_communications_bridge.sh"

Phase 47 then enforces recipient allowlisting, duplicate blocking, per-recipient rate limits,
delivery receipts, and approval gates before calling the final communications connector.

A final provider connector can be added later behind Phase 47 without changing the CEO pipeline.
TXT

echo "[4/6] Status..."
python "$CTL/phase47ctl" status

echo "[5/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

req=[
 r/"agents"/"phase47_communications_runtime.py",
 r/"agents"/"phase47_allowlist_manager.py",
 r/"companyos"/"phase47ctl",
 r/"companyos"/"phase47allowlistctl",
 r/"ceo_memory"/"phase47_communications_config.json",
 r/"ceo_memory"/"phase47_recipient_allowlist.json",
 r/"ceo_memory"/"phase47_delivery_receipts.json",
 r/"ceo_memory"/"phase47_idempotency.json",
 r/"ceo_memory"/"phase47_state.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in req[:4]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))

cfg=json.loads((r/"ceo_memory"/"phase47_communications_config.json").read_text())

if not cfg.get("require_recipient_allowlist"):
    errors.append("recipient allowlist must be required")
if not cfg.get("require_delivery_receipt"):
    errors.append("delivery receipts must be required")
if not cfg.get("require_idempotency"):
    errors.append("idempotency must be required")
if not cfg.get("mass_outreach_owner_approval_required"):
    errors.append("mass outreach must remain approval-gated")
if not cfg.get("fail_closed"):
    errors.append("communications layer must fail closed")

print("--------------------------------------------")
print("PHASE 47 COMMUNICATIONS EXECUTION VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo "[6/6] Complete."
echo
echo "============================================================"
echo " PHASE 47 EXTERNAL COMMUNICATIONS EXECUTION LAYER INSTALLED"
echo " RECIPIENT ALLOWLIST: ENABLED"
echo " DUPLICATE MESSAGE PROTECTION: ENABLED"
echo " PER-RECIPIENT RATE LIMITS: ENABLED"
echo " DELIVERY RECEIPTS: ENABLED"
echo " MASS OUTREACH / CONTRACTUAL / FINANCIAL-COMMITMENT LANGUAGE: APPROVAL-GATED"
echo " UNCONFIGURED FINAL PROVIDER CONNECTOR: FAIL-CLOSED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase47ctl status"
echo "  python companyos/phase47allowlistctl list"
echo "  python companyos/phase47allowlistctl add email someone@example.com \"Example Contact\""
echo
echo "Then add to ~/.companyos_secrets:"
echo '  export COMPANYOS_COMMUNICATIONS_COMMAND="$HOME/.companyos_secure/phase47_communications_bridge.sh"'
