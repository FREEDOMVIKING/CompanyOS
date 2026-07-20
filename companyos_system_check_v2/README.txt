COMPANYOS SYSTEM CHECK V2

Fixes the previous false syntax failure by excluding:
- backups/
- .git/
- venv/.venv
- site-packages
- __pycache__
- test/tool caches

Also runs:
- active Python syntax compilation
- every installed Phase 53-124 verification script
- pytest against tests/ when pytest is installed

INSTALL/RUN:
cd ~/companyos
cp /sdcard/Download/companyos_system_check_v2.zip .
unzip -o companyos_system_check_v2.zip
bash companyos_system_check_v2/run_check.sh ~/companyos

EXPECTED:
Python syntax: PASS
Phase 53_60 through 117_124: PASS
Pytest: PASS
"success": true
"status": "full_system_check_passed"
"failed_checks": []
