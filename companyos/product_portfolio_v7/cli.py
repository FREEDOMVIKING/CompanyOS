import json
from pathlib import Path
from .engine import ProductPortfolioEngineV7

def main():
    print(json.dumps(ProductPortfolioEngineV7(Path.home() / "companyos").run(), indent=2, default=str))

if __name__ == "__main__":
    main()
