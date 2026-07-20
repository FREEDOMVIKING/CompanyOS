from __future__ import annotations
import json, os, shlex, subprocess, tempfile
from pathlib import Path

class CoderBridge:
    """222: invoke an external coding model command.

    Configure COMPANYOS_CODER_CMD. The command receives one prompt JSON path
    argument and must print JSON: {"files": {"relative/path.py": "content"}}.
    """

    def __init__(self, command=None):
        self.command=(command or os.environ.get("COMPANYOS_CODER_CMD","")).strip()

    @property
    def configured(self):
        return bool(self.command)

    def invoke(self, payload):
        if not self.configured:
            return {"success":False,"reason":"external_coder_not_configured","files":{}}

        with tempfile.NamedTemporaryFile("w",suffix=".json",delete=False) as f:
            json.dump(payload,f,indent=2)
            prompt_path=f.name
        try:
            p=subprocess.run(
                shlex.split(self.command)+[prompt_path],
                text=True,capture_output=True,timeout=600,check=False
            )
            if p.returncode!=0:
                return {"success":False,"reason":"coder_failed","stderr":p.stderr[-12000:],"files":{}}
            try:
                data=json.loads(p.stdout)
            except Exception as e:
                return {"success":False,"reason":f"invalid_json:{e}","raw":p.stdout[-12000:],"files":{}}
            files=data.get("files",{})
            return {"success":isinstance(files,dict) and bool(files),"files":files,"metadata":data.get("metadata",{})}
        finally:
            Path(prompt_path).unlink(missing_ok=True)
