from unittest.mock import MagicMock, patch

import pytest

from workers.db_task_queue import DatabaseTaskQueue


@pytest.mark.asyncio
async def test_add_task_preserves_session_creation_error():
    queue = DatabaseTaskQueue()

    with patch(
        "workers.db_task_queue.SessionLocal",
        side_effect=RuntimeError("database unavailable"),
    ):
        with pytest.raises(RuntimeError, match="database unavailable"):
            await queue.add_task("crawl_1", "crawl_domain", {"url": "https://example.com"})


@pytest.mark.asyncio
async def test_add_task_preserves_original_error_when_cleanup_fails():
    queue = DatabaseTaskQueue()
    db = MagicMock()
    db.commit.side_effect = RuntimeError("commit failed")
    db.rollback.side_effect = RuntimeError("rollback failed")
    db.close.side_effect = RuntimeError("close failed")

    with patch("workers.db_task_queue.SessionLocal", return_value=db):
        with pytest.raises(RuntimeError, match="commit failed"):
            await queue.add_task("crawl_1", "crawl_domain", {"url": "https://example.com"})

    db.rollback.assert_called_once()
    db.close.assert_called_once()
