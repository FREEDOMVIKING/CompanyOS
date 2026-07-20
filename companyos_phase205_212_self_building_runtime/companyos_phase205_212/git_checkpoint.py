from pathlib import Path
import subprocess

class GitCheckpointManager:
    """209: create/restore local Git checkpoints when a repository is available."""

    def _git(self, root, *args):
        return subprocess.run(
            ["git", *args], cwd=str(root), text=True,
            capture_output=True, check=False
        )

    def available(self, project_root):
        root = Path(project_root)
        return root.exists() and self._git(root, "rev-parse", "--is-inside-work-tree").returncode == 0

    def checkpoint(self, project_root):
        root = Path(project_root)
        if not self.available(root):
            return {"available": False, "checkpoint": None}
        p = self._git(root, "rev-parse", "HEAD")
        return {"available": True, "checkpoint": p.stdout.strip() if p.returncode == 0 else None}

    def restore(self, project_root, checkpoint):
        root = Path(project_root)
        if not checkpoint or not self.available(root):
            return {"restored": False, "reason": "git_checkpoint_unavailable"}
        p = self._git(root, "reset", "--hard", checkpoint)
        return {"restored": p.returncode == 0, "stderr": p.stderr[-4000:]}
