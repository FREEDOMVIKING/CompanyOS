from __future__ import annotations
from pathlib import Path

class RepairController:
    """Failure-aware repair controller with current-code context."""

    def collect_generated_files(self, workspace, module_name, targeted_test=None):
        root = Path(workspace)
        candidates = []

        package = root / module_name
        if package.exists():
            candidates.extend(p for p in package.rglob("*") if p.is_file())

        single_module = root / f"{module_name}.py"
        if single_module.exists():
            candidates.append(single_module)

        if targeted_test:
            test_path = root / targeted_test
            if test_path.exists():
                candidates.append(test_path)

        result = {}
        seen = set()
        for p in candidates:
            try:
                rel = str(p.relative_to(root))
            except Exception:
                continue
            if rel in seen:
                continue
            seen.add(rel)
            try:
                result[rel] = p.read_text(encoding="utf-8")
            except Exception:
                pass
        return result

    def make_prompt(
        self,
        original_payload,
        verification,
        attempt,
        workspace=None,
        module_name=None,
        targeted_test=None,
    ):
        current_files = {}
        if workspace and module_name:
            current_files = self.collect_generated_files(
                workspace, module_name, targeted_test=targeted_test
            )

        return {
            **original_payload,
            "repair_mode": True,
            "repair_attempt": int(attempt),
            "failure_evidence": verification,
            "current_generated_files": current_files,
            "required_layout": {
                "package_directory": module_name,
                "package_init": f"{module_name}/__init__.py" if module_name else None,
                "implementation": f"{module_name}/core.py" if module_name else None,
                "targeted_test": targeted_test,
            },
            "repair_instructions": [
                "Diagnose the exact root cause from failure stdout/stderr.",
                "Inspect current_generated_files before changing anything.",
                "Return complete contents for every file you change.",
                "Keep the required package layout exactly as specified.",
                "Do not replace the package with a single top-level .py file.",
                "Do not weaken or delete tests merely to force a pass.",
                "Make implementation and tests agree on one explicit data contract.",
                "Handle missing keys, None values, empty input, and malformed records safely.",
                "Preserve unrelated working behavior.",
                "Return only the files JSON contract.",
            ],
        }
