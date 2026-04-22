#!/bin/bash
# SonarQube Report Script
# Note: Update credentials if changed

SONAR_USER="admin"
SONAR_PASS="ISPrevGR1_1971"
BASE_URL="http://localhost:9000"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         SonarQube Analysis Report                         ║"
echo "║         Project: B2B Contact Miner                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Get main metrics
METRICS=$(curl -s -u "$SONAR_USER:$SONAR_PASS" \
  "$BASE_URL/api/measures/component?component=b2b-contact-miner&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_index,reliability_rating,security_rating")

echo "📊 CODE QUALITY METRICS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Parse and display metrics
echo "$METRICS" | python3 << 'PYTHON_SCRIPT'
import sys, json

data = json.load(sys.stdin)
if 'component' in data and 'measures' in data['component']:
    measures = {m['metric']: m.get('value', 'N/A') for m in data['component']['measures']}
    
    # Rating helper
    def rating_label(value):
        ratings = {'1.0': 'A ✅', '2.0': 'B', '3.0': 'C ⚠️', '4.0': 'D ❌', '5.0': 'E ❌'}
        return ratings.get(str(value), str(value))
    
    print(f"🐛 Bugs:                      {measures.get('bugs', 'N/A')}")
    print(f"🔒 Vulnerabilities:           {measures.get('vulnerabilities', 'N/A')}")
    print(f"📝 Code Smells:               {measures.get('code_smells', 'N/A')}")
    print(f"📊 Test Coverage:             {measures.get('coverage', 'N/A')}%")
    print(f"🔄 Code Duplication:          {measures.get('duplicated_lines_density', 'N/A')}%")
    print()
    print("🏆 RATINGS (A=Best, E=Worst)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🛡️  Reliability:                {rating_label(measures.get('reliability_rating'))}")
    print(f"🔐 Security:                   {rating_label(measures.get('security_rating'))}")
    print(f"⏱️  Technical Debt:            {measures.get('sqale_index', 'N/A')} minutes")
else:
    print("❌ No metrics available")
PYTHON_SCRIPT

echo ""
echo "🚨 CRITICAL ISSUES (Top 5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get critical issues
ISSUES=$(curl -s -u "$SONAR_USER:$SONAR_PASS" \
  "$BASE_URL/api/issues/search?componentKeys=b2b-contact-miner&types=BUG,VULNERABILITY&severities=CRITICAL,BLOCKER&s=CREATION_DATE&asc=false&ps=5")

echo "$ISSUES" | python3 << 'PYTHON_SCRIPT'
import sys, json

data = json.load(sys.stdin)
total = data.get('total', 0)
issues = data.get('issues', [])

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
PYTHON_SCRIPT

echo ""
echo "📈 QUALITY GATE STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

QG_STATUS=$(curl -s -u "$SONAR_USER:$SONAR_PASS" \
  "$BASE_URL/api/qualitygates/project_status?projectKey=b2b-contact-miner")

echo "$QG_STATUS" | python3 << 'PYTHON_SCRIPT'
import sys, json

data = json.load(sys.stdin)
status = data.get('projectStatus', {}).get('status', 'UNKNOWN')
cayc = data.get('projectStatus', {}).get('caycStatus', 'N/A')

if status == 'OK':
    print(f"✅ Status: PASSED")
elif status == 'ERROR':
    print(f"❌ Status: FAILED")
else:
    print(f"⚠️  Status: {status}")

print(f"🎯 Clean as You Code: {cayc}")
PYTHON_SCRIPT

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 View full report:"
echo "   http://85.198.86.237:9000/dashboard?id=b2b-contact-miner"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
