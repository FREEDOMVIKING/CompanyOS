import json
from pathlib import Path
from .engine import RoadmapExecutionBridge
def main():print(json.dumps(RoadmapExecutionBridge(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
