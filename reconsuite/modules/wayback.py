import requests

WAYBACK_URL = "http://web.archive.org/cdx/search/cdx?url={target}/*&output=json&fl=timestamp,original&collapse=digest"

def run(ctx):
    target = ctx["target"]
    try:
        r = requests.get(WAYBACK_URL.format(target=target), timeout=15)
        if r.status_code == 200:
            arr = r.json()
            snapshots = [{"timestamp":t[0],"url":t[1]} for t in arr[1:]]
            return {"snapshots": snapshots[:200]}
        return {"error": f"status {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}
