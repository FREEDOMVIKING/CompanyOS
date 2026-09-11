from datetime import datetime, timezone
from typing import Dict
from .config import companyos_home, runtime_dir
from .processes import pid_alive
from .storage import read_json

def collect_health() -> Dict:
    home = companyos_home()
    state = read_json(runtime_dir() / "services.json", {"services": {}})
    services = {}
    for name, item in state.get("services", {}).items():
        pid = int(item.get("pid", 0) or 0)
        services[name] = {**item, "pid": pid, "alive": pid_alive(pid)}

    executive_dashboard = read_json(
        home / "companyos_runtime" / "phase18201_18300" / "executive_dashboard.json", {}
    )
    legacy_scan = read_json(
        home / "legacy_test_reports" / "latest_legacy_test_scan.json", {}
    )
    enabled = [x for x in services.values() if x.get("enabled", True)]
    active = sum(1 for x in enabled if x.get("alive"))
    expected = len(enabled)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "18301-18400",
        "overall_healthy": active == expected and expected > 0,
        "active_service_count": active,
        "expected_service_count": expected,
        "services": services,
        "executive": {
            "available": bool(executive_dashboard),
            "audit_passed": executive_dashboard.get("audit", {}).get("passed"),
            "venture_count": len(executive_dashboard.get("ranking", [])),
            "last_update": executive_dashboard.get("timestamp"),
        },
        "legacy_tests": {
            "reported": bool(legacy_scan),
            "historical_test_count": legacy_scan.get("historical_test_count", 0),
            "parse_error_count": legacy_scan.get("parse_error_count", 0),
            "execution_policy": "isolated_from_active_bundle_tests",
        },
    }
