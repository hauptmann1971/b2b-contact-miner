"""Tests for task queue dependency resolution and session cleanup."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from workers.db_task_queue import DatabaseTaskQueue


def _task(task_type: str, status: str):
    return SimpleNamespace(task_type=task_type, status=status)


def test_completed_parent_allows_child():
    parent = _task("search_keyword", "completed")
    child = _task("crawl_domain", "pending")
    assert DatabaseTaskQueue._dependency_satisfied(parent, child) is True


def test_running_parent_blocks_child():
    parent = _task("search_keyword", "running")
    child = _task("crawl_domain", "pending")
    assert DatabaseTaskQueue._dependency_satisfied(parent, child) is False


def test_failed_search_allows_crawl():
    parent = _task("search_keyword", "failed")
    child = _task("crawl_domain", "pending")
    assert DatabaseTaskQueue._dependency_satisfied(parent, child) is True


def test_failed_crawl_allows_extract():
    parent = _task("crawl_domain", "failed")
    child = _task("extract_contacts", "pending")
    assert DatabaseTaskQueue._dependency_satisfied(parent, child) is True


@pytest.mark.asyncio
async def test_add_task_preserves_session_creation_error():
    queue = DatabaseTaskQueue()

    with patch("workers.db_task_queue.SessionLocal", side_effect=RuntimeError("db down")), \
         patch.object(queue, "_safe_close_db", wraps=queue._safe_close_db) as close_db:
        with pytest.raises(RuntimeError, match="db down"):
            await queue.add_task("test", "search_keyword", {"keyword": "test"})

        close_db.assert_not_called()


@pytest.mark.asyncio
async def test_add_task_rolls_back_and_closes_on_commit_error():
    queue = DatabaseTaskQueue()
    db = MagicMock()
    db.commit.side_effect = RuntimeError("commit failed")

    with patch("workers.db_task_queue.SessionLocal", return_value=db):
        with pytest.raises(RuntimeError, match="commit failed"):
            await queue.add_task("test", "search_keyword", {"keyword": "test"})

    db.rollback.assert_called_once()
    db.close.assert_called_once()


@pytest.mark.asyncio
async def test_add_task_preserves_original_error_when_rollback_fails():
    queue = DatabaseTaskQueue()
    db = MagicMock()
    db.commit.side_effect = RuntimeError("commit failed")
    db.rollback.side_effect = RuntimeError("rollback failed")

    with patch("workers.db_task_queue.SessionLocal", return_value=db):
        with pytest.raises(RuntimeError, match="commit failed"):
            await queue.add_task("test", "search_keyword", {"keyword": "test"})

    db.rollback.assert_called_once()
    db.close.assert_called_once()
