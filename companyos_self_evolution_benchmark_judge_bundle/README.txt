COMPANYOS SELF-EVOLUTION BENCHMARK JUDGE

Purpose
-------
Add the missing quality gate after successful self-evolution promotion.

It evaluates:
- runtime running/ready state
- failed/halted orchestrations
- candidate pool breadth
- sector diversity
- business-model diversity
- qualified opportunity count
- runtime health issues
- compile/import/test success

Decision:
KEEP
or
ROLLBACK_RECOMMENDED

This version records rollback recommendations rather than directly reverting
working promoted extensions. Automatic destructive rollback remains governed by
the existing promotion engine health protections.

INSTALL
-------
cd ~/companyos || exit 1

rm -rf companyos_self_evolution_benchmark_judge_bundle
mkdir -p companyos_self_evolution_benchmark_judge_bundle

unzip -o ~/storage/downloads/COMPANYOS_SELF_EVOLUTION_BENCHMARK_JUDGE_BUNDLE.zip   -d ~/companyos/companyos_self_evolution_benchmark_judge_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_benchmark_judge_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_self_evolution_benchmark_judge_bundle/verify.py

RUN ONCE
--------
bash scripts/companyos_self_evolution_benchmark.sh once

START CONTINUOUSLY
------------------
bash scripts/companyos_self_evolution_benchmark.sh start

STATUS
------
bash scripts/companyos_self_evolution_benchmark.sh status

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_self_evolution_benchmark_status.py
