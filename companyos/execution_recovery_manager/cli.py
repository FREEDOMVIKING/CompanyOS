import json
from pathlib import Path
from .engine import ExecutionRecoveryManager
def main():print(json.dumps(ExecutionRecoveryManager(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
