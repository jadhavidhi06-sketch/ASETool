import requests
from bs4 import BeautifulSoup

# Compatibility imports for different python Wappalyzer packages
try:
    # python-Wappalyzer (capitalized package)
    from Wappalyzer import Wappalyzer, WebPage
    WAPPALYZER_TYPE = "python-Wappalyzer"
except Exception:
    try:
        # wappalyzer-python or other lowercase package
        from wappalyzer import Wappalyzer, WebPage
        WAPPALYZER_TYPE = "wappalyzer-python"
    except Exception:
        Wappalyzer = None
        WebPage = None
        WAPPALYZER_TYPE = None

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

        # Try using Wappalyzer if available
        if Wappalyzer and WebPage:
            try:
                if WAPPALYZER_TYPE == "python-Wappalyzer":
                    w = Wappalyzer.latest()
                    page = WebPage.new_from_response(r) if hasattr(WebPage, "new_from_response") else WebPage.new_from_url(url)
                    detected = w.analyze(page)
                    # detected may be dict-like; normalize to list
                    info["wappalyzer"] = list(detected) if hasattr(detected, "__iter__") else detected
                else:
                    # wappalyzer-python style
                    w = Wappalyzer()
                    # WebPage may accept either a requests.Response or URL
                    try:
                        page = WebPage(r)
                    except Exception:
                        page = WebPage(url)
                    try:
                        techs = w.analyze_with_categories(page)
                    except Exception:
                        techs = w.analyze(page)
                    info["wappalyzer"] = techs
                info["wappalyzer_meta"] = {"package_type": WAPPALYZER_TYPE}
            except Exception as e:
                info["wappalyzer_error"] = str(e)
        else:
            info["wappalyzer_error"] = "Wappalyzer package not available; install 'python-Wappalyzer' or 'wappalyzer-python'"

        # Simple HTML-based CMS heuristics fallback
        soup = BeautifulSoup(html, "html.parser")
        cms = []
        if soup.find(id="wp-content") or "wp-" in html:
            cms.append("WordPress")
        if "Drupal.settings" in html:
            cms.append("Drupal")
        if "Joomla!" in html or "com_content" in html:
            cms.append("Joomla")
        if cms:
            info["cms"] = cms

    except Exception as e:
        info["error"] = str(e)

    return info
