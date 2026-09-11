import json
from pathlib import Path
from .engine import MilestoneGeneratorV3
def main():print(json.dumps(MilestoneGeneratorV3(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
