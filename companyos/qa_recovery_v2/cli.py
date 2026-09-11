import argparse,json
from pathlib import Path
from .engine import QARecoveryV2
def main():
    p=argparse.ArgumentParser();p.add_argument("command",choices=["run"]);p.parse_args();print(json.dumps(QARecoveryV2(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
