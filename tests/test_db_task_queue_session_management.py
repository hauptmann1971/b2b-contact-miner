import pytest
from unittest.mock import MagicMock, patch

from workers.db_task_queue import DatabaseTaskQueue


@pytest.mark.asyncio
async def test_add_task_preserves_session_creation_error():
    queue = DatabaseTaskQueue(max_concurrent=1)
    session_error = RuntimeError("database unavailable")

    with patch("workers.db_task_queue.SessionLocal", side_effect=session_error):
        with pytest.raises(RuntimeError, match="database unavailable") as exc_info:
            await queue.add_task(
                task_name="test-task",
                task_type="crawl_domain",
                payload={"url": "https://example.com"},
            )

    assert exc_info.value is session_error


@pytest.mark.asyncio
async def test_add_task_rolls_back_and_closes_on_commit_error():
    queue = DatabaseTaskQueue(max_concurrent=1)
    db = MagicMock()
    db.commit.side_effect = RuntimeError("commit failed")

    with patch("workers.db_task_queue.SessionLocal", return_value=db):
        with pytest.raises(RuntimeError, match="commit failed"):
            await queue.add_task(
                task_name="test-task",
                task_type="crawl_domain",
                payload={"url": "https://example.com"},
            )

    db.rollback.assert_called_once()
    db.close.assert_called_once()


@pytest.mark.asyncio
async def test_queue_stats_handles_session_creation_error():
    queue = DatabaseTaskQueue(max_concurrent=1)

    with patch("workers.db_task_queue.SessionLocal", side_effect=RuntimeError("database unavailable")):
        assert await queue.get_queue_stats() == {}
