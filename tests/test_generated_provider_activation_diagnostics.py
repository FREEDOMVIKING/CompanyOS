from __future__ import annotations

import pytest

from generated_provider_activation_diagnostics import diagnose_provider_activation
from generated_provider_activation_diagnostics.core import (
    _coerce_records,
    _validate_record,
)


def test_empty_input_returns_empty_diagnostics():
    result = diagnose_provider_activation(None)
    assert result["success"] is True
    assert result["status"] == "provider_activation_diagnostics_complete"
    assert result["records"] == []
    assert result["summary"]["total_providers"] == 0
    assert result["summary"]["healthy"] is False
    assert result["summary"]["fully_healthy"] is False
    assert result["recommendations"] == ["No provider activation records were supplied."]


def test_single_dict_is_accepted():
    result = diagnose_provider_activation({"provider": "openai", "status": "active"})
    assert result["summary"]["total_providers"] == 1
    assert result["summary"]["active_count"] == 1
    assert result["summary"]["healthy"] is True
    assert result["summary"]["fully_healthy"] is True
    assert result["records"][0]["provider"] == "openai"
    assert result["records"][0]["errors"] == []


def test_multiple_providers():
    providers = [
        {"provider": "openai", "status": "active"},
        {"provider": "local_llama", "status": "inactive"},
        {"provider": "anthropic", "status": "degraded"},
    ]
    result = diagnose_provider_activation(providers)
    assert result["summary"]["total_providers"] == 3
    assert result["summary"]["active_count"] == 1
    assert result["summary"]["by_status"]["active"] == 1
    assert result["summary"]["by_status"]["inactive"] == 1
    assert result["summary"]["by_status"]["degraded"] == 1
    assert result["summary"]["healthy"] is True
    assert result["summary"]["fully_healthy"] is False
    assert any("Degraded providers detected" in r for r in result["recommendations"])


def test_malformed_record_missing_provider():
    result = diagnose_provider_activation([{"status": "active"}])
    record = result["records"][0]
    assert record["provider"] == "unknown"
    assert record["status"] == "active"
    assert "missing or non-string 'provider' field" in record["errors"]
    assert result["summary"]["invalid_count"] == 0  # status was valid


def test_malformed_record_missing_status():
    result = diagnose_provider_activation([{"provider": "openai"}])
    record = result["records"][0]
    assert record["status"] == "invalid"
    assert "missing or non-string 'status' field" in record["errors"]
    assert result["summary"]["invalid_count"] == 1
    assert result["summary"]["healthy"] is False


def test_unknown_status_normalized():
    result = diagnose_provider_activation([{"provider": "x", "status": "bogus"}])
    record = result["records"][0]
    assert record["status"] == "unknown"
    assert "unknown status 'bogus'" in record["errors"]


def test_non_dict_record():
    result = diagnose_provider_activation(["not-a-dict"])
    record = result["records"][0]
    assert record["provider"] == "unknown"
    assert record["status"] == "invalid"
    assert "record is not a dict" in record["errors"][0]
    assert result["summary"]["invalid_count"] == 1


def test_non_iterable_input():
    result = diagnose_provider_activation(12345)
    assert result["success"] is True
    assert result["summary"]["total_providers"] == 1
    assert result["records"][0]["status"] == "invalid"
    assert "providers argument is not iterable" in result["records"][0]["errors"]


def test_preserves_optional_metadata():
    provider = {
        "provider": "openai",
        "status": "active",
        "configured": True,
        "reachable": True,
        "usable": True,
        "latency_ms": 120,
        "note": "primary",
        "extra_ignored": True,
    }
    result = diagnose_provider_activation(provider)
    record = result["records"][0]
    assert record["configured"] is True
    assert record["reachable"] is True
    assert record["usable"] is True
    assert record["latency_ms"] == 120
    assert record["note"] == "primary"
    assert "extra_ignored" not in record


def test_error_status_recommendation():
    result = diagnose_provider_activation([{"provider": "broken", "status": "error"}])
    assert any("Providers in error state" in r for r in result["recommendations"])


def test_no_active_providers_recommendation():
    result = diagnose_provider_activation(
        [{"provider": "a", "status": "inactive"}, {"provider": "b", "status": "degraded"}]
    )
    assert any("No providers are currently active" in r for r in result["recommendations"])


def test_all_active_recommendation():
    result = diagnose_provider_activation(
        [{"provider": "a", "status": "active"}, {"provider": "b", "status": "active"}]
    )
    assert "All supplied providers are active and valid." in result["recommendations"]


def test_function_is_pure_and_does_not_raise():
    # Various nasty inputs should never raise.
    diagnose_provider_activation(None)
    diagnose_provider_activation([])
    diagnose_provider_activation([{}, {}, {}])
    diagnose_provider_activation([None, 1, "str", []])
    diagnose_provider_activation({"status": 123})
    diagnose_provider_activation([{"provider": 123, "status": 456}])


def test_coerce_records_with_generator():
    gen = (x for x in [{"provider": "a", "status": "active"}, {"provider": "b", "status": "inactive"}])
    records = _coerce_records(gen)
    assert len(records) == 2
    assert records[0]["index"] == 0
    assert records[1]["index"] == 1


def test_validate_record_returns_index():
    record = _validate_record({"provider": "x", "status": "active"}, 7)
    assert record["index"] == 7


def test_package_exports_public_function():
    import generated_provider_activation_diagnostics as pkg

    assert hasattr(pkg, "diagnose_provider_activation")
    assert pkg.diagnose_provider_activation is diagnose_provider_activation
    assert pkg.__all__ == ["diagnose_provider_activation"]
