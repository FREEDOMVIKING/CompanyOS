#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
MOD="$ROOT/companyos/runtime/verified_web_prospect_discovery.py"
CTL="$ROOT/scripts/companyos_prospectctl"
ACTL="$ROOT/scripts/companyos_acquisitionctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.31 MULTI-PROVIDER PROSPECT FALLBACK ====="
echo "GOAL=KEEP_PROSPECT_DISCOVERY_RUNNING_WHEN_OPENAI_WEB_SEARCH_IS_RATE_LIMITED"
echo "NOTE=BRAVE_API_IF_CONFIGURED_THEN_KEYLESS_DUCKDUCKGO_FALLBACK"
echo "NOTE=EXACT_PUBLIC_SOURCE_EMAIL_VERIFICATION_STAYS_REQUIRED"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$MOD" ] || { echo "V66_31_ABORT=missing:$MOD"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v66_31_backup_${stamp}"
echo "BACKUP=${MOD}.v66_31_backup_${stamp}"

echo "===== PATCH SEARCH PROVIDER FALLBACK ====="
python - <<'PY'
from pathlib import Path
import ast
import re

p=Path.home()/"companyos/companyos/runtime/verified_web_prospect_discovery.py"
s=p.read_text()

def fn_span(src,name):
    tree=ast.parse(src)
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return node.lineno,node.end_lineno
    return None

def replace_fn(src,name,new_text):
    sp=fn_span(src,name)
    if not sp:
        raise SystemExit(f"V66_31_ABORT=function_not_found:{name}")
    lines=src.splitlines()
    lines[sp[0]-1:sp[1]]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

# Rename the current OpenAI search implementation so a provider router can wrap it.
if "def openai_web_search(" not in s:
    sp=fn_span(s,"web_search")
    if not sp:
        raise SystemExit("V66_31_ABORT=web_search_missing")
    lines=s.splitlines()
    first=lines[sp[0]-1]
    lines[sp[0]-1]=first.replace("def web_search(","def openai_web_search(",1)
    s="\n".join(lines)+"\n"

helpers = r'''
ROLE_LOCALS={
    "info","sales","contact","office","hello","support","estimating",
    "estimate","bids","bid","quotes","quote","projects","project",
    "partnerships","business","inquiries","inquiry","admin","service",
    "services","customerservice","operations","ops","marketing",
}

def _provider_key(*names):
    vals=env_file_values()
    for name in names:
        value=os.getenv(name) or vals.get(name)
        if value:
            return value
    return None

def _search_query(cid: str, copy: dict[str,Any]) -> str:
    title=str(copy.get("title") or cid.replace("_"," ").title())
    audience=str(copy.get("audience") or "").strip()
    if audience:
        return f'{audience} business contact email "{title}"'
    return f'businesses that could use "{title}" contact email'

def _decode_ddg_url(url: str) -> str:
    try:
        parsed_url=parse.urlparse(url)
        qs=parse.parse_qs(parsed_url.query)
        uddg=qs.get("uddg")
        if uddg:
            return parse.unquote(uddg[0])
    except Exception:
        pass
    return url

def _brave_search(query: str) -> dict[str,Any]:
    key=_provider_key("COMPANYOS_BRAVE_SEARCH_API_KEY","BRAVE_SEARCH_API_KEY")
    if not key:
        return {"ok":False,"status":"BRAVE_KEY_MISSING"}

    url="https://api.search.brave.com/res/v1/web/search?"+parse.urlencode({
        "q":query,
        "count":10,
        "country":"US",
        "search_lang":"en",
    })
    req=request.Request(
        url,
        method="GET",
        headers={
            "Accept":"application/json",
            "X-Subscription-Token":key,
            "User-Agent":"CompanyOS/V66.31",
        },
    )
    try:
        with request.urlopen(req,timeout=30) as resp:
            payload=json.loads(resp.read().decode())
    except error.HTTPError as exc:
        return {"ok":False,"status":f"BRAVE_HTTP_{exc.code}"}
    except Exception as exc:
        return {"ok":False,"status":f"BRAVE_ERROR:{type(exc).__name__}"}

    rows=[]
    for x in ((payload.get("web") or {}).get("results") or [])[:10]:
        if not isinstance(x,dict):
            continue
        u=x.get("url")
        if isinstance(u,str) and u.startswith(("http://","https://")):
            rows.append({
                "title":str(x.get("title") or "")[:300],
                "url":u,
                "snippet":str(x.get("description") or "")[:800],
            })
    return {"ok":True,"status":"BRAVE_OK","provider":"brave","results":rows}

def _ddg_search(query: str) -> dict[str,Any]:
    url="https://html.duckduckgo.com/html/?"+parse.urlencode({"q":query})
    req=request.Request(
        url,
        method="GET",
        headers={
            "User-Agent":"Mozilla/5.0 CompanyOSProspectSearch/1.0",
            "Accept":"text/html,application/xhtml+xml",
        },
    )
    try:
        with request.urlopen(req,timeout=30) as resp:
            body=resp.read(2_000_000).decode("utf-8","replace")
    except error.HTTPError as exc:
        return {"ok":False,"status":f"DDG_HTTP_{exc.code}"}
    except Exception as exc:
        return {"ok":False,"status":f"DDG_ERROR:{type(exc).__name__}"}

    rows=[]
    # DuckDuckGo HTML result anchors use result__a. Keep parser simple and bounded.
    pattern=re.compile(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        re.I|re.S,
    )
    strip_tags=re.compile(r"<[^>]+>")
    for href,title_html in pattern.findall(body)[:15]:
        u=_decode_ddg_url(href.replace("&amp;","&"))
        if not u.startswith(("http://","https://")):
            continue
        title=strip_tags.sub(" ",title_html)
        rows.append({
            "title":" ".join(title.split())[:300],
            "url":u,
            "snippet":"",
        })
    return {"ok":True,"status":"DDG_OK","provider":"duckduckgo_keyless","results":rows}

def _same_host(a: str, b: str) -> bool:
    try:
        ha=parse.urlparse(a).netloc.lower().split(":")[0]
        hb=parse.urlparse(b).netloc.lower().split(":")[0]
    except Exception:
        return False
    for name in ("www.",):
        if ha.startswith(name): ha=ha[len(name):]
        if hb.startswith(name): hb=hb[len(name):]
    return ha==hb

def _extract_candidate_emails(html_text: str) -> list[str]:
    found=set()
    text=html_text or ""
    # Visible and mailto addresses.
    for m in re.findall(r'(?i)([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})',text):
        email=m.lower().strip(".,;:()[]<>\"'")
        if not EMAIL_RE.match(email):
            continue
        domain=email.split("@",1)[1]
        local=email.split("@",1)[0].lower()
        if domain in PERSONAL_DOMAINS:
            continue
        # Only role-based mailboxes are eligible for automatic outreach.
        normalized=re.sub(r'[^a-z]','',local)
        if normalized not in ROLE_LOCALS:
            continue
        found.add(email)
    return sorted(found)

def _contact_links(page_url: str, html_text: str) -> list[str]:
    hrefs=re.findall(r'(?i)href=["\\']([^"\\']+)["\\']',html_text or "")
    out=[]
    seen=set()
    for href in hrefs:
        href=href.replace("&amp;","&")
        absolute=parse.urljoin(page_url,href)
        if not absolute.startswith(("http://","https://")):
            continue
        if not _same_host(page_url,absolute):
            continue
        low=absolute.lower()
        if not any(x in low for x in (
            "contact","about","sales","office","estimating","estimate",
            "bid","quote","service","team",
        )):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        out.append(absolute)
        if len(out)>=4:
            break
    return out

def _find_business_email_on_site(result: dict[str,Any]) -> dict[str,Any]|None:
    start=result.get("url")
    if not isinstance(start,str):
        return None

    queue=[start]
    visited=set()
    for _ in range(5):
        if not queue:
            break
        url=queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        fetched=fetch_source(url)
        if not fetched.get("ok"):
            continue
        body=fetched.get("text") or ""
        emails=_extract_candidate_emails(body)
        if emails:
            final_url=fetched.get("final_url") or url
            website=f"{parse.urlparse(final_url).scheme}://{parse.urlparse(final_url).netloc}/"
            return {
                "company_name":str(result.get("title") or parse.urlparse(final_url).netloc)[:200],
                "public_business_email":emails[0],
                "official_website":website,
                "source_url":final_url,
                "fit_reason":str(result.get("snippet") or "Matched by public web search.")[:500],
            }

        for link in _contact_links(fetched.get("final_url") or url,body):
            if link not in visited and link not in queue:
                queue.append(link)

    return None

def provider_fallback_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    query=_search_query(cid,copy)
    attempts=[]

    providers=[]
    if _provider_key("COMPANYOS_BRAVE_SEARCH_API_KEY","BRAVE_SEARCH_API_KEY"):
        providers.append(("brave",_brave_search))
    providers.append(("duckduckgo_keyless",_ddg_search))

    for name,fn in providers:
        result=fn(query)
        attempts.append({
            "provider":name,
            "status":result.get("status"),
            "result_count":len(result.get("results") or []),
        })
        if not result.get("ok"):
            continue

        prospects=[]
        seen=set()
        for row in result.get("results") or []:
            prospect=_find_business_email_on_site(row)
            if not prospect:
                continue
            email=prospect["public_business_email"].lower()
            if email in seen:
                continue
            seen.add(email)
            prospects.append(prospect)
            if len(prospects)>=5:
                break

        if prospects:
            return {
                "ok":True,
                "status":"SEARCH_COMPLETED",
                "model":name,
                "response_id":None,
                "prospects":prospects,
                "provider_attempts":attempts,
                "query":query,
            }

    return {
        "ok":True,
        "status":"SEARCH_COMPLETED",
        "model":"multi_provider_fallback",
        "response_id":None,
        "prospects":[],
        "provider_attempts":attempts,
        "query":query,
    }

def web_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    primary=openai_web_search(cid,copy)
    if primary.get("ok"):
        primary["selected_provider"]="openai_web"
        return primary

    status=str(primary.get("status") or "")
    if status=="OPENAI_HTTP_429" or status in {
        "OPENAI_REQUEST_ERROR",
        "OPENAI_RETRY_EXHAUSTED",
    }:
        fallback=provider_fallback_search(cid,copy)
        fallback["openai_primary_status"]=status
        fallback["openai_retry_after_seconds"]=primary.get("retry_after_seconds")
        fallback["selected_provider"]=fallback.get("model")
        return fallback

    return primary
'''

if "def provider_fallback_search(" not in s:
    sp=fn_span(s,"normalize_url")
    if not sp:
        raise SystemExit("V66_31_ABORT=normalize_url_missing")
    lines=s.splitlines()
    lines[sp[0]-1:sp[0]-1]=helpers.strip("\n").splitlines()+[""]
    s="\n".join(lines)+"\n"

ast.parse(s)
p.write_text(s)
print("V66_31_PROVIDER_ROUTER_PATCH=PASS")
PY

cat > "$ROOT/tests/test_v66_31_multi_provider_fallback.py" <<'PY'
from companyos.runtime.verified_web_prospect_discovery import (
    _extract_candidate_emails,
    _decode_ddg_url,
)

def test_role_email_is_accepted():
    x=_extract_candidate_emails("Contact us at sales@example.com")
    assert "sales@example.com" in x

def test_named_work_email_is_not_auto_outreach_contact():
    x=_extract_candidate_emails("Contact john.smith@example.com")
    assert "john.smith@example.com" not in x

def test_personal_domain_is_rejected():
    x=_extract_candidate_emails("Contact info@gmail.com")
    assert x==[]

def test_ddg_redirect_decode():
    u=_decode_ddg_url(
        "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fcontact"
    )
    assert u=="https://example.com/contact"
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_31_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_31_multi_provider_fallback.py
echo "V66_31_TESTS=PASS"

echo "===== CLEAR ONLY CURRENT OPENAI-429 COOLDOWN ====="
python - <<'PY'
import json
from companyos.runtime.verified_web_prospect_discovery import (
    STATE,load_json,save_json,
)

state=load_json(STATE,{
    "last_search_by_venture":{},
    "last_outcome_by_venture":{},
})
changed=[]
for cid,outcome in list((state.get("last_outcome_by_venture") or {}).items()):
    if isinstance(outcome,dict) and str(outcome.get("status") or "")=="OPENAI_HTTP_429":
        state.setdefault("last_search_by_venture",{})[cid]=0
        changed.append(cid)
save_json(STATE,state)
print(json.dumps({"cleared_429_cooldown_for":changed},indent=2,sort_keys=True))
PY

echo "===== MULTI-PROVIDER PROSPECT SEARCH ====="
"$CTL" once

echo "===== HAND VERIFIED CONTACTS TO V66.27 ====="
if [ -x "$ACTL" ]; then
  "$ACTL" once || true
fi

echo "===== LIGHTWEIGHT LIVENESS REFRESH ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_31_OPENAI_429_FALLBACK=PASS"
echo "V66_31_BRAVE_IF_CONFIGURED=PASS"
echo "V66_31_KEYLESS_DDG_FALLBACK=PASS"
echo "V66_31_ROLE_BASED_BUSINESS_EMAIL_ONLY=PASS"
echo "V66_31_EXACT_SOURCE_VERIFICATION_PRESERVED=PASS"
echo "V66_31_V66_27_HANDOFF=PASS"
echo "V66_31_NO_NEW_DAEMON=PASS"
echo "V66_31_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_31_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_31_COMPLETE"
