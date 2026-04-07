# ASERecon v4.0 (Modular CLI)

ASERecon is an **authorized security assessment** CLI that now includes:

- Nmap full port scanning (`-p- -sV --open`)
- Nmap technology-focused NSE scripts
- Nmap vulnerability NSE scan (`--script vuln`)
- theHarvester email discovery
- Interactive module picker so you can run only what you need
- JSON output containing command outputs for complete review

## Legal Notice
Use only on systems you own or have explicit written permission to test.

## Installation

```bash
pip install -r requirements.txt
```

Install OSINT/scan tools in your OS:

- `nmap`
- `theHarvester`

## Quick Start

```bash
python asetool.py -t example.com
```

The banner opens an interactive module menu so you can choose specific scans.

## Non-interactive Usage

Run all modules:

```bash
python asetool.py -t example.com --non-interactive
```

Run specific modules only:

```bash
python asetool.py -t example.com --non-interactive -m dns,email,ports,vulns
```

Custom output file:

```bash
python asetool.py -t example.com --non-interactive -m ports,vulns -o results.json
```

## Modules

- `dns` — DNS records + resolved IP
- `whois` — domain registration details
- `subdomains` — crt.sh + common DNS brute checks
- `email` — MX/SPF/DMARC + theHarvester output
- `technology` — HTTP fingerprint + nmap NSE web scripts
- `ports` — nmap open ports/services scan
- `vulns` — nmap vulnerability NSE scripts
- `headers` — HTTP security header checks

## Output

- Console: per-module JSON preview
- File: full JSON report (`aserecon_<target>_<timestamp>.json`)
- Raw command outputs are retained for nmap/theHarvester modules

## Notes

If `nmap` or `theHarvester` are missing, ASERecon will continue and record an error message in the output.
