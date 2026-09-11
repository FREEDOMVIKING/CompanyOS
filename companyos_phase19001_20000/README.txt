CompanyOS Phase 19001-20000
CONTINUOUS AUTONOMY LAYER

Builds on the verified Phase 19000 cycle closure.

Adds:
- autonomous objective selection
- priority scoring/ranking
- persistent autonomy-cycle memory
- continuous internal autonomy loop
- automatic next-cycle decisioning

This does not bypass approval boundaries.
External consequential actions remain approval-gated.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_AUTONOMY_LAYER_20000.zip .
unzip -o CompanyOS_AUTONOMY_LAYER_20000.zip
bash companyos_phase19001_20000/install.sh ~/companyos

VERIFY:
bash ~/companyos/scripts/companyos_autonomy.sh verify

RUN ONE AUTONOMOUS CYCLE:
bash ~/companyos/scripts/companyos_autonomy.sh run --cycles 1

RUN THREE AUTONOMOUS CYCLES:
bash ~/companyos/scripts/companyos_autonomy.sh run --cycles 3
