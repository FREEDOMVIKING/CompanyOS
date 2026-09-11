from companyos_cf_common import emit, read_req
req = read_req()
emit({"ok": False, "action": "register", "reason": "domain_registration_not_enabled",
      "domain": req.get("domain"),
      "requires": "A separate registrar integration and explicit purchase safeguards.",
      "note": "DNS and Workers deployment are wired separately; this provider intentionally does not purchase domains."}, 1)
