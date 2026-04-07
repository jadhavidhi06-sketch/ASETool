import os
import json
import html
from typing import Dict, Any

# Import your modules here (must exist in your package)
from .modules import (
    dns,
    whois_lookup,
    subdomains,
    email_security,
    tech_detect,
    shodan_integration,
    wayback,
    security_headers,
    email_extraction,
    nmap_scan,
    risk_assessment,
)
from .utils.output import save_json, save_html

MODULE_MAP = {
    "dns": dns,
    "whois": whois_lookup,
    "subdomains": subdomains,
    "emailsec": email_security,
    "tech": tech_detect,
    "shodan": shodan_integration,
    "wayback": wayback,
    "headers": security_headers,
    "emails": email_extraction,
    "nmap": nmap_scan,
    "risk": risk_assessment,
}


class ReconSuite:
    def __init__(self, target: str, shodan_key: str = None, nmap_args: str = None):
        self.target = target
        self.shodan_key = shodan_key
        self.nmap_args = nmap_args or "-sV -p-"
        # base context provided to modules (copy for each call)
        self.base_context: Dict[str, Any] = {
            "target": target,
            "shodan_key": shodan_key,
            "nmap_args": self.nmap_args,
        }

    def run_modules(self, modules):
        """
        Run modules in the order provided. Each module gets a shallow copy of base_context
        with report injected under 'report'. Partial discoveries (subdomains, crtsh) are
        consolidated into a subdomains_aggregate entry for downstream modules.
        """
        report: Dict[str, Any] = {"target": self.target, "modules": {}}
        # aggregated discovery buckets
        aggregated = {"subdomains": set(), "crtsh": set()}

        for m in modules:
            mod = MODULE_MAP.get(m)
            if not mod:
                report["modules"][m] = {"error": "unknown module"}
                continue

            # Build module context (shallow copy) and include current report snapshot
            ctx = dict(self.base_context)
            ctx["report"] = report

            # Provide aggregated subdomains if available
            if aggregated["subdomains"]:
                ctx["subdomains"] = sorted(aggregated["subdomains"])

            try:
                data = mod.run(ctx)
                report["modules"][m] = data
            except Exception as e:
                report["modules"][m] = {"error": str(e)}
                data = report["modules"][m]

            # Merge discoveries into aggregated store for subsequent modules
            if isinstance(data, dict):
                # subdomains module style: may expose "brute" or "resolved" keys
                brute = data.get("brute") or []
                if isinstance(brute, (list, set)):
                    aggregated["subdomains"].update(brute)
                # crt.sh results
                crt = data.get("crtsh") or []
                if isinstance(crt, (list, set)):
                    aggregated["crtsh"].update(crt)
                # if the module returned resolved dict (host -> ips), include keys
                resolved = data.get("resolved") or {}
                if isinstance(resolved, dict):
                    aggregated["subdomains"].update(resolved.keys())

        # Store aggregated lists back into report for visibility
        report["modules"]["subdomains_aggregate"] = {
            "subdomains": sorted(aggregated["subdomains"]),
            "crtsh": sorted(aggregated["crtsh"]),
        }

        # Ensure risk assessment runs last and sees the final report
        if "risk" not in modules:
            try:
                report["modules"]["risk"] = risk_assessment.run({"report": report})
            except Exception as e:
                report["modules"]["risk"] = {"error": str(e)}

        return report

    def save_output(self, report: Dict[str, Any], filename: str):
        # Ensure parent directory exists
        outdir = os.path.dirname(filename) or "."
        os.makedirs(outdir, exist_ok=True)
        # Save JSON
        save_json(report, filename)
        # Save basic HTML representation
        save_html(report, filename.replace(".json", ".html"))
