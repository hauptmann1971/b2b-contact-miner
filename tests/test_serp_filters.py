from utils.serp_filters import (
    build_search_query,
    filter_search_results,
    is_blocked_url,
    normalize_host,
    pick_urls_for_crawl,
)


def test_build_search_query_no_invalid_site_operator():
    q = build_search_query("fintech startup", language="en", country="US")
    assert "site:" not in q
    assert "fintech" in q


def test_is_blocked_wikipedia():
    assert is_blocked_url("https://en.wikipedia.org/wiki/Fintech")


def test_filter_drops_blocked():
    results = [
        {"url": "https://example.com/contact"},
        {"url": "https://en.wikipedia.org/wiki/X"},
    ]
    out = filter_search_results(results)
    assert len(out) == 1
    assert "example.com" in out[0]["url"]


def test_pick_urls_dedupes_by_host():
    results = [
        {"url": "https://example.com/blog/post-1"},
        {"url": "https://www.example.com/about"},
    ]
    urls = pick_urls_for_crawl(results)
    hosts = {normalize_host(u) for u in urls}
    assert hosts == {"example.com"}
