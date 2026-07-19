#!/usr/bin/env python3

import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONFIG = ROOT / "ceo_memory/phase50/phase50_config.json"
ENGINE = ROOT / "agents/phase50_opportunity_engine/opportunity_engine.py"
INTAKE = ROOT / "agents/phase50_opportunity_engine/discovery_intake.py"
CTL = ROOT / "companyos/phase50ctl"

errors = []
warnings = []


def check(condition, message):
    if not condition:
        errors.append(message)


print("[1/5] Checking Phase 50 files...")

check(CONFIG.exists(), "Missing Phase 50 config")
check(ENGINE.exists(), "Missing opportunity engine")
check(INTAKE.exists(), "Missing discovery intake")
check(CTL.exists(), "Missing phase50ctl")


print("[2/5] Checking configuration...")

config = {}

try:
    config = json.loads(CONFIG.read_text())
except Exception as exc:
    errors.append(f"Invalid Phase 50 config: {exc}")

if config:
    check(config.get("enabled") is True, "Phase 50 is not enabled")

    check(
        config.get("minimum_qualification_score", 0) > 0,
        "Invalid qualification threshold"
    )

    check(
        config.get("minimum_confidence_score", 0) > 0,
        "Invalid confidence threshold"
    )

    scoring = config.get("scoring", {})

    check(
        sum(scoring.values()) == 100,
        "Scoring weights must total 100"
    )


print("[3/5] Checking safety boundaries...")

rules = config.get("rules", {}) if config else {}

check(
    rules.get("deduplicate_opportunities") is True,
    "Duplicate protection disabled"
)

check(
    rules.get("require_evidence") is True,
    "Evidence requirement disabled"
)

check(
    rules.get("reject_illegal_or_prohibited") is True,
    "Illegal/prohibited opportunity rejection disabled"
)

check(
    rules.get("reject_unbounded_financial_risk") is True,
    "Unbounded financial risk protection disabled"
)

check(
    rules.get(
        "require_owner_approval_for_irreversible_external_actions"
    ) is True,
    "Owner approval boundary for irreversible actions disabled"
)

check(
    rules.get(
        "require_owner_approval_for_financial_commitments"
    ) is True,
    "Owner approval boundary for financial commitments disabled"
)


print("[4/5] Compiling Phase 50 components...")

for path in [ENGINE, INTAKE, CTL]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile failure {path.name}: {exc}")


print("[5/5] Verifying persistent data...")

for name in [
    "opportunities.json",
    "phase50_state.json",
    "discovery_inbox.json",
    "discovery_history.json"
]:
    path = ROOT / "ceo_memory/phase50" / name

    if path.exists():
        try:
            json.loads(path.read_text())
        except Exception as exc:
            errors.append(f"Invalid JSON {name}: {exc}")


print()
print("--------------------------------------------")
print("PHASE 50 OPPORTUNITY ENGINE VERIFICATION")
print("Errors:", len(errors))
print("Warnings:", len(warnings))

if errors:
    print()
    print("ERRORS:")
    for error in errors:
        print("-", error)

if warnings:
    print()
    print("WARNINGS:")
    for warning in warnings:
        print("-", warning)

print("--------------------------------------------")

if errors:
    raise SystemExit(1)

print()
print("PHASE 50 AUTONOMOUS OPPORTUNITY ENGINE VERIFIED")
print("OPPORTUNITY SCORING: ENABLED")
print("QUALIFICATION ENGINE: ENABLED")
print("DUPLICATE PROTECTION: ENABLED")
print("DISCOVERY INTAKE PIPELINE: ENABLED")
print("PERSISTENT OPPORTUNITY MEMORY: ENABLED")
print("IRREVERSIBLE EXTERNAL ACTION APPROVAL: REQUIRED")
print("FINANCIAL COMMITMENT APPROVAL: REQUIRED")
print("Errors: 0")
print("Warnings: 0")
