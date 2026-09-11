import json
from pathlib import Path
from .bridge import CryptoPaymentBridgeV9

def main():
    print(json.dumps(CryptoPaymentBridgeV9(Path.home() / "companyos").run_cycle(), indent=2))

if __name__ == "__main__":
    main()
