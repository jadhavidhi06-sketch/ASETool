#!/usr/bin/env python3
import os, sys, shutil
from reconsuite.reconsuite import ReconSuite

# try to import curses menu helper
try:
    from reconsuite.curses_menu import run_curses_menu
    CURSES_AVAILABLE = True
except Exception:
    CURSES_AVAILABLE = False

BANNER = r"""
\033[1;36m   ___    ____  _______   ____  ____\033[0m
\033[1;36m  / _ |  / __ \/ ___/ /  / __ \/ __ \ \033[0m
\033[1;36m / __ | / /_/ /\__ \/ /__/ /_/ / /_/ /\033[0m
\033[1;36m/_/ |_| \____/___/ /____/\____/\____/ \033[0m
\033[1;33m      AS E-Tool - Authorized Recon Suite\033[0m
"""

DEFAULT_MODULES = ["dns","whois","subdomains","emailsec","tech","nmap","emails","headers","wayback","shodan","risk"]

def ensure_results_dir(base="results"):
    os.makedirs(base, exist_ok=True)
    return base

def next_target_dir(base, target):
    safe = target.replace("/", "_").replace(":", "_")
    existing = [d for d in os.listdir(base) if d.startswith(safe)]
    if not existing:
        name = f"{safe}"
    else:
        name = f"{safe}_{len(existing)+1}"
    out = os.path.join(base, name)
    os.makedirs(out, exist_ok=True)
    return out

def choose_modules():
    if CURSES_AVAILABLE:
        chosen = run_curses_menu(DEFAULT_MODULES)
        if chosen:
            return chosen
    print("\nAvailable modules:")
    for i,m in enumerate(DEFAULT_MODULES,1):
        print(f"  {i}. {m}")
    print("  0. all")
    sel = input("\nEnter module numbers separated by comma (e.g. 1,3,5) or 0 for all: ").strip()
    if sel in ("0","all","0."):
        return DEFAULT_MODULES
    nums = [s.strip() for s in sel.split(",") if s.strip().isdigit()]
    picked = []
    for n in nums:
        idx = int(n)-1
        if 0 <= idx < len(DEFAULT_MODULES):
            picked.append(DEFAULT_MODULES[idx])
    return picked or DEFAULT_MODULES

def main():
    print(BANNER)
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("Target domain (e.g., example.com): ").strip()
    if not target:
        print("No target specified. Exiting.")
        sys.exit(1)

    print("\nAuthorization required: You must have explicit written permission to scan the target.")
    consent = input(f"Do you confirm you have authorization to scan {target}? (yes/no): ").strip().lower()
    if consent not in ("yes","y"):
        print("Authorization not confirmed. Exiting.")
        sys.exit(1)

    modules = choose_modules()
    shodan_key = input("Shodan API key (press Enter to skip): ").strip() or None
    nmap_args = input("nmap args (press Enter for default '-sV -p- --max-retries 2 --host-timeout 30s'): ").strip()
    if not nmap_args:
        nmap_args = "-sV -p- --max-retries 2 --host-timeout 30s"

    results_base = ensure_results_dir()
    target_dir = next_target_dir(results_base, target)

    print(f"\nResults will be stored in: {target_dir}\n")

    suite = ReconSuite(target=target, shodan_key=shodan_key, nmap_args=nmap_args)
    print("Running modules:", ", ".join(modules))
    report = suite.run_modules(modules)
    json_path = os.path.join(target_dir, "report.json")
    suite.save_output(report, json_path)
    html_path = json_path.replace(".json",".html")
    if os.path.exists(html_path):
        shutil.move(html_path, os.path.join(target_dir, "report.html"))
    print("\nScan complete.")
    print("Saved:", json_path)
    print("Saved:", os.path.join(target_dir, "report.html"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
