from pathlib import Path
ctl=Path.home()/"companyos"/"companyosctl"
if not ctl.exists():raise SystemExit("Missing companyosctl")
text=ctl.read_text();marker="# COMPANYOS_LOGS_FIX_60001"
if marker in text:
    print("Logs fix already installed.");raise SystemExit(0)
block = """# COMPANYOS_LOGS_FIX_60001
if [ "${1:-}" = "logs" ]; then
  if [ -f "$HOME/companyos/logs/supervisor_18301_18400.log" ]; then
    tail -n 100 -f "$HOME/companyos/logs/supervisor_18301_18400.log"
  else
    find "$HOME/companyos/logs" -maxdepth 1 -type f -name "*.log" -print | sort
  fi
  exit 0
fi
"""
lines=text.splitlines();updated=lines[0]+"\n"+block+"\n"+"\n".join(lines[1:])+"\n" if lines and lines[0].startswith("#!") else block+"\n"+text
ctl.write_text(updated);ctl.chmod(0o755);print("Fixed companyosctl logs.")
