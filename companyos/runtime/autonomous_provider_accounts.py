from __future__ import annotations

import argparse
import email
import hashlib
import html
import imaplib
import json
import os
import re
import secrets
import ssl
import subprocess
import time
import urllib.parse
import urllib.request
import uuid
from email.header import decode_header
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
ART=RT/"provider_accounts"
VAULT=RT/"credential_vault"

STATE=ART/"state.json"
LATEST=ART/"latest.json"
HISTORY=ART/"history.jsonl"
CANDIDATES=ART/"provider_candidates.jsonl"
ACCOUNTS=ART/"accounts.jsonl"
HUMAN=ART/"human_verification_required.jsonl"
VAULT_INDEX=VAULT/"index.json"

ART.mkdir(parents=True,exist_ok=True)
VAULT.mkdir(parents=True,exist_ok=True)
os.chmod(VAULT,0o700)

VERSION="V66.06"
HTTP_TIMEOUT=20
MAX_PROVIDERS_PER_CYCLE=3

# Bootstrap only solves the "no search provider exists yet" chicken-and-egg
# problem. Once external sourcing is active, dynamic candidate domains are
# learned from CompanyOS procurement evidence.
BOOTSTRAP={
    "external_search":[
        {"provider":"tavily","domain":"tavily.com","credential_env":"COMPANYOS_TAVILY_API_KEY"},
        {"provider":"serper","domain":"serper.dev","credential_env":"COMPANYOS_SERPER_API_KEY"},
        {"provider":"brave_search","domain":"brave.com","credential_env":"COMPANYOS_BRAVE_SEARCH_API_KEY"},
    ]
}

KNOWN_SIGNUP_ROUTES={
    "tavily.com":["https://app.tavily.com/","https://www.tavily.com/"],
    "serper.dev":["https://serper.dev/"],
    "brave.com":["https://api-dashboard.search.brave.com/register","https://brave.com/search/api/"],
}

SIGNUP_WORDS=("sign up","signup","register","create account","get started","start free","try free")
VERIFY_WORDS=("verify","confirm","activate","validation")
BLOCK_WORDS=("captcha","recaptcha","hcaptcha","turnstile","phone verification","identity verification","kyc")
KEY_NAMES={
    "tavily":"COMPANYOS_TAVILY_API_KEY",
    "brave_search":"COMPANYOS_BRAVE_SEARCH_API_KEY",
    "serper":"COMPANYOS_SERPER_API_KEY",
}


def dotenv() -> dict[str,str]:
    p=ROOT/".env"
    out={}
    if not p.exists():
        return out
    for line in p.read_text(errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k,v=s.split("=",1)
        out[k.strip()]=v.strip().strip('"').strip("'")
    return out


def env(name: str, default: str|None=None) -> str|None:
    v=os.environ.get(name)
    if v is not None and v.strip():
        return v.strip()
    return dotenv().get(name) or default


def read_jsonl(path: Path) -> list[dict[str,Any]]:
    if not path.exists():
        return []
    out=[]
    for line in path.read_text(errors="ignore").splitlines():
        try:
            x=json.loads(line)
            if isinstance(x,dict):
                out.append(x)
        except Exception:
            pass
    return out


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def load_json(path: Path,default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    payload=json.dumps(data, indent=2, sort_keys=True, default=str) + "\n"
    fd,tmp_name=tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        except Exception:
            pass


def same_provider_host(host: str, domain: str) -> bool:
    host=(host or "").lower().split(":")[0].strip(".")
    domain=(domain or "").lower().strip(".")
    return bool(host and domain and (host==domain or host.endswith("."+domain)))


def safe_url(url: str, domain: str) -> bool:
    try:
        u=urllib.parse.urlparse(url)
    except Exception:
        return False
    return u.scheme=="https" and same_provider_host(u.hostname or "",domain)


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self._href=None
        self._text=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            d=dict(attrs)
            self._href=d.get("href")
            self._text=[]
    def handle_data(self,data):
        if self._href is not None:
            self._text.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self._href is not None:
            self.links.append((self._href," ".join(self._text).strip()))
            self._href=None
            self._text=[]


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms=[]
        self.current=None
    def handle_starttag(self,tag,attrs):
        d={str(k).lower():v for k,v in attrs}
        if tag.lower()=="form":
            self.current={
                "action":d.get("action",""),
                "method":str(d.get("method","get")).lower(),
                "inputs":[],
            }
        elif self.current is not None and tag.lower() in {"input","button","select","textarea"}:
            self.current["inputs"].append({
                "tag":tag.lower(),
                "name":d.get("name",""),
                "type":str(d.get("type","text")).lower(),
                "value":d.get("value",""),
                "required":"required" in d,
                "autocomplete":d.get("autocomplete",""),
                "id":d.get("id",""),
            })
    def handle_endtag(self,tag):
        if tag.lower()=="form" and self.current is not None:
            self.forms.append(self.current)
            self.current=None


def opener():
    jar=CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get_text(op,url: str) -> tuple[str,str,int]:
    req=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0 CompanyOS/66.06",
        "Accept":"text/html,application/xhtml+xml",
    })
    with op.open(req,timeout=HTTP_TIMEOUT) as r:
        raw=r.read(1_500_000)
        return r.geturl(),raw.decode(errors="ignore"),getattr(r,"status",200)


def discover_signup_url(domain: str) -> dict[str,Any]:
    op=opener()
    hints=list(KNOWN_SIGNUP_ROUTES.get(domain,[]))
    roots=hints+[f"https://{domain}/",f"https://www.{domain}/"]
    roots=list(dict.fromkeys(roots))
    errors=[]
    for root in roots:
        try:
            final,text,status=get_text(op,root)
        except Exception as exc:
            errors.append(f"{type(exc).__name__}:{exc}")
            continue
        if root in hints:
            probe=FormParser()
            try:
                probe.feed(text)
            except Exception:
                pass
            marker=text.lower()
            if probe.forms or any(x in marker for x in ("register new account","create your account","sign up","create account")):
                return {
                    "ok":True,
                    "signup_url":final,
                    "label":"known_official_signup_route",
                    "source_url":final,
                }

        p=LinkParser()
        try:
            p.feed(text)
        except Exception:
            pass
        scored=[]
        for href,label in p.links:
            full=urllib.parse.urljoin(final,href or "")
            if not safe_url(full,domain):
                continue
            q=(label+" "+href).lower()
            score=sum(1 for w in SIGNUP_WORDS if w in q)
            if score:
                scored.append((score,full,label))
        if scored:
            scored.sort(reverse=True)
            return {
                "ok":True,
                "signup_url":scored[0][1],
                "label":scored[0][2],
                "source_url":final,
            }
        return {"ok":False,"status":"signup_link_not_found","source_url":final}
    return {"ok":False,"status":"provider_homepage_unreachable","errors":errors[-3:]}


def detect_blockers(text: str,forms: list[dict[str,Any]]) -> list[str]:
    q=text.lower()
    blockers=[]
    for w in BLOCK_WORDS:
        if w in q:
            blockers.append(w.replace(" ","_"))
    for form in forms:
        for x in form.get("inputs") or []:
            name=(x.get("name") or "").lower()
            typ=(x.get("type") or "").lower()
            if x.get("required") and ("phone" in name or "mobile" in name or typ=="tel"):
                blockers.append("required_phone")
            if x.get("required") and typ=="checkbox":
                blockers.append("required_terms_or_checkbox")
    return sorted(set(blockers))


def choose_form(forms: list[dict[str,Any]]) -> dict[str,Any]|None:
    best=None
    best_score=-1
    for f in forms:
        if f.get("method")!="post":
            continue
        names=" ".join((x.get("name") or "")+" "+(x.get("autocomplete") or "") for x in f.get("inputs") or []).lower()
        score=0
        if "email" in names: score+=3
        if "password" in names or "new-password" in names: score+=3
        if "name" in names: score+=1
        if score>best_score:
            best=f; best_score=score
    return best if best_score>=3 else None


def build_form_payload(form: dict[str,Any],account_email: str,password: str) -> tuple[dict[str,str],list[str]]:
    data={}
    unresolved=[]
    for x in form.get("inputs") or []:
        name=str(x.get("name") or "")
        if not name:
            continue
        typ=str(x.get("type") or "text").lower()
        low=(name+" "+str(x.get("autocomplete") or "")+" "+str(x.get("id") or "")).lower()
        value=str(x.get("value") or "")

        if typ in {"hidden","submit"}:
            data[name]=value
        elif "email" in low or str(x.get("autocomplete"))=="username":
            data[name]=account_email
        elif "password" in low or str(x.get("autocomplete")) in {"new-password","current-password"}:
            data[name]=password
        elif "company" in low or "organization" in low:
            data[name]="CompanyAIOS"
        elif "first" in low and "name" in low:
            data[name]="CompanyAIOS"
        elif "last" in low and "name" in low:
            data[name]="Automation"
        elif low in {"name","full_name","fullname"} or "full-name" in low:
            data[name]="CompanyAIOS"
        elif typ=="checkbox":
            if x.get("required"):
                unresolved.append("required_terms_or_checkbox")
        elif x.get("required"):
            unresolved.append(f"required_field:{name}")
    return data,sorted(set(unresolved))


def post_form(op,signup_url: str,form: dict[str,Any],data: dict[str,str],domain: str) -> dict[str,Any]:
    target=urllib.parse.urljoin(signup_url,form.get("action") or signup_url)
    if not safe_url(target,domain):
        return {"ok":False,"status":"cross_domain_form_blocked","target_host":urllib.parse.urlparse(target).hostname}
    body=urllib.parse.urlencode(data).encode()
    req=urllib.request.Request(target,data=body,headers={
        "User-Agent":"Mozilla/5.0 CompanyOS/66.06",
        "Content-Type":"application/x-www-form-urlencoded",
        "Accept":"text/html,application/xhtml+xml",
        "Referer":signup_url,
    },method="POST")
    try:
        with op.open(req,timeout=HTTP_TIMEOUT) as r:
            raw=r.read(1_500_000)
            text=raw.decode(errors="ignore")
            final=r.geturl()
            status=getattr(r,"status",200)
    except Exception as exc:
        return {"ok":False,"status":"signup_submit_failed","error":f"{type(exc).__name__}:{exc}"}

    q=text.lower()
    awaiting=any(x in q for x in ("check your email","verify your email","verification email","confirm your email","email sent"))
    success=awaiting or any(x in q for x in ("account created","welcome","dashboard"))
    return {
        "ok":bool(success),
        "status":"AWAITING_EMAIL_VERIFICATION" if awaiting else ("ACCOUNT_CREATED" if success else "SIGNUP_RESULT_UNCERTAIN"),
        "http_status":status,
        "final_url":final,
        "body_fingerprint":hashlib.sha256(text.encode(errors="ignore")).hexdigest(),
    }


def mailbox_config() -> dict[str,Any]:
    e=dotenv()
    email_addr=env("COMPANYAIOS_EMAIL") or e.get("COMPANYOS_SMTP_FROM_EMAIL") or e.get("COMPANYOS_SMTP_USERNAME")
    user=env("COMPANYAIOS_IMAP_USERNAME") or e.get("COMPANYOS_SMTP_USERNAME") or email_addr
    password=env("COMPANYAIOS_IMAP_PASSWORD") or e.get("COMPANYOS_SMTP_PASSWORD")
    host=env("COMPANYAIOS_IMAP_HOST")
    if not host and email_addr:
        low=str(email_addr).lower()
        if low.endswith("@gmail.com") or low.endswith("@googlemail.com"):
            host="imap.gmail.com"
        elif low.endswith("@outlook.com") or low.endswith("@hotmail.com") or low.endswith("@live.com"):
            host="outlook.office365.com"
        elif low.endswith("@yahoo.com"):
            host="imap.mail.yahoo.com"
    port=int(env("COMPANYAIOS_IMAP_PORT","993") or 993)
    return {
        "email":email_addr,
        "username":user,
        "password_present":bool(password),
        "host":host,
        "port":port,
        "_password":password,
    }


def decode_header_value(v: str|None) -> str:
    if not v:
        return ""
    out=[]
    for part,enc in decode_header(v):
        if isinstance(part,bytes):
            out.append(part.decode(enc or "utf-8",errors="ignore"))
        else:
            out.append(str(part))
    return "".join(out)


def message_text(msg) -> str:
    parts=[]
    if msg.is_multipart():
        for p in msg.walk():
            ctype=p.get_content_type()
            if ctype not in {"text/plain","text/html"}:
                continue
            try:
                parts.append(p.get_payload(decode=True).decode(p.get_content_charset() or "utf-8",errors="ignore"))
            except Exception:
                pass
    else:
        try:
            parts.append(msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8",errors="ignore"))
        except Exception:
            pass
    return "\n".join(parts)


def verification_links_for(domain: str,lookback_messages: int=40) -> list[str]:
    cfg=mailbox_config()
    if not (cfg["host"] and cfg["username"] and cfg["_password"]):
        return []
    links=[]
    ctx=ssl.create_default_context()
    with imaplib.IMAP4_SSL(cfg["host"],cfg["port"],ssl_context=ctx) as m:
        m.login(cfg["username"],cfg["_password"])
        m.select("INBOX",readonly=True)
        typ,data=m.search(None,"ALL")
        if typ!="OK" or not data:
            return []
        ids=(data[0].split() or [])[-lookback_messages:]
        for mid in reversed(ids):
            typ,msgdata=m.fetch(mid,"(RFC822)")
            if typ!="OK" or not msgdata:
                continue
            raw=next((x[1] for x in msgdata if isinstance(x,tuple) and isinstance(x[1],bytes)),None)
            if not raw:
                continue
            msg=email.message_from_bytes(raw)
            subj=decode_header_value(msg.get("Subject"))
            frm=decode_header_value(msg.get("From"))
            body=message_text(msg)
            hay=(subj+" "+frm+" "+body).lower()
            if domain.lower() not in hay:
                continue
            if not any(w in hay for w in VERIFY_WORDS):
                continue
            for u in re.findall(r'https://[^\s<>"\']+',html.unescape(body)):
                u=u.rstrip(").,;]")
                try:
                    host=urllib.parse.urlparse(u).hostname or ""
                except Exception:
                    continue
                if same_provider_host(host,domain):
                    links.append(u)
    dedup=[]
    for x in links:
        if x not in dedup:
            dedup.append(x)
    return dedup


def click_verification(domain: str) -> dict[str,Any]:
    links=verification_links_for(domain)
    if not links:
        return {"ok":False,"status":"verification_email_not_found"}
    op=opener()
    for u in links[:3]:
        if not safe_url(u,domain):
            continue
        try:
            final,text,status=get_text(op,u)
        except Exception as exc:
            continue
        q=text.lower()
        verified=any(x in q for x in ("verified","account activated","email confirmed","welcome","dashboard"))
        return {
            "ok":bool(verified or status in (200,201,204)),
            "status":"EMAIL_VERIFICATION_OPENED",
            "http_status":status,
            "final_host":urllib.parse.urlparse(final).hostname,
            "verification_url_hash":hashlib.sha256(u.encode()).hexdigest(),
        }
    return {"ok":False,"status":"verification_link_not_usable"}


def openssl_available() -> bool:
    try:
        p=subprocess.run(["openssl","version"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
        return p.returncode==0
    except Exception:
        return False


def vault_store(provider: str,secret_obj: dict[str,Any]) -> dict[str,Any]:
    master=env("COMPANYOS_CREDENTIAL_VAULT_KEY")
    if not master:
        return {"ok":False,"status":"vault_master_key_missing"}
    if not openssl_available():
        return {"ok":False,"status":"openssl_missing"}

    ident=re.sub(r"[^a-zA-Z0-9._-]+","_",provider)[:80]
    target=VAULT/f"{ident}.json.enc"
    raw=json.dumps(secret_obj,sort_keys=True).encode()

    proc=subprocess.run(
        ["openssl","enc","-aes-256-cbc","-salt","-pbkdf2","-a","-pass","env:COMPANYOS_CREDENTIAL_VAULT_KEY"],
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ,"COMPANYOS_CREDENTIAL_VAULT_KEY":master},
        timeout=10,
    )
    if proc.returncode!=0:
        return {"ok":False,"status":"vault_encrypt_failed"}

    target.write_bytes(proc.stdout)
    os.chmod(target,0o600)

    idx=load_json(VAULT_INDEX,{"version":1,"entries":{}})
    idx.setdefault("entries",{})[provider]={
        "file":str(target),
        "updated_at_unix":time.time(),
        "secret_fields":sorted(secret_obj.keys()),
        "secret_values_printed":False,
    }
    save_json(VAULT_INDEX,idx)
    os.chmod(VAULT_INDEX,0o600)
    return {"ok":True,"status":"stored_encrypted","file":str(target)}


def sync_env_credential(provider: str,credentials: dict[str,Any]) -> dict[str,Any]:
    key_name=KEY_NAMES.get(provider)
    if not key_name:
        return {"ok":False,"status":"no_activation_env_mapping"}
    value=credentials.get("api_key") or credentials.get("token")
    if not value:
        return {"ok":False,"status":"api_key_not_returned"}

    p=ROOT/".env"
    lines=p.read_text(errors="ignore").splitlines() if p.exists() else []
    out=[]
    found=False
    for line in lines:
        if line.startswith(key_name+"="):
            out.append(key_name+"="+str(value))
            found=True
        else:
            out.append(line)
    if not found:
        out.append(key_name+"="+str(value))
    p.write_text("\n".join(out)+"\n")
    os.chmod(p,0o600)
    return {"ok":True,"status":"credential_activated","env_name":key_name,"secret_value_printed":False}


def external_provision(provider: dict[str,Any],identity: dict[str,Any]) -> dict[str,Any]|None:
    url=env("COMPANYOS_ACCOUNT_PROVISIONER_URL")
    token=env("COMPANYOS_ACCOUNT_PROVISIONER_TOKEN")
    if not url:
        return None
    data=json.dumps({
        "action":"create_provider_account",
        "provider":provider,
        "identity":{
            "email":identity.get("email"),
            "display_name":"CompanyAIOS",
        },
        "constraints":{
            "no_captcha_bypass":True,
            "no_phone_bypass":True,
            "no_kyc_bypass":True,
            "do_not_accept_human_only_contracts":True,
        },
    }).encode()
    headers={"Content-Type":"application/json","User-Agent":"CompanyOS/66.06"}
    if token:
        headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,data=data,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            result=json.loads(r.read().decode(errors="ignore"))
    except Exception as exc:
        return {"ok":False,"status":"external_provisioner_failed","error":f"{type(exc).__name__}:{exc}"}
    return result if isinstance(result,dict) else {"ok":False,"status":"external_provisioner_invalid_response"}


def dynamic_candidates() -> list[dict[str,Any]]:
    out=[]
    # Dynamic candidates from V66.05 sourcing.
    for path in (
        RT/"procurement/sourcing_resolutions.jsonl",
        RT/"procurement/sourcing_evidence.jsonl",
    ):
        for x in read_jsonl(path):
            domain=x.get("candidate_vendor") or x.get("domain")
            if not domain:
                continue
            domain=str(domain).lower().strip()
            if "://" in domain:
                try:
                    domain=urllib.parse.urlparse(domain).hostname or ""
                except Exception:
                    continue
            if domain:
                out.append({
                    "provider":re.sub(r"[^a-z0-9]+","_",domain.split(".")[0]) or "provider",
                    "domain":domain,
                    "credential_env":None,
                    "source":"dynamic_procurement_discovery",
                })

    # Bootstrap the search capability if no search provider is configured.
    d=dotenv()
    if not any(d.get(k) for k in (
        "COMPANYOS_TAVILY_API_KEY",
        "COMPANYOS_BRAVE_SEARCH_API_KEY",
        "COMPANYOS_SERPER_API_KEY",
    )):
        for x in BOOTSTRAP["external_search"]:
            out.append({**x,"source":"bootstrap_external_search_gap"})

    dedup={}
    for x in out:
        key=x["domain"]
        dedup[key]=x
    return list(dedup.values())


def existing_accounts() -> dict[str,dict[str,Any]]:
    out={}
    for x in read_jsonl(ACCOUNTS):
        domain=x.get("domain")
        if domain:
            out[str(domain)]=x
    return out


def already_configured(candidate: dict[str,Any]) -> bool:
    name=candidate.get("credential_env")
    return bool(name and env(str(name)))


def capability_available_without_account(candidate: dict[str,Any]) -> bool:
    # Tavily Search/Extract can operate keylessly. Do not make provider account
    # creation a prerequisite for the live external-search capability.
    return str(candidate.get("provider") or "")=="tavily"


def candidate_retry_due(candidate: dict[str,Any], current: dict[str,dict[str,Any]]) -> bool:
    old=current.get(str(candidate.get("domain") or ""))
    if not old:
        return True
    status=str(old.get("status") or "")
    age=time.time()-float(old.get("timestamp_unix") or 0)

    if status in {
        "ALREADY_CONFIGURED",
        "AUTO_PROVISIONED",
        "ACCOUNT_VERIFIED_KEY_ISSUANCE_PENDING",
        "HUMAN_VERIFICATION_REQUIRED",
    }:
        return False

    cooldowns={
        "SIGNUP_DISCOVERY_PENDING":6*3600,
        "BROWSER_ADAPTER_REQUIRED":12*3600,
        "SIGNUP_PAGE_UNREACHABLE":2*3600,
        "SIGNUP_RESULT_UNCERTAIN":6*3600,
        "EXTERNAL_PROVISIONER_FAILED":3600,
        "VAULT_NOT_READY":3600,
    }
    wait=cooldowns.get(status,900)
    return age>=wait


def human_record(candidate: dict[str,Any],reason: str,detail: Any=None) -> dict[str,Any]:
    row={
        "timestamp_unix":time.time(),
        "provider":candidate.get("provider"),
        "domain":candidate.get("domain"),
        "status":"HUMAN_VERIFICATION_REQUIRED",
        "reason":reason,
        "detail":detail,
    }
    append_jsonl(HUMAN,row)
    return row


def queue_followup_research(candidate: dict[str,Any],reason: str) -> dict[str,Any]:
    q=AutonomousTaskQueue()
    domain=candidate["domain"]
    t=q.enqueue(
        task_type="research",
        priority=92,
        max_attempts=3,
        idempotency_key=f"provider-account-discovery:{domain}",
        payload={
            "topic":f"Provider onboarding and API access for {domain}",
            "objective":"Find official signup, developer/API documentation, free tier, credential issuance, and automation requirements.",
            "query":f"site:{domain} official signup developer API key pricing",
            "constraints":[
                "use official provider documentation when available",
                "do not fabricate credentials",
                "do not bypass CAPTCHA",
                "do not bypass phone verification",
                "do not bypass KYC or identity verification",
            ],
            "stage":"research",
        },
    )
    return {"task_id":t.task_id,"state":t.state,"reason":reason}


def provision_candidate(candidate: dict[str,Any]) -> dict[str,Any]:
    domain=str(candidate["domain"])
    provider=str(candidate["provider"])
    identity=mailbox_config()

    base={
        "timestamp_unix":time.time(),
        "account_id":str(uuid.uuid4()),
        "provider":provider,
        "domain":domain,
        "company_email_present":bool(identity.get("email")),
        "company_email":identity.get("email"),
        "source":candidate.get("source"),
        "credential_env":candidate.get("credential_env"),
        "secret_values_printed":False,
    }

    if already_configured(candidate):
        row={**base,"status":"ALREADY_CONFIGURED"}
        append_jsonl(ACCOUNTS,row)
        return row

    if not identity.get("email"):
        row={**base,"status":"COMPANYAIOS_EMAIL_NOT_CONFIGURED"}
        append_jsonl(ACCOUNTS,row)
        return row

    remote=external_provision(candidate,identity)
    if remote is not None:
        status=str(remote.get("status") or "")
        creds=remote.get("credentials") if isinstance(remote.get("credentials"),dict) else None
        vault=None
        activated=None
        if creds:
            vault=vault_store(provider,{
                "provider":provider,
                "domain":domain,
                "company_email":identity.get("email"),
                **creds,
            })
            activated=sync_env_credential(provider,creds)
        row={**base,
             "status":status or ("AUTO_PROVISIONED" if remote.get("ok") else "EXTERNAL_PROVISIONER_FAILED"),
             "external_provisioner":True,
             "vault":vault,
             "credential_activation":activated,
             "remote_secret_values_removed":bool(creds)}
        append_jsonl(ACCOUNTS,row)
        return row

    signup=discover_signup_url(domain)
    if not signup.get("ok"):
        task=queue_followup_research(candidate,signup.get("status","signup_discovery_failed"))
        pending_status="BROWSER_ADAPTER_REQUIRED" if (
            domain in KNOWN_SIGNUP_ROUTES and signup.get("status")=="signup_link_not_found"
        ) else "SIGNUP_DISCOVERY_PENDING"
        row={**base,"status":pending_status,"signup":signup,"research_task":task}
        append_jsonl(ACCOUNTS,row)
        return row

    op=opener()
    try:
        final,text,http_status=get_text(op,signup["signup_url"])
    except Exception as exc:
        row={**base,"status":"SIGNUP_PAGE_UNREACHABLE","error":f"{type(exc).__name__}:{exc}","signup_url_host":urllib.parse.urlparse(signup["signup_url"]).hostname}
        append_jsonl(ACCOUNTS,row)
        return row

    fp=FormParser()
    try:
        fp.feed(text)
    except Exception:
        pass

    blockers=detect_blockers(text,fp.forms)
    if blockers:
        human=human_record(candidate,"signup_requires_human_verification_or_acceptance",blockers)
        row={**base,"status":"HUMAN_VERIFICATION_REQUIRED","blockers":blockers,"human_record":human}
        append_jsonl(ACCOUNTS,row)
        return row

    form=choose_form(fp.forms)
    if not form:
        task=queue_followup_research(candidate,"browser_or_js_signup_required")
        row={**base,"status":"BROWSER_ADAPTER_REQUIRED","research_task":task}
        append_jsonl(ACCOUNTS,row)
        return row

    password=secrets.token_urlsafe(28)+"Aa9!"
    data,unresolved=build_form_payload(form,identity["email"],password)
    if unresolved:
        human=human_record(candidate,"signup_form_has_unresolved_required_fields",unresolved)
        row={**base,"status":"HUMAN_VERIFICATION_REQUIRED","unresolved":unresolved,"human_record":human}
        append_jsonl(ACCOUNTS,row)
        return row

    vault=vault_store(provider,{
        "provider":provider,
        "domain":domain,
        "company_email":identity["email"],
        "account_password":password,
        "created_at_unix":time.time(),
    })
    if not vault.get("ok"):
        row={**base,"status":"VAULT_NOT_READY","vault":vault}
        append_jsonl(ACCOUNTS,row)
        return row

    result=post_form(op,final,form,data,domain)
    row={**base,
         "status":result.get("status"),
         "signup_url_host":urllib.parse.urlparse(final).hostname,
         "submit_result":result,
         "vault_status":vault.get("status")}
    append_jsonl(ACCOUNTS,row)
    return row


def verify_pending() -> list[dict[str,Any]]:
    latest=existing_accounts()
    out=[]
    for domain,row in latest.items():
        if row.get("status")!="AWAITING_EMAIL_VERIFICATION":
            continue
        result=click_verification(domain)
        new={
            **row,
            "timestamp_unix":time.time(),
            "verification":result,
            "status":"ACCOUNT_VERIFIED_KEY_ISSUANCE_PENDING" if result.get("ok") else "AWAITING_EMAIL_VERIFICATION",
        }
        append_jsonl(ACCOUNTS,new)
        out.append(new)
    return out


def run_once(max_providers: int=MAX_PROVIDERS_PER_CYCLE) -> dict[str,Any]:
    verified=verify_pending()
    current=existing_accounts()
    candidates=dynamic_candidates()

    selected=[]
    for c in candidates:
        if already_configured(c):
            continue
        if capability_available_without_account(c):
            continue
        if not candidate_retry_due(c,current):
            continue
        selected.append(c)

    results=[provision_candidate(x) for x in selected[:max(1,int(max_providers))]]

    report={
        "version":VERSION,
        "mode":"autonomous_provider_discovery_and_account_provisioning",
        "company_identity":{
            "email_present":bool(mailbox_config().get("email")),
            "imap_host_present":bool(mailbox_config().get("host")),
            "imap_password_present":bool(mailbox_config().get("password_present")),
            "personal_email_required":False,
        },
        "vault":{
            "openssl_available":openssl_available(),
            "master_key_present":bool(env("COMPANYOS_CREDENTIAL_VAULT_KEY")),
            "secret_values_printed":False,
        },
        "dynamic_candidates":len(candidates),
        "selected":len(results),
        "email_verifications_attempted":len(verified),
        "results":results,
        "constraints":{
            "captcha_bypass":False,
            "phone_bypass":False,
            "kyc_bypass":False,
            "human_only_contract_acceptance":False,
            "companyaios_email_only":True,
        },
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,{"timestamp_unix":time.time(),**report})
    st=load_json(STATE,{})
    st.update({"version":VERSION,"updated_at_unix":time.time(),"last_report":report})
    save_json(STATE,st)
    return report


def status() -> dict[str,Any]:
    cfg=mailbox_config()
    safe_mail={
        "email":cfg.get("email"),
        "host":cfg.get("host"),
        "port":cfg.get("port"),
        "username_present":bool(cfg.get("username")),
        "password_present":bool(cfg.get("password_present")),
    }
    return {
        "version":VERSION,
        "mailbox":safe_mail,
        "vault_index":load_json(VAULT_INDEX,{"entries":{}}),
        "candidate_count":len(dynamic_candidates()),
        "latest":load_json(LATEST,{}),
        "state":load_json(STATE,{}),
        "secret_values_printed":False,
    }


def loop(interval: int):
    while True:
        try:
            r=run_once()
            print(json.dumps({
                "ts":time.time(),
                "candidates":r["dynamic_candidates"],
                "selected":r["selected"],
                "email_verifications_attempted":r["email_verifications_attempted"],
            },sort_keys=True),flush=True)
        except Exception as exc:
            print(json.dumps({"ts":time.time(),"error":f"{type(exc).__name__}:{exc}"},sort_keys=True),flush=True)
        time.sleep(max(120,int(interval)))


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status")
    sub.add_parser("mail")
    sub.add_parser("candidates")
    sub.add_parser("verify")
    p=sub.add_parser("once")
    p.add_argument("--max-providers",type=int,default=MAX_PROVIDERS_PER_CYCLE)
    lp=sub.add_parser("loop")
    lp.add_argument("--interval",type=int,default=600)
    args=ap.parse_args()

    if args.cmd=="status":
        print(json.dumps(status(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="mail":
        c=mailbox_config()
        print(json.dumps({
            "email":c.get("email"),
            "host":c.get("host"),
            "port":c.get("port"),
            "username_present":bool(c.get("username")),
            "password_present":bool(c.get("password_present")),
        },indent=2,sort_keys=True))
    elif args.cmd=="candidates":
        print(json.dumps(dynamic_candidates(),indent=2,sort_keys=True))
    elif args.cmd=="verify":
        print(json.dumps(verify_pending(),indent=2,sort_keys=True,default=str))
    elif args.cmd=="once":
        print(json.dumps(run_once(args.max_providers),indent=2,sort_keys=True,default=str))
    elif args.cmd=="loop":
        loop(args.interval)


if __name__=="__main__":
    main()
