CompanyOS Phase 7001-7500
REAL-WORLD CONNECTOR + CAPABILITY LAYER

This 500-phase push adds:
- connector registry
- credential-safe environment-variable references
- connector health scoring and routing
- capability discovery
- research adapter
- communication adapter
- deployment adapter
- finance read/write action adapters
- generic API adapter
- approval routing for consequential external writes
- provider fallback
- execution receipts
- persistent connector state/audit
- unified CEO connector controller

INSTALL:
cd ~/companyos
cp /sdcard/Download/companyos_phase7001_7500_real_world_connector_capability_layer.zip .
unzip -o companyos_phase7001_7500_real_world_connector_capability_layer.zip
bash companyos_phase7001_7500/install.sh ~/companyos

RUN:
bash ~/companyos/scripts/companyos_connectors.sh status
bash ~/companyos/scripts/companyos_connectors.sh verify
bash ~/companyos/scripts/companyos_connectors.sh cycle
