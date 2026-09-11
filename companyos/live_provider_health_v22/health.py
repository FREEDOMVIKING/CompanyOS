from __future__ import annotations
import json, socket, ssl, smtplib, time
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

class LiveProviderHealthV22:
    def __init__(self,root=ROOT):
        self.root=Path(root)
        self.env=parse_env(self.root/".env")
        self.report=self.root/"ceo_memory/live_provider_health_v22.json"

    def smtp_probe(self):
        host=self.env.get("COMPANYOS_SMTP_HOST","")
        port=int(self.env.get("COMPANYOS_SMTP_PORT","587") or 587)
        user=self.env.get("COMPANYOS_SMTP_USERNAME","")
        password=self.env.get("COMPANYOS_SMTP_PASSWORD","")

        result={
            "provider":"gmail_smtp" if "gmail" in host.lower() else "generic_smtp",
            "host_present":bool(host),
            "port":port,
            "username_present":bool(user),
            "password_present":bool(password),
            "tcp_connect":False,
            "tls_ready":False,
            "auth_ok":False,
            "message_sent":False,
            "latency_ms":None,
            "error":None,
        }

        if not all((host,user,password)):
            result["error"]="missing_smtp_configuration"
            return result

        started=time.time()
        try:
            with smtplib.SMTP(host,port,timeout=12) as smtp:
                smtp.ehlo()
                result["tcp_connect"]=True
                if smtp.has_extn("starttls"):
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                    result["tls_ready"]=True
                elif port==465:
                    result["tls_ready"]=True
                smtp.login(user,password)
                result["auth_ok"]=True
        except Exception as e:
            result["error"]=f"{type(e).__name__}: {e}"
        result["latency_ms"]=round((time.time()-started)*1000,2)
        return result

    def run(self):
        smtp=self.smtp_probe()
        status="HEALTHY" if smtp["auth_ok"] else "DEGRADED"
        out={
            "status":"companyos_v22_live_provider_health_complete",
            "updated_at":now(),
            "providers":{
                "START_OUTREACH":{
                    "health_state":status,
                    "provider":smtp["provider"],
                    "tcp_connect":smtp["tcp_connect"],
                    "tls_ready":smtp["tls_ready"],
                    "auth_ok":smtp["auth_ok"],
                    "message_sent":False,
                    "latency_ms":smtp["latency_ms"],
                    "error":smtp["error"],
                }
            },
            "network_requests_sent":True,
            "customer_messages_sent":False,
            "external_business_actions_executed":False,
            "financial_actions_executed":False,
            "secret_values_printed":False
        }
        save(self.report,out)
        return out

    def recovery_plan(self):
        health=self.run()
        p=health["providers"]["START_OUTREACH"]
        if p["health_state"]=="HEALTHY":
            action="READY_FOR_NON_SENDING_OUTREACH_TESTS"
            retry=False
        else:
            action="RETRY_WITH_BACKOFF"
            retry=True
        plan={
            "status":"companyos_v22_recovery_plan_ready",
            "provider":"START_OUTREACH",
            "health_state":p["health_state"],
            "recommended_action":action,
            "retry_enabled":retry,
            "retry_schedule_seconds":[30,120,600] if retry else [],
            "send_customer_email":False
        }
        save(self.root/"ceo_memory/provider_recovery_plan_v22.json",plan)
        return plan
