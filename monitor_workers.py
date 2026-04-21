"""Мониторинг воркеров и очереди задач"""
import asyncio
from datetime import datetime, timezone
from models.database import SessionLocal
from models.task_queue import TaskQueue
from workers.db_task_queue import DatabaseTaskQueue
from sqlalchemy import func

async def monitor_workers():
    """Полный мониторинг системы воркеров"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("🔍 МОНИТОРИНГ ВОРКЕРОВ И ОЧЕРЕДИ ЗАДАЧ")
        print("=" * 80)
        
        # 1. Статистика по задачам
        print("\n📊 СТАТИСТИКА ЗАДАЧ:")
        print("-" * 80)
        
        stats = db.query(
            TaskQueue.status,
            func.count(TaskQueue.id)
        ).group_by(TaskQueue.status).all()
        
        total_tasks = sum(count for _, count in stats)
        
        for status, count in stats:
            percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
            status_icon = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(status, '❓')
            
            print(f"   {status_icon} {status:12s}: {count:4d} ({percentage:5.1f}%)")
        
        print(f"   {'='*40}")
        print(f"   {'ВСЕГО':12s}: {total_tasks:4d}")
        
        # 2. Проверка зависших задач (stale tasks)
        print("\n🚨 ЗАВИСШИЕ ЗАДАЧИ (stale tasks):")
        print("-" * 80)
        
        from config.settings import settings
        lock_timeout = settings.TASK_LOCK_TIMEOUT
        timeout_threshold = datetime.now(timezone.utc).timestamp() - lock_timeout
        
        stale_tasks = db.query(TaskQueue).filter(
            TaskQueue.status == 'running',
            TaskQueue.locked_at is not None
        ).all()
        
        # Фильтруем вручную, так как locked_at может быть datetime
        stale_count = 0
        for task in stale_tasks:
            if task.locked_at and task.locked_at.timestamp() < timeout_threshold:
                stale_count += 1
                print(f"   ⚠️  Task #{task.id}: {task.task_type}")
                print(f"       Locked by: {task.locked_by}")
                print(f"       Locked at: {task.locked_at}")
                print(f"       Duration: {(datetime.now(timezone.utc) - task.locked_at).total_seconds()/60:.1f} min")
        
        if stale_count == 0:
            print("   ✅ Нет зависших задач")
        else:
            print(f"\n   ⚠️  НАЙДЕНО {stale_count} ЗАВИСШИХ ЗАДАЧ!")
            print(f"   💡 Запустите: python recover_stale_tasks.py")
        
        # 3. Активные воркеры (задачи в running статусе)
        print("\n🔄 АКТИВНЫЕ ЗАДАЧИ (выполняются сейчас):")
        print("-" * 80)
        
        running_tasks = db.query(TaskQueue).filter(
            TaskQueue.status == 'running'
        ).order_by(TaskQueue.locked_at.desc()).limit(10).all()
        
        if running_tasks:
            for task in running_tasks:
                duration = ""
                if task.locked_at:
                    secs = (datetime.now(timezone.utc) - task.locked_at).total_seconds()
                    duration = f"({secs/60:.1f} min)"
                
                print(f"   🔄 Task #{task.id}: {task.task_type:20s} {duration}")
                if task.payload:
                    import json
                    try:
                        payload = json.loads(task.payload)
                        if 'keyword' in payload:
                            print(f"       Keyword: {payload['keyword']}")
                        if 'domain' in payload:
                            print(f"       Domain: {payload['domain']}")
                    except:
                        pass
        else:
            print("   ℹ️  Нет активных задач")
        
        # 4. Последние ошибки
        print("\n❌ ПОСЛЕДНИЕ ОШИБКИ:")
        print("-" * 80)
        
        failed_tasks = db.query(TaskQueue).filter(
            TaskQueue.status == 'failed'
        ).order_by(TaskQueue.created_at.desc()).limit(5).all()
        
        if failed_tasks:
            for task in failed_tasks:
                print(f"   ❌ Task #{task.id}: {task.task_type}")
                print(f"       Error: {task.error_message[:100] if task.error_message else 'N/A'}")
                print(f"       Time: {task.created_at}")
        else:
            print("   ✅ Нет ошибок")
        
        # 5. Прогресс по ключевым словам
        print("\n📝 ПРОГРЕСС ПО КЛЮЧЕВЫМ СЛОВАМ:")
        print("-" * 80)
        
        from models.database import Keyword, SearchResult
        
        keywords = db.query(Keyword).order_by(Keyword.id.desc()).limit(10).all()
        
        for kw in keywords:
            search_results = db.query(SearchResult).filter(
                SearchResult.keyword_id == kw.id
            ).count()
            
            status_icon = "✅" if search_results > 0 else "⏳"
            
            print(f"   {status_icon} {kw.keyword:30s} | Search Results: {search_results:2d}")
        
        # 6. Рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ:")
        print("-" * 80)
        
        if stale_count > 0:
            print("   ⚠️  Есть зависшие задачи!")
            print("      → Запустите: python recover_stale_tasks.py")
        
        if total_tasks == 0:
            print("   ℹ️  Очередь пуста")
            print("      → Добавьте keywords через веб-интерфейс или main.py")
        
        running_count = sum(1 for s, c in stats if s == 'running')
        if running_count > 15:
            print(f"   ⚠️  Высокая нагрузка: {running_count} задач выполняется")
            print("      → Это нормально при активной обработке")
        
        failed_count = sum(1 for s, c in stats if s == 'failed')
        if failed_count > 20:
            print(f"   ⚠️  Много ошибок: {failed_count} failed задач")
            print("      → Проверьте логи для диагностики")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(monitor_workers())
