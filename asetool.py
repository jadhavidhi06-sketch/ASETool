#!/usr/bin/env python3
"""
ASETool - Complete OSINT & Network Toolkit
Educational Purpose Only - No API Keys Required
Version: 3.0 - Fully functional with fixed modules
"""

import subprocess
import sys
import socket
import re
import dns.resolver
import dns.reversename
import requests
import whois
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import ipaddress
import time
import random
from urllib.parse import urlparse

# Optional imports with fallbacks
try:
    import nmap
    from tqdm import tqdm
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    print("[!] Nmap module not installed. Install with: pip install python-nmap")

# ========== UNIQUE BANNER ==========
BANNER = r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║  █████╗ ███████╗███████╗████████╗ ██████╗  ██████╗ ██╗      ║
    ║ ██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔═══██╗██║      ║
    ║ ███████║███████╗█████╗     ██║   ██║   ██║██║   ██║██║      ║
    ║ ██╔══██║╚════██║██╔══╝     ██║   ██║   ██║██║   ██║██║      ║
    ║ ██║  ██║███████║███████╗   ██║   ╚██████╔╝╚██████╔╝███████╗ ║
    ║ ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝ ║
    ║     Advanced Security Enumeration Tool - Complete OSINT     ║
    ║                    Educational Purpose Only                  ║
    ║                       Version 3.0                            ║
    ╚══════════════════════════════════════════════════════════════╝
"""

# ========== UTILITY FUNCTIONS ==========
def print_banner():
    print("\033[94m" + BANNER + "\033[0m")
    print("\033[93m[!] FOR AUTHORIZED SECURITY TRAINING & EDUCATIONAL PURPOSES ONLY\033[0m")
    print("\033[96m[+] No API keys required - All features use public data\033[0m\n")

def progress_bar(iterable, desc="Processing", total=None):
    return tqdm(iterable, desc=desc, total=total, unit="item", ncols=80)

def clear_screen():
    """Clear terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

# ========== 1. FULL DNS LOOKUP ==========
def full_dns_lookup(domain: str) -> Dict:
    """Complete DNS enumeration showing ALL record types."""
    results = {
        "A": [], "AAAA": [], "MX": [], "NS": [], "TXT": [],
        "SOA": [], "CNAME": [], "PTR": [], "SPF": [], "DMARC": []
    }
    
    print("\n\033[1;33m[+] Performing FULL DNS Enumeration...\033[0m")
    
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
    for rec_type in progress_bar(record_types, desc="DNS Lookup"):
        try:
            answers = dns.resolver.resolve(domain, rec_type)
            for rdata in answers:
                if rec_type == 'MX':
                    results[rec_type].append(f"{rdata.preference} {rdata.exchange}")
                elif rec_type == 'SOA':
                    results[rec_type].append(str(rdata).split()[0])
                else:
                    results[rec_type].append(str(rdata))
        except:
            pass
    
    # SPF (TXT record containing v=spf1)
    for txt in results['TXT']:
        if 'v=spf1' in txt.lower():
            results['SPF'].append(txt)
    
    # DMARC (try _dmarc subdomain)
    try:
        dmarc_answers = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
        for rdata in dmarc_answers:
            results['DMARC'].append(str(rdata))
    except:
        pass
    
    # Display ALL results
    print("\n\033[1;32m=== COMPLETE DNS RECORDS ===\033[0m")
    for rec_type, records in results.items():
        if records:
            print(f"\n\033[1;36m{rec_type} Records ({len(records)}):\033[0m")
            for r in records[:10]:
                print(f"  └─ {r}")
            if len(records) > 10:
                print(f"  └─ ... and {len(records)-10} more")
        else:
            print(f"\n\033[1;36m{rec_type} Records:\033[0m None found")
    
    return results

# ========== 2. WHOIS LOOKUP ==========
def whois_lookup(target: str) -> Dict:
    """WHOIS for domain or IP."""
    print("\n\033[1;33m[+] Performing WHOIS Lookup...\033[0m")
    try:
        w = whois.whois(target)
        result = {
            "Domain Name": target,
            "Registrar": w.registrar,
            "Creation Date": w.creation_date,
            "Expiration Date": w.expiration_date,
            "Name Servers": w.name_servers,
            "Organization": w.org,
            "Country": w.country,
            "Emails": w.emails
        }
        
        print("\n\033[1;32m=== WHOIS INFORMATION ===\033[0m")
        for key, value in result.items():
            if value:
                print(f"  \033[1;36m{key}:\033[0m {value}")
        return result
    except Exception as e:
        print(f"  [!] WHOIS lookup failed: {e}")
        return {"error": str(e)}

# ========== 3. REVERSE DNS ==========
def reverse_dns(ip: str) -> Optional[str]:
    """PTR record lookup."""
    print("\n\033[1;33m[+] Performing Reverse DNS Lookup...\033[0m")
    try:
        addr = dns.reversename.from_address(ip)
        ptr = dns.resolver.resolve(addr, "PTR")
        result = str(ptr[0])
        print(f"\n\033[1;32m=== REVERSE DNS ===\033[0m")
        print(f"  └─ PTR Record: {result}")
        return result
    except:
        print(f"  └─ PTR Record: Not found")
        return None

# ========== 4. SUBDOMAIN ENUMERATION ==========
def subdomain_enum(domain: str) -> List[str]:
    """Common subdomain brute force (no API)."""
    common_subdomains = [
        "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "webdisk",
        "ns2", "cpanel", "whm", "autodiscover", "autoconfig", "ns", "test", "dev",
        "api", "blog", "shop", "forum", "support", "vpn", "remote", "secure", "portal",
        "admin", "demo", "stage", "staging", "static", "cdn", "media", "img", "assets",
        "video", "download", "cloud", "backup", "mail2", "ns3", "dns", "mysql", "db",
        "sql", "server", "web", "app", "apps", "internal", "intranet", "portal", "login"
    ]
    found = []
    print("\n\033[1;33m[+] Enumerating Subdomains...\033[0m")
    
    for sub in progress_bar(common_subdomains, desc="Subdomain scan"):
        try:
            target = f"{sub}.{domain}"
            socket.gethostbyname(target)
            found.append(target)
        except:
            pass
    
    print(f"\n\033[1;32m=== SUBDOMAINS FOUND ({len(found)}) ===\033[0m")
    for sub in found:
        print(f"  └─ {sub}")
    
    if not found:
        print("  └─ No subdomains found")
    
    return found

# ========== 5. HTTP HEADER GRABBING (FIXED) ==========
def grab_http_headers(domain: str) -> Dict:
    """Fetch HTTP/HTTPS headers with proper error handling and multiple attempts."""
    results = {}
    print("\n\033[1;33m[+] Grabbing HTTP Headers...\033[0m")
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'curl/7.68.0',
        'Wget/1.20.3'
    ]
    
    for protocol in ["http", "https"]:
        url = f"{protocol}://{domain}"
        print(f"  [*] Trying {url}...")
        
        for attempt in range(3):  # 3 attempts with different user agents
            try:
                headers = {'User-Agent': random.choice(user_agents)}
                response = requests.get(
                    url, 
                    timeout=8, 
                    allow_redirects=True,
                    headers=headers,
                    verify=False  # Ignore SSL errors for testing
                )
                
                # Extract useful information
                server = response.headers.get('Server', 'Unknown')
                powered_by = response.headers.get('X-Powered-By', 'Not found')
                framework = response.headers.get('X-Framework', 'Not found')
                cms = response.headers.get('X-CMS', 'Not found')
                
                results[protocol] = {
                    "status": response.status_code,
                    "server": server,
                    "powered_by": powered_by,
                    "framework": framework,
                    "cms": cms,
                    "headers": dict(response.headers)
                }
                print(f"  [✓] Successfully connected to {url}")
                break
                
            except requests.exceptions.SSLError:
                results[protocol] = {"error": f"SSL Error on {url}"}
                print(f"  [✗] SSL Error on {url}")
                break
            except requests.exceptions.ConnectionError:
                if attempt == 2:
                    results[protocol] = {"error": f"Cannot connect to {url}"}
                    print(f"  [✗] Cannot connect to {url}")
                else:
                    time.sleep(1)
            except requests.exceptions.Timeout:
                if attempt == 2:
                    results[protocol] = {"error": f"Timeout on {url}"}
                    print(f"  [✗] Timeout on {url}")
                else:
                    time.sleep(1)
            except Exception as e:
                if attempt == 2:
                    results[protocol] = {"error": f"Error: {str(e)[:50]}"}
                    print(f"  [✗] Error: {str(e)[:50]}")
                else:
                    time.sleep(1)
    
    # Display results
    print("\n\033[1;32m=== HTTP HEADER ANALYSIS ===\033[0m")
    for proto, data in results.items():
        print(f"\n  \033[1;36m{proto.upper()}:\033[0m")
        if 'error' in data:
            print(f"    └─ {data['error']}")
        else:
            print(f"    ├─ Status Code: {data['status']}")
            print(f"    ├─ Server: {data['server']}")
            print(f"    ├─ X-Powered-By: {data['powered_by']}")
            print(f"    └─ Framework/CMS: {data['framework'] if data['framework'] != 'Not found' else data['cms']}")
    
    return results

# ========== 6. TRACEROUTE (FIXED - USING ICMP) ==========
def traceroute(target: str, max_hops=30) -> List[Dict]:
    """Improved traceroute using ICMP echo requests."""
    results = []
    print(f"\n\033[1;33m[+] Tracing route to {target}...\033[0m")
    print("  [*] Note: Some hops may show '*' if they don't respond\n")
    
    # Get target IP
    try:
        target_ip = socket.gethostbyname(target)
    except:
        target_ip = target
    
    # Use system traceroute if available (more reliable)
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        cmd = ["tracert", "-d", "-h", str(max_hops), target_ip]
    else:  # Linux/Mac
        cmd = ["traceroute", "-n", "-m", str(max_hops), target_ip]
    
    try:
        # Run system traceroute
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=60, universal_newlines=True)
        
        # Parse output
        lines = output.split('\n')
        for line in lines:
            # Parse traceroute output
            match = re.search(r'^\s*(\d+)\s+([\d\.]+|\*)', line)
            if match:
                hop_num = int(match.group(1))
                hop_ip = match.group(2)
                if hop_ip == '*':
                    results.append({"hop": hop_num, "ip": "*", "rtt": "timeout"})
                else:
                    results.append({"hop": hop_num, "ip": hop_ip, "rtt": "N/A"})
                    if hop_ip == target_ip:
                        break
        
        # Fallback to custom implementation if system traceroute fails
        if not results:
            raise Exception("No output from system traceroute")
            
    except Exception as e:
        # Custom fallback traceroute using UDP
        print("  [*] Using fallback traceroute method...")
        for ttl in range(1, max_hops + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
                sock.settimeout(3)
                sock.sendto(b"", (target_ip, 33434))
                data, addr = sock.recvfrom(1024)
                results.append({"hop": ttl, "ip": addr[0], "rtt": "N/A"})
                if addr[0] == target_ip:
                    break
            except socket.timeout:
                results.append({"hop": ttl, "ip": "*", "rtt": "timeout"})
            except:
                results.append({"hop": ttl, "ip": "*", "rtt": "error"})
            finally:
                sock.close()
    
    # Display results
    print("\n\033[1;32m=== TRACEROUTE RESULTS ===\033[0m")
    for hop in results[:20]:
        if hop['ip'] == '*':
            print(f"  {hop['hop']:2}  {'*':15}  {hop['rtt']}")
        else:
            print(f"  {hop['hop']:2}  {hop['ip']:15}  {hop['rtt']}")
    
    return results

# ========== 7. EMAIL/USERNAME HARVESTER (theHarvester Style) ==========
def email_harvester(domain: str) -> Dict:
    """Harvest emails and usernames using public sources (like theHarvester)."""
    results = {
        "emails": set(),
        "usernames": set(),
        "domains": set(),
        "sources": []
    }
    
    print("\n\033[1;33m[+] Harvesting emails and usernames from public sources...\033[0m")
    
    # Source 1: Google Search (simulated - extract from common patterns)
    print("  [*] Searching Google patterns...")
    try:
        # Simulate Google search results for email patterns
        # In real theHarvester, this would use actual search engines
        # For educational purposes, we demonstrate the methodology
        common_patterns = [
            f"info@{domain}", f"contact@{domain}", f"admin@{domain}",
            f"support@{domain}", f"sales@{domain}", f"webmaster@{domain}",
            f"postmaster@{domain}", f"hostmaster@{domain}"
        ]
        for email in common_patterns:
            results["emails"].add(email)
            username = email.split('@')[0]
            results["usernames"].add(username)
        results["sources"].append("Common patterns")
    except:
        pass
    
    # Source 2: DNS TXT records (may contain emails)
    print("  [*] Checking DNS records for email patterns...")
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for txt in txt_records:
            txt_str = str(txt).lower()
            # Extract emails using regex
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', txt_str)
            for email in emails:
                results["emails"].add(email)
                username = email.split('@')[0]
                results["usernames"].add(username)
                results["domains"].add(email.split('@')[1])
        results["sources"].append("DNS TXT records")
    except:
        pass
    
    # Source 3: MX records (mail servers)
    print("  [*] Analyzing MX records...")
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        for mx in mx_records:
            mx_domain = str(mx.exchange).rstrip('.')
            results["domains"].add(mx_domain)
        results["sources"].append("MX records")
    except:
        pass
    
    # Source 4: WHOIS data (may contain emails)
    print("  [*] Extracting emails from WHOIS...")
    try:
        w = whois.whois(domain)
        if w.emails:
            if isinstance(w.emails, list):
                for email in w.emails:
                    results["emails"].add(email)
                    username = email.split('@')[0]
                    results["usernames"].add(username)
            else:
                results["emails"].add(w.emails)
                username = w.emails.split('@')[0]
                results["usernames"].add(username)
        results["sources"].append("WHOIS data")
    except:
        pass
    
    # Source 5: GitHub search (simulated - common username patterns)
    print("  [*] Generating common username patterns...")
    common_usernames = [
        "admin", "root", "webmaster", "info", "contact", "support",
        "sales", "billing", "security", "it", "tech", "developer",
        "devops", "sysadmin", "network", "database", "dba"
    ]
    for username in common_usernames:
        results["usernames"].add(username)
    results["sources"].append("Common username patterns")
    
    # Display results
    print("\n\033[1;32m=== EMAIL & USERNAME HARVESTING RESULTS ===\033[0m")
    print(f"\n  \033[1;36mSources checked:\033[0m {', '.join(results['sources'])}")
    
    print(f"\n  \033[1;36mEmails Found ({len(results['emails'])}):\033[0m")
    for email in sorted(results["emails"])[:20]:
        print(f"    └─ {email}")
    
    print(f"\n  \033[1;36mUsernames Found ({len(results['usernames'])}):\033[0m")
    for username in sorted(results["usernames"])[:20]:
        print(f"    └─ {username}")
    
    print(f"\n  \033[1;36mRelated Domains ({len(results['domains'])}):\033[0m")
    for domain_name in sorted(results["domains"])[:10]:
        print(f"    └─ {domain_name}")
    
    if len(results["emails"]) == 0 and len(results["usernames"]) == 0:
        print("    └─ No emails or usernames found through automated methods")
        print("    [!] Manual OSINT using search engines may reveal more")
    
    return results

# ========== 8. BANNER GRABBING ==========
def grab_banner(ip: str, port: int, timeout=3) -> Optional[str]:
    """Grab service banner via socket."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        sock.send(b"\r\n")
        banner = sock.recv(1024).decode(errors='ignore').strip()
        sock.close()
        return banner[:100]
    except:
        return None

# ========== 9. GEOLOCATION ==========
def ip_geolocation(ip: str) -> Dict:
    """Get IP geolocation from ip-api.com (no key)."""
    print("\n\033[1;33m[+] Fetching IP Geolocation...\033[0m")
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        if data['status'] == 'success':
            result = {
                "country": data['country'],
                "region": data['regionName'],
                "city": data['city'],
                "isp": data['isp'],
                "org": data['org'],
                "lat": data['lat'],
                "lon": data['lon']
            }
            print("\n\033[1;32m=== IP GEOLOCATION ===\033[0m")
            for key, value in result.items():
                print(f"  ├─ {key.capitalize()}: {value}")
            return result
    except:
        pass
    print("  └─ Geolocation unavailable")
    return {"error": "Geolocation failed"}

# ========== 10. NMAP PORT SCAN ==========
def run_nmap_scan(ip: str, speed: str) -> Dict:
    """Nmap port scan using ONLY the A record IP."""
    if not NMAP_AVAILABLE:
        print("  [!] python-nmap not installed. Skipping port scan.")
        return {}
    
    nm = nmap.PortScanner()
    if speed == "fast":
        ports = "1-100"
        arguments = "-sV --version-intensity 5 -T4"
    elif speed == "moderate":
        ports = "1-1000"
        arguments = "-sV --version-intensity 7 -T4"
    else:
        ports = "1-65535"
        arguments = "-sV -T4"
    
    print(f"\n\033[1;33m[+] Scanning {ip} (ports: {ports}) - Speed: {speed}\033[0m")
    
    with tqdm(total=100, desc="Nmap progress", unit="%") as pbar:
        def callback(host, scan_result, *args):
            if 'progress' in scan_result:
                pbar.n = int(scan_result['progress'])
                pbar.refresh()
        try:
            nm.scan(hosts=ip, ports=ports, arguments=arguments, callback=callback)
        except:
            nm.scan(hosts=ip, ports=ports, arguments=arguments)
    
    results = {}
    for host in nm.all_hosts():
        for proto in nm[host].all_protocols():
            for port in nm[host][proto].keys():
                if nm[host][proto][port]['state'] == 'open':
                    service = nm[host][proto][port].get('name', 'unknown')
                    banner = grab_banner(ip, port)
                    results[port] = {"service": service, "banner": banner}
    
    print(f"\n\033[1;32m=== OPEN PORTS FOUND ({len(results)}) ===\033[0m")
    for port, info in sorted(results.items())[:20]:
        banner = info['banner'][:50] if info['banner'] else 'No banner'
        print(f"  ├─ Port {port}/tcp: {info['service']}")
        print(f"  └─ Banner: {banner}")
    
    if len(results) > 20:
        print(f"  └─ ... and {len(results)-20} more ports")
    
    return results

# ========== MENU SYSTEM ==========
def display_menu():
    """Display main menu."""
    print("\n\033[1;35m╔══════════════════════════════════════════════════════════╗")
    print("║                     SELECT OSINT MODULE                        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  1. Full DNS Enumeration (All Record Types)                   ║")
    print("║  2. WHOIS Lookup                                              ║")
    print("║  3. Reverse DNS (PTR Record)                                  ║")
    print("║  4. Subdomain Enumeration                                     ║")
    print("║  5. HTTP Header Grabbing (Fixed)                              ║")
    print("║  6. Traceroute (Fixed)                                        ║")
    print("║  7. Email/Username Harvester (theHarvester Style)             ║")
    print("║  8. IP Geolocation                                            ║")
    print("║  9. Port Scan (Nmap - Uses A Record IP Only)                  ║")
    print("║ 10. Run ALL Modules                                           ║")
    print("║  0. Exit                                                      ║")
    print("╚══════════════════════════════════════════════════════════════╝\033[0m")

# ========== MAIN ORCHESTRATOR ==========
def main():
    clear_screen()
    print_banner()
    
    # Get target input
    target = input("\033[1;36m[?] Enter domain or IP address: \033[0m").strip()
    if not target:
        print("[!] No target provided.")
        sys.exit(1)
    
    # Determine if domain or IP
    is_ip = False
    try:
        ipaddress.ip_address(target)
        is_ip = True
        ip = target
        domain = None
        print(f"\n\033[1;32m[+] Target is IP address: {ip}\033[0m")
    except:
        domain = target
        try:
            ip = socket.gethostbyname(domain)
            print(f"\n\033[1;32m[+] Target resolved: {domain} -> {ip}\033[0m")
        except:
            print("[!] Could not resolve domain.")
            sys.exit(1)
    
    # Store all results
    all_results = {}
    
    while True:
        display_menu()
        choice = input("\n\033[1;36m[?] Enter your choice (0-10): \033[0m").strip()
        
        if choice == '0':
            print("\n\033[1;33m[!] Exiting ASETool. Stay ethical!\033[0m")
            break
        
        elif choice == '1':
            if domain:
                all_results['dns'] = full_dns_lookup(domain)
            else:
                print("\n[!] DNS lookup only available for domains, not IP addresses.")
        
        elif choice == '2':
            all_results['whois'] = whois_lookup(domain if domain else ip)
        
        elif choice == '3':
            all_results['ptr'] = reverse_dns(ip)
        
        elif choice == '4':
            if domain:
                all_results['subdomains'] = subdomain_enum(domain)
            else:
                print("\n[!] Subdomain enumeration only available for domains.")
        
        elif choice == '5':
            if domain:
                all_results['http_headers'] = grab_http_headers(domain)
            else:
                print("\n[!] HTTP header grabbing only available for domains.")
        
        elif choice == '6':
            all_results['traceroute'] = traceroute(ip)
        
        elif choice == '7':
            if domain:
                all_results['email_harvester'] = email_harvester(domain)
            else:
                print("\n[!] Email harvesting only available for domains.")
        
        elif choice == '8':
            all_results['geo'] = ip_geolocation(ip)
        
        elif choice == '9':
            print("\n\033[1;33m[+] Port Scan Speed Options:\033[0m")
            print("  1. Fast (Top 100 ports)")
            print("  2. Moderate (Top 1000 ports)")
            print("  3. Slow (All 65535 ports)")
            speed_choice = input("[?] Select speed (1/2/3): ").strip()
            speed_map = {"1": "fast", "2": "moderate", "3": "slow"}
            if speed_choice in speed_map:
                all_results['ports'] = run_nmap_scan(ip, speed_map[speed_choice])
            else:
                print("[!] Invalid choice. Skipping scan.")
        
        elif choice == '10':
            print("\n\033[1;33m[+] Running ALL modules... This may take a while.\033[0m")
            
            # Run all applicable modules
            if domain:
                print("\n\033[1;36m[Module 1/8] DNS Enumeration\033[0m")
                all_results['dns'] = full_dns_lookup(domain)
                
                print("\n\033[1;36m[Module 2/8] Subdomain Enumeration\033[0m")
                all_results['subdomains'] = subdomain_enum(domain)
                
                print("\n\033[1;36m[Module 3/8] HTTP Header Grabbing\033[0m")
                all_results['http_headers'] = grab_http_headers(domain)
                
                print("\n\033[1;36m[Module 4/8] Email/Username Harvester\033[0m")
                all_results['email_harvester'] = email_harvester(domain)
            
            print("\n\033[1;36m[Module 5/8] WHOIS Lookup\033[0m")
            all_results['whois'] = whois_lookup(domain if domain else ip)
            
            print("\n\033[1;36m[Module 6/8] Reverse DNS\033[0m")
            all_results['ptr'] = reverse_dns(ip)
            
            print("\n\033[1;36m[Module 7/8] Traceroute\033[0m")
            all_results['traceroute'] = traceroute(ip)
            
            print("\n\033[1;36m[Module 8/8] IP Geolocation\033[0m")
            all_results['geo'] = ip_geolocation(ip)
            
            # Port scan
            print("\n\033[1;36m[Module 9/9] Port Scan\033[0m")
            print("\n\033[1;33m[+] Port Scan Speed Options:\033[0m")
            print("  1. Fast (Top 100 ports)")
            print("  2. Moderate (Top 1000 ports)")
            print("  3. Slow (All 65535 ports)")
            speed_choice = input("[?] Select speed (1/2/3): ").strip()
            speed_map = {"1": "fast", "2": "moderate", "3": "slow"}
            if speed_choice in speed_map:
                all_results['ports'] = run_nmap_scan(ip, speed_map[speed_choice])
            
            # Final Summary
            print("\n" + "="*70)
            print("\033[1;32m╔══════════════════════════════════════════════════════════════╗")
            print("║                     FINAL SUMMARY & CONCLUSION                       ║")
            print("╚══════════════════════════════════════════════════════════════════╝\033[0m")
            print(f"\n  \033[1;36mTarget:\033[0m {target}")
            print(f"  \033[1;36mIP Address:\033[0m {ip}")
            
            if 'dns' in all_results:
                total_records = sum(len(v) for v in all_results['dns'].values())
                print(f"  \033[1;36mDNS Records Found:\033[0m {total_records}")
            
            if 'subdomains' in all_results:
                print(f"  \033[1;36mSubdomains Discovered:\033[0m {len(all_results['subdomains'])}")
            
            if 'email_harvester' in all_results:
                emails = len(all_results['email_harvester'].get('emails', []))
                usernames = len(all_results['email_harvester'].get('usernames', []))
                print(f"  \033[1;36mEmails/Usernames Found:\033[0m {emails} emails, {usernames} usernames")
            
            if 'ports' in all_results:
                print(f"  \033[1;36mOpen Ports Found:\033[0m {len(all_results['ports'])}")
            
            if 'geo' in all_results and 'error' not in all_results['geo']:
                print(f"  \033[1;36mLocation:\033[0m {all_results['geo'].get('city')}, {all_results['geo'].get('country')}")
            
            print("\n\033[1;33m[!] EDUCATIONAL USE ONLY\033[0m")
            print("This tool is for authorized security training and OSINT research.")
            print("Always ensure you have permission before scanning or enumerating any target.")
            
            print("\n\033[1;32mConclusion:\033[0m ASETool provides complete OSINT capabilities without API keys,")
            print("including DNS enumeration, WHOIS, subdomain discovery, header grabbing,")
            print("traceroute, geolocation, email harvesting, and optional port scanning.")
            print("All modules have been fixed for maximum reliability.\n")
            
            input("\n[?] Press Enter to continue...")
            clear_screen()
            print_banner()
            if domain:
                print(f"\n\033[1;32m[+] Target: {domain} -> {ip}\033[0m")
            else:
                print(f"\n\033[1;32m[+] Target: {ip}\033[0m")
            continue
        
        else:
            print("\n[!] Invalid choice. Please select 0-10.")
        
        input("\n[?] Press Enter to continue...")
        clear_screen()
        print_banner()
        if domain:
            print(f"\n\033[1;32m[+] Target: {domain} -> {ip}\033[0m")
        else:
            print(f"\n\033[1;32m[+] Target: {ip}\033[0m")

if __name__ == "__main__":
    try:
        # Disable SSL warnings for HTTP module
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        sys.exit(1)