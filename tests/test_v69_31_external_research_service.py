from companyos.runtime.service_supervisor import ServiceSupervisor

def test_external_research_service_registered():
    names={x.name for x in ServiceSupervisor.default_services()}
    assert "external_research_network" in names
