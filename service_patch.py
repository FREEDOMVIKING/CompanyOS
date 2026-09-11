from pathlib import Path

config = Path.home() / "companyos" / "companyos" / "controlplane" / "config.py"
if not config.exists():
    raise SystemExit("Control-plane config.py not found")

text = config.read_text()
needle = 'ServiceSpec("supervisor_18301_18400", "companyos.controlplane.supervisor", True),'
addition = '''ServiceSpec("opscenter_18501_18700", "companyos.opscenter.runtime", True),
        ServiceSpec("supervisor_18301_18400", "companyos.controlplane.supervisor", True),'''

if "opscenter_18501_18700" not in text:
    text = text.replace(needle, addition)
    config.write_text(text)
    print("Added opscenter service to control plane.")
else:
    print("Opscenter service already registered.")
