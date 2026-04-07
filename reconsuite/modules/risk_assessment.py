def run(ctx):
    report = ctx.get("report") or {}
    score = 0
    notes = []
    modules = report.get("modules",{})
    emailsec = modules.get("emailsec",{})
    if emailsec and isinstance(emailsec, dict):
        s = emailsec.get("spoofing_risk",{})
        if isinstance(s, dict):
            score += s.get("score",50)
            if s.get("notes"):
                notes += s.get("notes")
    nmap = modules.get("nmap",{})
    if nmap and isinstance(nmap, dict):
        hosts = nmap.get("nmap") or {}
        for h,vals in (hosts.items() if isinstance(hosts, dict) else []):
            for p,info in vals.get("tcp",{}).items():
                score += 1
                if "vulns" in info or "script" in info:
                    notes.append(f"Potential vuln on {h}:{p}")
    sh = modules.get("shodan",{})
    if sh and isinstance(sh, dict):
        if sh.get("total"):
            score += min(30, sh.get("total")*2)
    headers = modules.get("headers",{})
    if headers:
        for k,v in headers.items():
            if v is None:
                score += 5
                notes.append(f"Missing header {k}")
    final = max(0, min(100, score))
    level = "low"
    if final >= 70: level = "high"
    elif final >= 40: level = "medium"
    return {"score": final, "level": level, "notes": notes}
