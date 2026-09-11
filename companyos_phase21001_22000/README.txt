CompanyOS Phase 21001-22000
PERSISTENT AUTONOMY + TREASURY SAFETY KERNEL

This bundle adds the missing long-running runtime layer plus a safe money-control kernel.

Persistent autonomy:
- daemonized multi-cycle operation
- checkpoint after every cycle
- status/start/stop/restart/log controls
- crash/restart-friendly durable state

Treasury safety:
- per-transaction autonomous limit
- daily autonomous spend limit
- reserve floor
- max daily loss guard
- destination allowlist
- append-only decision/execution ledger
- reconciliation support

IMPORTANT:
Real money movement is DISABLED BY DEFAULT.
This package does not contain private keys, bank credentials, or a transfer connector.

To enable real autonomous transfers later, connect a specific bank/wallet/payment provider
through a dedicated execution connector and explicitly set:
  COMPANYOS_ALLOW_AUTONOMOUS_TRANSFERS=true

Only do that after configuring:
  COMPANYOS_AUTONOMOUS_SINGLE_TX_LIMIT
  COMPANYOS_AUTONOMOUS_DAILY_LIMIT
  COMPANYOS_TREASURY_RESERVE_FLOOR
  COMPANYOS_MAX_DAILY_LOSS
  destination allowlists

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_AUTONOMOUS_TREASURY_22000.zip .
unzip -o CompanyOS_AUTONOMOUS_TREASURY_22000.zip
bash companyos_phase21001_22000/install.sh ~/companyos

START AUTONOMY:
bash ~/companyos/scripts/companyos_runtime_control.sh start

STATUS:
bash ~/companyos/scripts/companyos_runtime_control.sh status

LOGS:
bash ~/companyos/scripts/companyos_runtime_control.sh logs

CHECKPOINT:
bash ~/companyos/scripts/companyos_runtime_control.sh checkpoint

TREASURY STATUS:
bash ~/companyos/scripts/companyos_treasury.sh status
