PHASE 78 — REAL SOLANA TRANSACTION CONSTRUCTION + LOCAL SIGNING

Purpose:
- fetch a real recent Solana blockhash
- construct a real legacy System Program transfer message
- use source = destination = configured wallet
- use lamports = 0
- sign the real transaction message locally
- serialize the signed transaction
- verify the Ed25519 signature locally

This phase intentionally DOES NOT:
- call sendTransaction
- call simulateTransaction
- broadcast the signed transaction
- move funds
- print the private key

INSTALL:
cd ~/companyos || exit 1
rm -rf phase78_solana_transaction_build_sign_bundle
mkdir -p phase78_solana_transaction_build_sign_bundle

unzip -o ~/storage/downloads/PHASE78_SOLANA_TRANSACTION_BUILD_SIGN_BUNDLE.zip \
  -d ~/companyos/phase78_solana_transaction_build_sign_bundle

python ~/companyos/phase78_solana_transaction_build_sign_bundle/phase78_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase78_solana_transaction_build_sign_bundle/phase78_verify.py

RUN REAL BUILD + LOCAL SIGN TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase78_transaction_sign_test.py
