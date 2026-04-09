"""
View crawl results and extracted contacts from database
"""
from models.database import SessionLocal, init_db, Keyword, SearchResult, DomainContact, Contact, ContactType
from sqlalchemy import func


def show_crawl_results():
    """Display all crawl results"""
    init_db()
    db = SessionLocal()
    
    try:
        print("="*80)
        print("CRAWL RESULTS - All Keywords")
        print("="*80)
        
        # Get all keywords with their status
        keywords = db.query(Keyword).all()
        
        if not keywords:
            print("\nNo keywords found in database.")
            return
        
        for keyword in keywords:
            status = "✅ Processed" if keyword.is_processed else "⏳ Pending"
            last_crawl = keyword.last_crawled_at.strftime("%Y-%m-%d %H:%M") if keyword.last_crawled_at else "Never"
            
            print(f"\n{'='*80}")
            print(f"Keyword: '{keyword.keyword}' ({keyword.language}, {keyword.country})")
            print(f"Status: {status} | Last crawled: {last_crawl}")
            print(f"ID: {keyword.id}")
            
            # Get search results for this keyword
            search_results = db.query(SearchResult).filter(
                SearchResult.keyword_id == keyword.id
            ).order_by(SearchResult.position).all()
            
            if search_results:
                print(f"\n📊 Search Results Found: {len(search_results)}")
                for sr in search_results[:5]:  # Show top 5
                    print(f"   {sr.position}. {sr.title[:60]}")
                    print(f"      {sr.url[:70]}")
                
                # Get domain contacts for these search results
                domain_contacts = db.query(DomainContact).join(SearchResult).filter(
                    SearchResult.keyword_id == keyword.id
                ).all()
                
                if domain_contacts:
                    print(f"\n🌐 Domains Crawled: {len(domain_contacts)}")
                    
                    total_emails = 0
                    total_telegram = 0
                    total_linkedin = 0
                    
                    for dc in domain_contacts:
                        # Count contacts for this domain
                        emails = db.query(Contact).filter(
                            Contact.domain_contact_id == dc.id,
                            Contact.contact_type == ContactType.EMAIL
                        ).count()
                        
                        telegrams = db.query(Contact).filter(
                            Contact.domain_contact_id == dc.id,
                            Contact.contact_type == ContactType.TELEGRAM
                        ).count()
                        
                        linkedins = db.query(Contact).filter(
                            Contact.domain_contact_id == dc.id,
                            Contact.contact_type == ContactType.LINKEDIN
                        ).count()
                        
                        total_emails += emails
                        total_telegram += telegrams
                        total_linkedin += linkedins
                        
                        print(f"\n   📍 {dc.domain}")
                        print(f"      Confidence: {dc.confidence_score}%")
                        print(f"      Verified: {'Yes' if dc.is_verified else 'No'}")
                        print(f"      Contacts: {emails} emails, {telegrams} Telegram, {linkedins} LinkedIn")
                        
                        # Show actual contact values
                        contacts = db.query(Contact).filter(
                            Contact.domain_contact_id == dc.id
                        ).all()
                        
                        if contacts:
                            for c in contacts:
                                print(f"         • {c.contact_type.value}: {c.value}")
                    
                    print(f"\n   📈 Total for this keyword:")
                    print(f"      Emails: {total_emails}")
                    print(f"      Telegram: {total_telegram}")
                    print(f"      LinkedIn: {total_linkedin}")
                else:
                    print(f"\n   ⚠️  No domains crawled yet")
            else:
                print(f"\n   ⚠️  No search results saved")
        
        # Overall summary
        print(f"\n{'='*80}")
        print("OVERALL SUMMARY")
        print("="*80)
        
        total_keywords = db.query(func.count(Keyword.id)).scalar()
        processed_keywords = db.query(func.count(Keyword.id)).filter(Keyword.is_processed == True).scalar()
        total_domains = db.query(func.count(DomainContact.id)).scalar()
        total_emails = db.query(func.count(Contact.id)).filter(Contact.contact_type == ContactType.EMAIL).scalar()
        total_telegram = db.query(func.count(Contact.id)).filter(Contact.contact_type == ContactType.TELEGRAM).scalar()
        total_linkedin = db.query(func.count(Contact.id)).filter(Contact.contact_type == ContactType.LINKEDIN).scalar()
        
        print(f"\nTotal keywords: {total_keywords}")
        print(f"Processed keywords: {processed_keywords}")
        print(f"Pending keywords: {total_keywords - processed_keywords}")
        print(f"\nTotal domains crawled: {total_domains}")
        print(f"\nTotal contacts found:")
        print(f"  📧 Emails: {total_emails}")
        print(f"  ✈️  Telegram: {total_telegram}")
        print(f"  💼 LinkedIn: {total_linkedin}")
        print(f"  📊 Total: {total_emails + total_telegram + total_linkedin}")
        print("="*80)
        
    finally:
        db.close()


if __name__ == "__main__":
    show_crawl_results()
