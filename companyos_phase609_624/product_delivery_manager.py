from .delivery_intake import DeliveryIntake
from .product_spec import ProductSpec
from .implementation_plan import ImplementationPlan
from .specialist_plan import SpecialistPlan
from .telemetry_contract import TelemetryContract
from .launch_plan import LaunchPlan

class ProductDeliveryManager:
    """622: produce complete product-delivery packet."""

    def prepare(self, packet):
        gate = DeliveryIntake().evaluate(packet)
        if not gate["accepted"]:
            return {"success":False,"status":"delivery_intake_rejected","gate":gate}

        spec = ProductSpec().build(packet)
        tasks = ImplementationPlan().build(spec)
        return {
            "success":True,
            "status":"product_delivery_packet_ready",
            "venture_id":packet["venture_id"],
            "product_spec":spec,
            "implementation_plan":tasks,
            "specialists":SpecialistPlan().assign(tasks),
            "quality_gates":packet.get("quality_gates",[]),
            "telemetry_contract":TelemetryContract().build(packet.get("kpis")),
            "launch_plan":LaunchPlan().build(),
        }
