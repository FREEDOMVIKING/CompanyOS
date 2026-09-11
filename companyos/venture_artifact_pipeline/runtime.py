from companyos.runtime_common_v3 import run_forever
from .engine import VentureArtifactPipeline
def main():run_forever("venture_artifact_pipeline",lambda home:VentureArtifactPipeline(home),300)
if __name__=="__main__":main()
