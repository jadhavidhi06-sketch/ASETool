import dns.resolver

def run(ctx):
    target = ctx["target"]
    out = {}
    try:
        mx = dns.resolver.resolve(target, "MX", lifetime=5)
        out["mx"] = [r.exchange.to_text().rstrip('.') for r in mx]
    except Exception as e:
        out["mx"] = {"error": str(e)}
    try:
        txt = dns.resolver.resolve(target, "TXT", lifetime=5)
        txts = []
        for r in txt:
            try:
                txts.append("".join([s.decode() if isinstance(s, bytes) else str(s) for s in r.strings]))
            except Exception:
                txts.append(r.to_text())
        spf = [t for t in txts if "v=spf1" in t.lower()]
        out["txt"] = txts
        out["spf"] = spf
    except Exception as e:
        out["txt"] = {"error": str(e)}
    try:
        d = dns.resolver.resolve("_dmarc."+target, "TXT", lifetime=5)
        out["dmarc"] = [r.to_text().strip('"') for r in d]
    except Exception as e:
        out["dmarc"] = {"error": str(e)}
    out["spoofing_risk"] = _assess_spoofing(out)
    return out

def _assess_spoofing(out):
    score = 50
    notes = []
    if isinstance(out.get("mx"), dict):
        notes.append("No MX records")
        score += 20
    else:
        score -= 10
    if not out.get("spf"):
        notes.append("No SPF record found")
        score += 20
    else:
        score -= 15
    if not out.get("dmarc") or isinstance(out.get("dmarc"), dict):
        notes.append("No DMARC record")
        score += 20
    else:
        score -= 10
    score = max(0,min(100,score))
    return {"score": score, "notes": notes}
