import json
from pathlib import Path
from .engine import DashboardV2
if __name__=="__main__":print(json.dumps(DashboardV2(Path.home()/"companyos").snapshot(),indent=2))
