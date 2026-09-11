CompanyOS Phase 23001-24000
EXISTING CRYPTO WALLET CONNECTOR

This bundle is designed to reuse the crypto wallet already present in the earlier
CompanyOS code instead of creating another wallet or asking you to paste private keys.

The earlier CompanyOS wallet design is expected to support Solana/EVM-style wallet
functionality and a local wallet port. This connector discovers the actual installed
implementation and adapts it into the Phase 23000 payment framework.

Safety:
- No private key material is embedded in this package.
- The binder does not print private keys.
- Real transfer execution remains disabled by treasury policy by default.
- Destination allowlisting is preserved.
- Reserve floor, daily limit, single-transfer limit, and loss limits remain enforced.

INSTALL:
cd ~/companyos
cp /sdcard/Download/CompanyOS_CRYPTO_WALLET_CONNECTOR_24000.zip .
unzip -o CompanyOS_CRYPTO_WALLET_CONNECTOR_24000.zip
bash companyos_phase23001_24000/install.sh ~/companyos

THEN SCAN THE EXISTING CODE:
bash ~/companyos/scripts/companyos_crypto.sh scan

BIND THE BEST WALLET CANDIDATE:
bash ~/companyos/scripts/companyos_crypto.sh bind

CHECK STATUS:
bash ~/companyos/scripts/companyos_crypto.sh status

Do not enable live autonomous transfers until the binding identifies the correct
CompanyOS wallet implementation and balance/address methods pass cleanly.
