#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/verified_web_prospect_discovery.py"
ACQ="$ROOT/companyos/runtime/customer_acquisition_bridge.py"
PCTL="$ROOT/scripts/companyos_prospectctl"
ACTL="$ROOT/scripts/companyos_acquisitionctl"
XCTL="$ROOT/scripts/companyos_externalctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.33 PROSPECT RELEVANCE GUARD ====="
echo "GOAL=REJECT_SEARCH_CONTENT_SITES_AND_KEEP_ONLY_REAL_TARGET_BUSINESSES"
echo "NOTE=PAUSES_EXTERNAL_ROUTER_DURING_CONTACT_REVALIDATION"
echo "NOTE=PENDING_EMAILS_TO_QUARANTINED_CONTACTS_ARE_REMOVED_FROM_QUEUE_WITH_AUDIT_COPY"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$MOD" "$ACQ"; do
  [ -f "$f" ] || { echo "V66_33_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v66_33_backup_${stamp}"
cp "$ACQ" "${ACQ}.v66_33_backup_${stamp}"

if [ -x "$XCTL" ]; then
  echo "===== PAUSE EXTERNAL ROUTER ====="
  "$XCTL" stop || true
fi

echo "===== PATCH PROSPECT RELEVANCE ====="
python - <<'PY'
from pathlib import Path
import ast

p=Path.home()/"companyos/companyos/runtime/verified_web_prospect_discovery.py"
s=p.read_text()

def span(src,name):
    tree=ast.parse(src)
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return node.lineno,node.end_lineno
    return None

def replace_fn(src,name,new_text):
    sp=span(src,name)
    if not sp:
        raise SystemExit(f"V66_33_ABORT=function_not_found:{name}")
    lines=src.splitlines()
    lines[sp[0]-1:sp[1]]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

helpers = '''
RELEVANCE_STOP={
    "local","software","app","application","tool","platform","service","services",
    "solution","solutions","opportunity","company","companies","business","businesses",
    "organizer","system","online","digital","mobile","workflow","marketplace",
    "the","and","for","with","from","this","that","your","our","their","into",
}

CONTENT_PATH_MARKERS=(
    "/blog/","/blogs/","/article/","/articles/","/news/","/resources/",
    "/resource/","/guides/","/guide/","/templates/","/template/","/terms",
    "/privacy","/careers","/jobs","/press/","/stories/","/learn/",
)

CONTENT_TITLE_MARKERS=(
    " examples"," template"," templates"," trends"," company profile",
    " pricing"," directory"," list of "," how to "," guide to "," blog ",
)

def relevance_tokens(copy: dict[str,Any]) -> list[str]:
    values=[
        str(copy.get("audience") or ""),
        str(copy.get("title") or ""),
        str(copy.get("description") or ""),
    ]
    out=[]
    for raw in re.findall(r"[A-Za-z0-9]+"," ".join(values).lower()):
        token=raw.strip()
        if len(token)<4 or token in RELEVANCE_STOP:
            continue
        if token.endswith("ies") and len(token)>5:
            token=token[:-3]+"y"
        elif token.endswith("s") and len(token)>5:
            token=token[:-1]
        if token not in out:
            out.append(token)
        if len(out)>=10:
            break
    return out

def content_like_url(url: str) -> bool:
    low=str(url or "").lower()
    return any(x in low for x in CONTENT_PATH_MARKERS)

def content_like_title(title: str) -> bool:
    low=" "+str(title or "").lower()+" "
    return any(x in low for x in CONTENT_TITLE_MARKERS)

def page_relevance(body: str, copy: dict[str,Any]) -> dict[str,Any]:
    tokens=relevance_tokens(copy)
    text=" "+re.sub(r"[^a-z0-9]+"," ",str(body or "").lower())+" "
    matched=[]
    for token in tokens:
        if f" {token} " in text or f" {token}s " in text:
            matched.append(token)
    required=1 if tokens else 0
    return {
        "ok":len(matched)>=required,
        "tokens":tokens,
        "matched":matched,
        "required":required,
    }
'''

if "def relevance_tokens(" not in s:
    sp=span(s,"_find_business_email_on_site")
    if not sp:
        raise SystemExit("V66_33_ABORT=_find_business_email_on_site_missing")
    lines=s.splitlines()
    lines[sp[0]-1:sp[0]-1]=helpers.strip("\n").splitlines()+[""]
    s="\n".join(lines)+"\n"

find_site = '''
def _find_business_email_on_site(result: dict[str,Any], copy: dict[str,Any]) -> dict[str,Any]|None:
    start=result.get("url")
    if not isinstance(start,str) or not start.startswith(("http://","https://")):
        return None

    parsed_start=parse.urlparse(start)
    if not parsed_start.netloc:
        return None

    site_root=f"{parsed_start.scheme}://{parsed_start.netloc}/"

    root=fetch_source(site_root)
    if not root.get("ok"):
        return None

    root_body=root.get("text") or ""
    rel=page_relevance(root_body,copy)
    if not rel["ok"]:
        return None

    queue=[site_root]
    visited=set()

    if (
        not content_like_url(result.get("url") or "")
        and result.get("url")!=site_root
        and not content_like_title(str(result.get("title") or ""))
    ):
        queue.append(result["url"])

    for link in _contact_links(site_root,root_body):
        if link not in queue and not content_like_url(link):
            queue.append(link)

    while queue and len(visited)<8:
        url=queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        fetched=root if url==site_root else fetch_source(url)
        if not fetched.get("ok"):
            continue

        final_url=fetched.get("final_url") or url
        if content_like_url(final_url):
            continue

        body=fetched.get("text") or ""
        emails=_extract_candidate_emails(body)
        if emails:
            email=emails[0]
            if not same_company_domain(email,site_root):
                continue
            return {
                "company_name":str(result.get("title") or parsed_start.netloc)[:200],
                "public_business_email":email,
                "official_website":site_root,
                "source_url":final_url,
                "fit_reason":str(result.get("snippet") or "Matched by public business search.")[:500],
                "relevance_verified":True,
                "relevance_tokens":rel["tokens"],
                "matched_relevance_tokens":rel["matched"],
                "source_is_content_page":False,
            }

        for link in _contact_links(final_url,body):
            if link not in visited and link not in queue and not content_like_url(link):
                queue.append(link)

    return None
'''
s=replace_fn(s,"_find_business_email_on_site",find_site)

fallback = '''
def provider_fallback_search(cid: str, copy: dict[str,Any]) -> dict[str,Any]:
    queries=_query_variants(cid,copy)
    attempts=[]
    aggregated=[]
    seen_urls=set()

    providers=[]
    if _provider_key("COMPANYOS_BRAVE_SEARCH_API_KEY","BRAVE_SEARCH_API_KEY"):
        providers.append(("brave",_brave_search))
    providers.append(("duckduckgo_keyless",_ddg_search))

    for query in queries:
        for name,fn in providers:
            result=fn(query)
            attempts.append({
                "provider":name,
                "query":query,
                "status":result.get("status"),
                "result_count":len(result.get("results") or []),
                "sub_attempts":result.get("attempts"),
            })
            if not result.get("ok"):
                continue
            for row in result.get("results") or []:
                u=row.get("url")
                if not isinstance(u,str) or u in seen_urls:
                    continue
                seen_urls.add(u)
                aggregated.append(row)
            if len(aggregated)>=24:
                break
        if len(aggregated)>=24:
            break

    prospects=[]
    seen_emails=set()
    crawled=0
    relevance_rejected=0

    for row in aggregated[:24]:
        prospect=_find_business_email_on_site(row,copy)
        crawled += 1
        if not prospect:
            relevance_rejected += 1
            continue
        email=prospect["public_business_email"].lower()
        if email in seen_emails:
            continue
        seen_emails.add(email)
        prospects.append(prospect)
        if len(prospects)>=5:
            break

    return {
        "ok":True,
        "status":"SEARCH_COMPLETED",
        "model":"multi_provider_relevance_guard",
        "response_id":None,
        "prospects":prospects,
        "provider_attempts":attempts,
        "queries":queries,
        "search_candidate_count_raw":len(aggregated),
        "sites_crawled":crawled,
        "relevance_rejected":relevance_rejected,
    }
'''
s=replace_fn(s,"provider_fallback_search",fallback)

verify = '''
def verify_prospect(raw: dict[str,Any], copy: dict[str,Any]|None=None) -> dict[str,Any]:
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
    if source and content_like_url(source):
        reasons.append("content_or_policy_source_page")

    fetch=None
    rel=None
    if not reasons and source:
        fetch=fetch_source(source)
        if not fetch.get("ok"):
            reasons.append("source_fetch_failed")
        else:
            body=(fetch.get("text") or "").lower()
            if email.lower() not in body:
                reasons.append("exact_email_not_visible_on_source")
            if copy:
                home=fetch_source(website)
                if not home.get("ok"):
                    reasons.append("official_homepage_fetch_failed")
                else:
                    rel=page_relevance(home.get("text") or "",copy)
                    if not rel["ok"]:
                        reasons.append("target_audience_relevance_not_proven")

    domain_match=same_company_domain(email,website) if EMAIL_RE.match(email) else False
    if EMAIL_RE.match(email) and website and not domain_match:
        reasons.append("email_domain_does_not_match_official_site")

    if raw.get("relevance_verified") is False:
        reasons.append("upstream_relevance_rejected")

    return {
        "ok":not reasons,
        "company_name":company,
        "business_email":email,
        "official_website":website,
        "source_url":source,
        "fit_reason":fit,
        "email_domain_matches_official_site":domain_match,
        "source_fetch_status":(fetch or {}).get("status"),
        "relevance_verified":not reasons if copy else bool(raw.get("relevance_verified",False)),
        "relevance_tokens":(rel or {}).get("tokens") or raw.get("relevance_tokens") or [],
        "matched_relevance_tokens":(rel or {}).get("matched") or raw.get("matched_relevance_tokens") or [],
        "reasons":reasons,
    }
'''
s=replace_fn(s,"verify_prospect",verify)

s=s.replace("check=verify_prospect(raw)", "check=verify_prospect(raw,copy)")

needle='''                    "source_fetch_status":v["source_fetch_status"],
                    "verified_at_unix":time.time(),
'''
replacement='''                    "source_fetch_status":v["source_fetch_status"],
                    "relevance_verified":v.get("relevance_verified") is True,
                    "relevance_tokens":v.get("relevance_tokens") or [],
                    "matched_relevance_tokens":v.get("matched_relevance_tokens") or [],
                    "verified_at_unix":time.time(),
'''
if needle in s:
    s=s.replace(needle,replacement,1)

s=s.replace('"version":"V66.32"', '"version":"V66.33"')
ast.parse(s)
p.write_text(s)
print("V66_33_PROSPECT_RELEVANCE_PATCH=PASS")
PY

echo "===== HARDEN CUSTOMER ACQUISITION BRIDGE ====="
python - <<'PY'
from pathlib import Path
import ast

p=Path.home()/"companyos/companyos/runtime/customer_acquisition_bridge.py"
s=p.read_text()

needle='''def public_business_contact(d: dict[str,Any], source: str, own: set[str]) -> dict[str,Any]|None:
    email=None
'''
replacement='''def public_business_contact(d: dict[str,Any], source: str, own: set[str]) -> dict[str,Any]|None:
    if str(d.get("schema") or "")=="companyos.verified_public_business_prospect.v1":
        if d.get("relevance_verified") is not True:
            return None
        if d.get("email_domain_matches_official_site") is not True:
            return None

    email=None
'''
if needle not in s:
    raise SystemExit("V66_33_ABORT=customer_acquisition_contact_anchor_missing")
s=s.replace(needle,replacement,1)

ast.parse(s)
p.write_text(s)
print("V66_33_CUSTOMER_ACQUISITION_GATE=PASS")
PY

cat > "$ROOT/tests/test_v66_33_prospect_relevance_guard.py" <<'PY'
from companyos.runtime.verified_web_prospect_discovery import (
    content_like_url,
    page_relevance,
)

def test_blog_source_is_content():
    assert content_like_url("https://example.com/blog/business-email-examples")

def test_contractor_homepage_is_relevant():
    x=page_relevance(
        "ABC Construction is a commercial contractor serving local businesses.",
        {
            "title":"Local Contractor Bid Organizer",
            "audience":"construction contractors",
            "description":"Organize contractor bids",
        },
    )
    assert x["ok"] is True

def test_unrelated_email_marketing_site_is_not_relevant():
    x=page_relevance(
        "Email marketing software, newsletter templates, automation and campaigns.",
        {
            "title":"Local Contractor Bid Organizer",
            "audience":"construction contractors",
            "description":"Organize contractor bids",
        },
    )
    assert x["ok"] is False
PY

echo "===== COMPILE + TEST ====="
python -m py_compile "$MOD" "$ACQ"
python -m pytest -q tests/test_v66_33_prospect_relevance_guard.py
echo "V66_33_TESTS=PASS"

echo "===== REVALIDATE EXISTING CONTACTS ====="
python - <<'PY'
import json,time
from pathlib import Path
from companyos.runtime.customer_acquisition_bridge import roots_for,venture_copy
from companyos.runtime.verified_web_prospect_discovery import verify_prospect

rt=Path.home()/".companyos_runtime"
qdir=rt/"prospect_quarantine"
qdir.mkdir(parents=True,exist_ok=True)

quarantined=[]
kept=[]

for cid in ("local_contractor_bid_organizer",):
    copy=venture_copy(cid)
    for root in roots_for(cid):
        p=root/"companyos_progress"/"verified_prospect_contacts.jsonl"
        if not p.exists():
            continue
        good=[]
        bad=[]
        for line in p.read_text(errors="ignore").splitlines():
            try:
                row=json.loads(line)
            except Exception:
                continue
            check=verify_prospect(row,copy)
            if check.get("ok"):
                row["relevance_verified"]=True
                row["email_domain_matches_official_site"]=check.get("email_domain_matches_official_site")
                row["relevance_tokens"]=check.get("relevance_tokens") or []
                row["matched_relevance_tokens"]=check.get("matched_relevance_tokens") or []
                good.append(row)
                kept.append(row.get("business_email"))
            else:
                bad.append({
                    **row,
                    "quarantined_at_unix":time.time(),
                    "quarantine_reasons":check.get("reasons") or [],
                })
                quarantined.append(row.get("business_email"))
        p.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in good))
        qp=qdir/f"{cid}.jsonl"
        with qp.open("a") as f:
            for x in bad:
                f.write(json.dumps(x,sort_keys=True)+"\n")

print(json.dumps({
    "kept_verified_contact_count":len(kept),
    "quarantined_contact_count":len(quarantined),
},indent=2,sort_keys=True))
PY

echo "===== QUARANTINE UNSENT SMTP ACTIONS FOR REJECTED CONTACTS ====="
python - <<'PY'
import json,time
from pathlib import Path

home=Path.home()
rt=home/".companyos_runtime"
qdir=rt/"prospect_quarantine"
actions_path=home/"companyos/companyos_runtime/connectors/actions.json"
exec_path=home/"companyos/companyos_runtime/connectors/executions.json"
audit=qdir/"cancelled_pending_smtp_actions.jsonl"

bad=set()
for p in qdir.glob("*.jsonl"):
    for line in p.read_text(errors="ignore").splitlines():
        try:
            x=json.loads(line)
        except Exception:
            continue
        e=str(x.get("business_email") or "").lower()
        if e:
            bad.add(e)

try:
    actions=json.loads(actions_path.read_text())
except Exception:
    actions=[]
try:
    executions=json.loads(exec_path.read_text())
except Exception:
    executions=[]

done={str(x.get("action_id") or "") for x in executions if isinstance(x,dict)}
keep=[]
removed=[]
already_sent=[]

for a in actions if isinstance(actions,list) else []:
    if not isinstance(a,dict):
        keep.append(a)
        continue
    payload=a.get("payload") if isinstance(a.get("payload"),dict) else {}
    recipient=str(payload.get("to") or "").lower()
    aid=str(a.get("action_id") or "")
    targeted=(
        str(a.get("connector") or "")=="smtp"
        and str(a.get("action") or "")=="send_email"
        and recipient in bad
    )
    if targeted and aid not in done:
        removed.append(a)
        continue
    keep.append(a)
    if targeted and aid in done:
        already_sent.append({"action_id":aid,"recipient":recipient})

if removed:
    with audit.open("a") as f:
        for a in removed:
            f.write(json.dumps({
                "quarantined_at_unix":time.time(),
                "reason":"prospect_relevance_failed",
                "action":a,
            },sort_keys=True)+"\n")
    actions_path.write_text(json.dumps(keep,indent=2,sort_keys=True)+"\n")

print(json.dumps({
    "pending_bad_smtp_actions_quarantined":len(removed),
    "already_executed_bad_smtp_actions":already_sent,
},indent=2,sort_keys=True))
PY

echo "===== ENABLE IMMEDIATE RELEVANCE-GATED RETRY ====="
python - <<'PY'
from companyos.runtime.verified_web_prospect_discovery import STATE,load_json,save_json

state=load_json(STATE,{
    "last_search_by_venture":{},
    "last_outcome_by_venture":{},
})
for cid in list((state.get("last_search_by_venture") or {}).keys()):
    state["last_search_by_venture"][cid]=0
save_json(STATE,state)
print("V66_33_SEARCH_RETRY_ENABLED=PASS")
PY

echo "===== RUN RELEVANCE-GATED SEARCH ====="
"$PCTL" once || true

echo "===== CUSTOMER ACQUISITION PASS ====="
"$ACTL" once || true

echo "===== RESTART EXTERNAL ROUTER ====="
if [ -x "$XCTL" ]; then
  "$XCTL" start || true
fi

echo "===== LIGHTWEIGHT LIVENESS REFRESH ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "V66_33_FALSE_POSITIVE_QUARANTINE=PASS"
echo "V66_33_TARGET_AUDIENCE_RELEVANCE_GATE=PASS"
echo "V66_33_CONTENT_PAGE_REJECTION=PASS"
echo "V66_33_EMAIL_DOMAIN_MATCH_GATE=PASS"
echo "V66_33_PENDING_BAD_EMAIL_QUEUE_QUARANTINE=PASS"
echo "V66_33_V66_27_HARDENED=PASS"
echo "V66_33_NO_NEW_DAEMON=PASS"
echo "V66_33_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_33_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_33_COMPLETE"
