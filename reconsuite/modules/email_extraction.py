import requests, re, subprocess, shutil
from bs4 import BeautifulSoup

COMMON_PATHS = ["/","/contact","/about","/team","/employees","/staff","/contact-us"]
EMAIL_RE = re.compile(r"[a-zA-Z0-9.\-+_]+@[a-zA-Z0-9.\-+_]+\.[a-zA-Z]+")

def run(ctx):
    target = ctx["target"]
    base = f"https://{target}"
    found = set()
    for p in COMMON_PATHS:
        try:
            r = requests.get(base+p, timeout=8, verify=False)
            if r.status_code==200:
                found.update(EMAIL_RE.findall(r.text))
        except:
            pass
    harv = shutil.which("theHarvester")
    harv_out = None
    if harv:
        try:
            proc = subprocess.run([harv, "-d", target, "-b", "all", "-f", "/tmp/harv.xml"], capture_output=True, text=True, timeout=120)
            harv_out = proc.stdout + proc.stderr
        except Exception as e:
            harv_out = str(e)
    return {"emails": sorted(found), "theHarvester": harv_out}
