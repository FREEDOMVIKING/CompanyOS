import json
from pathlib import Path
from .engine import DashboardClusterManager
def main():print(json.dumps(DashboardClusterManager(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
