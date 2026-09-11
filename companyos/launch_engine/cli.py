import json
from pathlib import Path
from .engine import LaunchEngine
if __name__=="__main__":print(json.dumps(LaunchEngine(Path.home()/"companyos").run(),indent=2))
