#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.5 LIVE INTEGRATION EXPORT COMPAT ====="
F="companyos/liveintegration/__init__.py"
cp "$F" "$F.v65_5_backup_$(date +%Y%m%d_%H%M%S)"
python - <<'PY'
from pathlib import Path
p=Path("companyos/liveintegration/__init__.py")
s=p.read_text()
if "ConnectorCertification" in s:
    print("CONNECTOR_CERTIFICATION_ALREADY_PRESENT=1")
else:
    candidates=[
        "companyos/liveintegration/connector_certification.py",
        "companyos/liveintegration/certification.py",
        "companyos/liveintegration/connectors.py",
    ]
    found=None
    for c in candidates:
        q=Path(c)
        if q.exists() and "ConnectorCertification" in q.read_text(errors="ignore"):
            found=c
            break
    if not found:
        hits=[]
        for q in Path("companyos/liveintegration").glob("*.py"):
            if "ConnectorCertification" in q.read_text(errors="ignore"):
                hits.append(q)
        if hits: found=str(hits[0])
    if not found:
        raise SystemExit("V65_5_ABORT=ConnectorCertification implementation not found")
    mod=found[:-3].replace("/",".")
    s += f"\n# compatibility export restored by V65.5\nfrom {mod} import ConnectorCertification\n"
    p.write_text(s)
    print("EXPORT_SOURCE="+mod)
PY
python -m py_compile "$F"
python -m pytest -q tests/test_phase8501_9000.py --disable-warnings --maxfail=1
git diff --check
echo "V65_5_LIVEINTEGRATION_EXPORT=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_5_FULL_SUITE=PASS"
