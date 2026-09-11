#!/usr/bin/env python3
import json,sys
req=json.loads(sys.argv[1]) if len(sys.argv)>1 else {}
print(json.dumps({
  "success": False,
  "status": "adapter_not_configured",
  "kind": "publication",
  "message": "Configure this adapter for a specific approved provider/target before live execution."
}, indent=2))
raise SystemExit(2)
