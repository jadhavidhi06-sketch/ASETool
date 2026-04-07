import shodan

def run(ctx):
    key = ctx.get("shodan_key")
    if not key:
        return {"error": "no_shodan_key"}
    api = shodan.Shodan(key)
    target = ctx["target"]
    out = {}
    try:
        results = api.search(f"hostname:{target}")
        out["total"] = int(results.get("total", 0))
        out["matches"] = []
        for m in results.get("matches", []):
            data = m.get("data") or ""
            # truncate safely
            try:
                data_snippet = data[:400]
            except Exception:
                data_snippet = str(data)[:400]
            out["matches"].append({
                "ip": m.get("ip_str"),
                "port": m.get("port"),
                "org": m.get("org"),
                "isp": m.get("isp"),
                "data": data_snippet,
                "cpe": m.get("cpe") or []
            })
    except shodan.APIError as e:
        out["error"] = f"APIError: {e}"
    except Exception as e:
        out["error"] = str(e)
    return out
