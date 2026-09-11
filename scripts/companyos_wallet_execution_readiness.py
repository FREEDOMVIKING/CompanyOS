#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.walletintegration import SolanaExecutionReadiness
root = Path.home() / "companyos"
print(json.dumps(SolanaExecutionReadiness(root).inspect(), indent=2))
