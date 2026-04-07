import requests
from bs4 import BeautifulSoup
from wappalyzer import Wappalyzer, WebPage

def run(ctx):
    target = ctx["target"]
    url = f"https://{target}"
    info = {"url": url, "http": {}, "wappalyzer": {}}
    try:
        r = requests.get(url, timeout=10, allow_redirects=True, verify=False)
        info["http"]["status_code"] = r.status_code
        info["http"]["headers"] = dict(r.headers)
        info["http"]["server"] = r.headers.get("Server")
        html = r.text
        try:
            w = Wappalyzer.latest()
            page = WebPage.new_from_url(url)
            detected = w.analyze(page)
            info["wappalyzer"] = list(detected)
        except Exception as e:
            info["wappalyzer_error"] = str(e)
        soup = BeautifulSoup(html, "html.parser")
        if soup.find(id="wp-content") or "wp-" in html:
            info.setdefault("cms",[]).append("WordPress")
        if "Drupal.settings" in html:
            info.setdefault("cms",[]).append("Drupal")
    except Exception as e:
        info["error"] = str(e)
    return info
