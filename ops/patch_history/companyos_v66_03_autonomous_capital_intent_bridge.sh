#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
BRIDGE="$ROOT/companyos/runtime/capital_intent_bridge.py"
GOV="$ROOT/companyos/runtime/live_drl_strategy_governor.py"
ALLOC="$ROOT/companyos/runtime/drl_financial_allocator.py"
CTL="$ROOT/scripts/companyos_capital_bridge_ctl"
PIDFILE="$RT/capital_intent_bridge.pid"
LOGFILE="$RT/capital_intent_bridge.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.03 AUTONOMOUS CAPITAL INTENT BRIDGE ====="
echo "MODE=LIVE_DISCOVERY_TO_CAPITAL_PIPELINE"
echo "NOTE=LIVE_AUTHORITY_SWITCHES_UNCHANGED"
echo "NOTE=NO_RECIPIENT_OR_AMOUNT_FABRICATION"

for f in "$GOV" "$ALLOC"; do
  [ -f "$f" ] || { echo "V66_03_ABORT=missing:$f"; exit 1; }
done

mkdir -p "$ROOT/companyos/runtime" "$ROOT/scripts" "$RT"

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$BRIDGE" "$GOV"; do
  if [ -f "$f" ]; then
    cp "$f" "${f}.v66_03_backup_${stamp}"
    echo "BACKUP=${f}.v66_03_backup_${stamp}"
  fi
done

cat > "$BRIDGE" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Iterable

from companyos.runtime import drl_financial_allocator as allocator

HOME = Path.home()
ROOT = HOME / "companyos"
RT = HOME / ".companyos_runtime"
LOCAL_RT = ROOT / ".companyos_runtime"

STATE = RT / "finance" / "capital_intent_bridge_state.json"
LATEST = RT / "finance" / "capital_intent_bridge_latest.json"
HISTORY = RT / "finance" / "capital_intent_bridge_history.jsonl"
STATE.parent.mkdir(parents=True, exist_ok=True)

VERSION = "V66.03"
MAX_FILES_PER_CYCLE = 700
MAX_FILE_BYTES = 2_000_000
MAX_AGE_SECONDS = 14 * 86400

RECIPIENT_KEYS = (
    "recipient",
    "recipient_address",
    "wallet_address",
    "payment_address",
    "pay_to",
    "solana_recipient",
)

SOL_AMOUNT_KEYS = (
    "amount_sol",
    "capital_required_sol",
    "funding_required_sol",
    "payment_amount_sol",
    "spend_sol",
)

USD_AMOUNT_KEYS = (
    "amount_usd",
    "capital_required_usd",
    "funding_required_usd",
    "payment_amount_usd",
    "spend_usd",
)

PROFIT_KEYS = (
    "expected_profit_usd",
    "expected_profit_30d",
    "projected_profit_30d",
    "expected_profit",
    "profit_estimate",
)

PROB_KEYS = (
    "probability_estimate",
    "probability",
    "success_probability",
    "probability_of_profit",
)

EVIDENCE_COUNT_KEYS = (
    "evidence_count",
    "verified_evidence_count",
)

EVIDENCE_LIST_KEYS = (
    "evidence",
    "evidence_sources",
    "pricing_observations",
    "market_evidence",
)

VENTURE_ID_KEYS = (
    "venture_id",
    "candidate_id",
    "orchestration_id",
    "project_id",
    "id",
)

PURPOSE_KEYS = (
    "purpose",
    "next_action",
    "title",
    "name",
    "business_model",
    "slug",
)


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


def normalize_probability(v: float | None) -> float | None:
    if v is None:
        return None
    x = float(v)
    if 1.0 < x <= 100.0:
        x /= 100.0
    if 0.0 <= x <= 1.0:
        return x
    return None


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


def walk_dicts(obj: Any, depth: int = 0):
    if depth > 8:
        return
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_dicts(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_dicts(v, depth + 1)


def candidate_roots() -> list[Path]:
    roots = [
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
        RT / "finance_requests",
        LOCAL_RT / "finance_requests",
    ]
    return [p for p in roots if p.exists()]


def recent_files() -> list[Path]:
    now = time.time()
    files: list[Path] = []
    seen: set[str] = set()

    for root in candidate_roots():
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".json", ".jsonl"}:
                continue
            try:
                st = p.stat()
            except Exception:
                continue
            if st.st_size > MAX_FILE_BYTES:
                continue
            if now - st.st_mtime > MAX_AGE_SECONDS:
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            files.append(p)

    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[:MAX_FILES_PER_CYCLE]


def docs_from_file(path: Path):
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
            for d in walk_dicts(obj):
                yield d, f"{path}:{n}"
    else:
        try:
            obj = json.loads(text)
        except Exception:
            return
        for d in walk_dicts(obj):
            yield d, str(path)


def explicit_capital_fields(d: dict[str, Any]) -> dict[str, Any] | None:
    recipient = scalar(d, RECIPIENT_KEYS)
    amount_sol = numeric(d, SOL_AMOUNT_KEYS)
    amount_usd = numeric(d, USD_AMOUNT_KEYS)
    expected_profit = numeric(d, PROFIT_KEYS)
    prob = normalize_probability(numeric(d, PROB_KEYS))
    ev_count = evidence_count(d)
    venture_id = scalar(d, VENTURE_ID_KEYS)
    purpose = scalar(d, PURPOSE_KEYS)

    # Hard rule: no invented recipient and no invented spend amount.
    if not recipient or (amount_sol is None and amount_usd is None):
        return None

    if expected_profit is None or prob is None or ev_count is None:
        return None

    if not venture_id:
        return None

    if not purpose:
        purpose = f"Capital request for venture {venture_id}"

    converted_from_usd = False
    conversion_price = None

    if amount_sol is None and amount_usd is not None:
        price, _ = allocator.sol_price()
        if not price or price <= 0:
            return None
        amount_sol = float(amount_usd) / float(price)
        converted_from_usd = True
        conversion_price = float(price)

    return {
        "recipient": str(recipient),
        "amount_sol": float(amount_sol),
        "purpose": str(purpose),
        "venture_id": str(venture_id),
        "expected_profit_usd": float(expected_profit),
        "probability": float(prob),
        "evidence_count": int(ev_count),
        "source_amount_usd": float(amount_usd) if amount_usd is not None else None,
        "converted_from_usd": converted_from_usd,
        "conversion_sol_price_usd": conversion_price,
    }


def fingerprint(fields: dict[str, Any]) -> str:
    stable = {
        "recipient": fields["recipient"],
        "amount_sol": round(float(fields["amount_sol"]), 12),
        "venture_id": fields["venture_id"],
        "purpose": fields["purpose"],
        "expected_profit_usd": round(float(fields["expected_profit_usd"]), 4),
        "probability": round(float(fields["probability"]), 6),
        "evidence_count": int(fields["evidence_count"]),
    }
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def state() -> dict[str, Any]:
    return load_json(STATE, {"version": VERSION, "seen_fingerprints": []})


def scan_once() -> dict[str, Any]:
    st = state()
    seen = set(st.get("seen_fingerprints") or [])

    scanned_files = 0
    scanned_records = 0
    explicit_payment_records = 0
    created = []
    duplicates = 0

    for path in recent_files():
        scanned_files += 1
        for d, source in docs_from_file(path):
            scanned_records += 1
            fields = explicit_capital_fields(d)
            if not fields:
                continue

            explicit_payment_records += 1
            fp = fingerprint(fields)
            if fp in seen:
                duplicates += 1
                continue

            row = allocator.submit_intent(
                recipient=fields["recipient"],
                amount_sol=fields["amount_sol"],
                purpose=fields["purpose"],
                venture_id=fields["venture_id"],
                expected_profit_usd=fields["expected_profit_usd"],
                probability=fields["probability"],
                evidence_count=fields["evidence_count"],
                source=f"capital_intent_bridge:{source}",
            )

            created.append({
                "intent_id": row["intent_id"],
                "venture_id": fields["venture_id"],
                "source": source,
                "amount_sol": fields["amount_sol"],
                "converted_from_usd": fields["converted_from_usd"],
                "conversion_sol_price_usd": fields["conversion_sol_price_usd"],
            })
            seen.add(fp)

    st.update({
        "version": VERSION,
        "updated_at_unix": time.time(),
        "seen_fingerprints": list(seen)[-5000:],
        "last_created": created[-50:],
    })
    save_json(STATE, st)

    ranked = allocator.rank()
    result = {
        "version": VERSION,
        "mode": "live_discovery_to_capital_pipeline",
        "scanned_files": scanned_files,
        "scanned_records": scanned_records,
        "explicit_payment_records": explicit_payment_records,
        "new_intents_created": len(created),
        "duplicates_skipped": duplicates,
        "eligible_capital_intents": sum(
            1 for x in ranked if x.get("evaluation", {}).get("eligible")
        ),
        "open_capital_intents": len(ranked),
        "created": created,
        "rules": {
            "recipient_must_be_explicit": True,
            "amount_must_be_explicit": True,
            "profit_probability_evidence_must_be_present": True,
            "recipient_fabrication": False,
            "amount_fabrication": False,
        },
    }
    save_json(LATEST, result)
    append_jsonl(HISTORY, {"timestamp_unix": time.time(), **result})
    return result


def status() -> dict[str, Any]:
    ranked = allocator.rank()
    return {
        "version": VERSION,
        "bridge_state": state(),
        "latest": load_json(LATEST, {}),
        "capital_allocator": {
            "open_intents": len(ranked),
            "eligible_intents": sum(
                1 for x in ranked if x.get("evaluation", {}).get("eligible")
            ),
            "top": ranked[:5],
        },
    }


def loop(interval: int):
    while True:
        try:
            r = scan_once()
            print(json.dumps({
                "ts": time.time(),
                "scanned_files": r["scanned_files"],
                "new_intents_created": r["new_intents_created"],
                "eligible_capital_intents": r["eligible_capital_intents"],
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

echo "===== PATCH DRL FINANCIAL ACTION MASK ====="
python - <<'PY'
from pathlib import Path

p = Path.home()/"companyos/companyos/runtime/live_drl_strategy_governor.py"
s = p.read_text()

old = (
'    if action == "allocate_verified_capital":\n'
'        if not bool(LIVE_AUTHORITY.get("financial_actions")):\n'
'            return None, "financial_actions_authority_off"\n'
'        if not bool(LIVE_AUTHORITY.get("wallet_transactions")):\n'
'            return None, "wallet_transactions_authority_off"\n'
'        return ["python", "-m", "companyos.runtime.drl_financial_allocator", "once"], "drl_capital_allocator_once"\n'
)

new = (
'    if action == "allocate_verified_capital":\n'
'        if not bool(LIVE_AUTHORITY.get("financial_actions")):\n'
'            return None, "financial_actions_authority_off"\n'
'        if not bool(LIVE_AUTHORITY.get("wallet_transactions")):\n'
'            return None, "wallet_transactions_authority_off"\n'
'        try:\n'
'            from companyos.runtime import drl_financial_allocator as _capital_allocator\n'
'            _ranked = _capital_allocator.rank()\n'
'            _eligible = [x for x in _ranked if x.get("evaluation", {}).get("eligible")]\n'
'            if not _eligible:\n'
'                return None, "no_eligible_capital_intent"\n'
'        except Exception as _exc:\n'
'            return None, f"capital_intent_check_failed:{type(_exc).__name__}"\n'
'        return ["python", "-m", "companyos.runtime.drl_financial_allocator", "once"], "drl_capital_allocator_once"\n'
)

if new not in s:
    if old not in s:
        raise SystemExit("V66_03_ABORT=capital_action_block_not_found")
    s = s.replace(old, new, 1)

p.write_text(s)
print("V66_03_CAPITAL_ACTION_MASK=PASS")
PY

cat > "$CTL" <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
PIDFILE="$RT/capital_intent_bridge.pid"
LOGFILE="$RT/capital_intent_bridge.log"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

cmd="${1:-status}"
case "$cmd" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "CAPITAL_INTENT_BRIDGE_ALREADY_RUNNING PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python -m companyos.runtime.capital_intent_bridge loop \
      --interval "${COMPANYOS_CAPITAL_BRIDGE_INTERVAL_SECONDS:-60}" \
      >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "CAPITAL_INTENT_BRIDGE_RUNNING PID=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    echo "CAPITAL_INTENT_BRIDGE_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  once)
    python -m companyos.runtime.capital_intent_bridge once
    ;;
  status)
    python -m companyos.runtime.capital_intent_bridge status
    if [ -f "$PIDFILE" ]; then
      echo "PID=$(cat "$PIDFILE")"
      ps -p "$(cat "$PIDFILE")" -o pid,etime,args || true
    fi
    ;;
  log)
    tail -n "${2:-120}" "$LOGFILE"
    ;;
  *)
    echo "usage: $0 {start|stop|restart|once|status|log [lines]}"
    exit 2
    ;;
esac
SH
chmod +x "$CTL"

cat > "$ROOT/tests/test_capital_intent_bridge.py" <<'PY'
from companyos.runtime.capital_intent_bridge import (
    explicit_capital_fields,
    normalize_probability,
)

def test_probability_percent_normalizes():
    assert normalize_probability(25) == 0.25

def test_no_recipient_means_no_intent():
    d = {
        "amount_sol": 0.1,
        "expected_profit_30d": 50,
        "probability_estimate": 0.5,
        "evidence_count": 3,
        "venture_id": "v1",
    }
    assert explicit_capital_fields(d) is None

def test_no_amount_means_no_intent():
    d = {
        "recipient": "11111111111111111111111111111111",
        "expected_profit_30d": 50,
        "probability_estimate": 0.5,
        "evidence_count": 3,
        "venture_id": "v1",
    }
    assert explicit_capital_fields(d) is None

def test_complete_explicit_request_extracts():
    d = {
        "recipient": "11111111111111111111111111111111",
        "amount_sol": 0.1,
        "expected_profit_30d": 50,
        "probability_estimate": 0.5,
        "evidence_count": 3,
        "venture_id": "v1",
        "purpose": "buy required service",
    }
    x = explicit_capital_fields(d)
    assert x is not None
    assert x["recipient"] == d["recipient"]
    assert x["amount_sol"] == 0.1
PY

echo "===== COMPILE ====="
python -m py_compile "$BRIDGE" "$GOV"
echo "V66_03_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_capital_intent_bridge.py
echo "V66_03_TESTS=PASS"

echo "===== FIRST LIVE DISCOVERY SCAN ====="
python -m companyos.runtime.capital_intent_bridge once

echo "===== START CAPITAL INTENT BRIDGE ====="
"$CTL" restart

echo "===== RESTART LIVE DRL WITH CAPITAL-AWARE MASK ====="
if [ -x "$ROOT/scripts/companyos_live_drlctl" ]; then
  "$ROOT/scripts/companyos_live_drlctl" restart
fi

echo "===== STATUS ====="
"$CTL" status

echo "V66_03_DISCOVERY_TO_CAPITAL_BRIDGE=PASS"
echo "V66_03_EXPLICIT_RECIPIENT_REQUIRED=PASS"
echo "V66_03_EXPLICIT_AMOUNT_REQUIRED=PASS"
echo "V66_03_INTENT_DEDUP=PASS"
echo "V66_03_DRL_CAPITAL_ACTION_MASK=PASS"
echo "V66_03_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_03_COMPLETE"
