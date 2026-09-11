#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase737_744 import *
sample={"success":False,"status":"failed","error":"HTTPError: HTTP Error 403: rate limit exceeded"}
assert RateLimitDetector().detect(sample)["rate_limited"]
root=Path(tempfile.mkdtemp(prefix="phase744_"))
c=ProviderCooldown(root); c.set("github",30,"provider_rate_limited"); assert c.active("github")
assert BackoffPolicy().delay_seconds(3)==240
assert FallbackProvider().choose("github")!="github"
r=RetryClassifier().classify(sample); assert r["retryable"] and not r["hard_failure"]
m=MissionRescheduler().reschedule({"mission_id":"m1","attempts":0,"context":{}},30,"provider_rate_limited","hacker_news")
assert m["attempts"]==1 and m["status"]=="deferred"
h=ResilientExecutor(root).handle({"mission_id":"m1","attempts":0,"context":{}},sample,"github")
assert h["handled"] and not h["hard_failure"]
print(json.dumps({"success":True,"status":"phase737_744_verification_passed","cycle_status":"phase744_provider_rate_limit_recovery_ready"},indent=2))
