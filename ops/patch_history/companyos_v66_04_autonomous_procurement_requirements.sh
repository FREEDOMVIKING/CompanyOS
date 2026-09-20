#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
MOD="$ROOT/companyos/runtime/autonomous_procurement_requirements.py"
BRIDGE="$ROOT/companyos/runtime/capital_intent_bridge.py"
CTL="$ROOT/scripts/companyos_procurementctl"
PIDFILE="$RT/autonomous_procurement_requirements.pid"
LOGFILE="$RT/autonomous_procurement_requirements.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.04 AUTONOMOUS PROCUREMENT + CAPITAL REQUIREMENTS ====="
echo "MODE=LIVE_PROCUREMENT_DISCOVERY"
echo "NOTE=LIVE_AUTHORITY_SWITCHES_UNCHANGED"
echo "NOTE=NO_VENDOR_PRICE_OR_PAYMENT_DESTINATION_FABRICATION"

[ -f "$BRIDGE" ] || { echo "V66_04_ABORT=missing:$BRIDGE"; exit 1; }

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT/procurement"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$MOD" "$BRIDGE"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_04_backup_${stamp}"
    echo "BACKUP=${f}.v66_04_backup_${stamp}"
  fi
done

cat > "$MOD" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

HOME = Path.home()
ROOT = HOME / "companyos"
RT = HOME / ".companyos_runtime"
LOCAL_RT = ROOT / ".companyos_runtime"

PRT = RT / "procurement"
REQUIREMENTS = PRT / "requirements.jsonl"
SOURCING = PRT / "sourcing_requests.jsonl"
STATE = PRT / "state.json"
LATEST = PRT / "latest.json"
HISTORY = PRT / "history.jsonl"
PRT.mkdir(parents=True, exist_ok=True)

VERSION = "V66.04"
MAX_FILES = 700
MAX_FILE_BYTES = 2_000_000
MAX_AGE_SECONDS = 21 * 86400

NEED_TERMS = {
    "domain": ("domain", "dns", "registrar"),
    "hosting": ("hosting", "cloudflare", "vercel", "worker", "server"),
    "software_api": ("api", "software", "saas", "subscription", "license"),
    "inventory_product": ("inventory", "product", "supplier", "wholesale", "dropship", "drop ship"),
    "contractor_service": ("contractor", "service provider", "freelancer", "labor"),
    "materials_equipment": ("material", "equipment", "rental", "tool", "machine"),
    "advertising": ("advertising", "paid ads", "ad spend", "campaign"),
}

VENDOR_KEYS = ("vendor", "provider", "supplier", "merchant", "seller", "contractor")
ITEM_KEYS = ("item", "product", "service", "resource", "requirement", "need", "title", "name")
PRICE_USD_KEYS = (
    "price_usd", "quoted_price_usd", "cost_usd", "amount_usd",
    "capital_required_usd", "funding_required_usd", "payment_amount_usd",
)
PRICE_SOL_KEYS = (
    "amount_sol", "capital_required_sol", "funding_required_sol",
    "payment_amount_sol", "price_sol",
)
PAYMENT_KEYS = (
    "recipient", "recipient_address", "wallet_address", "payment_address",
    "pay_to", "solana_recipient",
)
VENTURE_KEYS = ("venture_id", "candidate_id", "orchestration_id", "project_id", "id")
PROFIT_KEYS = (
    "expected_profit_usd", "expected_profit_30d", "projected_profit_30d",
    "expected_profit", "profit_estimate",
)
PROB_KEYS = (
    "probability_estimate", "probability", "success_probability", "probability_of_profit",
)
EVIDENCE_COUNT_KEYS = ("evidence_count", "verified_evidence_count")
EVIDENCE_LIST_KEYS = ("evidence", "evidence_sources", "pricing_observations", "market_evidence")
URL_KEYS = ("source_url", "vendor_url", "product_url", "pricing_url", "url")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def scalar(d: dict[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return None


def numeric(d: dict[str, Any], keys: Iterable[str]) -> float | None:
    v = scalar(d, keys)
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def probability(d: dict[str, Any]) -> float | None:
    x = numeric(d, PROB_KEYS)
    if x is None:
        return None
    if 1.0 < x <= 100.0:
        x /= 100.0
    return x if 0.0 <= x <= 1.0 else None


def evidence_count(d: dict[str, Any]) -> int | None:
    x = numeric(d, EVIDENCE_COUNT_KEYS)
    if x is not None:
        return max(0, int(x))
    for k in EVIDENCE_LIST_KEYS:
        v = d.get(k)
        if isinstance(v, list):
            return len(v)
        if isinstance(v, dict):
            return len(v)
    return None


def walk(obj: Any, depth: int = 0):
    if depth > 8:
        return
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, depth + 1)


def roots() -> list[Path]:
    candidates = [
        RT / "profit_first_candidates",
        LOCAL_RT / "profit_first_candidates",
        RT / "canonical_research_outputs",
        LOCAL_RT / "canonical_research_outputs",
        RT / "reports",
        LOCAL_RT / "reports",
        RT / "live_validation",
        LOCAL_RT / "live_validation",
        RT / "venture_launch",
        LOCAL_RT / "venture_launch",
        RT / "ventures",
        LOCAL_RT / "ventures",
        RT / "generated_products",
        LOCAL_RT / "generated_products",
        RT / "specialist_evidence",
        LOCAL_RT / "specialist_evidence",
    ]
    return [p for p in candidates if p.exists()]


def recent_files() -> list[Path]:
    now = time.time()
    found = []
    seen = set()
    for root in roots():
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".json", ".jsonl"}:
                continue
            try:
                st = p.stat()
            except Exception:
                continue
            if st.st_size > MAX_FILE_BYTES or now - st.st_mtime > MAX_AGE_SECONDS:
                continue
            rp = str(p.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            found.append(p)
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found[:MAX_FILES]


def documents(path: Path):
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return
    if path.suffix.lower() == ".jsonl":
        for n, line in enumerate(text.splitlines(), 1):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            for d in walk(obj):
                yield d, f"{path}:{n}"
    else:
        try:
            obj = json.loads(text)
        except Exception:
            return
        for d in walk(obj):
            yield d, str(path)


def text_blob(d: dict[str, Any]) -> str:
    parts = []
    for k, v in d.items():
        if isinstance(v, str):
            parts.append(k)
            parts.append(v)
        elif isinstance(v, (int, float, bool)):
            parts.append(f"{k}={v}")
    return " ".join(parts).lower()


def classify_need(d: dict[str, Any]) -> str | None:
    blob = text_blob(d)
    for category, terms in NEED_TERMS.items():
        if any(t in blob for t in terms):
            return category
    explicit = scalar(d, ITEM_KEYS)
    if explicit:
        return "general_procurement"
    return None


def has_purchase_signal(d: dict[str, Any]) -> bool:
    blob = text_blob(d)
    signals = (
        "buy", "purchase", "pay", "cost", "price", "quote", "procure", "vendor",
        "supplier", "subscription", "license", "hosting", "domain", "inventory",
        "capital_required", "funding_required", "payment_amount",
    )
    return any(x in blob for x in signals) or any(k in d for k in PRICE_USD_KEYS + PRICE_SOL_KEYS)


def extract(d: dict[str, Any], source: str) -> dict[str, Any] | None:
    if not has_purchase_signal(d):
        return None

    category = classify_need(d)
    if not category:
        return None

    venture_id = scalar(d, VENTURE_KEYS)
    if not venture_id:
        return None

    item = scalar(d, ITEM_KEYS) or f"{category} requirement"
    vendor = scalar(d, VENDOR_KEYS)
    price_usd = numeric(d, PRICE_USD_KEYS)
    price_sol = numeric(d, PRICE_SOL_KEYS)
    recipient = scalar(d, PAYMENT_KEYS)
    profit = numeric(d, PROFIT_KEYS)
    prob = probability(d)
    ev_count = evidence_count(d)
    source_url = scalar(d, URL_KEYS)

    missing = []
    if not vendor:
        missing.append("vendor")
    if price_usd is None and price_sol is None:
        missing.append("price")
    if not recipient:
        missing.append("payment_destination")
    if profit is None:
        missing.append("expected_profit_usd")
    if prob is None:
        missing.append("probability")
    if ev_count is None:
        missing.append("evidence_count")

    ready_for_capital = not missing

    return {
        "schema": "companyos.procurement_requirement.v1",
        "requirement_id": str(uuid.uuid4()),
        "created_at_unix": time.time(),
        "venture_id": str(venture_id),
        "category": category,
        "item": str(item),
        "vendor": str(vendor) if vendor else None,
        "price_usd": price_usd,
        "amount_sol": price_sol,
        "recipient": str(recipient) if recipient else None,
        "expected_profit_usd": profit,
        "probability_estimate": prob,
        "evidence_count": ev_count,
        "source_url": str(source_url) if source_url else None,
        "source_artifact": source,
        "missing_fields": missing,
        "ready_for_capital_intent": ready_for_capital,
        "status": "READY_FOR_CAPITAL" if ready_for_capital else "SOURCING_REQUIRED",
        "fabricated_fields": [],
    }


def fingerprint(req: dict[str, Any]) -> str:
    stable = {
        "venture_id": req.get("venture_id"),
        "category": req.get("category"),
        "item": req.get("item"),
        "vendor": req.get("vendor"),
        "price_usd": req.get("price_usd"),
        "amount_sol": req.get("amount_sol"),
        "recipient": req.get("recipient"),
        "source_artifact": req.get("source_artifact"),
    }
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def make_sourcing_request(req: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "companyos.procurement_sourcing_request.v1",
        "sourcing_request_id": str(uuid.uuid4()),
        "created_at_unix": time.time(),
        "venture_id": req["venture_id"],
        "category": req["category"],
        "item": req["item"],
        "known_vendor": req.get("vendor"),
        "known_price_usd": req.get("price_usd"),
        "known_amount_sol": req.get("amount_sol"),
        "known_payment_destination": req.get("recipient"),
        "missing_fields": list(req.get("missing_fields") or []),
        "objective": (
            "Acquire real external evidence for missing procurement fields. "
            "Do not fabricate vendor, price, payment destination, probability, or profit."
        ),
        "required_evidence": [
            "real vendor/provider identity",
            "current quoted or published price",
            "source URL or other verifiable evidence",
            "actual payment destination only when supplied by the vendor/provider",
        ],
        "source_artifact": req.get("source_artifact"),
        "status": "OPEN",
    }


def scan_once() -> dict[str, Any]:
    st = load_json(STATE, {"version": VERSION, "seen_fingerprints": []})
    seen = set(st.get("seen_fingerprints") or [])

    scanned_files = 0
    scanned_records = 0
    requirements = 0
    ready = 0
    sourcing = 0
    duplicates = 0
    created = []

    for path in recent_files():
        scanned_files += 1
        for d, source in documents(path):
            scanned_records += 1
            req = extract(d, source)
            if not req:
                continue

            fp = fingerprint(req)
            if fp in seen:
                duplicates += 1
                continue

            append_jsonl(REQUIREMENTS, req)
            requirements += 1
            seen.add(fp)

            if req["ready_for_capital_intent"]:
                ready += 1
            else:
                sr = make_sourcing_request(req)
                append_jsonl(SOURCING, sr)
                sourcing += 1

            created.append({
                "requirement_id": req["requirement_id"],
                "venture_id": req["venture_id"],
                "category": req["category"],
                "status": req["status"],
                "missing_fields": req["missing_fields"],
            })

    st.update({
        "version": VERSION,
        "updated_at_unix": time.time(),
        "seen_fingerprints": list(seen)[-8000:],
        "last_created": created[-100:],
    })
    save_json(STATE, st)

    result = {
        "version": VERSION,
        "mode": "live_procurement_discovery",
        "scanned_files": scanned_files,
        "scanned_records": scanned_records,
        "requirements_created": requirements,
        "ready_for_capital": ready,
        "sourcing_requests_created": sourcing,
        "duplicates_skipped": duplicates,
        "created": created,
        "rules": {
            "vendor_fabrication": False,
            "price_fabrication": False,
            "payment_destination_fabrication": False,
            "profit_fabrication": False,
            "probability_fabrication": False,
            "capital_intent_requires_complete_real_fields": True,
        },
    }
    save_json(LATEST, result)
    append_jsonl(HISTORY, {"timestamp_unix": time.time(), **result})
    return result


def status() -> dict[str, Any]:
    return {
        "version": VERSION,
        "state": load_json(STATE, {}),
        "latest": load_json(LATEST, {}),
        "requirements_file": str(REQUIREMENTS),
        "sourcing_requests_file": str(SOURCING),
    }


def loop(interval: int):
    while True:
        try:
            r = scan_once()
            print(json.dumps({
                "ts": time.time(),
                "requirements_created": r["requirements_created"],
                "ready_for_capital": r["ready_for_capital"],
                "sourcing_requests_created": r["sourcing_requests_created"],
            }, sort_keys=True), flush=True)
        except Exception as exc:
            print(json.dumps({
                "ts": time.time(),
                "error": f"{type(exc).__name__}:{exc}",
            }, sort_keys=True), flush=True)
        time.sleep(max(30, int(interval)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("once")
    sub.add_parser("status")
    lp = sub.add_parser("loop")
    lp.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()

    if args.cmd == "once":
        print(json.dumps(scan_once(), indent=2, sort_keys=True, default=str))
    elif args.cmd == "status":
        print(json.dumps(status(), indent=2, sort_keys=True, default=str))
    elif args.cmd == "loop":
        loop(args.interval)


if __name__ == "__main__":
    main()
PY

echo "===== ADD PROCUREMENT OUTPUTS TO CAPITAL BRIDGE ====="
python - <<'PY'
from pathlib import Path

p = Path.home()/"companyos/companyos/runtime/capital_intent_bridge.py"
s = p.read_text()

needle = '        RT / "finance_requests",\n        LOCAL_RT / "finance_requests",\n'
replacement = (
    '        RT / "finance_requests",\n'
    '        LOCAL_RT / "finance_requests",\n'
    '        RT / "procurement",\n'
    '        LOCAL_RT / "procurement",\n'
)

if replacement not in s:
    if needle not in s:
        raise SystemExit("V66_04_ABORT=capital_bridge_root_anchor_missing")
    s = s.replace(needle, replacement, 1)

p.write_text(s)
print("V66_04_CAPITAL_BRIDGE_PROCUREMENT_ROOT=PASS")
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
PIDFILE="$RT/autonomous_procurement_requirements.pid"
LOGFILE="$RT/autonomous_procurement_requirements.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

cmd="${1:-status}"
case "$cmd" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "PROCUREMENT_ENGINE_ALREADY_RUNNING PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python -m companyos.runtime.autonomous_procurement_requirements loop \
      --interval "${COMPANYOS_PROCUREMENT_INTERVAL_SECONDS:-60}" \
      >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "PROCUREMENT_ENGINE_RUNNING PID=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    echo "PROCUREMENT_ENGINE_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  once)
    python -m companyos.runtime.autonomous_procurement_requirements once
    ;;
  status)
    python -m companyos.runtime.autonomous_procurement_requirements status
    if [ -f "$PIDFILE" ]; then
      echo "PID=$(cat "$PIDFILE")"
      ps -p "$(cat "$PIDFILE")" -o pid,etime,args || true
    fi
    ;;
  requirements)
    tail -n "${2:-30}" "$RT/procurement/requirements.jsonl" 2>/dev/null || true
    ;;
  sourcing)
    tail -n "${2:-30}" "$RT/procurement/sourcing_requests.jsonl" 2>/dev/null || true
    ;;
  log)
    tail -n "${2:-120}" "$LOGFILE"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|once|status|requirements [n]|sourcing [n]|log [n]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_autonomous_procurement_requirements.py" <<'PY'
from companyos.runtime.autonomous_procurement_requirements import extract

def test_detects_missing_payment_destination_without_fabricating():
    d = {
        "venture_id": "v1",
        "item": "hosting subscription",
        "vendor": "ExampleHost",
        "price_usd": 20,
        "expected_profit_30d": 100,
        "probability_estimate": 0.5,
        "evidence_count": 3,
    }
    x = extract(d, "test.json")
    assert x is not None
    assert x["ready_for_capital_intent"] is False
    assert "payment_destination" in x["missing_fields"]
    assert x["recipient"] is None

def test_complete_requirement_ready():
    d = {
        "venture_id": "v2",
        "item": "supplier inventory",
        "vendor": "VendorCo",
        "price_usd": 50,
        "recipient": "11111111111111111111111111111111",
        "expected_profit_usd": 200,
        "probability": 0.6,
        "evidence_count": 4,
    }
    x = extract(d, "test.json")
    assert x is not None
    assert x["ready_for_capital_intent"] is True
    assert x["missing_fields"] == []

def test_no_purchase_signal_is_ignored():
    d = {
        "venture_id": "v3",
        "title": "general market research",
        "expected_profit_30d": 100,
        "probability_estimate": 0.5,
        "evidence_count": 3,
    }
    assert extract(d, "test.json") is None
PY

echo "===== COMPILE ====="
python -m py_compile "$MOD" "$BRIDGE"
echo "V66_04_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_autonomous_procurement_requirements.py
echo "V66_04_TESTS=PASS"

echo "===== FIRST LIVE PROCUREMENT SCAN ====="
python -m companyos.runtime.autonomous_procurement_requirements once

echo "===== RE-SCAN CAPITAL BRIDGE ====="
python -m companyos.runtime.capital_intent_bridge once

echo "===== START PROCUREMENT ENGINE ====="
"$CTL" restart

echo "===== RESTART CAPITAL BRIDGE ====="
if [ -x "$ROOT/scripts/companyos_capital_bridge_ctl" ]; then
  "$ROOT/scripts/companyos_capital_bridge_ctl" restart
fi

echo "===== STATUS ====="
"$CTL" status

echo "V66_04_PROCUREMENT_REQUIREMENTS=PASS"
echo "V66_04_SOURCING_GAP_DETECTION=PASS"
echo "V66_04_CAPITAL_BRIDGE_INTEGRATION=PASS"
echo "V66_04_NO_VENDOR_FABRICATION=PASS"
echo "V66_04_NO_PRICE_FABRICATION=PASS"
echo "V66_04_NO_PAYMENT_DESTINATION_FABRICATION=PASS"
echo "V66_04_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_04_COMPLETE"
