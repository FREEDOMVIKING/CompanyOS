from pathlib import Path
home=Path.home()/"companyos"
ctl=home/"companyosctl"
if not ctl.exists():
    raise SystemExit("Missing ~/companyos/companyosctl")
text=ctl.read_text()
marker="# COMPANYOS_STABILITY_REPAIR_43OF43"
if marker in text:
    print("companyosctl stability commands already installed.")
    raise SystemExit(0)

block = '''# COMPANYOS_STABILITY_REPAIR_43OF43
if [ "${1:-}" = "status-snapshot" ]; then
  python -m companyos.controlplane.dashboard status > "$HOME/companyos_status.txt" 2>&1 || true
  exit 0
fi
if [ "${1:-}" = "status-lite" ]; then
  python -m companyos.controlplane.dashboard status > "$HOME/companyos_status.txt" 2>&1 || true
  python -m companyos.stability_tools.status_cli lite
  exit 0
fi
if [ "${1:-}" = "failed" ]; then
  [ -f "$HOME/companyos_status.txt" ] || python -m companyos.controlplane.dashboard status > "$HOME/companyos_status.txt" 2>&1 || true
  python -m companyos.stability_tools.status_cli failed
  exit 0
fi
if [ "${1:-}" = "diagnostics" ]; then
  python -m companyos.stability_tools.status_cli diagnostics
  exit 0
fi
'''

lines=text.splitlines()
updated=(lines[0]+"\n"+block+"\n"+"\n".join(lines[1:])+"\n") if lines and lines[0].startswith("#!") else block+"\n"+text
backup=ctl.with_name("companyosctl.before_stability_repair")
if not backup.exists():backup.write_text(text)
ctl.write_text(updated)
ctl.chmod(0o755)
print("Added status-lite, failed, diagnostics, and status-snapshot.")
