#!/usr/bin/env python3
import os
import sys
import shutil
import textwrap
from reconsuite.reconsuite import ReconSuite

# try to import curses menu helper
try:
    from reconsuite.curses_menu import run_curses_menu
    CURSES_AVAILABLE = True
except Exception:
    CURSES_AVAILABLE = False

# Polished banner: uses ANSI sequences, fills terminal width where possible
def make_banner():
    cols = 80
    try:
        cols = os.get_terminal_size().columns
        cols = max(60, min(cols, 120))
    except Exception:
        cols = 80

    title_lines = [
        r"   ___    ____  _______   ____  ____",
        r"  / _ |  / __ \/ ___/ /  / __ \/ __ \ ",
        r" / __ | / /_/ /\__ \/ /__/ /_/ / /_/ /",
        r"/_/ |_| \____/___/ /____/\____/\____/ ",
    ]
    subtitle = "AS E-Tool — Authorized Recon Suite"
    tagline = "Fast. Focused. Responsible."

    # center the ASCII art
    art = "\n".join(line.center(cols) for line in title_lines)
    subtitle_line = subtitle.center(cols)
    tag_line = tagline.center(cols)

    # color blocks
    cyan = "\033[1;36m"
    yellow = "\033[1;33m"
    green = "\033[1;32m"
    reset = "\033[0m"

    banner = "\n".join([
        cyan + art + reset,
        yellow + subtitle_line + reset,
        green + tag_line + reset,
    ])
    wrapper = "\n" + banner + "\n"
    return wrapper

BANNER = make_banner()

DEFAULT_MODULES = ["dns", "whois", "subdomains", "emailsec", "tech", "nmap", "emails", "headers", "wayback", "shodan", "risk"]

def ensure_results_dir(base="results"):
    os.makedirs(base, exist_ok=True)
    return base

def _safe_name(name: str) -> str:
    # create filesystem-safe name for target directories
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in name)

def next_target_dir(base, target):
    safe = _safe_name(target)
    existing = [d for d in os.listdir(base) if d.startswith(safe)]
    if not existing:
        name = f"{safe}"
    else:
        name = f"{safe}_{len(existing) + 1}"
    out = os.path.join(base, name)
    os.makedirs(out, exist_ok=True)
    return out

def choose_modules():
    if CURSES_AVAILABLE:
        chosen = run_curses_menu(DEFAULT_MODULES)
        if chosen:
            return chosen
    print("\nAvailable modules:")
    for i, m in enumerate(DEFAULT_MODULES, 1):
        print(f"  {i}. {m}")
    print("  0. all")
    sel = input("\nEnter module numbers separated by comma (e.g. 1,3,5) or 0 for all: ").strip()
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

def main():
    print(BANNER)
    # Get target
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("Target domain (e.g., example.com): ").strip()
    if not target:
        print("No target specified. Exiting.")
        sys.exit(1)

    print("\nAuthorization required: You must have explicit written permission to scan the target.")
    if not prompt_yes_no(f"Do you confirm you have authorization to scan {target}?", default=False):
        print("Authorization not confirmed. Exiting.")
        sys.exit(1)

    modules = choose_modules()
    shodan_key = input("Shodan API key (press Enter to skip): ").strip() or None
    default_nmap = "-sV -p- --max-retries 2 --host-timeout 30s"
    nmap_args = input(f"nmap args (press Enter for default '{default_nmap}'): ").strip()
    if not nmap_args:
        nmap_args = default_nmap

    results_base = ensure_results_dir()
    target_dir = next_target_dir(results_base, target)

    print(f"\nResults will be stored in: {target_dir}\n")

    suite = ReconSuite(target=target, shodan_key=shodan_key, nmap_args=nmap_args)
    print("Running modules:", ", ".join(modules))
    report = suite.run_modules(modules)

    json_path = os.path.join(target_dir, "report.json")
    suite.save_output(report, json_path)

    # move HTML if saved next to JSON
    html_src = json_path.replace(".json", ".html")
    html_dst = os.path.join(target_dir, "report.html")
    if os.path.exists(html_src):
        shutil.move(html_src, html_dst)
    else:
        # if save_output didn't create an HTML, create a minimal one
        try:
            from reconsuite.utils.output import save_html
            save_html(report, html_dst)
        except Exception:
            # fallback: write basic HTML
            try:
                import json, html as _html
                body = "<pre>" + _html.escape(json.dumps(report, indent=2)) + "</pre>"
                with open(html_dst, "w", encoding="utf-8") as fh:
                    fh.write(f"<!doctype html><html><head><meta charset='utf-8'><title>Report</title></head><body>{body}</body></html>")
            except Exception:
                pass

    print("\nScan complete.")
    print("Saved JSON:", json_path)
    print("Saved HTML :", html_dst)
    return 0

if __name__ == "__main__":
    sys.exit(main())
