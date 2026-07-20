#!/usr/bin/env python3
import pytest
from generated_internal_health_summary import generate_internal_health_summary

def test_empty_input():
    """Test that an empty input list returns a healthy status."""
    result = generate_internal_health_summary([])
    assert result["overall_status"] == "healthy"
    assert result["unhealthy_components"] == []
    assert result["warnings"] == []
    assert result["recommended_actions"] == []

def test_all_healthy():
    """Test with all components healthy."""
    records = [
        {"component_name": "service_a", "status": "healthy", "details": "All systems nominal.", "recommendation": None},
        {"component_name": "service_b", "status": "healthy", "details": "Operational.", "recommendation": ""},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "healthy"
    assert result["unhealthy_components"] == []
    assert result["warnings"] == []
    assert result["recommended_actions"] == []

def test_with_unhealthy_components():
    """Test with some unhealthy components."""
    records = [
        {"component_name": "service_a", "status": "healthy", "details": "All systems nominal.", "recommendation": None},
        {"component_name": "service_b", "status": "unhealthy", "details": "High latency detected.", "recommendation": "Investigate network latency."},
        {"component_name": "service_c", "status": "unhealthy", "details": "Service unavailable.", "recommendation": "Restart service C."},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "unhealthy"
    assert len(result["unhealthy_components"]) == 2
    assert {"component_name": "service_b", "details": "High latency detected."} in result["unhealthy_components"]
    assert {"component_name": "service_c", "details": "Service unavailable."} in result["unhealthy_components"]
    assert len(result["warnings"]) == 0
    assert len(result["recommended_actions"]) == 2
    assert {"component_name": "service_b", "action": "Investigate network latency."} in result["recommended_actions"]
    assert {"component_name": "service_c", "action": "Restart service C."} in result["recommended_actions"]

def test_with_warnings():
    """Test with some components having warnings."""
    records = [
        {"component_name": "service_a", "status": "healthy", "details": "All systems nominal.", "recommendation": None},
        {"component_name": "service_b", "status": "warning", "details": "Low disk space.", "recommendation": "Free up disk space."},
        {"component_name": "service_c", "status": "healthy", "details": "Operational.", "recommendation": ""},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "warning"
    assert len(result["unhealthy_components"]) == 0
    assert len(result["warnings"]) == 1
    assert {"component_name": "service_b", "details": "Low disk space."} in result["warnings"]
    assert len(result["recommended_actions"]) == 1
    assert {"component_name": "service_b", "action": "Free up disk space."} in result["recommended_actions"]

def test_mixed_statuses():
    """Test with a mix of healthy, warning, and unhealthy components."""
    records = [
        {"component_name": "service_a", "status": "healthy", "details": "Nominal.", "recommendation": None},
        {"component_name": "service_b", "status": "warning", "details": "High CPU usage.", "recommendation": "Optimize process B."},
        {"component_name": "service_c", "status": "unhealthy", "details": "Database connection failed.", "recommendation": "Check database credentials."},
        {"component_name": "service_d", "status": "healthy", "details": "OK.", "recommendation": ""},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "unhealthy"
    assert len(result["unhealthy_components"]) == 1
    assert {"component_name": "service_c", "details": "Database connection failed."} in result["unhealthy_components"]
    assert len(result["warnings"]) == 1
    assert {"component_name": "service_b", "details": "High CPU usage."} in result["warnings"]
    assert len(result["recommended_actions"]) == 2
    assert {"component_name": "service_c", "action": "Check database credentials."} in result["recommended_actions"]
    assert {"component_name": "service_b", "action": "Optimize process B."} in result["recommended_actions"]

def test_missing_keys_and_none_values():
    """Test handling of records with missing keys or None values."""
    records = [
        {"component_name": "service_a", "status": "healthy"}, # Missing details and recommendation
        {"component_name": "service_b", "status": None, "details": "Status is None.", "recommendation": None},
        {"component_name": "service_c", "status": "unhealthy", "details": None, "recommendation": "Fix C."},
        {"component_name": "service_d", "status": "warning", "details": "Low memory.", "recommendation": None},
        {},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "unhealthy"
    assert len(result["unhealthy_components"]) == 1
    assert {"component_name": "service_c", "details": None} in result["unhealthy_components"]
    assert len(result["warnings"]) == 1
    assert {"component_name": "service_d", "details": "Low memory."} in result["warnings"]
    assert len(result["recommended_actions"]) == 1
    assert {"component_name": "service_c", "action": "Fix C."} in result["recommended_actions"]

def test_no_recommendations():
    """Test when no recommendations are provided."""
    records = [
        {"component_name": "service_a", "status": "healthy", "details": "Nominal.", "recommendation": None},
        {"component_name": "service_b", "status": "unhealthy", "details": "Error occurred.", "recommendation": None},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "unhealthy"
    assert len(result["recommended_actions"]) == 0

def test_unknown_status():
    """Test handling of unknown status values.

    Unknown statuses do not affect overall_status, unhealthy_components, or warnings,
    but any non-empty recommendation is still surfaced in recommended_actions.
    """
    records = [
        {"component_name": "service_a", "status": "healthy", "details": "Nominal.", "recommendation": None},
        {"component_name": "service_b", "status": "critical", "details": "System down.", "recommendation": "Reboot server."},
        {"component_name": "service_c", "status": "maintenance", "details": "Undergoing maintenance.", "recommendation": ""},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "healthy"
    assert len(result["unhealthy_components"]) == 0
    assert len(result["warnings"]) == 0
    assert len(result["recommended_actions"]) == 1
    assert {"component_name": "service_b", "action": "Reboot server."} in result["recommended_actions"]

def test_multiple_recommendations_for_same_component():
    """Test that multiple recommendations for the same component are included."""
    records = [
        {"component_name": "service_a", "status": "unhealthy", "details": "Issue 1", "recommendation": "Action 1"},
        {"component_name": "service_a", "status": "warning", "details": "Issue 2", "recommendation": "Action 2"},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "unhealthy"
    assert len(result["unhealthy_components"]) == 1
    assert {"component_name": "service_a", "details": "Issue 1"} in result["unhealthy_components"]
    assert len(result["warnings"]) == 1
    assert {"component_name": "service_a", "details": "Issue 2"} in result["warnings"]
    assert len(result["recommended_actions"]) == 2
    assert {"component_name": "service_a", "action": "Action 1"} in result["recommended_actions"]
    assert {"component_name": "service_a", "action": "Action 2"} in result["recommended_actions"]

def test_non_dict_records():
    """Test that non-dict records are safely skipped."""
    records = [
        "not a dict",
        None,
        42,
        {"component_name": "service_a", "status": "healthy", "details": "OK.", "recommendation": None},
    ]
    result = generate_internal_health_summary(records)
    assert result["overall_status"] == "healthy"
    assert len(result["unhealthy_components"]) == 0
    assert len(result["warnings"]) == 0
    assert len(result["recommended_actions"]) == 0
