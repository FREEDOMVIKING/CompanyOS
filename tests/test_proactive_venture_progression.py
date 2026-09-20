from companyos.runtime.proactive_venture_progression import STAGE_RANK

def test_launch_ready_prioritizes_build():
    assert STAGE_RANK["LAUNCH_READY"] > STAGE_RANK["BUILD"]

def test_customer_acquisition_prioritizes_launch_ready():
    assert STAGE_RANK["CUSTOMER_ACQUISITION"] > STAGE_RANK["LAUNCH_READY"]

def test_scale_is_highest_but_scheduler_can_exclude_it():
    assert STAGE_RANK["SCALE"] > STAGE_RANK["OPERATE"]
