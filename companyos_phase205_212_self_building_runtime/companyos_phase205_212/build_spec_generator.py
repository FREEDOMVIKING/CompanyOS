import re

class BuildSpecGenerator:
    """206: turn a capability gap into a concrete implementation/test contract."""

    def _slug(self, value):
        value = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value)).strip("_").lower()
        return value or "new_capability"

    def generate(self, gap):
        capability = self._slug(gap.get("capability", "new_capability"))
        module = f"generated_{capability}"
        return {
            "capability": capability,
            "module_name": module,
            "files": [
                f"{module}/__init__.py",
                f"{module}/core.py",
                f"tests/test_{module}.py",
            ],
            "acceptance": [
                "python_files_compile",
                "targeted_tests_pass",
                "no_existing_tests_regress",
            ],
            "integration_policy": "verify_before_promote",
            "rollback_required": True,
            "autonomous_build": True,
        }
