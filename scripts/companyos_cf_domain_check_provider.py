from companyos_cf_common import emit, read_req, zone_id_for
req = read_req()
domain = str(req.get("domain") or "").strip().lower()
if not domain:
    emit({"ok": False, "reason": "missing_domain"}, 2)
zone_id, raw = zone_id_for(domain)
if raw.get("success") is False:
    emit({"ok": False, "reason": "cloudflare_zone_lookup_failed", "domain": domain, "details": raw,
          "note": "This checks Cloudflare zone presence; it is not registrar availability."}, 1)
emit({"ok": True, "action": "check", "domain": domain,
      "exists_in_cloudflare_account": bool(zone_id), "zone_id": zone_id,
      "note": "Cloudflare zone presence check only; not registrar availability."})
