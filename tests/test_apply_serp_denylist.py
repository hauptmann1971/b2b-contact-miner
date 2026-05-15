from scripts.apply_serp_denylist import _parse_env_hosts, _write_env_hosts


def test_parse_env_hosts_comma_separated(tmp_path):
    env = tmp_path / ".env"
    env.write_text("SERP_BLOCKED_HOST_SUFFIXES=foo.com,bar.com\n", encoding="utf-8")
    assert _parse_env_hosts(env.read_text(encoding="utf-8")) == ["foo.com", "bar.com"]


def test_write_env_hosts_updates_line(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=1\nSERP_BLOCKED_HOST_SUFFIXES=old.com\n", encoding="utf-8")
    _write_env_hosts(str(env), ["a.com", "b.com"])
    text = env.read_text(encoding="utf-8")
    assert 'SERP_BLOCKED_HOST_SUFFIXES=["a.com", "b.com"]' in text
    assert "old.com" not in text
