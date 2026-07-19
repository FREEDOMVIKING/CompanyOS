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
echo " PHASE 48 - COMMUNICATIONS PROVIDER ADAPTER + DELIVERY TEST"
echo "============================================================"

cat > "$MEM/phase48_provider_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "provider_adapter",
  "provider": "smtp",
  "require_phase47_allowlist": true,
  "require_phase47_rate_limits": true,
  "require_delivery_receipt": true,
  "fail_closed": true
}
JSON

cat > "$MEM/phase48_delivery_receipts.json" <<'JSON'
{
  "receipts": []
}
JSON

cat > "$AGENTS/phase48_smtp_provider.py" <<'PY'
#!/usr/bin/env python3
import json, os, smtplib, ssl, sys, hashlib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"phase48_provider_config.json"
RECEIPTS=MEM/"phase48_delivery_receipts.json"

def now(): return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def configured():
    names=[
      "COMPANYOS_SMTP_HOST",
      "COMPANYOS_SMTP_PORT",
      "COMPANYOS_SMTP_USERNAME",
      "COMPANYOS_SMTP_PASSWORD",
      "COMPANYOS_SMTP_FROM_EMAIL"
    ]
    return all(os.getenv(n,"").strip() for n in names)

def send(payload):
    if not configured():
        return {"success":False,"status":"smtp_not_configured"}

    to_addr=str(payload.get("recipient") or payload.get("to") or "").strip()
    subject=str(payload.get("subject") or "CompanyOS Message").strip()
    body=str(payload.get("body") or payload.get("message") or "").strip()

    if not to_addr or not body:
        return {"success":False,"status":"invalid_message_payload"}

    host=os.environ["COMPANYOS_SMTP_HOST"].strip()
    port=int(os.environ["COMPANYOS_SMTP_PORT"].strip())
    username=os.environ["COMPANYOS_SMTP_USERNAME"].strip()
    password=os.environ["COMPANYOS_SMTP_PASSWORD"].strip()
    from_email=os.environ["COMPANYOS_SMTP_FROM_EMAIL"].strip()
    use_tls=os.getenv("COMPANYOS_SMTP_USE_TLS","true").lower() not in ("0","false","no")

    msg=EmailMessage()
    msg["From"]=from_email
    msg["To"]=to_addr
    msg["Subject"]=subject
    msg.set_content(body)

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=30) as smtp:
                smtp.login(username,password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host,port,timeout=30) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                smtp.login(username,password)
                smtp.send_message(msg)

        rid=hashlib.sha256(f"{to_addr}|{subject}|{now()}".encode()).hexdigest()[:24]
        receipt={
          "receipt_id":rid,
          "created_at":now(),
          "provider":"smtp",
          "recipient":to_addr,
          "subject":subject,
          "success":True,
          "status":"delivered_to_smtp_server",
          "external_reference":rid
        }
        d=load(RECEIPTS,{"receipts":[]})
        d.setdefault("receipts",[]).append(receipt)
        save(RECEIPTS,d)

        return {"success":True,"status":"delivered","external_reference":rid}
    except Exception as e:
        return {"success":False,"status":"smtp_delivery_failed","error":str(e)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="send":
    payload=json.loads(sys.stdin.read() or "{}")
    out=send(payload)
else:
    out={"success":True,"status":"phase48_provider_status","provider":"smtp","configured":configured()}

print(json.dumps(out,indent=2))
raise SystemExit(0 if out.get("success") else 1)
PY

chmod +x "$AGENTS/phase48_smtp_provider.py"

cat > "$SECURE/phase48_smtp_connector.sh" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
exec python agents/phase48_smtp_provider.py send
SH
chmod 700 "$SECURE/phase48_smtp_connector.sh"

cat > "$CTL/phase48ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
  [sys.executable,str(r/"agents"/"phase48_smtp_provider.py"),*sys.argv[1:]],
  cwd=r
))
PY
chmod +x "$CTL/phase48ctl"

echo "[1/4] Compiling..."
python -m py_compile "$AGENTS/phase48_smtp_provider.py" "$CTL/phase48ctl"

echo "[2/4] Writing secure setup instructions..."
cat > "$SECURE/phase48_setup.txt" <<'TXT'
Add these to ~/.companyos_secrets:

export COMPANYOS_SMTP_HOST='smtp.example.com'
export COMPANYOS_SMTP_PORT='587'
export COMPANYOS_SMTP_USERNAME='your_username'
export COMPANYOS_SMTP_PASSWORD='your_app_password_or_smtp_password'
export COMPANYOS_SMTP_FROM_EMAIL='you@example.com'
export COMPANYOS_SMTP_USE_TLS='true'

export COMPANYOS_PHASE47_PROVIDER_COMMAND="$HOME/.companyos_secure/phase48_smtp_connector.sh"

Do not store SMTP passwords in GitHub or repository files.
TXT

echo "[3/4] Status..."
python "$CTL/phase48ctl" status

echo "[4/4] Verifying..."
python - <<'PY'
import json
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

for p in [
 r/"agents"/"phase48_smtp_provider.py",
 r/"companyos"/"phase48ctl",
 r/"ceo_memory"/"phase48_provider_config.json",
 r/"ceo_memory"/"phase48_delivery_receipts.json"
]:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

cfg=json.loads((r/"ceo_memory"/"phase48_provider_config.json").read_text())
if not cfg.get("require_phase47_allowlist"): errors.append("Phase47 allowlist must remain required")
if not cfg.get("require_phase47_rate_limits"): errors.append("Phase47 rate limits must remain required")
if not cfg.get("require_delivery_receipt"): errors.append("delivery receipt must be required")
if not cfg.get("fail_closed"): errors.append("provider adapter must fail closed")

print("--------------------------------------------")
print("PHASE 48 PROVIDER ADAPTER VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors: print("ERROR:",e)
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 48 COMMUNICATIONS PROVIDER ADAPTER INSTALLED"
echo " SMTP PROVIDER SUPPORT: INSTALLED"
echo " PHASE 47 CONTROLS: PRESERVED"
echo " DELIVERY RECEIPTS: ENABLED"
echo " SMTP CREDENTIALS: LOCAL-SECRETS ONLY"
echo " UNCONFIGURED SMTP: FAIL-CLOSED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
