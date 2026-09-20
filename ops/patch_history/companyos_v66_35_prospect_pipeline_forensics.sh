#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p "$RT"

echo "===== COMPANYOS V66.35 PROSPECT PIPELINE FORENSICS ====="
echo "GOAL=FIND_EXACT_STAGE_CAUSING_ZERO_VERIFIED_CONTACTS_WITHOUT_LOOSENING_GATES"
echo "NOTE=READ_ONLY_CORE_CODE"
echo "NOTE=PUBLIC_WEB_GETS_ONLY"
echo "NOTE=NO_EMAIL_SEND"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

python - <<'PY'
import json, time
from pathlib import Path
from urllib import parse

from companyos.runtime import verified_web_prospect_discovery as d
try:
    from companyos.runtime.customer_acquisition_bridge import venture_copy
except Exception:
    venture_copy=None

RT=Path.home()/".companyos_runtime"

# Prefer a venture already known to the prospect-discovery state. Fall back to the
# customer-acquisition venture that V66.28-V66.34 have been exercising.
state={}
try:
    state=d.load_json(d.STATE,{})
except Exception:
    pass
known=[]
for bucket in ("last_outcome_by_venture","last_search_by_venture"):
    x=state.get(bucket) if isinstance(state,dict) else None
    if isinstance(x,dict):
        for k in x:
            if k not in known:
                known.append(k)

fallback="local_contractor_bid_organizer"
cid=known[0] if known else fallback

copy={}
if callable(venture_copy):
    try:
        copy=venture_copy(cid) or {}
    except Exception:
        copy={}
if not copy and cid!=fallback and callable(venture_copy):
    try:
        alt=venture_copy(fallback) or {}
        if alt:
            cid=fallback; copy=alt
    except Exception:
        pass
if not copy:
    copy={
        "title":"Local Contractor Bid Organizer",
        "audience":"construction contractors",
        "description":"Organize contractor bids and estimates",
    }

queries=d._query_variants(cid,copy)
query_rows=[]
aggregated=[]
seen=set()

for q in queries[:6]:
    try:
        r=d._ddg_search(q)
    except Exception as exc:
        r={"ok":False,"status":f"EXCEPTION:{type(exc).__name__}","results":[],"attempts":[]}
    rows=r.get("results") or []
    query_rows.append({
        "query":q,
        "ok":bool(r.get("ok")),
        "status":r.get("status"),
        "result_count":len(rows),
        "attempts":r.get("attempts") or [],
    })
    for row in rows:
        u=str(row.get("url") or "")
        if not u or u in seen:
            continue
        seen.add(u); aggregated.append(row)

try:
    ranked=d.rank_search_candidates(aggregated,copy)
except Exception as exc:
    ranked=[]
    rank_exception=f"{type(exc).__name__}: {exc}"
else:
    rank_exception=None

candidate_rows=[]
counts={
    "candidate_checked":0,
    "root_fetch_failed":0,
    "relevance_failed":0,
    "no_prospect_found":0,
    "prospect_found":0,
    "verify_rejected":0,
    "verified":0,
}

for row in ranked[:15]:
    counts["candidate_checked"]+=1
    url=str(row.get("url") or "")
    p=parse.urlparse(url)
    root=f"{p.scheme}://{p.netloc}/" if p.scheme and p.netloc else url
    rec={
        "host":p.netloc,
        "title":str(row.get("title") or "")[:180],
        "url":url,
        "candidate_score":row.get("candidate_score"),
        "target_matches":row.get("target_matches") or [],
    }

    try:
        home=d.fetch_source(root)
    except Exception as exc:
        home={"ok":False,"status":f"EXCEPTION:{type(exc).__name__}"}
    rec["root_fetch_status"]=home.get("status")
    if not home.get("ok"):
        counts["root_fetch_failed"]+=1
        rec["pipeline_result"]="root_fetch_failed"
        candidate_rows.append(rec)
        continue

    try:
        rel=d.page_relevance(home.get("text") or "",copy)
    except Exception as exc:
        rel={"ok":False,"tokens":[],"matched":[],"error":f"{type(exc).__name__}: {exc}"}
    rec["relevance_tokens"]=rel.get("tokens") or []
    rec["matched_relevance_tokens"]=rel.get("matched") or []
    if not rel.get("ok"):
        counts["relevance_failed"]+=1
        rec["pipeline_result"]="relevance_failed"
        candidate_rows.append(rec)
        continue

    try:
        prospect=d._find_business_email_on_site(row,copy)
    except Exception as exc:
        prospect=None
        rec["prospect_exception"]=f"{type(exc).__name__}: {exc}"

    if not prospect:
        counts["no_prospect_found"]+=1
        rec["pipeline_result"]="no_public_role_email_found_or_domain_match_failed"
        candidate_rows.append(rec)
        continue

    counts["prospect_found"]+=1
    rec["prospect_email_domain"]=(str(prospect.get("public_business_email") or "").split("@",1)[-1])
    rec["prospect_source_url"]=prospect.get("source_url")
    try:
        verified=d.verify_prospect(prospect,copy)
    except TypeError:
        verified=d.verify_prospect(prospect)
    except Exception as exc:
        verified={"ok":False,"reasons":[f"verify_exception:{type(exc).__name__}"]}
    rec["verify_ok"]=bool(verified.get("ok"))
    rec["verify_reasons"]=verified.get("reasons") or []
    if verified.get("ok"):
        counts["verified"]+=1
        rec["pipeline_result"]="verified"
    else:
        counts["verify_rejected"]+=1
        rec["pipeline_result"]="verify_rejected"
    candidate_rows.append(rec)

# Diagnose the dominant bottleneck without changing any gate.
if not aggregated:
    diagnosis="SEARCH_PROVIDER_RETURNED_ZERO_RESULTS"
elif not ranked:
    diagnosis="ALL_SEARCH_RESULTS_REMOVED_BY_PREFILTER_OR_RANKING"
elif counts["root_fetch_failed"] >= max(1,counts["candidate_checked"]//2):
    diagnosis="OFFICIAL_SITE_FETCH_FAILURE_DOMINANT"
elif counts["relevance_failed"] >= max(1,counts["candidate_checked"]//2):
    diagnosis="RELEVANCE_GATE_DOMINANT"
elif counts["no_prospect_found"] >= max(1,counts["candidate_checked"]//2):
    diagnosis="PUBLIC_BUSINESS_EMAIL_DISCOVERY_DOMINANT"
elif counts["verify_rejected"] and counts["verified"]==0:
    diagnosis="FINAL_VERIFICATION_GATE_DOMINANT"
elif counts["verified"]:
    diagnosis="PIPELINE_CAN_VERIFY_CONTACTS"
else:
    diagnosis="MIXED_OR_INCONCLUSIVE"

report={
    "version":"V66.35",
    "mode":"read_only_prospect_pipeline_forensics",
    "venture_id":cid,
    "venture_copy":{
        "title":copy.get("title"),
        "audience":copy.get("audience") or copy.get("target_customer"),
        "description":copy.get("description") or copy.get("offer"),
    },
    "query_count":len(queries[:6]),
    "queries":query_rows,
    "raw_unique_search_results":len(aggregated),
    "ranked_candidate_count":len(ranked),
    "rank_exception":rank_exception,
    "counts":counts,
    "diagnosis":diagnosis,
    "candidate_examples":candidate_rows,
    "rules":{
        "core_code_changed":False,
        "verification_loosened":False,
        "emails_sent":False,
        "financial_actions":False,
        "authority_switches_changed":False,
    },
    "timestamp_unix":time.time(),
}

out=RT/"v66_35_prospect_pipeline_forensics_latest.json"
out.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
print(json.dumps(report,indent=2,sort_keys=True,default=str))
print(f"REPORT={out}")
print(f"V66_35_DIAGNOSIS={diagnosis}")
print("V66_35_CORE_CODE_UNCHANGED=PASS")
print("V66_35_VERIFICATION_GATES_UNCHANGED=PASS")
print("V66_35_NO_EMAIL_SEND=PASS")
print("V66_35_NO_FINANCIAL_ACTIONS=PASS")
print("V66_35_AUTHORITY_SWITCHES_UNCHANGED=PASS")
print("V66_35_COMPLETE")
PY
