from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

RT=Path.home()/".companyos_runtime"
STATE=RT/"persistent_host_scout_state.json"
HISTORY=RT/"persistent_host_scout_history.jsonl"
QUEUE=RT/"server_acquisition_queue.json"
DISCOVERED=RT/"server_host_discoveries.json"

INTERVAL=max(900,int(os.getenv("COMPANYOS_HOST_SCOUT_INTERVAL_SECONDS","10800")))
AUTO_HANDOFF=os.getenv("COMPANYOS_AUTO_REMOTE_HANDOFF","1")=="1"
ALLOW_PAID_PROVISIONING=os.getenv("COMPANYOS_HOST_SCOUT_ALLOW_PAID_PROVISIONING","0")=="1"
MAX_MONTHLY_USD=max(0.0,float(os.getenv("COMPANYOS_HOST_SCOUT_MAX_MONTHLY_USD","7.00")))

HOST_PROFILES={
    "railway_free":{
        "provider":"railway",
        "kind":"paas",
        "official_url":"https://railway.com/pricing",
        "signup_url":"https://railway.com",
        "official_domains":["railway.com","docs.railway.com"],
        "monthly_cost_usd":1.00,
        "free_or_trial":True,
        "always_on_expected":True,
        "ssh":False,
        "persistent_disk":True,
        "ram_mb":512,
        "notes":"30-day trial credit, then low-cost Free plan; verify current terms before provisioning.",
        "credential_env":["RAILWAY_TOKEN"],
    },
    "koyeb_free":{
        "provider":"koyeb",
        "kind":"paas",
        "official_url":"https://www.koyeb.com/docs/reference/instances",
        "signup_url":"https://app.koyeb.com",
        "official_domains":["koyeb.com","www.koyeb.com","app.koyeb.com"],
        "monthly_cost_usd":0.00,
        "free_or_trial":True,
        "always_on_expected":False,
        "ssh":False,
        "persistent_disk":False,
        "ram_mb":512,
        "notes":"Free instance; currently scales to zero after idle time.",
        "credential_env":["KOYEB_TOKEN","KOYEB_API_TOKEN"],
    },
    "render_free":{
        "provider":"render",
        "kind":"paas",
        "official_url":"https://render.com/docs/free",
        "signup_url":"https://dashboard.render.com",
        "official_domains":["render.com","dashboard.render.com"],
        "monthly_cost_usd":0.00,
        "free_or_trial":True,
        "always_on_expected":False,
        "ssh":False,
        "persistent_disk":False,
        "ram_mb":512,
        "notes":"Free web service; currently spins down on idle and filesystem is ephemeral.",
        "credential_env":["RENDER_API_KEY"],
    },
    "digitalocean_basic_512":{
        "provider":"digitalocean",
        "kind":"vps",
        "official_url":"https://www.digitalocean.com/pricing/droplets",
        "signup_url":"https://cloud.digitalocean.com/registrations/new",
        "official_domains":["digitalocean.com","www.digitalocean.com","cloud.digitalocean.com"],
        "monthly_cost_usd":4.00,
        "free_or_trial":False,
        "always_on_expected":True,
        "ssh":True,
        "persistent_disk":True,
        "ram_mb":512,
        "notes":"Low-cost VPS candidate with SSH and persistent storage.",
        "credential_env":["DIGITALOCEAN_ACCESS_TOKEN","DO_API_TOKEN"],
    },
    "hetzner_cx23":{
        "provider":"hetzner",
        "kind":"vps",
        "official_url":"https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/",
        "signup_url":"https://accounts.hetzner.com/signUp",
        "official_domains":["hetzner.com","www.hetzner.com","docs.hetzner.com","accounts.hetzner.com"],
        "monthly_cost_usd":6.49,
        "free_or_trial":False,
        "always_on_expected":True,
        "ssh":True,
        "persistent_disk":True,
        "ram_mb":4096,
        "notes":"Low-cost cloud VPS candidate; current price profile must be revalidated before provisioning.",
        "credential_env":["HETZNER_API_TOKEN","HCLOUD_TOKEN"],
    },
    "github_actions":{
        "provider":"github",
        "kind":"ephemeral_compute",
        "official_url":"https://github.com/features/actions",
        "signup_url":"https://github.com",
        "official_domains":["github.com","docs.github.com"],
        "monthly_cost_usd":0.00,
        "free_or_trial":True,
        "always_on_expected":False,
        "ssh":False,
        "persistent_disk":False,
        "ram_mb":None,
        "notes":"Burst compute only; not a persistent primary home.",
        "credential_env":["GH_TOKEN","GITHUB_TOKEN"],
    },
}

SEARCH_QUERIES=(
    "official free persistent Linux server Python hosting VPS pricing",
    "official low cost VPS 1GB RAM cloud server pricing",
    "official Python background worker hosting free tier",
    "official always on container hosting free tier",
)

KNOWN_DOMAINS={
    d
    for row in HOST_PROFILES.values()
    for d in row.get("official_domains") or []
}


def load(path:Path,default:Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass


def append_history(obj:dict[str,Any])->None:
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,default=str)+"\n")
    try:
        lines=HISTORY.read_text(encoding="utf-8").splitlines()
        if len(lines)>400:
            HISTORY.write_text("\n".join(lines[-400:])+"\n",encoding="utf-8")
    except Exception:
        pass


def env_values()->dict[str,str]:
    out=dict(os.environ)
    for path in (
        Path.home()/"companyos/.env",
        Path.home()/".companyos_runtime/.env",
        Path.home()/".config/companyos/.env",
    ):
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line=raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k,v=line.split("=",1)
                k=k.strip()
                v=v.strip().strip("'").strip('"')
                if k and v and k not in out:
                    out[k]=v
        except Exception:
            pass
    return out


def credential_state(profile:dict[str,Any])->dict[str,Any]:
    vals=env_values()
    names=list(profile.get("credential_env") or [])
    found=[n for n in names if vals.get(n)]
    return {
        "credential_present":bool(found),
        "credential_names_present":found,
        "secret_values_emitted":False,
    }


def http_probe(url:str)->dict[str,Any]:
    req=urllib.request.Request(
        url,
        headers={
            "User-Agent":"CompanyOS-PersistentHostScout/69.36",
            "Accept":"text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
        },
    )
    started=time.time()
    try:
        with urllib.request.urlopen(req,timeout=18) as r:
            raw=r.read(160000)
            return {
                "reachable":True,
                "http_status":int(r.status),
                "latency_seconds":round(time.time()-started,3),
                "content_sha256":hashlib.sha256(raw).hexdigest()[:20],
                "bytes_sampled":len(raw),
            }
    except urllib.error.HTTPError as exc:
        return {
            "reachable":False,
            "http_status":int(exc.code),
            "latency_seconds":round(time.time()-started,3),
        }
    except Exception as exc:
        return {
            "reachable":False,
            "error":f"{type(exc).__name__}:{str(exc)[:250]}",
            "latency_seconds":round(time.time()-started,3),
        }


def candidate_score(profile:dict[str,Any],cred:dict[str,Any],probe:dict[str,Any])->float:
    score=0.0
    kind=str(profile.get("kind") or "")
    monthly=float(profile.get("monthly_cost_usd") or 0)

    if probe.get("reachable"):
        score+=15
    if profile.get("always_on_expected"):
        score+=30
    if profile.get("persistent_disk"):
        score+=18
    if profile.get("ssh"):
        score+=20
    if cred.get("credential_present"):
        score+=12
    if monthly==0:
        score+=10
    elif monthly<=MAX_MONTHLY_USD:
        score+=7
    else:
        score-=20
    if kind=="ephemeral_compute":
        score-=25
    if not profile.get("always_on_expected"):
        score-=12

    ram=profile.get("ram_mb")
    if isinstance(ram,(int,float)):
        if ram>=1024:score+=8
        elif ram>=512:score+=3
        else:score-=5

    return round(max(0.0,min(100.0,score)),2)


def official_profiles()->list[dict[str,Any]]:
    rows=[]
    for host_id,profile in HOST_PROFILES.items():
        p=dict(profile)
        cred=credential_state(p)
        probe=http_probe(str(p["official_url"]))
        score=candidate_score(p,cred,probe)
        monthly=float(p.get("monthly_cost_usd") or 0)
        paid=monthly>0
        rows.append({
            "host_id":host_id,
            **p,
            **cred,
            "probe":probe,
            "score":score,
            "within_monthly_cap":monthly<=MAX_MONTHLY_USD,
            "automatic_paid_provisioning_allowed":bool(ALLOW_PAID_PROVISIONING and paid and monthly<=MAX_MONTHLY_USD),
            "automatic_account_creation_allowed":False,
        })
    rows.sort(key=lambda x:(-float(x.get("score") or 0),float(x.get("monthly_cost_usd") or 0),str(x.get("host_id"))))
    return rows


def domain_of(url:str)->str:
    try:
        return (urllib.parse.urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def dynamic_discovery()->dict[str,Any]:
    discovered=[]
    errors=[]
    try:
        from companyos.runtime import provider_connector_router as router
    except Exception as exc:
        return {"discoveries":[],"errors":[f"router_import:{type(exc).__name__}:{str(exc)[:200]}"]}

    for query in SEARCH_QUERIES:
        try:
            out=router.search_web(query,max_results=8)
            for row in out.get("results") or []:
                if not isinstance(row,dict):
                    continue
                url=str(row.get("url") or "").strip()
                if not url.startswith("https://"):
                    continue
                host=domain_of(url)
                discovered.append({
                    "query":query,
                    "title":row.get("title") or row.get("name"),
                    "url":url,
                    "domain":host,
                    "source":row.get("source") or out.get("provider"),
                    "known_official_domain":host in KNOWN_DOMAINS or any(host.endswith("."+d) for d in KNOWN_DOMAINS),
                    "eligible_for_automatic_interaction":False,
                })
        except Exception as exc:
            errors.append(f"{type(exc).__name__}:{str(exc)[:300]}")

    dedup=[]
    seen=set()
    for row in discovered:
        key=(row.get("domain"),row.get("url"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
        if len(dedup)>=40:
            break

    out={
        "schema":"companyos.server_host_discoveries.v69_36",
        "updated_at_unix":time.time(),
        "discoveries":dedup,
        "errors":errors[-20:],
        "automatic_interaction_with_newly_discovered_domains":False,
    }
    atomic(DISCOVERED,out)
    return out


def acquisition_queue(candidates:list[dict[str,Any]])->dict[str,Any]:
    tasks=[]
    for row in candidates:
        if row.get("kind")=="ephemeral_compute":
            continue
        cred=bool(row.get("credential_present"))
        monthly=float(row.get("monthly_cost_usd") or 0)

        if cred:
            status="credential_present_connector_needed"
        elif monthly==0:
            status="official_account_or_token_needed"
        elif monthly<=MAX_MONTHLY_USD:
            status="official_account_or_token_needed_paid_candidate"
        else:
            status="over_monthly_cap"

        tasks.append({
            "host_id":row.get("host_id"),
            "provider":row.get("provider"),
            "kind":row.get("kind"),
            "score":row.get("score"),
            "status":status,
            "signup_url":row.get("signup_url"),
            "official_url":row.get("official_url"),
            "monthly_cost_usd":monthly,
            "within_monthly_cap":monthly<=MAX_MONTHLY_USD,
            "always_on_expected":bool(row.get("always_on_expected")),
            "ssh":bool(row.get("ssh")),
            "credential_present":cred,
            "automatic_account_creation_allowed":False,
            "automatic_paid_provisioning_allowed":bool(row.get("automatic_paid_provisioning_allowed")),
            "next_action":"build_or_use_official_provider_connector" if cred else "obtain_provider_account_or_token_through_official_flow",
        })

    out={
        "schema":"companyos.server_acquisition_queue.v69_36",
        "updated_at_unix":time.time(),
        "tasks":tasks,
        "max_monthly_usd":MAX_MONTHLY_USD,
        "paid_provisioning_enabled":ALLOW_PAID_PROVISIONING,
        "financial_action_performed":False,
    }
    atomic(QUEUE,out)
    return out


def authorized_remote_nodes()->list[dict[str,Any]]:
    try:
        from companyos.runtime import remote_runtime_fabric as fabric
    except Exception:
        return []

    rows=[]
    for n in fabric.inventory().get("nodes") or []:
        if not isinstance(n,dict):
            continue
        if not n.get("enabled",True):
            continue
        if not n.get("authorized_by_user"):
            continue
        if str(n.get("role") or "")!="primary":
            continue
        try:
            probe=fabric.probe_node(n)
        except Exception as exc:
            probe={"healthy":False,"error":f"{type(exc).__name__}:{str(exc)[:300]}"}
        rows.append({
            "name":n.get("name"),
            "provider":n.get("provider"),
            "role":n.get("role"),
            "authorized_by_user":True,
            "healthy":bool(probe.get("healthy")),
            "probe":probe,
        })
    return rows


def maybe_handoff(nodes:list[dict[str,Any]])->dict[str,Any]:
    if not AUTO_HANDOFF:
        return {"attempted":False,"reason":"auto_handoff_disabled"}

    healthy=[n for n in nodes if n.get("healthy")]
    if not healthy:
        return {"attempted":False,"reason":"no_authorized_healthy_primary"}

    target=healthy[0]
    try:
        from companyos.runtime import remote_runtime_fabric as fabric
        result=fabric.handoff_primary(str(target["name"]))
        return {
            "attempted":True,
            "target":target["name"],
            "provider":target.get("provider"),
            "result":result,
        }
    except Exception as exc:
        return {
            "attempted":True,
            "target":target["name"],
            "provider":target.get("provider"),
            "error":f"{type(exc).__name__}:{str(exc)[:800]}",
        }


def scan(allow_handoff:bool=True)->dict[str,Any]:
    started=time.time()
    candidates=official_profiles()
    discoveries=dynamic_discovery()
    q=acquisition_queue(candidates)
    nodes=authorized_remote_nodes()

    top=candidates[0] if candidates else None
    handoff=maybe_handoff(nodes) if allow_handoff else {"attempted":False,"reason":"scan_only"}

    out={
        "schema":"companyos.persistent_host_scout.v69_36",
        "updated_at_unix":time.time(),
        "scan_seconds":round(time.time()-started,3),
        "healthy":True,
        "active_host_search":True,
        "scan_interval_seconds":INTERVAL,
        "max_monthly_usd":MAX_MONTHLY_USD,
        "paid_provisioning_enabled":ALLOW_PAID_PROVISIONING,
        "auto_remote_handoff_enabled":AUTO_HANDOFF,
        "official_candidates":candidates,
        "top_candidate":top,
        "dynamic_discoveries_count":len(discoveries.get("discoveries") or []),
        "dynamic_discovery_errors":discoveries.get("errors") or [],
        "authorized_primary_nodes":nodes,
        "handoff":handoff,
        "acquisition_task_count":len(q.get("tasks") or []),
        "internet_wide_scanning_performed":False,
        "credential_harvesting_performed":False,
        "automatic_account_creation_performed":False,
        "financial_action_performed":False,
    }
    atomic(STATE,out)
    append_history({
        "ts":out["updated_at_unix"],
        "top_candidate":(top or {}).get("host_id"),
        "top_score":(top or {}).get("score"),
        "dynamic_discoveries_count":out["dynamic_discoveries_count"],
        "authorized_primary_count":len(nodes),
        "handoff_attempted":bool(handoff.get("attempted")),
    })
    return out


def status()->dict[str,Any]:
    return load(STATE,{"status":"not_run","state_path":str(STATE)})


def loop()->None:
    while True:
        try:
            scan(allow_handoff=True)
        except Exception as exc:
            atomic(STATE,{
                "schema":"companyos.persistent_host_scout.v69_36",
                "healthy":False,
                "active_host_search":True,
                "updated_at_unix":time.time(),
                "error":f"{type(exc).__name__}:{str(exc)[:1000]}",
            })
        time.sleep(INTERVAL)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("scan","status","loop","queue"))
    p.add_argument("--no-handoff",action="store_true")
    a=p.parse_args()

    if a.command=="scan":
        out=scan(allow_handoff=not a.no_handoff)
    elif a.command=="status":
        out=status()
    elif a.command=="queue":
        out=load(QUEUE,{"tasks":[]})
    else:
        loop()
        return 0

    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
