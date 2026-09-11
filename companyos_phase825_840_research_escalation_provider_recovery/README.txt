COMPANYOS PHASE 825-840
AUTONOMOUS RESEARCH ESCALATION + PROVIDER FAILURE RECOVERY

Purpose:
- escalate failed providers automatically
- reformulate weak research queries
- analyze missing evidence
- accumulate evidence across providers
- track confidence improvement
- enforce bounded retry budgets/backoff
- promote research when quality threshold is reached
- otherwise defer cleanly instead of retry-looping forever

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase825_840_research_escalation_provider_recovery.zip .
unzip -o companyos_phase825_840_research_escalation_provider_recovery.zip
bash companyos_phase825_840_research_escalation_provider_recovery/install.sh ~/companyos

EXPECTED:
phase825_840_verification_passed
phase840_research_escalation_provider_recovery_ready
3 passed
PHASE825_840_INSTALL_OK

DEMO:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_research_escalation_demo.py
