from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RT = Path.home()/".companyos_runtime"
STATE = RT/"provider_acquisition_state.json"
QUEUE = RT/"provider_onboarding_queue.json"
CATALOG = RT/"provider_catalog.json"

# Official/public provider targets only.
# "free" means a documented no-charge allowance exists; it does not mean unlimited use.
PROVIDERS: dict[str,dict[str,Any]] = {
    "github_public_rest": {
        "kind":"public_data",
        "auth":"none",
        "free":True,
        "free_summary":"Public REST reads can be used without authentication; rate limits apply.",
        "official_url":"https://api.github.com",
        "signup_url":"https://github.com/signup",
        "credential_env":[],
        "account_required":False,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":1,
    },
    "tavily": {
        "kind":"web_search",
        "auth":"api_key",
        "free":True,
        "free_summary":"Free account includes monthly API credits.",
        "official_url":"https://www.tavily.com",
        "signup_url":"https://app.tavily.com",
        "credential_env":["TAVILY_API_KEY"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":2,
    },
    "brave_search": {
        "kind":"web_search",
        "auth":"api_key",
        "free":True,
        "free_summary":"Brave Search API includes monthly free credits.",
        "official_url":"https://brave.com/search/api/",
        "signup_url":"https://api.search.brave.com/app/keys",
        "credential_env":["BRAVE_SEARCH_API_KEY","BRAVE_API_KEY"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":3,
    },
    "groq": {
        "kind":"ai_inference",
        "auth":"api_key",
        "free":True,
        "free_summary":"Free tier with model-specific request/token limits.",
        "official_url":"https://console.groq.com",
        "signup_url":"https://console.groq.com",
        "credential_env":["GROQ_API_KEY"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":2,
    },
    "gemini": {
        "kind":"ai_inference",
        "auth":"api_key",
        "free":True,
        "free_summary":"Gemini API has a Free usage tier; active limits vary by project/model.",
        "official_url":"https://ai.google.dev",
        "signup_url":"https://aistudio.google.com",
        "credential_env":["GEMINI_API_KEY","GOOGLE_API_KEY"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":3,
    },
    "cloudflare_workers_ai": {
        "kind":"ai_inference",
        "auth":"api_token_plus_account",
        "free":True,
        "free_summary":"Workers AI includes a daily free allocation; model restrictions apply.",
        "official_url":"https://developers.cloudflare.com/workers-ai/",
        "signup_url":"https://dash.cloudflare.com/sign-up",
        "credential_env":["CLOUDFLARE_API_TOKEN","CF_API_TOKEN"],
        "account_id_env":["CLOUDFLARE_ACCOUNT_ID","CF_ACCOUNT_ID"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":4,
    },
    "huggingface": {
        "kind":"ai_inference",
        "auth":"token",
        "free":True,
        "free_summary":"Free users receive a small monthly Inference Providers credit.",
        "official_url":"https://huggingface.co",
        "signup_url":"https://huggingface.co/join",
        "credential_env":["HF_TOKEN","HUGGINGFACE_TOKEN","HUGGING_FACE_HUB_TOKEN"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":5,
    },
    "openai": {
        "kind":"ai_inference",
        "auth":"api_key",
        "free":False,
        "free_summary":"No guaranteed free API allowance; an account may have promotional/free credits.",
        "official_url":"https://platform.openai.com",
        "signup_url":"https://platform.openai.com",
        "credential_env":["OPENAI_API_KEY","COMPANYOS_OPENAI_API_KEY","OPENAI_KEY"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":6,
    },
    "github_actions": {
        "kind":"compute",
        "auth":"github_account",
        "free":True,
        "free_summary":"GitHub Free includes monthly Actions minutes for private repositories; public repositories have different billing rules.",
        "official_url":"https://github.com/features/actions",
        "signup_url":"https://github.com/signup",
        "credential_env":["GITHUB_TOKEN","GH_TOKEN"],
        "account_required":True,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":7,
    },
    "github_models": {
        "kind":"ai_inference",
        "auth":"retired",
        "free":False,
        "retired":True,
        "free_summary":"Retired; do not attempt to create or obtain access.",
        "official_url":"https://docs.github.com/en/github-models",
        "signup_url":None,
        "credential_env":[],
        "account_required":False,
        "official_registration_api":False,
        "automated_signup_permitted":False,
        "priority":99,
    },
}

AUTHORIZED_ENV_FILES = (
    Path.home()/"companyos/.env",
    Path.home()/".companyos_runtime/.env",
    Path.home()/".config/companyos/.env",
)

def _atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)

def _read_env_file(path: Path) -> dict[str,str]:
    out={}
    try:
        text=path.read_text(encoding="utf-8")
    except Exception:
        return out
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        k=k.strip()
        v=v.strip().strip('"').strip("'")
        if k and v:
            out[k]=v
    return out

def _authorized_secret_sources() -> list[tuple[str,dict[str,str]]]:
    sources=[("process_env",dict(os.environ))]
    for p in AUTHORIZED_ENV_FILES:
        vals=_read_env_file(p)
        if vals:
            sources.append((f"env_file:{p}",vals))
    return sources

def _fingerprint(value: str) -> str:
    # One-way short fingerprint for inventory correlation; never reveal the secret.
    return hashlib.sha256(value.encode("utf-8","ignore")).hexdigest()[:12]

def discover_credentials() -> tuple[dict[str,Any],dict[str,dict[str,str]]]:
    inventory={}
    private_values={}
    sources=_authorized_secret_sources()

    for name,provider in PROVIDERS.items():
        found=[]
        private_values[name]={}
        keys=list(provider.get("credential_env") or []) + list(provider.get("account_id_env") or [])
        for env_name in keys:
            for source_name,vals in sources:
                value=(vals.get(env_name) or "").strip()
                if not value:
                    continue
                found.append({
                    "name":env_name,
                    "source":source_name,
                    "fingerprint":_fingerprint(value),
                })
                private_values[name][env_name]=value
                break
        inventory[name]={
            "credential_material_present":bool(found),
            "credential_refs":found,
        }
    return inventory,private_values

def _http_json(url: str, headers: dict[str,str] | None=None, timeout: int=15) -> tuple[int,dict[str,Any],dict[str,str]]:
    req=urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent":"CompanyOS-ProviderAcquisition/69.26",
            "Accept":"application/json",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(300000).decode("utf-8","replace")
            try:
                data=json.loads(raw)
            except Exception:
                data={"raw_preview":raw[:500]}
            return int(r.status),data,{k.lower():v for k,v in r.headers.items()}
    except urllib.error.HTTPError as exc:
        raw=exc.read(2000).decode("utf-8","replace")
        try:
            data=json.loads(raw)
        except Exception:
            data={"raw_preview":raw[:500]}
        return int(exc.code),data,{k.lower():v for k,v in exc.headers.items()}

def probe_github_public() -> dict[str,Any]:
    status,data,headers=_http_json("https://api.github.com/rate_limit")
    core=((data.get("resources") or {}).get("core") or {}) if isinstance(data,dict) else {}
    return {
        "reachable":status==200,
        "http_status":status,
        "limit":core.get("limit"),
        "remaining":core.get("remaining"),
        "reset":core.get("reset"),
        "authenticated":bool(headers.get("x-oauth-scopes")),
    }

def probe_keyed_provider(name: str, secrets: dict[str,str]) -> dict[str,Any]:
    # Only zero-spend/read-only auth probes. No inference request is generated here.
    try:
        if name=="tavily":
            key=secrets.get("TAVILY_API_KEY")
            return {"probe":"credential_presence","authenticated":bool(key),"unverified_until_first_search":bool(key)} if key else {"probe":"skipped","reason":"credential_missing"}

        if name=="brave_search":
            key=secrets.get("BRAVE_SEARCH_API_KEY") or secrets.get("BRAVE_API_KEY")
            return {"probe":"credential_presence","authenticated":bool(key),"unverified_until_first_search":bool(key)} if key else {"probe":"skipped","reason":"credential_missing"}

        if name=="groq":
            key=secrets.get("GROQ_API_KEY")
            if not key:
                return {"probe":"skipped","reason":"credential_missing"}
            status,data,_=_http_json(
                "https://api.groq.com/openai/v1/models",
                {"Authorization":f"Bearer {key}"},
            )
            return {"probe":"models","http_status":status,"authenticated":status==200}

        if name=="gemini":
            key=secrets.get("GEMINI_API_KEY") or secrets.get("GOOGLE_API_KEY")
            if not key:
                return {"probe":"skipped","reason":"credential_missing"}
            status,data,_=_http_json(
                "https://generativelanguage.googleapis.com/v1beta/models?key="+key
            )
            return {"probe":"models","http_status":status,"authenticated":status==200}

        if name=="huggingface":
            key=secrets.get("HF_TOKEN") or secrets.get("HUGGINGFACE_TOKEN") or secrets.get("HUGGING_FACE_HUB_TOKEN")
            if not key:
                return {"probe":"skipped","reason":"credential_missing"}
            status,data,_=_http_json(
                "https://huggingface.co/api/whoami-v2",
                {"Authorization":f"Bearer {key}"},
            )
            return {"probe":"whoami","http_status":status,"authenticated":status==200}

        if name=="cloudflare_workers_ai":
            key=secrets.get("CLOUDFLARE_API_TOKEN") or secrets.get("CF_API_TOKEN")
            if not key:
                return {"probe":"skipped","reason":"credential_missing"}
            status,data,_=_http_json(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                {"Authorization":f"Bearer {key}"},
            )
            ok=status==200 and bool((data or {}).get("success"))
            return {"probe":"token_verify","http_status":status,"authenticated":ok}

        if name=="openai":
            key=secrets.get("OPENAI_API_KEY") or secrets.get("COMPANYOS_OPENAI_API_KEY") or secrets.get("OPENAI_KEY")
            if not key:
                return {"probe":"skipped","reason":"credential_missing"}
            status,data,_=_http_json(
                "https://api.openai.com/v1/models",
                {"Authorization":f"Bearer {key}"},
            )
            return {"probe":"models","http_status":status,"authenticated":status==200}

        if name=="github_actions":
            key=secrets.get("GITHUB_TOKEN") or secrets.get("GH_TOKEN")
            if not key:
                return {"probe":"skipped","reason":"credential_missing"}
            status,data,_=_http_json(
                "https://api.github.com/user",
                {"Authorization":f"Bearer {key}"},
            )
            return {"probe":"user","http_status":status,"authenticated":status==200}

    except Exception as exc:
        return {"probe":"error","error":f"{type(exc).__name__}:{str(exc)[:300]}"}

    return {"probe":"not_applicable"}

def company_account_email() -> dict[str,Any]:
    names=("COMPANYOS_ACCOUNT_EMAIL","COMPANYAIOS_EMAIL","COMPANYOS_EMAIL")
    sources=_authorized_secret_sources()
    for env_name in names:
        for source_name,vals in sources:
            value=(vals.get(env_name) or "").strip()
            if value and "@" in value:
                local,domain=value.split("@",1)
                masked=(local[:2]+"***@"+domain) if local else "***@"+domain
                return {
                    "configured":True,
                    "source":source_name,
                    "name":env_name,
                    "masked":masked,
                }
    return {"configured":False}

def account_creation_policy(provider: dict[str,Any]) -> dict[str,Any]:
    retired=bool(provider.get("retired"))
    if retired:
        return {
            "action":"skip",
            "reason":"provider_retired",
            "autonomous_account_creation_allowed":False,
        }

    if not provider.get("account_required"):
        return {
            "action":"use_without_account",
            "reason":"no_account_required",
            "autonomous_account_creation_allowed":True,
        }

    # CompanyOS may only create an account automatically when the provider has
    # an official programmatic registration API AND its policy explicitly allows it.
    # Interactive web signups remain queued because CAPTCHAs, email/phone verification,
    # KYC, payment details, or acceptance screens must not be bypassed or fabricated.
    allowed=bool(
        provider.get("official_registration_api")
        and provider.get("automated_signup_permitted")
    )
    return {
        "action":"auto_register" if allowed else "queue_official_signup",
        "reason":"official_registration_supported" if allowed else "interactive_signup_or_verification_required",
        "autonomous_account_creation_allowed":allowed,
    }

def build_onboarding_queue(inventory: dict[str,Any], probes: dict[str,Any]) -> dict[str,Any]:
    email=company_account_email()
    tasks=[]

    for name,provider in sorted(PROVIDERS.items(), key=lambda kv:int(kv[1].get("priority",999))):
        inv=inventory.get(name) or {}
        probe=probes.get(name) or {}
        policy=account_creation_policy(provider)

        if provider.get("retired"):
            status="retired_skip"
        elif provider.get("auth")=="none":
            status="ready_no_key" if probe.get("reachable") else "public_provider_unreachable"
        elif probe.get("authenticated"):
            status="credential_ready"
        elif inv.get("credential_material_present"):
            status="credential_present_but_not_validated"
        else:
            status="account_or_key_needed"

        task={
            "provider":name,
            "kind":provider.get("kind"),
            "free":provider.get("free"),
            "free_summary":provider.get("free_summary"),
            "official_url":provider.get("official_url"),
            "signup_url":provider.get("signup_url"),
            "status":status,
            "credential_material_present":bool(inv.get("credential_material_present")),
            "probe":probe,
            "account_policy":policy,
            "company_email_available":bool(email.get("configured")),
            "company_email_masked":email.get("masked"),
            "next_action":None,
        }

        if status in ("ready_no_key","credential_ready","retired_skip"):
            task["next_action"]="none"
        elif policy.get("action")=="auto_register":
            task["next_action"]="official_programmatic_registration"
        else:
            task["next_action"]="official_signup_then_store_credential"

        tasks.append(task)

    return {
        "schema":"companyos.provider_onboarding_queue.v69_26",
        "generated_at_unix":time.time(),
        "company_account_email":email,
        "tasks":tasks,
        "rules":{
            "search_public_repositories_for_keys":False,
            "use_leaked_or_third_party_keys":False,
            "print_secret_values":False,
            "bypass_captcha":False,
            "bypass_phone_verification":False,
            "bypass_kyc":False,
            "fabricate_identity":False,
            "accept_paid_plan_automatically":False,
            "automatic_purchase":False,
            "official_free_or_no_key_providers_first":True,
        },
    }

def open_next_signup(queue: dict[str,Any]) -> dict[str,Any]:
    # Human-assisted fallback only. It opens the official provider signup page
    # but does not submit a form or bypass any verification.
    task=next(
        (
            t for t in queue.get("tasks",[])
            if t.get("status")=="account_or_key_needed"
            and t.get("signup_url")
        ),
        None,
    )
    if not task:
        return {"opened":False,"reason":"no_signup_task"}

    opener="termux-open-url"
    try:
        subprocess.run([opener,str(task["signup_url"])],check=True)
        return {
            "opened":True,
            "provider":task.get("provider"),
            "signup_url":task.get("signup_url"),
        }
    except Exception as exc:
        return {
            "opened":False,
            "provider":task.get("provider"),
            "reason":f"{type(exc).__name__}:{str(exc)[:200]}",
        }

def run(open_signup: bool=False) -> dict[str,Any]:
    inventory,private_values=discover_credentials()

    probes={}
    probes["github_public_rest"]=probe_github_public()

    for name in PROVIDERS:
        if name in ("github_public_rest","github_models"):
            continue
        probes[name]=probe_keyed_provider(name,private_values.get(name) or {})

    queue=build_onboarding_queue(inventory,probes)

    catalog={
        "schema":"companyos.provider_catalog.v69_26",
        "generated_at_unix":time.time(),
        "providers":PROVIDERS,
    }
    _atomic(CATALOG,catalog)
    _atomic(QUEUE,queue)

    summary={
        "schema":"companyos.provider_acquisition_state.v69_26",
        "generated_at_unix":time.time(),
        "credential_inventory":inventory,
        "probes":probes,
        "queue_path":str(QUEUE),
        "catalog_path":str(CATALOG),
        "ready_no_key":[
            t["provider"] for t in queue["tasks"]
            if t.get("status")=="ready_no_key"
        ],
        "credential_ready":[
            t["provider"] for t in queue["tasks"]
            if t.get("status")=="credential_ready"
        ],
        "account_or_key_needed":[
            t["provider"] for t in queue["tasks"]
            if t.get("status")=="account_or_key_needed"
        ],
        "retired_skip":[
            t["provider"] for t in queue["tasks"]
            if t.get("status")=="retired_skip"
        ],
        "secret_values_emitted":False,
        "public_key_harvesting_performed":False,
        "automatic_purchase_performed":False,
        "financial_action_performed":False,
        "external_message_sent":False,
    }

    if open_signup:
        summary["signup_open_result"]=open_next_signup(queue)

    _atomic(STATE,summary)
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument(
        "--open-next-signup",
        action="store_true",
        help="Open the next official signup page for human-assisted verification.",
    )
    args=parser.parse_args()
    print(json.dumps(run(open_signup=args.open_next_signup),indent=2,sort_keys=True))
