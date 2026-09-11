import json
from pathlib import Path
from .engine import LearningEngine
if __name__=="__main__":print(json.dumps(LearningEngine(Path.home()/"companyos").run(),indent=2))
