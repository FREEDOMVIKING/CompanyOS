COMPANYOS PHASE 229-236 — MODEL CONNECTION + HANDOFF

229 Provider configuration persistence
230 Coder command builder
231 Connection-contract probe
232 Genuine model-backed self-build mission runner
233 Persistent model self-build queue/heartbeat
234 Append-only self-build audit log
235 Autonomous handoff readiness controller
236 Model-connected self-building runtime status

This bundle prepares the actual connection point to a coding/reasoning model.
It stays provider-neutral rather than hardcoding one vendor.

To activate real model-written self-building:
1. Configure a provider adapter command in COMPANYOS_PROVIDER_ADAPTER_CMD.
2. Export:
   COMPANYOS_CODER_CMD="python ~/companyos/scripts/companyos_coder_adapter.py"
3. Probe the connection.
4. Run one genuine self-build mission through Phase 228.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase229_236_model_connection.zip .
unzip -o companyos_phase229_236_model_connection.zip
bash companyos_phase229_236_model_connection/install.sh ~/companyos

EXPECTED:
phase229_236_verification_passed
phase236_model_connection_layer_ready
PHASE229_236_INSTALL_OK
MODEL_CONNECTION_LAYER=READY
