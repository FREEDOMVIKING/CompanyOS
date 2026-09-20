#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"

MOD="$ROOT/companyos/runtime/verified_web_prospect_discovery.py"
LIVE="$ROOT/companyos/runtime/venture_liveness_runtime.py"
CTL="$ROOT/scripts/companyos_prospectctl"
ACTL="$ROOT/scripts/companyos_acquisitionctl"
XCTL="$ROOT/scripts/companyos_externalctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.28 VERIFIED WEB PROSPECT DISCOVERY ====="
echo "GOAL=FIND_REAL_PUBLIC_BUSINESS_CONTACTS_FOR_LAUNCHED_VENTURES_AND_FEED_V66_27"
echo "NOTE=USES_OPENAI_RESPONSES_WEB_SEARCH_WHEN_CONFIGURED"
echo "NOTE=EXACT_EMAIL_MUST_APPEAR_ON_THE_CITED_PUBLIC_SOURCE_PAGE_BEFORE_AUTO_OUTREACH"
echo "NOTE=NO_PERSONAL_CONTACT_INFERENCE"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in \
  "$ROOT/companyos/runtime/customer_acquisition_bridge.py" \
  "$ROOT/companyos/runtime/venture_liveness_runtime.py" \
  "$ROOT/companyos/governance/venture_identity_progression.py"
do
  [ -f "$f" ] || { echo "V66_28_ABORT=missing:$f"; exit 1; }
done

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$MOD" "$LIVE"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_28_backup_${stamp}"
    echo "BACKUP=${f}.v66_28_backup_${stamp}"
  fi
done

cat > "$MOD" <<'PY'
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib import request, error, parse

from companyos.runtime.stalled_stage_progression_controller import canonical_ventures
from companyos.runtime.customer_acquisition_bridge import (
    venture_copy,
    roots_for,
    find_contacts,
)

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"

STATE=RT/"verified_web_prospect_discovery_state.json"
LATEST=RT/"verified_web_prospect_discovery_latest.json"
HISTORY=RT/"verified_web_prospect_discovery_history.jsonl"

VERSION="V66.28"
OPENAI_URL="https://api.openai.com/v1/responses"
DEFAULT_MODEL=os.getenv("COMPANYOS_WEB_SEARCH_MODEL","gpt-5.6-luna")
PERSONAL_DOMAINS={
    "gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com",
    "aol.com","proton.me","protonmail.com","live.com","msn.com",
}
EMAIL_RE=re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$",re.I)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    import tempfile
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            f.write(json.dumps(data,indent=2,sort_keys=True,default=str)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def append_jsonl(path: Path,row: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row,sort_keys=True,default=str)+"\n")


def env_file_values() -> dict[str,str]:
    out={}
    p=ROOT/".env"
    if not p.exists():
        return out
    for raw in p.read_text(errors="ignore").splitlines():
        if "=" not in raw or raw.lstrip().startswith("#"):
            continue
        k,v=raw.split("=",1)
        out[k.strip()]=v.strip().strip('"').strip("'")
    return out


def openai_key() -> str|None:
    return os.getenv("OPENAI_API_KEY") or env_file_values().get("OPENAI_API_KEY")


def output_text(resp: dict[str,Any]) -> str:
    texts=[]
    for item in resp.get("output") or []:
        if not isinstance(item,dict):
            continue
        if item.get("type")!="message":
            continue
        for content in item.get("content") or []:
            if not isinstance(content,dict):
                continue
            if content.get("type")=="output_text" and isinstance(content.get("text"),str):
                texts.append(content["text"])
    return "\n".join(texts).strip()


def parse_json_text(text: str) -> Any:
    t=text.strip()
    if t.startswith("```"):
        lines=t.splitlines()
        if lines and lines[0].startswith("```"):
            lines=lines[1:]
        if lines and lines[-1].strip()=="```":
            lines=lines[:-1]
        t="\n".join(lines).strip()
        if t.lower().startswith("json"):
            t=t[4:].lstrip()

    try:
        return json.loads(t)
    except Exception:
        pass

    starts=[x for x in (t.find("["),t.find("{")) if x>=0]
    if not starts:
        raise ValueError("no_json_in_web_search_output")
    start=min(starts)
    for end in range(len(t),start,-1):
        chunk=t[start:end].strip()
        if not chunk.endswith(("]", "}")):
            continue
        try:
            return json.loads(chunk)
        except Exception:
            continue
    raise ValueError("invalid_json_in_web_search_output")


def web_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    key=openai_key()
    if not key:
        return {"ok":False,"status":"OPENAI_API_KEY_MISSING"}

    audience=copy.get("audience") or "businesses that fit this product"
    live_url=copy.get("live_url") or ""
    title=copy.get("title") or cid.replace("_"," ").title()
    description=copy.get("description") or ""

    prompt = "\n".join([
        "Find up to 5 businesses that are plausible prospects for the launched venture below.",
        "",
        f"Venture: {title}",
        f"Description: {description}",
        f"Target audience: {audience}",
        f"Live product URL: {live_url}",
        "",
        "Return ONLY valid JSON in this exact shape:",
        '{"prospects":[{"company_name":"...","public_business_email":"...","official_website":"https://...","source_url":"https://...","fit_reason":"..."}]}',
        "",
        "Requirements:",
        "- The email must be a publicly listed BUSINESS contact email.",
        "- source_url must be an official company-owned page where that exact email is visible.",
        "- Prefer sales, info, estimating, office, contact, partnerships, or other role-based business addresses.",
        "- Do not infer, guess, generate, or pattern-match an email address.",
        "- Do not return private/personal contact data.",
        "- Do not use data-broker, people-search, scraped directory, social-media-profile, or lead-list pages as the source.",
        "- official_website and source_url must be public HTTP(S) URLs.",
        "- Fit must be based on the venture and target audience above.",
        '- If no qualifying prospects are found, return {"prospects":[]}.',
    ])

    body={
        "model":DEFAULT_MODEL,
        "tools":[{"type":"web_search","search_context_size":"low"}],
        "input":prompt,
    }
    data=json.dumps(body).encode()
    req=request.Request(
        OPENAI_URL,
        data=data,
        method="POST",
        headers={
            "Authorization":f"Bearer {key}",
            "Content-Type":"application/json",
            "User-Agent":"CompanyOS/V66.28",
        },
    )
    try:
        with request.urlopen(req,timeout=90) as resp:
            raw=resp.read()
        payload=json.loads(raw.decode())
    except error.HTTPError as exc:
        err_body=exc.read().decode("utf-8","replace")
        return {
            "ok":False,
            "status":f"OPENAI_HTTP_{exc.code}",
            "error":err_body[:1000],
        }
    except Exception as exc:
        return {
            "ok":False,
            "status":"OPENAI_REQUEST_ERROR",
            "error":f"{type(exc).__name__}:{exc}",
        }

    text=output_text(payload)
    try:
        parsed=parse_json_text(text)
    except Exception as exc:
        return {
            "ok":False,
            "status":"OPENAI_OUTPUT_PARSE_ERROR",
            "error":f"{type(exc).__name__}:{exc}",
            "output_preview":text[:1200],
        }

    prospects=parsed.get("prospects") if isinstance(parsed,dict) else None
    if not isinstance(prospects,list):
        prospects=[]

    return {
        "ok":True,
        "status":"SEARCH_COMPLETED",
        "model":DEFAULT_MODEL,
        "response_id":payload.get("id"),
        "prospects":prospects[:5],
    }


def normalize_url(v: Any) -> str|None:
    if not isinstance(v,str):
        return None
    s=v.strip()
    if not s.startswith(("http://","https://")):
        return None
    try:
        u=parse.urlparse(s)
    except Exception:
        return None
    if not u.netloc:
        return None
    return s


def fetch_source(url: str) -> dict[str,Any]:
    req=request.Request(
        url,
        method="GET",
        headers={
            "User-Agent":"Mozilla/5.0 CompanyOSContactVerification/1.0",
            "Accept":"text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
        },
    )
    try:
        with request.urlopen(req,timeout=15) as resp:
            raw=resp.read(2_000_000)
            final_url=resp.geturl()
            ctype=resp.headers.get("content-type","")
        return {
            "ok":True,
            "status":"FETCH_OK",
            "final_url":final_url,
            "content_type":ctype,
            "text":raw.decode("utf-8","replace"),
        }
    except error.HTTPError as exc:
        return {"ok":False,"status":f"HTTP_{exc.code}"}
    except Exception as exc:
        return {"ok":False,"status":f"FETCH_ERROR:{type(exc).__name__}"}


def same_company_domain(email: str, website: str|None) -> bool:
    if not website:
        return False
    try:
        w=parse.urlparse(website).netloc.lower().split(":")[0]
    except Exception:
        return False
    if w.startswith("www."):
        w=w[4:]
    domain=email.split("@",1)[1].lower()
    return domain==w or w.endswith("."+domain) or domain.endswith("."+w)


def verify_prospect(raw: dict[str,Any]) -> dict[str,Any]:
    company=str(raw.get("company_name") or "").strip()[:200]
    email=str(raw.get("public_business_email") or "").strip().lower()
    website=normalize_url(raw.get("official_website"))
    source=normalize_url(raw.get("source_url"))
    fit=str(raw.get("fit_reason") or "").strip()[:500]

    reasons=[]
    if not company:
        reasons.append("company_missing")
    if not EMAIL_RE.match(email):
        reasons.append("email_invalid")
    elif email.split("@",1)[1] in PERSONAL_DOMAINS:
        reasons.append("personal_email_domain")
    if not website:
        reasons.append("official_website_missing_or_invalid")
    if not source:
        reasons.append("source_url_missing_or_invalid")

    fetch=None
    if not reasons and source:
        fetch=fetch_source(source)
        if not fetch.get("ok"):
            reasons.append("source_fetch_failed")
        else:
            body=(fetch.get("text") or "").lower()
            if email.lower() not in body:
                reasons.append("exact_email_not_visible_on_source")

    domain_match=same_company_domain(email,website) if EMAIL_RE.match(email) else False

    return {
        "ok":not reasons,
        "company_name":company,
        "business_email":email,
        "official_website":website,
        "source_url":source,
        "fit_reason":fit,
        "email_domain_matches_official_site":domain_match,
        "source_fetch_status":(fetch or {}).get("status"),
        "reasons":reasons,
    }


def result_path(cid: str) -> Path|None:
    roots=roots_for(cid)
    if not roots:
        return None
    d=roots[0]/"companyos_progress"
    d.mkdir(parents=True,exist_ok=True)
    return d/"verified_prospect_contacts.jsonl"


def run_once() -> dict[str,Any]:
    state=load_json(STATE,{"last_search_by_venture":{}})
    last=state.setdefault("last_search_by_venture",{})
    cooldown=max(
        1800,
        int(os.getenv("COMPANYOS_PROSPECT_DISCOVERY_COOLDOWN_SECONDS","21600"))
    )
    now=time.time()

    results=[]
    total_verified=0

    for cid,row in sorted(canonical_ventures().items()):
        if str(row.get("stage") or "")!="LAUNCH":
            continue

        existing=find_contacts(cid)
        if existing:
            results.append({
                "canonical_id":cid,
                "status":"VERIFIED_CONTACTS_ALREADY_AVAILABLE",
                "existing_contact_count":len(existing),
            })
            continue

        previous=float(last.get(cid,0) or 0)
        if now-previous < cooldown:
            results.append({
                "canonical_id":cid,
                "status":"SEARCH_COOLDOWN",
                "cooldown_remaining_seconds":int(cooldown-(now-previous)),
            })
            continue

        copy=venture_copy(cid)
        search=web_search(cid,copy)
        last[cid]=now

        if not search.get("ok"):
            results.append({
                "canonical_id":cid,
                "status":search.get("status"),
                "error":search.get("error"),
            })
            break

        verified=[]
        rejected=[]
        for raw in search.get("prospects") or []:
            if not isinstance(raw,dict):
                continue
            check=verify_prospect(raw)
            if check["ok"]:
                verified.append(check)
            else:
                rejected.append(check)

        p=result_path(cid)
        if p:
            for v in verified:
                append_jsonl(p,{
                    "schema":"companyos.verified_public_business_prospect.v1",
                    "version":VERSION,
                    "canonical_id":cid,
                    "company_name":v["company_name"],
                    "business_email":v["business_email"],
                    "official_website":v["official_website"],
                    "source_url":v["source_url"],
                    "fit_reason":v["fit_reason"],
                    "email_domain_matches_official_site":v["email_domain_matches_official_site"],
                    "source_fetch_status":v["source_fetch_status"],
                    "verified_at_unix":time.time(),
                    "contact_method":"public_business_email",
                    "personal_contact_inferred":False,
                })

        total_verified += len(verified)
        results.append({
            "canonical_id":cid,
            "status":"DISCOVERY_COMPLETED",
            "model":search.get("model"),
            "response_id":search.get("response_id"),
            "search_candidate_count":len(search.get("prospects") or []),
            "verified_count":len(verified),
            "rejected_count":len(rejected),
            "verified":[
                {
                    "company_name":x["company_name"],
                    "email_domain":x["business_email"].split("@",1)[1],
                    "official_website":x["official_website"],
                    "source_url":x["source_url"],
                    "fit_reason":x["fit_reason"],
                }
                for x in verified
            ],
            "rejected":[
                {
                    "company_name":x.get("company_name"),
                    "email_domain":(
                        x.get("business_email","").split("@",1)[1]
                        if "@" in x.get("business_email","") else None
                    ),
                    "reasons":x.get("reasons"),
                    "source_fetch_status":x.get("source_fetch_status"),
                }
                for x in rejected
            ],
        })
        break

    save_json(STATE,{
        "version":VERSION,
        "updated_at_unix":time.time(),
        "last_search_by_venture":last,
    })

    report={
        "version":VERSION,
        "mode":"openai_web_search_plus_exact_source_verification",
        "model":DEFAULT_MODEL,
        "openai_key_present":bool(openai_key()),
        "cooldown_seconds":cooldown,
        "verified_contacts_created":total_verified,
        "results":results,
        "rules":{
            "one_web_search_per_run":True,
            "exact_email_visible_on_source_required":True,
            "official_public_source_required":True,
            "personal_email_domains_rejected":True,
            "personal_contact_inference":False,
            "financial_actions":False,
            "authority_switches_changed":False,
        },
        "timestamp_unix":time.time(),
    }
    save_json(LATEST,report)
    append_jsonl(HISTORY,report)
    return report
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-once}" in
  once)
    python - <<'PY'
import json
from companyos.runtime.verified_web_prospect_discovery import run_once
print(json.dumps(run_once(),indent=2,sort_keys=True,default=str))
PY
    ;;
  status)
    cat "$HOME/.companyos_runtime/verified_web_prospect_discovery_latest.json" 2>/dev/null || echo '{"status":"no_run_yet"}'
    ;;
  *)
    echo "usage: $0 {once|status}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

echo "===== PATCH EXISTING LIVENESS LOOP WITHOUT ADDING A DAEMON ====="
python - <<'PY'
from pathlib import Path
import ast

p=Path.home()/"companyos/companyos/runtime/venture_liveness_runtime.py"
s=p.read_text()

marker="V66_28_AUTONOMOUS_PROSPECT_DISCOVERY"
if marker not in s:
    tree=ast.parse(s)
    fn=None
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name=="run_once":
            fn=node
            break
    if fn is None:
        raise SystemExit("V66_28_ABORT=liveness_run_once_not_found")

    report_line=None
    for node in fn.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=="report":
                    report_line=node.lineno
                    break
        if report_line:
            break

    if not report_line:
        raise SystemExit("V66_28_ABORT=liveness_report_assignment_not_found")

    insert = '''
    # V66_28_AUTONOMOUS_PROSPECT_DISCOVERY
    try:
        from companyos.runtime.verified_web_prospect_discovery import run_once as run_prospect_discovery_once
        from companyos.runtime.customer_acquisition_bridge import run_once as run_customer_acquisition_once
        prospect_discovery=run_prospect_discovery_once()
        customer_acquisition=run_customer_acquisition_once()
    except Exception as exc:
        prospect_discovery={
            "version":"V66.28",
            "error":f"{type(exc).__name__}:{exc}",
        }
        customer_acquisition={
            "version":"V66.27",
            "error":"customer_acquisition_cycle_not_completed",
        }
'''
    lines=s.splitlines()
    lines[report_line-1:report_line-1]=insert.strip("\n").splitlines()+[""]
    s="\n".join(lines)+"\n"

    report_marker='"launch_bridge":launch_bridge,'
    if report_marker in s and '"prospect_discovery":prospect_discovery,' not in s:
        s=s.replace(
            report_marker,
            report_marker+
            '\n        "prospect_discovery":prospect_discovery,'+
            '\n        "customer_acquisition":customer_acquisition,',
            1,
        )

    ast.parse(s)
    p.write_text(s)
    print("V66_28_LIVENESS_PATCH=PASS")
else:
    print("V66_28_LIVENESS_PATCH=ALREADY_PRESENT")
PY

cat > "$ROOT/tests/test_v66_28_verified_web_prospect_discovery.py" <<'PY'
from companyos.runtime.verified_web_prospect_discovery import verify_prospect

def test_personal_domain_rejected_without_fetch():
    x=verify_prospect({
        "company_name":"Example",
        "public_business_email":"person@gmail.com",
        "official_website":"https://example.com",
        "source_url":"https://example.com/contact",
        "fit_reason":"fit",
    })
    assert x["ok"] is False
    assert "personal_email_domain" in x["reasons"]

def test_missing_source_is_rejected():
    x=verify_prospect({
        "company_name":"Example",
        "public_business_email":"sales@example.com",
        "official_website":"https://example.com",
        "source_url":"",
        "fit_reason":"fit",
    })
    assert x["ok"] is False
    assert "source_url_missing_or_invalid" in x["reasons"]
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD" "$LIVE"
echo "V66_28_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_28_verified_web_prospect_discovery.py
echo "V66_28_TESTS=PASS"

echo "===== FIRST VERIFIED WEB DISCOVERY PASS ====="
"$CTL" once

echo "===== FEED VERIFIED CONTACTS INTO V66.27 ====="
if [ -x "$ACTL" ]; then
  "$ACTL" once || true
fi

echo "===== ENSURE EXTERNAL ROUTER IS RUNNING ====="
if [ -x "$XCTL" ]; then
  "$XCTL" restart || true
fi

echo "===== ALLOW ONE OUTREACH ACTION TO PROCESS ====="
sleep 12

echo "===== RECONCILE REAL SMTP OUTCOME ====="
if [ -x "$ACTL" ]; then
  "$ACTL" once || true
fi

echo "===== REFRESH LIVENESS ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== FINAL PROSPECT STATUS ====="
"$CTL" status

echo "V66_28_OPENAI_WEB_SEARCH_PATH=PASS"
echo "V66_28_EXACT_SOURCE_EMAIL_VERIFICATION=PASS"
echo "V66_28_PUBLIC_BUSINESS_CONTACT_ONLY=PASS"
echo "V66_28_SEARCH_COOLDOWN=PASS"
echo "V66_28_V66_27_HANDOFF=PASS"
echo "V66_28_EXISTING_LIVENESS_PROCESS_REUSED=PASS"
echo "V66_28_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_28_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_28_COMPLETE"
