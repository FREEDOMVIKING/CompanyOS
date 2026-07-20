COMPANYOS PHASE 253-260 REPAIR UPGRADE

Upgrades the first real autonomous self-build repair loop.

Before:
- failure evidence was sent back,
- current generated code/tests were not included,
- the model could effectively start over,
- required package layout was not enforced.

After:
- exact failure output remains available,
- current generated implementation/tests are included in repair prompts,
- required package layout is explicit and verified before pytest,
- repairs are instructed to fix root cause instead of weakening tests,
- None/missing/malformed input handling is explicitly requested.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase253_260_repair_upgrade.zip .
unzip -o companyos_phase253_260_repair_upgrade.zip
bash companyos_phase253_260_repair_upgrade/install.sh ~/companyos
