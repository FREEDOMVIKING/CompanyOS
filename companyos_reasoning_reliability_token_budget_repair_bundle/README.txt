COMPANYOS REASONING RELIABILITY + TOKEN BUDGET REPAIR

Fixes the audit pattern:
- reasoning_http_error
- HTTP 402 / "requires more credits, or fewer max_tokens"
- repeated 502 provider errors
- requests asking for up to 65536 output tokens
- autonomy cycles degrading into partial_cycle_errors

What it does:
1. Installs a centralized requests-level reliability shim for LLM calls.
2. Clamps max_tokens/max_output_tokens to 8192 by default.
3. Retries retryable provider/credit failures with smaller budgets:
   8192 -> 4096 -> 2048/1024
4. Adds exponential backoff for 429/5xx/provider failures.
5. Patches CompanyOS runtime entrypoints so the shim is installed before autonomous work.
6. Does not alter financial, approval, signer, domain-purchase, or irreversible-action gates.

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_reasoning_reliability_token_budget_repair_bundle
mkdir -p companyos_reasoning_reliability_token_budget_repair_bundle

unzip -o ~/storage/downloads/COMPANYOS_REASONING_RELIABILITY_TOKEN_BUDGET_REPAIR_BUNDLE.zip   -d ~/companyos/companyos_reasoning_reliability_token_budget_repair_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_reasoning_reliability_token_budget_repair_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_reasoning_reliability_token_budget_repair_bundle/verify.py

Restart both autonomy layers:

bash scripts/companyos_productive_autonomy.sh restart
bash scripts/companyos_full_autonomy.sh restart 2>/dev/null || true

Wait 60 seconds, then:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_reasoning_reliability_status.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_recent_reasoning_errors.py

bash scripts/companyos_productive_autonomy.sh status
bash scripts/companyos_full_autonomy.sh status 2>/dev/null || true

Optional lower ceiling for tight API budgets:

export COMPANYOS_REASONING_MAX_OUTPUT_TOKENS=4096
export COMPANYOS_REASONING_MIN_RETRY_TOKENS=1024
