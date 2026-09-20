from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from companyos.connectors_live.engine import ConnectorEngine
from companyos.governance.venture_identity_progression import candidate_ventures, evaluate_all
from companyos.runtime.stalled_stage_progression_controller import canonical_ventures
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
CONNECTOR_RT=ROOT/"companyos_runtime"/"connectors"

STATE=RT/"customer_acquisition_bridge_state.json"
LATEST=RT/"customer_acquisition_bridge_latest.json"
HISTORY=RT/"customer_acquisition_bridge_history.jsonl"
VERSION="V66.27"

EMAIL_RE=re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$",re.I)
CONTACT_KEYS=("business_email","contact_email","sales_email","prospect_email","email")
COMPANY_KEYS=("company","company_name","business","organization","prospect_company")
SOURCE_KEYS=("source_url","website","url","company_url","official_website","domain")
DESC_KEYS=("value_proposition","description","summary","offer","tagline","headline")
AUDIENCE_KEYS=("target_customer","target_audience","audience","customer_segment")
PERSONAL_DOMAINS={
    "gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com",
    "aol.com","proton.me","protonmail.com",
}

def load_json(path: Path, default: Any) -> Any:
    try:return json.loads(path.read_text())
    except Exception:return default

def save_json(path: Path, data: Any) -> None:
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp): os.unlink(tmp)
        except Exception: pass

def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")

def clean(v: Any, limit=600) -> str|None:
    if not isinstance(v,str): return None
    t=" ".join(v.split()).strip()
    if len(t)<2:return None
    if any(x in t.lower() for x in (
        "do not fabricate","system prompt","internal only","task queue","procurement"
    )):
        return None
    return t[:limit]

def authority() -> dict[str,bool]:
    try:
        from companyos.runtime.live_drl_strategy_governor import LIVE_AUTHORITY
        return {str(k):bool(v) for k,v in LIVE_AUTHORITY.items()}
    except Exception:
        return {}

def outreach_authorized() -> bool:
    a=authority()
    return bool(a.get("unsolicited_outreach") and a.get("external_irreversible_actions"))

def smtp_health() -> dict[str,Any]:
    try:
        e=ConnectorEngine()
        return ((e.health().get("connectors") or {}).get("smtp") or {})
    except Exception as exc:
        return {"configured":False,"enabled":False,"error":f"{type(exc).__name__}:{exc}"}

def roots_for(cid: str) -> list[Path]:
    rec=(candidate_ventures().get(cid) or {})
    out=[]
    for rel in rec.get("roots") or []:
        p=ROOT/rel
        if p.exists() and p.is_dir():out.append(p)
    return out

def walk(obj: Any, depth=0):
    if depth>8:return
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from walk(v,depth+1)
    elif isinstance(obj,list):
        for v in obj:
            yield from walk(v,depth+1)

def json_records(path: Path):
    try:text=path.read_text(errors="ignore")
    except Exception:return
    if path.suffix.lower()==".jsonl":
        for n,line in enumerate(text.splitlines(),1):
            try:o=json.loads(line)
            except Exception:continue
            for d in walk(o):
                yield d,f"{path}:{n}"
    elif path.suffix.lower()==".json":
        try:o=json.loads(text)
        except Exception:return
        for d in walk(o):
            yield d,str(path)

def candidate_files(cid: str) -> list[Path]:
    rows=[]
    seen=set()
    roots=roots_for(cid)
    extra=[
        RT/"specialist_evidence",
        RT/"reports",
        RT/"live_validation",
    ]
    for root in roots+extra:
        if not root.exists():continue
        try:paths=list(root.rglob("*"))
        except Exception:continue
        for p in paths:
            if not p.is_file() or p.suffix.lower() not in {".json",".jsonl"}:continue
            try:st=p.stat()
            except Exception:continue
            if st.st_size<=0 or st.st_size>1_500_000:continue
            rp=str(p.resolve())
            if rp in seen:continue
            seen.add(rp)
            rows.append((st.st_mtime,p))
    rows.sort(key=lambda x:-x[0])
    return [p for _,p in rows[:700]]

def own_sender_emails() -> set[str]:
    vals=set()
    for key in ("COMPANYOS_EMAIL","COMPANYOS_SMTP_USERNAME","SMTP_USERNAME","EMAIL_USERNAME"):
        v=os.environ.get(key)
        if v and "@" in v:vals.add(v.strip().lower())
    envp=ROOT/".env"
    if envp.exists():
        for raw in envp.read_text(errors="ignore").splitlines():
            if "=" not in raw or raw.lstrip().startswith("#"):continue
            k,v=raw.split("=",1)
            if k.strip() in {"COMPANYOS_EMAIL","COMPANYOS_SMTP_USERNAME","SMTP_USERNAME","EMAIL_USERNAME"}:
                v=v.strip().strip('"').strip("'")
                if "@" in v:vals.add(v.lower())
    return vals

def public_business_contact(d: dict[str,Any], source: str, own: set[str]) -> dict[str,Any]|None:
    if str(d.get("schema") or "")=="companyos.verified_public_business_prospect.v1":
        if d.get("relevance_verified") is not True:
            return None
        if d.get("email_domain_matches_official_site") is not True:
            return None

    email=None
    key_used=None
    for k in CONTACT_KEYS:
        v=d.get(k)
        if isinstance(v,str) and EMAIL_RE.match(v.strip()):
            email=v.strip().lower()
            key_used=k
            break
    if not email or email in own:return None

    domain=email.split("@",1)[1]
    company=None
    for k in COMPANY_KEYS:
        company=clean(d.get(k),200)
        if company:break
    source_url=None
    for k in SOURCE_KEYS:
        source_url=clean(d.get(k),500)
        if source_url:break

    explicitly_business = key_used in {"business_email","sales_email","prospect_email"}
    if domain in PERSONAL_DOMAINS and not (explicitly_business and source_url and company):
        return None

    if not (source_url or explicitly_business):
        return None

    return {
        "email":email,
        "company":company,
        "source_url":source_url,
        "source_artifact":source,
        "contact_field":key_used,
        "public_business_contact":True,
    }

def find_contacts(cid: str) -> list[dict[str,Any]]:
    own=own_sender_emails()
    out=[]
    seen=set()
    for p in candidate_files(cid):
        for d,source in json_records(p):
            c=public_business_contact(d,source,own)
            if not c:continue
            if c["email"] in seen:continue
            seen.add(c["email"])
            out.append(c)
    return out[:100]

def venture_copy(cid: str) -> dict[str,Any]:
    title=cid.replace("_"," ").title()
    desc=None
    audience=None
    live_url=None

    for p in candidate_files(cid):
        for d,_ in json_records(p):
            if not desc:
                for k in DESC_KEYS:
                    desc=clean(d.get(k),500)
                    if desc:break
            if not audience:
                for k in AUDIENCE_KEYS:
                    audience=clean(d.get(k),300)
                    if audience:break
            if not live_url:
                v=d.get("live_url")
                if isinstance(v,str) and v.startswith(("http://","https://")):
                    live_url=v.strip()
            for k in ("product_name","venture_name","title","name"):
                v=clean(d.get(k),160)
                if v:
                    title=v
                    break
            if desc and audience and live_url:
                return {"title":title,"description":desc,"audience":audience,"live_url":live_url}
    return {"title":title,"description":desc,"audience":audience,"live_url":live_url}

def executions() -> list[dict[str,Any]]:
    x=load_json(CONNECTOR_RT/"executions.json",[])
    return x if isinstance(x,list) else []

def execution_for(action_id: str) -> dict[str,Any]|None:
    for x in reversed(executions()):
        if str(x.get("action_id") or "")==str(action_id):
            return x
    return None

def materialize_outreach(cid: str, info: dict[str,Any], rec: dict[str,Any]) -> str:
    roots=roots_for(cid)
    if not roots:
        raise RuntimeError("canonical_venture_root_missing")
    result=rec.get("result") or {}
    d=roots[0]/"companyos_progress"
    d.mkdir(parents=True,exist_ok=True)
    p=d/f"outreach_result_{info['action_id']}.json"
    save_json(p,{
        "schema":"companyos.real_outreach_result.v1",
        "version":VERSION,
        "canonical_id":cid,
        "connector":"smtp",
        "action":"send_email",
        "action_id":info["action_id"],
        "ok":bool(result.get("ok")),
        "status":result.get("status"),
        "recipient":info.get("recipient"),
        "recipient_company":info.get("company"),
        "contact_source":info.get("source_url") or info.get("source_artifact"),
        "executed_at":rec.get("executed_at"),
        "materialized_at_unix":time.time(),
    })
    return str(p)

def day_key() -> str:
    return time.strftime("%Y-%m-%d",time.gmtime())

def queue_discovery_request(cid: str, copy: dict[str,Any], state: dict[str,Any]) -> dict[str,Any]:
    day=day_key()
    key=f"{cid}:{day}"
    done=set(state.get("discovery_requested") or [])
    if key in done:
        return {"created":False,"reason":"already_requested_today"}

    roots=roots_for(cid)
    if roots:
        p=roots[0]/"companyos_progress"/"prospect_discovery_request.json"
        p.parent.mkdir(parents=True,exist_ok=True)
        save_json(p,{
            "schema":"companyos.prospect_discovery_request.v1",
            "version":VERSION,
            "canonical_id":cid,
            "target_audience":copy.get("audience"),
            "live_url":copy.get("live_url"),
            "required_fields":[
                "company_name","public_business_email","official_website","fit_reason"
            ],
            "constraints":[
                "public business contacts only",
                "official/public source URL required",
                "do not contact anyone during discovery",
                "do not fabricate emails",
                "exclude private personal contact data",
            ],
            "created_at_unix":time.time(),
        })

    q=AutonomousTaskQueue()
    try:
        t=q.enqueue(
            task_type="research",
            priority=188,
            max_attempts=3,
            idempotency_key=f"customer-prospect-discovery:{cid}:{day}",
            payload={
                "venture_id":cid,
                "goal_id":f"customer-acquisition:{cid}",
                "stage":"research",
                "objective":(
                    "Acquire fresh external evidence for customer prospects for this launched venture. "
                    "Return up to five public business contacts from official/public sources with "
                    "company_name, public_business_email, official_website, and fit_reason. "
                    "Do not contact them during discovery and do not fabricate contact data."
                ),
                "target_audience":copy.get("audience"),
                "live_url":copy.get("live_url"),
            },
        )
        row={"created":True,"task_id":t.task_id,"state":t.state}
    except Exception as exc:
        row={"created":False,"error":f"{type(exc).__name__}:{exc}"}

    done.add(key)
    state["discovery_requested"]=sorted(done)[-365:]
    return row

def build_message(copy: dict[str,Any], contact: dict[str,Any]) -> tuple[str,str]|None:
    if not copy.get("live_url"):
        return None
    title=copy["title"]
    company=contact.get("company")
    greeting=f"Hello {company}," if company else "Hello,"
    desc=copy.get("description")
    body=[
        greeting,
        "",
        f"We've launched {title}.",
    ]
    if desc:
        body.append(desc)
    body += [
        "",
        f"You can take a look here: {copy['live_url']}",
        "",
        "If this is relevant to your business, reply to this email and we can continue the conversation.",
        "",
        "CompanyOS",
    ]
    return f"{title} — quick introduction", "\n".join(body)

def run_once() -> dict[str,Any]:
    state=load_json(STATE,{
        "pending":{},
        "sent":{},
        "daily":{},
        "discovery_requested":[],
    })
    pending=state.setdefault("pending",{})
    sent=state.setdefault("sent",{})
    daily=state.setdefault("daily",{})

    materialized=[]
    for cid,info in list(pending.items()):
        rec=execution_for(str(info.get("action_id") or ""))
        if not rec:continue
        result=rec.get("result") or {}
        if result.get("ok") is True:
            evidence=materialize_outreach(cid,info,rec)
            recipient=str(info.get("recipient") or "").lower()
            sent[f"{cid}:{recipient}"]={
                "action_id":info.get("action_id"),
                "evidence":evidence,
                "sent_at_unix":time.time(),
            }
            materialized.append({"canonical_id":cid,"evidence":evidence})
        pending.pop(cid,None)

    cap=max(1,min(int(os.getenv("COMPANYOS_CUSTOMER_ACQUISITION_DAILY_EMAIL_CAP","3")),20))
    today=day_key()
    used=int(daily.get(today,0) or 0)

    auth=outreach_authorized()
    health=smtp_health()
    smtp_ready=bool(health.get("configured") and health.get("enabled") and health.get("dry_run") is not True)

    queued=[]
    skipped=[]
    discovery=[]

    ventures=canonical_ventures()
    if not pending and used < cap:
        for cid,row in sorted(ventures.items()):
            if str(row.get("stage") or "")!="LAUNCH":
                continue

            copy=venture_copy(cid)
            contacts=find_contacts(cid)

            if not contacts:
                discovery.append({
                    "canonical_id":cid,
                    **queue_discovery_request(cid,copy,state),
                    "reason":"no_verified_public_business_contacts",
                })
                continue

            if not auth:
                skipped.append({"canonical_id":cid,"reason":"outreach_authority_not_enabled"})
                continue
            if not smtp_ready:
                skipped.append({"canonical_id":cid,"reason":"smtp_not_live_ready","smtp_health":health})
                continue

            selected=None
            for c in contacts:
                key=f"{cid}:{c['email'].lower()}"
                if key not in sent:
                    selected=c
                    break
            if not selected:
                skipped.append({"canonical_id":cid,"reason":"all_verified_contacts_already_contacted"})
                continue

            msg=build_message(copy,selected)
            if not msg:
                skipped.append({"canonical_id":cid,"reason":"launch_url_missing"})
                continue
            subject,body=msg

            engine=ConnectorEngine()
            item=engine.queue(
                "smtp",
                "send_email",
                {"to":selected["email"],"subject":subject,"body":body},
                risk="medium",
            )
            pending[cid]={
                "action_id":item.get("action_id"),
                "recipient":selected["email"],
                "company":selected.get("company"),
                "source_url":selected.get("source_url"),
                "source_artifact":selected.get("source_artifact"),
                "queued_at_unix":time.time(),
            }
            daily[today]=used+1
            queued.append({
                "canonical_id":cid,
                "action_id":item.get("action_id"),
                "recipient_domain":selected["email"].split("@",1)[1],
                "company":selected.get("company"),
            })
            break

    save_json(STATE,{
        "version":VERSION,
        "updated_at_unix":time.time(),
        "pending":pending,
        "sent":sent,
        "daily":daily,
        "discovery_requested":state.get("discovery_requested") or [],
    })

    refreshed=[]
    if materialized:
        try:refreshed=evaluate_all()
        except Exception:refreshed=[]

    report={
        "version":VERSION,
        "mode":"verified_public_business_customer_acquisition",
        "outreach_authorized":auth,
        "smtp_ready":smtp_ready,
        "smtp_health":health,
        "daily_cap":cap,
        "daily_used":int(daily.get(today,0) or 0),
        "queued":queued,
        "pending":pending,
        "materialized":materialized,
        "prospect_discovery":discovery,
        "skipped":skipped,
        "refreshed_ventures":[
            {
                "canonical_id":x.get("canonical_id"),
                "stage":x.get("stage"),
                "verified_external_stage":x.get("verified_external_stage"),
            }
            for x in refreshed
        ],
        "rules":{
            "public_business_contacts_only":True,
            "source_provenance_required":True,
            "personal_email_domains_restricted":True,
            "one_outreach_action_per_run":True,
            "daily_cap_enforced":True,
            "financial_actions":False,
            "authority_switches_changed":False,
        },
        "timestamp_unix":time.time(),
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,report)
    return report
