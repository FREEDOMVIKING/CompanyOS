BUILTINS=[
("research","Research Intelligence","4.0",["research","evidence","market_analysis"]),
("product","Product Intelligence","4.0",["product","packaging","pricing"]),
("marketing","Marketing Intelligence","4.0",["campaigns","positioning","acquisition"]),
("finance","Finance Intelligence","4.0",["budget","revenue","cashflow"]),
("operations","Operations Intelligence","4.0",["workflow","health","capacity"]),
("customer","Customer Intelligence","4.0",["support","retention","feedback"]),
("launch","Launch Intelligence","4.0",["validation","launch","handoff"]),
("recovery","Recovery Intelligence","4.0",["diagnostics","retry","repair"]),
("strategy","Executive Strategy","4.0",["planning","prioritization","portfolio"]),
("memory","Executive Memory","4.0",["memory","lessons","decision_history"]),
]

def register(db):
    for pid,n,v,caps in BUILTINS:
        db.upsert_plugin(pid,n,v,"builtin",caps,True,"OK")
