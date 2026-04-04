#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ASERecon v3.0 - Advanced CLI Security Tool                  ║
║                  Social Engineering Reconnaissance & OSINT Suite               ║
║                          Authorized Use Only                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Advanced Social Engineering Reconnaissance Tool - CLI Version
For authorized security testing and educational purposes ONLY
"""

import requests
import re
import json
import argparse
import sys
import time
from datetime import datetime
import hashlib
from urllib.parse import urlparse
import whois
import dns.resolver
from bs4 import BeautifulSoup
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import os
from collections import Counter

# Try to import Shodan
try:
    import shodan
    SHODAN_AVAILABLE = True
except ImportError:
    SHODAN_AVAILABLE = False

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class Banner:
    @staticmethod
    def show():
        banner = f"""
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
║                    Advanced CLI Security Tool v3.0                            ║
║              Social Engineering Reconnaissance & OSINT Suite                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}
{Colors.YELLOW}{Colors.BOLD}[!] LEGAL DISCLAIMER: Use only on systems you own or have written permission to test{Colors.END}
{Colors.CYAN}[*] Authorized security testing and educational purposes only{Colors.END}
        """
        print(banner)

class ASEReconCLI:
    """Advanced Social Engineering Reconnaissance Tool - CLI Version"""
    
    def __init__(self, target, shodan_api_key=None, verbose=False):
        self.target = target
        self.shodan_api_key = shodan_api_key
        self.verbose = verbose
        self.results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "scan_results": {}
        }
        
    def log(self, message, level="INFO", color=Colors.CYAN):
        if self.verbose or level in ["ERROR", "WARNING", "SUCCESS"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if level == "ERROR":
                color = Colors.RED
                icon = "✘"
            elif level == "SUCCESS":
                color = Colors.GREEN
                icon = "✓"
            elif level == "WARNING":
                color = Colors.YELLOW
                icon = "⚠"
            else:
                icon = "→"
            print(f"{color}[{timestamp}] [{level}] {icon} {message}{Colors.END}")
    
    def print_section(self, title):
        """Print formatted section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}[+] {title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    
    def get_dns_info(self):
        """Fetch DNS information (no API required)"""
        self.log("Fetching DNS information...", "INFO")
        
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME', 'PTR']
        dns_info = {}
        
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(self.target, record_type)
                dns_info[record_type] = [str(answer) for answer in answers]
            except dns.resolver.NoAnswer:
                dns_info[record_type] = []
            except Exception as e:
                if self.verbose:
                    dns_info[record_type] = [f"Error: {str(e)}"]
        
        # Reverse DNS
        try:
            ip_address = socket.gethostbyname(self.target)
            reverse_dns = socket.gethostbyaddr(ip_address)[0]
            dns_info['reverse_dns'] = reverse_dns
            dns_info['ip_address'] = ip_address
        except:
            dns_info['reverse_dns'] = "Not available"
            dns_info['ip_address'] = "Not resolved"
        
        self.results["scan_results"]["dns_info"] = dns_info
        return dns_info
    
    def display_dns_info(self, dns_info):
        """Display DNS information in formatted output"""
        print(f"\n{Colors.BOLD}DNS Records:{Colors.END}")
        for record, values in dns_info.items():
            if values and record not in ['reverse_dns', 'ip_address']:
                print(f"  {Colors.GREEN}{record}:{Colors.END}")
                for value in values[:5]:
                    print(f"    └─ {value}")
        
        if 'ip_address' in dns_info:
            print(f"\n  {Colors.BOLD}IP Address:{Colors.END} {dns_info['ip_address']}")
        if 'reverse_dns' in dns_info:
            print(f"  {Colors.BOLD}Reverse DNS:{Colors.END} {dns_info['reverse_dns']}")
    
    def get_whois_info(self):
        """Get WHOIS information (no API required)"""
        self.log("Fetching WHOIS information...", "INFO")
        
        try:
            w = whois.whois(self.target)
            info = {
                "domain_name": w.domain_name,
                "registrar": w.registrar,
                "creation_date": str(w.creation_date) if w.creation_date else "Unknown",
                "expiration_date": str(w.expiration_date) if w.expiration_date else "Unknown",
                "name_servers": w.name_servers[:5] if w.name_servers else [],
                "org": w.org,
                "country": w.country,
                "email": w.emails if hasattr(w, 'emails') else "Not found"
            }
            self.results["scan_results"]["whois_info"] = info
            return info
        except Exception as e:
            self.log(f"Error fetching WHOIS: {e}", "WARNING")
            return None
    
    def display_whois_info(self, whois_info):
        """Display WHOIS information"""
        if not whois_info:
            print(f"  {Colors.RED}WHOIS information not available{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Domain Registration:{Colors.END}")
        print(f"  {Colors.GREEN}Registrar:{Colors.END} {whois_info.get('registrar', 'Unknown')}")
        print(f"  {Colors.GREEN}Organization:{Colors.END} {whois_info.get('org', 'Unknown')}")
        print(f"  {Colors.GREEN}Country:{Colors.END} {whois_info.get('country', 'Unknown')}")
        print(f"  {Colors.GREEN}Created:{Colors.END} {whois_info.get('creation_date', 'Unknown')}")
        print(f"  {Colors.GREEN}Expires:{Colors.END} {whois_info.get('expiration_date', 'Unknown')}")
        if whois_info.get('name_servers'):
            print(f"  {Colors.GREEN}Name Servers:{Colors.END}")
            for ns in whois_info['name_servers'][:3]:
                print(f"    └─ {ns}")
    
    def get_subdomains(self):
        """Discover subdomains using certificate transparency and DNS (no API required)"""
        self.log("Discovering subdomains...", "INFO")
        
        subdomains = set()
        
        # Method 1: Certificate Transparency logs
        try:
            crt_sh_url = f"https://crt.sh/?q=%.{self.target}&output=json"
            response = requests.get(crt_sh_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for entry in data[:200]:
                    if 'name_value' in entry:
                        names = entry['name_value'].split('\n')
                        for name in names:
                            if self.target in name and name != self.target:
                                subdomains.add(name.lower())
            self.log(f"Found {len(subdomains)} subdomains from certificate logs", "SUCCESS")
        except Exception as e:
            self.log(f"Error fetching from crt.sh: {e}", "WARNING")
        
        # Method 2: Common subdomain bruteforce
        common_subdomains = ['www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk', 
                            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm', 'imap', 'test', 'ns',
                            'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news', 'vpn', 'ns3', 'mail2',
                            'new', 'mysql', 'old', 'lists', 'support', 'mobile', 'mx', 'static', 'docs',
                            'beta', 'shop', 'sql', 'secure', 'demo', 'cp', 'calendar', 'wiki', 'web', 'media',
                            'email', 'images', 'img', 'download', 'dns', 'piwik', 'stats', 'dashboard']
        
        for sub in common_subdomains:
            try:
                test_domain = f"{sub}.{self.target}"
                socket.gethostbyname(test_domain)
                subdomains.add(test_domain)
            except:
                pass
        
        self.results["scan_results"]["subdomains"] = list(subdomains)[:50]
        return list(subdomains)[:50]
    
    def display_subdomains(self, subdomains):
        """Display discovered subdomains"""
        if not subdomains:
            print(f"  {Colors.YELLOW}No subdomains discovered{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Discovered Subdomains ({len(subdomains)}):{Colors.END}")
        for i, sub in enumerate(subdomains[:20], 1):
            print(f"  {i:2}. {Colors.CYAN}{sub}{Colors.END}")
        if len(subdomains) > 20:
            print(f"  ... and {len(subdomains) - 20} more")
    
    def get_email_patterns(self):
        """Analyze email patterns (no API required)"""
        self.log("Analyzing email patterns...", "INFO")
        
        email_info = {
            "domain": self.target,
            "common_patterns": [],
            "mx_records": [],
            "spf_record": None,
            "dmarc_record": None
        }
        
        # Get MX records
        try:
            mx = dns.resolver.resolve(self.target, 'MX')
            email_info["mx_records"] = [str(m.exchange) for m in mx]
        except:
            pass
        
        # Get SPF record
        try:
            txt = dns.resolver.resolve(self.target, 'TXT')
            for record in txt:
                if 'v=spf1' in str(record):
                    email_info["spf_record"] = str(record)[:200]
                    break
        except:
            pass
        
        # Get DMARC record
        try:
            dmarc = dns.resolver.resolve(f'_dmarc.{self.target}', 'TXT')
            for record in dmarc:
                email_info["dmarc_record"] = str(record)[:200]
                break
        except:
            pass
        
        # Common email patterns
        patterns = [
            "first@domain",
            "first.last@domain",
            "firstlast@domain",
            "f.last@domain",
            "firstl@domain",
            "flast@domain"
        ]
        
        self.results["scan_results"]["email_patterns"] = email_info
        return email_info
    
    def display_email_info(self, email_info):
        """Display email security information"""
        print(f"\n{Colors.BOLD}Email Security Analysis:{Colors.END}")
        
        if email_info.get('mx_records'):
            print(f"  {Colors.GREEN}MX Records:{Colors.END}")
            for mx in email_info['mx_records'][:3]:
                print(f"    └─ {mx}")
        
        print(f"\n  {Colors.BOLD}SPF Record:{Colors.END}")
        if email_info.get('spf_record'):
            print(f"    {Colors.GREEN}✓ Present{Colors.END}")
            if self.verbose:
                print(f"    └─ {email_info['spf_record']}")
        else:
            print(f"    {Colors.RED}✗ Missing - Email spoofing possible{Colors.END}")
        
        print(f"\n  {Colors.BOLD}DMARC Record:{Colors.END}")
        if email_info.get('dmarc_record'):
            print(f"    {Colors.GREEN}✓ Present{Colors.END}")
            if self.verbose:
                print(f"    └─ {email_info['dmarc_record']}")
        else:
            print(f"    {Colors.RED}✗ Missing - No email authentication{Colors.END}")
    
    def get_technology_stack(self):
        """Detect technology stack (no API required)"""
        self.log("Detecting technology stack...", "INFO")
        
        technologies = []
        
        try:
            url = f"http://{self.target}"
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            headers = response.headers
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Server headers
            if 'Server' in headers:
                technologies.append(f"Web Server: {headers['Server']}")
            if 'X-Powered-By' in headers:
                technologies.append(f"Framework: {headers['X-Powered-By']}")
            
            # JavaScript frameworks
            js_indicators = {
                'jQuery': ['jquery', 'jQuery'],
                'React': ['react', 'ReactDOM'],
                'Angular': ['angular', 'ng-app'],
                'Vue.js': ['vue', 'Vue'],
                'Bootstrap': ['bootstrap', 'popper']
            }
            
            for tech, indicators in js_indicators.items():
                for indicator in indicators:
                    if indicator.lower() in response.text.lower():
                        technologies.append(f"Frontend: {tech}")
                        break
            
            # CMS detection
            cms_indicators = {
                'WordPress': ['wp-content', 'wp-includes', 'wordpress'],
                'Drupal': ['drupal', 'Drupal'],
                'Joomla': ['joomla', 'Joomla'],
                'Magento': ['magento', 'Magento']
            }
            
            for cms, indicators in cms_indicators.items():
                for indicator in indicators:
                    if indicator.lower() in response.text.lower():
                        technologies.append(f"CMS: {cms}")
                        break
            
            # Security headers
            security_headers = ['Strict-Transport-Security', 'Content-Security-Policy', 'X-Frame-Options']
            present_headers = [h for h in security_headers if h in headers]
            if present_headers:
                technologies.append(f"Security Headers: {', '.join(present_headers)}")
            
        except Exception as e:
            self.log(f"Error detecting technologies: {e}", "WARNING")
        
        self.results["scan_results"]["technologies"] = list(set(technologies))
        return list(set(technologies))
    
    def display_technologies(self, technologies):
        """Display detected technologies"""
        if not technologies:
            print(f"  {Colors.YELLOW}No technologies detected{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Detected Technologies:{Colors.END}")
        for tech in technologies:
            print(f"  {Colors.GREEN}▶{Colors.END} {tech}")
    
    def search_shodan(self):
        """Search Shodan for host information (requires API key)"""
        if not self.shodan_api_key:
            self.log("Shodan API key not provided. Skipping Shodan search.", "WARNING")
            return None
        
        if not SHODAN_AVAILABLE:
            self.log("Shodan library not installed. Install with: pip install shodan", "WARNING")
            return None
        
        self.log("Searching Shodan...", "INFO")
        
        try:
            api = shodan.Shodan(self.shodan_api_key)
            ip = socket.gethostbyname(self.target)
            host = api.host(ip)
            
            shodan_info = {
                "ip": ip,
                "organization": host.get('org', 'Unknown'),
                "isp": host.get('isp', 'Unknown'),
                "country": host.get('country_name', 'Unknown'),
                "open_ports": host.get('ports', [])[:20],
                "vulnerabilities": list(host.get('vulns', {}).keys())[:10],
                "services": []
            }
            
            for service in host.get('data', [])[:10]:
                shodan_info["services"].append({
                    "port": service.get('port'),
                    "service": service.get('service'),
                    "product": service.get('product', 'Unknown')
                })
            
            self.results["scan_results"]["shodan"] = shodan_info
            self.log(f"Shodan: Found {len(shodan_info['open_ports'])} open ports", "SUCCESS")
            return shodan_info
            
        except shodan.APIError as e:
            self.log(f"Shodan API error: {e}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Shodan search error: {e}", "ERROR")
            return None
    
    def display_shodan_info(self, shodan_info):
        """Display Shodan information"""
        if not shodan_info:
            print(f"  {Colors.YELLOW}Shodan information not available (API key required){Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Shodan Intelligence:{Colors.END}")
        print(f"  {Colors.GREEN}Organization:{Colors.END} {shodan_info.get('organization', 'Unknown')}")
        print(f"  {Colors.GREEN}ISP:{Colors.END} {shodan_info.get('isp', 'Unknown')}")
        print(f"  {Colors.GREEN}Country:{Colors.END} {shodan_info.get('country', 'Unknown')}")
        
        if shodan_info.get('open_ports'):
            print(f"\n  {Colors.BOLD}Open Ports ({len(shodan_info['open_ports'])}):{Colors.END}")
            ports = sorted(shodan_info['open_ports'])[:15]
            print(f"    {', '.join(map(str, ports))}")
        
        if shodan_info.get('vulnerabilities'):
            print(f"\n  {Colors.RED}Known Vulnerabilities:{Colors.END}")
            for vuln in shodan_info['vulnerabilities'][:5]:
                print(f"    • {vuln}")
        
        if shodan_info.get('services'):
            print(f"\n  {Colors.BOLD}Services:{Colors.END}")
            for service in shodan_info['services'][:5]:
                print(f"    • Port {service['port']}: {service.get('product', service['service'])}")
    
    def get_archive_info(self):
        """Get archived website information (no API required)"""
        self.log("Checking Wayback Machine archives...", "INFO")
        
        try:
            api_url = f"https://archive.org/wayback/available?url={self.target}"
            response = requests.get(api_url, timeout=10)
            data = response.json()
            
            if data.get('archived_snapshots'):
                snapshots = data['archived_snapshots']
                archive_info = {
                    "available": True,
                    "closest_url": snapshots.get('closest', {}).get('url'),
                    "timestamp": snapshots.get('closest', {}).get('timestamp')
                }
            else:
                archive_info = {"available": False}
            
            self.results["scan_results"]["archive"] = archive_info
            return archive_info
            
        except Exception as e:
            self.log(f"Error fetching archive info: {e}", "WARNING")
            return None
    
    def display_archive_info(self, archive_info):
        """Display archive information"""
        if not archive_info or not archive_info.get('available'):
            print(f"  {Colors.YELLOW}No archived versions found{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Wayback Machine Archive:{Colors.END}")
        print(f"  {Colors.GREEN}Archived Version Available:{Colors.END} Yes")
        if archive_info.get('timestamp'):
            print(f"  {Colors.GREEN}Snapshot Date:{Colors.END} {archive_info['timestamp']}")
        if archive_info.get('closest_url'):
            print(f"  {Colors.GREEN}Archive URL:{Colors.END} {archive_info['closest_url'][:80]}...")
    
    def check_security_headers(self):
        """Check security headers configuration (no API required)"""
        self.log("Checking security headers...", "INFO")
        
        security_checks = {}
        
        try:
            url = f"https://{self.target}"
            response = requests.get(url, timeout=10, verify=False)
            headers = response.headers
            
            checks = {
                "Strict-Transport-Security": "HSTS enabled",
                "Content-Security-Policy": "CSP configured",
                "X-Frame-Options": "Clickjacking protection",
                "X-Content-Type-Options": "MIME sniffing protection",
                "Referrer-Policy": "Referrer policy set",
                "X-XSS-Protection": "XSS protection"
            }
            
            for header, description in checks.items():
                if header in headers:
                    security_checks[description] = f"✓ Present: {headers[header][:50]}"
                else:
                    security_checks[description] = "✗ Missing"
            
            self.results["scan_results"]["security_headers"] = security_checks
            return security_checks
            
        except Exception as e:
            self.log(f"Error checking security headers: {e}", "WARNING")
            return None
    
    def display_security_headers(self, security_checks):
        """Display security headers status"""
        if not security_checks:
            print(f"  {Colors.YELLOW}Could not check security headers{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Security Headers Analysis:{Colors.END}")
        for check, status in security_checks.items():
            if "✓" in status:
                print(f"  {Colors.GREEN}✓{Colors.END} {check}: {Colors.CYAN}Configured{Colors.END}")
            else:
                print(f"  {Colors.RED}✗{Colors.END} {check}: {Colors.RED}Missing{Colors.END}")
    
    def extract_emails_from_web(self):
        """Extract email addresses from website (no API required)"""
        self.log("Extracting email addresses from web...", "INFO")
        
        emails = set()
        
        try:
            url = f"https://{self.target}"
            response = requests.get(url, timeout=10, verify=False)
            
            # Find all email addresses
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            found_emails = re.findall(email_pattern, response.text)
            emails.update(found_emails)
            
            # Also check common pages
            common_pages = ['/contact', '/about', '/team', '/support']
            for page in common_pages:
                try:
                    page_url = f"https://{self.target}{page}"
                    page_response = requests.get(page_url, timeout=5, verify=False)
                    page_emails = re.findall(email_pattern, page_response.text)
                    emails.update(page_emails)
                except:
                    pass
            
        except Exception as e:
            self.log(f"Error extracting emails: {e}", "WARNING")
        
        self.results["scan_results"]["emails_found"] = list(emails)[:20]
        return list(emails)[:20]
    
    def display_emails(self, emails):
        """Display extracted emails"""
        if not emails:
            print(f"  {Colors.YELLOW}No email addresses found{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Extracted Email Addresses ({len(emails)}):{Colors.END}")
        for email in emails[:10]:
            print(f"  {Colors.CYAN}•{Colors.END} {email}")
        if len(emails) > 10:
            print(f"  ... and {len(emails) - 10} more")
    
    def generate_risk_assessment(self):
        """Generate risk assessment based on findings"""
        self.log("Generating risk assessment...", "INFO")
        
        risk_score = 0
        findings = []
        
        # Check email security
        email_info = self.results["scan_results"].get("email_patterns", {})
        if not email_info.get("spf_record"):
            risk_score += 15
            findings.append("Missing SPF record - Email spoofing risk")
        if not email_info.get("dmarc_record"):
            risk_score += 15
            findings.append("Missing DMARC record - No email authentication")
        
        # Check security headers
        security_headers = self.results["scan_results"].get("security_headers", {})
        missing_headers = [k for k, v in security_headers.items() if "Missing" in v]
        risk_score += len(missing_headers) * 5
        if missing_headers:
            findings.append(f"Missing security headers: {', '.join(missing_headers[:3])}")
        
        # Check Shodan vulnerabilities
        shodan_info = self.results["scan_results"].get("shodan", {})
        if shodan_info and shodan_info.get("vulnerabilities"):
            vuln_count = len(shodan_info["vulnerabilities"])
            risk_score += min(vuln_count * 3, 20)
            findings.append(f"Found {vuln_count} potential vulnerabilities via Shodan")
        
        # Check open ports
        if shodan_info and shodan_info.get("open_ports"):
            sensitive_ports = [22, 23, 3389, 5900, 1433, 3306, 27017]
            open_sensitive = [p for p in shodan_info["open_ports"] if p in sensitive_ports]
            if open_sensitive:
                risk_score += len(open_sensitive) * 2
                findings.append(f"Sensitive ports open: {', '.join(map(str, open_sensitive))}")
        
        # Email exposure risk
        emails = self.results["scan_results"].get("emails_found", [])
        if len(emails) > 10:
            risk_score += 10
            findings.append(f"High number of email addresses exposed ({len(emails)})")
        
        # Subdomain exposure
        subdomains = self.results["scan_results"].get("subdomains", [])
        if len(subdomains) > 20:
            risk_score += 5
            findings.append(f"Large attack surface: {len(subdomains)} subdomains discovered")
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "CRITICAL"
            risk_color = Colors.RED
        elif risk_score >= 40:
            risk_level = "HIGH"
            risk_color = Colors.YELLOW
        elif risk_score >= 20:
            risk_level = "MEDIUM"
            risk_color = Colors.CYAN
        else:
            risk_level = "LOW"
            risk_color = Colors.GREEN
        
        risk_assessment = {
            "score": min(risk_score, 100),
            "level": risk_level,
            "color": risk_color,
            "findings": findings,
            "recommendations": self.generate_recommendations(findings)
        }
        
        self.results["scan_results"]["risk_assessment"] = risk_assessment
        return risk_assessment
    
    def generate_recommendations(self, findings):
        """Generate recommendations based on findings"""
        recommendations = []
        
        if "SPF" in str(findings):
            recommendations.append("Implement SPF record: v=spf1 include:_spf.google.com ~all")
        if "DMARC" in str(findings):
            recommendations.append("Implement DMARC policy: v=DMARC1; p=quarantine; rua=mailto:dmarc@domain.com")
        if "security headers" in str(findings).lower():
            recommendations.append("Configure security headers (HSTS, CSP, X-Frame-Options)")
        if "vulnerabilities" in str(findings).lower():
            recommendations.append("Patch identified vulnerabilities and conduct regular security scans")
        if "sensitive ports" in str(findings).lower():
            recommendations.append("Restrict access to sensitive ports using firewall rules")
        if "emails exposed" in str(findings).lower() or "email addresses" in str(findings).lower():
            recommendations.append("Review public-facing employee information and implement privacy controls")
        
        if not recommendations:
            recommendations.append("Continue regular security assessments and monitoring")
            recommendations.append("Implement security awareness training for employees")
        
        return recommendations[:8]
    
    def display_risk_assessment(self, risk_assessment):
        """Display risk assessment"""
        print(f"\n{Colors.BOLD}{Colors.UNDERLINE}RISK ASSESSMENT{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}")
        
        score = risk_assessment['score']
        level = risk_assessment['level']
        color = risk_assessment['color']
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * score / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n  Risk Score: {color}{score}/100{Colors.END} [{level} RISK]")
        print(f"  [{color}{bar}{Colors.END}]")
        
        print(f"\n{Colors.BOLD}Key Findings:{Colors.END}")
        for finding in risk_assessment['findings'][:10]:
            print(f"  {Colors.YELLOW}⚠{Colors.END} {finding}")
        
        print(f"\n{Colors.BOLD}Recommendations:{Colors.END}")
        for i, rec in enumerate(risk_assessment['recommendations'][:8], 1):
            print(f"  {i}. {Colors.GREEN}→{Colors.END} {rec}")
    
    def save_results(self):
        """Save results to JSON file"""
        filename = f"aserecon_{self.target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            self.log(f"Results saved to {filename}", "SUCCESS")
            return filename
        except Exception as e:
            self.log(f"Error saving results: {e}", "ERROR")
            return None
    
    def display_summary(self):
        """Display scan summary"""
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}SCAN SUMMARY - {self.target}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*70}{Colors.END}")
        
        stats = {
            "Subdomains": len(self.results["scan_results"].get("subdomains", [])),
            "Emails Found": len(self.results["scan_results"].get("emails_found", [])),
            "Open Ports": len(self.results["scan_results"].get("shodan", {}).get("open_ports", [])),
            "Vulnerabilities": len(self.results["scan_results"].get("shodan", {}).get("vulnerabilities", [])),
            "Technologies": len(self.results["scan_results"].get("technologies", [])),
            "Risk Score": f"{self.results['scan_results'].get('risk_assessment', {}).get('score', 0)}/100"
        }
        
        for key, value in stats.items():
            print(f"  {Colors.CYAN}{key}:{Colors.END} {value}")
        
        print(f"\n{Colors.BOLD}Scan completed at:{Colors.END} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run_full_scan(self):
        """Run complete reconnaissance scan"""
        self.print_section(f"Starting Full Reconnaissance on {self.target}")
        
        # Run all modules
        self.get_dns_info()
        self.get_whois_info()
        self.get_subdomains()
        self.get_email_patterns()
        self.get_technology_stack()
        self.search_shodan()
        self.get_archive_info()
        self.check_security_headers()
        self.extract_emails_from_web()
        self.generate_risk_assessment()
        
        # Display results
        self.display_dns_info(self.results["scan_results"].get("dns_info", {}))
        self.display_whois_info(self.results["scan_results"].get("whois_info", {}))
        self.display_subdomains(self.results["scan_results"].get("subdomains", []))
        self.display_email_info(self.results["scan_results"].get("email_patterns", {}))
        self.display_technologies(self.results["scan_results"].get("technologies", []))
        self.display_shodan_info(self.results["scan_results"].get("shodan", {}))
        self.display_archive_info(self.results["scan_results"].get("archive", {}))
        self.display_security_headers(self.results["scan_results"].get("security_headers", {}))
        self.display_emails(self.results["scan_results"].get("emails_found", []))
        self.display_risk_assessment(self.results["scan_results"].get("risk_assessment", {}))
        self.display_summary()
        
        # Save results
        self.save_results()

def show_help():
    """Display detailed help information"""
    help_text = f"""
{Colors.BOLD}{Colors.CYAN}ASERecon v3.0 - Advanced CLI Security Tool{Colors.END}
{Colors.BOLD}{'='*60}{Colors.END}

{Colors.GREEN}DESCRIPTION:{Colors.END}
    Advanced Social Engineering Reconnaissance and OSINT tool for authorized
    security testing. Performs comprehensive reconnaissance including DNS,
    WHOIS, subdomain discovery, email analysis, technology detection, and
    Shodan integration.

{Colors.GREEN}USAGE:{Colors.END}
    python asetool.py -t <target> [OPTIONS]

{Colors.GREEN}REQUIRED ARGUMENTS:{Colors.END}
    -t, --target TARGET        Target domain or IP address (e.g., example.com)

{Colors.GREEN}OPTIONS:{Colors.END}
    -s, --shodan API_KEY       Shodan API key for vulnerability and port scanning
    -v, --verbose              Enable verbose output for detailed information
    -o, --output FILE          Save results to custom JSON file
    --no-save                  Don't save results to file
    -h, --help                 Show this help message

{Colors.GREEN}SCAN MODULES:{Colors.END}
    Without specifying modules, the tool runs a FULL SCAN including:
    
    1. DNS Information       - A, MX, NS, TXT records and reverse DNS
    2. WHOIS Lookup         - Domain registration and ownership details
    3. Subdomain Discovery   - Certificate transparency + common subdomains
    4. Email Security        - SPF, DMARC, MX records analysis
    5. Technology Stack      - Web servers, frameworks, CMS detection
    6. Shodan Integration    - Open ports, vulnerabilities (requires API key)
    7. Wayback Machine       - Historical website archives
    8. Security Headers      - HSTS, CSP, X-Frame-Options analysis
    9. Email Extraction      - Email addresses from web pages
    10. Risk Assessment      - Automated risk scoring and recommendations

{Colors.GREEN}EXAMPLES:{Colors.END}
    
    # Basic scan (no API key)
    python asetool.py -t example.com
    
    # Full scan with Shodan
    python asetool.py -t example.com -s YOUR_SHODAN_API_KEY
    
    # Verbose scan with custom output
    python asetool.py -t example.com -s YOUR_API_KEY -v -o custom_results.json
    
    # Quick scan without saving
    python asetool.py -t example.com --no-save

{Colors.GREEN}SHODAN API KEY:{Colors.END}
    Get your free Shodan API key at: https://account.shodan.io/register
    Without Shodan, the tool still performs comprehensive OSINT using
    API-free sources (DNS, WHOIS, certificate transparency, etc.)

{Colors.GREEN}OUTPUT FILES:{Colors.END}
    Results are automatically saved to: aserecon_<target>_<timestamp>.json
    Use -o to specify custom filename or --no-save to disable

{Colors.GREEN}REQUIREMENTS:{Colors.END}
    Python packages: requests, beautifulsoup4, dnspython, python-whois, shodan
    
    Install with:
    pip install requests beautifulsoup4 dnspython python-whois shodan

{Colors.GREEN}LEGAL DISCLAIMER:{Colors.END}
    {Colors.RED}This tool is for EDUCATIONAL and AUTHORIZED SECURITY TESTING only.
    Using this tool against systems you don't own or have permission to
    test is ILLEGAL. Always obtain written authorization before scanning.{Colors.END}

{Colors.GREEN}EXIT CODES:{Colors.END}
    0 - Scan completed successfully
    1 - Error (invalid target, network issue, etc.)
    2 - Missing dependencies

{Colors.BOLD}For more information: https://github.com/aserecon{Colors.END}
    """
    print(help_text)

def main():
    # Show banner
    Banner.show()
    
    # Parse arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-t", "--target", help="Target domain or IP address")
    parser.add_argument("-s", "--shodan", help="Shodan API key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-o", "--output", help="Save results to custom file")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")
    
    args = parser.parse_args()
    
    # Show help
    if args.help or not args.target:
        show_help()
        sys.exit(0)
    
    # Legal confirmation
    print(f"{Colors.YELLOW}{Colors.BOLD}")
    print("⚠️  LEGAL NOTICE ⚠️")
    print("="*50)
    print(f"{Colors.END}")
    print("By using this tool, you confirm that you have:")
    print("  1. Written authorization to test the target")
    print("  2. Permission from the system owner")
    print("  3. Understood the legal implications")
    print()
    
    response = input(f"{Colors.BOLD}Do you have authorization to test {args.target}? (yes/no): {Colors.END}")
    if response.lower() != 'yes':
        print(f"{Colors.RED}Exiting. Please obtain proper authorization first.{Colors.END}")
        sys.exit(0)
    
    print(f"{Colors.GREEN}✓ Authorization confirmed. Proceeding with security assessment...{Colors.END}\n")
    
    # Initialize tool
    recon = ASEReconCLI(
        target=args.target,
        shodan_api_key=args.shodan,
        verbose=args.verbose
    )
    
    # Run scan
    try:
        recon.run_full_scan()
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Scan completed successfully!{Colors.END}\n")
        sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Scan interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
