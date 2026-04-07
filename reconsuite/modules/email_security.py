#!/usr/bin/env python3
import dns.resolver

def run(ctx):
    """
    Email security module - Checks SPF, DMARC, MX records and assesses spoofing risk
    
    Args:
        ctx: Dictionary containing target information
    
    Returns:
        Dictionary with email security analysis results
    """
    target = ctx["target"]
    out = {}
    
    # Check MX records
    try:
        mx = dns.resolver.resolve(target, "MX", lifetime=5)
        out["mx"] = [r.exchange.to_text().rstrip('.') for r in mx]
    except Exception as e:
        out["mx"] = {"error": str(e)}
    
    # Check TXT records for SPF
    try:
        txt = dns.resolver.resolve(target, "TXT", lifetime=5)
        txts = []
        for r in txt:
            try:
                txts.append("".join([s.decode() if isinstance(s, bytes) else str(s) for s in r.strings]))
            except Exception:
                txts.append(r.to_text())
        spf = [t for t in txts if "v=spf1" in t.lower()]
        out["txt"] = txts
        out["spf"] = spf
    except Exception as e:
        out["txt"] = {"error": str(e)}
    
    # Check DMARC record
    try:
        d = dns.resolver.resolve("_dmarc." + target, "TXT", lifetime=5)
        out["dmarc"] = [r.to_text().strip('"') for r in d]
    except Exception as e:
        out["dmarc"] = {"error": str(e)}
    
    # Assess spoofing risk
    out["spoofing_risk"] = _assess_spoofing(out)
    
    return out

def _assess_spoofing(out):
    """
    Assess email spoofing risk based on DNS records
    
    Args:
        out: Dictionary containing MX, SPF, and DMARC data
    
    Returns:
        Dictionary with risk score and notes
    """
    score = 50  # Start from medium risk
    notes = []
    
    # Check MX records
    if isinstance(out.get("mx"), dict):
        notes.append("❌ No MX records found - Email delivery may be impossible")
        score += 20
    else:
        if out.get("mx"):
            notes.append(f"✓ MX records found: {len(out['mx'])} mail servers")
            score -= 10
        else:
            notes.append("⚠️ No MX records configured")
            score += 15
    
    # Check SPF record
    if not out.get("spf"):
        notes.append("❌ No SPF record found - Domain is vulnerable to spoofing")
        score += 25
    else:
        spf_record = out['spf'][0] if out['spf'] else ""
        if "~all" in spf_record:
            notes.append("⚠️ SPF uses soft fail (~all) - Provides limited protection")
            score += 5
        elif "-all" in spf_record:
            notes.append("✓ SPF uses hard fail (-all) - Good protection against spoofing")
            score -= 15
        elif "+all" in spf_record:
            notes.append("❌ SPF uses +all - Extremely dangerous! Anyone can spoof")
            score += 30
        else:
            notes.append("⚠️ SPF record found but no fail mechanism specified")
            score += 10
    
    # Check DMARC record
    if not out.get("dmarc") or isinstance(out.get("dmarc"), dict):
        notes.append("❌ No DMARC record found - No policy for unauthenticated emails")
        score += 25
    else:
        dmarc_record = out['dmarc'][0] if out['dmarc'] else ""
        if "p=reject" in dmarc_record:
            notes.append("✓ DMARC policy: reject - Strongest protection")
            score -= 20
        elif "p=quarantine" in dmarc_record:
            notes.append("✓ DMARC policy: quarantine - Good protection")
            score -= 10
        elif "p=none" in dmarc_record:
            notes.append("⚠️ DMARC policy: none - Monitoring only, no enforcement")
            score += 5
        else:
            notes.append("⚠️ DMARC found but policy unclear")
            score += 10
    
    # Additional DMARC checks
    if not isinstance(out.get("dmarc"), dict) and out.get("dmarc"):
        dmarc_record = out['dmarc'][0] if out['dmarc'] else ""
        if "rua=" in dmarc_record:
            notes.append("📊 DMARC aggregate reports configured")
        if "ruf=" in dmarc_record:
            notes.append("🔍 DMARC forensic reports configured")
    
    # Normalize score between 0-100
    score = max(0, min(100, score))
    
    # Determine risk level
    if score >= 70:
        risk_level = "CRITICAL"
    elif score >= 50:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "score": score,
        "risk_level": risk_level,
        "notes": notes,
        "recommendations": _get_recommendations(out, score)
    }

def _get_recommendations(out, score):
    """
    Generate recommendations based on findings
    
    Args:
        out: Dictionary containing MX, SPF, and DMARC data
        score: Current risk score
    
    Returns:
        List of recommendations
    """
    recommendations = []
    
    if isinstance(out.get("mx"), dict) or not out.get("mx"):
        recommendations.append("Configure MX records to enable email delivery")
    
    if not out.get("spf"):
        recommendations.append("Publish an SPF record to prevent email spoofing")
    elif out.get("spf") and "~all" in out['spf'][0]:
        recommendations.append("Upgrade SPF from soft fail (~all) to hard fail (-all)")
    elif out.get("spf") and "+all" in out['spf'][0]:
        recommendations.append("IMMEDIATELY remove +all from SPF record - Critical security risk!")
    
    if not out.get("dmarc") or isinstance(out.get("dmarc"), dict):
        recommendations.append("Implement DMARC policy starting with p=none, then move to p=quarantine or p=reject")
    elif out.get("dmarc") and "p=none" in out['dmarc'][0]:
        recommendations.append("Progress DMARC policy from none to quarantine or reject")
    
    if score > 60:
        recommendations.append("Consider implementing BIMI (Brand Indicators for Message Identification)")
        recommendations.append("Enable MTA-STS (SMTP MTA Strict Transport Security)")
    
    return recommendations