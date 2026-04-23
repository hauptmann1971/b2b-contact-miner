#!/usr/bin/env python3
"""
Download SonarCloud issues report for code fixing.
Requires SONAR_TOKEN environment variable or .env file.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
SONARCLOUD_API = "https://sonarcloud.io/api"
PROJECT_KEY = "hauptmann1971_b2b-contact-miner"
OUTPUT_DIR = Path("doc/sonarcloud_reports")

def get_sonar_token():
    """Get SonarCloud token from environment or .env file."""
    # Try environment variable first
    token = os.getenv('SONAR_TOKEN')
    if token:
        return token
    
    # Try reading from .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('SONAR_TOKEN='):
                    return line.split('=', 1)[1].strip()
    
    print("❌ Error: SONAR_TOKEN not found!")
    print("\nPlease set it in one of these ways:")
    print("1. Environment variable: export SONAR_TOKEN=your_token")
    print("2. Add to .env file: SONAR_TOKEN=your_token")
    print("\nGet token from: https://sonarcloud.io/account/security/")
    return None

def download_issues(token, severity=None, max_issues=500):
    """Download issues from SonarCloud API."""
    url = f"{SONARCLOUD_API}/issues/search"
    
    params = {
        'componentKeys': PROJECT_KEY,
        'ps': 100,  # Page size
        'p': 1,     # Page number
        's': 'SEVERITY',  # Sort by severity
        'asc': 'false'    # Descending order
    }
    
    if severity:
        params['severities'] = severity
    
    all_issues = []
    page = 1
    
    print(f"📥 Downloading issues from SonarCloud...")
    
    while True:
        params['p'] = page
        
        # Try different authentication methods for different token formats
        response = None
        
        # Method 1: Bearer token (for sqp_ tokens)
        if token.startswith('sqp_') or token.startswith('squ_'):
            response = requests.get(
                url, 
                params=params,
                headers={'Authorization': f'Bearer {token}'},
                timeout=30
            )
        
        # Method 2: Basic auth with token as username (for old format tokens)
        if not response or response.status_code == 401:
            response = requests.get(
                url,
                params=params,
                auth=(token, ''),
                timeout=30
            )
        
        # Method 3: Token in query parameter
        if response and response.status_code == 401:
            params_with_token = params.copy()
            params_with_token['sonar.token'] = token
            response = requests.get(
                url,
                params=params_with_token,
                timeout=30
            )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            print(f"Token (first 10 chars): {token[:10] if token else 'None'}...")
            print(f"URL: {response.url}")
            break
        
        data = response.json()
        issues = data.get('issues', [])
        
        if not issues:
            break
        
        all_issues.extend(issues)
        print(f"   Page {page}: {len(issues)} issues (total: {len(all_issues)})")
        
        # Check if we have more pages
        paging = data.get('paging', {})
        total = paging.get('total', 0)
        
        if len(all_issues) >= max_issues or len(all_issues) >= total:
            break
        
        page += 1
    
    return all_issues

def format_issue(issue):
    """Format issue for readability."""
    severity = issue.get('severity', 'UNKNOWN')
    issue_type = issue.get('type', 'UNKNOWN')
    message = issue.get('message', '')
    component = issue.get('component', '').replace(f'{PROJECT_KEY}:', '')
    line = issue.get('line', 'N/A')
    key = issue.get('key', '')
    
    # Get rule info
    rule = issue.get('rule', '')
    
    formatted = {
        'key': key,
        'severity': severity,
        'type': issue_type,
        'rule': rule,
        'file': component,
        'line': line,
        'message': message,
        'status': issue.get('status', 'OPEN'),
        'creationDate': issue.get('creationDate', ''),
    }
    
    return formatted

def save_report(issues, filename):
    """Save issues to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'project': PROJECT_KEY,
            'generated_at': datetime.now().isoformat(),
            'total_issues': len(issues),
            'issues': issues
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Report saved to: {filepath}")
    return filepath

def print_summary(issues):
    """Print summary of issues."""
    print("\n" + "="*70)
    print("SONARCLOUD ISSUES SUMMARY")
    print("="*70)
    
    # Count by severity
    severity_counts = {}
    for issue in issues:
        sev = issue['severity']
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    print("\nBy Severity:")
    for sev in ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']:
        count = severity_counts.get(sev, 0)
        if count > 0:
            print(f"  {sev:10s}: {count}")
    
    # Count by type
    type_counts = {}
    for issue in issues:
        itype = issue['type']
        type_counts[itype] = type_counts.get(itype, 0) + 1
    
    print("\nBy Type:")
    for itype, count in sorted(type_counts.items()):
        print(f"  {itype:15s}: {count}")
    
    # Top files with issues
    file_counts = {}
    for issue in issues:
        file = issue['file']
        file_counts[file] = file_counts.get(file, 0) + 1
    
    print("\nTop 10 Files with Issues:")
    sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for file, count in sorted_files:
        print(f"  {file:50s}: {count} issues")
    
    print("\n" + "="*70)

def main():
    """Main function."""
    print("="*70)
    print("SonarCloud Issues Downloader")
    print("="*70)
    
    # Get token
    token = get_sonar_token()
    if not token:
        return
    
    print(f"\n✅ Token loaded: {token[:10]}...")
    
    # Download BLOCKER and CRITICAL issues first
    print("\n--- Downloading BLOCKER & CRITICAL issues ---")
    critical_issues = download_issues(token, severity='BLOCKER,CRITICAL', max_issues=200)
    critical_formatted = [format_issue(issue) for issue in critical_issues]
    
    if critical_formatted:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_report(critical_formatted, f'critical_issues_{timestamp}.json')
        print_summary(critical_formatted)
    
    # Download all issues
    print("\n--- Downloading ALL issues ---")
    all_issues = download_issues(token, max_issues=1000)
    all_formatted = [format_issue(issue) for issue in all_issues]
    
    if all_formatted:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_report(all_formatted, f'all_issues_{timestamp}.json')
        print_summary(all_formatted)
    
    print("\n💡 Next steps:")
    print("1. Review the JSON reports in doc/sonarcloud_reports/")
    print("2. Share them with AI assistant to fix issues")
    print("3. Start with BLOCKER and CRITICAL severity issues")

if __name__ == '__main__':
    main()
