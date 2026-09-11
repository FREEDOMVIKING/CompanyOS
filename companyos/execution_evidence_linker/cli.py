import json
from pathlib import Path
from .engine import ExecutionEvidenceLinker
def main():print(json.dumps(ExecutionEvidenceLinker(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
