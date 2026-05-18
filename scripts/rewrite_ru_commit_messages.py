#!/usr/bin/env python3
"""Rewrite legacy Russian git commit subjects to English (used by git filter-branch)."""
from __future__ import annotations

import sys

SUBJECT_MAP = {
    "Сделал b2b-contact-miner": "Initial b2b-contact-miner project",
    "Использую DuckDuckGo как поисковик и YandexGPT в качестве LLM": (
        "Use DuckDuckGo for search and YandexGPT as LLM"
    ),
    "Упорядочил проект, написал геттеры для токенов": (
        "Reorganize project and add token getters"
    ),
    "Добавил шаблоны к эндпоинтам и сделал общий файл для запуска": (
        "Add endpoint templates and unified app entrypoint"
    ),
    "Доделал мониторинг. Вынес его на главную страницу": (
        "Finish monitoring and move it to the main page"
    ),
    "Немного подправил": "Minor fixes and cleanup",
}


def main() -> None:
    raw = sys.stdin.read()
    if not raw:
        return
    lines = raw.splitlines(keepends=True)
    if not lines:
        return
    subject = lines[0].rstrip("\r\n")
    if subject in SUBJECT_MAP:
        lines[0] = SUBJECT_MAP[subject] + (
            "\n" if lines[0].endswith("\n") else ""
        )
    sys.stdout.write("".join(lines))


if __name__ == "__main__":
    main()
