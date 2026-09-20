from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.procurement_intent_validator import is_sourcing_allowed
from companyos.runtime.procurement_evidence_verifier import verify_search_results
from companyos.runtime.procurement_requirement_specifier import specify as specify_procurement_requirement
from companyos.runtime.openai_web_search_adapter import configured as openai_web_configured, search as openai_web_search, cooldown_status as openai_web_cooldown_status
from companyos.runtime.tavily_keyless_adapter import configured as tavily_keyless_configured, search as tavily_keyless_search, state as tavily_keyless_state

HOME = Path.home()
ROOT = HOME / "companyos"
RT = HOME / ".companyos_runtime"
PRT = RT / "procurement"

SOURCING = PRT / "sourcing_requests.jsonl"
REQUIREMENTS = PRT / "requirements.jsonl"
EVIDENCE = PRT / "sourcing_evidence.jsonl"
RESOLUTIONS = PRT / "sourcing_resolutions.jsonl"
STATE = PRT / "sourcing_state.json"
LATEST = PRT / "sourcing_latest.json"
LOG = PRT / "sourcing_history.jsonl"

VERSION = "V66.05"
MAX_REQUESTS_PER_CYCLE = 12
MAX_RESULTS_PER_QUERY = 5
HTTP_TIMEOUT = 20

PRICE_RE = re.compile(r"(?<!\w)\$\s?([0-9]{1,7}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(errors="ignore").splitlines():
        try:
            x = json.loads(line)
            if isinstance(x, dict):
                out.append(x)
        except Exception:
            pass
    return out


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def load_json(path: Path, default: Any) -> Any:
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


def dotenv_values() -> dict[str, str]:
    p = ROOT / ".env"
    out: dict[str, str] = {}
    if not p.exists():
        return out
    for line in p.read_text(errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def env(name: str) -> str | None:
    v = os.environ.get(name)
    if v and v.strip():
        return v.strip()
    return dotenv_values().get(name)


def provider_status() -> dict[str, bool]:
    return {
        "tavily": bool(env("COMPANYOS_TAVILY_API_KEY") or env("TAVILY_API_KEY")),
        "tavily_keyless": bool(tavily_keyless_configured()),
        "brave": bool(env("COMPANYOS_BRAVE_SEARCH_API_KEY") or env("BRAVE_SEARCH_API_KEY")),
        "serper": bool(env("COMPANYOS_SERPER_API_KEY") or env("SERPER_API_KEY")),
        "openai_web": bool(openai_web_configured()),
    }


def chosen_provider() -> str | None:
    st = provider_status()
    # Keyed dedicated search remains first. Keyless Tavily is the preferred
    # bootstrap path before spending OpenAI request quota.
    for name in ("tavily", "brave", "serper", "tavily_keyless", "openai_web"):
        if st.get(name):
            if name=="tavily_keyless" and tavily_keyless_state().get("cooldown_active"):
                continue
            if name=="openai_web" and openai_web_cooldown_status().get("cooldown_active"):
                continue
            return name
    return None


def request_json(url: str, *, data: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    body = None
    hdr = {"User-Agent": "CompanyOS/66.05", "Accept": "application/json"}
    if headers:
        hdr.update(headers)
    if data is not None:
        body = json.dumps(data).encode()
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdr)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return json.loads(r.read().decode(errors="ignore"))


def search_tavily(query: str) -> list[dict[str, Any]]:
    key = env("COMPANYOS_TAVILY_API_KEY") or env("TAVILY_API_KEY")
    if not key:
        return []
    data = request_json(
        "https://api.tavily.com/search",
        data={
            "api_key": key,
            "query": query,
            "search_depth": "advanced",
            "max_results": MAX_RESULTS_PER_QUERY,
            "include_answer": False,
            "include_raw_content": False,
        },
    )
    out = []
    for x in data.get("results") or []:
        out.append({
            "title": x.get("title"),
            "url": x.get("url"),
            "snippet": x.get("content"),
            "score": x.get("score"),
            "provider": "tavily",
        })
    return out


def search_brave(query: str) -> list[dict[str, Any]]:
    key = env("COMPANYOS_BRAVE_SEARCH_API_KEY") or env("BRAVE_SEARCH_API_KEY")
    if not key:
        return []
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode({
        "q": query,
        "count": MAX_RESULTS_PER_QUERY,
        "safesearch": "moderate",
    })
    data = request_json(url, headers={"X-Subscription-Token": key})
    out = []
    for x in ((data.get("web") or {}).get("results") or []):
        out.append({
            "title": x.get("title"),
            "url": x.get("url"),
            "snippet": x.get("description"),
            "score": None,
            "provider": "brave",
        })
    return out


def search_serper(query: str) -> list[dict[str, Any]]:
    key = env("COMPANYOS_SERPER_API_KEY") or env("SERPER_API_KEY")
    if not key:
        return []
    data = request_json(
        "https://google.serper.dev/search",
        data={"q": query, "num": MAX_RESULTS_PER_QUERY},
        headers={"X-API-KEY": key},
    )
    out = []
    for x in data.get("organic") or []:
        out.append({
            "title": x.get("title"),
            "url": x.get("link"),
            "snippet": x.get("snippet"),
            "score": None,
            "provider": "serper",
        })
    return out


def search(query: str) -> tuple[str | None, list[dict[str, Any]], str | None]:
    p = chosen_provider()
    if not p:
        return None, [], "no_external_search_provider_configured"
    try:
        if p == "tavily":
            return p, search_tavily(query), None
        if p == "brave":
            return p, search_brave(query), None
        if p == "serper":
            return p, search_serper(query), None
        if p == "tavily_keyless":
            return p, tavily_keyless_search(query, MAX_RESULTS_PER_QUERY), None
        if p == "openai_web":
            return p, openai_web_search(query, MAX_RESULTS_PER_QUERY), None
        return p, [], "unknown_search_provider"
    except Exception as exc:
        return p, [], f"{type(exc).__name__}:{exc}"


def domain_name(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return None


def price_candidates(*texts: str | None) -> list[float]:
    vals = []
    for text in texts:
        if not text:
            continue
        for m in PRICE_RE.finditer(html.unescape(str(text))):
            try:
                vals.append(float(m.group(1).replace(",", "")))
            except Exception:
                pass
    return vals


def requirements_index() -> list[dict[str, Any]]:
    return read_jsonl(REQUIREMENTS)


def enrich_request(sr: dict[str, Any]) -> dict[str, Any]:
    best = None
    for req in reversed(requirements_index()):
        if req.get("venture_id") != sr.get("venture_id"):
            continue
        if req.get("category") != sr.get("category"):
            continue
        if str(req.get("item")) != str(sr.get("item")):
            continue
        best = req
        break

    merged = dict(sr)
    if best:
        merged["known_expected_profit_usd"] = best.get("expected_profit_usd")
        merged["known_probability"] = best.get("probability_estimate")
        merged["known_evidence_count"] = best.get("evidence_count")
        merged["known_vendor"] = merged.get("known_vendor") or best.get("vendor")
        merged["known_price_usd"] = (
            merged.get("known_price_usd")
            if merged.get("known_price_usd") is not None
            else best.get("price_usd")
        )
        merged["known_amount_sol"] = (
            merged.get("known_amount_sol")
            if merged.get("known_amount_sol") is not None
            else best.get("amount_sol")
        )
        merged["known_payment_destination"] = (
            merged.get("known_payment_destination") or best.get("recipient")
        )
    specificity=specify_procurement_requirement(merged)
    merged["procurement_specificity"]=specificity
    merged["requirement_specific"]=bool(specificity.get("requirement_specific"))
    merged["specific_item"]=specificity.get("specific_item")
    return merged


def build_query(sr: dict[str, Any]) -> str:
    item = str(sr.get("specific_item") or sr.get("item") or "").strip()
    category = str(sr.get("category") or "").strip()
    vendor = str(sr.get("known_vendor") or "").strip()
    missing = set(sr.get("missing_fields") or [])

    if vendor and "price" in missing:
        return f"{vendor} {item} official pricing current price"

    if category == "domain":
        return f"official domain registrar pricing {item} purchase"

    if category == "hosting":
        return f"official hosting provider pricing {item}"

    if category == "inventory_product":
        return f"{item} supplier wholesale official price"

    if category == "software_api":
        return f"{item} official pricing API subscription"

    if category == "contractor_service":
        return f"{item} provider pricing quote"

    if category == "materials_equipment":
        return f"{item} supplier rental purchase price"

    if category == "advertising":
        return f"{item} official advertising pricing"

    return f"{item} official vendor pricing"


def enqueue_research_task(sr: dict[str, Any], query: str) -> dict[str, Any]:
    q = AutonomousTaskQueue()
    sid = str(sr.get("sourcing_request_id") or sr.get("venture_id") or "unknown")
    task = q.enqueue(
        task_type="research",
        priority=96,
        max_attempts=3,
        idempotency_key=f"procurement-sourcing:{sid}",
        payload={
            "topic": query,
            "objective": "Find real vendor/provider, current price, and source evidence for procurement.",
            "query": query,
            "venture_id": sr.get("venture_id"),
            "procurement_category": sr.get("category"),
            "procurement_item": sr.get("item"),
            "missing_fields": sr.get("missing_fields") or [],
            "constraints": [
                "do not fabricate vendor",
                "do not fabricate price",
                "do not fabricate payment destination",
                "payment destination must come from verified checkout/invoice/provider data",
            ],
            "stage": "research",
        },
    )
    return {
        "task_id": task.task_id,
        "state": task.state,
        "idempotency_key": task.idempotency_key,
    }


def resolve_one(sr: dict[str, Any]) -> dict[str, Any]:
    sr = enrich_request(sr)

    if not sr.get("requirement_specific"):
        query = build_query(sr)
        research_task = None
        try:
            research_task = enqueue_research_task(
                {
                    **sr,
                    "item": str(sr.get("item") or ""),
                    "missing_fields": list(sr.get("missing_fields") or []) + ["specific_procurement_purpose"],
                },
                (
                    "Determine the concrete procurement purpose for venture "
                    + str(sr.get("venture_id") or "")
                    + " before vendor selection. Identify the exact capability, "
                      "data, service, material, domain use, hosting need, inventory "
                      "need, or advertising objective required by the venture."
                ),
            )
        except Exception as exc:
            research_task={"error":f"{type(exc).__name__}:{exc}"}

        resolution={
            "schema":"companyos.procurement_sourcing_resolution.v1",
            "timestamp_unix":time.time(),
            "sourcing_request_id":sr.get("sourcing_request_id"),
            "venture_id":sr.get("venture_id"),
            "category":sr.get("category"),
            "item":sr.get("item"),
            "specific_item":None,
            "query":query,
            "search_provider":None,
            "search_error":None,
            "result_count":0,
            "candidate_vendor":None,
            "candidate_price_usd":None,
            "candidate_source_url":None,
            "official_vendor_verified":False,
            "official_price_verified":False,
            "verified_provider_count":0,
            "provider_comparison":[],
            "provider_comparison_satisfied":False,
            "rejected_evidence":[],
            "known_amount_sol":sr.get("known_amount_sol"),
            "known_payment_destination":sr.get("known_payment_destination"),
            "known_expected_profit_usd":sr.get("known_expected_profit_usd"),
            "known_probability":sr.get("known_probability"),
            "known_evidence_count":sr.get("known_evidence_count"),
            "remaining_missing_fields":list(sr.get("missing_fields") or []) + ["specific_procurement_purpose"],
            "status":"REQUIREMENT_SPECIFICATION_REQUIRED",
            "requirement_provenance_verified":False,
            "research_task":research_task,
            "procurement_specificity":sr.get("procurement_specificity"),
            "auto_payment_destination_extraction":False,
            "ready_for_capital_intent":False,
        }
        append_jsonl(RESOLUTIONS,resolution)
        return resolution

    query = build_query(sr)
    provider, results, error = search(query)

    research_task = None
    if not results:
        try:
            research_task = enqueue_research_task(sr, query)
        except Exception as exc:
            research_task = {"error": f"{type(exc).__name__}:{exc}"}

    evidence_rows = []
    for rank, r in enumerate(results, 1):
        prices = price_candidates(r.get("title"), r.get("snippet"))
        er = {
            "schema": "companyos.procurement_sourcing_evidence.v1",
            "timestamp_unix": time.time(),
            "sourcing_request_id": sr.get("sourcing_request_id"),
            "venture_id": sr.get("venture_id"),
            "query": query,
            "provider": provider,
            "rank": rank,
            "title": r.get("title"),
            "url": r.get("url"),
            "domain": domain_name(r.get("url")),
            "snippet": r.get("snippet"),
            "provider_score": r.get("score"),
            "observed_price_candidates_usd": prices,
            "verified_vendor": False,
            "verified_price": False,
            "verified_payment_destination": False,
        }
        append_jsonl(EVIDENCE, er)
        evidence_rows.append(er)

    # Search results are leads only. V66.10 fetches the source page and
    # verifies that vendor identity + price belong to a real commercial page.
    official_verification = verify_search_results(
        evidence_rows,
        item=str(sr.get("specific_item") or sr.get("item") or ""),
        category=str(sr.get("category") or "general_procurement"),
        known_vendor=sr.get("known_vendor"),
    )

    chosen = official_verification.get("chosen") or {}
    candidate_vendor = chosen.get("final_domain")
    candidate_price = chosen.get("verified_price_usd")
    candidate_url = chosen.get("final_url")

    missing = list(sr.get("missing_fields") or [])

    if sr.get("known_vendor") or candidate_vendor:
        missing = [x for x in missing if x != "vendor"]

    if (
        sr.get("known_price_usd") is not None
        or sr.get("known_amount_sol") is not None
        or candidate_price is not None
    ):
        missing = [x for x in missing if x != "price"]

    if sr.get("known_expected_profit_usd") is not None:
        missing = [x for x in missing if x != "expected_profit_usd"]

    if sr.get("known_probability") is not None:
        missing = [x for x in missing if x != "probability"]

    if sr.get("known_evidence_count") is not None:
        missing = [x for x in missing if x != "evidence_count"]

    if sr.get("known_payment_destination"):
        missing = [x for x in missing if x != "payment_destination"]

    official_ready = bool(
        official_verification.get("comparison_satisfied")
        and candidate_vendor
        and candidate_price is not None
    )

    if not evidence_rows:
        status = "EXTERNAL_PROVIDER_REQUIRED"
    elif not official_ready:
        status = "OFFICIAL_VENDOR_EVIDENCE_REQUIRED"
    elif any(x in missing for x in ("expected_profit_usd","probability","evidence_count")):
        status = "ECONOMICS_EVIDENCE_REQUIRED"
    elif "payment_destination" in missing:
        status = "CHECKOUT_OR_INVOICE_REQUIRED"
    elif not missing:
        status = "PROCUREMENT_EVIDENCE_COMPLETE"
    else:
        status = "SOURCING_REQUIRED"

    resolution = {
        "schema": "companyos.procurement_sourcing_resolution.v1",
        "timestamp_unix": time.time(),
        "sourcing_request_id": sr.get("sourcing_request_id"),
        "venture_id": sr.get("venture_id"),
        "category": sr.get("category"),
        "item": sr.get("item"),
        "specific_item": sr.get("specific_item"),
        "procurement_specificity": sr.get("procurement_specificity"),
        "requirement_provenance_verified": bool(
            (sr.get("procurement_specificity") or {}).get("provenance_verified", False)
            or (sr.get("procurement_specificity") or {}).get("source")=="existing_explicit_requirement"
        ),
        "query": query,
        "search_provider": provider,
        "search_error": error,
        "result_count": len(evidence_rows),
        "candidate_vendor": sr.get("known_vendor") or candidate_vendor,
        "candidate_price_usd": (
            sr.get("known_price_usd")
            if sr.get("known_price_usd") is not None
            else candidate_price
        ),
        "candidate_source_url": candidate_url,
        "official_vendor_verified": bool(candidate_vendor),
        "official_price_verified": candidate_price is not None,
        "verified_provider_count": official_verification.get("verified_provider_count", 0),
        "provider_comparison": official_verification.get("providers", []),
        "provider_comparison_satisfied": official_verification.get("comparison_satisfied", False),
        "rejected_evidence": official_verification.get("rejected", []),
        "known_amount_sol": sr.get("known_amount_sol"),
        "known_payment_destination": sr.get("known_payment_destination"),
        "known_expected_profit_usd": sr.get("known_expected_profit_usd"),
        "known_probability": sr.get("known_probability"),
        "known_evidence_count": sr.get("known_evidence_count"),
        "remaining_missing_fields": missing,
        "status": status,
        "research_task": research_task,
        "auto_payment_destination_extraction": False,
        "ready_for_capital_intent": False,
    }
    append_jsonl(RESOLUTIONS, resolution)
    return resolution


def processed_ids() -> set[str]:
    # A request that previously failed only because no external search
    # provider existed is NOT terminal. Once a provider becomes available,
    # it must re-enter the sourcing queue automatically.
    terminal={"SEARCH_EVIDENCE_FOUND","CHECKOUT_OR_INVOICE_REQUIRED"}
    return {
        str(x.get("sourcing_request_id"))
        for x in read_jsonl(RESOLUTIONS)
        if x.get("sourcing_request_id")
        and str(x.get("status") or "") in terminal
    }


def pending_requests() -> list[dict[str, Any]]:
    done = processed_ids()
    latest = {}
    for x in read_jsonl(SOURCING):
        sid = x.get("sourcing_request_id")
        if sid:
            latest[str(sid)] = x
    return [
        x for sid, x in latest.items()
        if sid not in done
        and str(x.get("status") or "OPEN").upper() == "OPEN"
        and is_sourcing_allowed(x)
    ]


def run_once(max_requests: int = MAX_REQUESTS_PER_CYCLE) -> dict[str, Any]:
    pending = pending_requests()
    provider=chosen_provider()

    # The OpenAI web fallback is deliberately paced one uncached research
    # request at a time. This prevents a batch of procurement requests from
    # consuming the entire request window and producing a 429 storm.
    effective_max=max(1,int(max_requests))
    if provider=="openai_web":
        cd=openai_web_cooldown_status()
        if cd.get("cooldown_active"):
            selected=[]
        else:
            effective_max=1
            selected=pending[:1]
    elif provider=="tavily_keyless":
        cd=tavily_keyless_state()
        if cd.get("cooldown_active"):
            selected=[]
        else:
            effective_max=1
            selected=pending[:1]
    else:
        selected=pending[:effective_max]

    resolutions=[]
    for item in selected:
        row=resolve_one(item)
        resolutions.append(row)
        err=str(row.get("search_error") or "")
        if "rate_limited" in err or "HTTP Error 429" in err:
            break

    report = {
        "version": VERSION,
        "mode": "live_external_sourcing",
        "provider_status": provider_status(),
        "selected_provider": chosen_provider(),
        "openai_web_rate_state": openai_web_cooldown_status() if provider_status().get("openai_web") else None,
        "tavily_keyless_state": tavily_keyless_state() if provider_status().get("tavily_keyless") else None,
        "pending_before": len(pending),
        "processed": len(resolutions),
        "search_evidence_found": sum(1 for x in resolutions if x["result_count"] > 0),
        "checkout_or_invoice_required": sum(
            1 for x in resolutions if x["status"] == "CHECKOUT_OR_INVOICE_REQUIRED"
        ),
        "external_provider_required": sum(
            1 for x in resolutions if x["status"] == "EXTERNAL_PROVIDER_REQUIRED"
        ),
        "research_tasks_created_or_reused": sum(
            1 for x in resolutions if x.get("research_task")
        ),
        "capital_intents_created": 0,
        "payment_destinations_scraped": 0,
        "resolutions": resolutions,
    }
    save_json(LATEST, report)
    append_jsonl(LOG, {"timestamp_unix": time.time(), **report})

    st = load_json(STATE, {})
    st.update({
        "version": VERSION,
        "updated_at_unix": time.time(),
        "last_report": report,
    })
    save_json(STATE, st)
    return report


def status() -> dict[str, Any]:
    return {
        "version": VERSION,
        "provider_status": provider_status(),
        "selected_provider": chosen_provider(),
        "pending_requests": len(pending_requests()),
        "latest": load_json(LATEST, {}),
        "state": load_json(STATE, {}),
        "evidence_file": str(EVIDENCE),
        "resolutions_file": str(RESOLUTIONS),
    }


def loop(interval: int):
    while True:
        try:
            r = run_once()
            print(json.dumps({
                "ts": time.time(),
                "provider": r["selected_provider"],
                "processed": r["processed"],
                "search_evidence_found": r["search_evidence_found"],
                "external_provider_required": r["external_provider_required"],
            }, sort_keys=True), flush=True)
        except Exception as exc:
            print(json.dumps({
                "ts": time.time(),
                "error": f"{type(exc).__name__}:{exc}",
            }, sort_keys=True), flush=True)
        time.sleep(max(60, int(interval)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p = sub.add_parser("once")
    p.add_argument("--max-requests", type=int, default=MAX_REQUESTS_PER_CYCLE)
    lp = sub.add_parser("loop")
    lp.add_argument("--interval", type=int, default=300)
    args = ap.parse_args()

    if args.cmd == "status":
        print(json.dumps(status(), indent=2, sort_keys=True, default=str))
    elif args.cmd == "once":
        print(json.dumps(run_once(args.max_requests), indent=2, sort_keys=True, default=str))
    elif args.cmd == "loop":
        loop(args.interval)


if __name__ == "__main__":
    main()
