import requests
from bs4 import BeautifulSoup
import warnings
import re
import sys
import traceback

def _safe_import_wappalyzer():
    """
    Try both common Wappalyzer packages and return (WappalyzerClass, WebPageClass, package_type) or (None,None,None).
    Do lazy import to avoid import-time side-effects in other modules.
    """
    try:
        # python-Wappalyzer (capitalized package)
        from Wappalyzer import Wappalyzer as WappalyzerClass, WebPage as WebPageClass
        return WappalyzerClass, WebPageClass, "python-Wappalyzer"
    except Exception:
        pass
    try:
        # wappalyzer-python (lowercase)
        from wappalyzer import Wappalyzer as WappalyzerClass, WebPage as WebPageClass
        return WappalyzerClass, WebPageClass, "wappalyzer-python"
    except Exception:
        return None, None, None

def _suppress_wappalyzer_regex_warnings():
    """
    Some Wappalyzer versions emit UserWarning about regex compilation (unbalanced parenthesis).
    Temporarily filter such warnings to avoid noisy output while still capturing exceptions.
    """
    warnings.filterwarnings("ignore", message="Caught 'unbalanced parenthesis at position")
    # Keep other warnings intact

def run(ctx):
    """
    ctx: dict with at least {"target": "example.com"}.
    Returns a dict with keys: url, http, wappalyzer (or wappalyzer_error), cms, error.
    """
    target = ctx.get("target")
    if not target:
        return {"error": "No target provided in ctx"}

    # allow target already to include scheme
    if not re.match(r"^https?://", target):
        url = f"https://{target}"
    else:
        url = target

    info = {"url": url, "http": {}, "wappalyzer": {}, "wappalyzer_meta": {}, "cms": []}

    timeout = ctx.get("timeout", 10)
    verify = ctx.get("verify", False)  # default to False to match your previous code

    try:
        # HTTP request
        r = requests.get(url, timeout=timeout, allow_redirects=True, verify=verify)
        info["http"]["status_code"] = r.status_code
        try:
            info["http"]["headers"] = dict(r.headers)
        except Exception:
            info["http"]["headers"] = str(r.headers)
        info["http"]["server"] = r.headers.get("Server")
        html = r.text or ""

        # Lazy import Wappalyzer and attempt analysis
        WappalyzerClass, WebPageClass, pkg_type = _safe_import_wappalyzer()
        if WappalyzerClass and WebPageClass:
            info["wappalyzer_meta"]["package_type"] = pkg_type
            try:
                # suppress known noisy warning from some Wappalyzer regexes
                _suppress_wappalyzer_regex_warnings()

                if pkg_type == "python-Wappalyzer":
                    # python-Wappalyzer API: Wappalyzer.latest() -> instance with analyze(page)
                    try:
                        w = WappalyzerClass.latest() if hasattr(WappalyzerClass, "latest") else WappalyzerClass()
                    except Exception:
                        w = WappalyzerClass()
                    # Build a page object from requests.Response if supported
                    try:
                        if hasattr(WebPageClass, "new_from_response"):
                            page = WebPageClass.new_from_response(r)
                        elif hasattr(WebPageClass, "new_from_url"):
                            page = WebPageClass.new_from_url(url)
                        else:
                            # fallback: try constructing with URL
                            page = WebPageClass(url)
                    except Exception:
                        # as a last resort pass the HTML
                        try:
                            page = WebPageClass(html)
                        except Exception:
                            page = None

                    if page is not None:
                        detected = w.analyze(page)
                        # Normalize detected to a list or dict
                        try:
                            info["wappalyzer"] = list(detected) if hasattr(detected, "__iter__") and not isinstance(detected, dict) else detected
                        except Exception:
                            info["wappalyzer"] = detected
                    else:
                        info["wappalyzer_error"] = "Unable to construct WebPage for python-Wappalyzer"
                else:
                    # wappalyzer-python style
                    try:
                        w = WappalyzerClass()
                    except Exception:
                        w = WappalyzerClass
                    # try WebPage with response, URL, or HTML
                    page = None
                    for attempt in (r, url, html):
                        try:
                            page = WebPageClass(attempt)
                            break
                        except Exception:
                            continue
                    if page is None:
                        info["wappalyzer_error"] = "Unable to construct WebPage for wappalyzer-python"
                    else:
                        # prefer analyze_with_categories if available
                        try:
                            techs = w.analyze_with_categories(page)
                        except Exception:
                            techs = w.analyze(page)
                        info["wappalyzer"] = techs
            except Exception as e:
                info["wappalyzer_error"] = f"{type(e).__name__}: {str(e)}"
                info["_wappalyzer_traceback"] = traceback.format_exc()
        else:
            info["wappalyzer_error"] = "Wappalyzer package not available; install 'python-Wappalyzer' or 'wappalyzer-python'"

        # Simple HTML-based CMS heuristics fallback (safer checks)
        try:
            soup = BeautifulSoup(html, "html.parser")
            cms = set()
            body_text = (soup.get_text(" ", strip=True) or "").lower()
            page_html = html or ""

            # WordPress heuristics
            if soup.find(id=re.compile(r"wp-")) or "wp-content" in page_html or "wp-includes" in page_html or "wordpress" in body_text:
                cms.add("WordPress")
            # Drupal heuristics
            if "drupal.settings" in page_html or "/sites/default/" in page_html or "drupal" in body_text:
                cms.add("Drupal")
            # Joomla heuristics
            if "joomla" in body_text or "com_content" in page_html or "Joomla!" in page_html:
                cms.add("Joomla")
            # Shopify heuristics
            if "cdn.shopify.com" in page_html or "shopify.theme" in page_html:
                cms.add("Shopify")
            # Squarespace heuristics
            if "squarespace.com" in page_html or "sqs-" in page_html:
                cms.add("Squarespace")

            if cms:
                info["cms"] = sorted(list(cms))
        except Exception as e:
            info["cms_error"] = str(e)

    except Exception as e:
        info["error"] = f"{type(e).__name__}: {str(e)}"
        info["_traceback"] = traceback.format_exc()

    return info
