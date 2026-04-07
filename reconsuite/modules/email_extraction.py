import requests
import re
import subprocess
import shutil
import time
import os
import signal
from bs4 import BeautifulSoup
from typing import Set, Optional

COMMON_PATHS = ["/", "/contact", "/about", "/team", "/employees", "/staff", "/contact-us"]
# improved email regex (keeps it simple but avoids trailing punctuation)
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")

def _get_with_retries(url: str, timeout: int = 8, retries: int = 2, backoff: float = 0.5) -> Optional[str]:
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, timeout=timeout, verify=False)
            if r.status_code == 200:
                return r.text
            return None
        except requests.RequestException:
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            else:
                return None

def _run_theharvester(cmd: list[str], timeout: int = 120) -> str:
    # Launch in its own process group so we can kill the whole group on timeout
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    try:
        out, err = proc.communicate(timeout=timeout)
        return (out or "") + (err or "")
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            out, err = proc.communicate(timeout=5)
            return "TIMEOUT: terminated\n" + (out or "") + (err or "")
        except Exception:
            os.killpg(proc.pid, signal.SIGKILL)
            return "TIMEOUT: killed\n"
    except Exception as e:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            pass
        return f"ERROR: {e}"

def run(ctx):
    target = ctx["target"]
    base = f"https://{target}"
    found: Set[str] = set()

    # Quick crawl of common paths
    for p in COMMON_PATHS:
        html = _get_with_retries(base + p, timeout=8, retries=2)
        if not html:
            continue
        # Extract emails
        found.update(EMAIL_RE.findall(html))
        # Also check for mailto links
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("mailto:"):
                    addr = href.split("mailto:")[1].split("?")[0]
                    if EMAIL_RE.fullmatch(addr):
                        found.add(addr)
        except Exception:
            pass

    # Optionally run theHarvester if available
    harv = shutil.which("theHarvester")
    harv_out = None
    if harv:
        # Prefer XML output to a temp file to avoid massive stdout; use temp path per-target
        out_path = f"/tmp/harv_{target.replace('/', '_')}.xml"
        cmd = [harv, "-d", target, "-b", "all", "-f", out_path]
        try:
            harv_out = _run_theharvester(cmd, timeout=int(ctx.get("harv_timeout", 120)))
            # If XML file was produced, read it safely (small size assumed)
            if os.path.exists(out_path):
                try:
                    with open(out_path, "r", encoding="utf-8", errors="ignore") as fh:
                        harv_xml = fh.read()
                    # try to extract emails from the XML as a fallback
                    found.update(EMAIL_RE.findall(harv_xml))
                    harv_out = {"cmd_output": harv_out, "xml_path": out_path}
                except Exception as e:
                    harv_out = {"cmd_output": harv_out, "xml_read_error": str(e)}
        except Exception as e:
            harv_out = {"error": str(e)}

    return {"emails": sorted(found), "theHarvester": harv_out}
