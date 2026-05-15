from utils.serp_denylist import format_denylist_env_lines


def test_format_denylist_env_lines():
    rows = [("bad.example", 5, "reason"), ("worse.example", 3, "reason2")]
    assert format_denylist_env_lines(rows) == ["bad.example", "worse.example"]
