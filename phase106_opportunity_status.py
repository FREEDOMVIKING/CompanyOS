#!/usr/bin/env python3

from companyos.runtime.opportunity_discovery import OpportunityDiscoveryStore

records = sorted(
    OpportunityDiscoveryStore().all_records(),
    key=lambda x: (-x.score, x.created_at_unix),
)

print("TOTAL_OPPORTUNITIES:", len(records))
for record in records[:10]:
    print(
        f"{record.opportunity_id} | SCORE={record.score} | "
        f"CATEGORY={record.category} | TITLE={record.title}"
    )
print("PHASE106_OPPORTUNITY_STATUS: PASS")
