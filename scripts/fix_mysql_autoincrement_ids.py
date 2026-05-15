"""One-off repair: add AUTO_INCREMENT to legacy tables where `id` was created as plain INT.

Run on server:  python scripts/fix_mysql_autoincrement_ids.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from sqlalchemy import create_engine, text

from config.settings import settings

# Child tables first (DELETE id=0), then parents.
TABLES = [
    "contacts",
    "domain_contacts",
    "search_results",
    "crawl_logs",
    "keywords",
    "pipeline_state",
    "task_queue",
]


def main():
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in TABLES:
            ddl = conn.execute(text(f"SHOW CREATE TABLE `{table}`")).fetchone()[1]
            first_line = next((ln.strip() for ln in ddl.split("\n") if ln.strip().startswith("`id`")), "")
            if "AUTO_INCREMENT" in first_line:
                print(f"{table}: already AUTO_INCREMENT, skip")
                continue
            conn.execute(text(f"DELETE FROM `{table}` WHERE `id` = 0"))
            max_id = conn.execute(text(f"SELECT IFNULL(MAX(`id`), 0) FROM `{table}`")).scalar()
            next_id = int(max_id) + 1
            conn.execute(
                text(f"ALTER TABLE `{table}` MODIFY COLUMN `id` INT NOT NULL AUTO_INCREMENT")
            )
            conn.execute(text(f"ALTER TABLE `{table}` AUTO_INCREMENT = :n"), {"n": next_id})
            print(f"{table}: fixed AUTO_INCREMENT next={next_id}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


if __name__ == "__main__":
    main()
