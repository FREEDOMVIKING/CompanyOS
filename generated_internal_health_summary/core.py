#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Dict, List


def generate_internal_health_summary(
    system_health_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generates a structured summary of system health records.

    Args:
        system_health_records: A list of dictionaries, where each dictionary
            represents a system health record.

    Returns:
        A dictionary containing the structured health summary.
    """

    if not system_health_records:
        return {
            "overall_status": "healthy",
            "unhealthy_components": [],
            "warnings": [],
            "recommended_actions": [],
            "generated_at": "N/A",
        }

    unhealthy_components: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    recommended_actions: List[Dict[str, Any]] = []

    for record in system_health_records:
        if not isinstance(record, dict):
            continue

        component_name = record.get("component_name", "unknown_component")
        status = record.get("status", "unknown")
        details = record.get("details", "")
        recommendation = record.get("recommendation", "")

        if status == "unhealthy":
            unhealthy_components.append({
                "component_name": component_name,
                "details": details,
            })
        elif status == "warning":
            warnings.append({
                "component_name": component_name,
                "details": details,
            })

        if recommendation:
            recommended_actions.append({
                "component_name": component_name,
                "action": recommendation,
            })

    overall_status = "healthy"
    if unhealthy_components:
        overall_status = "unhealthy"
    elif warnings:
        overall_status = "warning"

    return {
        "overall_status": overall_status,
        "unhealthy_components": unhealthy_components,
        "warnings": warnings,
        "recommended_actions": recommended_actions,
        "generated_at": "N/A",
    }
