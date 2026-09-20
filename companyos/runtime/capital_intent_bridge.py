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
        RT / "procurement",
        LOCAL_RT / "procurement",
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
