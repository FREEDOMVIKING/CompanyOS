COMPANYOS PHASE 245-252 — LIVE PROVIDER BRIDGE

245 Provider profile persistence
246 Provider-response normalization
247 Provider-neutral HTTP JSON adapter
248 Real provider probe
249 Prompt-file mission launcher
250 Provider health assessment
251 Persistent activation state
252 Live provider runtime

This is the point where CompanyOS can connect to a REAL coding endpoint,
without hardcoding a vendor-specific API.

Required for live activation:
  COMPANYOS_PROVIDER_ENDPOINT
  COMPANYOS_PROVIDER_MODEL
Optional:
  COMPANYOS_CODER_API_KEY

Then:
  export COMPANYOS_CODER_CMD="python ~/companyos/scripts/companyos_http_coder_adapter.py"

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase245_252_live_provider_bridge.zip .
unzip -o companyos_phase245_252_live_provider_bridge.zip
bash companyos_phase245_252_live_provider_bridge/install.sh ~/companyos

EXPECTED:
phase245_252_verification_passed
phase252_live_provider_runtime_ready
PHASE245_252_INSTALL_OK
LIVE_PROVIDER_BRIDGE=READY
