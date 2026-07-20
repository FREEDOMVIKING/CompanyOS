from __future__ import annotations
import os, subprocess, tempfile, json, shlex

class ConnectionProbe:
    """231: verify configured coder command contract without modifying CompanyOS."""

    def probe(self, command):
        if not command:
            return {"success": False, "reason": "command_missing"}

        payload = {
            "task": "Return a tiny valid Python module and test.",
            "build_spec": {
                "capability": "connection_probe",
                "module_name": "generated_connection_probe",
            },
            "context": {"files": []},
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            path = f.name

        try:
            p = subprocess.run(
                shlex.split(command) + [path],
                text=True,
                capture_output=True,
                timeout=180,
                check=False,
                env=os.environ.copy(),
            )
            if p.returncode != 0:
                return {
                    "success": False,
                    "reason": "command_failed",
                    "stderr": p.stderr[-6000:],
                }
            try:
                data = json.loads(p.stdout)
            except Exception as e:
                return {
                    "success": False,
                    "reason": f"invalid_json:{e}",
                    "raw": p.stdout[-6000:],
                }
            files = data.get("files", {})
            return {
                "success": isinstance(files, dict) and bool(files),
                "file_count": len(files) if isinstance(files, dict) else 0,
            }
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass
