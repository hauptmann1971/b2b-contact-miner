"""Map pipeline country/language to Yandex Search API v2 enums."""
from __future__ import annotations

# Country (ISO) -> SearchQuery.searchType
COUNTRY_TO_SEARCH_TYPE = {
    "RU": "SEARCH_TYPE_RU",
    "KZ": "SEARCH_TYPE_KK",
    "UZ": "SEARCH_TYPE_UZ",
    "BY": "SEARCH_TYPE_BE",
    "TR": "SEARCH_TYPE_TR",
    "US": "SEARCH_TYPE_COM",
    "GB": "SEARCH_TYPE_COM",
    "DE": "SEARCH_TYPE_COM",
}

# Language -> WebSearchRequest.l10n
LANGUAGE_TO_L10N = {
    "ru": "LOCALIZATION_RU",
    "uk": "LOCALIZATION_UK",
    "be": "LOCALIZATION_BE",
    "kk": "LOCALIZATION_KK",
    "tr": "LOCALIZATION_TR",
    "en": "LOCALIZATION_EN",
}


def yandex_search_type(country: str) -> str:
    return COUNTRY_TO_SEARCH_TYPE.get((country or "RU").upper(), "SEARCH_TYPE_RU")


def yandex_l10n(language: str) -> str:
    return LANGUAGE_TO_L10N.get((language or "ru").lower(), "LOCALIZATION_RU")
