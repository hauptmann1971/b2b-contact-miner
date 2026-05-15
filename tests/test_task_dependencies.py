"""Tests for task queue dependency resolution."""
from types import SimpleNamespace

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
