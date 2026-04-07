import requests

HEADERS_TO_CHECK = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "X-XSS-Protection"
]

def run(ctx):
    target = ctx["target"]
    url = f"https://{target}"
    out = {}
    try:
        r = requests.get(url, timeout=10, verify=False)
        headers = r.headers
        for h in HEADERS_TO_CHECK:
            out[h] = headers.get(h)
    except Exception as e:
        out["error"] = str(e)
    return out
