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
