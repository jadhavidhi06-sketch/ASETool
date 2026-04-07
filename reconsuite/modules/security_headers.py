import requests

HEADERS_TO_CHECK = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "X-XSS-Protection",
]

# Map common header name variants to canonical keys
CANONICAL = {
    "strict-transport-security": "Strict-Transport-Security",
    "content-security-policy": "Content-Security-Policy",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type-Options",
    "referrer-policy": "Referrer-Policy",
    "x-xss-protection": "X-XSS-Protection",
}

def run(ctx):
    target = ctx["target"]
    url = ctx.get("url") or f"https://{target}"
    timeout = float(ctx.get("timeout", 10))
    out = {"url": url, "checked": {}, "missing": []}
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True, verify=False)
        # Normalize header names to lower-case for robust lookups
        norm_headers = {k.lower(): v for k, v in r.headers.items()}
        for h in HEADERS_TO_CHECK:
            val = norm_headers.get(h.lower())
            out["checked"][h] = val if val is not None else None
            if not val:
                out["missing"].append(h)
        out["status_code"] = r.status_code
    except Exception as e:
        out["error"] = str(e)
    return out
