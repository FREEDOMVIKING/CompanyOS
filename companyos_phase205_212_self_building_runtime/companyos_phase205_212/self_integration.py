from pathlib import Path
import shutil

class SelfIntegrationEngine:
    """210: promote verified generated modules from isolation into live project."""

    def integrate(self, workspace, project_root, module_name, verification):
        if not verification.get("success"):
            return {"integrated": False, "reason": "verification_failed"}

        src_root = Path(workspace)
        dst_root = Path(project_root)
        src = src_root / module_name
        if not src.exists() or not src.is_dir():
            return {"integrated": False, "reason": "generated_module_missing"}

        dst = dst_root / module_name
        backup = None
        if dst.exists():
            backup = dst_root / "backups" / "selfbuild_integration" / module_name
            backup.parent.mkdir(parents=True, exist_ok=True)
            if backup.exists():
                shutil.rmtree(backup)
            shutil.copytree(dst, backup)
            shutil.rmtree(dst)

        shutil.copytree(src, dst)

        src_test = src_root / "tests" / f"test_{module_name}.py"
        if src_test.exists():
            (dst_root / "tests").mkdir(exist_ok=True)
            shutil.copy2(src_test, dst_root / "tests" / src_test.name)

        return {
            "integrated": True,
            "module": module_name,
            "backup": str(backup) if backup else None,
        }
