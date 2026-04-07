import shodan

def run(ctx):
    key = ctx.get("shodan_key")
    if not key:
        return {"error":"no_shodan_key"}
    api = shodan.Shodan(key)
    target = ctx["target"]
    out = {}
    try:
        results = api.search(f"hostname:{target}")
        out["total"] = results.get("total")
        out["matches"] = []
        for m in results.get("matches",[]):
            out["matches"].append({
                "ip": m.get("ip_str"),
                "port": m.get("port"),
                "org": m.get("org"),
                "isp": m.get("isp"),
                "data": m.get("data")[:400],
                "cpe": m.get("cpe")
            })
    except Exception as e:
        out["error"] = str(e)
    return out
