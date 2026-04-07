import requests
import gzip
import concurrent.futures
import dns.resolver
import dns.reversename
import socket
import os
from typing import List, Dict, Any, Optional

CRT_SH_URL = "https://crt.sh/?q=%25.{target}&output=json"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "subdomains.txt.gz")
DEFAULT_WORDS = ["www", "mail", "api", "dev", "test", "admin", "shop", "blog", "ftp", "portal"]

def _load_wordlist(path: str = DATA_PATH) -> List[str]:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except Exception:
        return DEFAULT_WORDS.copy()

def _resolve_a_aaaa(name: str, timeout: float = 3.0) -> Optional[List[str]]:
    resolver = dns.resolver.Resolver()
    answers = []
    for qtype in ("A", "AAAA"):
        try:
            resp = resolver.resolve(name, qtype, lifetime=timeout)
            answers.extend([r.to_text() for r in resp])
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            continue
        except Exception:
            return None
    return answers if answers else None

def _ptr_lookup(ip: str, timeout: float = 3.0) -> Optional[List[str]]:
    resolver = dns.resolver.Resolver()
    try:
        rev = dns.reversename.from_address(ip).to_text()
        resp = resolver.resolve(rev, "PTR", lifetime=timeout)
        return [r.to_text().rstrip('.') for r in resp]
    except Exception:
        return None

def run(ctx: Dict[str, Any]) -> Dict[str, Any]:
    target = ctx["target"]
    timeout = float(ctx.get("dns_timeout", 3.0))
    max_workers = int(ctx.get("max_workers", 25))
    results: Dict[str, Any] = {"crtsh": [], "brute": [], "resolved": {}, "errors": {}}

    # crt.sh enumeration
    try:
        r = requests.get(CRT_SH_URL.format(target=target), timeout=float(ctx.get("crt_timeout", 15)))
        r.raise_for_status()
        items = r.json() if r.content else []
        names = set()
        for it in items:
            name = it.get("name_value") or it.get("common_name")
            if not name:
                continue
            for n in str(name).splitlines():
                n = n.strip()
                if n and (n == target or n.endswith("." + target) or n.endswith(target)):
                    names.add(n)
        results["crtsh"] = sorted(names)
        results["crtsh_count"] = len(names)
    except Exception as e:
        results["crtsh"] = []
        results["errors"]["crtsh"] = str(e)

    # load wordlist
    words = _load_wordlist()
    # allow override or extension
    extra = ctx.get("subdomain_words")
    if isinstance(extra, list):
        words = list(dict.fromkeys(words + extra))  # keep order, dedupe

    candidates = [f"{w}.{target}" for w in words]

    # concurrent DNS resolution
    resolved: Dict[str, List[str]] = {}
    def check(host: str):
        ips = _resolve_a_aaaa(host, timeout=timeout)
        if not ips:
            return None
        ptrs = []
        for ip in ips:
            p = _ptr_lookup(ip, timeout=timeout)
            if p:
                ptrs.append({ip: p})
        return {"host": host, "ips": ips, "ptr": ptrs}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(check, h): h for h in candidates}
        for fut in concurrent.futures.as_completed(futures):
            try:
                res = fut.result()
                if res:
                    resolved[res["host"]] = {"ips": res["ips"], "ptr": res["ptr"]}
            except Exception as e:
                results["errors"].setdefault("resolve", []).append(f"{futures[fut]}: {e}")

    results["resolved"] = resolved
    results["brute"] = sorted(resolved.keys())
    results["brute_count"] = len(results["brute"])
    return results
