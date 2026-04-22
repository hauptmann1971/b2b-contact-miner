#!/usr/bin/env python3
"""SonarQube Report Generator"""
import json
import urllib.request
import sys

SONAR_URL = "http://localhost:9000"
SONAR_USER = "admin"
SONAR_PASS = "ISPrevGR1_1971"
PROJECT_KEY = "b2b-contact-miner"

def sonar_api(endpoint):
    """Make authenticated request to SonarQube API"""
    url = f"{SONAR_URL}{endpoint}"
    req = urllib.request.Request(url)
    credentials = f"{SONAR_USER}:{SONAR_PASS}"
    req.add_header('Authorization', 'Basic ' + credentials.encode().hex())
    
    # Use basic auth properly
    import base64
    credentials_bytes = f"{SONAR_USER}:{SONAR_PASS}".encode('utf-8')
    encoded_credentials = base64.b64encode(credentials_bytes).decode('utf-8')
    req.add_header('Authorization', f'Basic {encoded_credentials}')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error fetching {endpoint}: {e}", file=sys.stderr)
        return None

def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         SonarQube Analysis Report                         ║")
    print("║         Project: B2B Contact Miner                        ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    # Get metrics
    print("📊 CODE QUALITY METRICS")
    print("━" * 55)
    
    metrics_data = sonar_api(
        f"/api/measures/component?component={PROJECT_KEY}"
        "&metricKeys=bugs,vulnerabilities,code_smells,coverage,"
        "duplicated_lines_density,sqale_index,reliability_rating,security_rating"
    )
    
    if metrics_data and 'component' in metrics_data:
        measures = {m['metric']: m.get('value', 'N/A') 
                   for m in metrics_data['component']['measures']}
        
        def rating_label(value):
            ratings = {'1.0': 'A ✅', '2.0': 'B', '3.0': 'C ⚠️', 
                      '4.0': 'D ❌', '5.0': 'E ❌'}
            return ratings.get(str(value), str(value))
        
        print(f"🐛 Bugs:                      {measures.get('bugs', 'N/A')}")
        print(f"🔒 Vulnerabilities:           {measures.get('vulnerabilities', 'N/A')}")
        print(f"📝 Code Smells:               {measures.get('code_smells', 'N/A')}")
        print(f"📊 Test Coverage:             {measures.get('coverage', 'N/A')}%")
        print(f"🔄 Code Duplication:          {measures.get('duplicated_lines_density', 'N/A')}%")
        print()
        print("🏆 RATINGS (A=Best, E=Worst)")
        print("━" * 55)
        print(f"🛡️  Reliability:                {rating_label(measures.get('reliability_rating'))}")
        print(f"🔐 Security:                   {rating_label(measures.get('security_rating'))}")
        print(f"⏱️  Technical Debt:            {measures.get('sqale_index', 'N/A')} minutes")
    else:
        print("❌ Could not fetch metrics")
    
    print()
    print("🚨 CRITICAL ISSUES (Top 5)")
    print("━" * 55)
    
    issues_data = sonar_api(
        f"/api/issues/search?componentKeys={PROJECT_KEY}"
        "&types=BUG,VULNERABILITY&severities=CRITICAL,BLOCKER"
        "&s=CREATION_DATE&asc=false&ps=5"
    )
    
    if issues_data:
        total = issues_data.get('total', 0)
        issues = issues_data.get('issues', [])
        
        if total == 0:
            print("✅ No critical issues found!")
        else:
            print(f"Total critical issues: {total}\n")
            for i, issue in enumerate(issues[:5], 1):
                severity = issue.get('severity', 'UNKNOWN')
                msg_type = '🐛 BUG' if issue.get('type') == 'BUG' else '🔒 VULN'
                message = issue.get('message', 'No message')
                component = issue.get('component', '').split(':')[-1]
                line = issue.get('line', 'N/A')
                
                print(f"{i}. [{severity}] {msg_type}")
                print(f"   Message: {message}")
                print(f"   File: {component}:{line}")
                print()
    else:
        print("❌ Could not fetch issues")
    
    print()
    print("📈 QUALITY GATE STATUS")
    print("━" * 55)
    
    qg_data = sonar_api(
        f"/api/qualitygates/project_status?projectKey={PROJECT_KEY}"
    )
    
    if qg_data and 'projectStatus' in qg_data:
        status = qg_data['projectStatus'].get('status', 'UNKNOWN')
        cayc = qg_data['projectStatus'].get('caycStatus', 'N/A')
        
        if status == 'OK':
            print(f"✅ Status: PASSED")
        elif status == 'ERROR':
            print(f"❌ Status: FAILED")
        else:
            print(f"⚠️  Status: {status}")
        
        print(f"🎯 Clean as You Code: {cayc}")
    else:
        print("❌ Could not fetch quality gate status")
    
    print()
    print("━" * 55)
    print("📋 View full report:")
    print(f"   http://85.198.86.237:9000/dashboard?id={PROJECT_KEY}")
    print("━" * 55)

if __name__ == "__main__":
    main()
