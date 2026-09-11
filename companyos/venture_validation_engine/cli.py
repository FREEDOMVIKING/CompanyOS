import json
from pathlib import Path
from .engine import VentureValidationEngine
def main():print(json.dumps(VentureValidationEngine(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
