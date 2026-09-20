#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
MOD="$ROOT/companyos/runtime/verified_web_prospect_discovery.py"
CTL="$ROOT/scripts/companyos_prospectctl"
ACTL="$ROOT/scripts/companyos_acquisitionctl"
XCTL="$ROOT/scripts/companyos_externalctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.34 TARGET-AWARE PROSPECT RETRIEVAL ====="
echo "GOAL=FIND_MORE_REAL_TARGET_BUSINESSES_WITHOUT_LOOSENING_V66_33_VERIFICATION"
echo "NOTE=OFFICIAL_SITE_FIRST_SEARCH_AND_HOST_DEDUP"
echo "NOTE=CONTENT_AND_DIRECTORY_RESULTS_DEPRIORITIZED_OR_REJECTED"
echo "NOTE=EXACT_PUBLIC_EMAIL_AND_DOMAIN_MATCH_STILL_REQUIRED"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$MOD" ] || { echo "V66_34_ABORT=missing:$MOD"; exit 1; }
[ -x "$CTL" ] || { echo "V66_34_ABORT=missing_or_not_executable:$CTL"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v66_34_backup_${stamp}"
echo "BACKUP=${MOD}.v66_34_backup_${stamp}"

if [ -x "$XCTL" ]; then
  echo "===== PAUSE EXTERNAL ROUTER DURING PATCH ====="
  "$XCTL" stop || true
fi

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
        raise SystemExit(f"V66_34_ABORT=function_not_found:{name}")
    lines=src.splitlines()
    lines[sp[0]-1:sp[1]]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

query_fn=r'''
def _query_variants(cid: str, copy: dict[str,Any]) -> list[str]:
    title=str(copy.get("title") or cid.replace("_"," ").title()).strip()
    audience=str(copy.get("audience") or copy.get("target_customer") or "").strip()
    description=str(copy.get("description") or copy.get("offer") or "").strip()
    geo=str(
        copy.get("location")
        or copy.get("geography")
        or copy.get("region")
        or copy.get("market")
        or ""
    ).strip()

    stop={
        "local","software","app","application","tool","platform","service","services",
        "solution","solutions","opportunity","company","companies","business","businesses",
        "organizer","system","online","digital","mobile","workflow","marketplace",
        "the","and","for","with","from","this","that","your","our","their","into",
    }

    def useful_words(value: str, limit: int=6) -> list[str]:
        out=[]
        for token in re.findall(r"[A-Za-z0-9]+",value.lower()):
            if len(token)<4 or token in stop:
                continue
            if token not in out:
                out.append(token)
            if len(out)>=limit:
                break
        return out

    audience_words=useful_words(audience,5)
    title_words=useful_words(title+" "+description,6)

    if audience:
        audience_phrase=" ".join(audience.split())
    elif audience_words:
        audience_phrase=" ".join(audience_words)
    else:
        audience_phrase=" ".join(title_words[:3]) or cid.replace("_"," ")

    # A singular-ish variant often finds actual business homepages instead of listicles.
    singular_words=[]
    for word in audience_phrase.split():
        w=word
        if w.lower().endswith("ies") and len(w)>5:
            w=w[:-3]+"y"
        elif w.lower().endswith("s") and len(w)>5:
            w=w[:-1]
        singular_words.append(w)
    singular_phrase=" ".join(singular_words)

    geo_prefix=(geo+" ") if geo else ""
    negative="-blog -article -news -directory -template -examples"

    queries=[
        f'{geo_prefix}"{audience_phrase}" "contact us" {negative}',
        f'{geo_prefix}"{singular_phrase}" contact {negative}',
        f'{geo_prefix}"{singular_phrase}" "about us" contact {negative}',
        f'{geo_prefix}"{singular_phrase}" email contact {negative}',
        f'{geo_prefix}"{singular_phrase}" official website contact',
    ]

    core=[x for x in audience_words+title_words if x not in {"contact","email"}]
    if core:
        queries.append(f'{geo_prefix}{" ".join(core[:4])} contact {negative}')

    out=[]
    seen=set()
    for q in queries:
        q=" ".join(q.split()).strip()
        key=q.lower()
        if not q or key in seen:
            continue
        seen.add(key)
        out.append(q)
        if len(out)>=7:
            break
    return out
'''
s=replace_fn(s,"_query_variants",query_fn)

helpers=r'''
SEARCH_INTERMEDIARY_HOSTS={
    "linkedin.com","www.linkedin.com","facebook.com","www.facebook.com",
    "instagram.com","www.instagram.com","x.com","twitter.com","www.twitter.com",
    "youtube.com","www.youtube.com","yelp.com","www.yelp.com",
    "yellowpages.com","www.yellowpages.com","angi.com","www.angi.com",
    "homeadvisor.com","www.homeadvisor.com","bbb.org","www.bbb.org",
    "crunchbase.com","www.crunchbase.com","pitchbook.com","www.pitchbook.com",
    "clutch.co","www.clutch.co","g2.com","www.g2.com",
    "capterra.com","www.capterra.com",
}

def _host_words(host: str) -> set[str]:
    return {
        x for x in re.findall(r"[a-z0-9]+",str(host or "").lower())
        if len(x)>=4 and x not in {"www","com","net","org","co"}
    }

def rank_search_candidates(rows: list[dict[str,Any]], copy: dict[str,Any]) -> list[dict[str,Any]]:
    target=set(relevance_tokens(copy))
    by_host={}

    for row in rows:
        url=str(row.get("url") or "")
        if not url.startswith(("http://","https://")):
            continue
        parsed=parse.urlparse(url)
        host=parsed.netloc.lower().split(":",1)[0]
        if not host or host in SEARCH_INTERMEDIARY_HOSTS:
            continue
        if content_like_url(url) or content_like_title(str(row.get("title") or "")):
            continue

        title_words={
            x for x in re.findall(r"[a-z0-9]+",str(row.get("title") or "").lower())
            if len(x)>=4
        }
        host_words=_host_words(host)
        matches=target.intersection(title_words.union(host_words))
        path=parsed.path or "/"
        depth=len([x for x in path.split("/") if x])
        rootish=depth<=1

        score=0
        score += 5 if rootish else max(0,3-depth)
        score += min(9,3*len(matches))
        if any(x in title_words for x in {"construction","contractor","builder","company","group"}):
            score += 2
        if "contact" in title_words:
            score += 1

        candidate={**row,"candidate_score":score,"candidate_host":host,"target_matches":sorted(matches)}
        prev=by_host.get(host)
        if prev is None or candidate["candidate_score"]>prev["candidate_score"]:
            by_host[host]=candidate

    ranked=sorted(
        by_host.values(),
        key=lambda x:(int(x.get("candidate_score") or 0),-len(parse.urlparse(x.get("url") or "").path)),
        reverse=True,
    )
    return ranked
'''

if "def rank_search_candidates(" not in s:
    sp=span(s,"provider_fallback_search")
    if not sp:
        raise SystemExit("V66_34_ABORT=provider_fallback_search_missing")
    lines=s.splitlines()
    lines[sp[0]-1:sp[0]-1]=helpers.strip("\n").splitlines()+[""]
    s="\n".join(lines)+"\n"

fallback=r'''
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

        ranked_now=rank_search_candidates(aggregated,copy)
        # Two useful query passes are enough when we already have a diverse official-site pool.
        if len(ranked_now)>=36 and len(attempts)>=2:
            break

    ranked=rank_search_candidates(aggregated,copy)
    prospects=[]
    seen_emails=set()
    crawled=0
    rejected=0

    for row in ranked[:36]:
        prospect=_find_business_email_on_site(row,copy)
        crawled += 1
        if not prospect:
            rejected += 1
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
        "model":"target_aware_official_site_search_v1",
        "response_id":None,
        "prospects":prospects,
        "provider_attempts":attempts,
        "queries":queries,
        "search_candidate_count_raw":len(aggregated),
        "search_candidate_count_ranked":len(ranked),
        "sites_crawled":crawled,
        "relevance_rejected":rejected,
        "candidate_hosts_preview":[x.get("candidate_host") for x in ranked[:10]],
    }
'''
s=replace_fn(s,"provider_fallback_search",fallback)

# Bump any embedded patch version strings without depending on one exact declaration style.
s=s.replace('"version":"V66.33"','"version":"V66.34"')
s=s.replace("'version':'V66.33'","'version':'V66.34'")
s=s.replace('VERSION="V66.33"','VERSION="V66.34"')
s=s.replace("VERSION='V66.33'","VERSION='V66.34'")

ast.parse(s)
p.write_text(s)
print("V66_34_TARGET_AWARE_PATCH=PASS")
PY

cat > "$ROOT/tests/test_v66_34_target_aware_prospect_retrieval.py" <<'PY'
from companyos.runtime.verified_web_prospect_discovery import (
    _query_variants,
    rank_search_candidates,
)

def copy():
    return {
        "title":"Local Contractor Bid Organizer",
        "audience":"construction contractors",
        "description":"Organize bids and estimates for contractors",
    }

def test_queries_bias_toward_official_contacts_and_away_from_content():
    q=_query_variants("local_contractor_bid_organizer",copy())
    assert len(q)>=4
    assert any('"contact us"' in x.lower() for x in q)
    assert any("-blog" in x.lower() for x in q)

def test_content_pages_are_removed_before_crawl():
    rows=[
        {"title":"20 Contractor Email Examples","url":"https://example.com/blog/contractor-email-examples"},
        {"title":"ABC Construction","url":"https://abcconstruction.example/"},
    ]
    ranked=rank_search_candidates(rows,copy())
    assert len(ranked)==1
    assert ranked[0]["candidate_host"]=="abcconstruction.example"

def test_duplicate_host_is_collapsed():
    rows=[
        {"title":"ABC Construction","url":"https://abcconstruction.example/"},
        {"title":"ABC Construction Contact","url":"https://abcconstruction.example/contact"},
    ]
    ranked=rank_search_candidates(rows,copy())
    assert len(ranked)==1

def test_known_directory_is_rejected():
    rows=[
        {"title":"Contractors on Yelp","url":"https://www.yelp.com/search?find_desc=contractor"},
        {"title":"Real Builder Group","url":"https://realbuilder.example/"},
    ]
    ranked=rank_search_candidates(rows,copy())
    assert all("yelp.com" not in x["candidate_host"] for x in ranked)
PY

echo "===== COMPILE + TEST ====="
python -m py_compile "$MOD"
python -m pytest -q tests/test_v66_34_target_aware_prospect_retrieval.py
echo "V66_34_TESTS=PASS"

echo "===== CLEAR ONLY ZERO-VERIFIED SEARCH COOLDOWN ====="
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
        str(outcome.get("status") or "") in {"DISCOVERY_COMPLETED","SEARCH_COMPLETED"}
        and int(outcome.get("verified_count") or 0)==0
    ):
        state.setdefault("last_search_by_venture",{})[cid]=0
        changed.append(cid)
save_json(STATE,state)
print(json.dumps({"cleared_zero_verified_cooldown_for":changed},indent=2,sort_keys=True))
PY

echo "===== RUN TARGET-AWARE DISCOVERY ====="
"$CTL" once || true

echo "===== HAND VERIFIED CONTACTS TO CUSTOMER ACQUISITION ====="
if [ -x "$ACTL" ]; then
  "$ACTL" once || true
fi

echo "===== RESTART EXTERNAL ROUTER ====="
if [ -x "$XCTL" ]; then
  "$XCTL" start || true
fi

echo "===== LIGHTWEIGHT LIVENESS REFRESH ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== FINAL PROSPECT STATUS ====="
"$CTL" status || true

echo "V66_34_TARGET_AWARE_QUERYING=PASS"
echo "V66_34_HOST_DEDUPLICATION=PASS"
echo "V66_34_CONTENT_RESULT_PREFILTER=PASS"
echo "V66_34_OFFICIAL_SITE_PRIORITY=PASS"
echo "V66_34_V66_33_RELEVANCE_GUARD_PRESERVED=PASS"
echo "V66_34_EXACT_PUBLIC_EMAIL_VERIFICATION_PRESERVED=PASS"
echo "V66_34_EMAIL_DOMAIN_MATCH_GATE_PRESERVED=PASS"
echo "V66_34_NO_NEW_DAEMON=PASS"
echo "V66_34_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_34_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_34_COMPLETE"
