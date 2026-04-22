#!/bin/bash
source /etc/profile.d/sonarqube.sh

echo "=== SonarQube Analysis Report ==="
echo ""

# Get main metrics
curl -s -u "$SONAR_TOKEN:" \
  "http://localhost:9000/api/measures/component?component=b2b-contact-miner&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_rating,reliability_rating,security_rating,maintainability_rating" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'component' in data and 'measures' in data['component']:
    measures = {m['metric']: m.get('value', 'N/A') for m in data['component']['measures']}
    
    print('📊 Code Quality Metrics:')
    print('=' * 50)
    print(f\"🐛 Bugs:                    {measures.get('bugs', 'N/A')}\")
    print(f\"🔒 Vulnerabilities:         {measures.get('vulnerabilities', 'N/A')}\")
    print(f\"📝 Code Smells:             {measures.get('code_smells', 'N/A')}\")
    print(f\"📊 Coverage:                {measures.get('coverage', 'N/A')}%\")
    print(f\"🔄 Duplicated Lines:        {measures.get('duplicated_lines_density', 'N/A')}%\")
    print()
    print('🏆 Ratings (A=Best, E=Worst):')
    print('=' * 50)
    print(f\"📈 Maintainability:         {measures.get('sqale_rating', 'N/A')}\")
    print(f\"🛡️  Reliability:              {measures.get('reliability_rating', 'N/A')}\")
    print(f\"🔐 Security:                 {measures.get('security_rating', 'N/A')}\")
else:
    print('❌ No data available')
"

echo ""
echo "View full report: http://85.198.86.237:9000/dashboard?id=b2b-contact-miner"
