from pathlib import Path

class CapabilityGapDetector:
    """205: detect missing capabilities from goals, registry, and filesystem."""

    def detect(self, goals, capabilities, project_root=None):
        available = set(capabilities or [])
        gaps = []
        for goal in goals or []:
            for required in goal.get("required_capabilities", []):
                if required not in available:
                    gaps.append({
                        "capability": required,
                        "reason": f"required_by:{goal.get('goal','unknown')}",
                        "priority": float(goal.get("priority", .7)),
                        "autonomous_build_candidate": True,
                    })

        if project_root:
            root = Path(project_root)
            if not (root / "tests").exists():
                gaps.append({
                    "capability": "test_infrastructure",
                    "reason": "tests_directory_missing",
                    "priority": 1.0,
                    "autonomous_build_candidate": True,
                })

        unique = {}
        for gap in gaps:
            key = gap["capability"]
            if key not in unique or gap["priority"] > unique[key]["priority"]:
                unique[key] = gap
        return sorted(unique.values(), key=lambda x: x["priority"], reverse=True)
