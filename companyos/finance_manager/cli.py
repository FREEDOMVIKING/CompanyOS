import json
from pathlib import Path
from .engine import FinanceManager
if __name__=="__main__":print(json.dumps(FinanceManager(Path.home()/"companyos").run(),indent=2))
