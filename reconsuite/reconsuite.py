#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import all modules
from reconsuite.modules import (
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
    risk_assessment
)

class ReconSuite:
    """Main reconnaissance suite class"""
    
    def __init__(self, target: str, shodan_key: Optional[str] = None, nmap_args: str = "-sV -p- --max-retries 2"):
        self.target = target
        self.shodan_key = shodan_key
        self.nmap_args = nmap_args
        self.results = {}
        self.ctx = {
            "target": target,
            "shodan_key": shodan_key,
            "nmap_args": nmap_args
        }
    
    def dns_enumeration(self) -> Dict[str, Any]:
        """Perform DNS enumeration"""
        return dns.run(self.ctx)
    
    def whois_lookup(self) -> Dict[str, Any]:
        """Perform WHOIS lookup"""
        return whois_lookup.run(self.ctx)
    
    def subdomain_enumeration(self) -> Dict[str, Any]:
        """Discover subdomains"""
        return subdomains.run(self.ctx)
    
    def email_security(self) -> Dict[str, Any]:
        """Check email security (SPF, DMARC, MX)"""
        return email_security.run(self.ctx)
    
    def technology_detection(self) -> Dict[str, Any]:
        """Detect technologies in use"""
        return tech_detect.run(self.ctx)
    
    def shodan_search(self) -> Dict[str, Any]:
        """Search Shodan for target information"""
        if not self.shodan_key:
            return {"error": "No Shodan API key provided"}
        return shodan_integration.run(self.ctx)
    
    def wayback_machine(self) -> Dict[str, Any]:
        """Query Wayback Machine for historical data"""
        return wayback.run(self.ctx)
    
    def http_headers(self) -> Dict[str, Any]:
        """Analyze HTTP security headers"""
        return security_headers.run(self.ctx)
    
    def email_discovery(self) -> Dict[str, Any]:
        """Discover email addresses"""
        return email_extraction.run(self.ctx)
    
    def nmap_scan(self) -> Dict[str, Any]:
        """Run Nmap scan"""
        return nmap_scan.run(self.ctx)
    
    def risk_assessment(self) -> Dict[str, Any]:
        """Perform overall risk assessment"""
        return risk_assessment.run(self.ctx)
    
    def run_modules(self, modules: list) -> Dict[str, Any]:
        """Run a list of modules"""
        results = {}
        module_map = {
            "dns": self.dns_enumeration,
            "whois": self.whois_lookup,
            "subdomains": self.subdomain_enumeration,
            "emailsec": self.email_security,
            "tech": self.technology_detection,
            "shodan": self.shodan_search,
            "wayback": self.wayback_machine,
            "headers": self.http_headers,
            "emails": self.email_discovery,
            "nmap": self.nmap_scan,
            "risk": self.risk_assessment
        }
        
        for module in modules:
            if module in module_map:
                try:
                    results[module] = module_map[module]()
                except Exception as e:
                    results[module] = {"error": str(e)}
            else:
                results[module] = {"error": f"Unknown module: {module}"}
        
        return results
    
    def save_output(self, results: Dict[str, Any], output_path: str):
        """Save results to JSON file"""
        output_data = {
            "metadata": {
                "target": self.target,
                "timestamp": datetime.now().isoformat(),
                "tool": "ASETool"
            },
            "results": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)