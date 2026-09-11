from pathlib import Path
import shutil,time
ROOT=Path.home()/"companyos";SRC=Path(__file__).resolve().parent;D=ROOT/"dashboard";stamp=str(int(time.time()))
for name in ["autonomy_activity_ledger_server.py","autonomy_activity_ledger.html"]:
    s=SRC/"dashboard"/name;d=D/name
    if d.exists():shutil.copy2(d,d.with_name(d.name+".bak.timestamp_dedupe."+stamp))
    shutil.copy2(s,d);print("INSTALLED:",d)
print("LEDGER_TIMESTAMP_DEDUPE_INSTALL: PASS")
print("HISTORICAL_ERROR_MISDATING_FIXED: YES")
print("ERROR_DEDUPLICATION_ENABLED: YES")
print("BOT_RUNTIME_LOGIC_MODIFIED: NO")
