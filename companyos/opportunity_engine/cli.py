import argparse,json
from .engine import OpportunityEngine
def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("run")
    sub.add_parser("list")
    add=sub.add_parser("add")
    add.add_argument("title")
    add.add_argument("--problem",default="")
    add.add_argument("--customer",default="")
    args=parser.parse_args()
    engine=OpportunityEngine()
    if args.command=="add":
        result=engine.add(args.title,args.problem,args.customer)
    elif args.command=="run":
        result=engine.run_cycle()
    else:
        result=engine.run_cycle()["pipeline"]
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
