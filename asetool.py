#!/usr/bin/env python3
import os
import sys
import shutil
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from reconsuite.reconsuite import ReconSuite

# Try to import progress bar libraries
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("[!] Install tqdm for better progress bars: pip install tqdm")

# Try to import curses menu helper
try:
    from reconsuite.curses_menu import run_curses_menu
    CURSES_AVAILABLE = True
except Exception:
    CURSES_AVAILABLE = False

# Color codes for rich CLI output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    # RGB colors for cinematic feel
    GOLD = '\033[38;2;255;215;0m'
    SILVER = '\033[38;2;192;192;192m'
    DARK_RED = '\033[38;2;139;0;0m'
    BRIGHT_RED = '\033[38;2;255;0;85m'
    BRIGHT_CYAN = '\033[38;2;0;255;255m'

def print_color(text: str, color: str = Colors.RESET, end: str = "\n"):
    """Print colored text"""
    print(f"{color}{text}{Colors.RESET}", end=end)

def make_banner():
    cols = 80
    try:
        cols = os.get_terminal_size().columns
        cols = max(80, min(cols, 140))
    except Exception:
        cols = 80
    
    title_lines = [
        r"    █████╗ ███████╗ ███████╗████████╗ ██████╗  ██████╗ ██╗     ",
        r"   ██╔══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔═══██╗██╔═══██╗██║     ",
        r"   ███████║███████╗ █████╗     ██║   ██║   ██║██║   ██║██║     ",
        r"   ██╔══██║╚════██║ ██╔══╝     ██║   ██║   ██║██║   ██║██║     ",
        r"   ██║  ██║║███████║███████╗   ██║   ╚██████╔╝╚██████╔╝███████╗",
        r"   ╚═╝  ╚═╝╝╚══════╝╚══════╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝",
        r"",
    ]
    
    subtitle = "⚡ ADVANCED SECURITY EVALUATION TOOLKIT ⚡"
    tagline = "Precision Reconnaissance • Ethical Intelligence • Professional Grade"
    version = "v2.1.0"
    
    art_width = max(len(line) for line in title_lines)
    start_col = (cols - art_width) // 2 if art_width < cols else 0
    
    gradient_lines = []
    for i, line in enumerate(title_lines):
        if i < 6:
            color = Colors.BRIGHT_CYAN if i % 2 == 0 else Colors.GOLD
        else:
            color = Colors.BRIGHT_RED if i % 2 == 0 else Colors.SILVER
        
        spaced_line = ' ' * start_col + line
        gradient_lines.append(f"{color}{spaced_line}{Colors.RESET}")
    
    banner = "\n".join([
        Colors.DARK_RED + "═" * cols + Colors.RESET,
        Colors.GOLD + "✨" + " " * (cols - 2) + "✨" + Colors.RESET,
        "",
        *gradient_lines,
        "",
        Colors.BOLD + Colors.GOLD + subtitle.center(cols) + Colors.RESET,
        Colors.SILVER + tagline.center(cols) + Colors.RESET,
        "",
        Colors.DIM + version.center(cols) + Colors.RESET,
        Colors.DARK_RED + "─" * cols + Colors.RESET,
        Colors.GOLD + "✨" + " " * (cols - 2) + "✨" + Colors.RESET,
        Colors.DARK_RED + "═" * cols + Colors.RESET,
    ])
    
    return banner

BANNER = make_banner()
DEFAULT_MODULES = ["dns", "whois", "subdomains", "emailsec", "tech", "nmap", "emails", "headers", "wayback", "shodan", "risk"]

def ensure_results_dir(base="results"):
    os.makedirs(base, exist_ok=True)
    return base

def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in name)

def next_target_dir(base, target):
    safe = _safe_name(target)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{safe}_{timestamp}"
    out = os.path.join(base, name)
    os.makedirs(out, exist_ok=True)
    return out

def choose_modules():
    if CURSES_AVAILABLE:
        chosen = run_curses_menu(DEFAULT_MODULES)
        if chosen:
            return chosen
    
    print_color("\n📋 Available Modules:", Colors.BOLD + Colors.CYAN)
    print_color("  " + "─" * 50, Colors.DIM)
    for i, m in enumerate(DEFAULT_MODULES, 1):
        print(f"  {i:2}. {m:12}", end="  ")
        if i % 3 == 0:
            print()
    if len(DEFAULT_MODULES) % 3 != 0:
        print()
    print_color("  " + "─" * 50, Colors.DIM)
    print_color("  0. ALL modules (full reconnaissance)", Colors.GOLD)
    
    sel = input(f"\n{Colors.BRIGHT_CYAN}🎯 Enter module numbers (comma-separated) or 0 for all: {Colors.RESET}").strip()
    if sel in ("0", "all", "0."):
        return DEFAULT_MODULES
    
    nums = [s.strip() for s in sel.split(",") if s.strip().isdigit()]
    picked = []
    for n in nums:
        idx = int(n) - 1
        if 0 <= idx < len(DEFAULT_MODULES):
            picked.append(DEFAULT_MODULES[idx])
    
    return picked or DEFAULT_MODULES

def prompt_yes_no(prompt, default=False):
    yn = "Y/n" if default else "y/N"
    ans = input(f"{prompt} [{yn}]: ").strip().lower()
    if ans == "" and default:
        return True
    return ans in ("y", "yes")

class ProgressTracker:
    def __init__(self, total_modules: int):
        self.total = total_modules
        self.completed = 0
        self.current_module = ""
        self.start_time = time.time()
        
    def update(self, module_name: str, status: str = "running"):
        self.current_module = module_name
        if status == "completed":
            self.completed += 1
        self.display()
    
    def display(self):
        cols = 80
        try:
            cols = os.get_terminal_size().columns
        except:
            pass
        
        percent = (self.completed / self.total) * 100 if self.total > 0 else 0
        bar_length = min(50, cols - 40)
        filled = int(bar_length * self.completed // self.total) if self.total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        elapsed = time.time() - self.start_time
        eta = (elapsed / self.completed * (self.total - self.completed)) if self.completed > 0 else 0
        
        sys.stdout.write(f"\r{Colors.BRIGHT_CYAN}Progress: [{bar}] {percent:5.1f}%{Colors.RESET} ")
        sys.stdout.write(f"{Colors.SILVER}[{self.completed}/{self.total}] | {Colors.GOLD}{self.current_module:<20}{Colors.RESET}")
        sys.stdout.write(f" {Colors.DIM}| Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s{Colors.RESET}")
        sys.stdout.flush()
    
    def finish(self):
        print()  # New line after progress bar
        elapsed = time.time() - self.start_time
        print_color(f"\n✅ All modules completed in {elapsed:.2f} seconds!", Colors.GREEN + Colors.BOLD)

def run_module_with_progress(suite: ReconSuite, module: str, progress: ProgressTracker) -> Dict[str, Any]:
    """Run a single module and return its results"""
    progress.update(module, "running")
    
    try:
        # Call the appropriate module method
        if module == "dns":
            result = suite.dns_enumeration()
        elif module == "whois":
            result = suite.whois_lookup()
        elif module == "subdomains":
            result = suite.subdomain_enumeration()
        elif module == "emailsec":
            result = suite.email_security()
        elif module == "tech":
            result = suite.technology_detection()
        elif module == "nmap":
            result = suite.nmap_scan()
        elif module == "emails":
            result = suite.email_discovery()
        elif module == "headers":
            result = suite.http_headers()
        elif module == "wayback":
            result = suite.wayback_machine()
        elif module == "shodan":
            result = suite.shodan_search()
        elif module == "risk":
            result = suite.risk_assessment()
        else:
            result = {"error": f"Unknown module: {module}"}
        
        progress.update(module, "completed")
        return {module: result}
        
    except Exception as e:
        progress.update(module, "completed")
        return {module: {"error": str(e)}}

def format_cli_output(results: Dict[str, Any], target: str):
    """Format and display results in a readable CLI format"""
    print_color("\n" + "="*80, Colors.BOLD + Colors.GOLD)
    print_color(f"📊 RECONNAISSANCE RESULTS FOR: {target}", Colors.BOLD + Colors.BRIGHT_CYAN)
    print_color("="*80 + "\n", Colors.BOLD + Colors.GOLD)
    
    for module, data in results.items():
        if not data:
            continue
            
        print_color(f"\n▶ {module.upper()} MODULE", Colors.BOLD + Colors.GREEN)
        print_color("  " + "─"*76, Colors.DIM)
        
        if isinstance(data, dict):
            # Handle errors
            if "error" in data:
                print_color(f"  ❌ Error: {data['error']}", Colors.RED)
                continue
            
            # Format specific module outputs
            if module == "dns":
                if "a_records" in data:
                    print_color(f"  📍 A Records: {', '.join(data['a_records'][:5])}", Colors.CYAN)
                if "mx_records" in data:
                    print_color(f"  ✉️  MX Records: {', '.join(data['mx_records'][:3])}", Colors.CYAN)
                    
            elif module == "subdomains":
                subdomains = data.get("subdomains", [])
                print_color(f"  🌐 Discovered Subdomains ({len(subdomains)}):", Colors.CYAN)
                for sub in subdomains[:10]:
                    print_color(f"    • {sub}", Colors.SILVER)
                if len(subdomains) > 10:
                    print_color(f"    ... and {len(subdomains)-10} more", Colors.DIM)
                    
            elif module == "emails":
                emails = data.get("emails", [])
                print_color(f"  📧 Found Emails ({len(emails)}):", Colors.CYAN)
                for email in emails[:10]:
                    print_color(f"    • {email}", Colors.SILVER)
                    
            elif module == "tech":
                tech_stack = data.get("technologies", [])
                print_color(f"  💻 Technology Stack ({len(tech_stack)}):", Colors.CYAN)
                for tech in tech_stack[:10]:
                    print_color(f"    • {tech}", Colors.SILVER)
                    
            elif module == "headers":
                headers = data.get("headers", {})
                print_color(f"  🔒 Security Headers:", Colors.CYAN)
                important = ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options"]
                for h in important:
                    if h in headers:
                        print_color(f"    ✓ {h}: {headers[h][:50]}", Colors.GREEN)
                    else:
                        print_color(f"    ✗ {h}: Not Set", Colors.RED)
                        
            elif module == "risk":
                risk_score = data.get("risk_score", "N/A")
                findings = data.get("findings", [])
                print_color(f"  ⚠️  Risk Score: {risk_score}/100", Colors.YELLOW)
                print_color(f"  📋 Key Findings ({len(findings)}):", Colors.CYAN)
                for finding in findings[:5]:
                    print_color(f"    • {finding}", Colors.SILVER)
                    
            else:
                # Generic output for other modules
                for key, value in list(data.items())[:5]:
                    if isinstance(value, list):
                        print_color(f"  📌 {key}: {len(value)} items", Colors.CYAN)
                        for item in value[:3]:
                            print_color(f"      • {item}", Colors.SILVER)
                    elif isinstance(value, dict):
                        print_color(f"  📌 {key}: {len(value)} entries", Colors.CYAN)
                    else:
                        print_color(f"  📌 {key}: {str(value)[:100]}", Colors.CYAN)
        else:
            print_color(f"  {str(data)[:200]}", Colors.SILVER)
        
        print()  # Add spacing

def generate_summary(results: Dict[str, Any], target: str, elapsed_time: float) -> Dict[str, Any]:
    """Generate a comprehensive summary of findings"""
    summary = {
        "target": target,
        "scan_time": datetime.now().isoformat(),
        "duration_seconds": elapsed_time,
        "modules_executed": len(results),
        "statistics": {},
        "key_findings": [],
        "risk_level": "Unknown"
    }
    
    stats = {}
    total_emails = 0
    total_subdomains = 0
    total_technologies = 0
    
    for module, data in results.items():
        if isinstance(data, dict):
            if module == "emails" and "emails" in data:
                total_emails = len(data["emails"])
                stats["emails_found"] = total_emails
                if total_emails > 0:
                    summary["key_findings"].append(f"Found {total_emails} email addresses")
                    
            elif module == "subdomains" and "subdomains" in data:
                total_subdomains = len(data["subdomains"])
                stats["subdomains_found"] = total_subdomains
                if total_subdomains > 0:
                    summary["key_findings"].append(f"Discovered {total_subdomains} subdomains")
                    
            elif module == "tech" and "technologies" in data:
                total_technologies = len(data["technologies"])
                stats["technologies_detected"] = total_technologies
                if total_technologies > 0:
                    summary["key_findings"].append(f"Detected {total_technologies} technologies")
                    
            elif module == "risk" and "risk_score" in data:
                risk_score = data["risk_score"]
                stats["risk_score"] = risk_score
                if risk_score > 70:
                    summary["risk_level"] = "HIGH"
                elif risk_score > 40:
                    summary["risk_level"] = "MEDIUM"
                else:
                    summary["risk_level"] = "LOW"
                summary["key_findings"].append(f"Risk assessment score: {risk_score}/100")
                
            elif module == "headers":
                headers = data.get("headers", {})
                missing_security = []
                for h in ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options"]:
                    if h not in headers:
                        missing_security.append(h)
                if missing_security:
                    summary["key_findings"].append(f"Missing security headers: {', '.join(missing_security)}")
    
    summary["statistics"] = stats
    return summary

def display_summary(summary: Dict[str, Any]):
    """Display the final summary in a nice format"""
    print_color("\n" + "🎯"*40, Colors.BOLD + Colors.GOLD)
    print_color("📊 EXECUTIVE SUMMARY", Colors.BOLD + Colors.BRIGHT_CYAN)
    print_color("🎯"*40 + "\n", Colors.BOLD + Colors.GOLD)
    
    print_color(f"Target: {summary['target']}", Colors.CYAN)
    print_color(f"Scan Duration: {summary['duration_seconds']:.2f} seconds", Colors.CYAN)
    print_color(f"Modules Executed: {summary['modules_executed']}", Colors.CYAN)
    print_color(f"Risk Level: {summary['risk_level']}", 
                Colors.RED if summary['risk_level'] == "HIGH" else Colors.YELLOW if summary['risk_level'] == "MEDIUM" else Colors.GREEN)
    
    if summary['statistics']:
        print_color("\n📈 Statistics:", Colors.BOLD + Colors.GREEN)
        for key, value in summary['statistics'].items():
            print_color(f"  • {key.replace('_', ' ').title()}: {value}", Colors.SILVER)
    
    if summary['key_findings']:
        print_color("\n🔑 Key Findings:", Colors.BOLD + Colors.YELLOW)
        for finding in summary['key_findings']:
            print_color(f"  • {finding}", Colors.SILVER)
    
    print_color("\n" + "="*80, Colors.DIM)

def save_detailed_report(results: Dict[str, Any], target_dir: str, target: str, summary: Dict[str, Any]):
    """Save comprehensive detailed reports in multiple formats"""
    
    # Save full JSON report
    json_path = os.path.join(target_dir, "complete_report.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "tool": "ASETool v2.1.0"
            },
            "summary": summary,
            "detailed_results": results
        }, f, indent=2, default=str)
    
    # Save readable text report
    txt_path = os.path.join(target_dir, "readable_report.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(f"ASETool Reconnaissance Report - {target}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Duration: {summary['duration_seconds']:.2f} seconds\n")
        f.write(f"Risk Level: {summary['risk_level']}\n\n")
        
        f.write("KEY FINDINGS:\n")
        f.write("-"*40 + "\n")
        for finding in summary['key_findings']:
            f.write(f"• {finding}\n")
        
        f.write("\n\nDETAILED RESULTS:\n")
        f.write("-"*40 + "\n")
        for module, data in results.items():
            f.write(f"\n[{module.upper()}]\n")
            f.write(json.dumps(data, indent=2, default=str))
            f.write("\n" + "-"*40 + "\n")
    
    # Save CSV for statistics
    csv_path = os.path.join(target_dir, "statistics.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("Metric,Value\n")
        for key, value in summary['statistics'].items():
            f.write(f"{key},{value}\n")
        f.write(f"duration_seconds,{summary['duration_seconds']}\n")
        f.write(f"risk_level,{summary['risk_level']}\n")
    
    return json_path, txt_path, csv_path

def main():
    print(BANNER)
    print_color("\n🎬 INITIALIZING RECONNAISSANCE SEQUENCE...", Colors.GOLD)
    
    # Get target
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print_color(f"🎯 TARGET SPECIFIED: {target}", Colors.BRIGHT_CYAN)
    else:
        target = input(f"\n{Colors.GOLD}🔍 Enter target domain: {Colors.RESET}").strip()
    
    if not target:
        print_color("❌ No target specified. Aborting.", Colors.RED)
        sys.exit(1)
    
    # Authorization
    print_color("\n⚖️  AUTHORIZATION PROTOCOL", Colors.BOLD + Colors.BRIGHT_RED)
    print_color("⚠️  You must have explicit written permission to scan this target", Colors.YELLOW)
    
    if not prompt_yes_no(f"\n📝 Confirm authorization for {target}?", default=False):
        print_color("\n❌ Authorization denied. Exiting.", Colors.RED)
        sys.exit(1)
    
    print_color("✅ Authorization verified.", Colors.GREEN)
    
    # Module selection
    modules = choose_modules()
    
    # Configuration
    shodan_key = input(f"\n{Colors.BRIGHT_CYAN}🔑 Shodan API key (Enter to skip): {Colors.RESET}").strip() or None
    default_nmap = "-sV -p- --max-retries 2 --host-timeout 30s"
    nmap_args = input(f"{Colors.BRIGHT_CYAN}🔧 Nmap args (Enter for default): {Colors.RESET}").strip()
    if not nmap_args:
        nmap_args = default_nmap
    
    # Setup output
    results_base = ensure_results_dir()
    target_dir = next_target_dir(results_base, target)
    
    print_color(f"\n📁 Results will be stored in: {target_dir}", Colors.CYAN)
    
    # Initialize and run
    suite = ReconSuite(target=target, shodan_key=shodan_key, nmap_args=nmap_args)
    progress = ProgressTracker(len(modules))
    
    print_color("\n🚀 Starting reconnaissance...\n", Colors.GOLD)
    start_time = time.time()
    
    results = {}
    for module in modules:
        module_result = run_module_with_progress(suite, module, progress)
        results.update(module_result)
    
    progress.finish()
    elapsed_time = time.time() - start_time
    
    # Display formatted results
    format_cli_output(results, target)
    
    # Generate and display summary
    summary = generate_summary(results, target, elapsed_time)
    display_summary(summary)
    
    # Save detailed reports
    json_path, txt_path, csv_path = save_detailed_report(results, target_dir, target, summary)
    
    # Also save HTML report using the suite's method
    html_path = os.path.join(target_dir, "report.html")
    try:
        suite.save_output(results, html_path)
    except:
        # Fallback HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"<!DOCTYPE html><html><head><title>ASETool Report - {target}</title></head>")
            f.write(f"<body><h1>Reconnaissance Report: {target}</h1>")
            f.write(f"<pre>{json.dumps(results, indent=2, default=str)}</pre></body></html>")
    
    # Final output
    print_color("\n" + "="*80, Colors.GOLD)
    print_color("✅ MISSION COMPLETE", Colors.GREEN + Colors.BOLD)
    print_color("="*80, Colors.GOLD)
    print_color(f"\n📄 Reports saved in: {target_dir}", Colors.CYAN)
    print_color(f"   • Complete JSON: {os.path.basename(json_path)}", Colors.SILVER)
    print_color(f"   • Readable TXT: {os.path.basename(txt_path)}", Colors.SILVER)
    print_color(f"   • Statistics CSV: {os.path.basename(csv_path)}", Colors.SILVER)
    print_color(f"   • HTML Report: report.html", Colors.SILVER)
    
    print_color("\n💡 Tip: Check the readable_report.txt for a human-friendly overview\n", Colors.DIM)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_color("\n\n⚠️ Scan interrupted by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_color(f"\n❌ Unexpected error: {str(e)}", Colors.RED)
        sys.exit(1)