import json
from pathlib import Path
from .engine import StorefrontSalesEngineV8

def main():
    print(json.dumps(StorefrontSalesEngineV8(Path.home() / "companyos").run(), indent=2))

if __name__ == "__main__":
    main()
