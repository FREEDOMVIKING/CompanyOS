COMPANYOS PHASE 213-220 — AUTONOMOUS SELF-BUILD PIPELINE

213 Pluggable coding/reasoning model adapter
214 Bounded local tool executor
215 Autonomous code materialization
216 Model-driven repair-agent interface
217 Final live integration gate
218 Persistent verified-capability registry
219 Traceable self-build missions
220 End-to-end autonomous self-builder

WHAT THIS PROVES
- A capability gap can be converted into a build spec.
- Code can be generated into a real isolated filesystem workspace.
- Real pytest execution validates the generated code.
- Verified code can be promoted into the live project.
- The live project can be tested after integration.
- Successfully built capabilities are persisted in a registry.

HONEST LIMIT
A real external coding/reasoning model is not magically bundled in this ZIP.
The verification uses a deterministic scaffold adapter to prove the pipeline.
For arbitrary self-written code, configure COMPANYOS_CODER_CMD with a coding
model/provider command that accepts a JSON prompt-file path and prints:
  {"files": {"relative/path.py": "file contents"}}

INSTALL
cd ~/companyos
cp /sdcard/Download/companyos_phase213_220_autonomous_self_build.zip .
unzip -o companyos_phase213_220_autonomous_self_build.zip
bash companyos_phase213_220_autonomous_self_build/install.sh ~/companyos

EXPECTED
phase213_220_verification_passed
phase220_autonomous_self_build_pipeline_completed
PHASE213_220_INSTALL_OK
AUTONOMOUS_SELF_BUILD_PIPELINE=TRUE

If COMPANYOS_CODER_CMD is not yet configured, the installer will truthfully show:
EXTERNAL_CODER_ADAPTER=NOT_CONFIGURED
