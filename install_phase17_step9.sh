#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase17_step9_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 17 Step 9 - Business Forecasting Engine"
echo "============================================================"

for file in \
  "$AGENTS/business_forecasting_engine.py" \
  "$CTL/forecastctl" \
  "$MEMORY/business_forecasting_config.json" \
  "$MEMORY/business_forecasting_results.json" \
  "$MEMORY/business_forecasting_briefing.json" \
  "$MEMORY/business_forecasting_health.json" \
  "$MEMORY/business_forecasting_audit.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/business_forecasting_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_forecasting": true,
  "automatic_scenario_generation": true,
  "automatic_forecast_briefing": true,
  "automatic_code_changes": false,
  "automatic_task_execution": false,
  "automatic_customer_contact": false,
  "automatic_external_execution": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required": true,
  "forecast_horizon_days": 30
}
JSON

cat > "$AGENTS/business_forecasting_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "business_forecasting_config.json"
RESULTS = MEMORY / "business_forecasting_results.json"
BRIEFING = MEMORY / "business_forecasting_briefing.json"
HEALTH = MEMORY / "business_forecasting_health.json"
AUDIT = MEMORY / "business_forecasting_audit.json"

PERFORMANCE = MEMORY / "performance_analytics_metrics.json"
INVOICES = MEMORY / "invoice_registry.json"
PROJECTS = MEMORY / "project_registry.json"
SALES = MEMORY / "sales_pipeline.json"
PRIORITIES = MEMORY / "executive_priority_rankings.json"
IMPROVEMENTS = MEMORY / "continuous_improvement_backlog.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []

    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })

    save_json(AUDIT, records[-1000:])


def collect_pipeline_value(records: list[dict[str, Any]]) -> float:
    total = 0.0

    for item in records:
        status = str(item.get("status") or "").lower()
        if status in {"won", "closed", "paid", "completed", "lost", "rejected"}:
            continue

        value = number(
            item.get("estimated_value"),
            number(
                item.get("amount"),
                number(item.get("value"), 0),
            ),
        )

        probability = number(
            item.get("probability"),
            number(item.get("probability_percent"), 50),
        )

        if probability > 1:
            probability = probability / 100.0

        probability = max(0.0, min(1.0, probability))
        total += value * probability

    return round(total, 2)


def run_forecast() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "business_forecasting_engine_disabled",
        }
        audit("forecast", result)
        return result

    performance = load_json(
        PERFORMANCE,
        {},
    ).get("metrics", {})

    invoices = load_json(INVOICES, {}).get("invoices", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    sales_store = load_json(SALES, {})
    sales = (
        sales_store.get("opportunities")
        or sales_store.get("deals")
        or sales_store.get("pipeline")
        or []
    )
    priorities = load_json(
        PRIORITIES,
        {},
    ).get("rankings", {}).get("priorities", [])
    improvements = load_json(IMPROVEMENTS, {}).get("items", [])

    outstanding_value = round(
        sum(
            number(item.get("balance_due"), 0)
            for item in invoices
            if number(item.get("balance_due"), 0) > 0
            and item.get("status") != "void"
        ),
        2,
    )

    project_value = round(
        sum(
            number(
                item.get("amount"),
                number(item.get("estimated_value"), 0),
            )
            for item in projects
            if item.get("status") not in {"completed", "cancelled", "closed"}
        ),
        2,
    )

    weighted_pipeline = collect_pipeline_value(sales)

    task_rate = number(
        performance.get("tasks", {}).get("completion_rate_percent"),
        0,
    )
    project_rate = number(
        performance.get("projects", {}).get("completion_rate_percent"),
        0,
    )
    health_score = number(
        load_json(
            MEMORY / "performance_analytics_report.json",
            {},
        ).get("report", {}).get("health_score"),
        70,
    )

    critical_count = sum(
        1 for item in priorities
        if item.get("priority_band") == "critical"
    )
    high_count = sum(
        1 for item in priorities
        if item.get("priority_band") == "high"
    )
    approved_improvements = sum(
        1 for item in improvements
        if item.get("status") == "approved"
    )

    recovery_rate = 0.55
    if health_score >= 80:
        recovery_rate = 0.75
    elif health_score < 50:
        recovery_rate = 0.35

    delivery_factor = max(
        0.25,
        min(1.0, (task_rate + project_rate + health_score) / 300.0),
    )

    base_cash_inflow = (
        outstanding_value * recovery_rate
        + weighted_pipeline * 0.45
        + project_value * delivery_factor * 0.20
    )

    risk_penalty = min(
        0.40,
        critical_count * 0.05 + high_count * 0.02,
    )

    improvement_bonus = min(
        0.20,
        approved_improvements * 0.025,
    )

    expected = round(
        max(0.0, base_cash_inflow * (1 - risk_penalty + improvement_bonus)),
        2,
    )
    conservative = round(expected * 0.65, 2)
    optimistic = round(expected * 1.35, 2)

    confidence = 50.0
    if outstanding_value > 0:
        confidence += 10
    if project_value > 0:
        confidence += 10
    if weighted_pipeline > 0:
        confidence += 10
    if performance:
        confidence += 10
    confidence -= min(20, critical_count * 5)
    confidence = round(max(20.0, min(90.0, confidence)), 2)

    horizon = int(config.get("forecast_horizon_days", 30))

    forecast = {
        "generated_at": now(),
        "forecast_horizon_days": horizon,
        "confidence_percent": confidence,
        "inputs": {
            "outstanding_receivables": outstanding_value,
            "active_project_value": project_value,
            "weighted_sales_pipeline": weighted_pipeline,
            "task_completion_rate_percent": task_rate,
            "project_completion_rate_percent": project_rate,
            "performance_health_score": health_score,
            "critical_priority_count": critical_count,
            "high_priority_count": high_count,
            "approved_improvement_count": approved_improvements,
        },
        "cash_inflow_scenarios": {
            "conservative": conservative,
            "expected": expected,
            "optimistic": optimistic,
        },
        "operating_outlook": {
            "delivery_factor": round(delivery_factor, 4),
            "receivable_recovery_rate": round(recovery_rate, 4),
            "risk_penalty": round(risk_penalty, 4),
            "improvement_bonus": round(improvement_bonus, 4),
        },
        "automatic_code_changes": False,
        "automatic_task_execution": False,
        "automatic_external_execution": False,
        "automatic_spending": False,
    }

    risks = []
    opportunities = []

    if outstanding_value > 0:
        opportunities.append(
            f"Recover up to ${outstanding_value:,.2f} in outstanding receivables."
        )

    if weighted_pipeline > 0:
        opportunities.append(
            f"Weighted sales pipeline contributes ${weighted_pipeline:,.2f}."
        )

    if critical_count > 0:
        risks.append(
            f"{critical_count} critical priority item(s) may reduce forecast performance."
        )

    if task_rate < 50:
        risks.append("Low task completion may delay expected cash inflow.")

    if project_rate < 50 and project_value > 0:
        risks.append("Low project completion may delay revenue recognition.")

    if not risks:
        risks.append("No major forecast risk was detected from current records.")

    if not opportunities:
        opportunities.append(
            "Add receivable, project, and sales records to improve forecast coverage."
        )

    briefing = {
        "generated_at": now(),
        "headline": (
            f"{horizon}-day expected cash inflow forecast: "
            f"${expected:,.2f}"
        ),
        "confidence_percent": confidence,
        "scenarios": forecast["cash_inflow_scenarios"],
        "top_risks": risks[:5],
        "top_opportunities": opportunities[:5],
        "recommended_focus": [
            "Review critical priorities first.",
            "Advance approved internal improvements.",
            "Prepare owner-reviewed receivable follow-ups.",
            "Keep external execution and spending under owner control.",
        ],
        "automatic_code_changes": False,
        "automatic_task_execution": False,
        "automatic_external_execution": False,
        "automatic_spending": False,
    }

    save_json(
        RESULTS,
        {
            "schema_version": 1,
            "forecast": forecast,
            "last_updated_at": now(),
        },
    )

    save_json(
        BRIEFING,
        {
            "schema_version": 1,
            "briefing": briefing,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_forecast_at": now(),
            "confidence_percent": confidence,
            "expected_cash_inflow": expected,
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "business_forecast_complete",
        "forecast": forecast,
        "briefing": briefing,
    }
    audit("forecast", result)
    return result


def show_forecast() -> dict[str, Any]:
    data = load_json(RESULTS, {}).get("forecast")
    result = {
        "success": bool(data),
        "status": "business_forecast_results",
        "forecast": data,
    }
    audit("show", result)
    return result


def show_briefing() -> dict[str, Any]:
    data = load_json(BRIEFING, {}).get("briefing")
    result = {
        "success": bool(data),
        "status": "business_forecast_briefing",
        "briefing": data,
    }
    audit("briefing", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "business_forecasting_engine_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_forecasting": config.get(
            "automatic_internal_forecasting", False
        ),
        "automatic_scenario_generation": config.get(
            "automatic_scenario_generation", False
        ),
        "automatic_forecast_briefing": config.get(
            "automatic_forecast_briefing", False
        ),
        "automatic_code_changes": config.get(
            "automatic_code_changes", False
        ),
        "automatic_task_execution": config.get(
            "automatic_task_execution", False
        ),
        "automatic_customer_contact": config.get(
            "automatic_customer_contact", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "health": health,
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "forecast":
            return print_result(run_forecast())

        if action == "show":
            return print_result(show_forecast())

        if action == "briefing":
            return print_result(show_briefing())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_forecast_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "business_forecasting_error",
            "error": str(exc),
        }

        save_json(
            HEALTH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )

        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/business_forecasting_engine.py"

cat > "$CTL/forecastctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "business_forecasting_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/forecastctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/business_forecasting_engine.py" \
  "$CTL/forecastctl"

echo "[2/5] Running business forecast..."
python "$CTL/forecastctl" forecast

echo "[3/5] Checking outputs..."
python "$CTL/forecastctl" show
python "$CTL/forecastctl" briefing
python "$CTL/forecastctl" status

echo "[4/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "business_forecasting_engine.py",
    root / "companyos" / "forecastctl",
    root / "ceo_memory" / "business_forecasting_config.json",
    root / "ceo_memory" / "business_forecasting_results.json",
    root / "ceo_memory" / "business_forecasting_briefing.json",
    root / "ceo_memory" / "business_forecasting_health.json",
]

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")
    elif path.stat().st_size <= 0:
        errors.append(f"Empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error: {exc}")

try:
    config = json.loads(required[2].read_text(encoding="utf-8"))

    for field in [
        "automatic_code_changes",
        "automatic_task_execution",
        "automatic_customer_contact",
        "automatic_external_execution",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    forecast = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("forecast", {})

    for field in [
        "forecast_horizon_days",
        "confidence_percent",
        "inputs",
        "cash_inflow_scenarios",
        "operating_outlook",
    ]:
        if field not in forecast:
            errors.append(f"Forecast missing field: {field}")

    scenarios = forecast.get("cash_inflow_scenarios", {})

    for field in ["conservative", "expected", "optimistic"]:
        if field not in scenarios:
            errors.append(f"Forecast scenario missing: {field}")

    if forecast.get("automatic_external_execution") is not False:
        errors.append("External execution was enabled")

    if forecast.get("automatic_spending") is not False:
        errors.append("Automatic spending was enabled")

    briefing = json.loads(
        required[4].read_text(encoding="utf-8")
    ).get("briefing", {})

    for field in [
        "headline",
        "confidence_percent",
        "scenarios",
        "top_risks",
        "top_opportunities",
        "recommended_focus",
    ]:
        if field not in briefing:
            errors.append(f"Briefing missing field: {field}")

except Exception as exc:
    errors.append(f"Forecast data error: {exc}")

print("--------------------------------------------")
print("Phase 17 Step 9 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo "[5/5] Complete."

echo
echo "============================================================"
echo " PHASE 17 STEP 9 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/forecastctl forecast"
echo "  python companyos/forecastctl show"
echo "  python companyos/forecastctl briefing"
echo "  python companyos/forecastctl status"
