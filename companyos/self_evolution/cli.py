import argparse, json
from pathlib import Path
from .engine import SelfEvolution

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command", choices=["run"])
    parser.parse_args()
    print(json.dumps(SelfEvolution(Path.home()/"companyos").run(), indent=2))

if __name__=="__main__":
    main()
