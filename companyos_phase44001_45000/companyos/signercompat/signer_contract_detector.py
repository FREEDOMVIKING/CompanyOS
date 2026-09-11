import os
from pathlib import Path

class SignerContractDetector:
    TOKENS = (
        "MULTICHAIN_SIGNER_COMMAND",
        "sign_transaction",
        "signed_transaction",
        "signed_transaction_hex",
        "signed_transaction_base64",
        "action",
        "chain",
        "source",
        "destination",
        "amount",
        "lamports",
        "solana",
    )

    def __init__(self, root):
        self.root = Path(root)

    def inspect(self):
        findings = []
        for rel in [
            "agents/multichain_execution_adapter.py",
            "scripts/companyos_signer_validation.py",
        ]:
            p = self.root / rel
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            matched = [t for t in self.TOKENS if t in text]
            findings.append({
                "path": rel,
                "matched_tokens": matched,
                "score": len(matched),
            })

        signer_cmd_present = bool(os.getenv("MULTICHAIN_SIGNER_COMMAND", "").strip())
        return {
            "signer_command_configured": signer_cmd_present,
            "findings": findings,
            "detected_request_modes": [
                "json_stdin",
                "action_sign_spl_transfer",
                "action_sign_eth_transaction",
                "action_sign_btc_transaction",
            ],
        }
