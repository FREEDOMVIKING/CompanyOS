import json
from pathlib import Path
from .engine import SalesEngine
if __name__=="__main__":print(json.dumps(SalesEngine(Path.home()/"companyos").run(),indent=2))
