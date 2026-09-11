#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase301_320 import DiscoveryOrchestrator

records = [
    {
        "source": "demo_customer_interview",
        "title": "Contractors struggle with slow manual estimating",
        "text": "Small contractors complain that estimating is slow, repetitive, manual, and difficult to keep consistent. Pricing software can also feel expensive.",
        "url": "demo://contractor-1",
    },
    {
        "source": "demo_forum",
        "title": "Manual proposal creation wastes hours",
        "text": "Teams struggle to turn job scope into polished proposals. The manual workflow is time-consuming and creates pricing mistakes.",
        "url": "demo://contractor-2",
    },
    {
        "source": "demo_market_note",
        "title": "Subscription estimating alternatives exist",
        "text": "Several competitor products use subscription pricing, but smaller contractors still complain about complexity and price.",
        "url": "demo://contractor-3",
    },
]

root = Path.home() / "companyos"
print(json.dumps(DiscoveryOrchestrator(root).run(records), indent=2, default=str))
