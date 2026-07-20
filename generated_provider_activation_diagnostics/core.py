"""Core implementation for provider activation diagnostics.

The public function :func:`diagnose_provider_activation` inspects a
collection of provider activation records and returns structured
diagnostic information. It is intentionally pure: it does not touch the
network, the filesystem, or any external service.
"""

from __future__ import annotations

from typing import Any, Iterable


REQUIRED_PROVIDER_FIELDS = ("provider", "status")

VALID_STATUSES = {
    "active",
    "inactive",
    "degraded",
    "unconfigured",
    "error",
    "unknown",
}


def _coerce_records(providers: Any) -> list[dict[str, Any]]:
    """Normalize the ``providers`` argument into a list of dicts.

    Accepts ``None``, a single dict, or an iterable of dicts. Malformed
    entries are replaced with sentinel dicts that carry an ``invalid``
    status so callers can see what was rejected.
    """

    if providers is None:
        return []

    if isinstance(providers, dict):
        # A single provider record.
        return [_validate_record(providers, 0)]

    if not isinstance(providers, Iterable):
        return [
            {
                "provider": "unknown",
                "status": "invalid",
                "index": 0,
                "errors": ["providers argument is not iterable"],
            }
        ]

    records: list[dict[str, Any]] = []
    for index, item in enumerate(providers):
        records.append(_validate_record(item, index))
    return records


def _validate_record(item: Any, index: int) -> dict[str, Any]:
    """Validate a single provider record.

    Returns a normalized dict with at least ``provider``, ``status``,
    ``index``, and ``errors`` keys. Malformed input is captured rather
    than raised.
    """

    errors: list[str] = []

    if not isinstance(item, dict):
        return {
            "provider": "unknown",
            "status": "invalid",
            "index": index,
            "errors": [f"record is not a dict: {type(item).__name__}"],
        }

    provider = item.get("provider")
    status = item.get("status")

    if not provider or not isinstance(provider, str):
        errors.append("missing or non-string 'provider' field")
        provider = "unknown"

    if not status or not isinstance(status, str):
        errors.append("missing or non-string 'status' field")
        status = "invalid"
    elif status not in VALID_STATUSES:
        errors.append(f"unknown status '{status}'")
        status = "unknown"

    record: dict[str, Any] = {
        "provider": provider,
        "status": status,
        "index": index,
        "errors": errors,
    }

    # Preserve additional metadata fields that may be useful.
    for key in ("configured", "reachable", "usable", "latency_ms", "note"):
        if key in item:
            record[key] = item[key]

    return record


def _summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build aggregate summary statistics from validated records."""

    total = len(records)
    by_status: dict[str, int] = {}
    invalid_count = 0
    active_count = 0
    providers_seen: list[str] = []

    for record in records:
        status = record.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        if status == "invalid":
            invalid_count += 1
        if status == "active":
            active_count += 1
        provider = record.get("provider", "unknown")
        if provider not in providers_seen:
            providers_seen.append(provider)

    healthy = total > 0 and active_count > 0 and invalid_count == 0
    fully_healthy = total > 0 and invalid_count == 0 and by_status.get("active", 0) == total

    return {
        "total_providers": total,
        "active_count": active_count,
        "invalid_count": invalid_count,
        "by_status": by_status,
        "providers": providers_seen,
        "healthy": healthy,
        "fully_healthy": fully_healthy,
    }


def _recommendations(records: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    """Produce simple, internal-only diagnostic recommendations."""

    recs: list[str] = []

    if summary["total_providers"] == 0:
        recs.append("No provider activation records were supplied.")
        return recs

    if summary["invalid_count"] > 0:
        recs.append(
            f"{summary['invalid_count']} provider record(s) are malformed; "
            "correct the input before relying on diagnostics."
        )

    if summary["active_count"] == 0 and summary["invalid_count"] == 0:
        recs.append("No providers are currently active; review activation configuration.")

    degraded = [r for r in records if r.get("status") == "degraded"]
    if degraded:
        names = sorted({r.get("provider", "unknown") for r in degraded})
        recs.append(
            "Degraded providers detected: " + ", ".join(names) + "."
        )

    errored = [r for r in records if r.get("status") == "error"]
    if errored:
        names = sorted({r.get("provider", "unknown") for r in errored})
        recs.append(
            "Providers in error state: " + ", ".join(names) + "."
        )

    if summary["fully_healthy"]:
        recs.append("All supplied providers are active and valid.")

    return recs


def diagnose_provider_activation(providers: Any = None) -> dict[str, Any]:
    """Diagnose provider activation records.

    Parameters
    ----------
    providers:
        ``None``, a single provider dict, or an iterable of provider
        dicts. Each dict should contain at least ``provider`` (str) and
        ``status`` (str) fields. Additional fields such as ``configured``,
        ``reachable``, ``usable``, ``latency_ms``, and ``note`` are
        preserved when present.

    Returns
    -------
    dict
        A structured diagnostic result containing:

        * ``success`` (bool) -- always ``True``; diagnostics never raise.
        * "status" (str) -- human-readable status label.
        * "records" (list[dict]) -- validated per-provider diagnostics.
        * "summary" (dict) -- aggregate statistics.
        * "recommendations" (list[str]) -- internal-only guidance.

    Notes
    -----
    This function is pure and side-effect free. It does not perform
    network, filesystem, financial, or external actions.
    """

    records = _coerce_records(providers)
    summary = _summarize(records)
    recommendations = _recommendations(records, summary)

    return {
        "success": True,
        "status": "provider_activation_diagnostics_complete",
        "records": records,
        "summary": summary,
        "recommendations": recommendations,
    }
