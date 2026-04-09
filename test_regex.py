import re

pattern = re.compile(r'href=["\']mailto:([^"\']+)["\']', re.IGNORECASE)
content = '<a href="mailto:info@company.com?subject=Hello">Contact</a>'

matches = list(pattern.finditer(content))
print(f"Found {len(matches)} matches")
for m in matches:
    email = m.group(1).strip()
    print(f"Raw match: '{email}'")
    email = email.split('?')[0]
    print(f"After split: '{email}'")
