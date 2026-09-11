from __future__ import annotations

from pathlib import Path
import os

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_solana_execution_engine import LiveSolanaExecutionEngine
from companyos.walletintegration.production_execution_coordinator import ProductionExecutionCoordinator
from companyos.walletintegration.execution_policy import ExecutionPolicy, ExecutionAuditLedger
from companyos.walletintegration.controlled_production_sol_gateway import ControlledProductionSolGateway
from companyos.walletintegration.live_execution_control import LiveExecutionControl
from companyos.walletintegration.autonomous_financial_execution_bridge import AutonomousFinancialExecutionBridge


def build_autonomous_financial_bridge() -> AutonomousFinancialExecutionBridge:
    material = load_signer_material(
        os.environ["SOLANA_PRIVATE_KEY"],
        os.getenv("SOLANA_PRIVATE_KEY_ENCODING", "auto"),
    )

    reserve = float(os.getenv("COMPANYOS_SOL_RESERVE_SOL", "0.01"))

    # Engine can support broadcast, but the bridge still requires explicit
    # per-action live authorization before allow_broadcast=True reaches it.
    engine = LiveSolanaExecutionEngine(
        rpc_url=os.environ["SOLANA_RPC_URL"],
        secret=os.environ["SOLANA_PRIVATE_KEY"],
        encoding=os.getenv("SOLANA_PRIVATE_KEY_ENCODING", "auto"),
        wallet_address=material.public_address,
        reserve_sol=reserve,
        broadcast_enabled=True,
    )

    gateway = ControlledProductionSolGateway(
        coordinator=ProductionExecutionCoordinator(engine=engine),
        wallet_address=material.public_address,
        policy=ExecutionPolicy(
            daily_cap_sol=float(os.getenv("COMPANYOS_SOL_DAILY_CAP_SOL", "200")),
            single_cap_sol=float(os.getenv("COMPANYOS_SOL_SINGLE_CAP_SOL", "150")),
            minimum_transfer_sol=float(os.getenv("COMPANYOS_SOL_MIN_TRANSFER_SOL", "0.000001")),
            reserve_sol=reserve,
            require_destination_allowlist=os.getenv(
                "COMPANYOS_SOL_REQUIRE_ALLOWLIST", "false"
            ).lower() == "true",
            allow_self_transfer=os.getenv(
                "COMPANYOS_SOL_ALLOW_SELF_TRANSFER", "true"
            ).lower() == "true",
        ),
        ledger=ExecutionAuditLedger(),
        allowlist_path=Path("config/solana_destination_allowlist.json"),
    )

    control = LiveExecutionControl(
        required_token=os.getenv("COMPANYOS_LIVE_CONFIRM_TOKEN", "")
    )

    return AutonomousFinancialExecutionBridge(
        gateway=gateway,
        live_control=control,
    )
