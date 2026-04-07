import requests, gzip, concurrent.futures, dns.resolver, os

CRT_SH_URL = "https://crt.sh/?q=%25.{target}&output=json"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "subdomains.txt.gz")

def _load_wordlist():
    try:
        with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except Exception:
        return ["www","mail","api","dev","test","admin","shop","blog","ftp","portal"]

def _resolve(name, timeout=3):
    try:
        answers = dns.resolver.resolve(name, "A", lifetime=timeout)
        return [r.to_text() for r in answers]
    except Exception:
        return None

def run(ctx):
    target = ctx["target"]
    results = {"crtsh": [], "brute": [], "resolved": {}}
    try:
        r = requests.get(CRT_SH_URL.format(target=target), timeout=15)
        if r.status_code == 200:
            items = r.json()
            names = set()
            for it in items:
                name = it.get("name_value")
                if name:
                    for n in name.split("\n"):
                        n = n.strip()
                        if n and n.endswith(target):
                            names.add(n)
            results["crtsh"] = sorted(names)
    except Exception as e:
        results["crtsh"] = {"error": str(e)}
    words = _load_wordlist()
    candidates = [f"{w}.{target}" for w in words]
    resolved = {}
    def check(host):
        ips = _resolve(host)
        return (host, ips)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        for host, ips in ex.map(check, candidates):
            if ips:
                resolved[host] = ips
    results["resolved"] = resolved
    results["brute"] = list(resolved.keys())
    return results
