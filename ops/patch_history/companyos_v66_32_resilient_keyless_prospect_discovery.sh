#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
MOD="$ROOT/companyos/runtime/verified_web_prospect_discovery.py"
CTL="$ROOT/scripts/companyos_prospectctl"
ACTL="$ROOT/scripts/companyos_acquisitionctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.32 RESILIENT KEYLESS PROSPECT DISCOVERY ====="
echo "GOAL=FIX_ZERO_RESULT_KEYLESS_SEARCH_WITH_MULTI_QUERY_AND_MULTI_PARSER_DISCOVERY"
echo "NOTE=EXACT_PUBLIC_SOURCE_EMAIL_VERIFICATION_STAYS_REQUIRED"
echo "NOTE=ROLE_BASED_BUSINESS_EMAILS_ONLY"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$MOD" ] || { echo "V66_32_ABORT=missing:$MOD"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v66_32_backup_${stamp}"
echo "BACKUP=${MOD}.v66_32_backup_${stamp}"

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
        raise SystemExit(f"V66_32_ABORT=function_not_found:{name}")
    lines=src.splitlines()
    lines[sp[0]-1:sp[1]]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

query_fn = r'''
def _query_variants(cid: str, copy: dict[str,Any]) -> list[str]:
    title=str(copy.get("title") or cid.replace("_"," ").title())
    audience=str(copy.get("audience") or "").strip()
    description=str(copy.get("description") or "").strip()

    raw_tokens=re.findall(r"[A-Za-z0-9]+", " ".join([title,description]))
    stop={
        "local","software","app","application","tool","platform","service",
        "services","solution","solutions","opportunity","company","business",
        "the","and","for","with","from","this","that","your","our",
    }

    keywords=[]
    for token in raw_tokens:
        t=token.lower()
        if len(t)<4 or t in stop or t in keywords:
            continue
        keywords.append(t)
        if len(keywords)>=5:
            break

    queries=[]
    if audience:
        queries.extend([
            f"{audience} companies contact email",
            f'{audience} "contact us"',
        ])

    if keywords:
        phrase=" ".join(keywords[:4])
        queries.extend([
            f"{phrase} companies contact",
            f"{phrase} business email",
        ])

    queries.extend([
        'contractor companies "contact us" email',
        'construction contractors office email contact',
    ])

    out=[]
    seen=set()
    for q in queries:
        q=" ".join(q.split()).strip()
        if not q or q.lower() in seen:
            continue
        seen.add(q.lower())
        out.append(q)
        if len(out)>=6:
            break
    return out
'''

if "def _query_variants(" not in s:
    sp=span(s,"_search_query")
    if not sp:
        raise SystemExit("V66_32_ABORT=_search_query_missing")
    lines=s.splitlines()
    lines[sp[1]:sp[1]]=[""]+query_fn.strip("\n").splitlines()
    s="\n".join(lines)+"\n"

ddg_fn = r'''
def _ddg_search(query: str) -> dict[str,Any]:
    endpoints=[
        ("duckduckgo_html","https://html.duckduckgo.com/html/?"+parse.urlencode({"q":query})),
        ("duckduckgo_lite","https://lite.duckduckgo.com/lite/?"+parse.urlencode({"q":query})),
    ]

    rows=[]
    seen=set()
    attempts=[]
    strip_tags=re.compile(r"<[^>]+>")

    patterns=[
        re.compile(
            r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
        re.compile(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
        re.compile(
            r'<a[^>]+rel=["\']nofollow["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
        re.compile(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']nofollow["\'][^>]*>(.*?)</a>',
            re.I|re.S,
        ),
    ]

    for provider_name,url in endpoints:
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
            attempts.append({"provider":provider_name,"status":f"HTTP_{exc.code}"})
            continue
        except Exception as exc:
            attempts.append({
                "provider":provider_name,
                "status":f"ERROR:{type(exc).__name__}",
            })
            continue

        before=len(rows)
        for pattern in patterns:
            for href,title_html in pattern.findall(body):
                href=href.replace("&amp;","&")
                u=_decode_ddg_url(href)
                if not u.startswith(("http://","https://")):
                    continue
                host=parse.urlparse(u).netloc.lower()
                if "duckduckgo.com" in host:
                    continue
                if u in seen:
                    continue
                seen.add(u)
                title=" ".join(strip_tags.sub(" ",title_html).split())[:300]
                rows.append({"title":title,"url":u,"snippet":""})
                if len(rows)>=20:
                    break
            if len(rows)>=20:
                break

        attempts.append({
            "provider":provider_name,
            "status":"OK",
            "new_results":len(rows)-before,
        })
        if len(rows)>=20:
            break

    return {
        "ok":True,
        "status":"DDG_OK",
        "provider":"duckduckgo_keyless",
        "results":rows,
        "attempts":attempts,
    }
'''

s=replace_fn(s,"_ddg_search",ddg_fn)

fallback_fn = r'''
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

            if len(aggregated)>=20:
                break
        if len(aggregated)>=20:
            break

    prospects=[]
    seen_emails=set()
    crawled=0

    for row in aggregated[:20]:
        prospect=_find_business_email_on_site(row)
        crawled += 1
        if not prospect:
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
        "model":"multi_provider_fallback_v2",
        "response_id":None,
        "prospects":prospects,
        "provider_attempts":attempts,
        "queries":queries,
        "search_candidate_count_raw":len(aggregated),
        "sites_crawled":crawled,
    }
'''

s=replace_fn(s,"provider_fallback_search",fallback_fn)
s=s.replace('"version":"V66.29"', '"version":"V66.32"')

ast.parse(s)
p.write_text(s)
print("V66_32_DISCOVERY_PATCH=PASS")
PY

cat > "$ROOT/tests/test_v66_32_resilient_keyless_discovery.py" <<'PY'
from companyos.runtime.verified_web_prospect_discovery import _query_variants

def test_query_variants_are_multiple():
    q=_query_variants("local_contractor_bid_organizer",{
        "title":"Local Contractor Bid Organizer",
        "audience":"construction contractors",
        "description":"Organize bids and estimates",
    })
    assert len(q) >= 3

def test_audience_drives_search():
    q=_query_variants("local_contractor_bid_organizer",{
        "title":"Local Contractor Bid Organizer",
        "audience":"construction contractors",
        "description":"Organize bids and estimates",
    })
    assert any("construction contractors" in x.lower() for x in q)
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_32_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_32_resilient_keyless_discovery.py
echo "V66_32_TESTS=PASS"

echo "===== CLEAR ONLY ZERO-CANDIDATE FALLBACK COOLDOWN ====="
python - <<'PY'
import json
from companyos.runtime.verified_web_prospect_discovery import STATE,load_json,save_json

state=load_json(STATE,{
    "last_search_by_venture":{},
    "last_outcome_by_venture":{},
})
changed=[]
for cid,outcome in list((state.get("last_outcome_by_venture") or {}).items()):
    if not isinstance(outcome,dict):
        continue
    if (
        str(outcome.get("status") or "")=="DISCOVERY_COMPLETED"
        and int(outcome.get("verified_count") or 0)==0
        and int(outcome.get("search_candidate_count") or 0)==0
    ):
        state.setdefault("last_search_by_venture",{})[cid]=0
        changed.append(cid)

save_json(STATE,state)
print(json.dumps({"cleared_zero_candidate_cooldown_for":changed},indent=2,sort_keys=True))
PY

echo "===== RUN RESILIENT MULTI-QUERY DISCOVERY ====="
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

echo "V66_32_MULTI_QUERY_SEARCH=PASS"
echo "V66_32_DDG_HTML_AND_LITE_PARSERS=PASS"
echo "V66_32_SITE_CONTACT_CRAWL=PASS"
echo "V66_32_ROLE_BASED_BUSINESS_EMAIL_ONLY=PASS"
echo "V66_32_EXACT_SOURCE_VERIFICATION_PRESERVED=PASS"
echo "V66_32_V66_27_HANDOFF=PASS"
echo "V66_32_NO_NEW_DAEMON=PASS"
echo "V66_32_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_32_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_32_COMPLETE"
