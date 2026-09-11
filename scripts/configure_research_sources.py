#!/usr/bin/env python3
import json, sys
from pathlib import Path
from companyos_phase321_336 import SourceRegistry

root = Path.home() / "companyos"
registry = SourceRegistry(root)

if len(sys.argv) == 1 or sys.argv[1] == "show":
    print(json.dumps(registry.load(), indent=2))
    raise SystemExit(0)

if sys.argv[1] == "example":
    example = {
        "sources": [
            {
                "name": "Example RSS Feed",
                "type": "rss",
                "url": "https://example.com/feed.xml",
                "enabled": False,
                "priority": 0.8
            },
            {
                "name": "Example JSON API",
                "type": "json",
                "url": "https://example.com/api/items",
                "items_path": "items",
                "title_key": "title",
                "text_key": "description",
                "url_key": "url",
                "enabled": False,
                "priority": 0.7
            }
        ]
    }
    print(json.dumps(example, indent=2))
    raise SystemExit(0)

raise SystemExit("Usage: configure_research_sources.py [show|example]")
