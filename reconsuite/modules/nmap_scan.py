import nmap, shlex, subprocess

def run(ctx):
    target = ctx["target"]
    args = ctx.get("nmap_args","-sV -p-")
    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=target, arguments=args)
        hosts = {}
        for h in nm.all_hosts():
            hosts[h] = {"status": nm[h].state(), "tcp": {}}
            for proto in nm[h].all_protocols():
                lport = nm[h][proto].keys()
                for p in lport:
                    hosts[h]["tcp"][p] = nm[h][proto][p]
        return {"nmap": hosts}
    except Exception as e:
        try:
            cmd = f"nmap {args} {target} -oX -"
            proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=300)
            return {"nmap_xml": proc.stdout}
        except Exception as e2:
            return {"error": str(e2)}
