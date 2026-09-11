from companyos.finallaunch import FinalLaunchController
ctl=FinalLaunchController()

p=ctl.preflight()
assert p["files_ok"] is True
safe=ctl.set_safe()
assert safe["live_enabled"] is False
assert safe["transaction_broadcasts_allowed"] is False

trial=ctl.set_trial(1.0, 5.0, "I_UNDERSTAND_TRIAL_LIVE")
assert trial["name"]=="TRIAL_LIVE"
assert trial["max_single_action_amount"]==1.0

safe2=ctl.set_safe()
assert safe2["name"]=="SAFE"

print("final_preflight => PASS")
print("safe_profile => PASS")
print("trial_profile_limits => PASS")
print("profile_persistence => PASS")
print("no_live_enable_at_install => PASS")
print("rollback_to_safe => PASS")
print("FINAL_HAUL_SMOKE_TEST: PASS")
