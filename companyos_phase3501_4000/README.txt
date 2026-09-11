CompanyOS Phase 3501-4000 — Autonomous Venture Factory

Install:
cd ~/companyos
cp /sdcard/Download/companyos_phase3501_4000_autonomous_venture_factory.zip .
unzip -o companyos_phase3501_4000_autonomous_venture_factory.zip
bash companyos_phase3501_4000/install.sh ~/companyos

Demo:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_phase4000_venture_factory_demo.py

Control:
bash ~/companyos/scripts/companyos_venture_factory.sh status
bash ~/companyos/scripts/companyos_venture_factory.sh cycle
bash ~/companyos/scripts/companyos_venture_factory.sh verify
