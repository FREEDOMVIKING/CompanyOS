COMPANYOS FULL SYSTEM CHECK

READ-ONLY DIAGNOSTIC:
- Does not modify CompanyOS logic.
- Does not take external, financial, or irreversible actions.
- Copies only the diagnostic checker into scripts/.
- Compiles Python files for syntax errors.
- Detects installed phase markers.
- Runs each available phase verification script.
- Runs pytest if pytest is already installed.
- Writes FULL_SYSTEM_CHECK_REPORT.json in ~/companyos.

TERMUX:
cd ~/companyos
cp /sdcard/Download/companyos_full_system_check.zip .
unzip -o companyos_full_system_check.zip
bash companyos_full_system_check/run_check.sh ~/companyos

GOOD RESULT:
"success": true
"status": "full_system_check_passed"

If it fails, send a screenshot of the bottom of the output and the failed_checks list.
