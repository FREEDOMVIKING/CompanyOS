from pathlib import Path
import subprocess, sys

class BuildTestRepairLoop:
    """208: execute compile/tests and produce bounded repair instructions."""

    def _run(self, cmd, cwd, timeout=120):
        p = subprocess.run(
            cmd, cwd=str(cwd), text=True, capture_output=True,
            timeout=timeout, check=False
        )
        return {
            "returncode": p.returncode,
            "stdout": p.stdout[-12000:],
            "stderr": p.stderr[-12000:],
            "passed": p.returncode == 0,
        }

    def verify(self, workspace, targeted_test=None):
        root = Path(workspace)
        compile_result = self._run(
            [sys.executable, "-m", "compileall", "-q", "."], root
        )
        if not compile_result["passed"]:
            return {
                "success": False,
                "stage": "compile",
                "result": compile_result,
                "repair_action": "diagnose_compile_error_and_patch",
            }

        test_cmd = [sys.executable, "-m", "pytest", "-q", "--disable-warnings"]
        if targeted_test:
            test_cmd.append(str(targeted_test))
        tests = self._run(test_cmd, root)
        return {
            "success": tests["passed"],
            "stage": "tests",
            "result": tests,
            "repair_action": None if tests["passed"] else "diagnose_test_failure_and_patch",
        }

    def bounded_cycle(self, workspace, repair_callback=None, max_attempts=3, targeted_test=None):
        history = []
        for attempt in range(1, max(1, int(max_attempts)) + 1):
            result = self.verify(workspace, targeted_test)
            history.append({"attempt": attempt, **result})
            if result["success"]:
                return {"success": True, "attempts": attempt, "history": history}
            if repair_callback is None:
                break
            repair_callback(workspace, result)
        return {"success": False, "attempts": len(history), "history": history}
