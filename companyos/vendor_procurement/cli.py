import argparse,json
from pathlib import Path
from .engine import VendorProcurement
def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["run"])
    p.parse_args()
    print(json.dumps(VendorProcurement(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":
    main()
