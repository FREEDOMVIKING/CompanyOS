from __future__ import annotations
from pathlib import Path
import subprocess, time

class GitTransaction:
    """224: safe local git transaction/checkpoint/commit primitives."""

    def _git(self,root,*args):
        return subprocess.run(["git",*args],cwd=str(root),text=True,capture_output=True,check=False)

    def available(self,root):
        root=Path(root)
        return self._git(root,"rev-parse","--is-inside-work-tree").returncode==0

    def begin(self,root):
        root=Path(root)
        if not self.available(root):
            return {"available":False,"checkpoint":None}
        p=self._git(root,"rev-parse","HEAD")
        return {"available":True,"checkpoint":p.stdout.strip() if p.returncode==0 else None}

    def commit_all(self,root,message):
        root=Path(root)
        if not self.available(root):
            return {"committed":False,"reason":"git_unavailable"}
        self._git(root,"add","-A")
        p=self._git(root,"commit","-m",message)
        if p.returncode!=0 and "nothing to commit" in (p.stdout+p.stderr).lower():
            return {"committed":True,"noop":True}
        return {"committed":p.returncode==0,"stdout":p.stdout[-4000:],"stderr":p.stderr[-4000:]}

    def rollback(self,root,checkpoint):
        root=Path(root)
        if not checkpoint or not self.available(root):
            return {"rolled_back":False,"reason":"checkpoint_unavailable"}
        p=self._git(root,"reset","--hard",checkpoint)
        return {"rolled_back":p.returncode==0,"stderr":p.stderr[-4000:]}
