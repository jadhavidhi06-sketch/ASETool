import whois
from datetime import datetime
from typing import Any, Dict, Optional, List, Union

def _fmt(val: Any) -> Optional[str]:
    if not val:
        return None
    # If list/tuple pick the earliest sensible date or first element
    if isinstance(val, (list, tuple)):
        # try to find a datetime in the list
        for v in val:
            if hasattr(v, "isoformat"):
                return v.isoformat()
        val = val[0]
    if hasattr(val, "isoformat"):
        try:
            return val.isoformat()
        except Exception:
            return str(val)
    return str(val)

def _normalize_list(v: Any) -> Optional[List[Any]]:
    if v is None:
        return None
    if isinstance(v, (list, tuple, set)):
        return list(v)
    return [v]

def run(ctx: Dict[str, Any]) -> Dict[str, Any]:
    target = ctx["target"]
    out: Dict[str, Any] = {"domain": target}
    try:
        w = whois.whois(target)
    except Exception as e:
        return {"error": f"whois_lookup_failed: {e}", "domain": target}

    # Many whois libraries return attributes as either str or lists; normalize safely
    registrar = getattr(w, "registrar", None)
    org = getattr(w, "org", None) or getattr(w, "organization", None)
    name = getattr(w, "name", None)
    emails = _normalize_list(getattr(w, "emails", None))
    creation = getattr(w, "creation_date", None)
    expiration = getattr(w, "expiration_date", None)
    name_servers = _normalize_list(getattr(w, "name_servers", None) or getattr(w, "nameservers", None))
    country = getattr(w, "country", None)
    raw = None
    try:
        raw = str(w)
    except Exception:
        raw = None

    out.update({
        "registrar": registrar,
        "org": org,
        "name": name,
        "emails": emails,
        "creation_date": _fmt(creation),
        "expiration_date": _fmt(expiration),
        "name_servers": name_servers,
        "country": country,
        "raw": raw
    })

    # Extra derived fields
    try:
        if out["creation_date"]:
            out["age_days"] = (datetime.utcnow() - datetime.fromisoformat(out["creation_date"])).days
    except Exception:
        out["age_days"] = None

    return out
