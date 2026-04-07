def run(ctx):
    report = ctx.get("report") or {}
    score = 0
    notes = []
    modules = report.get("modules", {}) or {}

    # Email security / spoofing risk
    emailsec = modules.get("emailsec") or {}
    if isinstance(emailsec, dict):
        s = emailsec.get("spoofing_risk") or {}
        if isinstance(s, dict):
            try:
                score += int(s.get("score", 0))
            except Exception:
                pass
            notes_list = s.get("notes")
            if isinstance(notes_list, list):
                notes.extend(str(x) for x in notes_list)
            elif notes_list:
                notes.append(str(notes_list))

    # Nmap findings
    nmap = modules.get("nmap") or {}
    if isinstance(nmap, dict):
        hosts = nmap.get("nmap") or {}
        if isinstance(hosts, dict):
            for h, vals in hosts.items():
                if not isinstance(vals, dict):
                    continue
                tcp = vals.get("tcp") or {}
                if isinstance(tcp, dict):
                    for p, info in tcp.items():
                        # port keys might be strings; keep as-is for messages
                        try:
                            score += 1
                        except Exception:
                            pass
                        if isinstance(info, dict):
                            # check for vulnerability indicators
                            if info.get("vulns") or info.get("script") or any(k.startswith("vuln") for k in info):
                                notes.append(f"Potential vuln on {h}:{p}")

    # Shodan summary
    sh = modules.get("shodan") or {}
    if isinstance(sh, dict):
        try:
            total = int(sh.get("total") or 0)
            score += min(30, total * 2)
        except Exception:
            pass

    # Security headers (expects modules['headers'] to be a dict of header->value)
    headers = modules.get("headers") or {}
    if isinstance(headers, dict):
        for k, v in headers.items():
            if v in (None, "", []):
                score += 5
                notes.append(f"Missing header {k}")

    # Finalize
    final = max(0, min(100, int(score)))
    if final >= 70:
        level = "high"
    elif final >= 40:
        level = "medium"
    else:
        level = "low"

    return {"score": final, "level": level, "notes": notes}
