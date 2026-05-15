from utils.serp_filters import (
    build_search_query,
    filter_search_results,
    is_blocked_url,
    normalize_host,
    pick_urls_for_crawl,
    score_crawl_url,
)


def test_build_search_query_no_invalid_site_operator():
    q = build_search_query("fintech startup", language="en", country="US")
    assert "site:" not in q
    assert "fintech" in q


def test_is_blocked_wikipedia():
    assert is_blocked_url("https://en.wikipedia.org/wiki/Fintech")


def test_is_blocked_investopedia():
    assert is_blocked_url("https://www.investopedia.com/terms/fintech.asp")


def test_filter_drops_blocked():
    results = [
        {"url": "https://example.com/contact"},
        {"url": "https://en.wikipedia.org/wiki/X"},
    ]
    out = filter_search_results(results)
    assert len(out) == 1
    assert "example.com" in out[0]["url"]


def test_pick_urls_dedupes_by_host_prefers_about_over_blog():
    results = [
        {"url": "https://example.com/blog/post-1"},
        {"url": "https://www.example.com/about"},
    ]
    urls = pick_urls_for_crawl(results)
    assert len(urls) == 1
    assert "/about" in urls[0]


def test_pick_urls_orders_contact_before_blog_hosts():
    results = [
        {"url": "https://blogcorp.com/news/item"},
        {"url": "https://acme.com/contact-us"},
    ]
    urls = pick_urls_for_crawl(results)
    assert len(urls) == 2
    assert "acme.com" in urls[0]


def test_score_skips_pdf():
    assert score_crawl_url("https://example.com/brochure.pdf") <= -1000
    assert pick_urls_for_crawl([{"url": "https://example.com/brochure.pdf"}]) == []


def test_is_blocked_netguru():
    assert is_blocked_url("https://www.netguru.com/clients")
