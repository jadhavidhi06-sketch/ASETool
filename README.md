<div align="center">

# 🔐 ASETool - Advanced Security Enumeration Tool

### *Complete OSINT & Network Reconnaissance Suite*

[![License](https://img.shields.io/badge/License-Educational%20Only-red)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![OSINT](https://img.shields.io/badge/Category-OSINT-green)](https://osintframework.com)
[![No API Keys](https://img.shields.io/badge/No%20API%20Keys-Required-brightgreen)]()

</div>

---

## 🎯 Overview

**ASETool** is a comprehensive, educational OSINT (Open Source Intelligence) and network reconnaissance tool that requires **NO API KEYS**. It's designed for security professionals, students, and researchers to understand how publicly available information can be gathered and analyzed.

### 🌟 Key Features

| Category | Features |
|----------|----------|
| **DNS Enumeration** | A, AAAA, MX, NS, TXT, SOA, CNAME, PTR, SPF, DMARC |
| **Domain Intelligence** | WHOIS lookup, Subdomain discovery, Reverse DNS |
| **Network Analysis** | Traceroute, IP Geolocation, Port Scanning (Nmap) |
| **Web Intelligence** | HTTP Header grabbing, Technology fingerprinting |
| **Person OSINT** | Email analysis, Social media discovery |
| **User Experience** | Interactive menu, Progress bars, Colorized output |

---

## 🚀 Quick Start

### Installation (3 Steps)

```bash
# 1. Clone or download ASETool
git clone https://github.com/yourusername/ASETool.git
cd ASETool

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Nmap (system package)
# Ubuntu/Debian:
sudo apt install nmap
# macOS:
brew install nmap
# Windows: Download from https://nmap.org/download.html

# 4. Run the tool
python ASETool.py