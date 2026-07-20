from pathlib import Path
import shutil, tempfile

class IsolatedWorkspace:
    """207: create disposable copies for autonomous code changes."""

    def create(self, project_root):
        source = Path(project_root).resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        parent = Path(tempfile.mkdtemp(prefix="companyos_selfbuild_"))
        target = parent / "workspace"
        ignore = shutil.ignore_patterns(
            ".git", "backups", "__pycache__", ".pytest_cache",
            ".venv", "venv", "node_modules", "*.pyc"
        )
        shutil.copytree(source, target, ignore=ignore)
        return {"workspace": str(target), "container": str(parent), "isolated": True}

    def destroy(self, container):
        path = Path(container)
        if path.exists():
            shutil.rmtree(path)
        return {"destroyed": not path.exists()}
