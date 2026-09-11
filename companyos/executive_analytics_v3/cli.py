import argparse,json
from pathlib import Path
from .engine import ExecutiveAnalyticsV3
def main():
    p=argparse.ArgumentParser();p.add_argument("command",choices=["run"]);p.parse_args();print(json.dumps(ExecutiveAnalyticsV3(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
