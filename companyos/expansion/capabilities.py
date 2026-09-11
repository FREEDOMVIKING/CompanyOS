CAPABILITIES = [
    ("opportunity_discovery", "Internet opportunity discovery"),
    ("crm", "Customer relationship management"),
    ("website", "Website builder and deployment"),
    ("product", "Product generation pipeline"),
    ("marketing", "Marketing campaign execution"),
    ("email", "Email automation"),
    ("domains", "Domain purchasing workflow"),
    ("accounting", "Accounting and bookkeeping"),
    ("banking", "Banking integration interface"),
    ("crypto", "Crypto wallet management interface"),
    ("hiring", "Hiring and recruiting"),
    ("documents", "Document generation"),
    ("vendors", "Vendor management"),
    ("legal", "Legal and compliance workflow"),
    ("deployment", "Production deployment automation"),
    ("revenue", "Revenue tracking"),
    ("external_api", "External API execution"),
    ("software_factory", "Autonomous software build and deployment"),
    ("portfolio", "Multi-company portfolio management"),
    ("executive_chat", "Executive chat interface"),
    ("voice", "Voice-control interface"),
]

def capability_manifest():
    return [
        {
            "id": cid,
            "name": name,
            "status": "installed",
            "external_execution": "requires_connector_and_approval",
        }
        for cid, name in CAPABILITIES
    ]
