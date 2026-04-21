"""Export contacts to flat CSV format exactly as requested"""
from models.database import SessionLocal, Contact, ContactType, DomainContact, Keyword, SearchResult
import csv
import sys

def export_flat_contacts():
    db = SessionLocal()
    
    try:
        # Query all data needed for flat export
        query = (
            db.query(
                Keyword.id.label('keyword_id'),
                Keyword.keyword,
                Keyword.country,
                Keyword.language,
                DomainContact.domain,
                DomainContact.tags,
                Contact.contact_type,
                Contact.value
            )
            .join(SearchResult, DomainContact.search_result_id == SearchResult.id)
            .join(Keyword, SearchResult.keyword_id == Keyword.id)
            .join(Contact, Contact.domain_contact_id == DomainContact.id)
            .order_by(Keyword.id, DomainContact.domain)
        )
        
        results = query.all()
        
        if not results:
            print("No contacts found in database!")
            return
        
        # Group by domain + keyword combination
        domains = {}
        for row in results:
            key = (row.keyword_id, row.keyword, row.country, row.language, row.domain)
            if key not in domains:
                domains[key] = {
                    'keyword': row.keyword,
                    'country': row.country,
                    'language': row.language,
                    'domain': row.domain,
                    'emails': [],
                    'telegrams': [],
                    'linkedins': [],
                    'phones': [],
                    'tags': row.tags or []
                }
            
            if row.contact_type == ContactType.EMAIL:
                if row.value not in domains[key]['emails']:
                    domains[key]['emails'].append(row.value)
            elif row.contact_type == ContactType.TELEGRAM:
                if row.value not in domains[key]['telegrams']:
                    domains[key]['telegrams'].append(row.value)
            elif row.contact_type == ContactType.LINKEDIN:
                if row.value not in domains[key]['linkedins']:
                    domains[key]['linkedins'].append(row.value)
            elif row.contact_type == ContactType.PHONE:
                if row.value not in domains[key]['phones']:
                    domains[key]['phones'].append(row.value)
        
        # Write to CSV
        output_file = 'contacts_export.csv'
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Headers
            writer.writerow([
                '№',
                'Ключевое слово',
                'Страна',
                'Язык',
                'Домен',
                'E-mail',
                'Telegram contact',
                'LinkedIn',
                'Phone',
                'Предметная область'
            ])
            
            # Data rows
            for idx, ((keyword_id, keyword, country, language, domain), data) in enumerate(domains.items(), 1):
                # Extract subject area from tags
                generic_tags = {'b2b', 'company', 'business', 'website'}
                meaningful_tags = [tag for tag in data['tags'] if isinstance(tag, str) and tag.lower() not in generic_tags]
                subject_area = ', '.join(meaningful_tags[:3]) if meaningful_tags else ''
                
                writer.writerow([
                    idx,
                    keyword,
                    country,
                    language,
                    domain,
                    '; '.join(data['emails']) if data['emails'] else '',
                    '; '.join(data['telegrams']) if data['telegrams'] else '',
                    '; '.join(data['linkedins']) if data['linkedins'] else '',
                    '; '.join(data['phones']) if data['phones'] else '',
                    subject_area
                ])
        
        print(f"✅ Exported {len(domains)} domains to {output_file}")
        print(f"\nSummary:")
        total_emails = sum(len(d['emails']) for d in domains.values())
        total_telegram = sum(len(d['telegrams']) for d in domains.values())
        total_linkedin = sum(len(d['linkedins']) for d in domains.values())
        total_phones = sum(len(d['phones']) for d in domains.values())
        
        print(f"  - Total emails: {total_emails}")
        print(f"  - Total Telegram: {total_telegram}")
        print(f"  - Total LinkedIn: {total_linkedin}")
        print(f"  - Total Phones: {total_phones}")
        print(f"\nFile saved as: {output_file}")
        
    finally:
        db.close()

if __name__ == "__main__":
    export_flat_contacts()
