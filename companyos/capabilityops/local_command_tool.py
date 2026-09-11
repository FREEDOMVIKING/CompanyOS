import subprocess

class LocalCommandTool:
    def run(self, command, timeout=60):
        if not isinstance(command, list) or not command:
            return {"success":False,"error":"command_must_be_list"}
        try:
            p=subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            return {
                "success":p.returncode==0,
                "returncode":p.returncode,
                "stdout":p.stdout[-10000:],
                "stderr":p.stderr[-10000:]
            }
        except Exception as e:
            return {"success":False,"error":type(e).__name__,"message":str(e)}
