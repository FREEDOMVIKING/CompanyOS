import os, shlex, subprocess, json

class SignerProbe:
    def inspect(self):
        cmd = os.getenv("MULTICHAIN_SIGNER_COMMAND", "").strip()
        return {
            "configured": bool(cmd),
            "command_exposed": False,
            "supports_probe": bool(cmd),
        }

    def probe(self):
        cmd = os.getenv("MULTICHAIN_SIGNER_COMMAND", "").strip()
        if not cmd:
            return {"success":False,"status":"signer_command_missing"}

        probe_payload = {
            "action":"probe",
            "chain":"solana",
            "message":"companyos_signer_probe",
            "broadcast":False,
        }

        try:
            p = subprocess.run(
                shlex.split(cmd),
                input=json.dumps(probe_payload),
                text=True,
                capture_output=True,
                timeout=20,
            )
            stdout = (p.stdout or "").strip()
            stderr = (p.stderr or "").strip()
            result = None
            if stdout:
                try:
                    result = json.loads(stdout)
                except Exception:
                    result = {"raw":stdout[:1000]}
            return {
                "success": p.returncode == 0,
                "status":"signer_probe_complete" if p.returncode == 0 else "signer_probe_failed",
                "returncode":p.returncode,
                "result":result,
                "stderr_present":bool(stderr),
                "command_exposed":False,
            }
        except Exception as exc:
            return {
                "success":False,
                "status":"signer_probe_exception",
                "error":type(exc).__name__,
                "message":str(exc),
                "command_exposed":False,
            }
