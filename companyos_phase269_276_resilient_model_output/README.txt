COMPANYOS PHASE 269-276
RESILIENT MODEL OUTPUT + AUTOMATIC CONTRACT RECOVERY

269 Response extractor
270 JSON/near-JSON recovery
271 Alternate contract repair
272 Output diagnostics
273 Strict automatic format-retry prompts
274 Resilient OpenRouter adapter
275 Resilient autonomous BuilderBridge
276 Resilient generation runtime/status

This bundle fixes the failure observed in the first autonomous improvement
cycle where the model returned content that failed the strict JSON contract.

It adds recovery for:
- markdown fenced JSON
- prose around JSON
- single-quoted Python-like dicts
- trailing commas
- alternate "artifacts" file lists

If recovery still fails, CompanyOS automatically retries the model with a
strict format-repair prompt before declaring generation failed.

The installer also rewires Phase 267's AutonomousImprover to use the new
resilient generation bridge.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase269_276_resilient_model_output.zip .
unzip -o companyos_phase269_276_resilient_model_output.zip
bash companyos_phase269_276_resilient_model_output/install.sh ~/companyos

EXPECTED:
phase269_276_verification_passed
phase276_resilient_generation_runtime_ready
4 passed
PHASE269_276_INSTALL_OK
RESILIENT_MODEL_OUTPUT=READY
AUTONOMOUS_IMPROVER_REWIRED=TRUE

NEXT:
Rerun:
PYTHONPATH="$HOME/companyos:$HOME/companyos/src" python ~/companyos/scripts/run_autonomous_improvement_once.py
