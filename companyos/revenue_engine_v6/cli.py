import json
from pathlib import Path
from .engine import RevenueEngineV6

def main():
    result = RevenueEngineV6(Path.home() / "companyos").run()
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
