import dns.resolver
import dns.reversename
import socket

def run(ctx):
    target = ctx["target"]
    resolver = dns.resolver.Resolver()
    out = {}
    for rtype in ("A","AAAA","MX","NS","TXT","SOA","CNAME"):
        try:
            answers = resolver.resolve(target, rtype, lifetime=5)
            vals = []
            for r in answers:
                vals.append(r.to_text())
            out[rtype] = vals
        except Exception as e:
            out[rtype] = {"error": str(e)}
    rev = {}
    for ip in (out.get("A",[]) if isinstance(out.get("A",[]), list) else [] ) + (out.get("AAAA",[]) if isinstance(out.get("AAAA",[]), list) else []):
        try:
            name = dns.reversename.from_address(ip)
            rev[ip] = str(socket.gethostbyaddr(ip)[0])
        except Exception as e:
            rev[ip] = {"error": str(e)}
    out["reverse"] = rev
    return out
