import argparse,json
from .engine import VentureBuilderEngine
def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True)
    s.add_parser("build-top");b=s.add_parser("build");b.add_argument("opportunity_id")
    s.add_parser("list");s.add_parser("health");a=p.parse_args();e=VentureBuilderEngine()
    if a.cmd=="build-top":r=e.build_top()
    elif a.cmd=="build":r=e.build_by_id(a.opportunity_id)
    elif a.cmd=="list":r=e.list_builds()
    else:r=e.health()
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
