from .modules import dns, whois_lookup, subdomains, email_security, tech_detect, shodan_integration, wayback, security_headers, email_extraction, nmap_scan, risk_assessment
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
    def __init__(self, target, shodan_key=None, nmap_args=None):
        self.target = target
        self.shodan_key = shodan_key
        self.nmap_args = nmap_args or "-sV -p-"
        self.context = {"target": target, "shodan_key": shodan_key, "nmap_args": self.nmap_args}

    def run_modules(self, modules):
        report = {"target": self.target, "modules": {}}
        for m in modules:
            mod = MODULE_MAP.get(m)
            if not mod:
                report["modules"][m] = {"error":"unknown module"}
                continue
            try:
                data = mod.run(self.context)
                report["modules"][m] = data
            except Exception as e:
                report["modules"][m] = {"error": str(e)}
        if "risk" not in modules:
            report["modules"]["risk"] = risk_assessment.run({"report":report})
        return report

    def save_output(self, report, filename):
        save_json(report, filename)
        save_html(report, filename.replace(".json",".html"))
