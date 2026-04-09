"""
Test MySQL connection and database setup
Run this after configuring .env file
"""
from sqlalchemy import text
from models.database import SessionLocal, engine, init_db
import sys


def test_mysql_connection():
    """Test MySQL database connection"""
    print("="*60)
    print("Testing MySQL Connection")
    print("="*60)
    
    try:
        # Test 1: Check engine URL
        print(f"\n1. Database URL: {engine.url}")
        print(f"   Driver: {engine.url.drivername}")
        
        # Test 2: Connect to database
        print("\n2. Testing connection...")
        db = SessionLocal()
        result = db.execute(text("SELECT VERSION()")).fetchone()
        print(f"   ✅ Connected! MySQL Version: {result[0]}")
        
        # Test 3: Check character set
        result = db.execute(text("SELECT @@character_set_database, @@collation_database")).fetchone()
        print(f"   ✅ Character Set: {result[0]}")
        print(f"   ✅ Collation: {result[1]}")
        
        db.close()
        
        # Test 4: Create tables
        print("\n3. Creating tables...")
        init_db()
        print("   ✅ All tables created successfully")
        
        # Test 5: Verify tables
        db = SessionLocal()
        result = db.execute(text("SHOW TABLES")).fetchall()
        tables = [row[0] for row in result]
        print(f"   ✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"      - {table}")
        db.close()
        
        print("\n" + "="*60)
        print("✅ All tests passed! MySQL is ready to use.")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL is running")
        print("2. Check DATABASE_URL in .env file")
        print("3. Verify user credentials")
        print("4. Run setup_mysql.sql to create database")
        print("\nCommon issues:")
        print("- Access denied: Check username/password in .env")
        print("- Unknown database: Run setup_mysql.sql first")
        print("- Can't connect: Make sure MySQL service is running")
        return False


if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)
