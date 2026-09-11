import json
from pathlib import Path
from .engine import LaunchReadinessEngine
def main():print(json.dumps(LaunchReadinessEngine(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
