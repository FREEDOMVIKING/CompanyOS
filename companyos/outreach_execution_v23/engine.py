from __future__ import annotations
import hashlib, json, re, smtplib, ssl, time
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"

def now():
    return datetime.now(timezone.utc).isoformat()

def parse_env(path):
    d={}
    for line in Path(path).read_text(encoding="utf-8",errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s=s[7:].strip()
        k,v=s.split("=",1)
        d[k.strip()]=v.strip().strip("'").strip('"')
    return d

def save(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

def load(path,default):
    try:return json.loads(Path(path).read_text(encoding="utf-8"))
    except:return default

def valid_email(addr):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",addr or ""))

class OutreachExecutionV23:
    def __init__(self,root=ROOT):
        self.root=Path(root)
        self.env=parse_env(self.root/".env")
        self.queue=self.root/".companyos_outreach/queue.json"
        self.receipts=self.root/".companyos_outreach/receipts.json"
        self.audit=self.root/"ceo_memory/outreach_audit_v23.json"
        self.policy=self.root/"config/outreach_policy_v23.json"
        if not self.policy.exists():
            save(self.policy,{
              "version":23,
              "manual_approval_required":True,
              "max_messages_per_run":5,
              "duplicate_window_hours":72,
              "allow_bulk_send":False,
              "allow_external_send":False,
              "test_self_only":True
            })

    def health(self):
        return {
          "status":"companyos_v23_outreach_execution_ready",
          "smtp_host_present":bool(self.env.get("COMPANYOS_SMTP_HOST")),
          "smtp_user_present":bool(self.env.get("COMPANYOS_SMTP_USERNAME")),
          "smtp_password_present":bool(self.env.get("COMPANYOS_SMTP_PASSWORD")),
          "sender_present":bool(self.env.get("COMPANYOS_SMTP_FROM")),
          "manual_approval_required":True,
          "external_send_enabled":bool(load(self.policy,{ }).get("allow_external_send",False)),
          "secret_values_printed":False
        }

    def _id(self,to,subject,body):
        raw=f"{to}|{subject}|{body}".encode()
        return hashlib.sha256(raw).hexdigest()[:24]

    def create(self,to,subject,body):
        if not valid_email(to):
            raise ValueError("invalid recipient email")
        if not subject.strip() or not body.strip():
            raise ValueError("subject/body required")
        q=load(self.queue,[])
        msg_id=self._id(to,subject,body)
        if any(x.get("message_id")==msg_id and x.get("status") not in ("FAILED","CANCELLED") for x in q):
            return {"status":"DUPLICATE_BLOCKED","message_id":msg_id}
        item={
          "message_id":msg_id,
          "to":to,
          "subject":subject,
          "body":body,
          "status":"REVIEW_REQUIRED",
          "approved":False,
          "created_at":now(),
          "updated_at":now()
        }
        q.append(item); save(self.queue,q)
        return {"status":"REVIEW_REQUIRED","message_id":msg_id,"recipient":to}

    def approve(self,message_id):
        q=load(self.queue,[])
        found=False
        for x in q:
            if x.get("message_id")==message_id:
                x["approved"]=True
                x["status"]="APPROVED"
                x["updated_at"]=now()
                found=True
        save(self.queue,q)
        return {"approved":found,"message_id":message_id}

    def _smtp_send(self,item):
        host=self.env.get("COMPANYOS_SMTP_HOST","")
        port=int(self.env.get("COMPANYOS_SMTP_PORT","587") or 587)
        user=self.env.get("COMPANYOS_SMTP_USERNAME","")
        password=self.env.get("COMPANYOS_SMTP_PASSWORD","")
        sender=self.env.get("COMPANYOS_SMTP_FROM",user)
        if not all((host,user,password,sender)):
            raise RuntimeError("smtp configuration incomplete")

        msg=EmailMessage()
        msg["From"]=sender
        msg["To"]=item["to"]
        msg["Subject"]=item["subject"]
        msg.set_content(item["body"])

        with smtplib.SMTP(host,port,timeout=15) as smtp:
            smtp.ehlo()
            if smtp.has_extn("starttls"):
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            smtp.login(user,password)
            smtp.send_message(msg)

    def send(self,message_id):
        policy=load(self.policy,{})
        q=load(self.queue,[])
        item=next((x for x in q if x.get("message_id")==message_id),None)
        if not item:
            return {"status":"NOT_FOUND","message_id":message_id}
        if not item.get("approved"):
            return {"status":"BLOCKED_NOT_APPROVED","message_id":message_id}

        sender=self.env.get("COMPANYOS_SMTP_FROM",self.env.get("COMPANYOS_SMTP_USERNAME",""))
        if policy.get("test_self_only",True) and item["to"].lower()!=sender.lower():
            return {"status":"BLOCKED_TEST_SELF_ONLY","message_id":message_id}
        if item["to"].lower()!=sender.lower() and not policy.get("allow_external_send",False):
            return {"status":"BLOCKED_EXTERNAL_SEND_DISABLED","message_id":message_id}

        receipts=load(self.receipts,[])
        if any(r.get("message_id")==message_id and r.get("status")=="SENT" for r in receipts):
            return {"status":"DUPLICATE_SEND_BLOCKED","message_id":message_id}

        started=time.time()
        try:
            self._smtp_send(item)
            item["status"]="SENT"
            result={"status":"SENT","message_id":message_id,
                    "latency_ms":round((time.time()-started)*1000,2),
                    "sent_at":now()}
        except Exception as e:
            item["status"]="FAILED"
            result={"status":"FAILED","message_id":message_id,
                    "error":f"{type(e).__name__}: {e}",
                    "failed_at":now()}

        item["updated_at"]=now()
        save(self.queue,q)
        receipts.append(result)
        save(self.receipts,receipts)
        return result

    def test_self(self):
        sender=self.env.get("COMPANYOS_SMTP_FROM",self.env.get("COMPANYOS_SMTP_USERNAME",""))
        if not valid_email(sender):
            return {"status":"BLOCKED_NO_VALID_SELF_ADDRESS"}
        created=self.create(
            sender,
            "CompanyOS V23 Outreach Self-Test",
            "CompanyOS V23 outreach execution self-test. No customer outreach was performed."
        )
        mid=created.get("message_id")
        if created.get("status")=="DUPLICATE_BLOCKED":
            return created
        self.approve(mid)
        return self.send(mid)

    def queue_status(self):
        q=load(self.queue,[])
        return {
          "total":len(q),
          "review_required":sum(x.get("status")=="REVIEW_REQUIRED" for x in q),
          "approved":sum(x.get("status")=="APPROVED" for x in q),
          "sent":sum(x.get("status")=="SENT" for x in q),
          "failed":sum(x.get("status")=="FAILED" for x in q)
        }
