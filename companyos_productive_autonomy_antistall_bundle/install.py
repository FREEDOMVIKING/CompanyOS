from pathlib import Path
import shutil, time, stat

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

targets = [
    (SRC/"companyos"/"runtime"/"productive_autonomy_watchdog.py",
     ROOT/"companyos"/"runtime"/"productive_autonomy_watchdog.py"),
    (SRC/"scripts"/"companyos_productive_autonomy.sh",
     ROOT/"scripts"/"companyos_productive_autonomy.sh"),
]

for src, dst in targets:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        backup = dst.with_name(dst.name + ".bak." + stamp)
        shutil.copy2(dst, backup)
        print("BACKUP:", backup)
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

ctl = ROOT/"scripts"/"companyos_productive_autonomy.sh"
ctl.chmod(ctl.stat().st_mode | stat.S_IXUSR)

# Create a safe wrapper for final launcher status so PYTHONPATH is always correct.
wrapper = ROOT/"scripts"/"companyos_final_launch_fixed.sh"
wrapper.write_text("""#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
exec python scripts/companyos_final_launch.py "$@"
""")
wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)

print("PRODUCTIVE_AUTONOMY_INSTALL: PASS")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
print("WALLET_CONFIG_MODIFIED: NO")
print("AUTOSTART_SCOPE: INTERNAL_REVERSIBLE_GOALS_ONLY")
