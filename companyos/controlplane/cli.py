import argparse
import json
from .legacy_scan import scan
from .manager import ControlPlane

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "stop", "restart", "status", "once"])
    args = parser.parse_args()
    plane = ControlPlane()
    if args.command == "start":
        scan()
        result = plane.start()
    elif args.command == "stop":
        result = plane.stop()
    elif args.command == "restart":
        scan()
        result = plane.restart()
    else:
        result = plane.status()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
