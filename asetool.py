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

# Cinematic banner with ASETool branding
def make_banner():
    cols = 80
    try:
        cols = os.get_terminal_size().columns
        cols = max(80, min(cols, 140))
    except Exception:
        cols = 80
    
    # Cinematic ASCII art with ASETool
    title_lines = [
        r"    █████╗ ███████╗ ███████╗████████╗ ██████╗  ██████╗ ██╗     ",
        r"   ██╔══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔═══██╗██╔═══██╗██║     ",
        r"   ███████║███████╗ █████╗     ██║   ██║   ██║██║   ██║██║     ",
        r"   ██╔══██║╚════██║ ██╔══╝     ██║   ██║   ██║██║   ██║██║     ",
        r"   ██║  ██║║███████║███████╗   ██║   ╚██████╔╝╚██████╔╝███████╗",
        r"   ╚═╝  ╚═╝╝╚══════╝╚══════╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝",
        r"",
    ]
    
    # Dynamic subtitle and tagline
    subtitle = "⚡ ADVANCED SECURITY EVALUATION TOOLKIT ⚡"
    tagline = "Precision Reconnaissance • Ethical Intelligence • Professional Grade"
    version = "v2.0.0"
    
    # Calculate center positions
    art_width = max(len(line) for line in title_lines)
    start_col = (cols - art_width) // 2 if art_width < cols else 0
    
    # ANSI color codes for cinematic feel
    colors = {
        'red': '\033[38;2;255;0;85m',
        'cyan': '\033[38;2;0;255;255m',
        'gold': '\033[38;2;255;215;0m',
        'silver': '\033[38;2;192;192;192m',
        'dark_red': '\033[38;2;139;0;0m',
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
    }
    
    # Create gradient effect for ASCII art
    gradient_lines = []
    for i, line in enumerate(title_lines):
        # Alternate colors for dramatic effect
        if i < 6:  # First logo
            if i % 2 == 0:
                color = colors['cyan']
            else:
                color = colors['gold']
        else:  # Second part "ETOOL"
            if i % 2 == 0:
                color = colors['red']
            else:
                color = colors['silver']
        
        spaced_line = ' ' * start_col + line
        gradient_lines.append(color + spaced_line + colors['reset'])
    
    # Cinematic border
    border = colors['dark_red'] + "═" * cols + colors['reset']
    thin_border = colors['dim'] + "─" * cols + colors['reset']
    
    # Assemble banner with cinematic formatting
    banner_parts = [
        border,
        "",
        *gradient_lines,
        "",
        colors['bold'] + colors['gold'] + subtitle.center(cols) + colors['reset'],
        colors['silver'] + tagline.center(cols) + colors['reset'],
        "",
        colors['dim'] + version.center(cols) + colors['reset'],
        thin_border,
    ]
    
    # Add some cinematic sparkle (stars at corners)
    banner_parts.insert(1, colors['gold'] + "✨" + " " * (cols - 2) + "✨" + colors['reset'])
    banner_parts.append(colors['gold'] + "✨" + " " * (cols - 2) + "✨" + colors['reset'])
    banner_parts.append(border)
    
    return "\n".join(banner_parts)

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
    print("\n📋 Available Modules:")
    print("  " + "─" * 50)
    for i, m in enumerate(DEFAULT_MODULES, 1):
        print(f"  {i:2}. {m:12}", end="  ")
        if i % 3 == 0:
            print()
    if len(DEFAULT_MODULES) % 3 != 0:
        print()
    print("  " + "─" * 50)
    print("  0. ALL modules (full reconnaissance)")
    sel = input("\n🎯 Enter module numbers separated by comma (e.g. 1,3,5) or 0 for all: ").strip()
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

def print_cinematic_header(text, color_code='\033[38;2;255;215;0m'):
    """Print a cinematic styled header"""
    cols = 80
    try:
        cols = os.get_terminal_size().columns
    except:
        pass
    
    reset = '\033[0m'
    border = "═" * cols
    print(f"\n{color_code}{border}{reset}")
    print(f"{color_code}{text.center(cols)}{reset}")
    print(f"{color_code}{border}{reset}\n")

def main():
    print(BANNER)
    
    # Cinematic intro effect
    print("\033[38;2;255;215;0m" + "🎬 INITIALIZING RECONNAISSANCE SEQUENCE...".center(80) + "\033[0m")
    
    # Get target
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"\033[38;2;0;255;255m🎯 TARGET SPECIFIED: {target}\033[0m")
    else:
        target = input("\n\033[38;2;255;215;0m🔍 Enter target domain (e.g., example.com): \033[0m").strip()
    
    if not target:
        print("\033[38;2;255;0;85m❌ No target specified. Aborting mission.\033[0m")
        sys.exit(1)
    
    # Authorization check with cinematic styling
    print_cinematic_header("⚖️  AUTHORIZATION PROTOCOL  ⚖️", '\033[38;2;255;0;85m')
    print("\033[38;2;192;192;192m⚠️  LEGAL REQUIREMENT: You must have explicit written permission to scan the target.\033[0m")
    print(f"\033[38;2;255;215;0m🎯 Target: {target}\033[0m")
    
    if not prompt_yes_no(f"\n📝 Do you confirm you have authorization to scan {target}?", default=False):
        print("\n\033[38;2;255;0;85m❌ Authorization not confirmed. Terminating session.\033[0m")
        sys.exit(1)
    
    print("\n\033[38;2;0;255;0m✅ Authorization verified. Proceeding with reconnaissance.\033[0m")
    
    modules = choose_modules()
    
    shodan_key = input("\n\033[38;2;0;255;255m🔑 Shodan API key (press Enter to skip): \033[0m").strip() or None
    if shodan_key:
        print("\033[38;2;0;255;0m✓ Shodan integration enabled\033[0m")
    
    default_nmap = "-sV -p- --max-retries 2 --host-timeout 30s"
    nmap_args = input(f"\033[38;2;0;255;255m🔧 nmap args (press Enter for default '{default_nmap}'): \033[0m").strip()
    if not nmap_args:
        nmap_args = default_nmap
    
    results_base = ensure_results_dir()
    target_dir = next_target_dir(results_base, target)
    
    print_cinematic_header("📁 OUTPUT DIRECTORY", '\033[38;2;0;255;255m')
    print(f"📂 {target_dir}\n")
    
    print_cinematic_header("🚀 EXECUTING MODULES", '\033[38;2;0;255;255m')
    print(f"📋 Modules loaded: {', '.join(modules)}")
    print(f"🔧 Nmap arguments: {nmap_args}\n")
    
    suite = ReconSuite(target=target, shodan_key=shodan_key, nmap_args=nmap_args)
    print("\033[38;2;0;255;255m⚡ Running reconnaissance modules...\033[0m\n")
    
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
                    fh.write(f"<!doctype html><html><head><meta charset='utf-8'><title>ASETool Report - {target}</title></head><body>{body}</body></html>")
            except Exception:
                pass
    
    # Cinematic completion screen
    print_cinematic_header("✅ MISSION COMPLETE", '\033[38;2;0;255;0m')
    print(f"\033[38;2;0;255;255m📊 JSON Report:   \033[38;2;192;192;192m{json_path}\033[0m")
    print(f"\033[38;2;0;255;255m🌐 HTML Report:   \033[38;2;192;192;192m{html_dst}\033[0m")
    print(f"\033[38;2;0;255;255m📁 Results Directory: \033[38;2;192;192;192m{target_dir}\033[0m")
    
    # ASCII art completion
    completion_art = r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ║
    ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█░░░█▀▀░█▀█░█▄█░█▀█░█░░░█▀▀░▀█▀░█▀▀░   ║
    ║   ░█░░░█░█░█░█░█▀▀░▄▀▄░░░█░░░█░█░█░█░█▀▀░█░░░█▀▀░░█░░█▀▀░   ║
    ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀░░░▀▀▀░▀▀▀░▀░▀░▀░░░▀▀▀░▀▀▀░░▀░░▀▀▀░   ║
    ║   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   ║
    ║                                                              ║
    ║              🎯 RECONNAISSANCE SUCCESSFUL 🎯                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print("\033[38;2;0;255;255m" + completion_art + "\033[0m")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())