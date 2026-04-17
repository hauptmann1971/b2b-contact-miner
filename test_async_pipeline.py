"""Test script for async parallel pipeline"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, Keyword, init_db
from workers.db_task_queue import DatabaseTaskQueue
from loguru import logger

async def test_queue_system():
    """Test the async task queue system"""
    
    print("="*80)
    print("Testing Async Parallel Pipeline")
    print("="*80)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("✓ Database initialized")
    
    # Create task queue
    print("\n2. Creating task queue...")
    queue = DatabaseTaskQueue(max_concurrent=5)
    print(f"✓ Task queue created (max_concurrent={queue.max_concurrent})")
    
    # Start workers
    print("\n3. Starting workers...")
    await queue.start_workers()
    print("✓ Workers started")
    
    # Add test tasks
    print("\n4. Adding test tasks...")
    
    # Check if we have pending keywords
    db = SessionLocal()
    pending_keywords = db.query(Keyword).filter(Keyword.is_processed == False).limit(3).all()
    db.close()
    
    if not pending_keywords:
        print("⚠ No pending keywords found. Creating a test keyword...")
        db = SessionLocal()
        test_keyword = Keyword(
            keyword="test B2B software",
            language="ru",
            country="RU",
            is_processed=False
        )
        db.add(test_keyword)
        db.commit()
        db.refresh(test_keyword)
        pending_keywords = [test_keyword]
        print(f"✓ Created test keyword: {test_keyword.keyword}")
        db.close()
    
    # Add search tasks for each keyword
    for keyword in pending_keywords:
        task_id = await queue.add_task(
            task_name=f"search_{keyword.id}",
            task_type='search_keyword',
            payload={
                'keyword_id': keyword.id,
                'keyword': keyword.keyword,
                'language': keyword.language,
                'country': keyword.country
            },
            priority=10,
            keyword_id=keyword.id
        )
        print(f"   ✓ Added search task #{task_id} for keyword: {keyword.keyword}")
    
    # Monitor progress
    print("\n5. Monitoring task execution...")
    print("   (This will take a few minutes depending on number of keywords)\n")
    
    iteration = 0
    max_iterations = 60  # 5 minutes max (60 * 5 seconds)
    
    while iteration < max_iterations:
        stats = await queue.get_queue_stats()
        
        print(f"\r   [{iteration*5}s] Pending: {stats['pending']:3d} | "
              f"Running: {stats['running']:3d} | "
              f"Completed: {stats['completed']:3d} | "
              f"Failed: {stats['failed']:3d} | "
              f"Keywords: {stats.get('keywords_in_progress', 0)}", end='', flush=True)
        
        # Check if all tasks completed
        if stats['pending'] == 0 and stats['running'] == 0:
            print("\n\n✅ All tasks completed!")
            print(f"\n   Final Statistics:")
            print(f"   - Total tasks: {stats['total']}")
            print(f"   - Completed: {stats['completed']}")
            print(f"   - Failed: {stats['failed']}")
            break
        
        await asyncio.sleep(5)
        iteration += 1
    else:
        print("\n\n⚠ Timeout reached. Some tasks may still be running.")
    
    # Stop workers
    print("\n6. Stopping workers...")
    await queue.stop_workers()
    print("✓ Workers stopped")
    
    # Show final results
    print("\n7. Checking results...")
    db = SessionLocal()
    
    from models.database import DomainContact, Contact
    
    total_domains = db.query(DomainContact).count()
    total_contacts = db.query(Contact).count()
    
    print(f"   - Domains with contacts: {total_domains}")
    print(f"   - Total contacts found: {total_contacts}")
    
    if total_contacts > 0:
        print(f"\n   Sample contacts:")
        sample_contacts = db.query(Contact).limit(5).all()
        for contact in sample_contacts:
            print(f"     • {contact.contact_type.value}: {contact.value}")
    
    db.close()
    
    print("\n" + "="*80)
    print("✅ Test completed successfully!")
    print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(test_queue_system())
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
