from pathlib import Path
import shutil,os,time
ROOT=Path.home()/"companyos";SRC=Path(__file__).resolve().parent;stamp=str(int(time.time()))
for rel in ["companyos/evolution/self_evolution_generator.py","scripts/companyos_self_evolution_generate_once.py","scripts/companyos_self_evolution_full_cycle.py","scripts/companyos_self_evolution_generator_status.py","scripts/companyos_self_evolution_generator.sh"]:
 s=SRC/rel;d=ROOT/rel;d.parent.mkdir(parents=True,exist_ok=True)
 if d.exists():shutil.copy2(d,d.with_name(d.name+".bak."+stamp))
 shutil.copy2(s,d);print("INSTALLED:",d)
os.chmod(ROOT/"scripts/companyos_self_evolution_generator.sh",0o755)
print("SELF_EVOLUTION_GENERATOR_CAPABILITY_GAP_ENGINE_INSTALL: PASS")
print("CAPABILITY_GAP_DETECTION: ENABLED")
print("CODE_GENERATION_TO_WATCHED_DIRECTORY: ENABLED")
print("PROMOTION_PIPELINE_HANDOFF: ENABLED")
print("CORE_OVERWRITE_BY_DEFAULT: NO")
