"""Export real website content for LLM testing"""
from models.database import SessionLocal, DomainContact, SearchResult
import json

def export_sample_content():
    """Export sample website content for manual LLM testing"""
    db = SessionLocal()
    
    try:
        # Get a few domain_contacts with their search results
        samples = db.query(DomainContact).join(SearchResult).limit(3).all()
        
        print("=" * 80)
        print("SAMPLE WEBSITE CONTENT FOR LLM TESTING")
        print("=" * 80)
        
        for i, dc in enumerate(samples, 1):
            print(f"\n{'='*80}")
            print(f"SAMPLE {i}")
            print(f"{'='*80}")
            print(f"Domain: {dc.domain}")
            print(f"Extraction method: {dc.extraction_method}")
            print(f"Contacts found: {dc.contacts_json}")
            print(f"\nTo test this content:")
            print(f"1. Open the website: https://{dc.domain}")
            print(f"2. Copy the text from contact/about page")
            print(f"3. Paste it into the prompt template")
            print(f"4. Test with ChatGPT/DeepSeek/YandexGPT")
            print(f"\nURL to visit: https://{dc.domain}/contact OR https://{dc.domain}/about")
            
        print("\n" + "=" * 80)
        print("PROMPT TEMPLATE TO USE:")
        print("=" * 80)
        print("""
Extract contact information from the following website content.

IMPORTANT RULES:
1. Return ONLY valid JSON, no additional text
2. Look for obfuscated emails like: name[at]domain.com, name (at) domain (dot) com
3. Find Telegram links: t.me/username, telegram.me/username, @username
4. Find LinkedIn profiles: linkedin.com/in/name, linkedin.com/company/name
5. Exclude generic emails: noreply@, support@, admin@, webmaster@
6. Include business emails even if they are info@ or sales@

Content to analyze:
[PASTE WEBSITE CONTENT HERE - max 4000 chars]

Return EXACTLY this JSON format (no extra text before or after):
{
  "emails": ["email1@example.com", "email2@example.com"],
  "telegram": ["https://t.me/username", "@username"],
  "linkedin": ["https://linkedin.com/in/name"]
}

If no contacts found, return:
{"emails": [], "telegram": [], "linkedin": []}
        """)
        
    finally:
        db.close()

if __name__ == "__main__":
    export_sample_content()
