import json
from pathlib import Path
from .engine import ProgressSyncV3
def main():print(json.dumps(ProgressSyncV3(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
