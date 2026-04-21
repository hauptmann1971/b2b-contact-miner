"""Check what contacts are actually in the database"""
from models.database import SessionLocal, Contact, ContactType, DomainContact, Keyword, SearchResult
from sqlalchemy import func

def check_contacts():
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("DATABASE CONTACTS ANALYSIS")
        print("=" * 80)
        
        # Total counts by type
        print("\n1. TOTAL CONTACTS BY TYPE:")
        print("-" * 80)
        for contact_type in ContactType:
            count = db.query(Contact).filter(Contact.contact_type == contact_type).count()
            print(f"   {contact_type.value:15} : {count:6} records")
        
        total = db.query(Contact).count()
        print(f"   {'TOTAL':15} : {total:6} records")
        
        # Check domain_contacts with JSON
        print("\n2. DOMAIN_CONTACTS WITH contacts_json:")
        print("-" * 80)
        domain_contacts = db.query(DomainContact).all()
        print(f"   Total domain_contacts records: {len(domain_contacts)}")
        
        if domain_contacts:
            sample = domain_contacts[0]
            print(f"\n   Sample domain_contact (ID={sample.id}):")
            print(f"   - Domain: {sample.domain}")
            print(f"   - contacts_json keys: {list(sample.contacts_json.keys()) if sample.contacts_json else 'None'}")
            if sample.contacts_json:
                for key, value in sample.contacts_json.items():
                    print(f"     * {key}: {value[:2] if isinstance(value, list) and len(value) > 0 else value}")
        
        # Check if contacts table has non-email types
        print("\n3. NON-EMAIL CONTACTS IN 'contacts' TABLE:")
        print("-" * 80)
        telegram_count = db.query(Contact).filter(Contact.contact_type == ContactType.TELEGRAM).count()
        linkedin_count = db.query(Contact).filter(Contact.contact_type == ContactType.LINKEDIN).count()
        phone_count = db.query(Contact).filter(Contact.contact_type == ContactType.PHONE).count()
        
        print(f"   Telegram: {telegram_count}")
        print(f"   LinkedIn: {linkedin_count}")
        print(f"   Phone:    {phone_count}")
        
        if telegram_count == 0 and linkedin_count == 0:
            print("\n   ⚠️  WARNING: No Telegram/LinkedIn contacts found!")
            print("   This means either:")
            print("   - Extraction didn't find any Telegram/LinkedIn links")
            print("   - OR they were not saved to the normalized 'contacts' table")
        
        # Show sample data from export query
        print("\n4. SAMPLE EXPORT DATA (first 5 domains):")
        print("-" * 80)
        
        query = (
            db.query(
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
        )
        
        results = query.limit(20).all()
        
        if not results:
            print("   No contacts found in database!")
        else:
            # Group by domain
            domains = {}
            for row in results:
                key = row.domain
                if key not in domains:
                    domains[key] = {
                        'keyword': row.keyword,
                        'country': row.country,
                        'language': row.language,
                        'emails': [],
                        'telegrams': [],
                        'linkedins': [],
                        'phones': []
                    }
                
                if row.contact_type == ContactType.EMAIL:
                    domains[key]['emails'].append(row.value)
                elif row.contact_type == ContactType.TELEGRAM:
                    domains[key]['telegrams'].append(row.value)
                elif row.contact_type == ContactType.LINKEDIN:
                    domains[key]['linkedins'].append(row.value)
                elif row.contact_type == ContactType.PHONE:
                    domains[key]['phones'].append(row.value)
            
            for idx, (domain, data) in enumerate(list(domains.items())[:5], 1):
                print(f"\n   {idx}. {domain}")
                print(f"      Keyword: {data['keyword']}")
                print(f"      Country: {data['country']}, Language: {data['language']}")
                print(f"      Emails:    {data['emails'][:2] if data['emails'] else 'None'}")
                print(f"      Telegram:  {data['telegrams'][:2] if data['telegrams'] else 'None'}")
                print(f"      LinkedIn:  {data['linkedins'][:2] if data['linkedins'] else 'None'}")
                print(f"      Phones:    {data['phones'][:2] if data['phones'] else 'None'}")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_contacts()
