import dns.resolver
import dns.reversename
import socket
from typing import Dict, Any, List

DEFAULT_LIFETIME = 5.0

def _safe_resolve(resolver: dns.resolver.Resolver, name: str, rtype: str, lifetime: float) -> List[str]:
    try:
        answers = resolver.resolve(name, rtype, lifetime=lifetime)
        return [r.to_text() for r in answers]
    except dns.resolver.NXDOMAIN:
        return []
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.Timeout as e:
        return [f"ERROR: timeout ({e})"]
    except dns.resolver.NoNameservers as e:
        return [f"ERROR: no nameservers ({e})"]
    except Exception as e:
        return [f"ERROR: {e}"]

def run(ctx: Dict[str, Any]) -> Dict[str, Any]:
    target = ctx["target"]
    lifetime = float(ctx.get("dns_timeout", DEFAULT_LIFETIME))

    resolver = dns.resolver.Resolver()
    # Optional: allow user to override nameservers via ctx["nameservers"] = ["1.1.1.1"]
    if "nameservers" in ctx:
        try:
            resolver.nameservers = list(ctx["nameservers"])
        except Exception:
            pass

    out: Dict[str, Any] = {}
    for rtype in ("A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"):
        out[rtype] = _safe_resolve(resolver, target, rtype, lifetime)

    # Normalize TXT entries (they may be lists of quoted strings)
    if isinstance(out.get("TXT"), list):
        normalized_txt = []
        for t in out["TXT"]:
            if t.startswith('"') and t.endswith('"'):
                normalized_txt.append(t.strip('"'))
            else:
                normalized_txt.append(t)
        out["TXT"] = normalized_txt

    # Reverse DNS lookups for valid IPs from A and AAAA records
    rev = {}
    ip_candidates = []
    for key in ("A", "AAAA"):
        vals = out.get(key, [])
        if isinstance(vals, list):
            ip_candidates.extend([v for v in vals if not v.startswith("ERROR:")])

    for ip in ip_candidates:
        try:
            # Skip values that are clearly not IPs
            socket.inet_pton(socket.AF_INET, ip)
            is_ip = True
        except OSError:
            try:
                socket.inet_pton(socket.AF_INET6, ip)
                is_ip = True
            except OSError:
                is_ip = False

        if not is_ip:
            rev[ip] = {"error": "not an IP address"}
            continue

        try:
            # prefer using dns.reversename + resolver.resolve PTR
            rev_name = dns.reversename.from_address(ip).to_text()
            ptr_answers = _safe_resolve(resolver, rev_name, "PTR", lifetime)
            if ptr_answers and any(a.startswith("ERROR:") for a in ptr_answers):
                rev[ip] = {"error": ptr_answers}
            else:
                rev[ip] = ptr_answers
        except Exception as e:
            # fallback to socket.gethostbyaddr
            try:
                rev[ip] = [socket.gethostbyaddr(ip)[0]]
            except Exception as e2:
                rev[ip] = {"error": f"dns_error: {e}; socket_error: {e2}"}

    out["reverse"] = rev
    return out
