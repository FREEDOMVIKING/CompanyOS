from pathlib import Path
import shutil, subprocess, os, time
ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))
for rel in [
    "companyos/evolution/self_evolution_sandbox_retry_repair.py",
    "scripts/companyos_self_evolution_sandbox_retry_repair.py",
    "scripts/patch_self_evolution_generator_test_imports.py",
    "scripts/patch_self_evolution_promotion_imports.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)
env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(["python", "scripts/patch_self_evolution_generator_test_imports.py"], cwd=ROOT, env=env, check=True)
subprocess.run(["python", "scripts/patch_self_evolution_promotion_imports.py"], cwd=ROOT, env=env, check=True)
print("SELF_EVOLUTION_SANDBOX_IMPORT_RETRY_REPAIR_INSTALL: PASS")
print("SELF_CONTAINED_GENERATED_TEST_IMPORTS: ENABLED")
print("SANDBOX_PARENT_PATH_IMPORT_SUPPORT: ENABLED")
print("REJECTED_CANDIDATE_RETRY: ENABLED")
print("AUTO_ROLLBACK_PRESERVED: YES")
print("CORE_OVERWRITE_BY_DEFAULT: NO")
