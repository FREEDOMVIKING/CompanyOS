import json, secrets, time
from pathlib import Path

class OneShotAuthorization:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"one_shot_live_authorization.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, max_amount, destination, ttl_seconds=300):
        token = secrets.token_urlsafe(24)
        data = {
            "token": token,
            "max_amount": float(max_amount),
            "destination": destination,
            "expires_at": int(time.time()) + int(ttl_seconds),
            "used": False,
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {
            "success": True,
            "status": "one_shot_authorization_created",
            "token": token,
            "expires_at": data["expires_at"],
            "max_amount": data["max_amount"],
            "destination": destination,
        }

    def validate(self, token, amount, destination):
        if not self.path.exists():
            return {"allowed":False,"status":"authorization_missing"}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"allowed":False,"status":"authorization_corrupt"}

        if data.get("used"):
            return {"allowed":False,"status":"authorization_already_used"}
        if int(time.time()) > int(data.get("expires_at",0)):
            return {"allowed":False,"status":"authorization_expired"}
        if token != data.get("token"):
            return {"allowed":False,"status":"authorization_token_mismatch"}
        if float(amount) > float(data.get("max_amount",0)):
            return {"allowed":False,"status":"authorization_amount_exceeded"}
        if destination != data.get("destination"):
            return {"allowed":False,"status":"authorization_destination_mismatch"}

        return {"allowed":True,"status":"one_shot_authorization_valid"}

    def consume(self):
        if not self.path.exists():
            return {"success":False,"status":"authorization_missing"}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["used"] = True
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"success":True,"status":"one_shot_authorization_consumed"}
