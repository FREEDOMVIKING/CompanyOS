import argparse, json
from pathlib import Path
from .engine import CompetitorIntelligence

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command", choices=["run"])
    parser.parse_args()
    print(json.dumps(CompetitorIntelligence(Path.home()/"companyos").run(), indent=2))

if __name__=="__main__":
    main()
