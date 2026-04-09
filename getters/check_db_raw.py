"""
Check raw database tables for test results
"""
from models.database import SessionLocal, init_db, Keyword, SearchResult, DomainContact, Contact, ContactType


def check_raw_data():
    """Check all tables for data"""
    init_db()
    db = SessionLocal()
    
    try:
        print("="*80)
        print("RAW DATABASE INSPECTION")
        print("="*80)
        
        # 1. Keywords
        print("\n1. KEYWORDS TABLE:")
        keywords = db.query(Keyword).all()
        print(f"   Total keywords: {len(keywords)}")
        for kw in keywords[:3]:  # Show first 3
            print(f"   - ID {kw.id}: '{kw.keyword}' ({kw.language}, {kw.country}) - {'Processed' if kw.is_processed else 'Pending'}")
        
        # 2. Search Results
        print("\n2. SEARCH RESULTS TABLE:")
        search_results = db.query(SearchResult).all()
        print(f"   Total search results: {len(search_results)}")
        
        # Group by keyword
        from collections import Counter
        keyword_counts = Counter(sr.keyword_id for sr in search_results)
        for keyword_id, count in keyword_counts.items():
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if keyword:
                print(f"   - Keyword ID {keyword_id} ('{keyword.keyword}'): {count} results")
        
        # Show some examples
        if search_results:
            print("\n   Sample search results:")
            for sr in search_results[:5]:
                print(f"     • [{sr.position}] {sr.url[:70]}")
        
        # 3. Domain Contacts
        print("\n3. DOMAIN CONTACTS TABLE:")
        domain_contacts = db.query(DomainContact).all()
        print(f"   Total domain contacts: {len(domain_contacts)}")
        
        if domain_contacts:
            for dc in domain_contacts:
                print(f"   - {dc.domain}")
                print(f"     Confidence: {dc.confidence_score}%")
                print(f"     Verified: {dc.is_verified}")
                
                # Get contacts for this domain
                contacts = db.query(Contact).filter(Contact.domain_contact_id == dc.id).all()
                if contacts:
                    for c in contacts:
                        print(f"     • {c.contact_type.value}: {c.value}")
        else:
            print("   ⚠️  No domain contacts found (crawling results not saved)")
        
        # 4. Contacts
        print("\n4. CONTACTS TABLE:")
        contacts = db.query(Contact).all()
        print(f"   Total contacts: {len(contacts)}")
        
        if contacts:
            contact_types = Counter(c.contact_type.value for c in contacts)
            for ctype, count in contact_types.items():
                print(f"   - {ctype}: {count}")
            
            print("\n   Sample contacts:")
            for c in contacts[:5]:
                dc = db.query(DomainContact).filter(DomainContact.id == c.domain_contact_id).first()
                domain = dc.domain if dc else "Unknown"
                print(f"     • {domain}: {c.contact_type.value} = {c.value}")
        else:
            print("   ⚠️  No contacts found")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Keywords: {len(keywords)}")
        print(f"Search Results: {len(search_results)}")
        print(f"Domain Contacts: {len(domain_contacts)}")
        print(f"Contacts: {len(contacts)}")
        print("="*80)
        
        if len(search_results) > 0 and len(domain_contacts) == 0:
            print("\n⚠️  NOTE: Search results exist but no domains were crawled/saved.")
            print("   The test script displayed results but didn't save them to DB.")
            print("   To save results, run the full pipeline: python main.py")
        
    finally:
        db.close()


if __name__ == "__main__":
    check_raw_data()
