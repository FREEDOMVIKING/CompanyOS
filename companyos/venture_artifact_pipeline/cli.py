import json
from pathlib import Path
from .engine import VentureArtifactPipeline
def main():print(json.dumps(VentureArtifactPipeline(Path.home()/"companyos").run(),indent=2))
if __name__=="__main__":main()
