#!/usr/bin/env python3
"""ASERecon v4.0 - Modular authorized security reconnaissance CLI."""

import argparse
import json
import re
import shutil
import socket
import subprocess
from datetime import datetime

import dns.resolver
import requests
import whois
from bs4 import BeautifulSoup


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class Banner:
    @staticmethod
    def show() -> None:
        print(
            f"""
{Colors.RED}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║    █████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗        ║
║   ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║        ║
║   ███████║███████╗█████╗  ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║        ║
║   ██╔══██║╚════██║██╔══╝  ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║        ║
║   ██║  ██║███████║███████╗██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║        ║
║   ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝        ║
║                                                                               ║
║                  ASERecon v4.0 - Modular Security Assessment                 ║
║                  Use ONLY with explicit written authorization                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}"""
        )


class ASEReconCLI:
    MODULES = {
        "dns": "DNS enumeration",
        "whois": "WHOIS lookup",
        "subdomains": "Subdomain discovery",
        "email": "Email intel (theHarvester + SPF/DMARC)",
        "technology": "Technology detection (nmap + web fingerprints)",
        "ports": "Open port + service scan (nmap)",
        "vulns": "Vulnerability scripts scan (nmap --script vuln)",
        "headers": "Security headers check",
    }

    def __init__(self, target: str, verbose: bool = False):
        self.target = target.strip()
        self.verbose = verbose
        self.results = {
            "target": self.target,
            "timestamp": datetime.utcnow().isoformat(),
            "scan_results": {},
        }

    def log(self, message: str, level: str = "INFO") -> None:
        color = Colors.CYAN
        if level == "ERROR":
            color = Colors.RED
        elif level == "WARNING":
            color = Colors.YELLOW
        elif level == "SUCCESS":
            color = Colors.GREEN

        if self.verbose or level in {"ERROR", "WARNING", "SUCCESS"}:
            ts = datetime.utcnow().strftime("%H:%M:%S")
            print(f"{color}[{ts}] [{level}] {message}{Colors.END}")

    def command_exists(self, cmd: str) -> bool:
        return shutil.which(cmd) is not None

    def run_command(self, command: list[str], timeout: int = 240) -> dict:
        """Run command and always capture stdout/stderr for full reporting."""
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return {
                "command": " ".join(command),
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "command": " ".join(command),
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
            }

    def resolve_target_ip(self) -> str | None:
        try:
            return socket.gethostbyname(self.target)
        except Exception:
            return None

    def get_dns_info(self) -> dict:
        self.log("Collecting DNS records...")
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]
        dns_info: dict[str, list[str] | str] = {}

        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(self.target, record_type)
                dns_info[record_type] = [str(a) for a in answers]
            except Exception:
                dns_info[record_type] = []

        ip = self.resolve_target_ip()
        dns_info["ip_address"] = ip or "Not resolved"

        self.results["scan_results"]["dns_info"] = dns_info
        return dns_info

    def get_whois_info(self) -> dict | None:
        self.log("Collecting WHOIS info...")
        try:
            w = whois.whois(self.target)
            info = {
                "domain_name": str(w.domain_name),
                "registrar": str(w.registrar),
                "creation_date": str(w.creation_date),
                "expiration_date": str(w.expiration_date),
                "name_servers": list(w.name_servers)[:10] if w.name_servers else [],
                "emails": w.emails,
                "country": str(w.country),
                "org": str(w.org),
            }
            self.results["scan_results"]["whois_info"] = info
            return info
        except Exception as exc:
            self.log(f"WHOIS failed: {exc}", "WARNING")
            return None

    def get_subdomains(self) -> list[str]:
        self.log("Discovering subdomains (crt.sh + DNS)...")
        found = set()

        try:
            url = f"https://crt.sh/?q=%.{self.target}&output=json"
            r = requests.get(url, timeout=20)
            if r.ok:
                for row in r.json()[:400]:
                    for name in row.get("name_value", "").split("\n"):
                        cleaned = name.strip().lower().replace("*.", "")
                        if cleaned.endswith(self.target) and cleaned != self.target:
                            found.add(cleaned)
        except Exception as exc:
            self.log(f"crt.sh lookup warning: {exc}", "WARNING")

        for common in ["www", "mail", "api", "dev", "admin", "vpn", "portal", "staging", "blog"]:
            try:
                candidate = f"{common}.{self.target}"
                socket.gethostbyname(candidate)
                found.add(candidate)
            except Exception:
                continue

        out = sorted(found)[:150]
        self.results["scan_results"]["subdomains"] = out
        return out

    def get_email_intel(self) -> dict:
        self.log("Collecting email intel (DNS + theHarvester)...")
        data = {
            "mx_records": [],
            "spf_record": None,
            "dmarc_record": None,
            "harvester_emails": [],
            "harvester_raw_output": "",
        }

        try:
            mx = dns.resolver.resolve(self.target, "MX")
            data["mx_records"] = [str(m.exchange) for m in mx]
        except Exception:
            pass

        try:
            txt = dns.resolver.resolve(self.target, "TXT")
            for rec in txt:
                val = str(rec)
                if "v=spf1" in val.lower():
                    data["spf_record"] = val
                    break
        except Exception:
            pass

        try:
            dmarc = dns.resolver.resolve(f"_dmarc.{self.target}", "TXT")
            for rec in dmarc:
                data["dmarc_record"] = str(rec)
                break
        except Exception:
            pass

        if self.command_exists("theHarvester"):
            harvester = self.run_command(["theHarvester", "-d", self.target, "-b", "all"], timeout=420)
            combined = f"{harvester['stdout']}\n{harvester['stderr']}"
            emails = sorted(set(re.findall(r"[a-zA-Z0-9._%+-]+@" + re.escape(self.target), combined, flags=re.I)))
            data["harvester_emails"] = emails[:300]
            data["harvester_raw_output"] = combined
        else:
            data["harvester_raw_output"] = "theHarvester command not found in PATH"
            self.log("theHarvester not installed; email OSINT partially skipped.", "WARNING")

        self.results["scan_results"]["email_intel"] = data
        return data

    def get_open_ports_nmap(self) -> dict:
        self.log("Running nmap port scan...")
        if not self.command_exists("nmap"):
            msg = "nmap command not found in PATH"
            self.log(msg, "WARNING")
            res = {"error": msg}
            self.results["scan_results"]["nmap_ports"] = res
            return res

        cmd = ["nmap", "-Pn", "-p-", "-sV", "--open", self.target]
        result = self.run_command(cmd, timeout=1200)
        open_ports = sorted(set(re.findall(r"^(\d+)/tcp\s+open", result.get("stdout", ""), flags=re.M)))
        payload = {**result, "open_ports": open_ports}
        self.results["scan_results"]["nmap_ports"] = payload
        return payload

    def get_technology_stack(self) -> dict:
        self.log("Detecting technology stack (web + nmap NSE)...")
        findings = {"http_fingerprints": [], "nmap_output": "", "nmap_stderr": ""}

        try:
            r = requests.get(f"https://{self.target}", timeout=12, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            server = r.headers.get("Server")
            powered = r.headers.get("X-Powered-By")
            if server:
                findings["http_fingerprints"].append(f"Server: {server}")
            if powered:
                findings["http_fingerprints"].append(f"X-Powered-By: {powered}")

            soup = BeautifulSoup(r.text, "html.parser")
            html = soup.prettify().lower()
            markers = {
                "wordpress": "CMS: WordPress",
                "drupal": "CMS: Drupal",
                "joomla": "CMS: Joomla",
                "react": "Frontend: React",
                "angular": "Frontend: Angular",
                "vue": "Frontend: Vue",
                "bootstrap": "Frontend: Bootstrap",
            }
            for needle, name in markers.items():
                if needle in html:
                    findings["http_fingerprints"].append(name)
        except Exception as exc:
            self.log(f"HTTP tech detection warning: {exc}", "WARNING")

        if self.command_exists("nmap"):
            cmd = [
                "nmap",
                "-Pn",
                "-sV",
                "--script",
                "http-title,http-server-header,http-enum",
                "-p",
                "80,443,8080,8443",
                self.target,
            ]
            nmap = self.run_command(cmd, timeout=600)
            findings["nmap_output"] = nmap["stdout"]
            findings["nmap_stderr"] = nmap["stderr"]
        else:
            findings["nmap_stderr"] = "nmap command not found in PATH"

        findings["http_fingerprints"] = sorted(set(findings["http_fingerprints"]))
        self.results["scan_results"]["technology"] = findings
        return findings

    def get_vulnerability_scan(self) -> dict:
        self.log("Running nmap vulnerability scripts...")
        if not self.command_exists("nmap"):
            msg = "nmap command not found in PATH"
            self.log(msg, "WARNING")
            payload = {"error": msg}
            self.results["scan_results"]["nmap_vulns"] = payload
            return payload

        cmd = ["nmap", "-Pn", "-sV", "--script", "vuln", self.target]
        result = self.run_command(cmd, timeout=1500)
        cves = sorted(set(re.findall(r"CVE-\d{4}-\d+", result.get("stdout", ""), flags=re.I)))
        payload = {**result, "identified_cves": cves}
        self.results["scan_results"]["nmap_vulns"] = payload
        return payload

    def check_security_headers(self) -> dict:
        self.log("Checking security headers...")
        expected = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy",
        ]
        output = {}
        try:
            r = requests.get(f"https://{self.target}", timeout=12, verify=False)
            for h in expected:
                output[h] = r.headers.get(h, "Missing")
        except Exception as exc:
            output["error"] = str(exc)

        self.results["scan_results"]["security_headers"] = output
        return output

    def module_menu(self) -> list[str]:
        print(f"\n{Colors.BOLD}{Colors.BLUE}Choose scan modules:{Colors.END}")
        keys = list(self.MODULES.keys())
        for idx, key in enumerate(keys, 1):
            print(f"  {idx}. {key:<11} - {self.MODULES[key]}")
        print("  a. all       - Run every module")

        raw = input("\nSelect modules (e.g., 1,4,6 or a): ").strip().lower()
        if raw in {"a", "all", ""}:
            return keys

        selected = []
        for part in [p.strip() for p in raw.split(",") if p.strip()]:
            if part.isdigit() and 1 <= int(part) <= len(keys):
                selected.append(keys[int(part) - 1])
            elif part in self.MODULES:
                selected.append(part)
        return sorted(set(selected)) or keys

    def run_selected(self, modules: list[str]) -> None:
        runners = {
            "dns": self.get_dns_info,
            "whois": self.get_whois_info,
            "subdomains": self.get_subdomains,
            "email": self.get_email_intel,
            "technology": self.get_technology_stack,
            "ports": self.get_open_ports_nmap,
            "vulns": self.get_vulnerability_scan,
            "headers": self.check_security_headers,
        }

        for module in modules:
            print(f"\n{Colors.BOLD}{Colors.BLUE}=== {module.upper()} ==={Colors.END}")
            result = runners[module]()
            print(json.dumps(result, indent=2, default=str)[:12000])

    def save_results(self, filename: str | None = None) -> str | None:
        out = filename or f"aserecon_{self.target}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, default=str)
            return out
        except Exception as exc:
            self.log(f"Failed to save JSON output: {exc}", "ERROR")
            return None


def show_help() -> None:
    keys = ", ".join(ASEReconCLI.MODULES.keys())
    print(
        f"""
{Colors.BOLD}ASERecon v4.0 (Modular){Colors.END}
Usage:
  python asetool.py -t <target> [options]

Options:
  -t, --target        Target domain/IP
  -m, --modules       Comma-separated modules ({keys})
  --non-interactive   Do not show module picker; use --modules or run all
  -o, --output        Custom JSON output filename
  -v, --verbose       Verbose logs
  --no-save           Do not save JSON output
  -h, --help          Show help
"""
    )


def main() -> None:
    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
    Banner.show()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-t", "--target", help="Target domain or IP")
    parser.add_argument("-m", "--modules", help="Comma-separated module names")
    parser.add_argument("--non-interactive", action="store_true", help="Disable module menu")
    parser.add_argument("-o", "--output", help="Output JSON filename")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument("--no-save", action="store_true", help="Skip JSON save")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    args = parser.parse_args()

    if args.help or not args.target:
        show_help()
        return

    print(f"{Colors.YELLOW}{Colors.BOLD}LEGAL NOTICE{Colors.END}")
    print("Use only on systems you own or are authorized to test in writing.")
    if input(f"Proceed with target {args.target}? type 'yes': ").strip().lower() != "yes":
        print("Aborted.")
        return

    recon = ASEReconCLI(args.target, verbose=args.verbose)

    if args.non_interactive:
        if args.modules:
            modules = [m.strip() for m in args.modules.split(",") if m.strip() in ASEReconCLI.MODULES]
            modules = modules or list(ASEReconCLI.MODULES.keys())
        else:
            modules = list(ASEReconCLI.MODULES.keys())
    else:
        modules = recon.module_menu()

    recon.run_selected(modules)

    if not args.no_save:
        output_file = recon.save_results(args.output)
        if output_file:
            print(f"\n{Colors.GREEN}Saved full results to {output_file}{Colors.END}")


if __name__ == "__main__":
    main()
