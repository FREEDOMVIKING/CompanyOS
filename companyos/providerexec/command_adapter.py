import subprocess

class CommandProviderAdapter:
    name="command_local"
    capabilities=["command","deploy"]
    live_supported=True

    def execute(self, request, timeout=60, live=False):
        command=request.get("command")
        if not live:
            return {"success":True,"simulated":True,"adapter":self.name,"command":command}
        if not isinstance(command,list) or not command:
            return {"success":False,"error_kind":"bad_input","error":"command must be a non-empty argument list"}
        try:
            p=subprocess.run(command,capture_output=True,text=True,timeout=timeout,check=False)
            return {
                "success":p.returncode==0,
                "returncode":p.returncode,
                "stdout":p.stdout[-10000:],
                "stderr":p.stderr[-10000:],
                "adapter":self.name
            }
        except subprocess.TimeoutExpired:
            return {"success":False,"error_kind":"timeout","error":"command timeout","adapter":self.name}
        except Exception as e:
            return {"success":False,"error_kind":"command_error","error":str(e),"adapter":self.name}
