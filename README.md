<!-- README.md - GitHub will render this natively -->

# 🔍 ASERecon v3.0 - Advanced CLI Security Tool

<p align="center">
  <img src="https://img.shields.io/badge/Security-Testing-red" alt="Security Testing">
  <img src="https://img.shields.io/badge/OSINT-Collection-blue" alt="OSINT">
  <img src="https://img.shields.io/badge/Python-3.7+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

> # ⚠️ EDUCATIONAL PURPOSE ONLY
> 
> **CRITICAL LEGAL NOTICE:** This tool is designed SOLELY for authorized penetration testing, 
> educational security research, and system administrators auditing their own infrastructure.
> 
> You MUST have EXPLICIT WRITTEN AUTHORIZATION before using this tool on any system you do not own.
> Unauthorized use may violate the Computer Fraud and Abuse Act (CFAA), GDPR, HIPAA, PCI DSS, 
> and other applicable laws. Violators face CRIMINAL PROSECUTION, FINES, and IMPRISONMENT.

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage Examples](#-usage-examples)
- [Command Line Options](#-command-line-options)
- [Risk Scoring](#-risk-scoring)
- [Shodan Integration](#-shodan-integration)
- [Legal Guidelines](#-legal-guidelines)
- [FAQ](#-frequently-asked-questions)

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/aserecon.git
cd aserecon

# Install dependencies
pip install -r requirements.txt

# Basic scan (no API key required)
python asetool.py -t example.com

# Full scan with Shodan
python asetool.py -t example.com -s YOUR_SHODAN_API_KEY

# View help
python asetool.py -h
