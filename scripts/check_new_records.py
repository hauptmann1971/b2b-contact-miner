"""Check if new records have contacts_json"""
from models.database import SessionLocal, DomainContact

def check_new_records():
    db = SessionLocal()
    
    try:
        # Get last 5 domain_contacts by ID (newest)
        recent = db.query(DomainContact).order_by(DomainContact.id.desc()).limit(10).all()
        
        print("=" * 80)
        print("RECENT DOMAIN_CONTACTS RECORDS")
        print("=" * 80)
        
        for dc in recent:
            print(f"\nID: {dc.id}")
            print(f"Domain: {dc.domain}")
            print(f"contacts_json is None: {dc.contacts_json is None}")
            if dc.contacts_json:
                print(f"contacts_json keys: {list(dc.contacts_json.keys())}")
                for key, value in dc.contacts_json.items():
                    if value:
                        print(f"  - {key}: {value[:2] if isinstance(value, list) else value}")
            print(f"Created at: {dc.created_at}")
            print("-" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_new_records()
