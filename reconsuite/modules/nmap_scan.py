import shlex
import subprocess
import json
from typing import Dict, Any

def run(ctx: Dict[str, Any]) -> Dict[str, Any]:
    target = ctx["target"]
    args = ctx.get("nmap_args", "-sV -p-")
    timeout = int(ctx.get("timeout", 300))

    # Try using python-nmap's PortScanner if available
    try:
        import nmap
    except Exception:
        nmap = None

    if nmap:
        try:
            nm = nmap.PortScanner()
            nm.scan(hosts=target, arguments=args, timeout=timeout)
            hosts = {}
            for h in nm.all_hosts():
                hosts[h] = {"status": nm[h].state(), "tcp": {}}
                # iterate all protocols present for the host
                for proto in nm[h].all_protocols():
                    # get ports (keys) and sort them as integers
                    ports = sorted(int(p) for p in nm[h][proto].keys())
                    for p in ports:
                        # ensure port info is a regular dict (not nmap.PortScannerResult internals)
                        hosts[h]["tcp"][p] = dict(nm[h][proto][str(p)])
                # include hostnames if present
                if nm[h].hostname():
                    hosts[h]["hostname"] = nm[h].hostname()
            return {"nmap": hosts}
        except Exception as e:
            # fall through to subprocess fallback, but capture exception message
            python_nmap_error = str(e)
    else:
        python_nmap_error = "python-nmap not installed or failed to import"

    # Fallback: run nmap binary and return XML output (or raw stdout/stderr)
    try:
        cmd = f"nmap {args} {target} -oX -"
        proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        result = {
            "nmap_xml": proc.stdout,
            "returncode": proc.returncode,
            "stderr": proc.stderr,
            "fallback_reason": python_nmap_error,
        }
        return result
    except Exception as e2:
        return {"error": str(e2), "fallback_reason": python_nmap_error}
