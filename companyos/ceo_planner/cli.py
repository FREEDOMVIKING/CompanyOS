import json
from pathlib import Path
from .engine import CEOPlanner
if __name__=="__main__":
    print(json.dumps(CEOPlanner(Path.home()/"companyos").run(),indent=2))
