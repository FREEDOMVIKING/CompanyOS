import json
from pathlib import Path
from .engine import SpecialistAssignmentV3
def main():print(json.dumps(SpecialistAssignmentV3(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
