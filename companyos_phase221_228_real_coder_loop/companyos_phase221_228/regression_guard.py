from __future__ import annotations
import subprocess, sys
from pathlib import Path

class RegressionGuard:
    """225: require targeted + full regression tests after live integration."""

    def run(self,project_root,targeted_test=None):
        root=Path(project_root)
        results={}
        if targeted_test:
            p=subprocess.run([sys.executable,"-m","pytest","-q",targeted_test,"--disable-warnings"],
                             cwd=str(root),text=True,capture_output=True,timeout=300,check=False)
            results["targeted"]={"passed":p.returncode==0,"stdout":p.stdout[-8000:],"stderr":p.stderr[-8000:]}
            if p.returncode!=0:
                return {"success":False,"results":results}
        p=subprocess.run([sys.executable,"-m","pytest","-q","tests","--disable-warnings"],
                         cwd=str(root),text=True,capture_output=True,timeout=600,check=False)
        results["full"]={"passed":p.returncode==0,"stdout":p.stdout[-12000:],"stderr":p.stderr[-12000:]}
        return {"success":p.returncode==0,"results":results}
