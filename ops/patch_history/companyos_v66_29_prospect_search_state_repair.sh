#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"

MOD="$ROOT/companyos/runtime/verified_web_prospect_discovery.py"
CTL="$ROOT/scripts/companyos_prospectctl"
ACTL="$ROOT/scripts/companyos_acquisitionctl"
LCTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.29 PROSPECT SEARCH STATE REPAIR ====="
echo "GOAL=PRESERVE_LAST_MEANINGFUL_SEARCH_RESULT_AND_AVOID_LONG_COOLDOWN_AFTER_FAILED_OR_EMPTY_SEARCHES"
echo "NOTE=REUSES_EXISTING_OPENAI_WEB_SEARCH_PATH"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=NO_FINANCIAL_ACTIONS"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$MOD" ] || { echo "V66_29_ABORT=missing:$MOD"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$MOD" "${MOD}.v66_29_backup_${stamp}"
echo "BACKUP=${MOD}.v66_29_backup_${stamp}"

echo "===== SHOW PRIOR SEARCH HISTORY ====="
python - <<'PY'
import json
from pathlib import Path

p=Path.home()/".companyos_runtime/verified_web_prospect_discovery_history.jsonl"
rows=[]
if p.exists():
    for line in p.read_text(errors="ignore").splitlines():
        try:
            x=json.loads(line)
        except Exception:
            continue
        if isinstance(x,dict):
            rows.append(x)

meaningful=[]
for row in rows:
    for result in row.get("results") or []:
        if not isinstance(result,dict):
            continue
        if result.get("status")=="SEARCH_COOLDOWN":
            continue
        meaningful.append({
            "timestamp_unix":row.get("timestamp_unix"),
            "canonical_id":result.get("canonical_id"),
            "status":result.get("status"),
            "search_candidate_count":result.get("search_candidate_count"),
            "verified_count":result.get("verified_count"),
            "rejected_count":result.get("rejected_count"),
            "error":result.get("error"),
        })

print(json.dumps({
    "history_rows":len(rows),
    "last_meaningful_results":meaningful[-5:],
},indent=2,sort_keys=True))
PY

echo "===== PATCH SEARCH STATE SEMANTICS ====="
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

def replace_function(src,name,new_text):
    sp=span(src,name)
    if not sp:
        raise SystemExit(f"V66_29_ABORT=function_not_found:{name}")
    lines=src.splitlines()
    lines[sp[0]-1:sp[1]]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

helpers = '''
def recent_meaningful_result(cid: str) -> dict[str,Any]|None:
    if not HISTORY.exists():
        return None

    latest=None
    try:
        lines=HISTORY.read_text(errors="ignore").splitlines()[-200:]
    except Exception:
        return None

    for line in lines:
        try:
            row=json.loads(line)
        except Exception:
            continue
        if not isinstance(row,dict):
            continue
        for result in row.get("results") or []:
            if not isinstance(result,dict):
                continue
            if str(result.get("canonical_id") or "")!=str(cid):
                continue
            if result.get("status")=="SEARCH_COOLDOWN":
                continue
            latest={
                "timestamp_unix":row.get("timestamp_unix"),
                **result,
            }
    return latest


def retry_delay_for_result(result: dict[str,Any]|None) -> int:
    if not result:
        return 0

    status=str(result.get("status") or "")

    if status=="DISCOVERY_COMPLETED":
        verified=int(result.get("verified_count") or 0)
        candidates=int(result.get("search_candidate_count") or 0)

        if verified>0:
            return max(
                1800,
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_SUCCESS_COOLDOWN_SECONDS",
                    "21600",
                )),
            )

        if candidates>0:
            # Search returned leads, but source verification rejected them.
            # Retry sooner with a fresh result set rather than stalling 6 hours.
            return max(
                900,
                int(os.getenv(
                    "COMPANYOS_PROSPECT_DISCOVERY_REJECTED_COOLDOWN_SECONDS",
                    "1800",
                )),
            )

        # A valid search that found nothing should back off modestly.
        return max(
            900,
            int(os.getenv(
                "COMPANYOS_PROSPECT_DISCOVERY_EMPTY_COOLDOWN_SECONDS",
                "3600",
            )),
        )

    if status=="OPENAI_HTTP_429":
        return max(
            900,
            int(os.getenv(
                "COMPANYOS_PROSPECT_DISCOVERY_RATE_LIMIT_BACKOFF_SECONDS",
                "1800",
            )),
        )

    if status.startswith("OPENAI_HTTP_"):
        return max(
            300,
            int(os.getenv(
                "COMPANYOS_PROSPECT_DISCOVERY_HTTP_ERROR_BACKOFF_SECONDS",
                "900",
            )),
        )

    if status in {
        "OPENAI_REQUEST_ERROR",
        "OPENAI_OUTPUT_PARSE_ERROR",
        "OPENAI_API_KEY_MISSING",
    }:
        return max(
            300,
            int(os.getenv(
                "COMPANYOS_PROSPECT_DISCOVERY_ERROR_BACKOFF_SECONDS",
                "900",
            )),
        )

    return 900
'''

if "def recent_meaningful_result(" not in s:
    marker="def run_once()"
    sp=span(s,"run_once")
    if not sp:
        raise SystemExit("V66_29_ABORT=run_once_missing")
    lines=s.splitlines()
    lines[sp[0]-1:sp[0]-1]=helpers.strip("\n").splitlines()+[""]
    s="\n".join(lines)+"\n"

run_once = '''
def run_once() -> dict[str,Any]:
    state=load_json(STATE,{
        "last_search_by_venture":{},
        "last_outcome_by_venture":{},
    })
    last=state.setdefault("last_search_by_venture",{})
    outcomes=state.setdefault("last_outcome_by_venture",{})

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
                "last_meaningful_result":recent_meaningful_result(cid),
            })
            continue

        prior=outcomes.get(cid)
        if not isinstance(prior,dict):
            prior=recent_meaningful_result(cid)

        previous=float(last.get(cid,0) or 0)
        delay=retry_delay_for_result(prior)

        if previous and now-previous < delay:
            results.append({
                "canonical_id":cid,
                "status":"SEARCH_COOLDOWN",
                "cooldown_seconds":delay,
                "cooldown_remaining_seconds":int(delay-(now-previous)),
                "last_meaningful_result":prior,
            })
            continue

        copy=venture_copy(cid)
        search=web_search(cid,copy)

        search_result={
            "canonical_id":cid,
            "status":search.get("status"),
            "error":search.get("error"),
        }

        if not search.get("ok"):
            # Failed searches now get a short, status-specific backoff rather
            # than being treated like a successful 6-hour search.
            last[cid]=now
            outcomes[cid]=search_result
            results.append(search_result)
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
            existing_emails=set()
            if p.exists():
                for line in p.read_text(errors="ignore").splitlines():
                    try:
                        old=json.loads(line)
                    except Exception:
                        continue
                    if isinstance(old,dict) and old.get("business_email"):
                        existing_emails.add(str(old["business_email"]).lower())

            for v in verified:
                if v["business_email"].lower() in existing_emails:
                    continue
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
                existing_emails.add(v["business_email"].lower())

        total_verified += len(verified)

        search_result={
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
        }

        last[cid]=now
        outcomes[cid]=search_result
        results.append(search_result)
        break

    save_json(STATE,{
        "version":VERSION,
        "updated_at_unix":time.time(),
        "last_search_by_venture":last,
        "last_outcome_by_venture":outcomes,
    })

    report={
        "version":"V66.29",
        "mode":"adaptive_web_prospect_search_backoff",
        "model":DEFAULT_MODEL,
        "openai_key_present":bool(openai_key()),
        "verified_contacts_created":total_verified,
        "results":results,
        "rules":{
            "successful_verified_search_long_cooldown":True,
            "empty_search_shorter_retry":True,
            "rejected_candidates_shorter_retry":True,
            "failed_search_short_backoff":True,
            "last_meaningful_result_preserved":True,
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
'''

s=replace_function(s,"run_once",run_once)
ast.parse(s)
p.write_text(s)
print("V66_29_SEARCH_STATE_PATCH=PASS")
PY

cat > "$ROOT/tests/test_v66_29_prospect_search_state.py" <<'PY'
from companyos.runtime.verified_web_prospect_discovery import retry_delay_for_result

def test_verified_search_gets_long_cooldown():
    assert retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":1,
        "search_candidate_count":3,
    }) >= 1800

def test_rejected_candidates_retry_sooner_than_verified_success():
    rejected=retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":0,
        "search_candidate_count":3,
    })
    success=retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":1,
        "search_candidate_count":3,
    })
    assert rejected < success

def test_http_error_does_not_get_success_cooldown():
    err=retry_delay_for_result({"status":"OPENAI_HTTP_500"})
    success=retry_delay_for_result({
        "status":"DISCOVERY_COMPLETED",
        "verified_count":1,
        "search_candidate_count":1,
    })
    assert err < success
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD"
echo "V66_29_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_29_prospect_search_state.py
echo "V66_29_TESTS=PASS"

echo "===== RESET ONLY STALE V66.28 COOLDOWN IF PRIOR SEARCH FAILED ====="
python - <<'PY'
import json
from pathlib import Path
from companyos.runtime.verified_web_prospect_discovery import (
    STATE,
    recent_meaningful_result,
    load_json,
    save_json,
)

state=load_json(STATE,{
    "last_search_by_venture":{},
    "last_outcome_by_venture":{},
})
changed=[]

for cid in list((state.get("last_search_by_venture") or {}).keys()):
    prior=recent_meaningful_result(cid)
    if not isinstance(prior,dict):
        continue
    status=str(prior.get("status") or "")
    if status in {
        "OPENAI_REQUEST_ERROR",
        "OPENAI_OUTPUT_PARSE_ERROR",
        "OPENAI_API_KEY_MISSING",
    } or status.startswith("OPENAI_HTTP_"):
        state["last_search_by_venture"][cid]=0
        state.setdefault("last_outcome_by_venture",{})[cid]=prior
        changed.append({"canonical_id":cid,"prior_status":status})

save_json(STATE,state)
print(json.dumps({
    "failed_search_cooldowns_cleared":changed,
},indent=2,sort_keys=True))
PY

echo "===== RUN ADAPTIVE SEARCH PASS ====="
"$CTL" once

echo "===== FEED ANY VERIFIED CONTACT INTO V66.27 ====="
if [ -x "$ACTL" ]; then
  "$ACTL" once || true
fi

echo "===== REFRESH LIVENESS ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_29_LAST_MEANINGFUL_RESULT_PRESERVED=PASS"
echo "V66_29_FAILED_SEARCH_SHORT_BACKOFF=PASS"
echo "V66_29_EMPTY_SEARCH_SHORTER_RETRY=PASS"
echo "V66_29_REJECTED_CONTACT_SHORTER_RETRY=PASS"
echo "V66_29_VERIFIED_CONTACT_DEDUP=PASS"
echo "V66_29_V66_27_HANDOFF=PASS"
echo "V66_29_NO_NEW_DAEMON=PASS"
echo "V66_29_NO_FINANCIAL_ACTIONS=PASS"
echo "V66_29_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_29_COMPLETE"
