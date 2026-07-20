COMPANYOS PHASE 205-212 — SELF-BUILDING RUNTIME FOUNDATION

205 Capability-gap detector
206 Autonomous implementation/acceptance-spec generator
207 Real isolated filesystem build workspace
208 Real compile/test/repair verification loop
209 Git checkpoint/rollback primitives
210 Verified self-integration engine
211 Persistent queue/state/heartbeat runtime supervisor
212 Integrated Self-Building Runtime

IMPORTANT:
This bundle deliberately moves beyond status-only autonomy modules.
It uses actual filesystem copies, subprocess test execution, persistent
runtime state, Git checkpoint detection, and verified module promotion.

It does NOT claim that CompanyOS can already invent arbitrary correct code
without a coding-model/tool adapter. Phase 213-220 will connect the builder
runtime to model/tool execution and prove an end-to-end autonomous build.

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase205_212_self_building_runtime.zip .
unzip -o companyos_phase205_212_self_building_runtime.zip
bash companyos_phase205_212_self_building_runtime/install.sh ~/companyos

EXPECTED:
phase205_212_verification_passed
phase212_self_building_runtime_ready
PHASE205_212_INSTALL_OK
SELF_BUILDING_RUNTIME_FOUNDATION=TRUE
REAL_FILESYSTEM_WORKSPACE=TRUE
REAL_TEST_EXECUTION=TRUE
