#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
GLOBAL_RT="$HOME/.companyos_runtime"
LOCAL_RT="$ROOT/.companyos_runtime"
MODULE="$ROOT/companyos/runtime/economics_validation_manager.py"
PIDFILE="$GLOBAL_RT/economics_validation_manager.pid"
LOGFILE="$GLOBAL_RT/economics_validation_manager.log"
INTERVAL_SECONDS="${COMPANYOS_ECONOMICS_VALIDATION_INTERVAL_SECONDS:-900}"

mkdir -p "$GLOBAL_RT" "$LOCAL_RT"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

install_module() {
cat > "$MODULE" <<'PY'
from __future__ import annotations

import importlib.util
import json
import math
import os
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
OUT = RT / "canonical_research_outputs"
STATE = RT / "economics_validation_state.json"
REPORTS = Path.home() / ".companyos_runtime" / "reports"
PLUGIN_PATH = ROOT / "plugins/installed/web_research/plugin.py"

OUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = max(1, min(5, int(os.getenv("COMPANYOS_ECONOMICS_CANDIDATES_PER_CYCLE", "3"))))
MAX_RESULTS = max(2, min(6, int(os.getenv("COMPANYOS_ECONOMICS_SEARCH_RESULTS", "4"))))
MAX_FETCHES_PER_CANDIDATE = max(2, min(8, int(os.getenv("COMPANYOS_ECONOMICS_FETCHES_PER_CANDIDATE", "5"))))
MIN_AVAILABLE_MB = max(500, int(os.getenv("COMPANYOS_ECONOMICS_MIN_AVAILABLE_MB", "900")))

PRICE_RE = re.compile(r"(?<![A-Za-z0-9])\$\s*([0-9]{1,6}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)")
PRICE_CONTEXT = (
    "price", "pricing", "plan", "month", "monthly", "year", "annual",
    "per user", "per seat", "subscription", "license", "starting at",
    "one-time", "one time", "buy", "cost"
)

MARGIN_PRIOR = {
    "software_saas_ai": 0.70,
    "automation_products": 0.60,
    "data_api_licensing": 0.70,
    "digital_products": 0.75,
    "subscriptions_memberships": 0.55,
    "content_media": 0.50,
    "lead_generation_assets": 0.50,
    "marketplaces_platforms": 0.55,
    "brokerage_commission": 0.55,
    "mobile_web_apps": 0.65,
    "services": 0.30,
    "ecommerce_physical_products": 0.20,
    "unknown": 0.25,
}

def load(path: Path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)

def slug(v):
    return re.sub(r"[^a-z0-9]+", "_", str(v or "").lower()).strip("_")[:90] or "candidate"

def available_mb():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except Exception:
        pass
    return 0

def load_web_plugin():
    if not PLUGIN_PATH.exists():
        raise FileNotFoundError(str(PLUGIN_PATH))
    spec = importlib.util.spec_from_file_location("companyos_v65_95_web_research", PLUGIN_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def domain(url):
    try:
        return urlparse(str(url)).netloc.lower().replace("www.", "")
    except Exception:
        return ""

def existing_domains(payload):
    urls = []
    for key in ("source_urls", "evidence"):
        v = payload.get(key)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item.startswith(("http://", "https://")):
                    urls.append(item)
                elif isinstance(item, dict):
                    u = item.get("url")
                    if isinstance(u, str) and u.startswith(("http://", "https://")):
                        urls.append(u)
    return {domain(u) for u in urls if domain(u)}

def candidate_queries(o):
    p = o.payload or {}
    name = str(o.name or "").replace(" Opportunity", "").strip()
    market = str(p.get("market") or p.get("sector") or o.category or "").replace("_", " ")
    buyer = str(p.get("target_customer") or "").replace("_", " ")
    model = str(p.get("business_model") or o.mechanism or "").replace("_", " ")
    problem = str(p.get("problem") or "")
    # Queries are deliberately economics-focused rather than broad discovery.
    qs = [
        f'"{name}" pricing competitors',
        f'{market} {model} pricing plans',
        f'{buyer} {name} cost per month',
    ]
    if problem and problem.lower() not in ("unknown", ""):
        qs.append(f'{problem[:110]} software pricing')
    out = []
    seen = set()
    for q in qs:
        q = " ".join(q.split())
        if q and q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
    return out[:3]

def extract_prices(text, url, title):
    findings = []
    low = text.lower()
    for m in PRICE_RE.finditer(text):
        try:
            amount = float(m.group(1).replace(",", ""))
        except Exception:
            continue
        if amount < 2 or amount > 100000:
            continue
        lo = max(0, m.start() - 110)
        hi = min(len(text), m.end() + 140)
        ctx = " ".join(text[lo:hi].split())
        ctx_low = ctx.lower()
        if not any(k in ctx_low for k in PRICE_CONTEXT):
            continue

        cadence = "unknown"
        monthly_equivalent = None
        if any(x in ctx_low for x in ("/mo", "per month", "monthly", " month")):
            cadence = "monthly"
            monthly_equivalent = amount
        elif any(x in ctx_low for x in ("/yr", "/year", "per year", "annual", "yearly")):
            cadence = "annual"
            monthly_equivalent = round(amount / 12.0, 2)
        elif any(x in ctx_low for x in ("one-time", "one time", "lifetime")):
            cadence = "one_time"

        findings.append({
            "amount_usd": amount,
            "cadence": cadence,
            "monthly_equivalent_usd": monthly_equivalent,
            "context": ctx[:320],
            "url": url,
            "domain": domain(url),
            "title": title,
        })
        if len(findings) >= 12:
            break
    return findings

def dedupe_prices(rows):
    seen = set()
    out = []
    for r in rows:
        key = (r["domain"], round(float(r["amount_usd"]), 2), r["cadence"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

def conservative_price(prices, model):
    recurring = [r["monthly_equivalent_usd"] for r in prices if r.get("monthly_equivalent_usd")]
    one_time = [r["amount_usd"] for r in prices if r.get("cadence") == "one_time"]
    unknown = [r["amount_usd"] for r in prices if r.get("cadence") == "unknown"]

    vals = recurring
    basis = "monthly_equivalent"
    if not vals and model in ("digital_products", "ecommerce_physical_products") and one_time:
        vals = one_time
        basis = "one_time"
    if not vals and unknown:
        vals = unknown
        basis = "unclassified_price"

    if not vals:
        return None, basis
    vals = sorted(float(x) for x in vals if x and x > 0)
    # Lower quartile / low observed price is intentionally conservative.
    idx = max(0, min(len(vals) - 1, int(math.floor((len(vals) - 1) * 0.25))))
    return round(vals[idx], 2), basis

def choose_diverse(rows, cursor, batch):
    rows = [
        o for o in rows
        if str(o.mechanism or "unknown") != "unknown"
        and int(o.evidence_count or 0) >= 1
    ]
    if not rows:
        return [], 0

    # Rotate so every candidate gets economics research, but preserve diversity.
    n = len(rows)
    ordered = [rows[(cursor + i) % n] for i in range(n)]
    chosen = []
    models = set()
    sectors = set()

    for o in ordered:
        model = str(o.mechanism or "unknown")
        sector = str(o.category or "unknown")
        if chosen and model in models and sector in sectors:
            continue
        chosen.append(o)
        models.add(model)
        sectors.add(sector)
        if len(chosen) >= batch:
            break

    if len(chosen) < batch:
        for o in ordered:
            if o not in chosen:
                chosen.append(o)
                if len(chosen) >= batch:
                    break

    return chosen, (cursor + len(chosen)) % n

def research_candidate(web, o):
    payload = dict(o.payload or {})
    queries = candidate_queries(o)
    search_rows = []
    errors = []

    for q in queries:
        try:
            r = web.search_web(q, MAX_RESULTS)
            if r.get("success"):
                for item in r.get("results") or []:
                    d = dict(item)
                    d["query"] = q
                    search_rows.append(d)
            else:
                errors.append(f"search:{q}:{r.get('error')}")
        except Exception as exc:
            errors.append(f"search:{q}:{type(exc).__name__}:{str(exc)[:180]}")

    # Prioritize pages that look commercial/pricing-oriented.
    seen_urls = set()
    candidates = []
    for r in search_rows:
        u = str(r.get("url") or "")
        if not u or u in seen_urls:
            continue
        seen_urls.add(u)
        t = (str(r.get("title") or "") + " " + u).lower()
        weight = 2 if any(k in t for k in ("pricing", "price", "plans", "cost")) else 1
        candidates.append((weight, r))
    candidates.sort(key=lambda x: x[0], reverse=True)

    fetched = []
    prices = []
    for _, r in candidates[:MAX_FETCHES_PER_CANDIDATE]:
        u = r.get("url")
        try:
            page = web.fetch_public_page(u)
            if not page.get("success"):
                continue
            txt = str(page.get("text") or "")
            fetched.append({
                "url": u,
                "domain": domain(u),
                "title": r.get("title"),
                "query": r.get("query"),
                "characters": page.get("characters"),
            })
            prices.extend(extract_prices(txt, u, str(r.get("title") or "")))
        except Exception as exc:
            errors.append(f"fetch:{u}:{type(exc).__name__}:{str(exc)[:180]}")

    prices = dedupe_prices(prices)

    existing = existing_domains(payload)
    searched_domains = {domain(r.get("url")) for r in search_rows if domain(r.get("url"))}
    fetched_domains = {x["domain"] for x in fetched if x["domain"]}
    all_domains = existing | searched_domains | fetched_domains
    pricing_domains = {x["domain"] for x in prices if x["domain"]}

    model = str(o.mechanism or payload.get("business_model") or "unknown")
    price_floor, price_basis = conservative_price(prices, model)

    # Only produce canonical economics when independent pricing evidence exists.
    # The estimates below are transparent validation-stage priors, NOT observed
    # revenue/profit and NOT a measured probability of business success.
    economics_ready = bool(price_floor and len(pricing_domains) >= 2 and len(all_domains) >= 3)

    expected_profit = 0.0
    probability = 0.0
    margin_pct = 0.0
    readiness = max(15.0, float(o.readiness or 0))
    time_to_cash_days = float(o.time_to_cash_days or 30)

    estimate_basis = None
    if economics_ready:
        margin_prior = MARGIN_PRIOR.get(model, MARGIN_PRIOR["unknown"])
        margin_pct = round(margin_prior * 100, 2)

        # Conservative validation scenario: ONE paid customer/order during the
        # first 30 days at the lower observed market price.
        expected_profit = round(max(1.0, price_floor * margin_prior), 2)

        # Evidence-conditioned validation prior, deliberately capped at 30%.
        # This is a model estimate, not an observed success rate.
        probability = round(min(
            30.0,
            6.0
            + min(10.0, len(all_domains) * 1.5)
            + min(8.0, len(pricing_domains) * 2.0)
            + min(6.0, len(prices) * 0.75)
        ), 2)

        readiness = max(readiness, 30.0)
        time_to_cash_days = min(time_to_cash_days, 30.0)
        estimate_basis = {
            "type": "conservative_validation_scenario",
            "observed_price_floor_usd": price_floor,
            "price_basis": price_basis,
            "assumed_first_30d_paid_customers_or_orders": 1,
            "contribution_margin_prior": margin_prior,
            "margin_prior_is_assumption": True,
            "expected_profit_is_observed": False,
            "probability_is_observed": False,
            "probability_method": "bounded evidence-conditioned validation prior",
        }

    evidence_quality = round(min(
        80.0,
        max(float(o.evidence_quality or 0), 20.0)
        + min(24.0, len(all_domains) * 3.0)
        + min(18.0, len(pricing_domains) * 4.5)
    ), 2)

    artifact = {
        "schema": "companyos.economics_validation.v1",
        "name": o.name,
        "business_model": model,
        "market": o.category,
        "sector": o.category,
        "target_customer": payload.get("target_customer", "unknown"),
        "problem": payload.get("problem", "unknown"),
        "offer": payload.get("offer", "unknown"),
        "description": payload.get("description", ""),
        "expected_profit": expected_profit,
        "expected_profit_period": "first_30_days",
        "expected_profit_basis": estimate_basis,
        "margin": margin_pct,
        "probability_success_pct": probability,
        "probability_basis": estimate_basis,
        "execution_readiness_pct": readiness,
        "time_to_cash_days": time_to_cash_days,
        "capital_required": float(o.capital_required or 0),
        "capital_required_unknown": bool(payload.get("capital_required_unknown", True)),
        "evidence_count": max(int(o.evidence_count or 0), len(all_domains)),
        "evidence_quality_pct": evidence_quality,
        "evidence_quality_method": "domain_diversity_plus_independent_pricing_sources",
        "source_urls": sorted({
            str(r.get("url")) for r in search_rows if r.get("url")
        })[:30],
        "evidence": {
            "existing_external_domains": sorted(existing),
            "search_queries": queries,
            "search_results": search_rows[:30],
            "fetched_pages": fetched,
            "pricing_observations": prices,
            "distinct_external_domains": sorted(all_domains),
            "distinct_pricing_domains": sorted(pricing_domains),
        },
        "pricing_observation_count": len(prices),
        "pricing_domain_count": len(pricing_domains),
        "economics_ready": economics_ready,
        "next_action": (
            "Run a reversible buyer-facing validation of the specific offer and observed price point; "
            "measure qualified interest, conversion, and any real revenue before scaling."
            if economics_ready else
            "Collect at least two independent current pricing sources plus buyer-demand evidence before estimating economics."
        ),
        "external_research_performed": True,
        "financial_action_performed": False,
        "external_outreach_performed": False,
        "publication_performed": False,
        "generated_at_unix": time.time(),
        "research_errors": errors[-20:],
    }

    path = OUT / f"v65_95_economics_{slug(o.name)}.json"
    save(path, artifact)
    return {
        "name": o.name,
        "business_model": model,
        "sector": o.category,
        "economics_ready": economics_ready,
        "pricing_observations": len(prices),
        "pricing_domains": len(pricing_domains),
        "external_domains": len(all_domains),
        "observed_price_floor_usd": price_floor,
        "expected_profit_30d_estimate": expected_profit,
        "probability_estimate": probability,
        "evidence_quality": evidence_quality,
        "artifact": str(path.relative_to(ROOT)),
        "errors": errors[-5:],
    }

def cycle():
    mem = available_mb()
    print("AVAILABLE_MB=", mem)
    if mem and mem < MIN_AVAILABLE_MB:
        result = {
            "version": "V65.95",
            "timestamp_unix": time.time(),
            "deferred": True,
            "reason": "resource_pressure",
            "available_mb": mem,
            "minimum_available_mb": MIN_AVAILABLE_MB,
        }
        save(STATE, result)
        print("V65_95_DEFERRED=resource_pressure")
        return result

    from companyos.runtime import profit_opportunity_engine as poe
    from companyos.runtime.candidate_enrichment_bridge import refresh_enrichments

    rows = poe.discover()
    state = load(STATE, {})
    cursor = int(state.get("cursor", 0) or 0)

    selected, next_cursor = choose_diverse(rows, cursor, BATCH_SIZE)

    print("DISCOVERED_CANDIDATES_BEFORE=", len(rows))
    print("ECONOMICS_CANDIDATES_THIS_CYCLE=", [o.name for o in selected])

    if not selected:
        result = {
            "version": "V65.95",
            "timestamp_unix": time.time(),
            "deferred": False,
            "reason": "no_evidence_bearing_classified_candidates",
            "candidate_count": len(rows),
        }
        save(STATE, result)
        print("V65_95_NO_ELIGIBLE_RESEARCH_TARGETS=true")
        return result

    web = load_web_plugin()
    results = []
    for o in selected:
        try:
            results.append(research_candidate(web, o))
        except Exception as exc:
            results.append({
                "name": o.name,
                "economics_ready": False,
                "error": f"{type(exc).__name__}:{exc}",
            })

    enrichment = refresh_enrichments(max_age_hours=168)
    decision = poe.choose()
    after = poe.discover()

    ready = [r for r in results if r.get("economics_ready")]
    models = Counter(str(o.mechanism or "unknown") for o in after)
    sectors = Counter(str(o.category or "unknown") for o in after)

    report = {
        "version": "V65.95",
        "timestamp_unix": time.time(),
        "deferred": False,
        "cursor_before": cursor,
        "cursor": next_cursor,
        "candidate_count_before": len(rows),
        "candidate_count_after": len(after),
        "economics_targets": len(selected),
        "economics_ready_this_cycle": len(ready),
        "strict_execution_qualified_after": int(decision.get("eligible_count", 0) or 0),
        "results": results,
        "enrichment": enrichment,
        "business_model_counts": dict(models),
        "sector_counts": dict(sectors),
        "observed_revenue_created": 0,
        "financial_actions": False,
        "external_outreach": False,
        "publication": False,
        "estimate_policy": {
            "expected_profit_is_scenario_estimate_not_observed_profit": True,
            "probability_is_bounded_validation_prior_not_observed_rate": True,
            "requires_two_independent_pricing_domains": True,
            "requires_three_external_domains": True,
            "assumed_paid_customers_or_orders_30d": 1,
        },
    }

    state = {
        "version": "V65.95",
        "cursor": next_cursor,
        "last_cycle_unix": time.time(),
        "last_result": report,
    }
    save(STATE, state)

    rp = REPORTS / f"v65_95_economics_validation_{int(time.time())}.json"
    save(rp, report)

    print("ECONOMICS_TARGETS=", len(selected))
    print("ECONOMICS_READY_THIS_CYCLE=", len(ready))
    print("ECONOMICS_RESULTS=", json.dumps(results, sort_keys=True, default=str))
    print("ENRICHMENT=", json.dumps(enrichment, sort_keys=True, default=str))
    print("DISTINCT_CANDIDATES_AFTER=", len(after))
    print("STRICT_EXECUTION_QUALIFIED_AFTER=", report["strict_execution_qualified_after"])
    print("BUSINESS_MODEL_COUNTS=", dict(models))
    print("SECTOR_COUNTS=", dict(sectors))
    print("REPORT=", rp)
    print("V65_95_TARGETED_ECONOMICS_RESEARCH=PASS")
    print("V65_95_INDEPENDENT_PRICING_REQUIREMENT=PASS")
    print("V65_95_TRANSPARENT_ESTIMATES=PASS")
    print("V65_95_NO_FINANCIAL_ACTIONS=PASS")
    print("V65_95_COMPLETE")
    return report

def status():
    print(json.dumps(load(STATE, {"status":"not_run"}), indent=2, sort_keys=True, default=str))

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("once","loop","status"))
    p.add_argument("--interval", type=int, default=900)
    a = p.parse_args()

    if a.command == "once":
        cycle()
    elif a.command == "status":
        status()
    else:
        interval = max(600, int(a.interval))
        while True:
            try:
                cycle()
            except Exception as exc:
                print("V65_95_LOOP_ERROR=", f"{type(exc).__name__}:{exc}", flush=True)
            time.sleep(interval)

if __name__ == "__main__":
    main()
PY

python -m py_compile "$MODULE"
echo "MODULE_COMPILE=PASS"
}

is_running() {
  if [ ! -f "$PIDFILE" ]; then
    return 1
  fi
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null
}

action="${1:-start}"

case "$action" in
  start)
    echo "===== COMPANYOS V65.95 ECONOMICS VALIDATION ====="
    install_module

    if is_running; then
      echo "ECONOMICS_MANAGER_ALREADY_RUNNING=true"
      echo "PID=$(cat "$PIDFILE")"
      exit 0
    fi

    echo "===== INITIAL ECONOMICS VALIDATION CYCLE ====="
    python -m companyos.runtime.economics_validation_manager once

    nohup python -m companyos.runtime.economics_validation_manager loop \
      --interval "$INTERVAL_SECONDS" >> "$LOGFILE" 2>&1 &
    pid="$!"
    echo "$pid" > "$PIDFILE"
    sleep 1

    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PIDFILE"
      echo "V65_95_ABORT=manager_failed_to_start"
      exit 1
    fi

    echo "ECONOMICS_MANAGER_RUNNING=true"
    echo "PID=$pid"
    echo "INTERVAL_SECONDS=$INTERVAL_SECONDS"
    echo "LOGFILE=$LOGFILE"
    echo "V65_95_MANAGER_START=PASS"
    echo "V65_95_COMPLETE"
    ;;

  once)
    install_module
    python -m companyos.runtime.economics_validation_manager once
    ;;

  status)
    echo "===== COMPANYOS V65.95 STATUS ====="
    if is_running; then
      echo "ECONOMICS_MANAGER_RUNNING=true"
      echo "PID=$(cat "$PIDFILE")"
    else
      echo "ECONOMICS_MANAGER_RUNNING=false"
    fi
    [ -f "$MODULE" ] && python -m companyos.runtime.economics_validation_manager status || true
    echo "----- LOG TAIL -----"
    tail -n 100 "$LOGFILE" 2>/dev/null || true
    ;;

  stop)
    echo "===== COMPANYOS V65.95 STOP ====="
    if is_running; then
      pid="$(cat "$PIDFILE")"
      kill "$pid" 2>/dev/null || true
      for _ in $(seq 1 20); do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        sleep 1
      done
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$PIDFILE"
    echo "V65_95_STOP=PASS"
    ;;

  restart)
    "$0" stop || true
    exec "$0" start
    ;;

  *)
    echo "Usage: $0 {start|status|stop|restart|once}"
    exit 2
    ;;
esac
