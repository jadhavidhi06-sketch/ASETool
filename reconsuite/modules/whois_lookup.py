import whois
from datetime import datetime

def run(ctx):
    target = ctx["target"]
    w = whois.whois(target)
    out = {
        "registrar": w.registrar,
        "org": w.org,
        "name": w.name,
        "emails": w.emails,
        "creation_date": _fmt(w.creation_date),
        "expiration_date": _fmt(w.expiration_date),
        "name_servers": w.name_servers,
        "country": w.country,
        "raw": str(w)
    }
    return out

def _fmt(val):
    if not val: return None
    if isinstance(val, (list,tuple)):
        val=val[0]
    if hasattr(val,'isoformat'):
        return val.isoformat()
    return str(val)
