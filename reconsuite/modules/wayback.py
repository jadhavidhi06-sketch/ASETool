import requests
from typing import Dict, Any, List

WAYBACK_URL = "https://web.archive.org/cdx/search/cdx?url={target}/*&output=json&fl=timestamp,original&collapse=digest"

def _parse_wayback_json(j: List) -> List[Dict[str, str]]:
    out = []
    # Expect first row to be header; rows: [timestamp, original]
    for row in j[1:]:
        if not isinstance(row, list) or len(row) < 2:
            continue
        ts, url = row[0], row[1]
        out.append({"timestamp": ts, "url": url})
    return out

def run(ctx: Dict[str, Any]) -> Dict[str, Any]:
    target = ctx["target"]
    timeout = float(ctx.get("timeout", 15))
    max_results = int(ctx.get("max_results", 200))

    try:
        resp = requests.get(WAYBACK_URL.format(target=target), timeout=timeout)
        resp.raise_for_status()
        if not resp.content:
            return {"snapshots": []}
        data = resp.json()
        snapshots = _parse_wayback_json(data)
        return {"snapshots": snapshots[:max_results], "count": len(snapshots)}
    except requests.HTTPError as e:
        return {"error": f"HTTP {resp.status_code}", "detail": str(e)}
    except ValueError as e:
        return {"error": "invalid_json", "detail": str(e)}
    except Exception as e:
        return {"error": str(e)}
