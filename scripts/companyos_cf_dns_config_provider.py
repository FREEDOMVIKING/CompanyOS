from companyos_cf_common import api, emit, read_req, zone_id_for
import urllib.parse
req = read_req()
zone_id = str(req.get("zone_id") or "").strip()
zone_name = str(req.get("zone") or req.get("domain") or "").strip().lower()
rtype = str(req.get("type") or "A").strip().upper()
name = str(req.get("name") or "").strip()
content = str(req.get("content") or "").strip()
ttl = int(req.get("ttl") or 1)
proxied = bool(req.get("proxied", False))
if not zone_id:
    if not zone_name:
        emit({"ok": False, "reason": "missing_zone_or_zone_id"}, 2)
    zone_id, lookup = zone_id_for(zone_name)
    if not zone_id:
        emit({"ok": False, "reason": "zone_not_found_or_not_readable", "details": lookup}, 1)
if not name or not content:
    emit({"ok": False, "reason": "missing_name_or_content"}, 2)
q = urllib.parse.urlencode({"type": rtype, "name": name})
existing = api("GET", f"/zones/{zone_id}/dns_records?{q}")
if not existing.get("success"):
    emit({"ok": False, "reason": "dns_lookup_failed", "details": existing}, 1)
payload = {"type": rtype, "name": name, "content": content, "ttl": ttl, "proxied": proxied}
items = existing.get("result") or []
if items:
    rid = items[0]["id"]
    res = api("PUT", f"/zones/{zone_id}/dns_records/{rid}", payload)
    mode = "updated"
else:
    res = api("POST", f"/zones/{zone_id}/dns_records", payload)
    mode = "created"
emit({"ok": bool(res.get("success")), "action": "configure_dns", "mode": mode,
      "zone_id": zone_id, "record": payload, "cloudflare": res}, 0 if res.get("success") else 1)
