from utils.yandex_search_mapping import yandex_l10n, yandex_search_type
from utils.yandex_search_xml import parse_web_search_xml


SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<yandexsearch version="1.0">
  <response>
    <results>
      <grouping>
        <group>
          <doc>
            <url>https://example.com/contact</url>
            <title>Example Corp</title>
            <passages><passage>Email info@example.com</passage></passages>
          </doc>
        </group>
      </grouping>
    </results>
  </response>
</yandexsearch>
"""


def test_parse_web_search_xml():
    rows = parse_web_search_xml(SAMPLE_XML, max_results=5)
    assert len(rows) == 1
    assert rows[0]["url"] == "https://example.com/contact"
    assert "Example" in rows[0]["title"]
    assert "info@example.com" in rows[0]["snippet"]


def test_country_mapping():
    assert yandex_search_type("KZ") == "SEARCH_TYPE_KK"
    assert yandex_search_type("XX") == "SEARCH_TYPE_RU"
    assert yandex_l10n("kk") == "LOCALIZATION_KK"
