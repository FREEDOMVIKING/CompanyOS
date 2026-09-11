import json
from pathlib import Path
from .engine import VentureBuilder
def main(): print(json.dumps(VentureBuilder(Path.home()/'companyos').run(),indent=2,default=str))
if __name__=='__main__': main()
