#!/usr/bin/env python3
"""
ASETool - Complete OSINT & Network Toolkit
Educational Purpose Only - No API Keys Required
Version: 2.0
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

# Optional imports with fallbacks
try:
    import nmap
    from tqdm import tqdm
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    print("[!] Nmap module not installed. Install with: pip install python-nmap")

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    import ssl as ssl_lib
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

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
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            pass
        except Exception as e:
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
            for r in records[:10]:  # Show first 10
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

# ========== 5. HTTP HEADER GRABBING ==========
def grab_http_headers(domain: str) -> Dict:
    """Fetch HTTP/HTTPS headers for tech detection."""
    results = {}
    print("\n\033[1;33m[+] Grabbing HTTP Headers...\033[0m")
    
    for protocol in ["http", "https"]:
        url = f"{protocol}://{domain}"
        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            headers = dict(response.headers)
            server = headers.get('Server', 'Unknown')
            tech = {
                "server": server,
                "powered_by": headers.get('X-Powered-By', 'Not found'),
                "framework": headers.get('X-Framework', 'Not found'),
                "cms": headers.get('X-CMS', 'Not found')
            }
            results[protocol] = {"status": response.status_code, "headers": headers, "tech": tech}
        except:
            results[protocol] = {"error": "Connection failed"}
    
    print("\n\033[1;32m=== HTTP HEADER ANALYSIS ===\033[0m")
    for proto, data in results.items():
        print(f"\n  \033[1;36m{proto.upper()}:\033[0m")
        if 'error' in data:
            print(f"    └─ {data['error']}")
        else:
            print(f"    ├─ Status: {data['status']}")
            print(f"    ├─ Server: {data['tech']['server']}")
            print(f"    ├─ X-Powered-By: {data['tech']['powered_by']}")
            print(f"    └─ Framework: {data['tech']['framework']}")
    
    return results

# ========== 6. TRACEROUTE ==========
def traceroute(target: str, max_hops=30) -> List[Dict]:
    """Simple traceroute using ICMP or UDP."""
    results = []
    print(f"\n\033[1;33m[+] Tracing route to {target}...\033[0m")
    
    for ttl in range(1, max_hops+1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            sock.settimeout(2)
            sock.sendto(b"", (target, 33434))
            data, addr = sock.recvfrom(1024)
            results.append({"hop": ttl, "ip": addr[0], "rtt": "N/A"})
            if addr[0] == target:
                break
        except socket.timeout:
            results.append({"hop": ttl, "ip": "*", "rtt": "timeout"})
        except:
            break
        finally:
            sock.close()
    
    print("\n\033[1;32m=== TRACEROUTE RESULTS ===\033[0m")
    for hop in results:
        if hop['ip'] == '*':
            print(f"  {hop['hop']:2}  {'*':15}  {hop['rtt']}")
        else:
            print(f"  {hop['hop']:2}  {hop['ip']:15}  {hop['rtt']}")
    
    return results

# ========== 7. EMAIL/USERNAME OSINT ==========
def email_osint(email: str) -> Dict:
    """Basic email breach/association check."""
    username, domain = email.split('@')
    results = {
        "username": username,
        "domain": domain,
        "possible_social": [
            f"https://github.com/{username}",
            f"https://twitter.com/{username}",
            f"https://linkedin.com/in/{username}",
            f"https://reddit.com/user/{username}",
            f"https://instagram.com/{username}",
            f"https://facebook.com/{username}"
        ]
    }
    
    print("\n\033[1;32m=== EMAIL OSINT RESULTS ===\033[0m")
    print(f"  ├─ Username: {username}")
    print(f"  ├─ Domain: {domain}")
    print(f"  └─ Possible Social Media Profiles:")
    for url in results['possible_social']:
        print(f"      └─ {url}")
    print(f"\n  [!] Check haveibeenpwned.com for breach data (no API key needed)")
    
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
        return banner[:100]  # Limit banner length
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
    for port, info in sorted(results.items())[:20]:  # Show first 20
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
    print("║  5. HTTP Header Grabbing                                      ║")
    print("║  6. Traceroute                                                ║")
    print("║  7. Email OSINT                                               ║")
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
            email = input("[?] Enter email address to analyze: ").strip()
            if email and '@' in email:
                all_results['email_osint'] = email_osint(email)
            else:
                print("[!] Invalid email address.")
        
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
                all_results['dns'] = full_dns_lookup(domain)
                all_results['subdomains'] = subdomain_enum(domain)
                all_results['http_headers'] = grab_http_headers(domain)
            
            all_results['whois'] = whois_lookup(domain if domain else ip)
            all_results['ptr'] = reverse_dns(ip)
            all_results['traceroute'] = traceroute(ip)
            all_results['geo'] = ip_geolocation(ip)
            
            # Email OSINT is optional, ask user
            email_input = input("\n[?] Enter email for OSINT (or press Enter to skip): ").strip()
            if email_input and '@' in email_input:
                all_results['email_osint'] = email_osint(email_input)
            
            # Port scan
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
            
            if 'ports' in all_results:
                print(f"  \033[1;36mOpen Ports Found:\033[0m {len(all_results['ports'])}")
            
            if 'geo' in all_results and 'error' not in all_results['geo']:
                print(f"  \033[1;36mLocation:\033[0m {all_results['geo'].get('city')}, {all_results['geo'].get('country')}")
            
            print("\n\033[1;33m[!] EDUCATIONAL USE ONLY\033[0m")
            print("This tool is for authorized security training and OSINT research.")
            print("Always ensure you have permission before scanning or enumerating any target.")
            
            print("\n\033[1;32mConclusion:\033[0m ASETool provides complete OSINT capabilities without API keys,")
            print("including DNS enumeration, WHOIS, subdomain discovery, header grabbing,")
            print("traceroute, geolocation, and optional port scanning. Perfect for educational")
            print("purposes and understanding open-source intelligence techniques.\n")
            
            input("\n[?] Press Enter to continue...")
            clear_screen()
            print_banner()
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
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        sys.exit(1)