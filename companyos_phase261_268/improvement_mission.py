from __future__ import annotations

class ImprovementMission:
    """264: create a strict internal-only autonomous improvement mission."""

    def create(self, mapped):
        capability = mapped["capability"]
        module = mapped["module_name"]

        return {
            "objective": (
                f"Build or improve the internal CompanyOS capability '{capability}' "
                "without performing external or financial actions."
            ),
            "requirements": [
                f"Create package {module}",
                f"Use {module}/__init__.py",
                f"Use {module}/core.py",
                "Expose one clear public function",
                "Handle empty and malformed inputs safely",
                "Return structured Python data",
                "Include meaningful pytest coverage",
                "No network access",
                "No financial actions",
                "No external actions",
                "Do not modify unrelated behavior",
            ],
            "internal_only": True,
            "capability": capability,
            "module_name": module,
        }
