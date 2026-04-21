"""Восстановление зависших задач (stale tasks)"""
import asyncio
from workers.db_task_queue import DatabaseTaskQueue

async def recover():
    """Recover stale tasks from crashed workers"""
    queue = DatabaseTaskQueue()
    recovered = await queue.recover_stale_tasks()
    
    print("\n" + "=" * 80)
    if recovered > 0:
        print(f"✅ Восстановлено {recovered} зависших задач")
        print("   Задачи возвращены в очередь pending и будут обработаны")
    else:
        print("✅ Нет зависших задач - все воркеры работают нормально")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(recover())
